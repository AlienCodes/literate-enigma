"""给合成结果打分：像不像你（声纹）、读得对不对（识别错字率）、节奏像不像（语速/音高）。"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

import numpy as np

from voicetwin.style.profile import target_rate
from voicetwin.style.prosody import f0_stats
from voicetwin.utils.audio import clip_ratio, resample, speech_activity
from voicetwin.utils.log import get_logger
from voicetwin.utils.textutil import cer as compute_cer
from voicetwin.utils.textutil import syllable_count

log = get_logger("metrics")


class CERChecker:
    """用 faster-whisper 把合成音频识别回文字，和原文比对，找出漏字、多字、读错。"""

    def __init__(self, model: str = "small", device: str = "auto"):
        self.model_name = model
        self.device = device
        self._model = None
        self.available = True

    def _load(self) -> bool:
        if self._model is not None:
            return True
        if not self.available:
            return False
        try:
            from voicetwin.data.asr import Transcriber

            self._model = Transcriber({"engine": "faster-whisper", "model": self.model_name, "device": self.device,
                                       "compute_type": "auto", "beam_size": 1,
                                       "initial_prompt_zh": "以下是普通话的句子，使用简体中文和标点符号。"})
            self._model._load()
            return True
        except Exception as exc:
            log.warning(f"识别校验不可用（{exc}），将只用声纹和节奏打分")
            self.available = False
            self._model = None
            return False

    def check(self, wav: np.ndarray, sr: int, text: str, lang: str) -> Optional[Dict[str, Any]]:
        if not self._load():
            return None
        res = self._model.transcribe(resample(wav, sr, 16000), language=lang)
        return {"cer": compute_cer(text, res.text), "hyp": res.text}


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

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        return {k: (round(v, 4) if isinstance(v, float) else v) for k, v in d.items()}


class Scorer:
    def __init__(self, profile: Dict[str, Any], centroid: Optional[np.ndarray], encoder: Any,
                 weights: Optional[Dict[str, float]] = None, cer_checker: Optional[CERChecker] = None):
        self.profile = profile or {}
        self.centroid = centroid
        self.encoder = encoder
        w = {"speaker": 1.0, "cer": 2.0, "rate": 0.6, "pitch": 0.3}
        w.update(weights or {})
        self.w = w
        self.cer_checker = cer_checker

    def score(self, wav: np.ndarray, sr: int, text: str, lang: str, speed: float = 1.0,
              use_asr: bool = True, check_pauses: bool = True) -> Score:
        issues: List[str] = []
        total = 0.0
        sim = None
        if self.encoder is not None and self.centroid is not None and wav.size > sr * 0.3:
            from voicetwin.eval.speaker import cosine

            sim = cosine(self.encoder.embed(wav, sr), self.centroid)
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
        ref_pitch = (self.profile.get("pitch") or {}).get(lang) or (self.profile.get("pitch") or {}).get("zh")
        if ref_pitch and self.w.get("pitch", 0) > 0:
            st = f0_stats(wav, sr)
            if st:
                semis = abs(12.0 * math.log2(st["f0_median"] / ref_pitch["f0_median"]))
                spread = abs(st["f0_semitone_std"] - ref_pitch.get("semitone_std", st["f0_semitone_std"]))
                pitch_dev = semis / 12.0 + spread / 12.0
                total -= self.w["pitch"] * pitch_dev
        cer_val, hyp = None, None
        if use_asr and self.cer_checker is not None:
            res = self.cer_checker.check(wav, sr, text, lang)
            if res is not None:
                cer_val, hyp = res["cer"], res["hyp"]
                total -= self.w["cer"] * cer_val
                if cer_val > 0.3:
                    issues.append(f"识别错字率 {cer_val:.0%}")
        return Score(total=total, speaker_sim=sim, cer=cer_val, hyp=hyp, rate=rate, rate_dev=rate_dev,
                     pitch_dev=pitch_dev, issues=issues)


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
