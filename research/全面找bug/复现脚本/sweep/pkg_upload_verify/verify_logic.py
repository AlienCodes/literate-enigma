"""Verify: after the one-time use of 「📝 一键全部文字校正」, what happens to 「📄 上传更多母本」.
Usage: python verify_logic.py <repo_root>"""
import os
import sys
import tempfile

ROOT = sys.argv[1]
sys.path.insert(0, ROOT + "/research/文字校正/随机操作")
import h  # noqa: E402  (inserts ROOT and ROOT/tests on sys.path)

import voicetwin  # noqa: E402
from voicetwin import workflows as wf  # noqa: E402
from voicetwin.webui import app as A  # noqa: E402

print("voicetwin from:", voicetwin.__file__)
cfg, project = h.voice(["这个借词后面要接宾语。", "我们今天讲同位于从句。"], name="v")
ui = A.WebUI(cfg)

print("--- before first use")
print("used:", wf.textfix_used(cfg, "v"), "btn interactive:", ui.textfix_btn("v").get("interactive"),
      "| has textfix_files:", hasattr(ui, "textfix_files"),
      "| files interactive:", ui.textfix_files("v").get("interactive") if hasattr(ui, "textfix_files") else "n/a")

list(ui.do_textfix("v", None))
print("--- after first use")
print("used:", wf.textfix_used(cfg, "v"), "btn interactive:", ui.textfix_btn("v").get("interactive"),
      "| files interactive:", ui.textfix_files("v").get("interactive") if hasattr(ui, "textfix_files") else "n/a")
info = ui.textfix_info("v")
print("info mentions upload box grey:", "上传框" in info)
print("info:", info[:260].replace("\n", " "))

# stale page / box still active: upload a file and click (button is grey in a fresh page; simulate a stale one)
tmp = tempfile.mkdtemp()
p = os.path.join(tmp, "新讲稿.txt")
open(p, "w", encoding="utf-8").write("我们今天讲同位语从句。\n")
outs = list(ui.do_textfix("v", [p]))
last = outs[-1]
O = ui.TEXTFIX_OUT
bar = last[O.index("proof_bar")] if isinstance(last, (list, tuple)) else last
print("--- click with upload while locked (stale page)")
print("message shown:", str(bar)[:200].replace("\n", " "))
print("files known:", wf.transcript_info(cfg, "v").get("files"), "| row c001:", h.cur(project, "c001")[1])

# new material arrives: button and box should light up again, and the upload gets used
recs = project.load_manifest()
recs.append({"id": "c002", "path": "clips/c002.wav", "text": "这是定语从剧的例子。", "lang": "zh",
             "duration": 3.0, "keep": True, "split": "train"})
project.save_manifest(recs)
print("--- after adding new material")
print("used:", wf.textfix_used(cfg, "v"), "btn interactive:", ui.textfix_btn("v").get("interactive"),
      "| files interactive:", ui.textfix_files("v").get("interactive") if hasattr(ui, "textfix_files") else "n/a")
p2 = os.path.join(tmp, "第二批讲稿.txt")
open(p2, "w", encoding="utf-8").write("这是定语从句的例子。我们今天讲同位语从句和定语从句的区别。\n")
list(ui.do_textfix("v", [p2]))
print("files known:", wf.transcript_info(cfg, "v").get("files"))
print("row c002:", h.cur(project, "c002")[1], "| row c001 untouched:", h.cur(project, "c001")[1])
print("used again:", wf.textfix_used(cfg, "v"), "files interactive:",
      ui.textfix_files("v").get("interactive") if hasattr(ui, "textfix_files") else "n/a")
print("--- second batch: print outputs of do_textfix")
p3 = os.path.join(tmp, "第三批讲稿.txt")
open(p3, "w", encoding="utf-8").write("这是定语从句的例子。我们今天讲同位语从句和定语从句的区别。\n")
for o in ui.do_textfix("v", [p3]):
    print("OUT:", [str(x)[:160].replace("\n", " ") for x in o] if isinstance(o, (list, tuple)) else str(o)[:300])
print("files known:", wf.transcript_info(cfg, "v"))
print("row c002:", h.cur(project, "c002")[1])
