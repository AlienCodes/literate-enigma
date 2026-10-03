"""Lost-update check: 「保存修改」 (do_save) and a table action that writes the manifest (delete / restore) run in two
different gradio concurrency groups, i.e. at the same time. apply_review() loads the manifest, works for seconds and
writes it back without a lock."""
import os, sys, json, threading, time, random
os.chdir(sys.argv[1])
sys.path.insert(0, "/home/user/literate-enigma")
from voicetwin.config import load_config
from voicetwin.webui.app import WebUI
from voicetwin import workflows as wf
from voicetwin.data import review as rv
ui = WebUI(load_config())
v = "我的声音"
p = wf.Project(ui.cfg, v)
recs = p.load_manifest()
ids = [r["id"] for r in recs if r.get("keep") and not r.get("deleted")]
losses = 0
for trial, delay in enumerate([0.0, 0.05, 0.1, 0.2, 0.4, 0.8, 1.2, 0.3, 0.6, 1.0]):
    X, Y = ids[2 * trial], ids[2 * trial + 1]
    new_text = f"老师改的第{trial}次文字。"
    rv.set_draft(p, Y, text=new_text)
    res = {}
    def a():
        res["del"] = ui.do_clip_action(v, json.dumps({"action": "delete", "id": X, "no": 1}))[0][:20]
    def b():
        time.sleep(delay)
        res["save"] = ui.do_save(v)[0][:20]
    ta, tb = threading.Thread(target=a), threading.Thread(target=b)
    t0 = time.time(); ta.start(); tb.start(); ta.join(); tb.join()
    m = {r["id"]: r for r in p.load_manifest()}
    d = rv.load_draft(p)
    ok_del = bool(m[X].get("deleted"))
    ok_txt = m[Y]["text"] == new_text or (Y in d and d[Y].get("text") == new_text)
    if not (ok_del and ok_txt):
        losses += 1
    print(f"delay {delay:.2f}s: delete kept={ok_del}  saved text kept={ok_txt}  ({time.time()-t0:.1f}s) {res}")
print("lost updates:", losses)
