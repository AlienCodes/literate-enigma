"""Repro: after the one-time use, a new 母本 uploaded in 「📄 上传更多母本」 is never used or even saved:
the only trigger is the (now grey) 「📝 一键全部文字校正」 button; the release notes still advertise the upload."""
import sys, os
HEAD = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("VT_ROOT", "/home/user/literate-enigma")
sys.path.insert(0, HEAD + "/research/文字校正/随机操作")
import h
from voicetwin import workflows as wf
from voicetwin.webui import app as A
from voicetwin.data import transcript_fix as tf
cfg, project = h.voice(["这个借词后面要接宾语。", "我们今天讲同位于从句。"], name="v")
ui = A.WebUI(cfg)
list(ui.do_textfix("v", None))
print("used:", wf.textfix_used(cfg, "v"), "| button interactive:", ui.textfix_btn("v").get("interactive"))
p = os.path.join(os.environ["TMPDIR"], "新讲稿.txt")
open(p, "w", encoding="utf-8").write("我们今天讲同位语从句。\n")
outs = list(ui.do_textfix("v", [p]))
print("uploaded files known to the voice:", wf.transcript_info(cfg, "v").get("files"))
print("row c001 now:", h.cur(project, "c001")[1])
