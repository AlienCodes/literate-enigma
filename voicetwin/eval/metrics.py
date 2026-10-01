"""给合成结果打分：像不像你（声纹）、读得对不对（识别错字率）、节奏像不像（语速/音高）。"""

from __future__ import annotations

import importlib.util
import math
import os
import re
import threading
import unicodedata
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

import numpy as np

from voicetwin.style.profile import target_rate
from voicetwin.style.prosody import f0_stats
from voicetwin.utils.audio import clip_ratio, resample, speech_activity
from voicetwin.utils.log import get_logger
from voicetwin.utils.textutil import ALL_PUNCT_RE, CJK_RE, NUM_RUN_RE, syllable_count, to_simplified

log = get_logger("metrics")
ProgressFn = Callable[[float, str], None]

#: GPT-SoVITS 整合包自带的 Paraformer（中文识别，和 VoiceTwin 素材准备用的 Whisper 不是同一个模型）
PARAFORMER_LOCAL = "tools/asr/models/speech_paraformer-large_asr_nat-zh-cn-16k-common-vocab8404-pytorch"
PARAFORMER_ID = "iic/speech_paraformer-large_asr_nat-zh-cn-16k-common-vocab8404-pytorch"
STRONG_MODELS = ("paraformer", "large-v3", "large-v2", "large-v3-turbo")
_LATIN = re.compile(r"[A-Za-z]")


def engine_is_strong(engine: str) -> bool:
    """识别校验引擎名（paraformer / whisper-small / whisper-large-v3-turbo ……）是不是"准"的那种。"""
    name = str(engine or "")
    if name.startswith("whisper-"):
        name = name[len("whisper-"):]
    return any(name.startswith(s) for s in STRONG_MODELS)


def _has_module(mod: str) -> bool:
    try:
        return importlib.util.find_spec(mod) is not None
    except Exception:
        return False


# ============================================================================ 错字率（同音字不算错）
def _pinyin_fn() -> Optional[Callable[[str], List[str]]]:
    try:
        from pypinyin import Style, lazy_pinyin  # type: ignore
    except Exception:
        return None

    def conv(ch: str) -> List[str]:
        return lazy_pinyin(ch, style=Style.NORMAL, errors="default")

    return conv


_NUM = "\ue000"  # 数字串的占位符（不会被当成标点去掉）


def _normalize(text: str) -> str:
    """去标点、转简体、小写；数字串（2024 / 二零二四）统一成一个占位符，漏读数字也能算出来。"""
    text = unicodedata.normalize("NFKC", text or "")
    text = to_simplified(text).lower()
    text = NUM_RUN_RE.sub(_NUM, text)
    return ALL_PUNCT_RE.sub("", text)


def _units(text: str, pinyin: Optional[Callable[[str], List[str]]]) -> List[str]:
    norm = _normalize(text)
    if pinyin is None:
        return list(norm)
    out: List[str] = []
    for ch in norm:
        if CJK_RE.match(ch):
            py = pinyin(ch)
            out.append(py[0] if py else ch)
        else:
            out.append(ch)
    return out


def _seq_distance(a: List[str], b: List[str]) -> int:
    if a == b:
        return 0
    if len(a) < len(b):
        a, b = b, a
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def cer_details(reference: str, hypothesis: str, lang: str = "zh", use_pinyin: bool = True) -> Tuple[float, int, int]:
    """返回 (错字率, 错了几个字, 一共几个字)。

    中文在装了 pypinyin（GPT-SoVITS 整合包里有）时按不带声调的拼音比较：识别模型把「他/她」「在/再」听混
    不算合成读错——合成是按读音来的。没有 pypinyin 时按字比较。数字串统一处理（2024 = 二零二四）。
    """
    pinyin = _pinyin_fn() if (use_pinyin and lang == "zh") else None
    ref = _units(reference, pinyin)
    hyp = _units(hypothesis, pinyin)
    if not ref:
        return (0.0 if not hyp else 1.0), len(hyp), 0
    errors = _seq_distance(ref, hyp)
    return errors / len(ref), errors, len(ref)


