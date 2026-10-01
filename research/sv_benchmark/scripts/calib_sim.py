"""Where do clones land on the calibrated % scale? Per clone-set speaker: enrol = first half of the real prompt,
held-out own = second half (-> 100%), impostors = en_cohort + other speakers' prompts (-> 0% at percentile q)."""
import os
import sys

import numpy as np
import onnxruntime as ort

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_sets import split_halves  # noqa: E402
from metrics2 import HERE, load, meta  # noqa: E402

name = sys.argv[1] if len(sys.argv) > 1 else "redimnet2_b6_cnc"
so = ort.SessionOptions(); so.intra_op_num_threads = 4
so.add_session_config_entry("session.set_denormal_as_zero", "1")
sess = ort.InferenceSession(os.path.join(HERE, "onnx", f"{name}.onnx"), sess_options=so, providers=["CPUExecutionProvider"])
emb = lambda a: (lambda e: e / np.linalg.norm(e))(sess.run(None, {"wav": np.asarray(a, np.float32)[None]})[0][0])

d = dict(np.load(os.path.join(HERE, "set_clone.npz"), allow_pickle=True))
E = load(name, "raw", "clone")
C = load(name, "raw", "en_cohort")
lab, kind, system = d["labels"], d["kind"], d["system"]


def topk(x, k=100):
    s = np.sort(C @ x)[-k:]
    return s.mean(), s.std() + 1e-6


def asn(x, enr, enr_stats):
    s = float(x @ enr); t = topk(x)
    return 0.5 * ((s - enr_stats[0]) / enr_stats[1] + (s - t[0]) / t[1])


res = {q: {} for q in (50, 90, 95, 99)}
gaps = []
for spk in sorted(set(lab)):
    p = np.flatnonzero((lab == spk) & (kind == "prompt"))[0]
    halves = split_halves(np.asarray(d["audio"][p], np.float32), min_half=2.0)
    if len(halves) < 2:
        continue
    A, B = emb(halves[0]), emb(halves[1])
    st = topk(A)
    G = asn(B, A, st)
    imp = [asn(c, A, st) for c in C] + [asn(E[j], A, st) for j in np.flatnonzero((lab != spk) & (kind == "prompt"))]
    full_prompt = asn(E[p], A, st)
    for q in res:
        I = np.percentile(imp, q)
        for j in np.flatnonzero((lab == spk) & (kind == "clone")):
            res[q].setdefault(system[j], []).append(100 * (asn(E[j], A, st) - I) / (G - I))
        res[q].setdefault("_impostor_max", []).append(100 * (max(imp) - I) / (G - I))
    gaps.append(G - np.percentile(imp, 95))
print(f"{name}: clone % of the way from impostor(q) to held-out own recording (median over clones)")
for q, r in res.items():
    print(f" q={q:2d}: " + "  ".join(f"{k}:{np.median(v):5.0f}" for k, v in sorted(r.items(), key=lambda kv: -np.median(kv[1]))))
