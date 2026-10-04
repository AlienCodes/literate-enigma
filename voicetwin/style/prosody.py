"""韵律特征：音高（F0）、语速、停顿——决定"语气和节奏"像不像。"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

import numpy as np

from voicetwin.utils.audio import auto_silence_threshold, frame_rms_db, resample, speech_activity
from voicetwin.utils.textutil import syllable_count


def f0_frames(wav: np.ndarray, sr: int, fmin: float = 60.0, fmax: float = 500.0) -> Tuple[np.ndarray, np.ndarray]:
    """有声帧的 (时间秒, F0 Hz)：帧中心每 10 ms 一个。f0_track 只要 F0，「一模一样」档还要知道每帧在什么时候
    （整句音调往下走得多快、句末是升还是降）。"""
    import librosa

    empty = np.zeros(0, dtype=np.float32)
    w16 = resample(wav, sr, 16000)
    if len(w16) < 16000 * 0.3:
        return empty, empty
    hop = 160
    f0 = librosa.yin(w16, fmin=fmin, fmax=fmax, sr=16000, frame_length=1024, hop_length=hop)
    db = frame_rms_db(w16, 16000, hop_ms=10.0, win_ms=40.0)
    n = min(len(f0), len(db))
    f0, db = f0[:n], db[:n]
    thr = auto_silence_threshold(w16, 16000) + 6.0
    ok = (db > thr) & (f0 > fmin * 1.05) & (f0 < fmax * 0.95)
    idx = np.flatnonzero(ok)
    f0 = f0[ok]
    if f0.size < 5:
        return empty, empty
    # 去掉倍频/半频错误
    med = np.median(f0)
    keep = (f0 > med / 1.8) & (f0 < med * 1.8)
    return (idx[keep] * (hop / 16000.0)).astype(np.float32), f0[keep].astype(np.float32)


def f0_track(wav: np.ndarray, sr: int, fmin: float = 60.0, fmax: float = 500.0) -> np.ndarray:
    """返回有声帧的 F0（Hz）。使用 librosa.yin + 能量门限，速度快。"""
    return f0_frames(wav, sr, fmin, fmax)[1]


def f0_stats(wav: np.ndarray, sr: int) -> Dict[str, float]:
    f0 = f0_track(wav, sr)
    if f0.size < 5:
        return {}
    med = float(np.median(f0))
    semis = 12.0 * np.log2(f0 / med)
    return {
        "f0_median": med,
        "f0_p10": float(np.percentile(f0, 10)),
        "f0_p90": float(np.percentile(f0, 90)),
        "f0_semitone_std": float(np.std(semis)),
    }


def rate_stats(wav: np.ndarray, sr: int, text: str) -> Dict[str, Any]:
    voiced, pauses = speech_activity(wav, sr)
    syl = syllable_count(text)
    return {
        "voiced": voiced,
        "pauses": [round(p, 3) for p in pauses],
        "syllables": syl,
        "rate": (syl / voiced) if voiced > 0.2 and syl > 0 else None,
    }


def quantiles(values: List[float], qs=(10, 25, 50, 75, 90)) -> Dict[str, float]:
    arr = np.asarray([v for v in values if v is not None and np.isfinite(v)], dtype=np.float64)
    if arr.size == 0:
        return {}
    return {f"p{q}": float(np.percentile(arr, q)) for q in qs} | {"mean": float(arr.mean()), "n": int(arr.size)}
