"""合成引擎：讲稿 → 完整的讲课音频（+ 字幕）。

为了"像你"做的事情：
1. 每句话生成多个候选（不同随机种子），用"像你本人（%）"（几个声纹模型校准后的平均）、
   识别错字率、语速/音高偏差打分；低于 85% 的候选直接淘汰，剩下的里面相似度为主挑最像的；
2. 错字太多（漏字/多字/读错）或者都不够像时自动重做；「完美」档会一批一批地试，直到达到严格标准或试满 20 次；
3. 疑问句用你的疑问语气参考音频，陈述句用陈述参考（「完美」档还会挑长短最接近的参考）；
4. 句间/段间停顿按你本人的停顿习惯（含自然波动），停顿和开头结尾都是绝对的数字静音（全是 0），没有任何底噪；
5. 每句首尾的非语音会被切掉并淡入淡出，句子边上不留杂音；
6. 语速用验证集自动校准，再乘上你选的快慢；快慢由合成模型本身控制（GPT-SoVITS 的 speed_factor 只改时长、
   不改音高和音色），这里从不对波形做重采样或变调式的拉伸；停顿也跟着快慢按比例变化；
7. 响度匹配你原来的录音；
8. 每句结果都缓存：改了讲稿的某一句，重新生成只会重做那一句；
9. 「完美」档同时输出「未去杂音」和「去杂音」两个完整版本，自动比较哪个更像你并标出推荐。
"""

from __future__ import annotations

import json
import math
import random
import shutil
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence, Tuple, Union

import numpy as np

from voicetwin.backends.base import Backend, SynthRequest
from voicetwin.data.references import aux_references, pick_reference
from voicetwin.eval.metrics import CERChecker, Score, Scorer, engine_is_strong
from voicetwin.eval.speaker import (
    HONEST_NOTE,
    PCT_HELP,
    SimilarityJudge,
    get_speaker_encoder,
    gsv_root_from_cfg,
    status_for_pct,
    voice_centroid,
)
from voicetwin.project import Project
from voicetwin.style.profile import pause_range, pause_seconds
from voicetwin.synth.script import ScriptSegment, parse_script
from voicetwin.utils.audio import (
    auto_silence_threshold,
    fade,
    frame_rms_db,
    load_audio,
    measure_lufs,
    normalize_lufs,
    resample,
    save_audio,
)
from voicetwin.utils.ffmpeg import encode
from voicetwin.utils.log import get_logger
from voicetwin.utils.textutil import short_hash, syllable_count

try:  # U1：停止按钮
    from voicetwin.utils.progress import check_cancel as _check_cancel
except ImportError:  # pragma: no cover - 没有 U1 时什么都不做
    def _check_cancel() -> None:
        return None

log = get_logger("synth")
CACHE_VERSION = "v2"
ProgressFn = Callable[[float, str], None]

QUALITY_ORDER = ("fast", "balanced", "best", "max", "perfect")
#: 网页「质量」单选框上的字（命令行、报告里也用它）。「极致」不写「最慢」：「完美」比它更慢。
QUALITY_LABELS = {
    "fast": "快速（最快，每句只做 1 遍）",
    "balanced": "均衡（每句做 3 遍，挑最像你的）",
    "best": "最好（每句做 5 遍，并检查漏字错字）",
    "max": "极致（很慢，更稳更像，建议显存 ≥ 8GB）",
    "perfect": "完美：每句最多试 20 次、严格检查漏字错字，去掉杂音，句子之间完全静音，尽最大可能接近你本人（最慢）",
}
QUALITY_SHORT = {"fast": "快速", "balanced": "均衡", "best": "最好", "max": "极致", "perfect": "完美"}
#: 每个档位一行说明（网页上显示，诚实：只说多试几次、挑得更准，不吹"一模一样"）
QUALITY_HELP = {
    "fast": "快速：每句只生成 1 次，最快；偶尔会有读错或不太像的句子。",
    "balanced": "均衡：每句生成 3 次，自动挑最像你的；速度和效果兼顾。",
    "best": "最好：每句生成 5 次，并用语音识别检查漏字、错字；更慢，但更稳。",
    "max": "极致：每句生成 8 次并严格检查漏字错字，不够像的自动重做；时间大约是「均衡」的 3～5 倍。",
    "perfect": "完美：每句最多试 20 次、严格检查漏字错字，去掉杂音，句子之间完全静音，尽最大可能接近你本人（最慢）。",
}
QUALITY_NOTE = ("档位越高越慢，但结果更稳定、更像你；它只是让出错更少、挑得更准，不会超过模型训练出来的水平。"
                "素材的质量和数量、文字校对最重要。")

#: 各档位的参数。依据见 research_quality.md §6（结构有依据，具体数字是工程取值，最终由识别校验和声纹打分把关）。
QUALITY_PRESETS: Dict[str, Dict[str, Any]] = {
    "fast": {"candidates": 1, "asr": False, "retry_rounds": 0, "retry_candidates": 0, "aux_refs": None},
    "balanced": {"candidates": 3, "asr": False, "retry_rounds": 2, "retry_candidates": 2, "aux_refs": None,
                 "cer_retry_threshold": {"strong": 0.15, "weak": 0.15}},
    "best": {"candidates": 5, "asr": True, "retry_rounds": 2, "retry_candidates": 2, "aux_refs": None,
             "cer_retry_threshold": {"strong": 0.10, "weak": 0.15}},
    "max": {"candidates": 8, "low_tier_candidates": 6, "asr": True, "force_asr": True, "retry_rounds": 3,
            "retry_candidates": 3, "early_after": 4, "early_pct": 99.0, "aux_refs": 3, "low_tier_aux_refs": 2,
            "cer_retry_threshold": {"strong": 0.08, "weak": 0.12}},
    "perfect": {"candidates": 4, "adaptive": True, "max_candidates": 20, "low_tier_max_candidates": 12,
                "asr": True, "force_asr": True, "aux_refs": 3, "low_tier_aux_refs": 2,
                "cer_retry_threshold": {"strong": 0.08, "weak": 0.12}, "cer_target": {"strong": 0.05, "weak": 0.08},
                "target_pct": 99.0, "variants": True, "match_reference": True},
}
#: 重做时用更保守的采样（温度/候选词更少 → 更稳）；GPT-SoVITS 官方温度上限是 1
RETRY_SAMPLING = [{"temperature": 0.7, "top_k": 10, "top_p": 1.0}, {"temperature": 0.6, "top_k": 15, "top_p": 0.8}]
VARIANT_RAW, VARIANT_DENOISED = "未去杂音", "去杂音"
RESULT_HEADERS = ["#", "句子", "像你本人（%）", "状态", "提示"]
LEAD_IN, LEAD_OUT = 0.35, 0.4


def _vram_tier() -> str:
    try:
        from voicetwin.utils.gpu import vram_tier

        return vram_tier()
    except Exception:
        return "none"


def recommended_quality(tier: Optional[str] = None) -> Tuple[str, str]:
    """按显卡推荐的默认档位和一句说明：显存 ≥ 8GB → 完美；更小 → 极致；没有能用的显卡 → 均衡。"""
    tier = tier or _vram_tier()
    if tier in ("high", "mid"):
        return "perfect", ("已按你的显卡自动选「完美」：每句会多试几次再挑最像你的，所以比较慢。"
                           "档位越高越慢，但结果越稳定。")
    if tier == "low":
        return "max", "显存小于 8GB：默认用「极致」（「完美」会非常慢）。档位越高越慢，但结果越稳定。"
    return "balanced", "没有检测到能用的 NVIDIA 显卡：默认用「均衡」，更高的档位会非常慢。"


