"""一键校正改好 → 保存 → 🔍 自动查找 flags the corrected word: red mark is drawn under the blue one (invisible),
row still counts as 可能有错, and 「这句没错」 is not offered (the menu looks for .vt-red)."""
import re
from common import *  # noqa
from voicetwin.webui import app as A
from voicetwin.data import proofcheck as pc

strip = lambda s: re.sub("<[^>]+>", "", str(s or ""))
cfg, p, ui = fresh("redhidden")
rs = p.load_manifest()
a = rs[1]["id"]
for r in rs:
    r.pop("suspect", None)
rs[1]["text"] = "我们先来看艾子引导的定语从句。"
p.save_manifest(rs)
list(ui.do_textfix(VOICE))                      # 📝 一键全部文字校正: 艾子 -> as (draft)
ui.do_save(VOICE)                               # 保存修改
print("saved text:", recs(p)[a]["text"], "| orig_text:", recs(p)[a].get("orig_text"))


def second_engine(self, rec, lang):             # the second recognizer hears the English word differently
    t = str(rec.get("text") or "")
    return t.replace("as", "a在"), None, "funasr"


pc._EngineRunner.recognize = second_engine
outs = list(ui.do_proofcheck(VOICE, False))    # 🔍 自动查找可能的错字
last = dict(zip(ui.PROOF_OUT, outs[-1]))
print("proofcheck:", strip(last["proof_md"]).splitlines()[0])
print("suspect stored:", recs(p)[a].get("suspect"))
count, rows = ui.refresh_clips(VOICE, True)    # 只看可能有错的
m = re.search(r"\*\*(\d+)\*\* 条可能有错", count)
print("header:", m.group(0) if m else "-")
row = [r for r in rows if r[1] == a][0]
col = row[5]
print("可能有错 cell has vt-red:", "vt-red" in col, "| has vt-blue:", "vt-blue" in col)
print("可能有错 cell text:", strip(col))
print("修改建议 cell:", strip(row[6]))
print("=> menu offers 「这句没错」 only when the cell contains .vt-red (REVIEW_JS line ~532/571):", "vt-red" in col)
