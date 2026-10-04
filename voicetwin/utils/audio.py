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


def save_audio(path: PathLike, wav: np.ndarray, sr: int, subtype: str = "PCM_16",
               comment: Optional[str] = None) -> Path:
    """写音频。comment：写进文件里面的注释（WAV 的 LIST/INFO ICMT，libsndfile 写的；改了文件名也能查到用的是哪个模型）。"""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    wav = np.clip(np.asarray(wav, dtype=np.float32), -1.0, 1.0)
    if not comment:
        sf.write(str(path), wav, int(sr), subtype=subtype)
        return path
    fmt = "WAV" if path.suffix.lower() == ".wav" else None
    with sf.SoundFile(str(path), "w", int(sr), 1, subtype=subtype, format=fmt) as f:
        try:
            f.comment = str(comment)
        except Exception:  # noqa: BLE001 - 这种格式写不了注释：照样写声音
            pass
        f.write(wav)
    return path


def audio_comment(path: PathLike) -> str:
    """读文件里面的注释（save_audio 写的）；没有或读不了是空字符串。"""
    try:
        with sf.SoundFile(str(path)) as f:
            return str(f.comment or "")
    except Exception:  # noqa: BLE001
        return ""


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


def frame_rms_db_chunked(wav: np.ndarray, sr: int, hop_ms: float = 10.0, win_ms: float = 40.0,
                         chunk_frames: int = 10_000) -> np.ndarray:
    """和 frame_rms_db 一样的逐帧电平（同样的帧、同样的窗、同样的算法），只是分段算：整篇讲课音频（一小时 32 kHz
    一亿多个采样）整个算要好几 GB 内存，分段算（每段 100 秒）每段只要几十 MB。数值和 frame_rms_db 只差浮点运算的先后（10⁻⁶ dB 以下）。"""
    hop = max(1, int(round(sr * hop_ms / 1000.0)))
    win = max(hop, int(round(sr * win_ms / 1000.0)))
    n = len(wav)
    if n == 0:
        return np.zeros(0, dtype=np.float32)
    pad = win // 2
    total = n + 2 * pad                      # frame_rms_db 里补过 0 的长度
    n_frames = 1 + (n - 1) // hop
    out = np.empty(n_frames, dtype=np.float32)
    for f0 in range(0, n_frames, max(1, int(chunk_frames))):
        f1 = min(n_frames, f0 + int(chunk_frames))
        a = f0 * hop                         # 这一段在补过 0 的信号里从哪到哪
        b = min((f1 - 1) * hop + win, total)
        seg = np.zeros(b - a, dtype=np.float64)
        lo, hi = max(a - pad, 0), min(b - pad, n)
        if hi > lo:
            seg[lo - (a - pad):hi - (a - pad)] = wav[lo:hi]
        csum = np.concatenate([[0.0], np.cumsum(seg ** 2)])
        starts = np.arange(f0, f1) * hop
        ends = np.minimum(starts + win, total)
        energy = (csum[ends - a] - csum[starts - a]) / np.maximum(ends - starts, 1)
        out[f0:f1] = (10.0 * np.log10(energy + EPS)).astype(np.float32)
    return out


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


def auto_silence_threshold(wav: np.ndarray, sr: int, floor_db: float = -65.0, drop_db: float = 30.0,
                           noise_db: float = 6.0) -> float:
    """自动静音阈值：以语音电平为基准（-30 dB），底噪较高时抬高到底噪之上 6 dB。

    底噪用很低的分位数（3%）估计，这样即使音频首尾静音很短也不会把轻声部分误判成底噪。
    drop_db / noise_db：「一模一样」档切首尾时用 45 / 12（比语音低 45 dB、比底噪高 12 dB），见 engine.trim_edges；
    不传时和以前一模一样。
    """
    return silence_threshold_from_db(frame_rms_db(wav, sr), floor_db, drop_db, noise_db)


def speech_noise_db(db: np.ndarray) -> Optional[Tuple[float, float]]:
    """逐帧电平里的 (底噪 = 3% 分位, 语音 = 95% 分位)；全是数字静音（-100 dB）时 None。"""
    db = np.asarray(db)
    db = db[db > -100]
    if db.size == 0:
        return None
    return float(np.percentile(db, 3)), float(np.percentile(db, 95))


