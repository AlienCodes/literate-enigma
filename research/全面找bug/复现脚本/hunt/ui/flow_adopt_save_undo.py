import os, sys, json, re
os.chdir(sys.argv[1])
sys.path.insert(0, "/home/user/literate-enigma")
from voicetwin.config import load_config
from voicetwin.webui.app import WebUI, _safe, CLIP_HEADERS
ui = WebUI(load_config())
v = "我的声音"
f = _safe("校对表", 3, 0)(ui.do_clip_action)
cid = "0006_9498bb_0001"
def row(table):
    r = next(r for r in table if r[1] == cid)
    return r
def sug(table):
    s = row(table)[6]
    return "red" if "vt-sug-red" in s else ("blue" if "vt-sug-blue" in s else "none")
out = f(v, json.dumps({"action": "adopt", "id": cid, "no": 2})); print("adopt:", out[0][:60], "| button:", sug(out[2]))
out = ui.do_save(v); print("save:", out[0][:40], "| button:", sug(out[2]))
out = f(v, json.dumps({"action": "unadopt", "id": cid, "no": 2})); print("unadopt after save:", out[0][:100].replace("\n", " "), "| button:", sug(out[2]) if not isinstance(out[2], dict) else out[2])
out = ui.do_save(v); print("save:", out[0][:40], "| button:", sug(out[2]))
out = f(v, json.dumps({"action": "adopt", "id": cid, "no": 2})); print("re-adopt:", out[0][:100].replace("\n", " "), "| button:", sug(out[2]) if not isinstance(out[2], dict) else out[2])
out = ui.do_confirm(v); print("confirm:", out[0][:40], "| button:", sug(out[2]))
out = f(v, json.dumps({"action": "unadopt", "id": cid, "no": 2})); print("unadopt after confirm:", out[0][:100].replace("\n", " "))
