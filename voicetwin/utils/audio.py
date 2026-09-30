"""音频基础工具：读写、重采样、响度、静音检测、拼接。只依赖 numpy / scipy / soundfile。"""

from __future__ import annotations

import io
from math import gcd
from pathlib import Path
from typing import List, Optional, Sequence, Tuple, Union

import numpy as np
import soundfile as sf
from scipy import signal

PathLike = Union[str, Path]
EPS = 1e-10


# ----------------------------------------------------------------------------- I/O
def to_mono(wav: np.ndarray) -> np.ndarray:
    if wav.ndim == 2:
        # soundfile: (frames, channels)
        axis = 1 if wav.shape[1] <= 8 else 0
        wav = wav.mean(axis=axis)
    return wav.astype(np.float32, copy=False)


def resample(wav: np.ndarray, sr_from: int, sr_to: int) -> np.ndarray:
    if sr_from == sr_to or wav.size == 0:
        return wav.astype(np.float32, copy=False)
    g = gcd(int(sr_from), int(sr_to))
    up, down = int(sr_to) // g, int(sr_from) // g
    return signal.resample_poly(wav, up, down).astype(np.float32)


def load_audio(path: PathLike, sr: Optional[int] = None, mono: bool = True) -> Tuple[np.ndarray, int]:
    """读取任意音频/视频文件，返回 float32 波形和采样率。"""
    path = Path(path)
    try:
        wav, file_sr = sf.read(str(path), dtype="float32", always_2d=False)
    except Exception:
        from voicetwin.utils.ffmpeg import decode_to_array

        wav, file_sr = decode_to_array(path, sample_rate=sr or 44100, mono=mono)
    if mono:
        wav = to_mono(np.asarray(wav))
    if sr is not None and file_sr != sr:
        wav = resample(wav, file_sr, sr)
        file_sr = sr
    return np.ascontiguousarray(wav, dtype=np.float32), int(file_sr)


def load_audio_bytes(data: bytes) -> Tuple[np.ndarray, int]:
    wav, sr = sf.read(io.BytesIO(data), dtype="float32", always_2d=False)
    return to_mono(np.asarray(wav)), int(sr)


def save_audio(path: PathLike, wav: np.ndarray, sr: int, subtype: str = "PCM_16") -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    wav = np.clip(np.asarray(wav, dtype=np.float32), -1.0, 1.0)
    sf.write(str(path), wav, int(sr), subtype=subtype)
    return path


def duration_of(path: PathLike) -> float:
    try:
        info = sf.info(str(path))
        return float(info.frames) / float(info.samplerate)
    except Exception:
        wav, sr = load_audio(path)
        return len(wav) / sr


# ----------------------------------------------------------------------------- 电平/静音
def frame_rms_db(wav: np.ndarray, sr: int, hop_ms: float = 10.0, win_ms: float = 40.0) -> np.ndarray:
    """逐帧 RMS（dBFS），帧中心与 i*hop 对齐。"""
    hop = max(1, int(round(sr * hop_ms / 1000.0)))
    win = max(hop, int(round(sr * win_ms / 1000.0)))
    if wav.size == 0:
        return np.zeros(0, dtype=np.float32)
    pad = win // 2
    padded = np.pad(wav.astype(np.float64), (pad, pad), mode="constant")
    sq = padded ** 2
    csum = np.concatenate([[0.0], np.cumsum(sq)])
    n_frames = 1 + (len(wav) - 1) // hop
    starts = np.arange(n_frames) * hop
    ends = np.minimum(starts + win, len(padded))
    energy = (csum[ends] - csum[starts]) / np.maximum(ends - starts, 1)
    return (10.0 * np.log10(energy + EPS)).astype(np.float32)


