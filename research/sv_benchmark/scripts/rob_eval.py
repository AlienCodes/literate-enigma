"""How much does product-style processing move the score of the SAME voice? (ideal: 0)

For every same-speaker pair (i, j) of different Mandarin segments: score(processed_i, original_j) minus
score(original_i, original_j), expressed in "similarity %" units of that model: 100 * delta / (mean target score -
mean impostor score) on the original set. Also reports EER of processed-vs-original trials.
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from metrics2 import asnorm, eer_dcf, load, meta  # noqa: E402

CONDS = ["dsil", "dn", "quiet", "loud", "noisy", "crop3", "crop15"]


def score(A, B, C, norm):
    return A @ B.T if norm == "cos" else asnorm(A, B, C)


def main(models, norm="asn"):
    lab = meta("zh")["labels"]
    same = lab[:, None] == lab[None, :]
    off = ~np.eye(len(lab), dtype=bool)
    print(f"{'model':40s} prep | " + " ".join(f"{c:>13s}" for c in CONDS))
    for m in models:
        for prep in ("raw", "vad"):
            E0 = load(m, prep, "zh")
            C = load(m, prep, "en_cohort")
            if E0 is None or C is None:
                continue
            S0 = score(E0, E0, C, norm)
            tgt, imp = S0[same & off].mean(), S0[~same].mean()
            cells = []
            for c in CONDS:
                Ec = load(m, prep, f"rob_{c}")
                if Ec is None:
                    cells.append(f"{'-':>13s}"); continue
                Sc = score(Ec, E0, C, norm)
                d = 100 * (Sc - S0)[same & off] / (tgt - imp)
                e = eer_dcf(Sc[off], same[off])[0]
                cells.append(f"{d.mean():+5.1f}±{d.std():4.1f}/{e*100:3.1f}")
            print(f"{m[:40]:40s} {prep:4s} | " + " ".join(cells))


if __name__ == "__main__":
    main(sys.argv[1:])
