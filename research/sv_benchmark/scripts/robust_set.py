"""Product-condition variants of the Mandarin set (set_zh): the same real recordings, processed the way VoiceTwin's
output differs from a raw lecture recording. A perfect judge gives the same score before and after (same voice).

  dsil   : pauses replaced by exact digital silence (what the "absolute silence" output looks like)
  dn     : VoiceTwin's light denoise (noisereduce, the "去杂音" version) + digital-silence pauses
  quiet  : -14 dB
  loud   : peak-normalised to -0.5 dBFS
  crop3  : first 3 s of speech     crop15 : first 1.5 s of speech
  noisy  : white noise added at 20 dB SNR (a worse microphone)
"""
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, "/home/user/literate-enigma")
from voicetwin.synth.engine import denoise_light  # noqa: E402

zh = dict(np.load(os.path.join(HERE, "set_zh.npz"), allow_pickle=True))
vad = np.load(os.path.join(HERE, "emb", "vad_zh.npy"), allow_pickle=True)
rng = np.random.default_rng(7)


def speech_mask(y, thr_db=None):
    """frame-level speech mask from energy (20 ms frames), threshold = noise floor + 12 dB"""
    hop = 320
    n = len(y) // hop
    e = 10 * np.log10(np.mean(y[: n * hop].reshape(n, hop) ** 2, axis=1) + 1e-12)
    floor = np.percentile(e, 10)
    m = e > max(floor + 12, e.max() - 45)
    # close small gaps (< 120 ms) and drop tiny islands (< 60 ms)
    out = m.copy()
    for i in range(n):
        if not m[i]:
            l = i - 1
            r = i + 1
            while l >= 0 and not m[l] and i - l < 6:
                l -= 1
            while r < n and not m[r] and r - i < 6:
                r += 1
            if l >= 0 and r < n and m[l] and m[r]:
                out[i] = True
    return np.repeat(out, hop), hop


def digital_silence(y):
    m, hop = speech_mask(y)
    out = np.zeros_like(y)
    out[: len(m)][m] = y[: len(m)][m]
    # 10 ms fades at every speech/silence boundary so there are no clicks (like the product)
    edges = np.flatnonzero(np.diff(m.astype(np.int8)))
    f = 160
    for e in edges:
        a, b = max(0, e - f), min(len(out), e + f)
        out[a:b] *= np.abs(np.linspace(-1, 1, b - a))
    return out


def crop_speech(v, sec):
    n = int(sec * 16000)
    return v[:n] if len(v) > n else v


conds = {
    "dsil": lambda y, v: digital_silence(y),
    "dn": lambda y, v: digital_silence(denoise_light(y, 16000) if denoise_light(y, 16000) is not None else y),
    "quiet": lambda y, v: y * 10 ** (-14 / 20),
    "loud": lambda y, v: y * (10 ** (-0.5 / 20) / max(1e-6, np.max(np.abs(y)))),
    "crop3": lambda y, v: crop_speech(v, 3.0),
    "crop15": lambda y, v: crop_speech(v, 1.5),
    "noisy": lambda y, v: y + rng.normal(0, 1, len(y)).astype(np.float32) * np.sqrt(np.mean(v ** 2) / 100),
}
for name, fn in conds.items():
    out = [np.asarray(fn(np.asarray(y, np.float32), np.asarray(v, np.float32)), np.float32)
           for y, v in zip(zh["audio"], vad)]
    np.savez_compressed(os.path.join(HERE, f"set_rob_{name}.npz"), audio=np.array(out, dtype=object),
                        labels=zh["labels"], sessions=zh["sessions"], allow_pickle=True)
    zero = np.mean([np.mean(a == 0) for a in out])
    print(name, "done; exact-zero samples: %.0f%%" % (100 * zero))
