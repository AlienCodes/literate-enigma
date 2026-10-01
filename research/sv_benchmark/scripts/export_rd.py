"""Export ReDimNet2 (waveform -> 192-d embedding, mel frontend included) to ONNX and check it against torch."""
import os
import sys
import time

import numpy as np
import onnxruntime as ort
import torch

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import rd_embed  # noqa: E402

torch.set_flush_denormal(True)
os.makedirs(os.path.join(HERE, "onnx"), exist_ok=True)


def export(name, opset=17):
    model = rd_embed.load(name)
    out = os.path.join(HERE, "onnx", f"{name}.onnx")
    x = torch.randn(1, 16000 * 4) * 0.1
    torch.onnx.export(model, (x,), out, input_names=["wav"], output_names=["embedding"],
                      dynamic_axes={"wav": {0: "batch", 1: "samples"}, "embedding": {0: "batch"}},
                      opset_version=opset, dynamo=False, do_constant_folding=True)
    sess = ort.InferenceSession(out, providers=["CPUExecutionProvider"])
    sets = dict(np.load(os.path.join(HERE, "set_zh.npz"), allow_pickle=True))
    worst = 1.0
    t_onnx = t_torch = 0.0
    for a in list(sets["audio"])[:12] + [np.random.randn(16000 * 2).astype(np.float32) * 0.05,
                                         np.random.randn(16000 * 23).astype(np.float32) * 0.05]:
        a = np.asarray(a, np.float32)[None]
        t0 = time.time()
        with torch.inference_mode():
            e1 = model(torch.from_numpy(a))[0].numpy()
        t_torch += time.time() - t0
        t0 = time.time()
        e2 = sess.run(None, {"wav": a})[0][0]
        t_onnx += time.time() - t0
        cos = float(np.dot(e1, e2) / np.linalg.norm(e1) / np.linalg.norm(e2))
        worst = min(worst, cos)
    print(f"{name}: {os.path.getsize(out) / 1e6:.1f} MB, worst cosine torch vs onnx = {worst:.6f}, "
          f"time torch {t_torch:.1f}s onnx {t_onnx:.1f}s")


if __name__ == "__main__":
    for n in sys.argv[1:]:
        export(n)
