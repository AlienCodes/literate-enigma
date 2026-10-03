"""「保存修改」 then 「✅ 确认训练素材」 shortly after: separate gradio concurrency groups -> two apply_review() at once."""
import os, sys, json, threading, time
os.chdir(sys.argv[1])
sys.path.insert(0, "/home/user/literate-enigma")
from voicetwin.config import load_config
from voicetwin.webui.app import WebUI
from voicetwin import workflows as wf
from voicetwin.data import review as rv
ui = WebUI(load_config())
v = "我的声音"
p = wf.Project(ui.cfg, v)
wf.apply_review(ui.cfg, v, read_csv=False)
ids = [r["id"] for r in p.load_manifest() if r.get("keep") and not r.get("deleted")]
bad = 0
for trial, delay in enumerate([0.0, 0.1, 0.2, 0.3, 0.5, 0.7, 1.0, 1.5, 0.05, 0.4, 0.6, 0.8]):
    rv.set_draft(p, ids[trial], text=f"老师改的第{trial}次。")
    res = {}
    from voicetwin.webui.app import _safe
    S, Cf = _safe("保存修改", 3, 0)(ui.do_save), _safe("确认训练素材", 3, 0)(ui.do_confirm)  # exactly as build() wires them
    def s():
        res["save"] = S(v)[0].replace("\n", " ")[:90]
    def c():
        time.sleep(delay); res["confirm"] = Cf(v)[0].replace("\n", " ")[:90]
    a, b = threading.Thread(target=s), threading.Thread(target=c)
    a.start(); b.start(); a.join(); b.join()
    err = any("没有完成" in x for x in res.values())
    bad += err
    print(f"delay {delay:.2f}: {'ERROR SHOWN' if err else 'ok'} {res}", flush=True)
print("trials with an error shown to the teacher:", bad)
