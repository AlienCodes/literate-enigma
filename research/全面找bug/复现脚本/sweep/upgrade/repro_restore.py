"""A row deleted in the old version, restored after the one-click: the button state flips (only after a page reload)."""
import sys, json
sys.path.insert(0, "/home/user/literate-enigma"); sys.path.insert(0, "/home/user/literate-enigma/tests")
from pathlib import Path
from conftest import make_cfg
from voicetwin import workflows as wf
from voicetwin.webui import app as A
WS = Path(sys.argv[1]); V = "我的声音"
cfg = make_cfg(WS); p = wf.open_project(cfg, V, must_exist=True); ui = A.WebUI(cfg)
dele = [r for r in p.load_manifest() if r.get("deleted")][0]
list(ui.do_textfix(V))
print("after one-click button:", ui.textfix_btn(V)["interactive"])
outs = ui.do_clip_action(V, json.dumps({"action": "restore", "id": dele["id"], "no": "5"}))
print("restore outputs:", len(outs), "(clip_msg, clips_count, clips -- no button refresh)")
print("button on reload:", ui.textfix_btn(V)["interactive"])
outs = list(ui.do_textfix(V))
print(str(dict(zip(ui.TEXTFIX_OUT, outs[-1]))["proof_md"]).split("\n")[0])
