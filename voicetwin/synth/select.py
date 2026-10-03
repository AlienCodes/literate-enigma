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

import json
import math
import shutil
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

import numpy as np

from voicetwin.backends.base import Backend, SynthRequest
from voicetwin.data.exporters import validation_items
from voicetwin.data.references import pick_reference
from voicetwin.eval.metrics import CERChecker, Score
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

    def __init__(self, cfg: Dict[str, Any], project: Project, judge: Optional[SimilarityJudge] = None):
        """judge：已经加载好的声纹打分（「准备「一模一样」」时用生成引擎那一份，不再加载一遍）。"""
        self.judge: Optional[SimilarityJudge] = None
        try:
            judge = judge if judge is not None else SimilarityJudge.for_project(cfg, project)
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

    def compare(self, gen: Dict[str, np.ndarray], real: Dict[str, np.ndarray],
                seconds: Optional[float] = None) -> Dict[str, Optional[float]]:
        """返回 {'to_voice', 'to_real', 'pct', 'pct_raw', 'spread'}：to_* 已按每个模型自己的 p50 缩放（没校准时是原始余弦）；
        pct_raw 是没封顶的「像你本人」、spread 是几个声纹模型之间差多少（「一模一样」挑选用）。seconds：人声几秒（短句子的标准）。"""
        to_voice: List[float] = []
        to_real: List[float] = []
        pct = pct_raw = spread = None
        if self.judge is not None:
            res = self.judge.judge_embeddings(gen, seconds)
            pct, pct_raw, spread = res.get("pct"), res.get("pct_raw"), res.get("spread")
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
                "to_real": float(np.mean(to_real)) if to_real else None, "pct": pct, "pct_raw": pct_raw,
                "spread": spread}

    def info(self) -> Dict[str, Any]:
        if self.judge is not None:
            return self.judge.info()
        return {"models": [self.encoder.name], "labels": [model_label(self.encoder.name)],
                "reliable": bool(self.encoder.reliable), "calibration": {}, "definition": PCT_HELP, "note": HONEST_NOTE}


def _fatal(exc: BaseException) -> bool:
    """重试也没用的错误（显存不够、引擎起不来……，见 errors.FATAL_KEYS）。"""
    try:
        from voicetwin.errors import is_fatal

        return is_fatal(exc)
    except Exception:
        return False


def _asr_checker(cfg: Dict[str, Any], items: List[Dict[str, Any]], use_asr: Optional[bool],
                 progress: Optional[ProgressFn] = None) -> Optional[CERChecker]:
    """挑选时查错字用的识别模型。use_asr=None（自动）：一个识别模型都加载不了时不查（只按声纹和节奏挑）。"""
    if use_asr is False:
        return None
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
        return None
    return checker


def select_and_calibrate(cfg: Dict[str, Any], project: Project, backend: Backend, max_items: int = DEFAULT_ITEMS,
                         use_asr: Optional[bool] = None, progress: Optional[ProgressFn] = None,
                         all_checkpoints: bool = False) -> Dict[str, Any]:
    """用验证集挑最像你的模型并校准语速。all_checkpoints=True（「一模一样」训练）：第 4 轮以后存下的每个版本都试
    （GPT-SoVITS 的 checkpoints(all=True)），否则从早到晚均匀挑几个。"""
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
    checker = _asr_checker(cfg, items, use_asr, progress)

    real_emb: Dict[str, Dict[str, np.ndarray]] = {}
    real_voiced: Dict[str, float] = {}
    for it in items:
        _check_cancel()
        wav, sr = load_audio(project.abspath(it["path"]))
        real_emb[it["id"]] = sim.embed(wav, sr)
        real_voiced[it["id"]] = it.get("voiced") or speech_activity(wav, sr)[0]

    if all_checkpoints:
        try:
            ckpts = backend.checkpoints(all=True) or [None]  # type: ignore[call-arg]
        except TypeError:  # 这个引擎不分（只有一种挑法）
            ckpts = backend.checkpoints() or [None]
    else:
        ckpts = backend.checkpoints() or [None]
    hint = getattr(backend, "start_hint", lambda: "")()
    _p(0.05, "启动合成引擎" + (f"（{hint}）" if hint else "") + "……", log_it=True)
    backend.start()
    tmp = project.cache_dir / "select"
    tmp.mkdir(parents=True, exist_ok=True)
    results: List[Dict[str, Any]] = []
    asr_failed = False
    total_steps = max(1, len(ckpts) * len(items))
    step = 0
    log.info(f"共 {len(ckpts)} 个模型 × {len(items)} 句验证集，逐个试听（声纹模型：{'、'.join(sim.info()['labels'])}）")
    for j, ck in enumerate(ckpts):
        ck_id = (ck or {}).get("id", "当前模型")
        _p(0.10 + 0.90 * (j * len(items)) / total_steps, f"切换到模型 {ck_id}（第 {j + 1}/{len(ckpts)} 个）", log_it=True)
        if ck is not None:
            try:
                backend.use_checkpoint(ck)
            except Exception as exc:
                if _fatal(exc):  # 显存不够、引擎起不来……：后面的模型也一样，直接报出真正的原因
                    raise
                # 某一个模型文件坏了 / 读不了：跳过它，接着比别的，不要整个挑选都停下
                log.warning(f"  模型 {ck_id} 加载失败，跳过这个模型：{str(exc).splitlines()[0] if str(exc) else exc!r}")
                step += len(items)
                continue
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
                if _fatal(exc):  # 例如显存不够：每一句都会一样失败，不要白试完所有模型才说「都失败了」
                    raise
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
                try:
                    res = checker.check(wav, sr, it["text"], it["lang"])
                except Exception as exc:
                    # 识别校验只是帮着挑的（比如识别模型显存不够）：关掉它接着挑，不能让整个挑选停下
                    log.warning(f"⚠️ 识别校验出错了（{str(exc).splitlines()[0] if str(exc) else type(exc).__name__}），"
                                "这次只按声纹和节奏挑选（所有模型都不算错字率，比较才公平）")
                    checker, asr_failed, res = None, True, None
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
    if asr_failed:  # 有的模型算了错字率、有的没算：都不算，按同样的标准比
        for e in results:
            if e["cer"]:
                e["total"] += 2.0 * e["cer"]
            e["cer"] = None
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


# ============================================================================ 「一模一样」：深度挑选（设计方案 §1.3、§1.4、§2 P8）
#: 存在 cache/select_deep/ 里的每次请求的结果的格式；改了打分的算法就加 1（以前存下的作废、重新试）
DEEP_VERSION = 1
#: models.json 里 identical 这一块的格式
IDENTICAL_VERSION = 1
#: 种子：1234 + 第几句 × 7919 + 第几条参考 × 104729（每次挑选都一样，比较才公平，也能接着上次没做完的往下做）
SEED_BASE = 1234
ITEM_SEED_STEP = 7919
REF_SEED_STEP = 104729
#: 没能生成（出错、生成的是空的、几乎没有声音）的句子按这个分算：比任何真的生成出来的都差
FAIL_S = -3.0
#: 第一步、第二步各留几个
SCREEN_KEEP = 3
#: 第三步每句用几条参考录音
FINAL_REFS = 2
#: 第一、二步每句一次请求同时生成几个；第三步每句一共几个（= 2 条参考 × 每条 4 个）；检查用的句子几句（config.yaml 可改）
SCREEN_SEEDS = 2
FINAL_CANDIDATES = 8
TEST_TEXTS_N = 24
#: 没有按句子种类分的分数时（没有校准好的声纹模型），第 1、2 名「重新抽样里第 1 名更好」的比例不到这么多就算分不出来
TIE_P = 0.8
#: 语速重新校准：至少要几句没参加训练的录音；限制在多少之间；差不到 3% 就不调
SPEED_MIN_ITEMS = 8
SPEED_CLIP = (0.8, 1.25)
SPEED_DEADBAND = 0.03
#: 试听参考录音：原来分数最高的 24 条（同一个视频最多 3 条）× 6 句没参加训练的录音，每次同时生成 4 个
AUDITION_REFS = 24
AUDITION_PER_SOURCE = 3
AUDITION_ITEMS = 6
AUDITION_B = 4
#: 读错的字：平均错字率比读得最准的那个多 1 个百分点以上、并且超出误差范围，就不能排第一
CER_GATE = 0.01
NOTE_BIAS = "挑选和打分校准用的是同一批没参加训练的录音"
BIAS_LINE = "注意：挑选和打分校准用的是同一批没参加训练的录音，分数会偏乐观一点；最终请用耳朵听。"
#: 几乎一样高（综合分差不到这么多）时按时长、音调、读得准不准挑（和生成时一样）
TIE_EPS = 0.02


def _num(x: Any) -> Optional[float]:
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    return v if math.isfinite(v) else None


