"""声纹打分的前端处理：只保留人声（silero-vad）+ Kaldi fbank。只依赖 numpy 和 onnxruntime。

为什么要"只保留人声"：生成的音频句子之间是绝对静音（数字 0），你的原声录音停顿里有教室的环境声。
声纹模型会对整段音频做均值归一化，大段的数字静音会把整段的特征拉偏——同一个人的声音，
"停顿是绝对静音"和"停顿里有环境声"打出来的分数不一样。所以原声和生成的声音都先用同一个
人声检测模型（silero-vad v4）找出说话的部分，只拿说话的部分去比，停顿怎么处理都不影响分数。

fbank 和 3D-Speaker / WeSpeaker 训练时用的 torchaudio.compliance.kaldi.fbank 一致
（80 维、25 ms 窗、10 ms 帧移、povey 窗、预加重 0.97、dither=0、20 Hz~奈奎斯特频率、去掉首尾不完整的帧），
这里用 numpy 重写，和 torchaudio 的结果最大相差约 2e-4，不需要 torch。
"""

from __future__ import annotations

import threading
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np

SR = 16000
VAD_WINDOW = 512
#: 每段人声前后各多留 100 ms（不切掉字头字尾）
VAD_PAD_SECONDS = 0.10
#: 检测出来的人声加起来不到这么长时，就用整段（太短的话声纹不可靠，宁可带上停顿）
MIN_SPEECH_SECONDS = 0.5

_MEL_CACHE: Dict[Tuple[int, int, int, float, float], np.ndarray] = {}


def _mel_banks(num_bins: int = 80, n_fft: int = 512, sr: int = SR, low: float = 20.0, high: float = 0.0) -> np.ndarray:
    key = (num_bins, n_fft, sr, low, high)
    cached = _MEL_CACHE.get(key)
    if cached is not None:
        return cached
    nyquist = sr / 2.0
    high = nyquist + high if high <= 0 else high

    def mel(f: np.ndarray) -> np.ndarray:
        return 1127.0 * np.log(1.0 + np.asarray(f, dtype=np.float64) / 700.0)

    mlow, mhigh = float(mel(low)), float(mel(high))
    delta = (mhigh - mlow) / (num_bins + 1)
    half = n_fft // 2
    fft_mel = mel(np.arange(half) * sr / n_fft)
    banks = np.zeros((num_bins, half + 1), dtype=np.float64)
    for b in range(num_bins):
        left, center, right = mlow + b * delta, mlow + (b + 1) * delta, mlow + (b + 2) * delta
        up = (fft_mel - left) / (center - left)
        down = (right - fft_mel) / (right - center)
        banks[b, :half] = np.maximum(0.0, np.minimum(up, down))
    _MEL_CACHE[key] = banks
    return banks


def kaldi_fbank(wav: np.ndarray, sr: int = SR, num_bins: int = 80, frame_ms: float = 25.0, shift_ms: float = 10.0,
                preemph: float = 0.97, scale: float = 1.0) -> np.ndarray:
    """Kaldi 风格的 log-mel fbank，返回 (帧数, num_bins) float32。scale=32768 用于按 16 位整数幅度训练的模型。"""
    x = np.asarray(wav, dtype=np.float64).reshape(-1) * float(scale)
    flen = int(sr * frame_ms / 1000.0)
    fshift = int(sr * shift_ms / 1000.0)
    if x.size < flen:
        return np.zeros((0, num_bins), dtype=np.float32)
    n = 1 + (x.size - flen) // fshift
    idx = np.arange(flen)[None, :] + fshift * np.arange(n)[:, None]
    frames = x[idx]
    frames = frames - frames.mean(axis=1, keepdims=True)
    frames = np.concatenate([frames[:, :1] * (1.0 - preemph), frames[:, 1:] - preemph * frames[:, :-1]], axis=1)
    window = (0.5 - 0.5 * np.cos(2.0 * np.pi * np.arange(flen) / (flen - 1))) ** 0.85
    frames *= window
    n_fft = 1 << int(np.ceil(np.log2(flen)))
    power = np.abs(np.fft.rfft(frames, n=n_fft, axis=1)) ** 2
    mel = power @ _mel_banks(num_bins, n_fft, sr).T
    return np.log(np.maximum(mel, np.finfo(np.float32).eps)).astype(np.float32)


