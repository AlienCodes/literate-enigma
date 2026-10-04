# 复查（第四轮 g2 的检查意见）用的复现脚本，原样保留；不给参数就用这个仓库：/tmp/gsv39/bin/python 复查_p5_after_use.py
# Upload a correct per-sentence script, run the one-click; then look at the info line under the button
import sys, tempfile, shutil, re
from pathlib import Path
ROOT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[4]; sys.path[:0] = [str(ROOT), str(ROOT / "tests")]
from conftest import make_cfg
from voicetwin import workflows as wf
from voicetwin.data import transcript_fix as tf, review
from voicetwin.webui import app as A
d = Path(tempfile.mkdtemp())
try:
    cfg = make_cfg(d / "ws")
    project = wf.Project(cfg, "v").ensure()
    rows = ["我们先来复习一下关系代词威驰的用法，它可以指物。", "我们先来看艾子引导的定语从句，它比较特殊。"]
    project.save_manifest([{"id": f"c{i}", "path": f"clips/c{i}.wav", "text": t, "lang": "zh", "duration": 3.0,
                            "keep": True, "split": "train"} for i, t in enumerate(rows)])
    up = d / "这节课的讲稿.txt"
    up.write_text("我们先来复习一下关系代词which的用法，它可以指物。\n我们先来看as引导的定语从句，它比较特殊。\n", encoding="utf-8")
    ui = A.WebUI(cfg)
    print("INFO before:", ui.textfix_info("v").split("另外")[-1])
    out = dict(zip(ui.TEXTFIX_OUT, list(ui.do_textfix("v", [str(up)]))[-1]))
    md = out["proof_md"]
    print("RESULT:", [l for l in str(md).splitlines() if "上传" in l or "例如" in l])
    dr = review.load_draft(project)
    print("rows now:", [review.current_values(r, dr.get(r["id"]))["text"] for r in project.load_manifest()])
    print("INFO after:", ui.textfix_info("v").split("另外")[-1])
    print("TRINFO same screen:", "用不上" in str(out.get("tr_info")), "| result says used:", "另外用了你上传的" in str(md))
finally:
    shutil.rmtree(d, ignore_errors=True)
