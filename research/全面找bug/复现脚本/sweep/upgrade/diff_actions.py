"""Differential test: same old workspace, same row action (adopt / unadopt / ok / revert / save_row), old code vs new code.

usage: python diff_actions.py <src_dir (old version or repo)> <workspace copy> <out json>
For every row: copy is reset by the caller; here we run each action on a fresh in-memory copy of the files.
"""
import json
import shutil
import sys
import tempfile
from pathlib import Path

SRC, WS, OUT = sys.argv[1], Path(sys.argv[2]), Path(sys.argv[3])
sys.path.insert(0, SRC)
sys.path.insert(0, SRC + "/tests")
import voicetwin  # noqa: E402

from conftest import make_cfg  # noqa: E402
from voicetwin import workflows as wf  # noqa: E402
from voicetwin.data import review  # noqa: E402

V = "我的声音"
res = {"version": voicetwin.__version__}
base_cfg = make_cfg(WS)
ids = [r["id"] for r in wf.open_project(base_cfg, V, must_exist=True).load_manifest()]
for i, rid in enumerate(ids):
    for action in ("adopt", "unadopt"):
        tmp = Path(tempfile.mkdtemp(dir=str(WS.parent)))
        shutil.copytree(WS / V, tmp / V)
        cfg = make_cfg(tmp)
        p = wf.open_project(cfg, V, must_exist=True)
        try:
            fn = review.adopt_suggestion if action == "adopt" else review.unadopt_suggestion
            fn(p, rid)
            rec = {r["id"]: r for r in p.load_manifest()}[rid]
            out = review.current_values(rec, review.load_draft(p).get(rid))["text"]
        except Exception as exc:  # noqa: BLE001
            out = f"ERR {type(exc).__name__}: {str(exc)[:80]}"
        res[f"{i}:{action}"] = out
        shutil.rmtree(tmp)
OUT.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
print("done", voicetwin.__version__)
