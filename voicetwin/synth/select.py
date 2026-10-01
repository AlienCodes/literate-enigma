"""自动挑选最佳模型 + 语速校准。

训练会在不同轮数保存多个模型。挑哪个最像你？不靠猜：
用"验证集"（素材准备时留出、没参与训练的你的真实录音）逐一测试——
让每个模型读同样的文字，和你的真实录音比较：
    - 声纹相似度（几个声纹模型一起打分，按你自己真实录音的水平校准；和你整体音色比、和这一句的真实录音比）
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
from voicetwin.eval.speaker import (
    HONEST_NOTE,
    PCT_HELP,
    SimilarityJudge,
    cosine,
    get_speaker_encoder,
    gsv_root_from_cfg,
    model_label,
    voice_centroid,
)
from voicetwin.project import Project
from voicetwin.utils.audio import load_audio, speech_activity, trim_silence
from voicetwin.utils.log import get_logger
from voicetwin.utils.textutil import sentence_kind

try:  # U1：停止按钮
    from voicetwin.utils.progress import check_cancel as _check_cancel
except ImportError:  # pragma: no cover
    def _check_cancel() -> None:
        return None

log = get_logger("select")
ProgressFn = Callable[[float, str], None]
DEFAULT_ITEMS = 20


def _vram_tier() -> str:
    try:
        from voicetwin.utils.gpu import vram_tier

        return vram_tier()
    except Exception:
        return "none"


class _Sim:
    """统一"几个声纹模型一起打分"和"只有一个声纹模型"两种情况。"""

    def __init__(self, cfg: Dict[str, Any], project: Project):
        self.judge: Optional[SimilarityJudge] = None
        try:
            judge = SimilarityJudge.for_project(cfg, project)
            if judge.available:
                self.judge = judge
        except Exception as exc:
            log.warning(f"多模型声纹打分不可用（{exc}），改用单个声纹模型")
        self.encoder = None
        self.cen = None
        if self.judge is None:
            self.encoder = get_speaker_encoder(cfg.get("speaker_encoder", "auto"))
            self.cen = voice_centroid(project, self.encoder)

    def embed(self, wav: np.ndarray, sr: int) -> Dict[str, np.ndarray]:
        if self.judge is not None:
            return self.judge.embed(wav, sr)
        return {self.encoder.name: self.encoder.embed(wav, sr)}

    def compare(self, gen: Dict[str, np.ndarray], real: Dict[str, np.ndarray]) -> Dict[str, Optional[float]]:
        """返回 {'to_voice', 'to_real', 'pct'}：to_* 已按每个模型自己的 p50 缩放（没校准时是原始余弦）。"""
        to_voice: List[float] = []
        to_real: List[float] = []
        pct = None
        if self.judge is not None:
            res = self.judge.judge_embeddings(gen)
            pct = res.get("pct")
            for m in self.judge.members:
                if m.name not in gen:
                    continue
                scale = m.p50 or 1.0
                to_voice.append(cosine(gen[m.name], m.centroid) / scale)
                if m.name in real:
                    to_real.append(cosine(gen[m.name], real[m.name]) / scale)
        else:
            name = self.encoder.name
            emb = gen.get(name)
            if emb is not None:
                to_voice.append(cosine(emb, self.cen) if self.cen is not None else cosine(emb, real[name]))
                to_real.append(cosine(emb, real[name]))
        return {"to_voice": float(np.mean(to_voice)) if to_voice else None,
                "to_real": float(np.mean(to_real)) if to_real else None, "pct": pct}

    def info(self) -> Dict[str, Any]:
        if self.judge is not None:
            return self.judge.info()
        return {"models": [self.encoder.name], "labels": [model_label(self.encoder.name)],
                "reliable": bool(self.encoder.reliable), "calibration": {}, "definition": PCT_HELP, "note": HONEST_NOTE}


def select_and_calibrate(cfg: Dict[str, Any], project: Project, backend: Backend, max_items: int = DEFAULT_ITEMS,
                         use_asr: Optional[bool] = None, progress: Optional[ProgressFn] = None) -> Dict[str, Any]:
    def _p(frac: float, msg: str, log_it: bool = False) -> None:
        if log_it:
            log.info(msg)
        if progress is not None:
            try:
                progress(max(0.0, min(1.0, frac)), msg)
            except Exception:  # 进度条出问题不能打断挑选（TaskCancelled 是 BaseException，会照常传出去）
                pass

    max_items = int(max_items or DEFAULT_ITEMS)
    items = validation_items(project, limit=max_items)
    if not items:
        log.warning("没有验证集片段（素材太少），用部分训练片段代替，结果仅供参考")
        items = [r for r in project.load_manifest(only_kept=True) if 3.0 <= r["duration"] <= 9.0][:max_items]
    if not items:
        raise RuntimeError("没有可用于评估的片段")
    refs = project.load_references()
    _p(0.0, "加载声纹和识别模型（第一次使用会先下载）……", log_it=True)
    sim = _Sim(cfg, project)
    checker = None
    if use_asr is None or use_asr:
        checker = CERChecker(cfg.get("synth", {}).get("asr_check_model", "auto"), progress=progress,
                             vram_tier=_vram_tier(), gsv_root=gsv_root_from_cfg(cfg), progress_range=(0.0, 0.05))
        need = {"paraformer" if checker.wants_paraformer(it.get("lang", "zh"), it.get("text", "")) else "whisper"
                for it in items}
        ok = []
        for name in sorted(need):
            try:
                ok.append(checker._load_paraformer() if name == "paraformer" else checker._load())
            except Exception:
                ok.append(False)
        if use_asr is None and not any(ok):
            checker = None

    real_emb: Dict[str, Dict[str, np.ndarray]] = {}
    real_voiced: Dict[str, float] = {}
    for it in items:
        _check_cancel()
        wav, sr = load_audio(project.abspath(it["path"]))
        real_emb[it["id"]] = sim.embed(wav, sr)
        real_voiced[it["id"]] = it.get("voiced") or speech_activity(wav, sr)[0]

    ckpts = backend.checkpoints() or [None]
    _p(0.05, "启动合成引擎（第一次大约 1~2 分钟）……", log_it=True)
    backend.start()
    tmp = project.cache_dir / "select"
    tmp.mkdir(parents=True, exist_ok=True)
    results: List[Dict[str, Any]] = []
    total_steps = max(1, len(ckpts) * len(items))
    step = 0
    log.info(f"共 {len(ckpts)} 个模型 × {len(items)} 句验证集，逐个试听（声纹模型：{'、'.join(sim.info()['labels'])}）")
    for j, ck in enumerate(ckpts):
        ck_id = (ck or {}).get("id", "当前模型")
        _p(0.10 + 0.90 * (j * len(items)) / total_steps, f"切换到模型 {ck_id}（第 {j + 1}/{len(ckpts)} 个）", log_it=True)
        if ck is not None:
            backend.use_checkpoint(ck)
        sims_c, sims_i, pcts, cers, ratios = [], [], [], [], {"zh": [], "en": []}
        for it in items:
            _check_cancel()
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
                _p(0.10 + 0.90 * step / total_steps, f"试听模型 {ck_id}：{step}/{total_steps}")
                continue
            gen_voiced = speech_activity(wav, sr)[0]
            wav, _, _ = trim_silence(wav, sr)
            cmp = sim.compare(sim.embed(wav, sr), real_emb[it["id"]])
            if cmp["to_voice"] is not None:
                sims_c.append(cmp["to_voice"])
            if cmp["to_real"] is not None:
                sims_i.append(cmp["to_real"])
            if cmp["pct"] is not None:
                pcts.append(cmp["pct"])
            if gen_voiced > 0.2 and real_voiced[it["id"]] > 0.2:
                ratios.setdefault(it["lang"], []).append(gen_voiced / real_voiced[it["id"]])
            if checker is not None:
                res = checker.check(wav, sr, it["text"], it["lang"])
                if res:
                    cers.append(res["cer"])
            _p(0.10 + 0.90 * step / total_steps, f"试听模型 {ck_id}：{step}/{total_steps}")
        if not sims_c:
            continue
        all_ratios = ratios["zh"] + ratios["en"]
        rhythm_dev = float(np.median([abs(math.log(r)) for r in all_ratios])) if all_ratios else 0.0
        entry = {
            "id": (ck or {}).get("id", "current"), "ckpt": ck,
            "speaker_sim": float(np.mean(sims_c)), "sim_to_real": float(np.mean(sims_i)) if sims_i else float(np.mean(sims_c)),
            "pct": round(float(np.mean(pcts)), 1) if pcts else None,
            "cer": float(np.mean(cers)) if cers else None, "rhythm_dev": rhythm_dev,
            "duration_ratio": {k: float(np.median(v)) for k, v in ratios.items() if v},
        }
        entry["total"] = entry["speaker_sim"] + entry["sim_to_real"] - 2.0 * (entry["cer"] or 0.0) - 0.8 * rhythm_dev
        results.append(entry)
        log.info(f"  {entry['id']}：" + (f"像你本人 {entry['pct']:.1f}% / " if entry["pct"] is not None else "")
                 + f"相似度 {entry['speaker_sim']:.3f} / 与原句 {entry['sim_to_real']:.3f}"
                 + (f" / 错字率 {entry['cer']:.1%}" if entry["cer"] is not None else "")
                 + f" / 节奏偏差 {rhythm_dev:.3f} → 综合 {entry['total']:.3f}")
    if not results:
        raise RuntimeError("所有模型都合成失败，请检查引擎日志")
    best = max(results, key=lambda e: e["total"])
    speed = {}
    for lang, ratio in best["duration_ratio"].items():
        # 模型读得比你慢（ratio>1）→ 加快；GPT-SoVITS 的 speed_factor>1 表示更快
        speed[lang] = round(float(np.clip(ratio, 0.8, 1.25)), 3) if abs(ratio - 1.0) > 0.03 else 1.0
    ranked = sorted(results, key=lambda e: -e["total"])
    info: Dict[str, Any] = {"speed": speed, "selection": {
        "evaluated_at": time.strftime("%Y-%m-%d %H:%M"), "items": len(items), "checkpoints": len(ckpts),
        "asr_check": checker is not None, "similarity": sim.info(),
        "results": [{k: v for k, v in r.items() if k != "ckpt"} for r in results],
        "ranking": [r["id"] for r in ranked], "best": best["id"]}}
    if best["ckpt"] is not None:
        info["selected"] = best["ckpt"]
        backend.use_checkpoint(best["ckpt"])
    project.update_models(backend.name, info)
    log.info(f"最佳模型：{best['id']}" + (f"（像你本人 {best['pct']:.1f}%）" if best.get("pct") is not None else "")
             + f"；语速校准：{speed or '无需调整'}")
    return info


def evaluate_file(cfg: Dict[str, Any], project: Project, audio: Path, text: str = "", lang: str = "") -> Dict[str, Any]:
    """评估任意一段音频有多像你（例如对比不同引擎/参数的效果），返回中文可读的结果。"""
    from voicetwin.eval.metrics import Scorer, pct_label, similarity_label
    from voicetwin.style.profile import target_rate
    from voicetwin.utils.textutil import detect_lang

    judge = None
    try:
        judge = SimilarityJudge.for_project(cfg, project)
        if not judge.available:
            judge = None
    except Exception as exc:
        log.warning(f"多模型声纹打分不可用：{exc}")
    encoder = get_speaker_encoder(cfg.get("speaker_encoder", "auto")) if judge is None else None
    cen = voice_centroid(project, encoder) if encoder is not None else None
    profile = project.load_profile()
    checker = CERChecker(cfg.get("synth", {}).get("asr_check_model", "auto"), vram_tier=_vram_tier(),
                         gsv_root=gsv_root_from_cfg(cfg)) if text else None
    wav, sr = load_audio(audio)
    wav, _, _ = trim_silence(wav, sr)
    lang = lang or (detect_lang(text) if text else "zh")
    scorer = Scorer(profile, cen, encoder, cfg.get("synth", {}).get("score"), checker, judge=judge)
    # 你自己上传的音频里的停顿是有意为之（段落、[停顿] 标记），这里不检查"异常停顿"；
    # 该检查只用于合成时给同一句话的多个候选打分。
    score = scorer.score(wav, sr, text or "", lang, use_asr=bool(text), check_pauses=False)
    first_model = judge.models[0] if judge is not None else encoder.name
    result: Dict[str, Any] = {
        "结论": pct_label(score.pct) if score.pct is not None else similarity_label(score.speaker_sim, first_model),
        "像你本人（%）": score.pct,
        "声纹相似度": None if score.speaker_sim is None else round(score.speaker_sim, 3),
        "相似度参考": "像你本人 ≥95% 非常像；85%~95% 比较像；75%~85% 有点像（不到 85% 就算不够像）；<75% 不太像（" + PCT_HELP + "）",
        "时长（秒）": round(len(wav) / sr, 1),
    }
    if judge is not None and score.sims:
        result["各声纹模型"] = {model_label(name): {"像你本人（%）": score.pcts.get(name),
                                                          "原始相似度": round(float(s), 3)}
                           for name, s in score.sims.items()}
    if score.rate:
        result["语速（音节/秒）"] = round(score.rate, 2)
        result["你本人的平均语速"] = round(target_rate(profile, lang), 2)
    if score.pitch_dev is not None:
        result["音高偏差"] = f"{score.pitch_dev * 12:.1f} 半音（越小越接近你本人）"
    if score.cer is not None:
        result["错字率"] = f"{score.cer:.1%}"
        result["识别出的文字"] = score.hyp
    result["提示"] = score.issues or ["无"]
    result["声纹模型"] = "、".join(judge.info()["labels"]) if judge is not None else encoder.name
    result["说明"] = HONEST_NOTE
    return result