def silence_threshold_from_db(db: np.ndarray, floor_db: float = -65.0, drop_db: float = 30.0,
                              noise_db: float = 6.0) -> float:
    """auto_silence_threshold 的计算部分：已经有逐帧电平（10 ms 一帧、40 ms 窗）时直接用
    （很长的整段录音分块读、分块算电平，不用整个读进内存）。
    阈值 = max(语音 − drop_db, 底噪 + noise_db, floor_db)，最高到 语音 − 15 dB。"""
    levels = speech_noise_db(db)
    if levels is None:
        return -40.0
    noise, speech = levels
    thr = max(speech - float(drop_db), noise + float(noise_db), float(floor_db))
    return float(min(thr, speech - 15.0))


def speech_level_db(wav: np.ndarray, sr: int) -> Optional[float]:
    """说话时的响度（dBFS）：自动静音阈值以上的帧（10 ms 一帧、40 ms 窗）按能量平均。
    和 twin_profile 量你本人每段录音的 level_db 是同一个算法（「一模一样」拼接时按它调每句的音量）。没有声音时 None。"""
    wav = np.asarray(wav, dtype=np.float32)
    if wav.size < int(0.1 * sr):
        return None
    db = frame_rms_db(wav, sr)
    thr = silence_threshold_from_db(db)
    sdb = db[db >= thr].astype(np.float64)
    if sdb.size == 0 or not np.any(db > -100):
        return None
    return float(10.0 * np.log10(np.mean(10.0 ** (sdb / 10.0)) + EPS))


#: 噪声在每个频率上的功率是指数分布：p10 = −ln(0.9) × 平均功率（除以它才是平均功率，和逐帧电平的刻度一样）
_P10_OF_MEAN = float(-np.log(0.9))


def speech_noise_floor_db(wav: np.ndarray, sr: int, min_frames: int = 5) -> Optional[float]:
    """一句话说话部分的底噪（dBFS，和逐帧电平同一个刻度：标准差 σ 的白噪声量出来是 20·log10(σ)）。

    只看有声音的那一段（第一个到最后一个比自动静音阈值响的帧，10 ms 一帧、40 ms 窗），切成约 32 毫秒一帧
    （一半重叠，汉宁窗），**每个频率**取所有帧里的 p10（换算成平均功率），再取所有频率的中位数，乘上频率个数就是底噪的
    总功率（噪声估计里常用的「最小统计」）。说话的声音任何时候只占一部分频率：一个频率上总有一成以上的帧没有声音，
    这个频率的 p10 就是底噪；一直被占着的只有音高附近几个频率，中位数不受它们影响。
    以前直接取逐帧电平的 p10：句子里停顿不到一成时量到的是轻声的字（干净的、连着说的句子也有 −28 dBFS，被当成有底噪）。
    句子里有停顿时两种量法差不多（停顿里就是底噪）。底噪不是白噪声、低频多时会量低一些（粉红噪声约低 7 dB）。
    整句都量不出声音、或者有声音的那一段不到 min_frames 帧时返回 None。"""
    wav = np.asarray(wav, dtype=np.float32)
    if wav.size < int(0.1 * sr):
        return None
    db = frame_rms_db(wav, sr)
    idx = np.flatnonzero(db >= silence_threshold_from_db(db))
    if idx.size == 0 or not np.any(db > -100):
        return None
    hop10 = max(1, int(round(sr * 0.01)))
    x = wav[idx[0] * hop10:min(wav.size, (idx[-1] + 1) * hop10)].astype(np.float64)
    n = 1 << int(np.ceil(np.log2(max(0.032 * sr, 16.0))))
    h = n // 2
    n_frames = 1 + (x.size - n) // h if x.size >= n else 0
    if n_frames < max(1, int(min_frames)):
        return None
    win = np.hanning(n)
    frames = x[np.arange(n_frames)[:, None] * h + np.arange(n)[None, :]] * win
    power = np.abs(np.fft.rfft(frames, axis=1)[:, 1:-1]) ** 2   # 不要直流和最高的那个频率
    floor = np.percentile(power, 10, axis=0) / _P10_OF_MEAN
    return float(10.0 * np.log10(float(np.median(floor)) / float(np.sum(win ** 2)) + EPS))


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


