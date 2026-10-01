"""Build the evaluation sets (16 kHz float32 audio + speaker labels) and save them as npz.

EN: Google Speech Commands v0.02 (2,618 real speakers, browser/phone mics). One "utterance" = 4 different
    one-second word recordings of the same speaker, concatenated as recorded (their own room noise between words).
ZH: real Mandarin clips collected from public GitHub repositories (de-duplicated by audio hash) + sr-data
    (multi-session recordings of the same people).
"""
import glob
import hashlib
import os
import random
import re
import warnings

import librosa
import numpy as np

warnings.filterwarnings("ignore")
HERE = os.path.dirname(os.path.abspath(__file__))
SC = os.path.join(HERE, "data", "sc")
RNG = random.Random(20261001)


def load(path):
    y, _ = librosa.load(path, sr=16000, mono=True)
    return y.astype(np.float32)


def build_en(n_eval=300, n_cal=300, n_cohort=400, words_per_utt=4):
    by_spk = {}
    for w in sorted(os.listdir(SC)):
        d = os.path.join(SC, w)
        if not os.path.isdir(d) or w.startswith("_"):
            continue
        for f in os.listdir(d):
            by_spk.setdefault(f.split("_nohash_")[0], []).append(os.path.join(d, f))
    spks = sorted(s for s, fs in by_spk.items() if len(fs) >= 3 * words_per_utt)
    RNG.shuffle(spks)
    groups = {"eval": spks[:n_eval], "cal": spks[n_eval:n_eval + n_cal],
              "cohort": spks[n_eval + n_cal:n_eval + n_cal + n_cohort]}
    out = {}
    for g, members in groups.items():
        audio, labels = [], []
        for s in members:
            files = sorted(by_spk[s])
            RNG.shuffle(files)
            n_utt = 1 if g == "cohort" else 2
            for k in range(n_utt):
                chunk = files[k * words_per_utt:(k + 1) * words_per_utt]
                audio.append(np.concatenate([load(f) for f in chunk]))
                labels.append(s)
        out[g] = (audio, labels)
        print(g, len(audio), "utterances,", len(set(labels)), "speakers")
    return out


SAME = [(r"speaker1_.*_cn", "3dspk1_cn"), (r"speaker1_.*_en", "3dspk1_en"), (r"speaker2_.*_cn", "3dspk2_cn"), (r"speaker2_.*_en", "3dspk2_en"), (r"zh_man_sichuan|taiyizhenren|basic_ref_zh", "sichuan_man"), (r"fear_zh_female|Tingting_prompt", "stepfun_tingting"), (r"fangjun", "fangjun"), (r"leijun", "leijun"),
        (r"liudehua", "liudehua")]


def split_halves(y, min_half=2.5):
    """Split at the quietest 200 ms window near the middle (so no word is cut in half)."""
    if len(y) < 2 * min_half * 16000:
        return [y]
    mid = len(y) // 2
    lo, hi = int(mid - 0.25 * len(y)), int(mid + 0.25 * len(y))
    win = 3200
    best, best_e = mid, None
    for start in range(lo, hi - win, 800):
        e = float(np.mean(y[start:start + win] ** 2))
        if best_e is None or e < best_e:
            best, best_e = start + win // 2, e
    return [y[:best], y[best:]]


def build_zh():
    files = sorted(glob.glob(os.path.join(HERE, "data", "zh", "*"))) + \
        sorted(glob.glob(os.path.join(HERE, "data", "sr-data", "**", "*.wav"), recursive=True))
    seen, audio, labels, sessions = {}, [], [], []
    for f in files:
        y = load(f)
        h = hashlib.md5(np.round(y[:160000], 3).tobytes()).hexdigest()
        if h in seen:
            print("duplicate:", os.path.basename(f), "==", os.path.basename(seen[h]))
            continue
        seen[h] = f
        base = os.path.basename(f)
        spk = next((lab for pat, lab in SAME if re.search(pat, base)), base)
        if spk == base:  # one clip of this speaker: make a same-session pair from its two halves
            for i, part in enumerate(split_halves(y)):
                audio.append(part); labels.append(spk); sessions.append(f"{base}#half{i}")
        else:
            audio.append(y); labels.append(spk); sessions.append(base)
    print("zh", len(audio), "segments,", len(set(labels)), "speakers")
    return audio, labels, sessions


if __name__ == "__main__":
    en = build_en()
    for g, (audio, labels) in en.items():
        np.savez_compressed(os.path.join(HERE, f"set_en_{g}.npz"), labels=np.array(labels),
                            audio=np.array(audio, dtype=object), allow_pickle=True)
    audio, labels, sessions = build_zh()
    np.savez_compressed(os.path.join(HERE, "set_zh.npz"), labels=np.array(labels), sessions=np.array(sessions),
                        audio=np.array(audio, dtype=object), allow_pickle=True)
