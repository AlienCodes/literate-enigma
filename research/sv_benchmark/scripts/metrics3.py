"""Harder benchmark (2-second utterances): EN-short (300 speakers x 4 utts, split by speaker hash into A/B halves)
and ZH-short (2-s chunks of the Mandarin set). Single models and greedy fusion (selected on A + ZH-short,
reported on B). AS-norm cohort = en_cohort (400 other Speech Commands speakers)."""
import hashlib
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from metrics2 import EMB, HERE, asnorm, eer_dcf, load, meta  # noqa: E402

import glob


def models(prep):
    names = sorted({os.path.basename(p).split("__")[0] for p in glob.glob(os.path.join(EMB, f"*__{prep}__en_short.npy"))})
    return [n for n in names if all(os.path.exists(os.path.join(EMB, f"{n}__{prep}__{s}.npy"))
                                    for s in ("zh_short", "en_cohort"))]


en = meta("en_short")["labels"]
half = np.array([int(hashlib.md5(s.encode()).hexdigest(), 16) % 2 for s in en])
IDX = {"A": np.flatnonzero(half == 0), "B": np.flatnonzero(half == 1)}
ZS = meta("zh_short")["labels"]
ZKEEP = np.flatnonzero(np.array(["single_reference" not in x for x in ZS]))  # MOSS-TTSD dialogue file: 2 speakers
LAB = {"A": en[IDX["A"]], "B": en[IDX["B"]], "zs": ZS[ZKEEP]}
CACHE = {}


def scores(m, prep, norm, part):
    k = (m, prep, norm, part)
    if k not in CACHE:
        E = load(m, prep, "zh_short" if part == "zs" else "en_short")
        if part in IDX:
            E = E[IDX[part]]
        elif part == "zs":
            E = E[ZKEEP]
        S = E @ E.T if norm == "cos" else asnorm(E, E, load(m, prep, "en_cohort"))
        iu = np.triu_indices(len(E), 1)
        CACHE[k] = (S[iu], LAB[part][iu[0]] == LAB[part][iu[1]])
    return CACHE[k]


def fused(sel, part):
    return np.mean([scores(*m, part)[0] for m in sel], axis=0), scores(*sel[0], part)[1]


def main():
    rows = []
    for prep in ("raw",):
        for m in models(prep):
            for norm in ("cos", "asn"):
                r = {"model": m, "prep": prep, "norm": norm}
                for part in ("A", "B", "zs"):
                    r[part] = eer_dcf(*scores(m, prep, norm, part))
                rows.append(r)
    rows.sort(key=lambda r: r["A"][0] + r["B"][0] + r["zs"][0])
    print(f"{'model':52s} prep norm | EN2s-A  EN2s-B  DCF-B | ZH2s EER  DCF")
    for r in rows:
        print(f"{r['model'][:52]:52s} {r['prep']:4s} {r['norm']:4s} | {r['A'][0]*100:5.2f}%  {r['B'][0]*100:5.2f}%  "
              f"{r['B'][1]:5.3f} | {r['zs'][0]*100:5.2f}%  {r['zs'][1]:5.3f}")
    json.dump(rows, open(os.path.join(HERE, "metrics3_single.json"), "w"), indent=1)
    pool = [(r["model"], r["prep"], r["norm"]) for r in rows if r["norm"] == "asn"]
    obj = lambda sel: eer_dcf(*fused(sel, "A"))[0] + eer_dcf(*fused(sel, "zs"))[0] + 0.02 * eer_dcf(*fused(sel, "A"))[1]
    chosen, best = [], 9.0
    while pool and len(chosen) < 6:
        cand = sorted((obj(chosen + [m]), m) for m in pool)
        if cand[0][0] >= best - 1e-5:
            break
        best, mb = cand[0]
        chosen.append(mb); pool.remove(mb)
        eb, ez = eer_dcf(*fused(chosen, "B")), eer_dcf(*fused(chosen, "zs"))
        print(f"+ {mb[0][:50]:50s} -> EN2s-B EER {eb[0]*100:.2f}% DCF {eb[1]:.3f} | ZH2s EER {ez[0]*100:.2f}% DCF {ez[1]:.3f}")
    json.dump({"chosen": chosen}, open(os.path.join(HERE, "fusion3.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