def noise_and_speech_levels(wav: np.ndarray, sr: int) -> Tuple[float, float]:
    """粗略估计底噪电平与语音电平（dBFS）：分别取帧能量的 10% / 95% 分位。"""
    db = frame_rms_db(wav, sr)
    db = db[db > -100]
    if db.size == 0:
        return -100.0, -100.0
    return float(np.percentile(db, 10)), float(np.percentile(db, 95))


def estimate_snr(wav: np.ndarray, sr: int) -> float:
    noise, speech = noise_and_speech_levels(wav, sr)
    return float(speech - noise)


def auto_silence_threshold(wav: np.ndarray, sr: int, floor_db: float = -60.0) -> float:
    """根据底噪和语音电平自动给出静音阈值。"""
    noise, speech = noise_and_speech_levels(wav, sr)
    if speech <= -99:
        return -40.0
    thr = max(noise + 8.0, speech - 35.0, floor_db)
    return float(min(thr, speech - 12.0))


def _fill_short_gaps(mask: np.ndarray, max_gap: int) -> np.ndarray:
    """把 mask 中长度 <= max_gap 的 False 空洞填成 True（两侧都为 True 时）。"""
    out = mask.copy()
    n = len(mask)
    i = 0
    while i < n:
        if not out[i]:
            j = i
            while j < n and not out[j]:
                j += 1
            if i > 0 and j < n and (j - i) <= max_gap:
                out[i:j] = True
            i = j
        else:
            i += 1
    return out


def silent_runs(wav: np.ndarray, sr: int, threshold_db: Optional[float] = None, hop_ms: float = 10.0,
                min_run_ms: float = 150.0) -> List[Tuple[float, float]]:
    """返回所有长度 ≥ min_run_ms 的静音区间 [(start_sec, end_sec), ...]。"""
    if threshold_db is None:
        threshold_db = auto_silence_threshold(wav, sr)
    db = frame_rms_db(wav, sr, hop_ms=hop_ms)
    silent = db < threshold_db
    hop_s = hop_ms / 1000.0
    runs = []
    i, n = 0, len(silent)
    min_frames = max(1, int(round(min_run_ms / hop_ms)))
    while i < n:
        if silent[i]:
            j = i
            while j < n and silent[j]:
                j += 1
            if j - i >= min_frames:
                runs.append((i * hop_s, min(j * hop_s, len(wav) / sr)))
            i = j
        else:
            i += 1
    return runs


def trim_silence(wav: np.ndarray, sr: int, threshold_db: Optional[float] = None, pad_ms: float = 60.0
                 ) -> Tuple[np.ndarray, int, int]:
    """去掉首尾静音，保留 pad_ms 的余量。返回 (波形, 起始样本, 结束样本)。"""
    if wav.size == 0:
        return wav, 0, 0
    if threshold_db is None:
        threshold_db = auto_silence_threshold(wav, sr)
    hop_ms = 10.0
    db = frame_rms_db(wav, sr, hop_ms=hop_ms)
    voiced = np.where(db >= threshold_db)[0]
    if voiced.size == 0:
        return wav[:0], 0, 0
    hop = sr * hop_ms / 1000.0
    pad = int(sr * pad_ms / 1000.0)
    start = max(0, int(voiced[0] * hop) - pad)
    end = min(len(wav), int((voiced[-1] + 1) * hop) + pad)
    return wav[start:end], start, end


def speech_activity(wav: np.ndarray, sr: int, threshold_db: Optional[float] = None, bridge_ms: float = 200.0
                    ) -> Tuple[float, List[float]]:
    """返回 (发声时长秒, 句内停顿列表秒)。停顿指 > bridge_ms 的内部静音。"""
    if wav.size == 0:
        return 0.0, []
    if threshold_db is None:
        threshold_db = auto_silence_threshold(wav, sr)
    hop_ms = 10.0
    db = frame_rms_db(wav, sr, hop_ms=hop_ms)
    mask = db >= threshold_db
    if not mask.any():
        return 0.0, []
    first, last = np.where(mask)[0][[0, -1]]
    core = mask[first:last + 1]
    bridged = _fill_short_gaps(core, int(bridge_ms / hop_ms))
    voiced_s = float(bridged.sum()) * hop_ms / 1000.0
    pauses: List[float] = []
    i, n = 0, len(bridged)
    while i < n:
        if not bridged[i]:
            j = i
            while j < n and not bridged[j]:
                j += 1
            pauses.append((j - i) * hop_ms / 1000.0)
            i = j
        else:
            i += 1
    return voiced_s, pauses


