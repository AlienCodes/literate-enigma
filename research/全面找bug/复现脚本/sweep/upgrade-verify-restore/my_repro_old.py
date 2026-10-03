"""Verify: row deleted in v18.4 -> upgrade -> one-click -> restore row. Does textfix button become enabled?"""
import sys, json, shutil
from pathlib import Path
sys.path.insert(0, "/tmp/claude-0/-home-user-literate-enigma/a7bf493d-04b5-5828-bb09-9d8cecef37ad/scratchpad/sweep/upgrade-verify-restore/old"); sys.path.insert(0, "/tmp/claude-0/-home-user-literate-enigma/a7bf493d-04b5-5828-bb09-9d8cecef37ad/scratchpad/sweep/upgrade-verify-restore/old/tests")
import voicetwin
assert voicetwin.__file__.startswith("/tmp/claude-0/-home-user-literate-enigma/a7bf493d-04b5-5828-bb09-9d8cecef37ad/scratchpad/sweep/upgrade-verify-restore/old/"), voicetwin.__file__
print("current version", voicetwin.__version__)
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
dele = [r for r in recs if r.get("deleted")]
print("deleted rows:", [(recs.index(r) + 1, r["id"], repr(r.get("text"))[:40], r.get("keep")) for r in dele])
d = dele[0]
print("before one-click: button interactive =", ui.textfix_btn(V)["interactive"], " new ids =", len(transcript_fix.textfix_new_ids(p)))
print("batch ids: (n/a in old code)")
outs = list(ui.do_textfix(V))
last = dict(zip(ui.TEXTFIX_OUT, outs[-1]))
print("one-click final md:", str(last.get("proof_md"))[:120].replace("\n", " "))
print("after one-click: button interactive =", ui.textfix_btn(V)["interactive"])
used = json.loads((p.root / "textfix_used.json").read_text(encoding="utf-8"))
print("used.json contains deleted id?", d["id"] in used["ids"], " n ids =", len(used["ids"]))
no = recs.index(d) + 1
outs = ui.do_clip_action(V, json.dumps({"action": "restore", "id": d["id"], "no": str(no)}))
print("restore msg:", str(outs[0])[:100].replace("\n", " "), "| n outputs =", len(outs))
p2 = wf.open_project(cfg, V, must_exist=True)
print("row deleted now?", [r for r in p2.load_manifest() if r["id"] == d["id"]][0].get("deleted"))
print("after restore (fresh reload): button interactive =", A.WebUI(cfg).textfix_btn(V)["interactive"],
      " new ids =", transcript_fix.textfix_new_ids(p2))
print("info text locked?", "🔒" in A.WebUI(cfg).textfix_info(V))
outs = list(A.WebUI(cfg).do_textfix(V))
print("click again:", str(dict(zip(ui.TEXTFIX_OUT, outs[-1])).get("proof_md"))[:160].replace("\n", " "))
print("bar:", str(dict(zip(ui.TEXTFIX_OUT, outs[-1])).get("proof_bar"))[:200].replace("\n", " "))
