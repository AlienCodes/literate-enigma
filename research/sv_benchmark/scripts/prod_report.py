"""Report for the PRODUCT pipeline embeddings (emb_prod/): accuracy, robustness, clones, calibration.

AS-norm cohort for evaluation = the 400 English cohort speakers (en_cohort, product frontend) + Mandarin demo
prompts from FunAudioLLM (cohort.json 'fun_' entries) that are NOT the same voice as any test speaker."""
import hashlib
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from metrics2 import eer_dcf, meta  # noqa: E402

P = os.path.join(HERE, os.environ.get("EMB_DIR", "emb_prod"))


def l2(x):
    return x / np.maximum(np.linalg.norm(x, axis=-1, keepdims=True), 1e-9)


def E(key, s):
    p = os.path.join(P, f"{key}__{s}.npy")
    return l2(np.load(p)) if os.path.exists(p) else None


def topk(X, C, k=100):
    s = X @ C.T
    t = np.sort(s, axis=1)[:, -k:]
    return t.mean(1), t.std(1) + 1e-6


def asn(A, B, C):
    S = A @ B.T
    ma, sa = topk(A, C); mb, sb = topk(B, C)
    return 0.5 * ((S - ma[:, None]) / sa[:, None] + (S - mb[None]) / sb[None])


def cohort(key):
    C = E(key, "en_cohort")
    extra = E(key, "zh_cohort_extra")
    if extra is not None:
        C = np.concatenate([C, extra])
    return C


def trials(S, lab):
    iu = np.triu_indices(len(lab), 1)
    return S[iu], lab[iu[0]] == lab[iu[1]]


def main(keys):
    en = meta("en_short")["labels"]
    half = np.array([int(hashlib.md5(s.encode()).hexdigest(), 16) % 2 for s in en])
    B = np.flatnonzero(half == 1)
    zl = meta("zh_short")["labels"]
    zk = np.flatnonzero(np.array(["single_reference" not in x for x in zl]))
    zfl = meta("zh")["labels"]
    zfk = np.flatnonzero(np.array(["single_reference" not in x for x in zfl]))
    out = {}
    scores = {}
    for key in keys:
        C = cohort(key)
        r = {}
        for name, s, idx, lab in (("EN2s-B", "en_short", B, en[B]), ("ZH2s", "zh_short", zk, zl[zk]),
                                  ("ZH", "zh", zfk, zfl[zfk])):
            X = E(key, s)[idx]
            for norm in ("cos", "asn"):
                S = X @ X.T if norm == "cos" else asn(X, X, C)
                sc, same = trials(S, lab)
                scores[(key, name, norm)] = (sc, same)
                r[f"{name}|{norm}"] = eer_dcf(sc, same)
        out[key] = r
        print(f"{key:18s} " + "  ".join(f"{k}: {v[0]*100:5.2f}%/{v[1]:.3f}" for k, v in r.items()))
    if len(keys) > 1:
        for norm in ("asn", "cos"):
            line = []
            for name in ("EN2s-B", "ZH2s", "ZH"):
                sc = np.mean([scores[(k, name, norm)][0] for k in keys], axis=0)
                e = eer_dcf(sc, scores[(keys[0], name, norm)][1])
                line.append(f"{name}|{norm}: {e[0]*100:5.2f}%/{e[1]:.3f}")
            print(f"{'FUSED ' + '+'.join(k.split('-')[0] for k in keys):18s} " + "  ".join(line))
    json.dump({k: {kk: list(vv) for kk, vv in v.items()} for k, v in out.items()},
              open(os.path.join(HERE, "prod_report.json"), "w"), indent=1)


if __name__ == "__main__":
    main(sys.argv[1:])


# ----------------------------------------------------------------------------- robustness / clones / calibration
CONDS = ["dsil", "dn", "quiet", "loud", "noisy", "crop3", "crop15"]


def robustness(keys):
    """How far does product-style processing move the score of the SAME voice? In % units of each model's scale
    (100 % = mean same-speaker score, 0 % = 95th percentile of different-speaker scores on the original set)."""
    lab = meta("zh")["labels"]
    keep = np.array(["single_reference" not in x for x in lab])
    same = (lab[:, None] == lab[None, :]) & keep[:, None] & keep[None, :]
    off = ~np.eye(len(lab), dtype=bool)
    diff = (lab[:, None] != lab[None, :]) & keep[:, None] & keep[None, :]
    rows = {}
    fused = {c: [] for c in CONDS}
    for key in keys:
        C = cohort(key)
        E0 = E(key, "zh")
        S0 = asn(E0, E0, C)
        tgt, imp = S0[same & off].mean(), np.percentile(S0[diff], 95)
        r = {}
        for c in CONDS:
            Ec = E(key, f"rob_{c}")
            if Ec is None:
                continue
            Sc = asn(Ec, E0, C)
            d = 100 * (Sc - S0)[same & off] / (tgt - imp)
            r[c] = (float(d.mean()), float(d.std()), eer_dcf(Sc[off & (same | diff)], same[off & (same | diff)])[0])
            fused[c].append(d)
        rows[key] = r
        print(f"{key:18s} " + "  ".join(f"{c}:{v[0]:+5.1f}±{v[1]:4.1f}" for c, v in r.items()))
    print(f"{'FUSED':18s} " + "  ".join(f"{c}:{np.mean(np.mean(v, 0)):+5.1f}±{np.std(np.mean(v, 0)):4.1f}"
                                       for c, v in fused.items() if v))
    return rows


def clones(keys):
    m = meta("clone")
    P = np.flatnonzero(m["kind"] == "prompt"); Cl = np.flatnonzero(m["kind"] == "clone")
    same = m["labels"][Cl][:, None] == m["labels"][P][None, :]
    systems = m["system"][Cl]
    allS = []
    for key in keys:
        X = E(key, "clone")
        S = asn(X[Cl], X[P], cohort(key))
        allS.append(S)
        acc = float(np.mean(np.argmax(S, 1) == np.argmax(same, 1)))
        print(f"{key:18s} clone attribution {acc*100:5.1f}%  EER {eer_dcf(S.ravel(), same.ravel())[0]*100:5.2f}%")
    S = np.mean(allS, 0)
    acc = float(np.mean(np.argmax(S, 1) == np.argmax(same, 1)))
    print(f"{'FUSED':18s} clone attribution {acc*100:5.1f}%  EER {eer_dcf(S.ravel(), same.ravel())[0]*100:5.2f}%")
    order = sorted(set(systems), key=lambda s: -np.mean(S[same][systems == s]))
    print("   system ranking (fused):", " > ".join(order))


if __name__ == "__main__" and len(sys.argv) > 1:
    keys = sys.argv[1:]
    print("== robustness (ZH, same voice: processed vs original, % units)")
    robustness(keys)
    print("== clones")
    clones(keys)
