"""R4: the first recognizer found no text (row says 没有识别出文字); the teacher types the whole sentence and saves.
🔍 自动查找: the 2nd engine hears an extra word at the very start. Whole sentence is blue (typed by her)."""
import re, shutil
from base import *  # noqa
from voicetwin.webui import app as A
from voicetwin.data import proofcheck as pc

cfg, p, ui = fresh("r4")
rs = p.load_manifest()
a = rs[2]["id"]
for r in rs:
    r.pop("suspect", None)
rs[2]["text"] = ""
rs[2]["orig_text"] = ""
rs[2]["asr_done"] = True
p.save_manifest(rs)
act(ui, "edit", a, text="首先我们看一个宾语从句的例子。")
ui.do_save(VOICE)
r = recs(p)[a]
print("saved:", r["text"], "| orig_text:", repr(r.get("orig_text")), "| keep:", r.get("keep"))
pc._EngineRunner.recognize = lambda self, rec, lang: ("那" + str(rec.get("text") or ""), None, "funasr")
outs = list(ui.do_proofcheck(VOICE, False))
last = dict(zip(ui.PROOF_OUT, outs[-1]))
print("proofcheck md:", strip(last["proof_md"]).splitlines()[0])
r = recs(p)[a]
print("stored suspect:", r.get("suspect"))
row = [x for x in A._clips_table(cfg, VOICE) if x[1] == a][0]
m = re.search(r"\*\*(\d+)\*\* 条可能有错", A._clips_count_md(cfg, VOICE))
print("vt-red in cell:", "vt-red" in row[5], "| 修改建议:", strip(row[6]), "| header:", m.group(0) if m else "-")
shutil.rmtree(Path(cfg.get("workspace")).parent, ignore_errors=True)