# ============================================================================ 识别校验
class CERChecker:
    """把合成音频识别回文字，和原文比对，找出漏字、多字、读错。

    model="auto"：中文句子优先用 GPT-SoVITS 整合包自带的 Paraformer（中文错字率约 2%，Whisper small 约 10%）；
    没有 funasr 时，显存 ≥ 8GB 用 faster-whisper large-v3-turbo（int8_float16，约 1.5GB 显存），否则用 small。
    """

    def __init__(self, model: str = "small", device: str = "auto", progress: Optional[ProgressFn] = None,
                 vram_tier: Optional[str] = None, gsv_root: Optional[Path] = None,
                 progress_range: Tuple[float, float] = (0.0, 0.0)):
        self.model_name = str(model or "small")
        self.device = device
        self.progress = progress
        self.progress_range = progress_range
        self.vram_tier = vram_tier
        self.gsv_root = Path(gsv_root) if gsv_root else None
        self._model = None  # 兼容旧代码：Whisper 的 Transcriber
        self._para = None
        self._para_failed = False
        self.available = True
        self._lock = threading.Lock()

    # ------------------------------------------------------------------ 选模型
    def whisper_model(self) -> str:
        if self.model_name not in ("auto", "", "paraformer"):
            return self.model_name
        return "large-v3-turbo" if self.vram_tier in ("mid", "high") else "small"

    def wants_paraformer(self, lang: str, text: str = "") -> bool:
        """中文句子用 Paraformer；句子里有英文单词时不用（Paraformer 拼不出英文，会把 Python 识别成"派森"，误判成读错）。"""
        if lang != "zh" or self._para_failed or _LATIN.search(text or ""):
            return False
        if self.model_name == "paraformer":
            return True
        return self.model_name == "auto" and _has_module("funasr")

    def engine_name(self, lang: str = "zh", text: str = "") -> str:
        return "paraformer" if self.wants_paraformer(lang, text) else f"whisper-{self.whisper_model()}"

    def strong(self, lang: str = "zh", text: str = "") -> bool:
        """识别模型够不够准：准的模型可以用更严格的错字门槛（弱模型本身就有 5~10% 的误差）。"""
        return engine_is_strong(self.engine_name(lang, text))

    # ------------------------------------------------------------------ 加载
    def _load(self) -> bool:
        if self._model is not None:
            return True
        if not self.available:
            return False
        with self._lock:
            if self._model is not None:
                return True
            try:
                from voicetwin.data.asr import Transcriber

                name = self.whisper_model()
                compute = "int8_float16" if name.startswith("large") else "auto"
                model = Transcriber({"engine": "faster-whisper", "model": name, "device": self.device,
                                     "compute_type": compute, "beam_size": 1,
                                     "initial_prompt_zh": "以下是普通话的句子，使用简体中文和标点符号。"})
                model.progress = self.progress
                model.progress_range = self.progress_range
                model.download_label = "识别校验模型"
                model._load()
                self._model = model
                return True
            except Exception as exc:
                log.warning(f"识别校验不可用（{exc}），将只用声纹和节奏打分")
                self.available = False
                self._model = None
                return False

    def _paraformer_path(self) -> str:
        cands: List[Path] = []
        if self.gsv_root is not None:
            cands.append(self.gsv_root / PARAFORMER_LOCAL)
        ms_cache = os.environ.get("MODELSCOPE_CACHE") or str(Path.home() / ".cache" / "modelscope" / "hub")
        cands += [Path(ms_cache) / PARAFORMER_ID, Path(ms_cache) / "iic" / Path(PARAFORMER_LOCAL).name]
        for c in cands:
            if (c / "configuration.json").exists() or ((c / "config.yaml").exists() and (c / "model.pt").exists()):
                return str(c)
        return PARAFORMER_ID

    def _load_paraformer(self) -> bool:
        if self._para is not None:
            return True
        if self._para_failed:
            return False
        with self._lock:
            if self._para is not None:
                return True
            try:
                from funasr import AutoModel  # type: ignore  # 导入较慢，只在这里导入

                from voicetwin.data.asr import _auto_device

                path = self._paraformer_path()
                device = _auto_device(self.device)
                log.info(f"加载中文识别校验模型 Paraformer（{device}）……")
                self._para = AutoModel(model=path, model_revision="v2.0.4", device="cuda:0" if device == "cuda" else "cpu",
                                       disable_update=True, disable_pbar=True, disable_log=True, check_latest=False)
                return True
            except Exception as exc:
                log.warning(f"Paraformer 用不了（{exc}），改用 Whisper 做识别校验")
                self._para_failed = True
                self._para = None
                return False

    # ------------------------------------------------------------------ 识别
    def _paraformer_text(self, wav16: np.ndarray) -> str:
        from voicetwin.utils.textutil import clean_transcript, to_simplified

        res = self._para.generate(input=wav16)
        text = res[0].get("text", "") if res else ""
        return clean_transcript(to_simplified(text))

    def check(self, wav: np.ndarray, sr: int, text: str, lang: str) -> Optional[Dict[str, Any]]:
        wav16 = resample(wav, sr, 16000)
        hyp: Optional[str] = None
        engine = ""
        if self.wants_paraformer(lang, text) and self._load_paraformer():
            try:
                hyp = self._paraformer_text(wav16)
                engine = "paraformer"
            except Exception as exc:
                log.warning(f"Paraformer 识别失败（{exc}），这一句改用 Whisper")
                hyp = None
        if hyp is None:
            if not self._load():
                return None
            hyp = self._model.transcribe(wav16, language=lang).text
            engine = f"whisper-{self.whisper_model()}"
        rate, errors, units = cer_details(text, hyp, lang)
        return {"cer": rate, "hyp": hyp, "errors": errors, "units": units, "engine": engine,
                "strong": engine_is_strong(engine)}


