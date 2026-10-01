"""Embeddings for waveform-input ONNX models (our ReDimNet/ReDimNet2 exports in onnx/) with onnxruntime.
usage: SETS=... PREPS=... python ort_wave_embed.py name ..."""
import os
import sys
import time

import numpy as np
import onnxruntime as ort

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "emb")
SETS = os.environ.get("SETS", "en_eval,en_cohort,zh").split(",")
PREPS = os.environ.get("PREPS", "raw,vad").split(",")


def main(names):
    sets = {s: dict(np.load(os.path.join(HERE, f"set_{s}.npz"), allow_pickle=True)) for s in SETS}
    for name in names:
        so = ort.SessionOptions(); so.intra_op_num_threads = int(os.environ.get("THREADS", "4"))
        so.add_session_config_entry("session.set_denormal_as_zero", "1")
        sess = ort.InferenceSession(os.path.join(HERE, "onnx", f"{name}.onnx"), sess_options=so,
                                    providers=["CPUExecutionProvider"])
        for prep in PREPS:
            for s in SETS:
                p = os.path.join(OUT, f"{name}__{prep}__{s}.npy")
                if os.path.exists(p):
                    continue
                src = sets[s]["audio"] if prep == "raw" else np.load(os.path.join(OUT, f"{prep}_{s}.npy"), allow_pickle=True)
                t0 = time.time()
                embs = [sess.run(None, {"wav": np.asarray(a, np.float32)[None]})[0][0] for a in src]
                np.save(p, np.stack(embs).astype(np.float32))
                print(f"{name} {prep} {s}: {len(embs)} in {time.time() - t0:.0f}s", flush=True)


if __name__ == "__main__":
    main(sys.argv[1:])