def clip_ratio(wav: np.ndarray, level: float = 0.995) -> float:
    if wav.size == 0:
        return 0.0
    return float(np.mean(np.abs(wav) >= level))


# ----------------------------------------------------------------------------- 滤波/响度
def highpass(wav: np.ndarray, sr: int, cutoff_hz: float = 60.0, order: int = 4) -> np.ndarray:
    if not cutoff_hz or cutoff_hz <= 0 or wav.size < 64:
        return wav
    sos = signal.butter(order, cutoff_hz, btype="highpass", fs=sr, output="sos")
    return signal.sosfiltfilt(sos, wav).astype(np.float32)


def measure_lufs(wav: np.ndarray, sr: int) -> float:
    """ITU-R BS.1770 积分响度；太短或 pyloudnorm 不可用时退化为 RMS 估计。"""
    if wav.size == 0:
        return -70.0
    try:
        import pyloudnorm as pyln

        if len(wav) / sr >= 0.5:
            meter = pyln.Meter(sr)
            val = float(meter.integrated_loudness(wav.astype(np.float64)))
            if np.isfinite(val):
                return val
    except Exception:
        pass
    rms = np.sqrt(np.mean(wav.astype(np.float64) ** 2) + EPS)
    return float(20 * np.log10(rms) - 0.691 + 3.0)


def peak_limit(wav: np.ndarray, ceiling_db: float = -1.0) -> np.ndarray:
    ceiling = 10 ** (ceiling_db / 20.0)
    peak = float(np.max(np.abs(wav))) if wav.size else 0.0
    if peak > ceiling:
        wav = wav * (ceiling / peak)
    return wav.astype(np.float32)


def normalize_lufs(wav: np.ndarray, sr: int, target_lufs: float = -20.0, ceiling_db: float = -1.0) -> np.ndarray:
    current = measure_lufs(wav, sr)
    if not np.isfinite(current) or current < -69:
        return wav
    gain = 10 ** ((target_lufs - current) / 20.0)
    return peak_limit(wav * gain, ceiling_db)


# ----------------------------------------------------------------------------- 拼接
def silence(seconds: float, sr: int) -> np.ndarray:
    return np.zeros(max(0, int(round(seconds * sr))), dtype=np.float32)


def fade(wav: np.ndarray, sr: int, in_ms: float = 8.0, out_ms: float = 15.0) -> np.ndarray:
    wav = wav.astype(np.float32, copy=True)
    n_in = min(len(wav), int(sr * in_ms / 1000.0))
    n_out = min(len(wav), int(sr * out_ms / 1000.0))
    if n_in > 0:
        wav[:n_in] *= np.linspace(0.0, 1.0, n_in, dtype=np.float32)
    if n_out > 0:
        wav[-n_out:] *= np.linspace(1.0, 0.0, n_out, dtype=np.float32)
    return wav


def concat_with_pauses(chunks: Sequence[np.ndarray], sr: int, pauses_after: Sequence[float]) -> np.ndarray:
    parts: List[np.ndarray] = []
    for i, chunk in enumerate(chunks):
        parts.append(fade(chunk, sr))
        pause = pauses_after[i] if i < len(pauses_after) else 0.0
        if pause > 0:
            parts.append(silence(pause, sr))
    return np.concatenate(parts).astype(np.float32) if parts else np.zeros(0, dtype=np.float32)
