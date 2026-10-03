import os, sys, time, json
os.chdir(sys.argv[1])
sys.path.insert(0, "/home/user/literate-enigma")
from voicetwin.config import load_config
from voicetwin.webui.app import WebUI, _clips_table
ui = WebUI(load_config())
v = "我的声音"
t = time.time(); tab = _clips_table(ui.cfg, v); print("clips_table", len(tab), round(time.time() - t, 3))
from voicetwin import workflows as wf
recs = wf.Project(ui.cfg, v).load_manifest()
cid = recs[5]["id"]
t = time.time(); out = ui.do_clip_action(v, json.dumps({"action": "lang", "id": cid, "no": 6})); print("lang", round(time.time() - t, 3), out[0][:40])
t = time.time(); out = ui.do_clip_action(v, json.dumps({"action": "lang", "id": cid, "no": 6})); print("lang back", round(time.time() - t, 3))
t = time.time(); out = ui.do_clip_action(v, json.dumps({"action": "delete", "id": cid, "no": 6})); print("delete", round(time.time() - t, 3), out[0][:30])
t = time.time(); out = ui.do_clip_action(v, json.dumps({"action": "restore", "id": cid, "no": 6})); print("restore", round(time.time() - t, 3), out[0][:30])
