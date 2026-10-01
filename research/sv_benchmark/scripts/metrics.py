"""Measure speaker-verification accuracy for every cached model / preprocessing, plus fused ensembles.

Reports EER and minDCF(0.01) on:
  EN-eval: 300 Speech Commands speakers (600 utterances, every cross pair used as an impostor trial)
  ZH:      43 Mandarin speakers (86 segments)
Scores: raw cosine, and AS-norm against the EN cohort (400 other speakers, top-100).
"""
import glob
import itertools
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
EMB = os.path.join(HERE, "emb")
TOPK = 100


def l2(x):
    return x / np.maximum(np.linalg.norm(x, axis=-1, keepdims=True), 1e-9)


def labels(s):
    return np.load(os.path.join(HERE, f"set_{s}.npz"), allow_pickle=True)["labels"]


def trial_mask(lab):
    n = len(lab)
    iu = np.triu_indices(n, 1)
    same = (lab[iu[0]] == lab[iu[1]])
    return iu, same


def eer_dcf(scores, same, p_target=0.01):
    order = np.argsort(scores)
    s = scores[order]; y = same[order]
    n_t, n_n = y.sum(), (~y).sum()
    frr = np.concatenate([[0], np.cumsum(y)]) / n_t          # targets below threshold (rejected)
    far = 1 - np.concatenate([[0], np.cumsum(~y)]) / n_n       # non-targets above threshold (accepted)
    i = np.argmin(np.abs(frr - far))
    eer = (frr[i] + far[i]) / 2
    dcf = np.min(p_target * frr + (1 - p_target) * far) / min(p_target, 1 - p_target)
    return float(eer), float(dcf)


def asnorm_matrix(E, C, topk=TOPK):
    """AS-norm for all pairs of E (n x d) against cohort C (m x d)."""
    S = E @ E.T
    cs = E @ C.T                                  # n x m
    top = -np.sort(-cs, axis=1)[:, :topk]
    mu, sd = top.mean(1), top.std(1) + 1e-6
    Z = (S - mu[:, None]) / sd[:, None]
    return 0.5 * (Z + Z.T)


def load_emb(model, prep, s):
    p = os.path.join(EMB, f"{model}__{prep}__{s}.npy")
    return l2(np.load(p)) if os.path.exists(p) else None


def models_available():
    names = sorted({os.path.basename(p).split("__")[0] for p in glob.glob(os.path.join(EMB, "*__raw__zh.npy"))})
    return [n for n in names if os.path.exists(os.path.join(EMB, f"{n}__vad__zh.npy"))]


def score_set(model, prep, s, norm):
    E = load_emb(model, prep, s)
    if norm == "cos":
        return E @ E.T
    C = load_emb(model, prep, "en_cohort")
    return asnorm_matrix(E, C)


def main():
    models = models_available()
    lab = {s: labels(s) for s in ("en_eval", "en_cal", "zh")}
    tm = {s: trial_mask(lab[s]) for s in lab}
    res = {}
    for m in models:
        for prep in ("raw", "vad"):
            for norm in ("cos", "asn"):
                row = {}
                for s in ("en_eval", "en_cal", "zh"):
                    iu, same = tm[s]
                    sc = score_set(m, prep, s, norm)[iu]
                    row[s] = eer_dcf(sc, same)
                res[f"{m}|{prep}|{norm}"] = row
    print(f"{'model':58s} {'prep':4s} {'norm':4s}  EN-EER  EN-DCF  ZH-EER  ZH-DCF")
    for k, row in sorted(res.items(), key=lambda kv: kv[1]["en_eval"][0]):
        m, prep, norm = k.split("|")
        print(f"{m[:58]:58s} {prep:4s} {norm:4s}  {row['en_eval'][0]*100:5.2f}%  {row['en_eval'][1]:6.3f}  "
              f"{row['zh'][0]*100:5.2f}%  {row['zh'][1]:6.3f}")
    json.dump(res, open(os.path.join(HERE, "metrics_single.json"), "w"), indent=1)

    # ---- fusion: greedy forward selection on EN-cal (+ZH weight), report on EN-eval and ZH
    def fused(sel, s, prep="vad"):
        iu, _ = tm[s]
        return np.mean([score_set(m, prep, s, "asn")[iu] for m in sel], axis=0)

    def objective(sel):
        e_cal = eer_dcf(fused(sel, "en_cal"), tm["en_cal"][1])[0]
        e_zh = eer_dcf(fused(sel, "zh"), tm["zh"][1])[0]
        return e_cal + e_zh

    chosen, best = [], 9
    pool = list(models)
    while pool:
        cand = sorted(((objective(chosen + [m]), m) for m in pool))
        if cand[0][0] >= best - 1e-4:
            break
        best, mbest = cand[0]
        chosen.append(mbest); pool.remove(mbest)
        e = eer_dcf(fused(chosen, "en_eval"), tm["en_eval"][1]); z = eer_dcf(fused(chosen, "zh"), tm["zh"][1])
        print(f"+ {mbest[:56]:56s} -> EN-eval EER {e[0]*100:.2f}% DCF {e[1]:.3f} | ZH EER {z[0]*100:.2f}% DCF {z[1]:.3f}")
    json.dump({"chosen": chosen}, open(os.path.join(HERE, "fusion_chosen.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
