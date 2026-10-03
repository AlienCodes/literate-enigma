"""Teacher corrects a word herself (listening to the audio) and saves; 🔍 自动查找 (2nd engine misheard the same way)
flags exactly that word: red drawn under blue (invisible), 「这句没错」 not offered, row counted as 可能有错 for good."""
import re
from common import *  # noqa
from voicetwin.webui import app as A
from voicetwin.data import proofcheck as pc

strip = lambda s: re.sub("<[^>]+>", "", str(s or ""))
cfg, p, ui = fresh("redhidden2")
rs = p.load_manifest()
a = rs[2]["id"]
for r in rs:
    r.pop("suspect", None)
rs[2]["text"] = "首先我们看一个主语从句的例子。"   # what the 1st recognizer wrote; she actually said 宾语
p.save_manifest(rs)
act(ui, "edit", a, text="首先我们看一个宾语从句的例子。")  # double-click, fix it
ui.do_save(VOICE)


def second_engine(self, rec, lang):
    t = str(rec.get("text") or "")
    return t.replace("宾语", "主语"), None, "funasr"


pc._EngineRunner.recognize = second_engine
outs = list(ui.do_proofcheck(VOICE, False))
last = dict(zip(ui.PROOF_OUT, outs[-1]))
print("proofcheck:", strip(last["proof_md"]).splitlines()[0])
row = [r for r in A._clips_table(cfg, VOICE) if r[1] == a][0]
print("可能有错 cell (html):", row[5][:400])
print("vt-red present:", "vt-red" in row[5], "| 修改建议:", strip(row[6]))
m = re.search(r"\*\*(\d+)\*\* 条可能有错", A._clips_count_md(cfg, VOICE))
print("header:", m.group(0) if m else "-")
