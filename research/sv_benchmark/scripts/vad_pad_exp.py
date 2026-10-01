"""How much original pause audio to keep around each speech segment (VAD padding)? Measure, for ReDimNet2-B6 with
the product code: shift caused by digital-silence pauses (rob_dsil vs zh) and by denoise (rob_dn), and ZH EER."""
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, "/home/user/literate-enigma")
sys.path.insert(0, HERE)
from voicetwin.eval import sv_frontend as fe  # noqa: E402
from voicetwin.eval import sv_models  # noqa: E402
from voicetwin.eval.speaker import OnnxSVEncoder  # noqa: E402
from metrics2 import eer_dcf, meta  # noqa: E402
from prod_report import asn, cohort  # noqa: E402

MD = os.path.join(HERE, "models_prod")
key = sys.argv[1] if len(sys.argv) > 1 else "redimnet2-b6"
spec = sv_models.MODELS[key]
vad = fe.SileroVAD(os.path.join(MD, "silero_vad.onnx"))
enc = OnnxSVEncoder(spec, os.path.join(MD, spec.file), vad)
lab = meta("zh")["labels"]
keep = np.array(["single_reference" not in x for x in lab])
same = (lab[:, None] == lab[None, :]) & keep[:, None] & keep[None, :]
diff = (lab[:, None] != lab[None, :]) & keep[:, None] & keep[None, :]
off = ~np.eye(len(lab), dtype=bool)
data = {s: np.load(os.path.join(HERE, f"set_{s}.npz"), allow_pickle=True)["audio"] for s in ("zh", "rob_dsil", "rob_dn")}
C = cohort(key)
for pad in [float(x) for x in os.environ.get("PADS", "0.0,0.03,0.10,0.25").split(",")]:
    fe.VAD_PAD_SECONDS = pad
    E = {s: np.stack([enc.embed(np.asarray(a, np.float32), 16000) for a in data[s]]) for s in data}
    E = {s: v / np.linalg.norm(v, axis=1, keepdims=True) for s, v in E.items()}
    S0 = asn(E["zh"], E["zh"], C)
    tgt, imp = S0[same & off].mean(), np.percentile(S0[diff], 95)
    out = []
    for s in ("rob_dsil", "rob_dn"):
        d = 100 * (asn(E[s], E["zh"], C) - S0)[same & off] / (tgt - imp)
        out.append(f"{s}: {d.mean():+5.1f}±{d.std():4.1f}")
    e = eer_dcf(S0[off & (same | diff)], same[off & (same | diff)])
    print(f"pad {pad:.2f}s  ZH EER {e[0]*100:.2f}%  " + "  ".join(out), flush=True)
