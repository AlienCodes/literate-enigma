"""Lost-update check (both orders): 「保存修改」 (do_save) and 「⋯ 选项 → 删除这一行」 (do_clip_action delete) run at the
same time (different gradio concurrency groups). apply_review() loads the manifest, works for seconds, writes it back
without a lock -> whichever finishes last wins."""
import os, sys, json, threading, time, traceback
os.chdir(sys.argv[1])
ORDER = sys.argv[2]  # "del_first" or "save_first"
sys.path.insert(0, "/home/user/literate-enigma")
from voicetwin.config import load_config
from voicetwin.webui.app import WebUI
from voicetwin import workflows as wf
from voicetwin.data import review as rv
ui = WebUI(load_config())
v = "我的声音"
p = wf.Project(ui.cfg, v)
wf.apply_review(ui.cfg, v, read_csv=False)  # warm-up: clip stats for all rows computed once (like a real voice)
recs = p.load_manifest()
ids = [r["id"] for r in recs if r.get("keep") and not r.get("deleted")]
lost = 0
for trial, delay in enumerate([0.0, 0.05, 0.1, 0.2, 0.3, 0.5, 0.8, 1.0, 1.5, 2.0]):
    X, Y = ids[2 * trial], ids[2 * trial + 1]
    new_text = f"老师改的第{trial}次文字。"
    rv.set_draft(p, Y, text=new_text)
    res = {}
    def do_del():
        try:
            res["del"] = ui.do_clip_action(v, json.dumps({"action": "delete", "id": X, "no": 1}))[0][:14]; res["delmsg"] = ui._last if hasattr(ui, "_last") else ""
        except Exception as e:
            res["del"] = "RAISED " + repr(e)[:200]
    def do_sav():
        try:
            res["save"] = ui.do_save(v)[0][:14]
        except Exception as e:
            res["save"] = "RAISED " + repr(e)[:200]
    first, second = (do_del, do_sav) if ORDER == "del_first" else (do_sav, do_del)
    def later():
        time.sleep(delay); second()
    ta, tb = threading.Thread(target=first), threading.Thread(target=later)
    t0 = time.time(); ta.start(); tb.start(); ta.join(); tb.join()
    m = {r["id"]: r for r in p.load_manifest()}
    d = rv.load_draft(p)
    ok_del = bool(m[X].get("deleted"))
    ok_txt = m[Y]["text"] == new_text or (Y in d and d[Y].get("text") == new_text)
    lost += not (ok_del and ok_txt)
    print(f"{ORDER} delay {delay:.2f}s: deletion kept={ok_del}  saved text kept={ok_txt}  ({time.time()-t0:.1f}s) {res}", flush=True)
print("trials with a lost update:", lost)
