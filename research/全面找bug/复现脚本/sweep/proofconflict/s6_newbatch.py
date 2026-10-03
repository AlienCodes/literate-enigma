"""Batch 1 corrected with one-click + saved + confirmed; then the teacher adds batch 2 (开始准备素材 with a new video).
prepare re-runs 🔍 自动查找 over ALL rows (prepare.proofcheck = auto, on when a 2nd engine is installed; forced on here)."""
import re, shutil
from pathlib import Path
from common import *  # noqa
from voicetwin.webui import app as A
from voicetwin.data import proofcheck as pc

strip = lambda s: re.sub("<[^>]+>", "", str(s or ""))
cfg, p, ui = fresh("newbatch")
rs = p.load_manifest()
a = rs[1]["id"]
for r in rs:
    r.pop("suspect", None)
rs[1]["text"] = "我们先来看艾子引导的定语从句。"
p.save_manifest(rs)
list(ui.do_textfix(VOICE))
ui.do_save(VOICE)
md, _, _ = ui.do_confirm(VOICE)
row = [r for r in A._clips_table(cfg, VOICE) if r[1] == a][0]
print("batch 1 done: text", cur(p, a)["text"], "| 修改建议:", strip(row[6]), "| one-click button:", ui.textfix_btn(VOICE)["interactive"])


def second_engine(self, rec, lang):   # the 2nd recognizer hears the English word "as" as Chinese (what it does for 艾子)
    t = str(rec.get("text") or "")
    return t.replace("as", "a在"), None, "funasr"


pc._EngineRunner.recognize = second_engine
newdir = Path(cfg.get("workspace")).parent / "lectures2"
make_lecture(newdir / "第2课.wav", repeats=1, seed=7)
cfg_on = make_cfg(Path(cfg.get("workspace")), prepare={"asr": {"engine": "none"}, "proofcheck": "on"})
summary = wf.run_prepare(cfg_on, VOICE, [str(newdir)])
ui.after_prepare_clips(VOICE, False, None, {"voice": VOICE})
print("batch 2 added: clips now", len(p.load_manifest()), "| prepare's proofcheck:", (summary.get("proofcheck") or {}).get("flagged"), "flagged")
row = [r for r in A._clips_table(cfg, VOICE) if r[1] == a][0]
count = A._clips_count_md(cfg, VOICE)
print("old row a: 可能有错 cell:", strip(row[5]), "| has vt-red:", "vt-red" in row[5], "| 修改建议:", strip(row[6]))
m = re.search(r"\*\*(\d+)\*\* 条可能有错", count)
print("header:", m.group(0) if m else "-")
print("one-click button now:", ui.textfix_btn(VOICE)["interactive"], "| new ids:", len(tf.textfix_new_ids(p)), "| row a in new ids:", a in tf.textfix_new_ids(p))
outs = list(ui.do_textfix(VOICE))
row = [r for r in A._clips_table(cfg, VOICE) if r[1] == a][0]
print("after one-click for batch 2: old row a 修改建议:", strip(row[6]), "| red visible:", "vt-red" in row[5])
