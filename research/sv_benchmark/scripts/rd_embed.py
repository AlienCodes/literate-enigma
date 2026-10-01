"""Embeddings with ReDimNet (Interspeech 2024) and ReDimNet2 (Interspeech 2026) from local weight files.

usage: tvenv/bin/python rd_embed.py [name-substring ...]
"""
import os
import sys
import time

import numpy as np
import torch

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "repos", "redimnet2"))
from redimnet2.redimnet2 import ReDimNet2Wrap  # noqa: E402

sys.path.insert(0, os.path.join(HERE, "repos", "ReDimNet"))
from redimnet.model import ReDimNetWrap  # noqa: E402

torch.set_num_threads(int(os.environ.get("THREADS", "2")))
torch.set_flush_denormal(True)  # 10x faster on CPU (denormal floats in the frontend)
SETS = os.environ.get("SETS", "en_eval,en_cal,en_cohort,zh").split(",")
OUT = os.path.join(HERE, "emb")
WEIGHTS = {
    "redimnet2_b6_cnc": ("rd2", "b6-vb2+vox2+cnc2_v0-lm.pt"),
    "redimnet2_b3_cnc": ("rd2", "b3-vb2+vox2+cnc2_v0-lm.pt"),
    "redimnet2_b6_vb2": ("rd2", "b6-vb2+vox2_v0-lm.pt"),
    "redimnet2_b6_vox2": ("rd2", "b6-vox2-lm.pt"),
    "redimnet_M_cnc": ("rd1", "rd1_M-vb2+vox2+cnc-ft_mix.pt"),
    "redimnet_b6_vox2": ("rd1", "rd1_b6-vox2-ft_lm.pt"),
}


def load(name):
    kind, fn = WEIGHTS[name]
    sd = torch.load(os.path.join(HERE, "rd", fn), map_location="cpu", weights_only=False)
    tiny = torch.finfo(torch.float32).tiny
    for k, v in sd["state_dict"].items():  # subnormal weights (dead channels) make CPU math ~25x slower
        if v.dtype.is_floating_point:
            v[(v != 0) & (v.abs() < tiny)] = 0.0
    model = (ReDimNet2Wrap if kind == "rd2" else ReDimNetWrap)(**sd["model_config"])
    res = model.load_state_dict(sd["state_dict"])
    assert not res.missing_keys and not res.unexpected_keys, res
    return model.eval()


def main(filters):
    sets = {s: dict(np.load(os.path.join(HERE, f"set_{s}.npz"), allow_pickle=True)) for s in SETS}
    preps = os.environ.get("PREPS", "raw,vad").split(",")
    cache = {(p, s): np.load(os.path.join(OUT, f"{p}_{s}.npy"), allow_pickle=True) for p in preps if p != "raw"
             for s in SETS}
    for name in WEIGHTS:
        if filters and not any(f in name for f in filters):
            continue
        model = None
        for prep in preps:
            for s in SETS:
                p = os.path.join(OUT, f"{name}__{prep}__{s}.npy")
                if os.path.exists(p):
                    continue
                model = model or load(name)
                t0 = time.time()
                src = sets[s]["audio"] if prep == "raw" else cache[prep, s]
                embs = []
                with torch.inference_mode():
                    for a in src:
                        x = torch.from_numpy(np.asarray(a, np.float32))[None]
                        embs.append(model(x)[0].float().numpy())
                np.save(p, np.stack(embs))
                print(f"{name} {prep} {s}: {len(embs)} in {time.time() - t0:.0f}s", flush=True)


if __name__ == "__main__":
    main(sys.argv[1:])
