"""Variant: a row with NO text at one-click time; teacher types the text afterwards. Button state after edit?"""
import sys, json, shutil
from pathlib import Path
sys.path.insert(0, "/home/user/literate-enigma"); sys.path.insert(0, "/home/user/literate-enigma/tests")
from conftest import make_cfg
from voicetwin import workflows as wf
from voicetwin.data import transcript_fix, review
from voicetwin.webui import app as A
SRC = Path(sys.argv[1]); WS = Path(sys.argv[2])
if WS.exists(): shutil.rmtree(WS)
shutil.copytree(SRC, WS)
V = "我的声音"
cfg = make_cfg(WS); p = wf.open_project(cfg, V, must_exist=True); ui = A.WebUI(cfg)
recs = p.load_manifest()
r = recs[12]
# simulate an ASR row without text (no_text) -- what v18.2+ warns about
for x in recs:
    if x["id"] == r["id"]:
        x["text"] = ""
p.save_manifest(recs)
list(ui.do_textfix(V))
print("after one-click: interactive =", ui.textfix_btn(V)["interactive"])
outs = ui.do_clip_action(V, json.dumps({"action": "edit", "id": r["id"], "no": "13", "text": "所以这个从句修饰的是整个主句。"}))
print("edit outputs:", len(outs), str(outs[0])[:60])
print("after typing text (reload): interactive =", A.WebUI(cfg).textfix_btn(V)["interactive"],
      "new ids =", transcript_fix.textfix_new_ids(p))
