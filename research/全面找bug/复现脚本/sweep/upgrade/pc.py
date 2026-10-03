import sys, json
sys.path.insert(0, "/home/user/literate-enigma"); sys.path.insert(0, "/home/user/literate-enigma/tests")
from pathlib import Path
from conftest import make_cfg
from voicetwin import workflows as wf
from voicetwin.data import review
from voicetwin.webui import app as A
WS = Path(sys.argv[1]); V = "我的声音"
cfg = make_cfg(WS); project = wf.open_project(cfg, V, must_exist=True)
ui = A.WebUI(cfg)
def snap():
    d = review.load_draft(project)
    return {r["id"]: (review.current_values(r, d.get(r["id"]))["text"], review.analyze(r, review.current_values(r, d.get(r["id"]))["text"])["adopted"], bool(r.get("suspect"))) for r in project.load_manifest()}
b = snap()
outs = list(ui.do_proofcheck(V))
last = dict(zip(ui.PROOF_OUT, outs[-1]))
print("proofcheck:", str(last["proof_md"])[:400].replace("\n"," | "))
a = snap()
for k in b:
    if b[k] != a[k]:
        print(k, b[k], "->", a[k])
