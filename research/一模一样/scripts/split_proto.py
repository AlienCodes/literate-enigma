"""Prototype: split one api_v2 answer that holds N fragments (each followed by fragment_interval exact zeros,
TTS.py audio_postprocess L1551-1561 @abe9843) back into N candidates. Returns None when ambiguous -> caller
falls back to N single requests."""
import numpy as np
def split_fragments(x, sr, n, interval=0.5, min_piece=0.3):
    x = np.asarray(x)
    need = int(0.6 * interval * sr)          # v3/v4: zeros are sized with configs.sampling_rate, wav may be 48 kHz
    z = np.concatenate([[False], x == 0, [False]])
    d = np.diff(z.astype(np.int8))
    starts, ends = np.flatnonzero(d == 1), np.flatnonzero(d == -1)
    runs = [(s, e) for s, e in zip(starts, ends) if e - s >= need]
    if len(runs) != n or runs[-1][1] != len(x):
        return None
    out, prev = [], 0
    for s, e in runs:
        piece = x[prev:s]
        if len(piece) < min_piece * sr or not piece.any():
            return None
        out.append(piece); prev = e
    return out
rng = np.random.default_rng(0)
sr = 32000
def frag(sec, internal_zero=0.0):
    a = (rng.standard_normal(int(sec * sr)) * 3000).astype(np.int16)
    if internal_zero:
        k = len(a) // 2; a[k:k + int(internal_zero * sr)] = 0
    return a
z = np.zeros(int(0.5 * sr), np.int16)
ok = np.concatenate([np.concatenate([frag(s), z]) for s in (4.1, 5.0, 3.7, 4.4)])
p = split_fragments(ok, sr, 4); print("normal:", [round(len(q) / sr, 2) for q in p])
amb = np.concatenate([np.concatenate([frag(4, internal_zero=0.4), z]), np.concatenate([frag(4), z])])
print("internal 0.4 s digital silence ->", split_fragments(amb, sr, 2))
short = np.concatenate([np.concatenate([frag(4), z]), np.concatenate([frag(4), z])])
print("asked 3 but got 2 ->", split_fragments(short, sr, 3))
print("v4-style 48 kHz wav with zeros sized at 32 kHz ->",
      [round(len(q) / 48000, 2) for q in split_fragments(np.concatenate([np.concatenate([(rng.standard_normal(48000*4)*3000).astype(np.int16), np.zeros(16000, np.int16)]) for _ in range(3)]), 48000, 3)])
