"""numpy re-implementation of the pieces sherpa-onnx does for speaker models (to run them with plain onnxruntime):
Kaldi-compatible fbank (80 mel, 25/10 ms, povey window, pre-emphasis 0.97, dither 0, snip_edges) and
silero-vad v4 (k2-fsa 16 kHz export) speech segments."""
import numpy as np

_MEL = {}


def _mel_banks(num_bins=80, n_fft=512, sr=16000, low=20.0, high=0.0):
    key = (num_bins, n_fft, sr, low, high)
    if key in _MEL:
        return _MEL[key]
    nyq = sr / 2.0
    high = nyq + high if high <= 0 else high
    mel = lambda f: 1127.0 * np.log(1.0 + f / 700.0)
    mlow, mhigh = mel(low), mel(high)
    delta = (mhigh - mlow) / (num_bins + 1)
    n = n_fft // 2
    fft_mel = mel(np.arange(n) * sr / n_fft)
    banks = np.zeros((num_bins, n + 1), np.float32)
    for b in range(num_bins):
        l, c, r = mlow + b * delta, mlow + (b + 1) * delta, mlow + (b + 2) * delta
        up = (fft_mel - l) / (c - l)
        down = (r - fft_mel) / (r - c)
        banks[b, :n] = np.maximum(0.0, np.minimum(up, down))
    _MEL[key] = banks
    return banks


def kaldi_fbank(wav, sr=16000, num_bins=80, frame_ms=25.0, shift_ms=10.0, preemph=0.97, scale=1.0):
    """wav: float32 mono at 16 kHz (scale=32768 for models trained on int16-range audio)."""
    x = np.asarray(wav, np.float64) * scale
    flen, fshift = int(sr * frame_ms / 1000), int(sr * shift_ms / 1000)
    if len(x) < flen:
        return np.zeros((0, num_bins), np.float32)
    n = 1 + (len(x) - flen) // fshift
    idx = np.arange(flen)[None, :] + fshift * np.arange(n)[:, None]
    fr = x[idx]
    fr = fr - fr.mean(axis=1, keepdims=True)                       # remove DC
    fr = np.concatenate([fr[:, :1] * (1 - preemph), fr[:, 1:] - preemph * fr[:, :-1]], axis=1)
    win = (0.5 - 0.5 * np.cos(2 * np.pi * np.arange(flen) / (flen - 1))) ** 0.85  # povey
    fr = fr * win
    n_fft = 1 << int(np.ceil(np.log2(flen)))
    spec = np.abs(np.fft.rfft(fr, n=n_fft, axis=1)) ** 2
    mel = spec @ _mel_banks(num_bins, n_fft, sr).T.astype(np.float64)
    return np.log(np.maximum(mel, np.finfo(np.float32).eps)).astype(np.float32)


class SileroVAD:
    """silero-vad v4 (k2-fsa export: x[1,512], h, c -> prob). Returns speech spans in samples."""

    def __init__(self, path, threshold=0.5, min_silence=0.25, min_speech=0.10, sr=16000):
        import onnxruntime as ort

        so = ort.SessionOptions(); so.intra_op_num_threads = 1; so.inter_op_num_threads = 1
        self.sess = ort.InferenceSession(path, sess_options=so, providers=["CPUExecutionProvider"])
        self.th, self.min_sil, self.min_sp, self.sr = threshold, min_silence, min_speech, sr

    def probs(self, wav):
        w = 512
        h = np.zeros((2, 1, 64), np.float32); c = np.zeros((2, 1, 64), np.float32)
        out = []
        wav = np.asarray(wav, np.float32)
        for i in range(0, len(wav) - w + 1, w):
            p, h, c = self.sess.run(None, {"x": wav[None, i:i + w], "h": h, "c": c})
            out.append(float(p[0, 0]))
        return np.asarray(out)

    def spans(self, wav):
        w = 512
        p = self.probs(wav)
        spans, start, sil = [], None, 0
        min_sil_w = int(np.ceil(self.min_sil * self.sr / w))
        for i, v in enumerate(p):
            if start is None:
                if v > self.th:
                    start, sil = i, 0
            else:
                if v < self.th - 0.15:
                    sil += 1
                    if sil >= min_sil_w:
                        spans.append((start, i - sil + 1)); start = None
                elif v > self.th:
                    sil = 0
        if start is not None:
            spans.append((start, len(p) - sil))
        min_sp_w = self.min_sp * self.sr / w
        return [(a * w, b * w) for a, b in spans if b - a >= min_sp_w]
