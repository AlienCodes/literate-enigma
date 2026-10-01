"""End-to-end benchmark of the PRODUCT code (voicetwin.eval: silero-vad speech-only frontend, numpy fbank,
onnxruntime models), so the reported accuracy is what users get.

  tvenv/bin/python prod_bench.py embed KEY [KEY ...]     -> emb_prod/<key>__<set>.npy
"""
import os
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, "/home/user/literate-enigma")
from voicetwin.eval import sv_models  # noqa: E402
from voicetwin.eval.speaker import OnnxSVEncoder  # noqa: E402
from voicetwin.eval.sv_frontend import SileroVAD  # noqa: E402

MD = os.path.join(HERE, "models_prod")
OUT = os.path.join(HERE, "emb_prod")
os.makedirs(OUT, exist_ok=True)
SETS = os.environ.get("SETS", "zh,zh_short,en_short,en_cohort,clone,rob_dsil,rob_dn,rob_quiet,rob_loud,rob_noisy,"
                      "rob_crop3,rob_crop15").split(",")


def main(keys):
    vad = SileroVAD(os.path.join(MD, "silero_vad.onnx"))
    data = {}
    for key in keys:
        spec = sv_models.MODELS[key]
        enc = OnnxSVEncoder(spec, os.path.join(MD, spec.file), vad)
        for s in SETS:
            p = os.path.join(OUT, f"{key}__{s}.npy")
            if os.path.exists(p):
                continue
            if s not in data:
                data[s] = np.load(os.path.join(HERE, f"set_{s}.npz"), allow_pickle=True)["audio"]
            t0 = time.time()
            E = np.stack([enc.embed(np.asarray(a, np.float32), 16000) for a in data[s]])
            np.save(p, E.astype(np.float32))
            print(f"{key} {s}: {len(E)} in {time.time() - t0:.0f}s", flush=True)


if __name__ == "__main__":
    main(sys.argv[2:] if sys.argv[1] == "embed" else [])
