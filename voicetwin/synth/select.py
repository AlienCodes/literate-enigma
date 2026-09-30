"""自动挑选最佳模型 + 语速校准。

训练会在不同轮数保存多个模型。挑哪个最像你？不靠猜：
用"验证集"（素材准备时留出、没参与训练的你的真实录音）逐一测试——
让每个模型读同样的文字，和你的真实录音比较：
    - 声纹相似度（和你整体音色比、和这一句的真实录音比）
    - 识别错字率（读得准不准，可选）
    - 时长比（同一句话，模型读的时长 / 你本人读的时长 → 节奏像不像）
综合得分最高的模型被选为默认模型，同时根据时长比算出语速校准系数。
"""

from __future__ import annotations

import math
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import numpy as np

from voicetwin.backends.base import Backend, SynthRequest
from voicetwin.data.exporters import validation_items
from voicetwin.data.references import pick_reference
from voicetwin.eval.metrics import CERChecker
from voicetwin.eval.speaker import cosine, get_speaker_encoder, voice_centroid
from voicetwin.project import Project
from voicetwin.utils.audio import load_audio, speech_activity, trim_silence
from voicetwin.utils.log import get_logger
from voicetwin.utils.textutil import sentence_kind

log = get_logger("select")
ProgressFn = Callable[[float, str], None]