def _jsonable(x: Any) -> Any:
    """存进 json 的样子（numpy 的数换成普通的数，小数留 6 位）。"""
    if isinstance(x, dict):
        return {str(k): _jsonable(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_jsonable(v) for v in x]
    if isinstance(x, (bool, np.bool_)):
        return bool(x)
    if isinstance(x, (int, np.integer)):
        return int(x)
    if isinstance(x, (float, np.floating)):
        v = float(x)
        return round(v, 6) if math.isfinite(v) else None
    return x


def _first_line(exc: BaseException) -> str:
    text = str(exc).strip()
    return text.splitlines()[0][:200] if text else type(exc).__name__


def _paired_bootstrap(a: Sequence[float], b: Sequence[float], n: int = 2000, seed: int = 1234) -> float:
    """成对重新抽样（同一批句子）n 次：a 的平均比 b 高的比例（= P(a 更好)）。"""
    x = np.asarray(list(a), dtype=np.float64)
    y = np.asarray(list(b), dtype=np.float64)
    if x.size == 0 or x.size != y.size:
        return 0.5
    rng = np.random.default_rng(int(seed))
    idx = rng.integers(0, x.size, size=(int(n), x.size))
    d = (x[idx] - y[idx]).mean(axis=1)
    return float(np.mean(d > 0))


def _paired_ci(a: Sequence[float], b: Sequence[float], n: int = 2000, seed: int = 1234) -> Tuple[float, float]:
    """成对重新抽样的 a − b 的 95% 范围。"""
    x = np.asarray(list(a), dtype=np.float64)
    y = np.asarray(list(b), dtype=np.float64)
    if x.size == 0 or x.size != y.size:
        return (0.0, 0.0)
    rng = np.random.default_rng(int(seed))
    idx = rng.integers(0, x.size, size=(int(n), x.size))
    d = (x[idx] - y[idx]).mean(axis=1)
    lo, hi = np.percentile(d, [2.5, 97.5])
    return float(lo), float(hi)


# ---------------------------------------------------------------------------- 音调走向（DTW 对齐）
def _mfcc_f0(wav: np.ndarray, sr: int) -> Dict[str, Any]:
    """20 维 MFCC（10 ms 一帧）和同样的帧上的音高（半音；没声音的帧是 nan）。"""
    import librosa

    from voicetwin.style.prosody import f0_frames
    from voicetwin.utils.audio import resample

    w16 = resample(np.asarray(wav, dtype=np.float32), sr, 16000)
    mfcc = librosa.feature.mfcc(y=w16, sr=16000, n_mfcc=20, n_fft=512, hop_length=160)
    st = np.full(mfcc.shape[1], np.nan)
    times, f0 = f0_frames(w16, 16000)
    for t, f in zip(times, f0):
        i = int(round(float(t) / 0.01))
        if 0 <= i < st.size and f > 0:
            st[i] = 12.0 * math.log2(float(f) / 100.0)
    return {"mfcc": mfcc, "st": st}


def _f0_dtw(gen: Dict[str, Any], real: Dict[str, Any]) -> Tuple[Optional[float], Optional[float]]:
    """生成的和你的真实录音按 MFCC 做 DTW 对齐以后，沿对齐路径比音高：(皮尔逊相关系数 r_F0, 均方根差（半音）)。
    对齐上的有声帧不到 20 个时量不出来（None, None）。"""
    import librosa

    if gen["mfcc"].shape[1] < 2 or real["mfcc"].shape[1] < 2:
        return None, None
    _, wp = librosa.sequence.dtw(X=gen["mfcc"], Y=real["mfcc"], metric="cosine")
    wp = np.asarray(wp)[::-1]
    a = gen["st"][wp[:, 0]]
    b = real["st"][wp[:, 1]]
    ok = np.isfinite(a) & np.isfinite(b)
    if int(ok.sum()) < 20:
        return None, None
    a, b = a[ok], b[ok]
    rmse = float(np.sqrt(np.mean((a - b) ** 2)))
    if float(np.std(a)) < 1e-9 or float(np.std(b)) < 1e-9:
        return None, rmse
    return float(np.corrcoef(a, b)[0, 1]), rmse


# ---------------------------------------------------------------------------- 模型、参考录音
def _file_sig(path: Any) -> str:
    try:
        st = Path(str(path)).stat()
        return f"{st.st_size}-{st.st_mtime_ns}"
    except (OSError, ValueError):
        return "-"


def _weights_sig(backend: Backend, ckpt: Optional[Dict[str, Any]]) -> str:
    """一组模型文件的指纹（路径 + 大小 + 修改时间）：重新训练以后文件名一样、内容换了，以前存下的结果也不能用。"""
    if ckpt is None:
        try:
            return str(backend.model_id())
        except Exception:  # noqa: BLE001
            return backend.name
    paths = [str(ckpt.get(k)) for k in ("sovits", "gpt", "path") if ckpt.get(k)]
    from voicetwin.utils.textutil import short_hash

    return short_hash(backend.name, sorted(paths), [_file_sig(p) for p in sorted(paths)], n=16)


def _cid(ckpt: Optional[Dict[str, Any]]) -> str:
    return str((ckpt or {}).get("id") or "current")


def run_stamp(project: Project, backend: Backend) -> str:
    """这一次训练的指纹：训练时间、素材指纹、存下的模型列表（重新训练了就变）。没训练过的引擎是空的。"""
    from voicetwin.utils.textutil import short_hash

    entry = project.load_models().get(backend.name) or {}
    if not entry.get("trained_at") and not entry.get("sovits") and not entry.get("checkpoints"):
        return ""
    return short_hash(entry.get("trained_at"), entry.get("features_sha1"), sorted(entry.get("sovits") or []),
                      sorted(entry.get("gpt") or []), sorted(entry.get("checkpoints") or []), n=12)


def selected_stamp(backend: Backend, sel: Optional[Dict[str, Any]] = None) -> str:
    """现在选定的模型的指纹（换了模型、模型文件变了都会变）。"""
    sel = sel if sel is not None else backend.selected_checkpoint()
    return _weights_sig(backend, sel) if isinstance(sel, dict) and sel else ""


def _ensure_bank(project: Project, judge: Any, records: List[Dict[str, Any]],
                 progress: Optional[ProgressFn] = None) -> Optional[Dict[str, Any]]:
    """参考录音库（带声纹）：没有、不带声纹、声纹模型换了、能进库的录音变了（改了文字、删了片段……）就重新整理；
    声纹按片段缓存，只算新的。"""
    from voicetwin.data.references import build_reference_bank, eligible_signature, load_reference_bank

    bank = load_reference_bank(project)
    models = sorted(judge.models) if judge is not None and getattr(judge, "available", False) else []
    try:
        jsig = str(judge.signature()) if models else ""
    except Exception:  # noqa: BLE001
        jsig = ""
    stale = (bank is None or bank.get("eligible_sig") != eligible_signature(project, records)
             or (models and (sorted(bank.get("judge_models") or []) != models or str(bank.get("judge_sig") or "") != jsig)))
    if stale:
        build_reference_bank(project, records, judge=judge if models else None, progress=progress)
        bank = load_reference_bank(project)
    return bank


def _bank_pool(project: Project, bank: Optional[Dict[str, Any]], records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """能拿来当参考的录音：库里现在还能用的（片段还在、还用来训练、文字没改过）；一条都没有时用 references.json。"""
    from voicetwin.data.references import bank_eligible
    from voicetwin.synth import search as S

    by_id = {str(r.get("id")): r for r in records}
    pool = []
    for e in S.pool_from_bank(bank):
        r = by_id.get(str(e["id"]))
        if r is not None and bank_eligible(r) and str(r.get("text") or "").strip() == e["text"]:
            pool.append(e)
    if not pool:
        pool = S.pool_from_refs(project.load_references())
    return pool


# ---------------------------------------------------------------------------- 一句话、一次请求
@dataclass
class _Item:
    """挑选用的一句话：没参加训练的录音（val，有真实录音）或者检查用的句子（test，只有文字）。"""
    key: str
    id: str
    kind: str                    # val | test
    text: str
    lang: str
    group: str                   # mixed | zh | en（lang_groups.text_group）
    index: int
    w: float                     # 这一句的人声秒数（四项评分按它加权）：录音的实测值，检查用的句子按你的语速估
    real: Optional[Dict[str, Any]] = None      # 真实录音：emb（声纹）、voiced（人声秒数）、mfcc / st（音调走向）
    expected: Optional[float] = None           # 按你本人的语速这句话应该说多久（秒）
    refs: List[Dict[str, Any]] = field(default_factory=list)
    aux: Dict[str, List[Dict[str, Any]]] = field(default_factory=dict)

    @property
    def lang_eff(self) -> str:
        from voicetwin.utils.textutil import send_lang

        return send_lang(self.text, self.lang)


@dataclass
class _Job:
    stage: str
    ckpt: Optional[Dict[str, Any]]
    item: _Item
    ref: Dict[str, Any]
    ref_j: int
    aux: List[Dict[str, Any]]
    sampling: Dict[str, Any]
    n: int
    seed: int
    key: str = ""

    @property
    def cid(self) -> str:
        return _cid(self.ckpt)


class _DeepSelect:
    """深度挑选（和「准备「一模一样」」里的小校准）共用的东西：句子、参考录音、打分、请求的缓存、生成线程。"""

    def __init__(self, cfg: Dict[str, Any], project: Project, backend: Backend, progress: Optional[ProgressFn] = None,
                 max_items: int = DEFAULT_ITEMS, use_asr: Optional[bool] = None, judge: Any = None,
                 checker: Any = None, sim: Any = None):
        from voicetwin.synth.engine import QUALITY_PRESETS

        self.cfg, self.project, self.backend, self.progress = cfg, project, backend, progress
        self.max_items = int(max_items or DEFAULT_ITEMS)
        self.use_asr = use_asr
        self._judge_in, self._checker_in, self._sim_in = judge, checker, sim
        tcfg = dict((getattr(backend, "bcfg", {}) or {}).get("train") or {})
        self.n_test = max(0, self._int(tcfg.get("select_test_texts"), TEST_TEXTS_N))
        self.screen_b = max(1, self._int(tcfg.get("select_screen_seeds"), SCREEN_SEEDS))
        self.final_n = max(1, self._int(tcfg.get("select_final_candidates"), FINAL_CANDIDATES))
        preset = QUALITY_PRESETS["identical"]
        self.sampling = dict((preset.get("presets") or [{}])[0] or {"temperature": 1.0, "top_k": 15, "top_p": 1.0})
        thr = preset.get("cer_retry_threshold") or {}
        self.cer_thr = (float(thr.get("strong", 0.08)), float(thr.get("weak", 0.12)))
        sim_cfg = dict(cfg.get("similarity", {}) or {})
        self.min_pct = float(sim_cfg.get("min_pct", 85) or 85)
        self.min_wrong = int((cfg.get("synth", {}) or {}).get("min_wrong_chars", 2) or 0)
        self.asr_failed = False
        self.pipeline = _vram_tier() != "none"
        self.cache_dir = project.cache_dir / "select_deep"
        self.tmp: Optional[Path] = None
        self._loaded: Optional[str] = None
        self._broken: Dict[str, str] = {}
        self.stats = {"requests": 0, "cached": 0, "failed_requests": 0}

    @staticmethod
    def _int(v: Any, default: int) -> int:
        try:
            return int(v) if v not in (None, "", "auto") else default
        except (TypeError, ValueError):
            return default

    def _p(self, frac: float, msg: str, log_it: bool = False) -> None:
        if log_it:
            log.info(msg)
        if self.progress is not None:
            try:
                self.progress(max(0.0, min(1.0, frac)), msg)
            except Exception:  # noqa: BLE001 - 进度条出问题不能打断挑选（停止按钮是 BaseException，照常传出去）
                pass

    # ------------------------------------------------------------------ 准备
    def load(self, with_tests: bool = True, lo: float = 0.0, hi: float = 0.05, bank_msg: str = "",
             group_calib: bool = True) -> None:
        """加载打分模型、你本人的说话习惯、参考录音库、按句子种类的校准、你素材里各类句子的比例、要试的句子。
        group_calib=False（生成前的小校准只有一个模型、不排名次）：不按句子种类校准，省时间。"""
        from voicetwin.eval import lang_groups as LG
        from voicetwin.eval.identical_judge import IdenticalScorer
        from voicetwin.style.twin_profile import build_twin_profile, load_twin_profile
        from voicetwin.synth import search as S

        def sub(a: float, b: float) -> ProgressFn:
            return lambda f, m: self._p(lo + (hi - lo) * (a + (b - a) * max(0.0, min(1.0, f))), (bank_msg or "") + m)

        val = validation_items(self.project, limit=self.max_items)
        if not val and not with_tests:
            self.items = []
            return
        if not val:
            raise RuntimeError("没有没参加训练的录音（验证集），没法按「一模一样」的方式挑选")
        self._p(lo, "加载声纹和识别模型（第一次使用会先下载）……", log_it=True)
        self.sim = self._sim_in if self._sim_in is not None else _Sim(self.cfg, self.project, judge=self._judge_in)
        if self._checker_in is not None and self.use_asr is not False:
            self.checker = self._checker_in
        else:
            self.checker = _asr_checker(self.cfg, val, self.use_asr, None)
        try:
            twin = build_twin_profile(self.project)
        except Exception as exc:  # noqa: BLE001 - 停止按钮不是 Exception，照常传出去
            log.warning(f"你本人的说话习惯这次没量出来（{_first_line(exc)}），语速按以前的方式比")
            twin = None
        self.twin = twin or load_twin_profile(self.project) or {}
        records = self.project.load_manifest()
        judge = self.sim.judge
        try:
            bank = _ensure_bank(self.project, judge, records, progress=sub(0.1, 0.6))
        except Exception as exc:  # noqa: BLE001
            log.warning(f"参考录音库这次没整理好（{_first_line(exc)}），用以前挑好的参考录音")
            bank = None
        self.pool = _bank_pool(self.project, bank, records)
        self.bank_sig = S.pool_signature(self.pool, bank)
        self.prior = S.prior_scores(self.pool, None)
        self.calib = LG.build_group_calibration(self.project, judge, progress=sub(0.6, 0.9)) \
            if (judge is not None and group_calib) else {"ok": False, "groups": {}}
        self.shares = LG.material_shares(self.project.load_manifest(only_kept=True))
        # 挑选时生成的打分用默认的排序权重（不用上次校准的）：挑选的结果不受上次校准影响，存下的结果下次也接着能用；
        # 校准是在这次挑选之后、用这次的版本做的
        self.rank_weights: Dict[str, Any] = {}
        self.weights_version = "default"
        self.scorer = IdenticalScorer(self.project.load_profile(), self.sim.cen, self.sim.encoder,
                                      (self.cfg.get("synth", {}) or {}).get("score"), self.checker, judge=judge,
                                      twin=self.twin, rank_weights=self.rank_weights)
        try:
            self.judge_sig = str(judge.signature()) if judge is not None else str(getattr(self.sim.encoder, "name", ""))
        except Exception:  # noqa: BLE001
            self.judge_sig = ""
        self.twin_sig = str(self.twin.get("signature") or "")
        self.items = [self._val_item(r, k) for k, r in enumerate(val)]
        self.items = [it for it in self.items if it is not None]
        if with_tests:
            from voicetwin.synth.probe_texts import probe_items

            base = len(self.items)
            for k, t in enumerate(probe_items(self.n_test)):
                self.items.append(self._test_item(t, base + k))
        for it in self.items:
            self._shortlist(it)
        self._p(hi, f"要试的句子：没参加训练的录音 {sum(1 for i in self.items if i.kind == 'val')} 句、"
                    f"检查用的句子 {sum(1 for i in self.items if i.kind == 'test')} 句", log_it=True)

    def _val_item(self, r: Dict[str, Any], index: int) -> Optional[_Item]:
        from voicetwin.eval import lang_groups as LG

        try:
            wav, sr = load_audio(self.project.abspath(r["path"]))
        except Exception as exc:  # noqa: BLE001 - 读不了的录音不用
            log.warning(f"没参加训练的录音 {r.get('id')} 读不了，这句不用：{_first_line(exc)}")
            return None
        _check_cancel()
        voiced = float(r.get("voiced") or speech_activity(wav, sr)[0])
        real: Dict[str, Any] = {"emb": self.sim.embed(wav, sr), "voiced": voiced}
        try:
            real.update(_mfcc_f0(wav, sr))
        except Exception as exc:  # noqa: BLE001 - 音调走向量不出来：这一项不算
            log.debug(f"{r.get('id')} 的音调走向量不出来：{exc}")
        text = str(r.get("text") or "")
        return _Item(key=f"v:{r['id']}", id=str(r["id"]), kind="val", text=text, lang=str(r.get("lang") or "zh"),
                     group=LG.text_group(text) or "zh", index=index, w=max(0.2, voiced), real=real)

    def _test_item(self, t: Dict[str, str], index: int) -> _Item:
        from voicetwin.eval import lang_groups as LG
        from voicetwin.utils.textutil import syllable_count

        exp = self.scorer.expected(t["text"], t.get("lang", "zh"))
        w = float(exp) if exp else max(0.2, 0.25 * syllable_count(t["text"]))
        return _Item(key=f"t:{t['id']}", id=str(t["id"]), kind="test", text=t["text"], lang=t.get("lang", "zh"),
                     group=LG.text_group(t["text"]) or "zh", index=index, w=w, expected=exp)

    def _shortlist(self, it: _Item) -> None:
        """这句话用哪两条参考录音（不用它自己的录音、不用文字一样的）、每条配哪几条辅助参考。"""
        from types import SimpleNamespace

        from voicetwin.synth import search as S
        from voicetwin.utils.textutil import sentence_kind

        pool = [e for e in self.pool if str(e["id"]) != it.id]
        seg = SimpleNamespace(text=it.text, kind=sentence_kind(it.text), pause_after="sentence", lang=it.lang)
        refs = S.shortlist_refs(seg, pool, self.prior, FINAL_REFS)
        if not refs:
            refs = pool[:FINAL_REFS]
        if not refs:
            raise RuntimeError("没有可以当参考的录音（参考录音库和 references.json 都是空的）")
        it.refs = refs
        n_aux = 3 if getattr(self.backend, "supports_aux_refs", False) else 0
        it.aux = {str(r["id"]): S.aux_set(r, pool, self.prior, n_aux) for r in refs}

    # ------------------------------------------------------------------ 请求
    def _key(self, job: _Job) -> str:
        from voicetwin.utils.textutil import short_hash

        r = job.ref
        return short_hash(DEEP_VERSION, _weights_sig(self.backend, job.ckpt), job.item.key, job.item.text, job.item.lang,
                          job.seed, str(r.get("id")), str(r.get("text") or ""), r.get("trim"),
                          [str(a.get("id")) for a in job.aux], sorted(job.sampling.items()), job.n, 1.0,
                          self.judge_sig, self.twin_sig, self.weights_version,
                          self.checker is not None and not self.asr_failed, n=20)

    def job(self, stage: str, ckpt: Optional[Dict[str, Any]], it: _Item, ref_j: int, n: int,
            ref: Optional[Dict[str, Any]] = None, aux: Optional[List[Dict[str, Any]]] = None) -> _Job:
        ref = ref if ref is not None else it.refs[min(ref_j, len(it.refs) - 1)]
        if aux is None:
            aux = it.aux.get(str(ref["id"])) or []
        seed = SEED_BASE + it.index * ITEM_SEED_STEP + ref_j * REF_SEED_STEP
        j = _Job(stage=stage, ckpt=ckpt, item=it, ref=ref, ref_j=ref_j, aux=list(aux), sampling=dict(self.sampling),
                 n=max(1, int(n)), seed=int(seed))
        j.key = self._key(j)
        return j

    def _cache_path(self, key: str) -> Path:
        return self.cache_dir / key[:2] / f"{key}.json"

    def _cache_get(self, key: str) -> Optional[Dict[str, Any]]:
        path = self._cache_path(key)
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return None
        return data if isinstance(data, dict) and data.get("version") == DEEP_VERSION else None

    def _cache_put(self, key: str, rec: Dict[str, Any]) -> None:
        from voicetwin.utils import atomic

        path = self._cache_path(key)
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            atomic.write_text(path, json.dumps(_jsonable(dict(rec, version=DEEP_VERSION)), ensure_ascii=False))
        except Exception as exc:  # noqa: BLE001 - 存不了：这次照样用，只是下次不能接着用
            log.debug(f"挑选的结果存不了：{exc}")

    def _work(self, job: _Job) -> Dict[str, Any]:
        """真正发请求（生成线程里；没有 N 卡时在主线程里）：要换模型就先换（同一组模型的请求排在一起，换得最少）。
        重试也没用的错误（显存不够、引擎起不来……）照常抛出；别的错误这一次算没生成出来。"""
        try:
            if job.ckpt is not None and job.cid != self._loaded:
                if job.cid in self._broken:
                    raise RuntimeError(self._broken[job.cid])
                try:
                    self.backend.use_checkpoint(job.ckpt)
                except Exception as exc:
                    if _fatal(exc):
                        raise
                    self._broken[job.cid] = f"模型 {job.cid} 加载失败：{_first_line(exc)}"
                    log.warning(f"  {self._broken[job.cid]}（这个模型按最差算）")
                    raise RuntimeError(self._broken[job.cid]) from exc
                self._loaded = job.cid
            it = job.item
            ref_audio = self._audio(job.ref)
            req = SynthRequest(text=it.text, lang=it.lang, ref_audio=ref_audio, ref_text=str(job.ref.get("text") or ""),
                               ref_lang=str(job.ref.get("lang") or "zh"), aux_refs=[self._audio(a) for a in job.aux],
                               seed=job.seed, speed=1.0, temperature=job.sampling.get("temperature"),
                               top_k=job.sampling.get("top_k"), top_p=job.sampling.get("top_p"))
            assert self.tmp is not None
            files = self.backend.synthesize_many(req, job.n, self.tmp)
            return {"files": [(str(p), int(r)) for p, r in (files or [])]}
        except Exception as exc:
            if _fatal(exc):
                raise
            return {"error": _first_line(exc)}

    def _audio(self, e: Dict[str, Any]) -> Path:
        from voicetwin.data.references import bank_wav

        return bank_wav(self.project, e) if e.get("_bank") else self.project.abspath(e["path"])

    def _absorb(self, job: _Job, out: Dict[str, Any]) -> Dict[str, Any]:
        """读生成的声音、打分（主线程，生成线程同时在做下一个请求），删掉临时文件。"""
        if out.get("error"):
            self.stats["failed_requests"] += 1
            log.warning(f"  {job.cid} 第 {job.item.index + 1} 句没能生成：{out['error']}")
            return {"error": str(out["error"]), "rows": []}
        rows = []
        for path, row in sorted(out.get("files") or [], key=lambda f: f[1]):
            try:
                wav, sr = load_audio(path)
            except Exception as exc:  # noqa: BLE001
                log.debug(f"读不了生成的声音：{exc}")
                continue
            finally:
                try:
                    Path(path).unlink()
                except OSError:
                    pass
            if wav.size == 0:
                continue
            try:
                m = self.measure(job.item, wav, sr, job.stage)
            except Exception as exc:  # noqa: BLE001 - 打分出错（不是模型的问题）：这一个不算
                log.warning(f"  第 {job.item.index + 1} 句有一个版本打不了分：{_first_line(exc)}")
                continue
            rows.append({"row": int(row), "m": m})
        if not rows:
            self.stats["failed_requests"] += 1
        return {"error": None if rows else "生成的声音是空的", "rows": rows}

    def measure(self, it: _Item, wav: np.ndarray, sr: int, stage: str) -> Dict[str, Any]:
        """给一个版本打分：生成时用的打分（不看你的真实录音：综合分、像你本人、错字、长短）和真实答案（和你那句录音比：
        声纹、长短、音调走向；只有没参加训练的录音才有）。每个声纹模型各自的分数也记下（四项评分按句子种类校准用）。"""
        from voicetwin.eval import lang_groups as LG

        sc = self.scorer
        prepared = sc.prepare(wav, sr)
        use_asr = self.checker is not None and not self.asr_failed
        try:
            s = sc.full(wav, sr, it.text, it.lang_eff, 1.0, prepared=prepared, use_asr=use_asr)
        except Exception as exc:
            if not use_asr:
                raise
            # 识别校验（查错字）只是帮着挑的：它出错时关掉，所有模型都不算错字率（比较才公平）
            log.warning(f"⚠️ 识别校验出错了（{_first_line(exc)}），这次只按声纹和节奏挑选（所有模型都不算错字率）")
            self.asr_failed = True
            sc.cer_checker = None
            s = sc.full(wav, sr, it.text, it.lang_eff, 1.0, prepared=prepared, use_asr=False)
        embs = dict((prepared or {}).get("embs") or {}) if isinstance(prepared, dict) else {}
        seconds = prepared.get("seconds") if isinstance(prepared, dict) else None
        raws = LG.member_raws(self.sim.judge, embs, seconds) if self.sim.judge is not None else {}
        m: Dict[str, Any] = {"total": s.total, "timbre": sc.timbre_term(s), "pct": s.pct, "pct_raw": s.pct_raw,
                             "spread": s.spread, "sim": s.speaker_sim, "cer": s.cer, "errors": s.errors,
                             "checker": s.checker, "voiced": s.voiced, "expected": s.expected, "dur_dev": s.dur_dev,
                             "silent": "几乎没有声音" in (s.issues or []), "raws": raws, "seconds": seconds}
        if it.real is not None:
            gen = embs if embs else self.sim.embed(wav, sr)
            m["to_real"] = self.sim.compare(gen, it.real["emb"], seconds)["to_real"]
            rv = float(it.real.get("voiced") or 0.0)
            v = float(s.voiced or 0.0)
            m["dur_ratio"] = v / rv if v >= 0.2 and rv >= 0.2 else None
            m["r_f0"] = m["f0_rmse"] = None
            if stage != "AU" and "mfcc" in it.real:
                try:
                    m["r_f0"], m["f0_rmse"] = _f0_dtw(_mfcc_f0(wav, sr), it.real)
                except Exception as exc:  # noqa: BLE001 - 量不出来就不算这一项
                    log.debug(f"音调走向量不出来：{exc}")
            if stage == "C":  # 排序权重的校准要用（只用第三步的版本）
                try:
                    m["prosody_z"], m["ltas_d"] = sc._shape(wav, sr, it.text)
                except Exception as exc:  # noqa: BLE001
                    log.debug(f"音调起伏 / 频谱量不出来：{exc}")
        return _jsonable(m)

    def run_jobs(self, jobs: List[_Job], lo: float, hi: float, label: str) -> Dict[str, Dict[str, Any]]:
        """按顺序发这些请求（以前做过的直接用存下的结果），生成线程发请求、主线程同时给上一个打分。"""
        from voicetwin.synth.search import _Producer

        recs: Dict[str, Dict[str, Any]] = {}
        todo: List[_Job] = []
        seen: set = set()
        for j in jobs:
            if j.key in seen:
                continue
            seen.add(j.key)
            hit = self._cache_get(j.key)
            if hit is not None:
                recs[j.key] = hit
            else:
                todo.append(j)
        self.stats["cached"] += len(seen) - len(todo)
        self.stats["requests"] += len(todo)
        if not jobs:
            return recs
        producer = None
        self.tmp = self.cache_dir / f"tmp_{uuid.uuid4().hex[:8]}"
        self.tmp.mkdir(parents=True, exist_ok=True)
        try:
            if todo and self.pipeline:
                producer = _Producer(self._work)
                producer.start()
                for j in todo:
                    producer.submit(j)
            n = len(jobs)
            last_cid: Optional[str] = None
            for i, j in enumerate(jobs):
                _check_cancel()
                if j.ckpt is not None and j.cid != last_cid:  # 同一组模型的请求排在一起：换到下一组时说一声
                    last_cid = j.cid
                    self._p(lo + (hi - lo) * i / n, f"{label}：切换到模型 {j.cid}")
                if j.key not in recs:
                    if producer is not None:
                        job, out = producer.get(_check_cancel)
                        assert job is j
                    else:
                        out = self._work(j)
                    rec = self._absorb(j, out)
                    self._cache_put(j.key, rec)
                    recs[j.key] = rec
                self._p(lo + (hi - lo) * (i + 1) / n, f"{label}……{i + 1}/{n}")
        finally:
            if producer is not None:
                producer.close()
            shutil.rmtree(self.tmp, ignore_errors=True)
        return recs

    # ------------------------------------------------------------------ 一句话的分数
    def rows(self, rec: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return [r["m"] for r in (rec or {}).get("rows") or [] if isinstance(r, dict) and isinstance(r.get("m"), dict)]

    def item_S(self, it: _Item, m: Optional[Dict[str, Any]], w_t: float = 1.0, w_c: float = 3.0) -> float:
        """一句话的分数（设计方案 §1.3）：没参加训练的录音 S = T + R_real − 3·错字率 − 0.8·|ln 长短比| − 0.3·(1 − r_F0)；
        检查用的句子 S = T − 3·错字率 − 0.8·|ln(说话时长 / 按你的语速应该说多久)|。T 是「像你本人」那一项（按句子种类校准、
        封顶在你自己录音的 p90、减去模型之间的差别）。没能生成 / 几乎没有声音：−3。"""
        from voicetwin.eval import lang_groups as LG

        if m is None or m.get("silent"):
            return FAIL_S
        g_raw = LG.calibrated_raw(m.get("raws") or {}, it.group, self.calib)
        sc = Score(total=0.0, pct_raw=g_raw if g_raw is not None else m.get("pct_raw"), spread=m.get("spread"),
                   pct=m.get("pct"), speaker_sim=m.get("sim"))
        val = w_t * float(self.scorer.timbre_term(sc))
        if not self.asr_failed and m.get("cer") is not None:
            val -= w_c * float(m["cer"])
        if it.real is not None:
            val += float(m.get("to_real") or 0.0)
            ratio = _num(m.get("dur_ratio"))
            if ratio:
                val -= 0.8 * abs(math.log(ratio))
            r = _num(m.get("r_f0"))
            if r is not None:
                val -= 0.3 * (1.0 - r)
        else:
            exp, v = _num(m.get("expected")), _num(m.get("voiced"))
            if exp and v and v >= 0.2:
                val -= 0.8 * abs(math.log(v / exp))
        return float(val)

    def item_pct(self, it: _Item, m: Optional[Dict[str, Any]]) -> Optional[float]:
        """四项评分用的「像你本人 %」（按句子种类校准）；没能生成算 0，量不出来（没有声纹打分）是 None。"""
        from voicetwin.eval import lang_groups as LG

        if self.sim.judge is None:
            return None
        if m is None or m.get("silent"):
            return 0.0
        return LG.calibrated_pct(m.get("raws") or {}, it.group, self.calib)

    def item_cer(self, m: Optional[Dict[str, Any]]) -> Optional[float]:
        if self.checker is None or self.asr_failed:
            return None
        if m is None or m.get("silent"):
            return 1.0
        return _num(m.get("cer"))

    def _cer_ok(self, m: Dict[str, Any]) -> bool:
        from voicetwin.eval.metrics import engine_is_strong

        c = _num(m.get("cer"))
        if c is None or self.asr_failed:
            return True
        if self.min_wrong > 1 and m.get("errors") is not None and int(m["errors"]) < self.min_wrong:
            return True
        return c <= (self.cer_thr[0] if engine_is_strong(str(m.get("checker") or "")) else self.cer_thr[1])

    def pick(self, rows: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """和生成时一样挑（不看你的真实录音）：几乎没声音的不要；不够像（< 85%，可靠的声纹打分时）的排后面；
        读对的 > 综合分高的；综合分差不到 0.02 时按时长、音调、读得准不准挑。"""
        alive = [m for m in rows if not m.get("silent")]
        if not alive:
            return None
        judge = self.sim.judge
        if judge is not None and getattr(judge, "calibrated", False) and getattr(judge, "reliable", False):
            alive = [m for m in alive if m.get("pct") is None or float(m["pct"]) >= self.min_pct] or alive
        top = max(alive, key=lambda m: (self._cer_ok(m), float(m["total"])))
        ok = self._cer_ok(top)
        group = [m for m in alive if self._cer_ok(m) == ok and float(m["total"]) >= float(top["total"]) - TIE_EPS]
        return max(group, key=lambda m: (round(float(m["total"]) - float(m.get("timbre") or 0.0), 9), float(m["total"])))

    # ------------------------------------------------------------------ 第一、二步：粗筛
    def screen(self, stage: str, combos: List[Optional[Dict[str, Any]]], lo: float, hi: float, label: str,
               w_t: float, w_c: float) -> List[Dict[str, Any]]:
        """每个模型 × 每句 × 一次请求（同时生成 2 个）；每句的分数是这几个版本的平均（没能生成的按最差算）；
        模型的分数 = 各类句子的平均按你素材里的时间比例加权（和综合总评分一样的比例）。"""
        from voicetwin.eval import lang_groups as LG

        jobs = {(_cid(c), it.key): self.job(stage, c, it, 0, self.screen_b) for c in combos for it in self.items}
        recs = self.run_jobs(list(jobs.values()), lo, hi, label)
        out = []
        for c in combos:
            by_group: Dict[str, List[float]] = {}
            failed = 0
            for it in self.items:
                rows = self.rows(recs.get(jobs[(_cid(c), it.key)].key))
                if not rows or all(m.get("silent") for m in rows):
                    failed += 1
                vals = [self.item_S(it, m, w_t, w_c) for m in rows] or [FAIL_S]
                by_group.setdefault(it.group, []).append(float(np.mean(vals)))
            weights, _ = LG.composite_weights(self.shares.get("shares"), by_group.keys(),
                                              fallback={g: float(len(v)) for g, v in by_group.items()})
            score = float(sum(weights[g] * float(np.mean(by_group[g])) for g in weights)) if weights else FAIL_S
            out.append({"id": _cid(c), "ckpt": c, "score": round(score, 4), "failed": failed, "n_items": len(self.items),
                        "by_group": {g: round(float(np.mean(v)), 4) for g, v in by_group.items()}})
        return out

    # ------------------------------------------------------------------ 第三步：按「一模一样」的方式比
    def final(self, combos: List[Optional[Dict[str, Any]]], lo: float, hi: float, label: str) -> List[Dict[str, Any]]:
        """每个模型 × 每句 × 2 条参考录音 × 每条同时生成 4 个；生成时的打分（不看你的真实录音）挑一个，再拿挑出来的
        那个和你的真实录音比（这才是真的「像不像」）。"""
        per_ref = max(1, self.final_n // FINAL_REFS)
        jobs: Dict[Tuple[str, str], List[_Job]] = {}
        for c in combos:
            for it in self.items:
                jobs[(_cid(c), it.key)] = [self.job("C", c, it, j, per_ref) for j in range(min(FINAL_REFS, len(it.refs)))]
        recs = self.run_jobs([j for js in jobs.values() for j in js], lo, hi, label)
        out = []
        for c in combos:
            per_item: Dict[str, Dict[str, Any]] = {}
            for it in self.items:
                rows = [m for j in jobs[(_cid(c), it.key)] for m in self.rows(recs.get(j.key))]
                chosen = self.pick(rows)
                per_item[it.key] = {"S": self.item_S(it, chosen), "pct": self.item_pct(it, chosen),
                                    "cer": self.item_cer(chosen), "group": it.group, "w": it.w, "kind": it.kind,
                                    "lang": it.lang, "failed": chosen is None, "rows": rows,
                                    "ratio": _num((chosen or {}).get("dur_ratio"))}
            out.append(self.summarize(c, per_item))
        return out

    def summarize(self, c: Optional[Dict[str, Any]], per_item: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """一个模型的实测结果：S 的平均 ± 标准误差、句数、每句几次请求、两类句子分开的平均、错字率、四项评分。"""
        from voicetwin.eval import lang_groups as LG

        S_all = [float(v["S"]) for v in per_item.values()]
        val = [float(v["S"]) for v in per_item.values() if v["kind"] == "val"]
        test = [float(v["S"]) for v in per_item.values() if v["kind"] == "test"]
        cers = [float(v["cer"]) for v in per_item.values() if v.get("cer") is not None]
        four = LG.group_scores([{"key": k, "group": v["group"], "pct": v["pct"], "w": v["w"]} for k, v in per_item.items()],
                               self.shares.get("shares"))
        se = float(np.std(S_all, ddof=1) / math.sqrt(len(S_all))) if len(S_all) > 1 else None
        comp = four.get("composite") or {}
        return {"id": _cid(c), "ckpt": c, "previous": bool((c or {}).get("previous")),
                "pct": comp.get("mean") if comp.get("status") == "ok" else None, "four": four,
                "cer": round(float(np.mean(cers)), 4) if cers else None,
                "total": round(float(np.mean(S_all)), 4) if S_all else FAIL_S, "se": None if se is None else round(se, 4),
                "n_items": len(S_all), "n_seeds": FINAL_REFS,
                "val_mean": round(float(np.mean(val)), 4) if val else None,
                "test_mean": round(float(np.mean(test)), 4) if test else None,
                "failed": sum(1 for v in per_item.values() if v["failed"]), "per_item": per_item}

    # ------------------------------------------------------------------ 排名
    def rank(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        return rank_results(results)

    # ------------------------------------------------------------------ 语速、权重、参考录音
    def speed(self, result: Dict[str, Any]) -> Tuple[Dict[str, float], Dict[str, Any]]:
        """语速重新校准：第 1 名在没参加训练的录音上，生成的说话时长 / 你本人的说话时长（第三步的全部版本；只用挑出来的那个
        会偏向你平时的语速——挑的时候本来就按「接近你平时的长短」挑）。每种语言至少 8 句才调，限制在 0.8~1.25，差不到 3% 不调。"""
        by_lang: Dict[str, List[float]] = {}
        n_items: Dict[str, int] = {}
        for k, v in result["per_item"].items():
            if v["kind"] != "val":
                continue
            lang = "en" if v.get("lang") == "en" else "zh"
            n_items.setdefault(lang, 0)
            ratios = [float(m["dur_ratio"]) for m in v.get("rows") or [] if _num(m.get("dur_ratio")) and not m.get("silent")]
            if ratios:
                n_items[lang] += 1
                by_lang.setdefault(lang, []).extend(ratios)
        speed: Dict[str, float] = {}
        info: Dict[str, Any] = {"n_items": dict(n_items), "median": {}}
        for lang in sorted(n_items) or ["zh"]:
            vals = by_lang.get(lang) or []
            if n_items.get(lang, 0) < SPEED_MIN_ITEMS or not vals:
                speed[lang] = 1.0
                continue
            med = float(np.median(vals))
            info["median"][lang] = round(med, 4)
            speed[lang] = round(float(np.clip(med, *SPEED_CLIP)), 3) if abs(med - 1.0) > SPEED_DEADBAND else 1.0
        return speed, info

    def calibration(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """排序权重（calibrate_rank）：第三步里每个模型、每句没参加训练的录音生成的几个版本。"""
        from voicetwin.synth import calibrate_rank

        groups: Dict[str, List[Dict[str, Any]]] = {}
        for r in results:
            for k, v in r["per_item"].items():
                if v["kind"] != "val":
                    continue
                cands = [dict(m, item=k) for m in v.get("rows") or [] if not m.get("silent")]
                if cands:
                    groups[f"{r['id']}|{k}"] = cands
        try:
            return calibrate_rank.calibrate(groups, cap_value=self.scorer.cap)
        except Exception as exc:  # noqa: BLE001 - 校准不了：照旧用默认权重
            log.warning(f"排序权重这次没校准（{_first_line(exc)}），照旧用默认的")
            return {"weights": {}, "version": "default", "gain": None, "adopted": False, "why": _first_line(exc)}

    def audition(self, ckpt: Optional[Dict[str, Any]], lo: float, hi: float, label: str) -> Dict[str, Any]:
        """试听参考录音：原来分数最高的 24 条（同一个视频最多 3 条）× 6 句没参加训练的录音（均匀挑，不用参考自己的录音）
        × 一次请求同时生成 4 个；真实答案 = R_real − 2·错字率 − 0.8·|ln 长短比|，每句取 4 个里最好的，再对 6 句取平均
        = 这条参考的「先验」。没参加训练的录音不到 6 句时不做。"""
        from voicetwin.eval.speaker import spread_sample
        from voicetwin.synth import search as S

        val = [it for it in self.items if it.kind == "val" and it.real is not None]
        if len(val) < AUDITION_ITEMS:
            return {"prior": None, "skipped": f"没参加训练的录音只有 {len(val)} 句（至少要 {AUDITION_ITEMS} 句）",
                    "n_refs": 0, "n_items": len(val), "requests": 0}
        bank = [e for e in self.pool if e.get("_bank")] or list(self.pool)
        refs: List[Dict[str, Any]] = []
        per_src: Dict[str, int] = {}
        for e in sorted(bank, key=lambda e: (-float(e.get("base") or 0.0), str(e["id"]))):
            src = str(e.get("source") or "")
            if per_src.get(src, 0) >= AUDITION_PER_SOURCE:
                continue
            refs.append(e)
            per_src[src] = per_src.get(src, 0) + 1
            if len(refs) >= AUDITION_REFS:
                break
        items = spread_sample(val, AUDITION_ITEMS)
        base_prior = S.prior_scores(self.pool, None)
        n_aux = 3 if getattr(self.backend, "supports_aux_refs", False) else 0
        from voicetwin.utils.textutil import normalize_for_cer

        jobs: List[Tuple[Dict[str, Any], _Item, _Job]] = []
        for r_i, ref in enumerate(refs):  # 同一条参考的排在一起（引擎可以接着用算好的参考特征）
            aux = S.aux_set(ref, self.pool, base_prior, n_aux)
            for it in items:
                if str(ref["id"]) == it.id or normalize_for_cer(str(ref.get("text") or "")) == normalize_for_cer(it.text):
                    continue
                jobs.append((ref, it, self.job("AU", ckpt, it, r_i, AUDITION_B, ref=ref, aux=aux)))
        recs = self.run_jobs([j for _, _, j in jobs], lo, hi, label)
        truth: Dict[str, List[float]] = {}
        for ref, it, j in jobs:
            best = FAIL_S
            for m in self.rows(recs.get(j.key)):
                if m.get("silent"):
                    continue
                v = float(m.get("to_real") or 0.0)
                if not self.asr_failed and m.get("cer") is not None:
                    v -= 2.0 * float(m["cer"])
                ratio = _num(m.get("dur_ratio"))
                if ratio:
                    v -= 0.8 * abs(math.log(ratio))
                best = max(best, v)
            truth.setdefault(str(ref["id"]), []).append(best)
        prior = {k: round(float(np.mean(v)), 5) for k, v in truth.items() if v}
        from voicetwin.utils.textutil import short_hash

        return {"prior": prior, "version": "aud-" + short_hash(sorted(prior.items()), n=10) if prior else "",
                "n_refs": len(refs), "n_items": len(items), "requests": len(jobs)}


# ---------------------------------------------------------------------------- 排名
def rank_results(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """排名（老师 10-04 定的规则）：综合总评分高的排前；读错字明显多的不能当第一；任何一类句子明显比别的模型差
    （超出误差范围）、又没有哪一类明显更好的，不能当第一；第 1、2 名的综合总评分差别在误差范围内 → 分不出来，两个都留着；
    第 2 名有一类句子明显更好 → 各有长处，两个都留着。没有四项评分（没有校准好的声纹模型）时按 S 的平均排，
    成对重新抽样里第 1 名更好的比例不到 0.8 算分不出来。"""
    from voicetwin.eval import lang_groups as LG

    def items_of(r: Dict[str, Any], key: str) -> List[Dict[str, Any]]:
        return [{"key": k, "group": v["group"], "pct": v[key] if key != "S" else v["S"], "w": v["w"]}
                for k, v in r["per_item"].items()]

    four_ok = any(((r.get("four") or {}).get("composite") or {}).get("status") == "ok" for r in results)
    weights: Dict[str, float] = {}
    w_source = ""
    if four_ok:
        ok = next(r for r in results if ((r.get("four") or {}).get("composite") or {}).get("status") == "ok")
        weights = dict(ok["four"]["composite"]["weights"])
        w_source = str(ok["four"]["composite"].get("weights_source") or "")
    notes: List[str] = []
    gated: Dict[str, str] = {}
    with_cer = [r for r in results if r.get("cer") is not None]
    if len(with_cer) > 1:
        best_c = min(with_cer, key=lambda r: (float(r["cer"]), -float(r["total"])))
        keys = [k for k, v in best_c["per_item"].items() if v.get("cer") is not None]
        for r in with_cer:
            if r is best_c or float(r["cer"]) - float(best_c["cer"]) <= CER_GATE:
                continue
            common = [k for k in keys if r["per_item"].get(k, {}).get("cer") is not None]
            lo, _ = _paired_ci([r["per_item"][k]["cer"] for k in common], [best_c["per_item"][k]["cer"] for k in common])
            if lo > 0:
                gated[r["id"]] = (f"{r['id']} 读错的字明显比 {best_c['id']} 多（错字率 {100 * float(r['cer']):.1f}% 对 "
                                  f"{100 * float(best_c['cer']):.1f}%，超出误差范围），所以不能排第一。")

    def primary(r: Dict[str, Any]) -> float:
        comp = (r.get("four") or {}).get("composite") or {}
        if four_ok:
            return float(comp["mean"]) if comp.get("status") == "ok" else float("-inf")
        return float(r["total"])

    order = sorted(results, key=lambda r: (r["id"] not in gated, primary(r), float(r["total"])), reverse=True)
    dominated: Dict[str, Tuple[str, List[str]]] = {}
    if four_ok:
        for x in order:
            for y in order:
                if y is x or y["id"] in gated:
                    continue
                cmp = LG.paired_compare(items_of(y, "pct"), items_of(x, "pct"), weights)
                y_better = [g for g, e in cmp["groups"].items() if e.get("clear") == "a"]
                x_better = [g for g, e in cmp["groups"].items() if e.get("clear") == "b"]
                if y_better and not x_better:
                    dominated[x["id"]] = (y["id"], y_better)
                    break
    first = next((r for r in order if r["id"] not in gated and r["id"] not in dominated), order[0])
    final = [first] + [r for r in order if r is not first]
    # 分数最高的那个为什么不是第一名（读错字明显多 / 某一类句子明显差）：如实写出来
    for r in sorted(results, key=lambda r: (primary(r), float(r["total"])), reverse=True):
        if r is first:
            break
        if r["id"] in gated:
            notes.append(gated[r["id"]])
        elif r["id"] in dominated:
            y, gs = dominated[r["id"]]
            names = "」「".join(LG.GROUP_LABELS[g] for g in gs)
            what = "综合总评分" if four_ok else "综合分"
            notes.append(f"{r['id']} 的{what}更高，但「{names}」明显比 {y} 差（超出误差范围），所以不能排第一。")
    second = final[1] if len(final) > 1 else None
    tie, tradeoff, p = False, [], None
    if second is not None:
        if four_ok:
            cmp = LG.paired_compare(items_of(first, "pct"), items_of(second, "pct"), weights)
            comp = cmp.get("composite") or {}
            tie = comp.get("clear") is None
            p = cmp.get("p_a")
            tradeoff = [g for g, e in cmp["groups"].items() if e.get("clear") == "b"]
        else:
            p = _paired_bootstrap([v["S"] for v in first["per_item"].values()],
                                  [second["per_item"][k]["S"] for k in first["per_item"]])
            tie = p < TIE_P
    keep_two = bool(second is not None and second["id"] not in gated and (tie or tradeoff))
    return {"order": final, "first": first, "second": second, "tie": bool(tie), "tradeoff": tradeoff,
            "ci_p": p, "keep_two": keep_two, "gated": gated, "dominated": dominated, "notes": notes,
            "four_ok": four_ok, "weights": weights, "weights_source": w_source}


# ---------------------------------------------------------------------------- 深度挑选
def _grid(backend: Backend) -> List[Optional[Dict[str, Any]]]:
    try:
        ckpts = backend.checkpoints(all=True)  # type: ignore[call-arg]
    except TypeError:  # 这个引擎不分（只有一种挑法）
        ckpts = backend.checkpoints()
    return list(ckpts or [])


def _combo(s: str, g: str, s_ep: int, g_ep: int, known: Dict[Tuple[str, str], Dict[str, Any]]) -> Dict[str, Any]:
    return dict(known.get((s, g)) or {"id": f"s{s_ep}-g{g_ep}", "sovits": s, "gpt": g, "sovits_epoch": s_ep,
                                      "gpt_epoch": g_ep})


def select_deep(cfg: Dict[str, Any], project: Project, backend: Backend, progress: Optional[ProgressFn] = None,
                max_items: int = DEFAULT_ITEMS, use_asr: Optional[bool] = None, judge: Any = None,
                checker: Any = None) -> Dict[str, Any]:
    """「一模一样」的挑选（设计方案 §1.3）：分三步，每一步都只换一种模型（换得最少）。

    1. 先比语气模型（GPT）：音色模型固定用存下的里面最接近训练一半的那个，第 4 轮以后存下的每个语气模型 × 每句（没参加训练的
       录音 + 检查用的句子）× 一次请求同时生成 2 个，留前 3 个；
    2. 再比音色模型（SoVITS）：第一步最好的语气模型 × 每个音色模型，留前 3 个；
    3. 最后 3 × 3 组 + 你原来的模型按「一模一样」生成时的方式比：每句 2 条参考录音 × 每条 4 个，生成时的打分挑一个，
       再拿它和你的真实录音比；四项评分（中英夹在一起 / 纯中文 / 纯英文 / 综合总评分）排名，读错字分开把关。
    之后：按第 1 名重新校准语速、用你的录音校准排序权重、试听参考录音，都存进 models.json 的 identical。
    每次请求的结果存在 cache/select_deep/：中途停下 / 出错，下次接着做（做过的不再生成）。"""
    sel = _DeepSelect(cfg, project, backend, progress, max_items=max_items, use_asr=use_asr, judge=judge,
                      checker=checker)
    sel.load(with_tests=True, lo=0.0, hi=0.05)
    grid = _grid(backend)
    opaque = any(c is not None and not (c.get("sovits") and c.get("gpt")) for c in grid)
    prev = next((c for c in grid if c and c.get("previous")), None)
    cur = [c for c in grid if c and not c.get("previous")]
    hint = getattr(backend, "start_hint", lambda: "")()
    sel._p(0.05, "启动合成引擎" + (f"（{hint}）" if hint else "") + "……", log_it=True)
    backend.start()
    k_items = len(sel.items)
    stages: Dict[str, Any] = {}
    if opaque or not cur:
        combos_c: List[Optional[Dict[str, Any]]] = list(cur) or ([] if prev else [None])
    else:
        known = {(c["sovits"], c["gpt"]): c for c in cur}
        sov = sorted({c["sovits"]: int(c.get("sovits_epoch") or 0) for c in cur}.items(), key=lambda kv: (kv[1], kv[0]))
        gpt = sorted({c["gpt"]: int(c.get("gpt_epoch") or 0) for c in cur}.items(), key=lambda kv: (kv[1], kv[0]))
        # 第一步：比语气模型（只换 GPT）
        if len(gpt) > SCREEN_KEEP:
            top_ep = max(e for _, e in sov)
            s_mid = min(sov, key=lambda kv: (abs(kv[1] - top_ep / 2.0), -kv[1]))
            combos = [_combo(s_mid[0], g, s_mid[1], ge, known) for g, ge in gpt]
            ranked = sel.screen("A", combos, 0.06, 0.34,
                                f"挑选第一步：比较 {len(gpt)} 个语气模型（每个读 {k_items} 句、每句 {sel.screen_b} 遍）",
                                w_t=1.0, w_c=4.0)
            ranked.sort(key=lambda r: -r["score"])
            stages["A"] = [{k: v for k, v in r.items() if k != "ckpt"} for r in ranked]
            top_g = [(r["ckpt"]["gpt"], int(r["ckpt"].get("gpt_epoch") or 0)) for r in ranked[:SCREEN_KEEP]]
        else:
            top_g = sorted(gpt, key=lambda kv: -kv[1])
        # 第二步：比音色模型（只换 SoVITS）
        if len(sov) > SCREEN_KEEP:
            g_best = top_g[0]
            combos = [_combo(s, g_best[0], se, g_best[1], known) for s, se in sov]
            ranked = sel.screen("B", combos, 0.34, 0.60, f"挑选第二步：比较 {len(sov)} 个音色模型", w_t=1.5, w_c=3.0)
            ranked.sort(key=lambda r: -r["score"])
            stages["B"] = [{k: v for k, v in r.items() if k != "ckpt"} for r in ranked]
            top_s = [(r["ckpt"]["sovits"], int(r["ckpt"].get("sovits_epoch") or 0)) for r in ranked[:SCREEN_KEEP]]
        else:
            top_s = sorted(sov, key=lambda kv: -kv[1])
        # 第三步的组合按音色模型排在一起（一个音色模型只加载一次）
        combos_c = [_combo(s, g, se, ge, known) for s, se in sorted(top_s, key=lambda kv: (kv[1], kv[0]))
                    for g, ge in sorted(top_g, key=lambda kv: (kv[1], kv[0]))]
    if prev is not None and all(_cid(c) != _cid(prev) for c in combos_c):
        combos_c.append(prev)
    results = sel.final(combos_c, 0.60, 0.87, "挑选第三步：最好的几组按「一模一样」的方式比")
    if not results:
        raise RuntimeError("没有可以比较的模型")
    if all(r["failed"] == r["n_items"] for r in results):
        raise RuntimeError("所有模型都合成失败，请检查引擎日志")
    rk = sel.rank(results)
    first, second = rk["first"], rk["second"]
    speed, speed_info = sel.speed(first)
    sel._p(0.87, "试听参考录音、校准打分……", log_it=True)
    cal = sel.calibration(results)
    aud = sel.audition(first["ckpt"], 0.88, 0.99, "试听参考录音、校准打分")
    from voicetwin.eval import lang_groups as LG

    order = rk["order"]
    ckpts = [first["ckpt"]] + ([second["ckpt"]] if rk["keep_two"] else [])
    block = {"version": IDENTICAL_VERSION, "run_stamp": run_stamp(project, backend),
             "selected_stamp": selected_stamp(backend, first["ckpt"]) if first["ckpt"] else "",
             "ckpts": [c for c in ckpts if c is not None], "ranking": [r["id"] for r in order], "ci_p": rk["ci_p"],
             "tie": rk["tie"], "tradeoff": rk["tradeoff"], "speed": speed, "speed_info": speed_info,
             "weights": cal.get("weights") or {}, "weights_version": cal.get("version") or "default",
             "calibration": {k: cal.get(k) for k in ("gain", "adopted", "loo", "default_score", "n_groups", "n_items", "why")},
             "ref_prior": aud.get("prior"), "ref_prior_version": aud.get("version") or "",
             "audition": {k: aud.get(k) for k in ("n_refs", "n_items", "requests", "skipped")},
             "bank_sig": sel.bank_sig, "model_ids": [_weights_sig(backend, c) for c in ckpts],
             "items": {"val": sum(1 for i in sel.items if i.kind == "val"), "test": sum(1 for i in sel.items if i.kind == "test")},
             "seeds": {"base": SEED_BASE, "item_step": ITEM_SEED_STEP, "ref_step": REF_SEED_STEP},
             "v4": {"trained": False}, "evaluated_at": time.strftime("%Y-%m-%d %H:%M"), "note_bias": NOTE_BIAS,
             "lang": {"shares": sel.shares, "weights": rk["weights"], "weights_source": rk["weights_source"], "groups": {
                 g: {k: v for k, v in e.items() if k != "label"} for g, e in (sel.calib.get("groups") or {}).items()}},
             "mini": False}
    selection = {
        "method": "deep", "evaluated_at": block["evaluated_at"], "items": len(sel.items),
        "val_items": block["items"]["val"], "test_items": block["items"]["test"],
        "checkpoints": len({_cid(c) for c in cur + ([prev] if prev else [])}) or len(combos_c),
        "asr_check": sel.checker is not None and not sel.asr_failed, "similarity": sel.sim.info(),
        "results": [{k: v for k, v in r.items() if k not in ("ckpt", "per_item")} for r in order],
        "ranking": [r["id"] for r in order], "best": first["id"],
        "two": [_cid(c) for c in ckpts] if rk["keep_two"] else [], "tie": rk["tie"], "tradeoff": rk["tradeoff"],
        "ci_p": rk["ci_p"], "notes": rk["notes"], "four_ok": rk["four_ok"], "stages": stages,
        "lang_weights": rk["weights"], "lang_weights_source": rk["weights_source"], "lang_shares": sel.shares.get("shares"),
        "lang_calibration_notes": LG.calibration_notes(sel.calib, {i.group for i in sel.items}),
        "speed_info": speed_info, "weights_note": _cal_note(cal), "audition": block["audition"],
        "requests": dict(sel.stats)}
    selection["lines"] = deep_summary_lines(selection)
    info: Dict[str, Any] = {"speed": speed, "selection": selection, "identical": block}
    if first["ckpt"] is not None:
        info["selected"] = first["ckpt"]
    project.update_models(backend.name, info)
    _save_report(project, sel, results, rk)
    if first["ckpt"] is not None:
        backend.use_checkpoint(first["ckpt"])
    sel._p(1.0, f"最佳模型：{first['id']}" + (f"（综合总评分 {first['pct']:.1f}%）" if first.get("pct") is not None else ""),
           log_it=True)
    for line in selection["lines"]:
        log.info("  " + line)
    return info


def _cal_note(cal: Dict[str, Any]) -> str:
    from voicetwin.synth import calibrate_rank

    return calibrate_rank.describe(cal)


def _save_report(project: Project, sel: "_DeepSelect", results: List[Dict[str, Any]], rk: Dict[str, Any]) -> None:
    """每个模型每句的实测分数（核对用）：cache/select_deep/last_report.json。存不了不影响挑选。"""
    try:
        from voicetwin.utils import atomic

        rows = []
        for r in rk["order"]:
            rows.append({"id": r["id"], "previous": r["previous"], "four": r["four"], "cer": r["cer"], "total": r["total"],
                         "items": {k: {kk: v.get(kk) for kk in ("S", "pct", "cer", "group", "w", "kind", "failed", "ratio")}
                                   for k, v in r["per_item"].items()}})
        sel.cache_dir.mkdir(parents=True, exist_ok=True)
        atomic.write_text(sel.cache_dir / "last_report.json",
                          json.dumps(_jsonable({"evaluated_at": time.strftime("%Y-%m-%d %H:%M"), "models": rows,
                                                "items": [{"key": i.key, "text": i.text, "group": i.group, "kind": i.kind,
                                                           "w": i.w} for i in sel.items]}),
                                     ensure_ascii=False, indent=1))
    except Exception as exc:  # noqa: BLE001
        log.debug(f"挑选的详细结果存不了：{exc}")


def audition_references(cfg: Dict[str, Any], project: Project, backend: Backend, sim: Any = None,
                        items: Optional[Sequence[Any]] = None, bank: Optional[Sequence[Dict[str, Any]]] = None,
                        ckpt: Optional[Dict[str, Any]] = None, progress: Optional[ProgressFn] = None,
                        use_asr: Optional[bool] = None, checker: Any = None) -> Dict[str, Any]:
    """试听参考录音（设计方案 §2 P8，见 _DeepSelect.audition）：用 ckpt（不给 = 现在用的模型）把参考录音库里原来分数
    最高的 24 条（同一个视频最多 3 条）在 6 句没参加训练的录音上各试一次（同时生成 4 个）。
    sim：已经加载好的声纹打分（_Sim）；items：只用这几句没参加训练的录音（片段 id 或记录）；bank：只从这些参考录音里挑。
    返回 {"prior": {参考 id: 先验}, "version", "n_refs", "n_items", "requests"}；没参加训练的录音不到 6 句时 prior 是 None。"""
    sel = _DeepSelect(cfg, project, backend, progress, use_asr=use_asr, checker=checker, sim=sim)
    sel.load(with_tests=False, group_calib=False)
    if items is not None:
        want = {str(x.get("id")) if isinstance(x, dict) else str(getattr(x, "id", x)) for x in items}
        sel.items = [it for it in sel.items if it.id in want]
    if bank is not None:
        sel.pool = [dict(e, _bank=e.get("_bank", True)) for e in bank]
    if not [it for it in sel.items if it.kind == "val"]:
        return sel.audition(ckpt, 0.0, 1.0, "试听参考录音、校准打分")
    backend.start()
    return sel.audition(ckpt, 0.0, 1.0, "试听参考录音、校准打分")


def deep_summary_lines(selection: Dict[str, Any]) -> List[str]:
    """挑选结果给老师看的几行（只写实测的数）：前 5 名的四项评分和错字率、分不出来 / 各有长处、为什么不能排第一、
    按句子种类校准的说明、综合总评分的比例、英文的提示、语速、排序权重、试听参考录音、分数偏乐观的提醒。"""
    from voicetwin.eval import lang_groups as LG

    res = list(selection.get("results") or [])
    nv, nt = int(selection.get("val_items") or 0), int(selection.get("test_items") or 0)
    lines = [f"挑选结果（实测，{nv + nt} 句：没参加训练的录音 {nv} 句、检查用的句子 {nt} 句）："]
    for k, r in enumerate(res[:5], 1):
        name = str(r.get("id")) + ("（你原来的模型）" if r.get("previous") else "")
        cer = r.get("cer")
        text = f"第 {k} 名 {name}：{LG.four_scores_text(r.get('four'))}；"
        text += f"错字率 {100 * float(cer):.1f}%" if cer is not None else f"错字率{LG.NOT_MEASURED}"
        if r.get("failed"):
            text += f"；有 {int(r['failed'])} 句没能生成（按最差算）"
        lines.append(text)
    if not selection.get("four_ok"):
        lines.append("「像你本人」的四项评分这次没测出来（没有按你的录音校准好的声纹模型），名次按综合分"
                     "（声纹相似度、读错字、长短、音调）排。")
    lines += [str(x) for x in selection.get("notes") or []]
    two = selection.get("two") or []
    if len(two) == 2 and selection.get("tradeoff"):
        names = "」「".join(LG.GROUP_LABELS.get(g, g) for g in selection["tradeoff"])
        lines.append(f"第 1、2 名各有长处：第 2 名「{names}」明显更像（超出误差范围），第 1 名综合总评分更高；"
                     "两个都留着，现在生成用第 1 名，请用耳朵听听两个的差别。")
    elif len(two) == 2:
        lines.append("第 1、2 名的差别在误差范围内（分不出来）：两个都留着，现在生成用第 1 名，请用耳朵听听两个的差别。")
    lines += [str(x) for x in selection.get("lang_calibration_notes") or []]
    w = selection.get("lang_weights") or {}
    if w:
        lines.append(LG.weights_text(w, str(selection.get("lang_weights_source") or "material")))
    if any(int((((r.get("four") or {}).get("groups") or {}).get(g) or {}).get("n") or 0) > 0
           for r in res[:1] for g in ("mixed", "en")):
        lines.append(LG.EN_NOTE + "。")
    sp = selection.get("speed_info") or {}
    n_zh = int((sp.get("n_items") or {}).get("zh") or 0)
    if sp and n_zh < SPEED_MIN_ITEMS:
        lines.append(f"没参加训练的录音只有 {n_zh} 句能比语速（不到 {SPEED_MIN_ITEMS} 句），语速先不调。")
    if selection.get("weights_note"):
        lines.append(str(selection["weights_note"]) + "。")
    aud = selection.get("audition") or {}
    if aud.get("skipped"):
        lines.append(f"没有试听参考录音（{aud['skipped']}），生成时按原来的方法挑参考录音。")
    elif aud.get("n_refs"):
        lines.append(f"已用第 1 名把 {aud['n_refs']} 条参考录音在 {aud.get('n_items')} 句没参加训练的录音上试听过，"
                     "生成时优先用实测更像的参考录音。")
    lines.append(BIAS_LINE)
    return lines


# ---------------------------------------------------------------------------- 准备「一模一样」（生成前）
def identical_block(project: Project, backend: Backend) -> Dict[str, Any]:
    block = (project.load_models().get(backend.name) or {}).get("identical")
    return block if isinstance(block, dict) else {}


def identical_stale(project: Project, backend: Backend) -> bool:
    """models.json 里的 identical 是不是要重新做：没有（以前的版本练的模型、标准方式练的）、格式旧了、重新训练过、
    换了模型（例如按标准的挑法重新挑过）。只有能训练、选定了模型的引擎才有。"""
    if not getattr(backend, "supports_training", False):
        return False
    sel = backend.selected_checkpoint()
    if not isinstance(sel, dict) or not sel:
        return False
    block = identical_block(project, backend)
    return (not block or block.get("version") != IDENTICAL_VERSION
            or str(block.get("run_stamp") or "") != run_stamp(project, backend)
            or str(block.get("selected_stamp") or "") != selected_stamp(backend, sel))


def prepare_identical(cfg: Dict[str, Any], project: Project, backend: Backend, progress: Optional[ProgressFn] = None,
                      judge: Any = None, checker: Any = None, use_asr: Optional[bool] = None) -> Dict[str, Any]:
    """生成「一模一样」前的准备（设计方案 §1.4，进度条上的「准备「一模一样」」）：缺了或者旧了才做——
    1. 你本人的说话习惯（twin_profile.json，素材没变时不用重新量）；
    2. 参考录音库（带声纹；能进库的录音或者声纹模型变了才重新整理，声纹按片段缓存）；
    3. models.json 的 identical（语速、排序权重、试听参考录音）：以前的版本练的模型、标准方式练的模型、重新挑过模型以后
       都没有 / 旧了 → 用选定的这个模型做一次小校准：没参加训练的录音按「一模一样」生成时的方式各试 2 条参考 × 4 个，
       校准语速和排序权重，再试听参考录音。这样以前练的模型不用重新训练，也能按「一模一样」生成。
    judge / checker：生成引擎已经加载好的声纹打分和识别模型（不再加载一遍）。返回 {"twin", "bank", "mini", "block"}。"""
    from voicetwin.style.twin_profile import build_twin_profile

    def _p(frac: float, msg: str) -> None:
        if progress is not None:
            try:
                progress(max(0.0, min(1.0, frac)), msg)
            except Exception:  # noqa: BLE001
                pass

    out: Dict[str, Any] = {"twin": False, "bank": False, "mini": False, "block": identical_block(project, backend)}
    _p(0.0, "准备「一模一样」：测量你的说话习惯（停顿、音调、语速）……")
    try:
        out["twin"] = build_twin_profile(project) is not None
    except Exception as exc:  # noqa: BLE001 - 停止按钮不是 Exception，照常传出去
        log.warning(f"你本人的说话习惯这次没量出来（{_first_line(exc)}），语速按以前的方式比")
    if judge is None:
        try:
            judge = SimilarityJudge.for_project(cfg, project)
        except Exception as exc:  # noqa: BLE001
            log.warning(f"声纹打分不可用：{_first_line(exc)}")
            judge = None
    if judge is not None and not getattr(judge, "available", False):
        judge = None
    try:
        records = project.load_manifest()
        bank = _ensure_bank(project, judge, records,
                            progress=lambda f, m: _p(0.05 + 0.25 * max(0.0, min(1.0, f)), f"准备「一模一样」：{m}"))
        out["bank"] = bank is not None
    except Exception as exc:  # noqa: BLE001
        log.warning(f"参考录音库这次没整理好（{_first_line(exc)}），用以前挑好的参考录音")
    if not identical_stale(project, backend):
        return out
    sel_ck = backend.selected_checkpoint()
    log.info("准备「一模一样」（这个模型只做一次）：models.json 里还没有这个模型按「一模一样」校准的结果，"
             "用没参加训练的录音做一次小校准")
    try:
        out["block"] = _mini_calibration(cfg, project, backend, sel_ck, _p, judge=judge, checker=checker, use_asr=use_asr)
        out["mini"] = True
    except Exception as exc:  # noqa: BLE001 - 小校准没做成：照样生成（语速、权重、参考按以前的方式），下次再试
        if _fatal(exc):
            raise
        log.warning(f"⚠️ 「一模一样」的小校准这次没做成（{_first_line(exc)}），这次生成按以前的语速和挑参考的方法；"
                    "下次生成时会再试")
    return out


def _mini_calibration(cfg: Dict[str, Any], project: Project, backend: Backend, sel_ck: Dict[str, Any],
                      p: Callable[[float, str], None], judge: Any = None, checker: Any = None,
                      use_asr: Optional[bool] = None) -> Dict[str, Any]:
    """选定的模型 × 没参加训练的录音（不加检查用的句子）按第三步的方式试一遍 → 语速、排序权重、试听参考录音。
    只写 models.json 的 identical（不改选定的模型、挑选结果和别的档位用的语速）。"""
    sel = _DeepSelect(cfg, project, backend, lambda f, m: p(f, m), use_asr=use_asr, judge=judge, checker=checker)
    sel.load(with_tests=False, lo=0.30, hi=0.32, bank_msg="准备「一模一样」：", group_calib=False)
    block: Dict[str, Any] = {"version": IDENTICAL_VERSION, "run_stamp": run_stamp(project, backend),
                             "selected_stamp": selected_stamp(backend, sel_ck), "ckpts": [sel_ck],
                             "ranking": [_cid(sel_ck)], "ci_p": None, "speed": {}, "weights": {},
                             "weights_version": "default", "ref_prior": None, "ref_prior_version": "",
                             "evaluated_at": time.strftime("%Y-%m-%d %H:%M"), "note_bias": NOTE_BIAS, "mini": True,
                             "model_ids": [_weights_sig(backend, sel_ck)], "v4": {"trained": False},
                             "seeds": {"base": SEED_BASE, "item_step": ITEM_SEED_STEP, "ref_step": REF_SEED_STEP}}
    if not sel.items:
        block.update(items={"val": 0, "test": 0}, note="没有没参加训练的录音，语速、排序权重都按以前的方式")
        project.update_models(backend.name, {"identical": block})
        return block
    hint = getattr(backend, "start_hint", lambda: "")()
    p(0.32, "启动合成引擎" + (f"（{hint}）" if hint else "") + "……")
    backend.start()
    results = sel.final([sel_ck], 0.33, 0.70, "准备「一模一样」（这个模型只做一次）：用没参加训练的录音试一遍这个模型")
    r = results[0]
    speed, speed_info = sel.speed(r)
    cal = sel.calibration(results)
    aud = sel.audition(sel_ck, 0.70, 0.99, "准备「一模一样」：用没参加训练的录音试听参考录音")
    block.update(speed=speed, speed_info=speed_info, weights=cal.get("weights") or {},
                 weights_version=cal.get("version") or "default",
                 calibration={k: cal.get(k) for k in ("gain", "adopted", "loo", "default_score", "n_groups", "n_items", "why")},
                 ref_prior=aud.get("prior"), ref_prior_version=aud.get("version") or "",
                 audition={k: aud.get(k) for k in ("n_refs", "n_items", "requests", "skipped")}, bank_sig=sel.bank_sig,
                 items={"val": len(sel.items), "test": 0},
                 result={k: v for k, v in r.items() if k not in ("ckpt", "per_item")})
    project.update_models(backend.name, {"identical": block})
    log.info(f"准备「一模一样」：小校准做完了（语速 {speed}；{_cal_note(cal)}）")
    return block
