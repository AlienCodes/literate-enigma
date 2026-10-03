import os, sys, json
os.chdir(sys.argv[1])
sys.path.insert(0, "/home/user/literate-enigma")
from voicetwin.config import load_config
from voicetwin.webui.app import WebUI
from voicetwin import workflows as wf
ui = WebUI(load_config())
v = "我的声音"
recs = wf.Project(ui.cfg, v).load_manifest()
cid = recs[4]["id"]
dele = next((r["id"] for r in recs if r.get("deleted")), recs[6]["id"])
payloads = ["[]", "{}", '"x"', "123", "null", "{bad", json.dumps({"action": "edit", "id": cid, "text": "   "}),
            json.dumps({"action": "edit", "id": cid, "text": None}), json.dumps({"action": "edit", "id": cid, "text": "a\nb"}),
            json.dumps({"action": "edit", "id": " " + cid + " ", "text": "新的文字"}),
            json.dumps({"action": "delete", "id": "nope"}), json.dumps({"action": "zzz", "id": cid}),
            json.dumps({"action": "edit", "id": dele, "text": "删了的行"}), json.dumps({"action": "use", "id": cid}),
            json.dumps({"action": "unadopt", "id": cid}), json.dumps({"action": "adopt", "id": cid}),
            json.dumps({"action": "ok", "id": cid}), json.dumps({"action": "save_row", "id": cid}),
            json.dumps({"action": "revert", "id": cid}), json.dumps({"action": "edit", "id": cid, "text": "x" * 20000}),
            json.dumps({"action": "edit", "id": cid, "text": 12345}), json.dumps({"action": ["edit"], "id": cid}),
            json.dumps({"action": "edit", "id": {"a": 1}, "text": "y"})]
from voicetwin.webui.app import _safe
f = _safe("校对表", 3, 0)(ui.do_clip_action)
for p in payloads:
    try:
        out = f(v, p)
        msg = out[0] if isinstance(out[0], str) else out[0]
        print(p[:60], "=>", str(msg)[:140].replace("\n", " "))
    except Exception as e:
        print(p[:60], "RAISED", type(e).__name__, e)