def select_and_calibrate(cfg: Dict[str, Any], project: Project, backend: Backend, max_items: int = 12,
                         use_asr: Optional[bool] = None, progress: Optional[ProgressFn] = None) -> Dict[str, Any]:
    items = validation_items(project, limit=max_items)
    if not items:
        log.warning("没有验证集片段（素材太少），用部分训练片段代替，结果仅供参考")
        items = [r for r in project.load_manifest(only_kept=True) if 3.0 <= r["duration"] <= 9.0][:max_items]
    if not items:
        raise RuntimeError("没有可用于评估的片段")
    refs = project.load_references()
    encoder = get_speaker_encoder(cfg.get("speaker_encoder", "auto"))
    cen = voice_centroid(project, encoder)
    checker = None
    if use_asr is None or use_asr:
        checker = CERChecker(cfg.get("synth", {}).get("asr_check_model", "small"))
        if use_asr is None and not checker._load():
            checker = None

    real_emb: Dict[str, np.ndarray] = {}
    real_voiced: Dict[str, float] = {}
    for it in items:
        wav, sr = load_audio(project.abspath(it["path"]))
        real_emb[it["id"]] = encoder.embed(wav, sr)
        real_voiced[it["id"]] = it.get("voiced") or speech_activity(wav, sr)[0]

    ckpts = backend.checkpoints() or [None]
    backend.start()
    tmp = project.cache_dir / "select"
    tmp.mkdir(parents=True, exist_ok=True)
    results: List[Dict[str, Any]] = []
    total_steps = len(ckpts) * len(items)
    step = 0
    for ck in ckpts:
        if ck is not None:
            log.info(f"评估模型 {ck['id']} ……")
            backend.use_checkpoint(ck)
        sims_c, sims_i, cers, ratios = [], [], [], {"zh": [], "en": []}
        for it in items:
            step += 1
            ref_pool = [r for r in refs if r["id"] != it["id"]] or refs
            ref = pick_reference(ref_pool, it["lang"], sentence_kind(it["text"]))
            out = tmp / f"{(ck or {}).get('id', 'current')}_{it['id']}.wav"
            try:
                backend.synthesize(SynthRequest(text=it["text"], lang=it["lang"], ref_audio=project.abspath(ref["path"]),
                                                ref_text=ref["text"], ref_lang=ref["lang"], seed=1234, speed=1.0), out)
                wav, sr = load_audio(out)
            except Exception as exc:
                log.warning(f"  合成失败：{exc}")
                continue
            gen_voiced = speech_activity(wav, sr)[0]
            wav, _, _ = trim_silence(wav, sr)
            emb = encoder.embed(wav, sr)
            sims_c.append(cosine(emb, cen) if cen is not None else cosine(emb, real_emb[it["id"]]))
            sims_i.append(cosine(emb, real_emb[it["id"]]))
            if gen_voiced > 0.2 and real_voiced[it["id"]] > 0.2:
                ratios.setdefault(it["lang"], []).append(gen_voiced / real_voiced[it["id"]])
            if checker is not None:
                res = checker.check(wav, sr, it["text"], it["lang"])
                if res:
                    cers.append(res["cer"])
            if progress:
                progress(step / total_steps, f"评估 {(ck or {}).get('id', '当前模型')}：{step}/{total_steps}")
        if not sims_c:
            continue
        all_ratios = ratios["zh"] + ratios["en"]
        rhythm_dev = float(np.median([abs(math.log(r)) for r in all_ratios])) if all_ratios else 0.0
        entry = {
            "id": (ck or {}).get("id", "current"), "ckpt": ck,
            "speaker_sim": float(np.mean(sims_c)), "sim_to_real": float(np.mean(sims_i)),
            "cer": float(np.mean(cers)) if cers else None, "rhythm_dev": rhythm_dev,
            "duration_ratio": {k: float(np.median(v)) for k, v in ratios.items() if v},
        }
        entry["total"] = entry["speaker_sim"] + entry["sim_to_real"] - 2.0 * (entry["cer"] or 0.0) - 0.8 * rhythm_dev
        results.append(entry)
        log.info(f"  {entry['id']}：相似度 {entry['speaker_sim']:.3f} / 与原句 {entry['sim_to_real']:.3f}"
                 + (f" / 错字率 {entry['cer']:.1%}" if entry["cer"] is not None else "")
                 + f" / 节奏偏差 {rhythm_dev:.3f} → 综合 {entry['total']:.3f}")
    if not results:
        raise RuntimeError("所有模型都合成失败，请检查引擎日志")
    best = max(results, key=lambda e: e["total"])
    speed = {}
    for lang, ratio in best["duration_ratio"].items():
        # 模型读得比你慢（ratio>1）→ 加快；GPT-SoVITS 的 speed_factor>1 表示更快
        speed[lang] = round(float(np.clip(ratio, 0.8, 1.25)), 3) if abs(ratio - 1.0) > 0.03 else 1.0
    info: Dict[str, Any] = {"speed": speed, "selection": {
        "evaluated_at": time.strftime("%Y-%m-%d %H:%M"), "items": len(items),
        "results": [{k: v for k, v in r.items() if k != "ckpt"} for r in results], "best": best["id"]}}
    if best["ckpt"] is not None:
        info["selected"] = best["ckpt"]
        backend.use_checkpoint(best["ckpt"])
    project.update_models(backend.name, info)
    log.info(f"最佳模型：{best['id']}；语速校准：{speed or '无需调整'}")
    return info


def evaluate_file(cfg: Dict[str, Any], project: Project, audio: Path, text: str = "", lang: str = "") -> Dict[str, Any]:
    """评估任意一段音频有多像你（例如对比不同引擎/参数的效果）。"""
    from voicetwin.eval.metrics import Scorer, similarity_label
    from voicetwin.utils.textutil import detect_lang

    encoder = get_speaker_encoder(cfg.get("speaker_encoder", "auto"))
    cen = voice_centroid(project, encoder)
    profile = project.load_profile()
    checker = CERChecker(cfg.get("synth", {}).get("asr_check_model", "small")) if text else None
    wav, sr = load_audio(audio)
    wav, _, _ = trim_silence(wav, sr)
    lang = lang or (detect_lang(text) if text else "zh")
    scorer = Scorer(profile, cen, encoder, cfg.get("synth", {}).get("score"), checker)
    score = scorer.score(wav, sr, text or "", lang, use_asr=bool(text))
    d = score.to_dict()
    d["label"] = similarity_label(score.speaker_sim, encoder.name)
    d["encoder"] = encoder.name
    return d
