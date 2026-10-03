"""(a)/(d): one-click suggestion rows, adopted rows, untouched rows -> 🔍 auto check (web path wf.run_proofcheck)."""
from common import *
install_fake()
texts = ["那么到底什么是定语从句呢", "这个主剧的结构也很完整", "我们今天天气很好", "下面我们来看第二个例子"]
ids = ["x_0031", "x_0032", "x_0033", "x_0034"]
cfg, project = voice(texts, ids=ids)
up = project.root.parent / "transcripts.csv"
up.write_text("id,text\nx_0031,我们今天来学习定语从句那么到底什么是定语从句呢\n", encoding="utf-8")
ANS.update(dict(zip(ids, texts)))
res = wf.run_transcript_fix(cfg, "v", files=[str(up)], once=True)
s1 = {i: state(project, i) for i in ids}
for i in ids: print("after one-click", i, s1[i])
# second engine now hears new differences: x_0033 (row one-click found nothing) and x_0032 (row one-click fixed)
ANS["x_0033"] = "我们今天天气很少"; ANS["x_0032"] = "这个主剧的结构也很完成"
r = wf.run_proofcheck(cfg, "v")
print("auto check flagged", r["flagged"])
s2 = {i: state(project, i) for i in ids}
for i in ids: print("after 🔍", i, s2[i])
ok = (s2["x_0031"]["edits"] == s1["x_0031"]["edits"] and s2["x_0032"]["undo"] == s1["x_0032"]["undo"]
      and "少" in str(s2["x_0033"]["edits"]) and ("成" in str(s2["x_0032"]["edits"])))
print("suggestion kept / undo kept / new findings visible:", ok)
shown = sum(1 for i in ids if s2[i]["active"])
print("flagged count", r["flagged"], "== rows active in table", shown, r["flagged"] == shown)
# teacher adopts the unsure one-click suggestion, saves, re-runs 🔍
print("adopt x_0031:", review.adopt_suggestion(project, "x_0031").get("ok", "?"))
review.save_rows(project)
wf.run_proofcheck(cfg, "v")
print("after adopt+save+🔍 x_0031", state(project, "x_0031"))
print("one-click again possible?", not tf.textfix_used(project))
