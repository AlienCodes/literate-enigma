"""Energy-based "speech only" extraction (candidate for the product: no extra model needed).

Frames of 20 ms; a frame is speech when its level is above BOTH
  - the recording's own noise floor (10th percentile of non-silent frames) + 10 dB, and
  - the loudest frames (99th percentile) - 40 dB.
Exact digital silence is never speech. Speech runs are padded by 60 ms; gaps shorter than 100 ms are kept
(so syllables are not chopped); islands shorter than 60 ms are dropped.
"""
import numpy as np

SR = 16000
HOP = 320  # 20 ms


def speech_only(y, sr=SR, pad_ms=60, min_gap_ms=100, min_run_ms=60, min_keep_s=0.5):
    y = np.asarray(y, np.float32)
    n = len(y) // HOP
    if n < 5:
        return y
    fr = y[: n * HOP].reshape(n, HOP).astype(np.float64)
    e = np.mean(fr * fr, axis=1)
    live = e > 1e-12
    if not live.any():
        return y
    db = 10 * np.log10(np.maximum(e, 1e-20))
    floor = np.percentile(db[live], 10)
    top = np.percentile(db[live], 99)
    thr = max(floor + 10.0, top - 40.0)
    m = live & (db > thr)
    # fill short gaps
    gap = int(round(min_gap_ms / 20))
    idx = np.flatnonzero(m)
    if idx.size == 0:
        return y
    for a, b in zip(idx[:-1], idx[1:]):
        if 1 < b - a <= gap + 1:
            m[a:b] = True
    # drop tiny islands
    run = int(round(min_run_ms / 20))
    d = np.diff(np.concatenate([[0], m.astype(np.int8), [0]]))
    starts, ends = np.flatnonzero(d == 1), np.flatnonzero(d == -1)
    keep = np.zeros(n, bool)
    p = int(round(pad_ms / 20))
    for s, t in zip(starts, ends):
        if t - s >= run:
            keep[max(0, s - p):min(n, t + p)] = True
    keep &= live  # padding never brings back exact digital silence
    if keep.sum() * HOP < min_keep_s * sr:
        return y
    return y[: n * HOP].reshape(n, HOP)[keep].reshape(-1)
