"""Accuracy of every model (raw/vad audio x cosine/AS-norm) and of fused ensembles.

EN : Speech Commands eval group, speakers split in two halves by hash -> A (model selection) / B (reporting).
ZH : Mandarin set (42 speakers).  CLONE: 24 prompts + 154 zero-shot clones (6 systems).
AS-norm cohort: 400 other Speech Commands speakers (top-100).
"""
import glob
import hashlib
import json
import os
import sys
from itertools import combinations

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
EMB = os.path.join(HERE, "emb")
TOPK = 100


def l2(x):
    return x / np.maximum(np.linalg.norm(x, axis=-1, keepdims=True), 1e-9)


def meta(s):
    d = np.load(os.path.join(HERE, f"set_{s}.npz"), allow_pickle=True)
    return {k: d[k] for k in d.files if k != "audio"}


def eer_dcf(scores, same, p_target=0.01):
    order = np.argsort(scores, kind="stable")
    y = same[order]
    n_t, n_n = y.sum(), (~y).sum()
    frr = np.concatenate([[0], np.cumsum(y)]) / n_t
    far = 1 - np.concatenate([[0], np.cumsum(~y)]) / n_n
    i = np.argmin(np.abs(frr - far))
    return float((frr[i] + far[i]) / 2), float(np.min(p_target * frr + (1 - p_target) * far) / p_target)


def load(model, prep, s):
    p = os.path.join(EMB, f"{model}__{prep}__{s}.npy")
    return l2(np.load(p)) if os.path.exists(p) else None


def asnorm(E, F, C, topk=TOPK):
    """AS-norm scores between rows of E and rows of F (cohort C)."""
    S = E @ F.T
    te = -np.sort(-(E @ C.T), axis=1)[:, :topk]
    tf = -np.sort(-(F @ C.T), axis=1)[:, :topk]
    return 0.5 * ((S - te.mean(1)[:, None]) / (te.std(1)[:, None] + 1e-6) +
                  (S - tf.mean(1)[None, :]) / (tf.std(1)[None, :] + 1e-6))


def models_with(sets, prep="raw"):
    names = sorted({os.path.basename(p).split("__")[0] for p in glob.glob(os.path.join(EMB, "*__raw__zh.npy"))})
    return [n for n in names if all(os.path.exists(os.path.join(EMB, f"{n}__{prep}__{s}.npy")) for s in sets)]


class Bench:
    def __init__(self):
        en = meta("en_eval")["labels"]
        half = np.array([int(hashlib.md5(s.encode()).hexdigest(), 16) % 2 for s in en])
        self.idx = {"A": np.flatnonzero(half == 0), "B": np.flatnonzero(half == 1)}
        self.lab = {"A": en[self.idx["A"]], "B": en[self.idx["B"]], "zh": meta("zh")["labels"]}
        self.cache = {}

    def scores(self, model, prep, norm, part):
        key = (model, prep, norm, part)
        if key in self.cache:
            return self.cache[key]
        s = "zh" if part == "zh" else "en_eval"
        E = load(model, prep, s)
        if part in ("A", "B"):
            E = E[self.idx[part]]
        S = E @ E.T if norm == "cos" else asnorm(E, E, load(model, prep, "en_cohort"))
        iu = np.triu_indices(len(E), 1)
        lab = self.lab[part]
        out = (S[iu], lab[iu[0]] == lab[iu[1]])
        self.cache[key] = out
        return out

    def fused(self, members, part):
        sc = [self.scores(m, p, n, part)[0] for m, p, n in members]
        z = [(x - x.mean()) / x.std() for x in sc] if members[0][2] == "cos" else sc
        return np.mean(z, axis=0), self.scores(*members[0], part)[1]


def main():
    b = Bench()
    rows = []
    for m in models_with(["en_eval", "en_cohort", "zh"]):
        for prep in ("raw", "vad"):
            if load(m, prep, "zh") is None or load(m, prep, "en_eval") is None:
                continue
            for norm in ("cos", "asn"):
                r = {"model": m, "prep": prep, "norm": norm}
                for part in ("A", "B", "zh"):
                    r[part] = eer_dcf(*b.scores(m, prep, norm, part))
                rows.append(r)
    rows.sort(key=lambda r: r["A"][0] + r["B"][0])
    print(f"{'model':52s} prep norm | EN-A EER  EN-B EER  DCF-B | ZH EER  ZH DCF")
    for r in rows:
        print(f"{r['model'][:52]:52s} {r['prep']:4s} {r['norm']:4s} | {r['A'][0]*100:6.2f}%  {r['B'][0]*100:6.2f}%  "
              f"{r['B'][1]:5.3f} | {r['zh'][0]*100:5.2f}%  {r['zh'][1]:5.3f}")
    json.dump(rows, open(os.path.join(HERE, "metrics2_single.json"), "w"), indent=1)

    for prep in ("vad", "raw"):
        pool = [(r["model"], r["prep"], r["norm"]) for r in rows if r["prep"] == prep and r["norm"] == "asn"]
        obj = lambda sel: (eer_dcf(*b.fused(sel, "A"))[0] + eer_dcf(*b.fused(sel, "zh"))[0]
                           + 0.01 * eer_dcf(*b.fused(sel, "A"))[1])
        chosen, best = [], 9.0
        while pool:
            cand = sorted((obj(chosen + [m]), m) for m in pool)
            if cand[0][0] >= best - 1e-5 or len(chosen) >= 6:
                break
            best, mbest = cand[0]
            chosen.append(mbest); pool.remove(mbest)
            eb = eer_dcf(*b.fused(chosen, "B")); ez = eer_dcf(*b.fused(chosen, "zh"))
            print(f"[{prep}] + {mbest[0][:50]:50s} -> EN-B EER {eb[0]*100:.2f}% DCF {eb[1]:.3f} | "
                  f"ZH EER {ez[0]*100:.2f}% DCF {ez[1]:.3f}")
        json.dump({"chosen": chosen}, open(os.path.join(HERE, f"fusion2_{prep}.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
