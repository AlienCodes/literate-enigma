import numpy as np
from voicetwin.utils.audio import load_audio

def gaps(path, segments, margin=0.002, label=""):
    """Return list of problems: non-zero samples outside segment extents, and big jumps (clicks)."""
    wav, sr = load_audio(path)
    probs = []
    m = int(margin * sr)
    first = int(round(segments[0]["start"] * sr))
    if not np.all(wav[: max(0, first - m)] == 0.0):
        probs.append(f"{label}: lead-in not zero (max {np.max(np.abs(wav[:first-m])):.2e})")
    for a, b in zip(segments, segments[1:]):
        lo, hi = int(round(a["end"] * sr)) + m, int(round(b["start"] * sr)) - m
        if hi <= lo:
            probs.append(f"{label}: no gap between {a['index']} and {b['index']} (end {a['end']} start {b['start']})")
            continue
        seg = wav[lo:hi]
        if not np.all(seg == 0.0):
            nz = np.nonzero(seg)[0]
            probs.append(f"{label}: gap {a['index']}->{b['index']} has {len(nz)} non-zero samples, max {np.max(np.abs(seg)):.2e}")
    last = int(round(segments[-1]["end"] * sr)) + m
    if not np.all(wav[last:] == 0.0):
        probs.append(f"{label}: tail not zero (max {np.max(np.abs(wav[last:])):.2e})")
    # clicks: sample-to-sample jumps near each boundary (±15 ms) vs. the largest jump inside speech
    d = np.abs(np.diff(wav))
    inner = []
    for s in segments:
        a, b = int(round(s["start"] * sr)), int(round(s["end"] * sr))
        k = int(0.03 * sr)
        if b - a > 2 * k:
            inner.append(np.max(d[a + k:b - k]))
    ref = max(inner) if inner else np.max(d)
    for s in segments:
        for t in (s["start"], s["end"]):
            c = int(round(t * sr)); k = int(0.015 * sr)
            j = np.max(d[max(0, c - k):min(len(d), c + k)])
            if j > 1.5 * ref and j > 0.02:
                probs.append(f"{label}: possible click at {t:.3f}s (jump {j:.3f} vs speech max {ref:.3f})")
    return probs, wav, sr