def quality_choices() -> List[Tuple[str, str]]:
    """给网页单选框用的 (中文标签, 值) 列表，从快到慢。"""
    return [(QUALITY_LABELS[q], q) for q in QUALITY_ORDER]


def resolve_quality(quality: Any, tier: Optional[str] = None) -> str:
    """把用户/配置给的档位变成 fast|balanced|best|max|perfect；auto 或空 = 按显卡推荐。"""
    q = str(quality or "").strip()
    if isinstance(quality, (list, tuple)) and quality:  # gradio 偶尔会把单选值包成列表
        q = str(quality[0]).strip()
    low = q.lower()
    if low in ("", "auto", "自动", "none"):
        return recommended_quality(tier)[0]
    if low in QUALITY_PRESETS:
        return low
    for key in QUALITY_ORDER:
        if q in (QUALITY_LABELS[key], QUALITY_SHORT[key]) or q.startswith(QUALITY_SHORT[key]):
            return key
    log.warning(f"不认识的质量档位「{q}」，改用「均衡」")
    return "balanced"


def trim_edges(wav: np.ndarray, sr: int, pad_ms: float = 30.0) -> np.ndarray:
    """去掉一句话首尾的非语音（按能量判断），首尾各留一点余量，并在余量里平滑淡入淡出：
    第一个和最后一个采样都是 0，句子边上不会留下杂音，也不会有"咔哒"声。"""
    wav = np.asarray(wav, dtype=np.float32)
    if wav.size == 0:
        return wav
    hop_ms, win_ms = 5.0, 20.0
    thr = auto_silence_threshold(wav, sr)
    db = frame_rms_db(wav, sr, hop_ms=hop_ms, win_ms=win_ms)
    voiced = np.where(db >= thr)[0]
    if voiced.size == 0:
        return wav[:0]
    hop = sr * hop_ms / 1000.0
    half = sr * win_ms / 2000.0
    pad = int(sr * pad_ms / 1000.0)
    start = max(0, int(voiced[0] * hop - half) - pad)
    end = min(len(wav), int(voiced[-1] * hop + half) + pad)
    out = wav[start:end].astype(np.float32, copy=True)
    n = len(out)
    if n < 4:
        return out[:0]
    n_in = min(n // 2, pad + int(sr * 0.004))
    n_out = min(n // 2, pad + int(sr * 0.008))
    if n_in > 1:
        out[:n_in] *= (0.5 - 0.5 * np.cos(np.linspace(0.0, np.pi, n_in))).astype(np.float32)
    if n_out > 1:
        out[-n_out:] *= (0.5 + 0.5 * np.cos(np.linspace(0.0, np.pi, n_out))).astype(np.float32)
    out[0] = 0.0
    out[-1] = 0.0
    return out


def denoise_light(wav: np.ndarray, sr: int, strength: float = 0.5) -> Optional[np.ndarray]:
    """轻度去杂音（noisereduce 平稳噪声模式，中等强度）。没装 noisereduce 时返回 None。

    噪声样本取这句话里最安静的几段（句内停顿）；样本不够（< 0.15 秒）时不处理，原样返回——宁可不去，也不伤音色。
    """
    try:
        import noisereduce as nr  # type: ignore
    except Exception:
        return None
    wav = np.asarray(wav, dtype=np.float32)
    if wav.size < sr * 0.3:
        return wav.copy()
    try:
        hop = int(sr * 0.01)
        edge = int(sr * 0.045)  # 首尾已经淡入淡出过，不能拿来估计噪声
        inner = wav[edge:len(wav) - edge] if len(wav) > 2 * edge + sr * 0.2 else wav
        db = frame_rms_db(inner, sr, hop_ms=10.0, win_ms=30.0)
        valid = db > -90.0
        if not np.any(valid):
            return wav.copy()
        floor = float(np.percentile(db[valid], 10))
        top = float(np.percentile(db[valid], 95))
        if top - floor < 15.0:  # 没有明显的停顿可以当噪声样本
            return wav.copy()
        quiet = np.where(valid & (db <= floor + 3.0))[0]
        pieces = [inner[i * hop:(i + 1) * hop] for i in quiet if (i + 1) * hop <= len(inner)]
        noise = np.concatenate(pieces) if pieces else np.zeros(0, dtype=np.float32)
        if len(noise) < sr * 0.15 or float(np.max(np.abs(noise))) <= 0.0:
            return wav.copy()
        out = nr.reduce_noise(y=wav, sr=sr, y_noise=noise, stationary=True, prop_decrease=float(strength),
                              n_std_thresh_stationary=1.5)
        out = np.asarray(out, dtype=np.float32).reshape(-1)
        if out.shape != wav.shape or not np.all(np.isfinite(out)):
            return wav.copy()
        n = min(len(out) // 2, int(sr * 0.01))
        if n > 1:  # 保证首尾仍然从 0 开始、到 0 结束
            out[:n] *= np.linspace(0.0, 1.0, n, dtype=np.float32)
            out[-n:] *= np.linspace(1.0, 0.0, n, dtype=np.float32)
        out[0] = 0.0
        out[-1] = 0.0
        return out
    except Exception as exc:
        log.warning(f"去杂音失败（{exc}），这一句用原声")
        return wav.copy()


@dataclass
class SegmentResult:
    segment: ScriptSegment
    wav: np.ndarray
    sr: int
    score: Dict[str, Any]
    ref_id: str
    cached: bool
    seed: int
    candidates: List[Dict[str, Any]] = field(default_factory=list)
    start: float = 0.0
    end: float = 0.0
    path: Optional[Path] = None          # 这一句的音频（缓存里的 wav），网页上可以单独试听
    pct: Optional[float] = None          # 像你本人（%）
    status: str = ""                     # ✅ / 🟢 / 🔴 / ⚠️
    hint: str = ""                       # 给老师看的提示
    flagged: bool = False
    tries: int = 0                       # 这一句一共试了几次
    met: Optional[bool] = None           # 「完美」档：有没有达到严格标准


@dataclass
class NarrationResult:
    audio_path: Path
    srt_path: Optional[Path]
    report_path: Path
    duration: float
    segments: List[Dict[str, Any]]
    warnings: List[str]
    flagged: List[int] = field(default_factory=list)       # 有问题的句子编号（从 1 开始，和结果表的 # 一样）
    variants: List[Dict[str, Any]] = field(default_factory=list)  # 「完美」档的两个版本
    quality: str = ""
    overall_pct: Optional[float] = None                    # 整篇的像你本人（%），按时长加权
    notes: List[str] = field(default_factory=list)         # 中文小结


@dataclass
class _Plan:
    ref: Dict[str, Any]
    aux: List[Dict[str, Any]]
    speed: float
    key: str
    wav_path: Path
    meta_path: Path

    @property
    def cached(self) -> bool:
        return self.wav_path.exists() and self.meta_path.exists()


@dataclass
class _Cand:
    score: Score
    seed: int
    wav: np.ndarray
    sr: int
    round: int
    k: int


class Narrator:
    def __init__(self, cfg: Dict[str, Any], project: Project, backend: Backend, quality: Optional[str] = None,
                 candidates: Optional[int] = None, speed: Union[str, float, None] = None, reference: str = "",
                 asr_check: Optional[bool] = None, progress: Optional[ProgressFn] = None,
                 variants: Optional[bool] = None, tier: Optional[str] = None):
        self.cfg = cfg
        self.scfg: Dict[str, Any] = dict(cfg.get("synth", {}) or {})
        self.project = project
        self.backend = backend
        self._tier = tier
        self.quality = resolve_quality(quality if quality not in (None, "") else self.scfg.get("quality", "auto"),
                                       tier=tier)
        tiers_cfg = self.scfg.get("tiers") or {}
        preset = dict(QUALITY_PRESETS[self.quality])
        preset.update({k: v for k, v in (tiers_cfg.get(self.quality) or {}).items() if v not in (None, "auto")})
        if self.quality in ("balanced", "best"):  # 老配置里的全局项只管这两档
            if self.scfg.get("cer_retry_threshold") not in (None, "auto"):
                thr = float(self.scfg["cer_retry_threshold"])
                if self.quality == "balanced" or thr != 0.15:
                    preset["cer_retry_threshold"] = {"strong": thr, "weak": thr}
            if self.scfg.get("max_retries") not in (None, "auto"):
                preset["retry_rounds"] = int(self.scfg["max_retries"])
        self.preset = preset
        self.notes: List[str] = []
        low = preset.get("low_tier_candidates") is not None or preset.get("low_tier_max_candidates") is not None
        is_low = low and self.tier == "low"
        cand_cfg = candidates if candidates is not None else self.scfg.get("candidates", "auto")
        n = preset.get("low_tier_candidates") if (is_low and preset.get("low_tier_candidates")) else preset["candidates"]
        self.n_candidates = max(1, int(n if cand_cfg in (None, "auto", 0, "0") else cand_cfg))
        self.adaptive = bool(preset.get("adaptive"))
        cap = preset.get("low_tier_max_candidates") if (is_low and preset.get("low_tier_max_candidates")) \
            else preset.get("max_candidates", self.n_candidates)
        self.max_candidates = max(self.n_candidates, int(cap or self.n_candidates))
        if is_low and self.quality in ("max", "perfect"):
            self.notes.append("显存较小，已减少候选数（每句最多试 "
                              f"{self.max_candidates if self.adaptive else self.n_candidates} 次）")
            log.info(self.notes[-1])
        asr_cfg = asr_check if asr_check is not None else self.scfg.get("asr_check", "auto")
        if preset.get("force_asr") and asr_cfg is not False:
            self.use_asr = True
        else:
            self.use_asr = bool(preset["asr"]) if asr_cfg in (None, "auto") else bool(asr_cfg)
        self.min_wrong = int(preset.get("min_wrong_chars", self.scfg.get("min_wrong_chars", 2)) or 0)
        self.want_variants = bool(preset.get("variants")) if variants is None else bool(variants)
        self.speed_opt = speed if speed is not None else self.scfg.get("speed", "auto")
        self.reference = reference
        self.progress = progress
        self.profile = project.load_profile()
        self.refs = project.load_references()
        self.warnings: List[str] = []
        self._scorer: Optional[Scorer] = None
        self._judge: Optional[SimilarityJudge] = None
        self._checker: Optional[CERChecker] = None
        self._started = False
        self._pos: Tuple[int, int] = (0, 1)
        self._gen_range: Tuple[float, float] = (0.03, 0.95)
        self.base_seed = int(self.scfg.get("seed", 20240601))
        sim_cfg = dict(cfg.get("similarity", {}) or {})
        self.min_pct = float(sim_cfg.get("min_pct", 85) or 85)
        self.filter_mode = str(sim_cfg.get("filter", "auto") or "auto").lower()
        # 「完美」档的目标：synth.tiers.<档位>.target_pct 优先，其次 similarity.target_pct（配置文件里写着的那个），
        # 都没写（或写 auto）才用档位自带的 99
        tier_target = (tiers_cfg.get(self.quality) or {}).get("target_pct")
        if tier_target not in (None, "auto", ""):
            target = tier_target
        elif sim_cfg.get("target_pct") not in (None, "auto", ""):
            target = sim_cfg.get("target_pct")
        else:
            target = preset.get("target_pct", 99)
        try:
            self.target_pct = float(target) if float(target) > 0 else 99.0
        except (TypeError, ValueError):
            self.target_pct = 99.0

    # ------------------------------------------------------------------ 显卡档位
    @property
    def tier(self) -> str:
        if self._tier is None:
            self._tier = _vram_tier()
        return self._tier

    # ------------------------------------------------------------------ 打分器
    @property
    def judge(self) -> Optional[SimilarityJudge]:
        self.scorer  # noqa: B018 - 触发加载
        return self._judge

    @property
    def scorer(self) -> Scorer:
        if self._scorer is None:
            judge = None
            try:
                judge = SimilarityJudge.for_project(self.cfg, self.project)
            except Exception as exc:
                log.warning(f"声纹打分不可用：{exc}")
            encoder, cen = None, None
            if judge is None or not judge.available:
                try:
                    encoder = get_speaker_encoder(self.cfg.get("speaker_encoder", "auto"))
                    cen = voice_centroid(self.project, encoder)
                except Exception as exc:
                    log.warning(f"声纹打分不可用：{exc}")
            self._judge = judge if (judge is not None and judge.available) else None
            if self.use_asr:
                self._checker = CERChecker(self.scfg.get("asr_check_model", "auto"), progress=self.progress,
                                           vram_tier=self.tier, gsv_root=gsv_root_from_cfg(self.cfg),
                                           progress_range=(0.02, 0.03))
            self._scorer = Scorer(self.profile, cen, encoder, self.scfg.get("score"), self._checker, judge=self._judge)
            if self._judge is not None:
                log.info("声纹打分模型：" + "、".join(self._judge.info()["labels"]) + f"（{PCT_HELP}）")
        return self._scorer

    @property
    def sim_filter(self) -> bool:
        """要不要按"像你本人"淘汰候选（< 85%）。auto：有正经声纹模型并且校准成功时才淘汰。"""
        judge = self.judge
        if judge is None or not judge.calibrated or self.filter_mode in ("off", "false", "0", "no"):
            return False
        if self.filter_mode in ("on", "true", "1", "yes"):
            return True
        return judge.reliable

    def _cer_strong(self, c: Optional["_Cand"], lang: str, text: str = "") -> bool:
        """这个候选是用"准"的识别模型检查的吗（Paraformer / Whisper large）？准的模型用更严的门槛。"""
        if c is not None and c.score.checker:
            return engine_is_strong(c.score.checker)
        return bool(self._checker is not None and self._checker.strong(lang, text))

    def _thr(self, key: str, lang: str, default: float, c: Optional["_Cand"] = None) -> float:
        val = self.preset.get(key)
        if isinstance(val, dict):
            return float(val.get("strong" if self._cer_strong(c, lang) else "weak", default))
        return float(val) if isinstance(val, (int, float)) else default

    # ------------------------------------------------------------------ 工具
    def _speed_multiplier(self) -> float:
        """用户额外指定的快慢倍数（auto = 1.0，即完全按你本人的语速）。>1 更快，<1 更慢。"""
        opt = self.speed_opt
        if opt in (None, "auto", ""):
            return 1.0
        try:
            val = float(opt)
        except (TypeError, ValueError):
            return 1.0
        return float(min(2.0, max(0.5, val))) if math.isfinite(val) and val > 0 else 1.0

    def _speed_for(self, lang: str) -> float:
        """最终传给引擎的语速 = 自动校准系数 × 用户倍数（由模型自己控制时长，不改音高音色）。"""
        cal = self.backend.speed_calibration()
        val = float(cal.get(lang, cal.get("zh", 1.0)) or 1.0) * self._speed_multiplier()
        return float(min(2.0, max(0.5, val)))

    def _progress(self, frac: float, msg: str) -> None:
        if self.progress:
            try:
                self.progress(max(0.0, min(1.0, frac)), msg)
            except Exception:
                pass

    def _cache_paths(self, key: str) -> Tuple[Path, Path]:
        d = self.project.cache_dir / "segments" / key[:2]
        d.mkdir(parents=True, exist_ok=True)
        return d / f"{key}.wav", d / f"{key}.json"

    def _n_aux(self) -> int:
        if self.preset.get("aux_refs") is not None:
            if self.tier == "low" and self.preset.get("low_tier_aux_refs") is not None:
                return int(self.preset["low_tier_aux_refs"])
            return int(self.preset["aux_refs"])
        return int((self.backend.bcfg.get("infer") or {}).get("aux_refs", 0) or 0)

    def _ref_for(self, seg: ScriptSegment) -> Dict[str, Any]:
        if self.reference or not self.preset.get("match_reference"):
            return pick_reference(self.refs, seg.lang, seg.kind, self.reference)
        # 「完美」：同语言、同句型里，挑字数和这句话最接近的参考（同样接近时挑分数高的）
        same_lang = [r for r in self.refs if r.get("lang") == seg.lang] or list(self.refs)
        pool = [r for r in same_lang if r.get("kind") == seg.kind] or \
            [r for r in same_lang if r.get("kind") == "statement"] or same_lang
        if not pool:
            return pick_reference(self.refs, seg.lang, seg.kind)
        n = syllable_count(seg.text) + 1
        return min(enumerate(pool), key=lambda p: (round(abs(math.log((syllable_count(p[1].get("text", "")) + 1) / n)), 1),
                                                   p[0]))[1]

    def _tier_sig(self) -> List[Any]:
        return [self.quality, self.n_candidates, self.max_candidates, self.use_asr, self.adaptive, self.min_wrong,
                self.min_pct, self.filter_mode, self.target_pct,
                {k: self.preset.get(k) for k in ("cer_retry_threshold", "cer_target", "retry_rounds", "retry_candidates",
                                                 "early_after", "early_pct")}]

    def _plan(self, seg: ScriptSegment) -> _Plan:
        ref = self._ref_for(seg)
        aux = aux_references(self.refs, ref, self._n_aux())
        if not self.backend.supports_aux_refs:
            aux = []
        speed = self._speed_for(seg.lang)
        key = short_hash(CACHE_VERSION, self.backend.model_id(), seg.text, seg.lang, ref["id"], [a["id"] for a in aux],
                         round(speed, 3), self._tier_sig(), self.base_seed, n=16)
        wav_path, meta_path = self._cache_paths(key)
        return _Plan(ref, aux, speed, key, wav_path, meta_path)

    def _ensure_started(self, frac: Optional[float] = None) -> None:
        if self._started:
            return
        if frac is None:
            i, n = self._pos
            frac = self._gen_range[0] + (self._gen_range[1] - self._gen_range[0]) * i / max(n, 1)
        self._progress(frac, "启动合成引擎（第一次大约 1~2 分钟）……")
        self.backend.start()  # 已经在运行的服务也要调用：它会切换到这个声音的模型
        self._started = True

    def _warm_up(self, segments: Iterable[ScriptSegment]) -> None:
        """提前加载打分模型（第一次使用会下载），这样进度条能显示在做什么。"""
        self.scorer  # noqa: B018
        if self._checker is None:
            return
        need = {"paraformer" if self._checker.wants_paraformer(s.lang, s.text) else "whisper" for s in segments}
        for name in sorted(need):
            try:
                if name == "paraformer":
                    self._checker._load_paraformer()
                else:
                    self._checker._load()
            except Exception:
                pass

    # ------------------------------------------------------------------ 挑选
    def _cer_ok(self, c: _Cand, lang: str, thr: Optional[float] = None) -> bool:
        s = c.score
        if s.cer is None:
            return True
        if self.min_wrong > 1 and s.errors is not None and s.errors < self.min_wrong:
            return True  # 短句只错 1 个字（可能是识别误差）不算
        return s.cer <= (thr if thr is not None else self._thr("cer_retry_threshold", lang, 0.15, c))

    def _pct_ok(self, c: _Cand) -> bool:
        return not self.sim_filter or c.score.pct is None or c.score.pct >= self.min_pct

    def _select(self, cands: List[_Cand], lang: str, seg: Optional[ScriptSegment] = None) -> Tuple[_Cand, List[_Cand]]:
        alive = [c for c in cands if "几乎没有声音" not in c.score.issues] or cands
        survivors = [c for c in alive if self._pct_ok(c)]
        pool = survivors or alive
        # 读对的永远排在读错的前面；同一类里按综合分（相似度为主）。
        # 「完美」档（给了 seg）：达到全部严格标准的排在没达到的前面——综合分最高的不一定达标
        # （综合分里语速/音高偏差也要扣分），已经有达标的就要用达标的。
        if self.adaptive and seg is not None:
            best = max(pool, key=lambda c: (self._cer_ok(c, lang), self._meets_targets(c, seg), c.score.total))
        else:
            best = max(pool, key=lambda c: (self._cer_ok(c, lang), c.score.total))
        return best, survivors

    def _meets_targets(self, c: _Cand, seg: ScriptSegment) -> bool:
        s = c.score
        cer_ok = s.cer is None or s.cer <= self._thr("cer_target", seg.lang, 0.05, c) or s.errors == 0
        pct_ok = s.pct is None or not self.sim_filter or s.pct >= self.target_pct
        return bool(cer_ok and pct_ok and "几乎没有声音" not in s.issues
                    and self.scorer.in_normal_range(s, seg.lang, self._speed_multiplier()))

    def _target_miss(self, c: _Cand, seg: ScriptSegment) -> str:
        """「完美」档没达标时，按真正没达到的那一项写提示。"""
        s = c.score
        if self.sim_filter and s.pct is not None and s.pct < self.target_pct:
            return "这一句可能不够像，建议重新生成或改写"
        if s.cer is not None and not (s.cer <= self._thr("cer_target", seg.lang, 0.05, c) or s.errors == 0):
            return "这一句可能有个别字读得不太准，建议重新生成或改写"
        if not self.scorer.in_normal_range(s, seg.lang, self._speed_multiplier()):
            return "这一句的语速或音调和你平时不太一样，建议重新生成或改写"
        return "这一句可能不够像，建议重新生成或改写"

    def _clearly_good(self, c: _Cand, seg: ScriptSegment) -> bool:
        s = c.score
        thr = self._thr("cer_retry_threshold", seg.lang, 0.12, c)
        cer_ok = s.cer is None or s.cer <= thr / 2 or s.errors == 0
        pct_ok = s.pct is None or s.pct >= float(self.preset.get("early_pct", 99.0))
        return bool(cer_ok and pct_ok and "几乎没有声音" not in s.issues)

    def _retry_reason(self, cands: List[_Cand], seg: ScriptSegment) -> Optional[str]:
        if not cands:
            return "没生成成功"
        best, survivors = self._select(cands, seg.lang)
        if self.use_asr and not self._cer_ok(best, seg.lang):
            hyp = f"，识别为：{best.score.hyp}" if best.score.hyp else ""
            return f"有字读错了（错字率 {best.score.cer:.0%}{hyp}）"
        if self.sim_filter and not survivors:
            return f"不够像（最好的只有 {best.score.pct:.1f}%，低于 {self.min_pct:.0f}%）"
        return None

    # ------------------------------------------------------------------ 单句
    def _load_cached(self, seg: ScriptSegment, plan: _Plan) -> SegmentResult:
        meta = json.loads(plan.meta_path.read_text(encoding="utf-8"))
        wav, sr = load_audio(plan.wav_path)
        score = meta.get("score", {}) or {}
        return SegmentResult(seg, wav, sr, score, plan.ref["id"], True, meta.get("seed", 0), meta.get("candidates", []),
                             path=plan.wav_path, pct=score.get("pct"), status=meta.get("status", ""),
                             hint=meta.get("hint", ""), flagged=bool(meta.get("flagged")), tries=int(meta.get("tries", 0)),
                             met=meta.get("met"))

    def synthesize_segment(self, seg: ScriptSegment, force: bool = False) -> SegmentResult:
        plan = self._plan(seg)
        if plan.cached and not force:
            return self._load_cached(seg, plan)
        self._ensure_started()
        ref, aux, speed, key = plan.ref, plan.aux, plan.speed, plan.key
        seed0 = self.base_seed + seg.index * 7919
        if force:
            seed0 += random.randint(1, 10_000_000)
        tmp_dir = self.project.cache_dir / "tmp"
        tmp_dir.mkdir(parents=True, exist_ok=True)
        cands: List[_Cand] = []
        state = {"tried": 0, "last_exc": None}
        i, total_n = self._pos
        lo, hi = self._gen_range
        expected = 8 if self.adaptive else self.n_candidates
        mult = self._speed_multiplier()
        ref_audio = self.project.abspath(ref["path"])
        aux_paths = [self.project.abspath(a["path"]) for a in aux]

        def attempt(r_i: int, k: int, sampling: Optional[Dict[str, Any]], msg: str) -> None:
            _check_cancel()
            seed = seed0 + (r_i * 101 + k) * 104729
            sampling = sampling or {}
            req = SynthRequest(text=seg.text, lang=seg.lang, ref_audio=ref_audio, ref_text=ref["text"],
                               ref_lang=ref["lang"], aux_refs=list(aux_paths), seed=seed, speed=speed,
                               temperature=sampling.get("temperature"), top_k=sampling.get("top_k"),
                               top_p=sampling.get("top_p"))
            out = tmp_dir / f"{key}_{r_i}_{k}.wav"
            wav: Optional[np.ndarray] = None
            sr = 0
            try:
                self.backend.synthesize(req, out)
                wav, sr = load_audio(out)
            except Exception as exc:
                state["last_exc"] = exc
                log.warning(f"  第 {seg.index + 1} 句第 {state['tried'] + 1} 次生成失败：{exc}")
                if _is_fatal(exc):  # 显存不够、服务起不来……换个种子也没用
                    raise RuntimeError(f"第 {seg.index + 1} 句没能生成（原因：{_reason(exc)}）：{seg.text[:30]}") from exc
            finally:
                out.unlink(missing_ok=True)
                state["tried"] += 1
                self._progress(lo + (hi - lo) * (i + min(0.95, state["tried"] / max(expected, 1))) / max(total_n, 1), msg)
            if wav is None or wav.size == 0:
                return
            # 在裁剪前打分（语速测量需要首尾的静音作为底噪参考）
            score = self.scorer.score(wav, sr, seg.text, seg.lang, speed=mult, use_asr=self.use_asr)
            trimmed = trim_edges(wav, sr)
            if trimmed.size == 0:
                return
            cands.append(_Cand(score, seed, trimmed, sr, r_i, k))

        head = f"[{i + 1}/{total_n}]"
        met: Optional[bool] = None
        if self.adaptive:
            batch, cap, b = self.n_candidates, self.max_candidates, 0
            met = False
            while state["tried"] < cap:
                sampling = None if b % 3 == 0 else RETRY_SAMPLING[(b % 3) - 1]
                for k in range(min(batch, cap - state["tried"])):
                    n_try = state["tried"] + 1
                    msg = (f"{head} 第 {n_try}/{cap} 次尝试：{seg.display[:20]}" if b == 0 else
                           f"{head} 还没达到「完美」标准，继续试（第 {n_try}/{cap} 次）")
                    attempt(b, k, sampling, msg)
                # 任何一个候选达到全部严格标准就停（不只看综合分最高的那个）
                if any(self._meets_targets(c, seg) for c in cands):
                    met = True
                    break
                if not cands and state["tried"] >= 2 * batch:
                    break  # 一直生成不出来：不再浪费时间
                b += 1
        else:
            retry_n = int(self.preset.get("retry_candidates", 2) or 0)
            rounds: List[Tuple[int, Optional[Dict[str, Any]]]] = [(self.n_candidates, None)]
            for r in range(int(self.preset.get("retry_rounds", 0) or 0)):
                rounds.append((retry_n, RETRY_SAMPLING[min(r, len(RETRY_SAMPLING) - 1)]))
            early_after = int(self.preset.get("early_after", 0) or 0)
            for r_i, (n, sampling) in enumerate(rounds):
                reason = ""
                if r_i > 0:
                    reason = self._retry_reason(cands, seg) or ""
                    if not reason:
                        break
                    log.info(f"  第 {seg.index + 1} 句{reason}，重新生成（第 {r_i} 次）……")
                for k in range(n):
                    if r_i == 0:
                        msg = f"{head} 第 {k + 1}/{n} 个版本：{seg.display[:20]}"
                    elif reason.startswith("有字读错"):
                        msg = f"{head} 有字读错了，重新生成（第 {r_i} 次）"
                    else:
                        msg = f"{head} 不够像，重新生成（第 {r_i} 次）"
                    attempt(r_i, k, sampling, msg)
                    if (r_i == 0 and early_after and k + 1 == early_after and k + 1 < n and cands
                            and self._clearly_good(self._select(cands, seg.lang)[0], seg)):
                        log.info(f"  第 {seg.index + 1} 句前 {early_after} 个版本里已经有很好的，提前结束")
                        break
        if not cands:
            exc = state["last_exc"]
            why = _reason(exc) if exc is not None else "生成的音频是空的"
            raise RuntimeError(f"第 {seg.index + 1} 句没能生成（原因：{why}）：{seg.text[:30]}") from exc

        best, survivors = self._select(cands, seg.lang, seg)
        if self.adaptive:
            met = self._meets_targets(best, seg)
        filt = self.sim_filter
        hints: List[str] = []
        if filt and best.score.pct is not None and best.score.pct < self.min_pct:
            hints.append(f"低于 {self.min_pct:.0f}%，建议重新生成或改写这一句")
        if self.use_asr and not self._cer_ok(best, seg.lang):
            hints.append("可能有读错的字" + (f"（识别为：{best.score.hyp}）" if best.score.hyp else "") + "，建议重新生成或改写这一句")
        if self.adaptive and not met and not hints:
            hints.append(self._target_miss(best, seg))
        issues = list(best.score.issues)
        pct = best.score.pct
        if filt and pct is not None:
            status = status_for_pct(pct, self.min_pct)
            if status != "🔴" and (hints or issues):
                status = "⚠️"
        else:
            status = "⚠️" if (hints or issues) else "✅"
        flagged = bool(hints or issues)
        cand_info = []
        for c in cands:
            d = c.score.to_dict()
            cand_info.append({"seed": c.seed, "pct": d.get("pct"), "cer": d.get("cer"), "errors": d.get("errors"),
                              "total": d.get("total"), "speaker_sim": d.get("speaker_sim"), "round": c.round,
                              "eliminated": bool(filt and c.score.pct is not None and c.score.pct < self.min_pct),
                              "chosen": c is best})
        cand_info.sort(key=lambda d: (d["pct"] is None, -(d["pct"] or 0.0), -(d["total"] or 0.0)))
        save_audio(plan.wav_path, best.wav, best.sr)
        # 重新生成（--redo / 只重新生成第几句）会写到同一个缓存文件：旁边旧的「去杂音」版本是旧句子做的，必须删掉，
        # 否则长度刚好一样时版本 B 里还是旧的那句
        for old in plan.wav_path.parent.glob(plan.wav_path.stem + ".dn*.wav"):
            old.unlink(missing_ok=True)
        score = best.score.to_dict()
        meta = {"text": seg.text, "lang": seg.lang, "ref": ref["id"], "seed": best.seed, "score": score,
                "candidates": cand_info, "model": self.backend.model_id(), "quality": self.quality,
                "tries": state["tried"], "met": met, "hint": "；".join(hints), "status": status, "flagged": flagged,
                "created": time.strftime("%Y-%m-%d %H:%M:%S")}
        plan.meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
        return SegmentResult(seg, best.wav, best.sr, score, ref["id"], False, best.seed, cand_info, path=plan.wav_path,
                             pct=pct, status=status, hint=meta["hint"], flagged=flagged, tries=state["tried"], met=met)

    # ------------------------------------------------------------------ 整篇
    def _segments(self, source: Union[str, Path, Sequence[ScriptSegment]]) -> List[ScriptSegment]:
        if isinstance(source, (list, tuple)):
            return list(source)
        return parse_script(
            source, lexicon=self.project.load_lexicon(),
            max_units_zh=int(self.scfg.get("max_units_zh", 50)), max_units_en=int(self.scfg.get("max_units_en", 45)),
            min_units=int(self.scfg.get("min_units", 6)), skip_code_blocks=bool(self.scfg.get("skip_code_blocks", True)),
        )

    def _desc(self) -> str:
        if self.adaptive:
            return f"每句最多试 {self.max_candidates} 次，达到严格标准就停"
        if self.n_candidates > 1:
            return f"每句做 {self.n_candidates} 遍，挑最像你的"
        return "每句做 1 遍"

    def synthesize_all(self, segments: List[ScriptSegment], redo: Iterable[int] = ()) -> List[SegmentResult]:
        """逐句合成（含缓存）。redo 是从 1 开始的句子编号（和结果表的 # 一样）。"""
        n = len(segments)
        redo_set, bad = set(), []
        for x in redo:
            try:
                v = int(x)
            except (TypeError, ValueError):
                continue
            if 1 <= v <= n:
                redo_set.add(v - 1)  # 用户看到的编号从 1 开始
            else:
                bad.append(v)
        if bad:
            msg = f"讲稿只有 {n} 句，第 {'、'.join(str(b) for b in sorted(set(bad)))} 句不存在，已跳过"
            self.warnings.append(msg)
            log.warning(msg)
        lo, hi = self._gen_range
        plans = [self._plan(s) for s in segments]
        need_engine = any(i in redo_set or not p.cached for i, p in enumerate(plans))
        if need_engine and not self._started:
            self._ensure_started(0.0)
            self._progress(0.02, "加载打分模型（第一次使用会先下载）……")
            self._warm_up(segments)
        self._progress(lo, f"开始生成，共 {n} 句（{self._desc()}）")
        results: List[SegmentResult] = []
        for i, seg in enumerate(segments):
            _check_cancel()
            self._pos = (i, n)
            res = self.synthesize_segment(seg, force=i in redo_set)
            results.append(res)
            tag = "已有，直接用" if res.cached else "生成"
            pct = res.pct
            msg = f"[{i + 1}/{n}] {tag}：{seg.display[:20]}" + (f"（像你本人 {pct:.1f}%）" if pct is not None else "")
            log.info(msg)
            self._progress(lo + (hi - lo) * (i + 1) / max(n, 1), msg)
            for issue in res.score.get("issues") or []:
                self.warnings.append(f"第 {i + 1} 句：{issue}")
            if res.hint:
                self.warnings.append(f"第 {i + 1} 句：{res.hint}")
        return results

    def synthesize_text(self, text: Union[str, Sequence[ScriptSegment]]) -> Tuple[np.ndarray, int, List[SegmentResult]]:
        """合成一段文字，返回拼好的波形（停顿是绝对静音），不写输出文件（盲听测试、试听语速用）。"""
        segments = self._segments(text)
        if not segments:
            raise ValueError("讲稿里没有可以朗读的内容")
        if not self.refs:
            raise RuntimeError("这个声音还没有参考音频，请先完成素材准备（voicetwin prepare）")
        results = self.synthesize_all(segments)
        layout = self._layout(results)
        sr = max(r.sr for r in results)
        return self._render(layout, [(r.wav, r.sr) for r in results], sr), sr, results

    def narrate(self, source: Union[str, Path, Sequence[ScriptSegment]], out_path: Union[str, Path],
                redo: Iterable[int] = (), subtitles: Optional[bool] = None) -> NarrationResult:
        segments = self._segments(source)
        if not segments:
            raise ValueError("讲稿里没有可以朗读的内容")
        if not self.refs:
            raise RuntimeError("这个声音还没有参考音频，请先完成素材准备（voicetwin prepare）")
        out_path = Path(out_path)
        variants_on = self.want_variants
        self._gen_range = (0.03, 0.90) if variants_on else (0.03, 0.95)
        log.info(f"共 {len(segments)} 句，引擎 {self.backend.display_name}，质量「{QUALITY_SHORT[self.quality]}」"
                 f"（{self._desc()}{'，识别校验' if self.use_asr else ''}）")
        t0 = time.time()
        results = self.synthesize_all(segments, redo)

        assemble_at = self._gen_range[1]
        self._progress(assemble_at, "拼接音频、调整音量、生成字幕……")
        layout = self._layout(results)
        sr = max(r.sr for r in results)
        audio_a = self._render(layout, [(r.wav, r.sr) for r in results], sr)
        mult = self._speed_multiplier()

        variants: List[Dict[str, Any]] = []
        final_name = ""
        if variants_on:
            self._progress(0.93, "做「去杂音」版本，并比较哪个版本更像你……")
            variants, audio_by_name = self._make_variants(results, layout, audio_a, sr, mult)
            rec = next(v for v in variants if v["recommended"])
            final_name = rec["name"]
            stem, fmt = out_path.stem, (out_path.suffix or f".{self.scfg.get('output_format', 'wav')}")
            for v in variants:
                path = self._write_audio(audio_by_name[v["name"]], sr, out_path.with_name(f"{stem}_{v['name']}{fmt}"))
                v["path"] = str(path)
            final = Path(next(v["path"] for v in variants if v["recommended"]))
            target = final.with_name(f"{stem}{final.suffix}")
            shutil.copyfile(final, target)
            final = target
            for v in variants:
                v["final"] = v["name"] == final_name
            audio_main = audio_by_name[final_name]
        else:
            final = self._write_audio(audio_a, sr, out_path)
            audio_main = audio_a
        srt_path = None
        if subtitles if subtitles is not None else self.scfg.get("subtitles", True):
            srt_path = self._write_srt(results, final.with_suffix(".srt"))

        seg_report = self._seg_report(results)
        sims = [s["speaker_sim"] for s in seg_report if s.get("speaker_sim") is not None]
        overall = _weighted_pct(results)
        if variants:  # 两个版本时，整篇百分比用最终版本的（和版本卡片上的数字一致）
            final_pct = next((v.get("pct") for v in variants if v.get("final")), None)
            overall = final_pct if final_pct is not None else overall
        flagged = sorted(s["index"] for s in seg_report if s.get("flagged"))
        notes = list(self.notes) + self._summary_lines(results, flagged, overall)
        for line in notes:
            log.info(line)
        judge = self.judge
        report = {
            "audio": str(final), "backend": self.backend.name, "model": self.backend.model_id(),
            "quality": self.quality, "quality_label": QUALITY_LABELS[self.quality],
            "duration": round(len(audio_main) / sr, 2), "speed": round(mult, 3),
            "mean_speaker_sim": round(float(np.mean(sims)), 4) if sims else None,
            "overall_pct": overall, "min_pct": self.min_pct, "similarity_filter": self.sim_filter,
            "similarity": judge.info() if judge is not None else {"models": [], "note": HONEST_NOTE},
            "elapsed_sec": round(time.time() - t0, 1), "warnings": self.warnings, "flagged": flagged,
            "notes": notes, "variants": variants, "final": final_name, "segments": seg_report,
            "tries_avg": round(float(np.mean([r.tries for r in results if not r.cached])), 2)
            if any(not r.cached for r in results) else None,
        }
        report_path = final.with_suffix(".report.json")
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
        self._progress(1.0, f"完成：{final.name}")
        return NarrationResult(final, srt_path, report_path, len(audio_main) / sr, seg_report, self.warnings,
                               flagged=flagged, variants=variants, quality=self.quality, overall_pct=overall, notes=notes)

    def say(self, text: str, out_path: Union[str, Path]) -> NarrationResult:
        return self.narrate(text, out_path, subtitles=False)

    # ------------------------------------------------------------------ 报告
    def _seg_report(self, results: List[SegmentResult]) -> List[Dict[str, Any]]:
        out = []
        for r in results:
            entry = {
                "index": r.segment.index + 1, "text": r.segment.display, "tts_text": r.segment.text,
                "lang": r.segment.lang, "start": round(r.start, 3), "end": round(r.end, 3), "ref": r.ref_id,
                "cached": r.cached, "seed": r.seed,
                **{k: v for k, v in r.score.items() if k in ("speaker_sim", "cer", "rate", "issues", "pct", "pcts",
                                                              "sims", "hyp")},
                "pct": r.pct, "status": r.status, "hint": r.hint, "flagged": r.flagged, "tries": r.tries,
                "met": r.met, "candidates": r.candidates,
            }
            if r.path is not None:
                entry["clip"] = self.project.relpath(r.path)
            out.append(entry)
        return out

    def _summary_lines(self, results: List[SegmentResult], flagged: List[int],
                       overall: Optional[float] = None) -> List[str]:
        fresh = [r for r in results if not r.cached]
        lines = []
        if fresh:
            avg = float(np.mean([r.tries for r in fresh]))
            line = f"本次生成：共 {len(results)} 句（新生成 {len(fresh)} 句），平均每句试了 {avg:.1f} 次"
            if self.adaptive:
                met = sum(1 for r in fresh if r.met)
                line += f"；{met} 句达到了「完美」的严格标准"
            lines.append(line + "。")
        else:
            lines.append(f"本次生成：共 {len(results)} 句，全部用的是之前生成好的结果。")
        if overall is None:
            overall = _weighted_pct(results)
        if overall is not None:
            lines.append(f"整篇像你本人 {overall:.1f}%（{PCT_HELP}；{HONEST_NOTE}）。")
        if flagged:
            lines.append("需要注意的句子：第 " + "、".join(str(n) for n in flagged) + " 句（可以只重做这几句）。")
        else:
            lines.append("没有需要特别注意的句子。")
        return lines

    # ------------------------------------------------------------------ 两个版本（「完美」档）
    def _step(self, lo: float, hi: float, k: int, n: int, msg: str) -> None:
        """长循环里的进度（每 10 句报一次，最后一句也报）。"""
        if k % 10 == 0 or k == n:
            self._progress(lo + (hi - lo) * k / max(n, 1), f"{msg} {k}/{n}")

    def _version_score(self, wavs: List[np.ndarray], results: List[SegmentResult], sr: int, mult: float,
                       rng: Tuple[float, float] = (0.0, 0.0), label: str = ""
                       ) -> Tuple[float, Optional[float], List[Optional[float]]]:
        """同一个标准给整篇打分：每句（相似度为主 − 语速/音高偏差）按时长加权平均；同时给出整篇百分比。"""
        totals, weights, pcts = [], [], []
        for k, (wav, r) in enumerate(zip(wavs, results), 1):
            _check_cancel()
            if label:
                self._step(rng[0], rng[1], k, len(wavs), label)
            s = self.scorer.score(wav, sr, r.segment.text, r.segment.lang, speed=mult, use_asr=False,
                                  check_pauses=False)
            dur = len(wav) / sr
            totals.append(s.total)
            weights.append(dur)
            pcts.append(s.pct)
        w = np.asarray(weights, dtype=np.float64)
        score = float(np.average(totals, weights=w)) if w.sum() > 0 else float(np.mean(totals))
        valid = [(p, d) for p, d in zip(pcts, weights) if p is not None]
        pct = round(float(np.average([p for p, _ in valid], weights=[d for _, d in valid])), 1) \
            if valid and sum(d for _, d in valid) > 0 else None
        return round(score, 4), pct, pcts

    def _make_variants(self, results: List[SegmentResult], layout: List[Tuple[float, int]], audio_a: np.ndarray,
                       sr: int, mult: float) -> Tuple[List[Dict[str, Any]], Dict[str, np.ndarray]]:
        wavs_a = [resample(r.wav, r.sr, sr) for r in results]
        n = len(results)
        score_a, pct_a, _ = self._version_score(wavs_a, results, sr, mult, (0.93, 0.95), "给「未去杂音」版本打分")
        variants = [{"name": VARIANT_RAW, "label": "版本 A：未去杂音", "score": score_a, "pct": pct_a}]
        audio_by_name = {VARIANT_RAW: audio_a}
        wavs_b: List[np.ndarray] = []
        for k, (r, w) in enumerate(zip(results, wavs_a), 1):
            _check_cancel()
            self._step(0.95, 0.97, k, n, "去杂音")
            dn = self._denoised(r, w, sr)
            if dn is None:
                wavs_b = []
                break
            wavs_b.append(dn)
        if wavs_b:
            audio_b = self._render(layout, [(w, sr) for w in wavs_b], sr)
            score_b, pct_b, _ = self._version_score(wavs_b, results, sr, mult, (0.97, 0.99), "给「去杂音」版本打分")
            variants.append({"name": VARIANT_DENOISED, "label": "版本 B：去杂音", "score": score_b, "pct": pct_b})
            audio_by_name[VARIANT_DENOISED] = audio_b
        else:
            msg = ("没有安装 noisereduce，这次只生成了「未去杂音」一个版本（想要「去杂音」版本，"
                   "请重新双击 install_windows.bat 安装一次，安装程序会自动装上它）")
            self.warnings.append(msg)
            self.notes.append(msg)
            log.warning(msg)
        best = max(variants, key=lambda v: (v["score"], v["name"] == VARIANT_RAW))  # 一样高时用没处理过的
        for rank, v in enumerate(sorted(variants, key=lambda v: (-v["score"], v["name"] != VARIANT_RAW)), 1):
            v["rank"] = rank
        for v in variants:
            v["recommended"] = v is best
        if len(variants) > 1:
            other = next(v for v in variants if v is not best)
            if best.get("pct") is not None and other.get("pct") is not None:
                gap = float(best["pct"]) - float(other["pct"])
                detail = f"像你本人 {best['pct']:.1f}%，另一个版本 {other['pct']:.1f}%，相差 {gap:.1f}%；"
            else:
                detail = ""
            line = (f"⭐ 推荐：{best['label']}，更像你的原声（{detail}"
                    f"综合分 {best['score']:.3f} 对 {other['score']:.3f}）")
            self.notes.append(line)  # 最后和小结一起写进日志
        return variants, audio_by_name

    def _denoised(self, r: SegmentResult, wav: np.ndarray, sr: int) -> Optional[np.ndarray]:
        """这一句的去杂音版本（缓存在这句旁边，下次不用重算）。没有 noisereduce 时返回 None。"""
        cache = r.path.with_name(r.path.stem + f".dn{sr}.wav") if r.path is not None else None
        if cache is not None and cache.exists():
            try:
                # 比这句的音频还旧的去杂音版本不能用（这句后来重新生成过）
                fresh = not r.path.exists() or cache.stat().st_mtime >= r.path.stat().st_mtime
                w, s = load_audio(cache)
                if fresh and s == sr and len(w) == len(wav):
                    return w
            except Exception:
                pass
        out = denoise_light(wav, sr)
        if out is None:
            return None
        if cache is not None:
            try:
                save_audio(cache, out, sr, subtype="FLOAT")
            except Exception:
                pass
        return out

    # ------------------------------------------------------------------ 拼接
    def _pause(self, seg: ScriptSegment, i: int) -> float:
        kind = seg.pause_after
        if isinstance(kind, (int, float)):
            return float(kind)
        if self.scfg.get("pauses", "profile") == "fixed":
            return pause_seconds(self.profile, kind, self.scfg.get("fixed_pauses") or {})
        lo, hi = pause_range(self.profile, kind)
        base = pause_seconds(self.profile, kind)
        rng = random.Random(self.base_seed + i)
        # 在你的常见停顿范围内轻微波动（偏向中位数），避免机械感
        val = base + (rng.random() - 0.5) * (hi - lo) * 0.6
        return float(max(0.08, val))

    def _layout(self, results: List[SegmentResult]) -> List[Tuple[float, int]]:
        """算出每句的起点（秒）和长度（采样数），写进 r.start / r.end。字幕和两个版本都用同一套时间。"""
        sr = max(r.sr for r in results)
        timed = any(r.segment.cue_start is not None for r in results)
        mult = self._speed_multiplier()
        cursor = LEAD_IN
        layout: List[Tuple[float, int]] = []
        for i, r in enumerate(results):
            n = len(resample(r.wav, r.sr, sr)) if r.sr != sr else len(r.wav)
            if timed and r.segment.cue_start is not None:
                start = r.segment.cue_start
                if start < cursor - 0.02:
                    if start + 0.5 < cursor:
                        self.warnings.append(f"第 {i + 1} 句比字幕时间轴晚了 {cursor - start:.1f} 秒（上一句太长）")
                    start = cursor
            else:
                start = cursor
            r.start, r.end = start, start + n / sr
            layout.append((start, n))
            if timed:
                cursor = r.end + (0.08 if r.segment.pause_after == "clause" else 0.0)
            else:
                pause = self._pause(r.segment, i)
                if not isinstance(r.segment.pause_after, (int, float)):
                    pause /= mult  # 说得慢，停顿也按比例长一点（讲稿里写明的秒数不变）
                cursor = r.end + pause
        return layout

    def _render(self, layout: List[Tuple[float, int]], pieces: List[Tuple[np.ndarray, int]], sr: int) -> np.ndarray:
        """按排好的时间把每句放进一条全是 0 的音轨：停顿、开头、结尾都是绝对的数字静音。"""
        total = (max((start + n / sr for start, n in layout), default=0.0)) + LEAD_OUT
        out = np.zeros(int(total * sr) + 1, dtype=np.float32)
        for (start, n), (wav, wsr) in zip(layout, pieces):
            w = resample(wav, wsr, sr) if wsr != sr else np.asarray(wav, dtype=np.float32)
            w = fade(w[:n], sr, in_ms=4.0, out_ms=8.0)
            a = int(round(start * sr))
            w = w[: max(0, len(out) - a)]
            out[a:a + len(w)] += w
        return out

    def _target_lufs(self) -> Optional[float]:
        opt = self.scfg.get("loudness", "profile")
        if opt in (None, "off", False):
            return None
        if opt == "profile":
            loud = self.profile.get("loudness") or {}
            val = loud.get("source_lufs") or loud.get("clip_lufs")
            return float(val) if val is not None else -18.0
        return float(opt)

    def _write_audio(self, audio: np.ndarray, sr: int, out_path: Path) -> Path:
        target = self._target_lufs()
        if target is not None:
            audio = normalize_lufs(audio, sr, target, ceiling_db=-1.0)  # 只乘一个系数：0 还是 0
        fmt = (out_path.suffix.lower().lstrip(".") or self.scfg.get("output_format", "wav"))
        wav_path = out_path.with_suffix(".wav")
        save_audio(wav_path, audio, sr)
        log.info(f"输出响度 {measure_lufs(audio, sr):.1f} LUFS，时长 {len(audio) / sr:.1f} 秒")
        if fmt in ("mp3", "m4a", "flac"):
            final = encode(wav_path, out_path.with_suffix("." + fmt))
            wav_path.unlink(missing_ok=True)
            return final
        return wav_path

    def _write_srt(self, results: List[SegmentResult], path: Path) -> Path:
        from voicetwin.data.subtitles import Cue, write_srt

        cues = [Cue(r.start, r.end, r.segment.display) for r in results]
        return write_srt(cues, path)


def _weighted_pct(results: List[SegmentResult]) -> Optional[float]:
    vals = [(r.pct, max(r.end - r.start, len(r.wav) / max(r.sr, 1))) for r in results if r.pct is not None]
    if not vals or sum(d for _, d in vals) <= 0:
        return None
    return round(float(np.average([p for p, _ in vals], weights=[d for _, d in vals])), 1)


def _reason(exc: Optional[BaseException]) -> str:
    if exc is None:
        return "未知原因"
    try:
        from voicetwin.errors import explain

        return explain(exc).title
    except Exception:
        return str(exc)[:80]


def _is_fatal(exc: BaseException) -> bool:
    try:
        from voicetwin.errors import is_fatal

        return bool(is_fatal(exc))
    except Exception:
        return False


def result_rows(segments: Sequence[Dict[str, Any]]) -> List[List[Any]]:
    """逐句结果表（#, 句子, 像你本人（%）, 状态, 提示），# 从 1 开始，和 --redo 的编号一致。"""
    rows = []
    for s in segments:
        pct = s.get("pct")
        hint = s.get("hint") or "；".join(s.get("issues") or [])
        rows.append([s.get("index"), s.get("text", ""), "" if pct is None else f"{pct:.1f}",
                     s.get("status") or ("⚠️" if hint else "✅"), hint])
    return rows


def clear_cache(project: Project) -> int:
    seg_dir = project.cache_dir / "segments"
    n = sum(1 for p in seg_dir.rglob("*.wav") if ".dn" not in p.name) if seg_dir.exists() else 0
    shutil.rmtree(seg_dir, ignore_errors=True)
    return n