# ============================================================================ 打分
@dataclass
class Score:
    total: float
    speaker_sim: Optional[float] = None
    cer: Optional[float] = None
    hyp: Optional[str] = None
    rate: Optional[float] = None
    rate_dev: Optional[float] = None
    pitch_dev: Optional[float] = None
    issues: List[str] = field(default_factory=list)
    pct: Optional[float] = None                       # 像你本人（%），几个声纹模型校准后的平均
    pcts: Dict[str, float] = field(default_factory=dict)   # 每个声纹模型的百分比
    sims: Dict[str, float] = field(default_factory=dict)   # 每个声纹模型的原始余弦相似度
    errors: Optional[int] = None                       # 识别出来错了几个字
    f0: Optional[float] = None                         # 音高中位数（Hz）
    checker: str = ""

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        out: Dict[str, Any] = {}
        for k, v in d.items():
            if isinstance(v, float):
                out[k] = round(v, 4)
            elif isinstance(v, dict):
                out[k] = {kk: (round(vv, 4) if isinstance(vv, float) else vv) for kk, vv in v.items()}
            else:
                out[k] = v
        return out

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Score":
        known = {k: d[k] for k in cls.__dataclass_fields__ if k in d}  # type: ignore[attr-defined]
        known.setdefault("total", 0.0)
        return cls(**known)