def ort_session(path: Path, threads: int = 0, device: str = "auto"):
    """onnxruntime 会话。device=auto/cuda 时先试显卡（onnxruntime-gpu），不行就用 CPU，不报错。"""
    import onnxruntime as ort

    try:
        ort.set_default_logger_severity(3)  # 显卡不可用时 onnxruntime 会打印一大段英文错误，没用
    except Exception:
        pass
    opts = ort.SessionOptions()
    if threads:
        opts.intra_op_num_threads = int(threads)
    opts.inter_op_num_threads = 1
    # 极小的浮点数（denormal）按 0 算：ReDimNet2 中文版里有很多"快要为 0"的中间结果，不这样 CPU 会慢 25 倍以上，
    # 结果完全一样（实测余弦相似度 1.0000000）
    opts.add_session_config_entry("session.set_denormal_as_zero", "1")
    providers = ["CPUExecutionProvider"]
    if device in ("auto", "cuda", "gpu") and "CUDAExecutionProvider" in ort.get_available_providers():
        providers = ["CUDAExecutionProvider", "CPUExecutionProvider"]
    try:
        return ort.InferenceSession(str(path), sess_options=opts, providers=providers)
    except Exception:
        if providers[0] == "CPUExecutionProvider":
            raise
        return ort.InferenceSession(str(path), sess_options=opts, providers=["CPUExecutionProvider"])


class SileroVAD:
    """silero-vad v4（k2-fsa 导出的 16 kHz 版本：x[1,512], h, c → prob），找出说话的时间段。

    判定规则和 sherpa-onnx 的默认设置一致：概率 > 0.5 开始算说话；低于 0.35 并持续 0.25 秒才算说完；
    短于 0.1 秒的不算。"""

    def __init__(self, path: Path, threshold: float = 0.5, min_silence: float = 0.25, min_speech: float = 0.10):
        self.sess = ort_session(Path(path), threads=1, device="cpu")
        self.threshold = float(threshold)
        self.min_silence = float(min_silence)
        self.min_speech = float(min_speech)
        self._lock = threading.Lock()

    def probs(self, wav: np.ndarray) -> np.ndarray:
        wav = np.ascontiguousarray(wav, dtype=np.float32).reshape(-1)
        h = np.zeros((2, 1, 64), dtype=np.float32)
        c = np.zeros((2, 1, 64), dtype=np.float32)
        out: List[float] = []
        with self._lock:
            for i in range(0, wav.size - VAD_WINDOW + 1, VAD_WINDOW):
                p, h, c = self.sess.run(None, {"x": wav[None, i:i + VAD_WINDOW], "h": h, "c": c})
                out.append(float(np.asarray(p).reshape(-1)[0]))
        return np.asarray(out, dtype=np.float32)

    def spans(self, wav: np.ndarray) -> List[Tuple[int, int]]:
        """说话的时间段 [(开始样本, 结束样本), ...]（16 kHz）。"""
        p = self.probs(wav)
        spans: List[Tuple[int, int]] = []
        start: Optional[int] = None
        quiet = 0
        need_quiet = int(np.ceil(self.min_silence * SR / VAD_WINDOW))
        for i, v in enumerate(p):
            if start is None:
                if v > self.threshold:
                    start, quiet = i, 0
            elif v < self.threshold - 0.15:
                quiet += 1
                if quiet >= need_quiet:
                    spans.append((start, i - quiet + 1))
                    start = None
            elif v > self.threshold:
                quiet = 0
        if start is not None:
            spans.append((start, len(p) - quiet))
        min_windows = self.min_speech * SR / VAD_WINDOW
        return [(a * VAD_WINDOW, b * VAD_WINDOW) for a, b in spans if b - a >= min_windows]

    def speech_only(self, wav: np.ndarray) -> np.ndarray:
        """只保留说话的部分（每段前后多留 100 ms 原始音频），拼起来。人声太少时返回原音频。"""
        wav = np.asarray(wav, dtype=np.float32).reshape(-1)
        spans = self.spans(wav)
        if not spans:
            return wav
        pad = int(VAD_PAD_SECONDS * SR)
        merged: List[List[int]] = []
        for s, e in spans:
            s, e = max(0, s - pad), min(wav.size, e + pad)
            if merged and s <= merged[-1][1]:
                merged[-1][1] = max(merged[-1][1], e)
            else:
                merged.append([s, e])
        out = np.concatenate([wav[s:e] for s, e in merged])
        return out if out.size >= MIN_SPEECH_SECONDS * SR else wav
