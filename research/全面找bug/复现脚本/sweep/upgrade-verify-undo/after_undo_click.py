"""Fresh v18.4 workspace: press 撤销刚才的替换 first, THEN the one-click: does the one-click repair 借词 itself?"""
import sys
sys.path.insert(0, "/home/user/literate-enigma"); sys.path.insert(0, "/home/user/literate-enigma/tests")
from pathlib import Path
from conftest import make_cfg
from voicetwin import workflows as wf
from voicetwin.data import review
from voicetwin.webui import app as A
cfg = make_cfg(Path(sys.argv[1])); V = "我的声音"; p = wf.open_project(cfg, V, must_exist=True); ui = A.WebUI(cfg)
ui.on_voice_change(V); ui.do_undo_replace(V)
r = p.load_manifest()[6]
print("after undo:", review.current_values(r, review.load_draft(p).get(r["id"]))["text"])
list(ui.do_textfix(V))
r = p.load_manifest()[6]; d = review.load_draft(p).get(r["id"])
print("after one-click:", review.current_values(r, d)["text"])
print("suggestion/red:", review.analyze(r, review.current_values(r, d)["text"]).get("red"), "| suspect:", r.get("suspect"))