def mask_runs(mask: np.ndarray, min_frames: int = 1) -> List[Tuple[int, int]]:
    """mask 里连续为 True 的段 [(起始帧, 结束帧（不含）), ...]，只留长度 ≥ min_frames 的。"""
    m = np.asarray(mask, dtype=bool)
    if m.size == 0:
        return []
    edges = np.diff(np.concatenate([[0], m.astype(np.int8), [0]]))
    starts = np.flatnonzero(edges == 1)
    ends = np.flatnonzero(edges == -1)
    keep = (ends - starts) >= max(1, int(min_frames))
    return [(int(a), int(b)) for a, b in zip(starts[keep], ends[keep])]


def silent_runs(wav: np.ndarray, sr: int, threshold_db: Optional[float] = None, hop_ms: float = 10.0,
                min_run_ms: float = 120.0, chunked: bool = False) -> List[Tuple[float, float]]:
    """返回所有长度 ≥ min_run_ms 的静音区间 [(start_sec, end_sec), ...]（包括文件开头和结尾的静音）。

    10 ms 一帧、40 ms 窗、自动静音阈值——和切片时量停顿用的是同一个方法；「一模一样」档量你本人的停顿
    （twin_profile）和量生成结果的停顿都用它，两边才能直接比。chunked：整篇讲课音频这种很长的，逐帧电平分段算
    （frame_rms_db_chunked，结果一样，内存少很多）。"""
    if chunked:
        db = frame_rms_db_chunked(wav, sr, hop_ms=hop_ms)
        if threshold_db is None:
            threshold_db = silence_threshold_from_db(db) if hop_ms == 10.0 else auto_silence_threshold(wav, sr)
    else:
        if threshold_db is None:
            threshold_db = auto_silence_threshold(wav, sr)
        db = frame_rms_db(wav, sr, hop_ms=hop_ms)
    hop_s = hop_ms / 1000.0
    min_frames = max(1, int(round(min_run_ms / hop_ms)))
    total = len(wav) / sr if sr else 0.0
    return [(i * hop_s, min(j * hop_s, total)) for i, j in mask_runs(db < threshold_db, min_frames)]


def speech_runs(wav: np.ndarray, sr: int, threshold_db: Optional[float] = None, hop_ms: float = 10.0,
                min_gap_ms: float = 120.0) -> List[Tuple[float, float]]:
    """有声音的区间 [(start_sec, end_sec), ...]：被 ≥ min_gap_ms 的静音隔开的每一段（比这短的停顿算在声音里）。
    整段都是静音时返回 []。"""
    if wav.size == 0:
        return []
    total = len(wav) / sr
    out: List[Tuple[float, float]] = []
    cursor = 0.0
    for s, e in silent_runs(wav, sr, threshold_db=threshold_db, hop_ms=hop_ms, min_run_ms=min_gap_ms):
        if s > cursor + 1e-9:
            out.append((cursor, s))
        cursor = max(cursor, e)
    if total > cursor + 1e-9:
        out.append((cursor, total))
    return out


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


def clip_counts(wav: np.ndarray, sr: int, level: float = 0.995, hop_ms: float = 1.0) -> Tuple[np.ndarray, int]:
    """每 hop_ms 毫秒里有几个样本到了满格（削顶 / 爆音）。返回 (每帧的个数, 每帧几个样本)。
    要在统一音量以前、对原始录音算（统一音量以后最响只有 -1 dB，永远不会满格）；整段录音很长时分块算，不多占内存。"""
    hop = max(1, int(round(sr * hop_ms / 1000.0)))
    n = int(len(wav))
    out = np.zeros((n + hop - 1) // hop, dtype=np.uint16)
    chunk = hop * 65536
    for i in range(0, n, chunk):
        part = np.abs(wav[i:i + chunk]) >= level
        pad = (-len(part)) % hop
        if pad:
            part = np.concatenate([part, np.zeros(pad, dtype=bool)])
        k = i // hop
        out[k:k + len(part) // hop] = part.reshape(-1, hop).sum(axis=1)
    return out, hop


def clipped_fraction(counts: np.ndarray, hop: int, start: int, end: int) -> float:
    """clip_counts 算出来的结果里，样本 [start, end) 这一段满格样本的比例（误差不超过一帧）。"""
    if end <= start or hop <= 0:
        return 0.0
    return float(np.sum(counts[start // hop:end // hop], dtype=np.int64)) / float(end - start)


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
