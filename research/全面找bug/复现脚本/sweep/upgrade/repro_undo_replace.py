"""v18.4: teacher did 全部替换 借词→介词, saved, confirmed.  After upgrading she runs the one-click, then presses
「↩️ 撤销刚才的替换」 (thinking it undoes what just happened): it silently reverts the days-old replacement."""
import sys, json
sys.path.insert(0, "/home/user/literate-enigma"); sys.path.insert(0, "/home/user/literate-enigma/tests")
from pathlib import Path
from conftest import make_cfg
from voicetwin import workflows as wf
from voicetwin.data import review
from voicetwin.webui import app as A
cfg = make_cfg(Path(sys.argv[1])); V = "我的声音"; p = wf.open_project(cfg, V, must_exist=True); ui = A.WebUI(cfg)
print("undo record left by v18.4:", json.loads((p.root / review.UNDO_FILE).read_text(encoding="utf-8")))
print("blocker before:", wf.training_blocker(p) or "(none: confirmed in v18.4)")
ui.on_voice_change(V)
list(ui.do_textfix(V))
status = ui.do_undo_replace(V)[0]
print("undo status:", status[:200])
rid = p.load_manifest()[6]["id"]
r = {x["id"]: x for x in p.load_manifest()}[rid]
print("row 7 now:", review.current_values(r, review.load_draft(p).get(rid))["text"])
