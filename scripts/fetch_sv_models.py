"""从模型原作者的发布页下载声纹打分用的模型（核对 sha256），放到 --out，供 sv-models 发布用。

    python scripts/fetch_sv_models.py --out dist/sv-models
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main() -> None:
    from voicetwin.eval import sv_models

    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="dist/sv-models")
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    rows = []
    for m in [sv_models.VAD_MODEL] + [sv_models.MODELS[k] for k in sv_models.MODELS]:
        if not m.sha256:
            continue  # 我们自己导出的（ReDimNet2）由 export_redimnet2.py 生成
        url = next(u for u in m.sources if not u.startswith(sv_models.RELEASE_BASE)
                   and not any(u.startswith(g) for g in sv_models.GH_MIRRORS))
        dst = out / m.file
        print(f"下载 {url}")
        urllib.request.urlretrieve(url, dst)
        got = hashlib.sha256(dst.read_bytes()).hexdigest()
        if got != m.sha256 or dst.stat().st_size != m.size:
            raise SystemExit(f"{m.file} 核对不通过：{got}")
        rows.append({"file": m.file, "label": m.label, "size": m.size, "sha256": m.sha256, "origin": m.origin, "from": url})
    (out / "sv_models_sources.json").write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
    notes = ["声音分身 VoiceTwin「精准声纹打分」用的模型（v0.1.7 起）。**程序会自动下载这些文件，不需要手动下载。**", "",
             "| 文件 | 模型 | 出处 |", "|---|---|---|"]
    notes += [f"| {r['file']} | {r['label']} | {r['origin']} |" for r in rows]
    notes += ["| redimnet2_b6_vb2_vox2_cnc2_lm.onnx | ReDimNet2-B6 | ReDimNet2（Interspeech 2026，Palabra.ai，MIT 许可），"
              "由官方权重导出（scripts/export_redimnet2.py） |", "",
              "每个文件的 sha256 见 sv_models_sources.json / redimnet2_export.json；程序下载后会逐个核对。"]
    (out / "NOTES.md").write_text("\n".join(notes) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
