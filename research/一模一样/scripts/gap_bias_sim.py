"""Simulation (NOT the teacher's data): how far are VoiceTwin's measured pauses from the true pauses?

Part 1 - profile side. A synthetic 'lecture' is built from speech-like bursts (harmonic tone with syllable-rate
amplitude modulation and an exponential 60 ms decay at each end) separated by exact-zero gaps whose true lengths
come from a known distribution. find_segments (the real slicer, default params) cuts it into clips; the profile
uses gap_after of the clips (build_profile L42-55). We compare median(gap_after) with median(true gaps).

Part 2 - generation side. A synthetic GSV-like sentence (speech-like burst + 0.3 s trailing zeros, like
fragment_interval) goes through the real trim_edges + Narrator._render path (pad 30 ms, fades) with a requested
pause; the silence actually present between the two sentences is then measured with the SAME detector the slicer
uses to measure her gaps (frame_rms_db 10 ms hop / 40 ms window, auto_silence_threshold).
"""
import sys
import numpy as np

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[3]))
from voicetwin.data.slicer import find_segments
from voicetwin.synth.engine import trim_edges
from voicetwin.utils.audio import auto_silence_threshold, fade, frame_rms_db

SR = 32000
rng = np.random.default_rng(7)


def burst(sec, f0=210.0, level=0.25, decay=0.06):
    n = int(sec * SR)
    t = np.arange(n) / SR
    f = f0 * (1 + 0.04 * np.sin(2 * np.pi * 0.7 * t))
    ph = 2 * np.pi * np.cumsum(f) / SR
    x = sum(np.sin(k * ph) / k for k in range(1, 8))
    env = 0.55 + 0.45 * np.abs(np.sin(2 * np.pi * 2.3 * t))  # ~4.6 syllables / s
    x = x * env
    d = int(decay * SR)
    e = np.ones(n)
    e[:d] = 1 - np.exp(-np.arange(d) / (d / 5))
    e[-d:] = np.exp(-np.arange(d) / (d / 5))
    x = x * e
    return (level * x / np.max(np.abs(x))).astype(np.float32)


def measured_gaps(wav, sr):
    thr = auto_silence_threshold(wav, sr)
    db = frame_rms_db(wav, sr, hop_ms=10.0)
    sil = db < thr
    gaps, i, n = [], 0, len(sil)
    while i < n:
        if sil[i]:
            j = i
            while j < n and sil[j]:
                j += 1
            if i > 0 and j < n:
                gaps.append((j - i) * 0.01)
            i = j
        else:
            i += 1
    return gaps


# ---------------------------------------------------------------- part 1
true_gaps = []
pieces = []
for k in range(600):
    pieces.append(burst(rng.uniform(1.2, 4.0)))
    g = float(np.exp(rng.normal(np.log(0.45), 0.45)))  # true sentence gaps: median 0.45 s
    true_gaps.append(g)
    pieces.append(np.zeros(int(g * SR), np.float32))
lecture = np.concatenate(pieces)
segs = find_segments(lecture, SR)
ga = [s.gap_after for s in segs if s.gap_after]
inner = [g for s in segs for g in s.inner_gaps]
print("PART 1 (profile side, simulated lecture, true gap median 0.45 s)")
print(f"  true gaps: n={len(true_gaps)} median={np.median(true_gaps):.3f} p25={np.percentile(true_gaps,25):.3f} "
      f"p75={np.percentile(true_gaps,75):.3f}")
print(f"  clip gap_after (what build_profile uses): n={len(ga)} median={np.median(ga):.3f} "
      f"p25={np.percentile(ga,25):.3f} p75={np.percentile(ga,75):.3f}")
print(f"  gaps hidden inside clips (inner_gaps): n={len(inner)} median={np.median(inner):.3f}")
allm = measured_gaps(lecture, SR)
print(f"  every gap re-measured on the source with the slicer's detector: n={len(allm)} median={np.median(allm):.3f}")

# ---------------------------------------------------------------- part 2
print("PART 2 (generation side): requested pause vs silence measured with the slicer's detector")
for target in (0.25, 0.45, 0.70, 1.10):
    a = np.concatenate([burst(2.5), np.zeros(int(0.3 * SR), np.float32)])
    b = np.concatenate([burst(2.5), np.zeros(int(0.3 * SR), np.float32)])
    ta, tb = trim_edges(a, SR), trim_edges(b, SR)
    lead = 0.35
    out = np.zeros(int((lead + len(ta) / SR + target + len(tb) / SR + 0.4) * SR) + 1, np.float32)
    s0 = int(round(lead * SR))
    out[s0:s0 + len(ta)] += fade(ta, SR, 4.0, 8.0)
    s1 = int(round((lead + len(ta) / SR + target) * SR))
    out[s1:s1 + len(tb)] += fade(tb, SR, 4.0, 8.0)
    m = measured_gaps(out, SR)
    exact = (lambda z: z)(np.flatnonzero(out[s0:s1 + len(tb)] != 0))
    # longest exact-zero run between the two sentences
    nz = np.flatnonzero(out != 0)
    runs = np.diff(nz)
    zero_run = (runs.max() - 1) / SR
    print(f"  requested {target:.2f} s -> measured gap {m[0] if m else float('nan'):.3f} s "
          f"(exact-zero run {zero_run:.3f} s)")
