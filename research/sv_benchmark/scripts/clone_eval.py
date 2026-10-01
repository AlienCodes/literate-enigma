"""Clone test: does each judge recognise a clone as (a copy of) its own speaker, and do judges agree on which
TTS system clones voices best?"""
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from metrics2 import HERE, asnorm, eer_dcf, load, meta, models_with  # noqa: E402

SYS = ["IndexTTS", "CosyVoice2", "F5-TTS", "FireRedTTS", "FishSpeech", "XTTS"]


def clone_scores(model, prep, norm):
    m = meta("clone")
    E = load(model, prep, "clone")
    P = np.flatnonzero(m["kind"] == "prompt")
    Cl = np.flatnonzero(m["kind"] == "clone")
    S = E[Cl] @ E[P].T if norm == "cos" else asnorm(E[Cl], E[P], load(model, prep, "en_cohort"))
    same = m["labels"][Cl][:, None] == m["labels"][P][None, :]
    return S, same, m["system"][Cl]


def summarize(S, same, systems):
    acc = float(np.mean(np.argmax(S, axis=1) == np.argmax(same, axis=1)))
    eer = eer_dcf(S.ravel(), same.ravel())[0]
    tgt = S[same]
    imp = S[~same]
    d = (tgt.mean() - imp.mean()) / np.sqrt(0.5 * (tgt.var() + imp.var()))
    per_sys = {s: float(np.mean(S[same][systems == s])) for s in SYS}
    return acc, eer, d, per_sys


def main(prep="raw", norm="asn"):
    models = models_with(["clone", "en_cohort"], prep)
    res = {}
    for mdl in models:
        S, same, systems = clone_scores(mdl, prep, norm)
        res[mdl] = (S, same, systems)
    print(f"{'model':52s} attrib%  EER%   d'   " + " ".join(f"{s[:8]:>8s}" for s in SYS))
    ranks = {}
    for mdl, (S, same, systems) in res.items():
        acc, eer, d, ps = summarize(S, same, systems)
        z = (np.array([ps[s] for s in SYS]) - S[~same].mean()) / S[~same].std()
        ranks[mdl] = np.argsort(np.argsort(-z))
        print(f"{mdl[:52]:52s} {acc*100:6.1f}  {eer*100:5.2f}  {d:5.2f} " + " ".join(f"{v:8.2f}" for v in z))
    out = {m: {"rank": ranks[m].tolist()} for m in ranks}
    json.dump(out, open(os.path.join(HERE, f"clone_{prep}_{norm}.json"), "w"), indent=1)


if __name__ == "__main__":
    main(*(sys.argv[1:3] or ["raw", "asn"]))
