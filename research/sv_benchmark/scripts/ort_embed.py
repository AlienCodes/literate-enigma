"""Embeddings for fbank-input ONNX speaker models run with plain onnxruntime + our numpy Kaldi fbank
(training-style frontend: snip_edges, 20 Hz..Nyquist, mean-normalised), saved as <model>@np__<prep>__<set>.npy.
usage: SETS=... PREPS=... python3 ort_embed.py model-substring ..."""
import glob
import os
import sys
import time

import numpy as np
import onnxruntime as ort

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from np_frontend import kaldi_fbank  # noqa: E402

OUT = os.path.join(HERE, "emb")
SETS = os.environ.get("SETS", "en_eval,en_cohort,zh").split(",")
PREPS = os.environ.get("PREPS", "raw").split(",")


def main(filters):
    sets = {s: dict(np.load(os.path.join(HERE, f"set_{s}.npz"), allow_pickle=True)) for s in SETS}
    for m in sorted(glob.glob(os.path.join(HERE, "models", "*.onnx"))):
        name = os.path.basename(m)[:-5]
        if "silero" in name or not any(f in name for f in filters):
            continue
        so = ort.SessionOptions(); so.intra_op_num_threads = int(os.environ.get("THREADS", "4"))
        sess = ort.InferenceSession(m, sess_options=so, providers=["CPUExecutionProvider"])
        md = sess.get_modelmeta().custom_metadata_map
        scale = 32768.0 if md.get("normalize_samples", "1") == "0" else 1.0
        inp = sess.get_inputs()[0].name
        for prep in PREPS:
            for s in SETS:
                p = os.path.join(OUT, f"{name}@np__{prep}__{s}.npy")
                if os.path.exists(p):
                    continue
                src = sets[s]["audio"] if prep == "raw" else np.load(os.path.join(OUT, f"{prep}_{s}.npy"), allow_pickle=True)
                t0 = time.time()
                embs = []
                for a in src:
                    f = kaldi_fbank(np.asarray(a, np.float32), scale=scale)
                    f = f - f.mean(0, keepdims=True)
                    embs.append(sess.run(None, {inp: f[None]})[0][0].astype(np.float32))
                np.save(p, np.stack(embs))
                print(f"{name}@np {prep} {s}: {len(embs)} in {time.time() - t0:.0f}s", flush=True)


if __name__ == "__main__":
    main(sys.argv[1:])
