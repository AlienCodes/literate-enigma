"""把 ReDimNet2 的官方权重导出成 ONNX（声纹打分用；发布 sv-models 时由 GitHub Actions 运行）。

    python scripts/export_redimnet2.py --out dist/sv-models [--model b6]

步骤：
1. 下载 ReDimNet2 代码（固定到某个提交）和官方权重（核对 sha256）；
2. 极小的权重（subnormal）置 0——不影响结果，避免某些 CPU 上变慢；
3. 导出 ONNX（输入 16 kHz 波形，输出 192 维声纹；梅尔频谱前端也在模型里）；
4. 用 onnxruntime 跑一遍，和 PyTorch 的结果逐个比较（余弦相似度必须 ≥ 0.99999），再算出自检向量。

ReDimNet2：Palabra.ai，MIT 许可，https://github.com/PalabraAI/redimnet2（Interspeech 2026）。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

REPO = "https://github.com/PalabraAI/redimnet2.git"
COMMIT = "c5bbe0b76e37df698c403f8844e41304ceab6307"
WEIGHTS = {
    "b6": ("b6-vb2+vox2+cnc2_v0-lm.pt", "287365f6f485b19e65e5176554f8f7123bfa8d85185f3d2c040eab51acec9868",
           "redimnet2_b6_vb2_vox2_cnc2_lm.onnx"),
    "b3": ("b3-vb2+vox2+cnc2_v0-lm.pt", "b64989536ef8822447d72517ad9019b870a951e85a3f176f0ed42d2a4c3d811d",
           "redimnet2_b3_vb2_vox2_cnc2_lm.onnx"),
}
WEIGHT_URL = "https://github.com/PalabraAI/redimnet2/releases/download/v1.0.0/{}"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def fetch(url: str, dst: Path, want: str) -> Path:
    if not dst.exists() or sha256(dst) != want:
        print(f"下载 {url}")
        urllib.request.urlretrieve(url, dst)
    got = sha256(dst)
    if got != want:
        raise SystemExit(f"{dst.name} 的 sha256 不对：{got}")
    return dst


def export(size: str, out_dir: Path, work: Path) -> dict:
    import numpy as np
    import onnxruntime as ort
    import torch

    from voicetwin.eval.sv_models import selftest_signal

    code = work / "redimnet2"
    if not code.exists():
        subprocess.run(["git", "clone", "-q", REPO, str(code)], check=True)
    subprocess.run(["git", "-C", str(code), "checkout", "-q", COMMIT], check=True)
    sys.path.insert(0, str(code))
    from redimnet2.redimnet2 import ReDimNet2Wrap  # type: ignore

    fname, digest, onnx_name = WEIGHTS[size]
    pt = fetch(WEIGHT_URL.format(fname), work / fname, digest)
    try:
        state = torch.load(str(pt), map_location="cpu", weights_only=False)
    except TypeError:
        state = torch.load(str(pt), map_location="cpu")
    tiny = torch.finfo(torch.float32).tiny
    for value in state["state_dict"].values():
        if value.dtype.is_floating_point:
            value[(value != 0) & (value.abs() < tiny)] = 0.0
    model = ReDimNet2Wrap(**state["model_config"])
    res = model.load_state_dict(state["state_dict"])
    assert not res.missing_keys and not res.unexpected_keys, res
    model.eval()

    out_dir.mkdir(parents=True, exist_ok=True)
    dst = out_dir / onnx_name
    example = torch.from_numpy(selftest_signal(4.0))[None]
    kwargs = dict(input_names=["wav"], output_names=["embedding"],
                  dynamic_axes={"wav": {0: "batch", 1: "samples"}, "embedding": {0: "batch"}},
                  opset_version=17, do_constant_folding=True)
    try:
        torch.onnx.export(model, (example,), str(dst), dynamo=False, **kwargs)
    except TypeError:  # 旧版 torch 没有 dynamo 参数
        torch.onnx.export(model, (example,), str(dst), **kwargs)

    opts = ort.SessionOptions()
    opts.add_session_config_entry("session.set_denormal_as_zero", "1")
    sess = ort.InferenceSession(str(dst), sess_options=opts, providers=["CPUExecutionProvider"])
    rng = np.random.default_rng(7)
    worst = 1.0
    for seconds in (0.6, 2.0, 5.0, 13.0):
        x = selftest_signal(seconds) + 0.01 * rng.standard_normal(int(16000 * seconds)).astype(np.float32)
        with torch.no_grad():
            ref = model(torch.from_numpy(x)[None])[0].numpy()
        got = sess.run(None, {"wav": x[None]})[0][0]
        worst = min(worst, float(np.dot(ref, got) / (np.linalg.norm(ref) * np.linalg.norm(got))))
    if worst < 0.99999:
        raise SystemExit(f"ONNX 和 PyTorch 的结果对不上：{worst}")
    emb = sess.run(None, {"wav": selftest_signal()[None]})[0][0]
    info = {"file": onnx_name, "size": dst.stat().st_size, "sha256": sha256(dst), "worst_cosine": round(worst, 7),
            "selftest": {"head": [round(float(v), 6) for v in emb[:16]], "norm": round(float(np.linalg.norm(emb)), 6)},
            "weights": fname, "weights_sha256": digest, "code_commit": COMMIT}
    print(json.dumps(info, ensure_ascii=False))
    return info


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="dist/sv-models")
    ap.add_argument("--model", action="append", choices=sorted(WEIGHTS), help="默认 b6")
    args = ap.parse_args()
    out = Path(args.out)
    with tempfile.TemporaryDirectory() as tmp:
        infos = [export(m, out, Path(tmp)) for m in (args.model or ["b6"])]
    (out / "redimnet2_export.json").write_text(json.dumps(infos, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
