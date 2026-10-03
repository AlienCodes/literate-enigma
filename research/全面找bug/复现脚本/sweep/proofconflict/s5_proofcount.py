"""一键校正 (unsaved) → 🔍 自动查找: the proofcheck result says N rows were marked red, the header / table show fewer."""
import re
from common import *  # noqa
from voicetwin.webui import app as A
from voicetwin.data import proofcheck as pc

strip = lambda s: re.sub("<[^>]+>", "", str(s or ""))
cfg, p, ui = fresh("proofcount")
rs = p.load_manifest()
a = rs[1]["id"]
for r in rs:
    r.pop("suspect", None)
rs[1]["text"] = "我们先来看艾子引导的定语从句。"
p.save_manifest(rs)
list(ui.do_textfix(VOICE))                      # 艾子 -> as, unsaved (🔴), 「已采用」 button
print("after one-click:", cur(p, a)["text"])


def second_engine(self, rec, lang):             # second recognizer disagrees only on this clip (on the saved text 艾子)
    t = str(rec.get("text") or "")
    return (t.replace("引导", "指导") if rec["id"] == a else t), None, "funasr"


pc._EngineRunner.recognize = second_engine
outs = list(ui.do_proofcheck(VOICE, False))
last = dict(zip(ui.PROOF_OUT, outs[-1]))
print("proofcheck result :", strip(last["proof_md"]).splitlines()[0])
m = re.search(r"\*\*(\d+)\*\* 条可能有错", last["clips_count"])
print("header right below:", m.group(0) if m else "(no 可能有错 line at all)")
count, rows = ui.refresh_clips(VOICE, True)
print("rows in 只看可能有错的:", [(r[0], strip(r[5]), strip(r[6])) for r in rows])
print("rows with red marks in full table:", sum("vt-red" in r[5] for r in A._clips_table(cfg, VOICE)))

print("stored for 'next one-click' (suspect_auto):", recs(p)[a].get("suspect_auto"))
print("one-click button interactive:", ui.textfix_btn(VOICE)["interactive"])
ui.do_save(VOICE)
row = [r for r in A._clips_table(cfg, VOICE) if r[1] == a][0]
print("after 保存修改: 可能有错 cell:", strip(row[5]), "| red?", "vt-red" in row[5], "| 修改建议:", strip(row[6]))
