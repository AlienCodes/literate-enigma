"""Dev-machine timing (4 CPU cores, no GPU) of the proposed perceptual features on one 5 s, 32 kHz candidate.
Prototype implementations of: F0 contour features (yin, 10 ms), LTAS in 1/3-octave bands 100 Hz-15 kHz,
internal pause positions, and a Viterbi over 300 sentences x 6 candidates."""
import sys
import time
import numpy as np

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[3]))
from voicetwin.style.prosody import f0_track
from voicetwin.utils.audio import speech_activity, frame_rms_db, auto_silence_threshold, resample

SR = 32000
rng = np.random.default_rng(1)
t = np.arange(int(5 * SR)) / SR
f = 200 * (1 + 0.08 * np.sin(2 * np.pi * 0.5 * t)) * np.exp(-0.03 * t)
ph = 2 * np.pi * np.cumsum(f) / SR
x = sum(np.sin(k * ph) / k for k in range(1, 12)) * (0.55 + 0.45 * np.abs(np.sin(2 * np.pi * 2.3 * t)))
x[int(2.0 * SR):int(2.3 * SR)] = 0  # a comma pause
x = (0.25 * x / np.abs(x).max() + 0.002 * rng.standard_normal(len(x))).astype(np.float32)


def f0_features(wav, sr):
    w16 = resample(wav, sr, 16000)
    import librosa
    f0 = librosa.yin(w16, fmin=60, fmax=500, sr=16000, frame_length=1024, hop_length=160)
    db = frame_rms_db(w16, 16000, hop_ms=10.0, win_ms=40.0)
    n = min(len(f0), len(db))
    f0, db = f0[:n], db[:n]
    ok = (db > auto_silence_threshold(w16, 16000) + 6) & (f0 > 63) & (f0 < 475)
    if ok.sum() < 10:
        return {}
    tt = np.flatnonzero(ok) * 0.01
    st = 12 * np.log2(f0[ok] / np.median(f0[ok]))
    slope = np.polyfit(tt, st, 1)[0]
    tail = tt >= tt[-1] - 0.3
    fin = np.polyfit(tt[tail], st[tail], 1)[0] if tail.sum() >= 5 else 0.0
    return {"median": float(np.median(f0[ok])), "range": float(np.percentile(st, 90) - np.percentile(st, 10)),
            "decl": float(slope), "final": float(fin)}


EDGES = 1000 * 2 ** (np.arange(-10, 12) / 3)  # 1/3-octave centres ~100 Hz .. ~12.7 kHz


def ltas(wav, sr, n_fft=1024, hop=320):
    import scipy.signal as ss
    fr, _, Z = ss.stft(wav, sr, nperseg=n_fft, noverlap=n_fft - hop, boundary=None)
    p = (np.abs(Z) ** 2)
    e = p.sum(0)
    keep = e > np.percentile(e, 30)
    p = p[:, keep].mean(1)
    out = []
    for c in EDGES:
        lo, hi = c / 2 ** (1 / 6), c * 2 ** (1 / 6)
        m = (fr >= lo) & (fr < hi)
        out.append(10 * np.log10(p[m].mean() + 1e-12) if m.any() else np.nan)
    out = np.array(out)
    return out - np.nanmean(out)


def viterbi(n=300, k=6):
    u = rng.normal(size=(n, k))
    feat = rng.normal(size=(n, k, 3))
    best = u[0].copy()
    back = np.zeros((n, k), int)
    for i in range(1, n):
        d = feat[i][None, :, :] - feat[i - 1][:, None, :]
        trans = -0.5 * (d ** 2).sum(-1)
        tot = best[:, None] + trans
        back[i] = tot.argmax(0)
        best = tot.max(0) + u[i]
    return best.max()


def bench(fn, n=10):
    fn()
    a = time.perf_counter()
    for _ in range(n):
        fn()
    return (time.perf_counter() - a) / n * 1000


print(f"F0 contour features: {bench(lambda: f0_features(x, SR)):.0f} ms")
print(f"LTAS 1/3-octave (22 bands): {bench(lambda: ltas(x, SR)):.0f} ms")
print(f"speech_activity (pauses): {bench(lambda: speech_activity(x, SR)):.0f} ms")
print(f"Viterbi 300 sentences x 6 candidates: {bench(viterbi, 3):.0f} ms")
print("features:", {k: round(v, 3) for k, v in f0_features(x, SR).items()})
print("ltas:", np.round(ltas(x, SR), 1))
