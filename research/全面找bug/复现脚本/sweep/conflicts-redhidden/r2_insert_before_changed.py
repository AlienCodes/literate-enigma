"""R1: first recognizer wrote 主语; teacher double-clicks, fixes to 宾语, saves; then 🔍 自动查找 with a second
engine that also hears 主语. Check stored suspect, analyze(), the 可能有错 cell, counts, and menu condition."""
import re
from base import *  # noqa
from voicetwin.webui import app as A
from voicetwin.data import proofcheck as pc

cfg, p, ui = fresh("r2")
rs = p.load_manifest()
print("rows:", len(rs), [r.get("text") for r in rs][:6])
a = rs[2]["id"]
for r in rs:
    r.pop("suspect", None)
    r.pop("orig_text", None)
rs[2]["text"] = "首先我们看一个主语从句的例子。"   # what the first recognizer wrote (orig)
p.save_manifest(rs)
act(ui, "edit", a, text="首先我们看一个宾语从句的例子。")
ui.do_save(VOICE)
r = recs(p)[a]
print("after save: text=", r["text"], "| orig_text=", r.get("orig_text"), "| suspect=", r.get("suspect"))


calls = []


def second_engine(self, rec, lang):
    t = str(rec.get("text") or "")
    calls.append(rec["id"])
    return t.replace("一个宾语", "一个双宾语"), None, "funasr"


pc._EngineRunner.recognize = second_engine
outs = list(ui.do_proofcheck(VOICE, False))
last = dict(zip(ui.PROOF_OUT, outs[-1]))
print("engine calls:", len(calls))
print("proofcheck md:", strip(last["proof_md"]).splitlines()[0])
r = recs(p)[a]
print("stored suspect:", r.get("suspect"))
info = review.analyze(r)
print("analyze: red=", info["red"], "blue=", info["blue"], "edits=", info["edits"], "active=", info["active"])
row = [x for x in A._clips_table(cfg, VOICE) if x[1] == a][0]
print("可能有错 cell html:", row[5])
print("vt-red in cell:", "vt-red" in row[5], "| 修改建议:", strip(row[6]))
m = re.search(r"\*\*(\d+)\*\* 条可能有错", A._clips_count_md(cfg, VOICE))
print("header:", m.group(0) if m else "-")
count, rows = ui.refresh_clips(VOICE, True)
print("rows in 只看可能有错的:", [x[1] for x in rows], "| a included:", a in [x[1] for x in rows])
print("analyze reasons:", info["reasons"], "| undo:", info["undo"])
# what the ⋯ menu would offer: REVIEW_JS shows 「👍 这句没错」 only when the 可能有错 cell has .vt-red
print("menu offers 这句没错:", "vt-red" in row[5])