class Scorer:
    def __init__(self, profile: Dict[str, Any], centroid: Optional[np.ndarray], encoder: Any,
                 weights: Optional[Dict[str, float]] = None, cer_checker: Optional[CERChecker] = None,
                 judge: Any = None):
        self.profile = profile or {}
        self.centroid = centroid
        self.encoder = encoder
        w = {"speaker": 1.0, "cer": 2.0, "rate": 0.6, "pitch": 0.3}
        w.update({k: float(v) for k, v in (weights or {}).items() if isinstance(v, (int, float))})
        self.w = w
        self.cer_checker = cer_checker
        self.judge = judge if (judge is not None and getattr(judge, "available", False)) else None

    def score(self, wav: np.ndarray, sr: int, text: str, lang: str, speed: float = 1.0,
              use_asr: bool = True, check_pauses: bool = True) -> Score:
        issues: List[str] = []
        total = 0.0
        sim = None
        pct: Optional[float] = None
        pcts: Dict[str, float] = {}
        sims: Dict[str, float] = {}
        if wav.size > sr * 0.3:
            if self.judge is not None:
                res = self.judge.judge(wav, sr)
                sim, pct, pcts, sims = res.get("sim"), res.get("pct"), res.get("pcts") or {}, res.get("sims") or {}
            elif self.encoder is not None and self.centroid is not None:
                from voicetwin.eval.speaker import cosine

                sim = cosine(self.encoder.embed(wav, sr), self.centroid)
        if pct is not None:
            total += self.w["speaker"] * pct / 100.0  # 相似度为主：用校准后的百分比
        elif sim is not None:
            total += self.w["speaker"] * sim
        voiced, pauses = speech_activity(wav, sr)
        if voiced < 0.2:
            issues.append("几乎没有声音")
            total -= 2.0
        syl = syllable_count(text)
        rate = syl / voiced if voiced >= 0.2 and syl else None
        rate_dev = None
        if rate:
            target = target_rate(self.profile, lang) * float(speed or 1.0)
            rate_dev = abs(math.log(rate / target))
            total -= self.w["rate"] * rate_dev
            if rate < target * 0.45:
                issues.append("语速过慢/可能有重复或杂音")
                total -= 0.5
            if rate > target * 2.0:
                issues.append("语速过快/可能漏读")
                total -= 0.5
        long_pauses = [p for p in pauses if p > 1.2] if check_pauses else []
        if long_pauses:
            issues.append(f"句中有 {max(long_pauses):.1f}s 的异常停顿")
            total -= 0.3 * len(long_pauses)
        if clip_ratio(wav) > 0.002:
            issues.append("有爆音")
            total -= 0.3
        pitch_dev = None
        f0_med = None
        ref_pitch = (self.profile.get("pitch") or {}).get(lang) or (self.profile.get("pitch") or {}).get("zh")
        if ref_pitch and self.w.get("pitch", 0) > 0:
            st = f0_stats(wav, sr)
            if st:
                f0_med = float(st["f0_median"])
                semis = abs(12.0 * math.log2(st["f0_median"] / ref_pitch["f0_median"]))
                spread = abs(st["f0_semitone_std"] - ref_pitch.get("semitone_std", st["f0_semitone_std"]))
                pitch_dev = semis / 12.0 + spread / 12.0
                total -= self.w["pitch"] * pitch_dev
        cer_val, hyp, errors, checker = None, None, None, ""
        if use_asr and self.cer_checker is not None:
            res = self.cer_checker.check(wav, sr, text, lang)
            if res is not None:
                cer_val, hyp = res["cer"], res["hyp"]
                errors, checker = res.get("errors"), res.get("engine", "")
                total -= self.w["cer"] * cer_val
                if cer_val > 0.3:
                    issues.append(f"识别错字率 {cer_val:.0%}")
        return Score(total=total, speaker_sim=sim, cer=cer_val, hyp=hyp, rate=rate, rate_dev=rate_dev,
                     pitch_dev=pitch_dev, issues=issues, pct=pct, pcts=pcts, sims=sims, errors=errors, f0=f0_med,
                     checker=checker)

    def in_normal_range(self, score: Score, lang: str, speed: float = 1.0) -> bool:
        """语速、音高在不在你平时说话的正常范围里（你自己录音的 10%~90% 分位，留一点余量）。"""
        rate_q = (self.profile.get("rate") or {}).get(lang) or {}
        if score.rate and rate_q.get("p10") and rate_q.get("p90"):
            lo, hi = rate_q["p10"] * float(speed or 1.0) * 0.92, rate_q["p90"] * float(speed or 1.0) * 1.08
            if not lo <= score.rate <= hi:
                return False
        pitch = (self.profile.get("pitch") or {}).get(lang) or (self.profile.get("pitch") or {}).get("zh") or {}
        if score.f0 and pitch.get("f0_p10") and pitch.get("f0_p90"):
            if not pitch["f0_p10"] / 1.06 <= score.f0 <= pitch["f0_p90"] * 1.06:  # 多留约 1 个半音
                return False
        return True


def similarity_label(sim: Optional[float], encoder_name: str) -> str:
    if sim is None:
        return "未知"
    if encoder_name == "mfcc-stats":
        return "（简易声纹，仅供参考）"
    if sim >= 0.86:
        return "非常像"
    if sim >= 0.78:
        return "比较像"
    if sim >= 0.70:
        return "有点像"
    return "不太像"


def pct_label(pct: Optional[float]) -> str:
    if pct is None:
        return "未知"
    if pct >= 95:
        return "非常像"
    if pct >= 85:
        return "比较像"
    if pct >= 75:
        return "有点像"
    return "不太像"
