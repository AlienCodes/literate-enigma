"""Harder sets so that good models can be told apart (4-second sets are almost saturated):
  en_short: the 300 EN-eval speakers, 4 new utterances each of 2 words (~2 s)  -> 1,800 target trials
  zh_short: every Mandarin segment cut into non-overlapping 2-second speech chunks (VAD'd audio)
"""
import os
import random

import librosa
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
SC = os.path.join(HERE, "data", "sc")
RNG = random.Random(4242)


def load(p):
    return librosa.load(p, sr=16000, mono=True)[0].astype(np.float32)


ev = set(np.load(os.path.join(HERE, "set_en_eval.npz"), allow_pickle=True)["labels"].tolist())
by = {}
for w in sorted(os.listdir(SC)):
    d = os.path.join(SC, w)
    if os.path.isdir(d) and not w.startswith("_"):
        for f in os.listdir(d):
            s = f.split("_nohash_")[0]
            if s in ev:
                by.setdefault(s, []).append(os.path.join(d, f))
audio, labels = [], []
for s in sorted(by):
    files = sorted(by[s]); RNG.shuffle(files)
    files = files[::-1]  # different order from build_sets (which used the first 8 after its own shuffle)
    for k in range(4):
        chunk = files[2 * k:2 * k + 2]
        if len(chunk) == 2:
            audio.append(np.concatenate([load(f) for f in chunk])); labels.append(s)
np.savez_compressed(os.path.join(HERE, "set_en_short.npz"), audio=np.array(audio, dtype=object),
                    labels=np.array(labels), allow_pickle=True)
print("en_short", len(audio), "utterances", len(set(labels)), "speakers")

zh = np.load(os.path.join(HERE, "set_zh.npz"), allow_pickle=True)
vad = np.load(os.path.join(HERE, "emb", "vad_zh.npy"), allow_pickle=True)
audio, labels, sessions = [], [], []
for v, lab, ses in zip(vad, zh["labels"], zh["sessions"]):
    n = 32000
    for i in range(len(v) // n):
        audio.append(np.asarray(v[i * n:(i + 1) * n], np.float32)); labels.append(lab); sessions.append(f"{ses}#{i}")
np.savez_compressed(os.path.join(HERE, "set_zh_short.npz"), audio=np.array(audio, dtype=object),
                    labels=np.array(labels), sessions=np.array(sessions), allow_pickle=True)
print("zh_short", len(audio), "chunks", len(set(labels)), "speakers")
