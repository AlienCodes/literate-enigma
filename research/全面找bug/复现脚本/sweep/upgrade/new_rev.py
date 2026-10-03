import sys
sys.path.insert(0, "/home/user/literate-enigma"); sys.path.insert(0, "/home/user/literate-enigma/tests")
from pathlib import Path
from conftest import make_cfg
from voicetwin import workflows as wf
from voicetwin.data import review
WS = Path(sys.argv[1]); V="我的声音"
cfg = make_cfg(WS); p = wf.open_project(cfg, V, must_exist=True)
rid = p.load_manifest()[7]["id"]
wf.run_transcript_fix(cfg, V, once=True)
r = {x["id"]: x for x in p.load_manifest()}[rid]
print("after one-click:", review.current_values(r, review.load_draft(p).get(rid))["text"])
