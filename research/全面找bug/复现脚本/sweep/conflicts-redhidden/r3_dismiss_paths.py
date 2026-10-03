"""R3: continue R2 (row active with only an insertion suggestion, no red). Can the teacher get rid of it?
(a) 采用 then 已采用 (undo)  (b) the server-side 'ok' action (what 这句没错 would send if the menu offered it)."""
import re, shutil
from base import *  # noqa
from voicetwin.webui import app as A
from voicetwin.data import proofcheck as pc


def setup(name):
    cfg, p, ui = fresh(name)
    rs = p.load_manifest()
    a = rs[2]["id"]
    for r in rs:
        r.pop("suspect", None)
        r.pop("orig_text", None)
    rs[2]["text"] = "首先我们看一个主语从句的例子。"
    p.save_manifest(rs)
    act(ui, "edit", a, text="首先我们看一个宾语从句的例子。")
    ui.do_save(VOICE)
    pc._EngineRunner.recognize = lambda self, rec, lang: (str(rec.get("text") or "").replace("一个宾语", "一个双宾语"), None, "funasr")
    list(ui.do_proofcheck(VOICE, False))
    return cfg, p, ui, a


def state(cfg, p, a, tag):
    row = [x for x in A._clips_table(cfg, VOICE) if x[1] == a][0]
    m = re.search(r"\*\*(\d+)\*\* 条可能有错", A._clips_count_md(cfg, VOICE))
    vals = review.current_values(recs(p)[a], review.load_draft(p).get(a))
    print(f"[{tag}] text={vals['text']} | red in cell={'vt-red' in row[5]} | 修改建议={strip(row[6])!r} | header={m.group(0) if m else '-'}")


cfg, p, ui, a = setup("r3a")
state(cfg, p, a, "after proofcheck")
act(ui, "adopt", a)
state(cfg, p, a, "after 采用")
act(ui, "unadopt", a)
state(cfg, p, a, "after 已采用 (undo)")
ui.do_save(VOICE)
state(cfg, p, a, "after save")
shutil.rmtree(Path(cfg.get("workspace")).parent, ignore_errors=True)

cfg, p, ui, a = setup("r3b")
act(ui, "ok", a)
state(cfg, p, a, "after server-side ok")
shutil.rmtree(Path(cfg.get("workspace")).parent, ignore_errors=True)
