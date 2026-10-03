"""一键全部文字校正（每批只能用一次）以后，再点「🔍 自动查找可能的错字」：标准库给的建议还在吗？"""
from common import *

# 1) 和 test_partly_similar_same_id_row_is_only_an_unsure_suggestion 一样：上传的 csv 里同一个 id 有点像 → 没把握的建议
cfg, project = voice(["那么到底什么是定语从句呢", "这个主剧的结构也很完整", "我们今天天气很好"], ids=["x_0031", "x_0032", "x_0033"])
up = project.root.parent / "transcripts.csv"
up.write_text("id,text\nx_0031,我们今天来学习定语从句那么到底什么是定语从句呢\n", encoding="utf-8")
fake_engine({"x_0031": "那么到底什么是定语从句呢", "x_0032": "这个主剧的结构也很完整", "x_0033": "我们今天天气很好"})

res = wf.run_transcript_fix(cfg, "v", files=[str(up)], once=True)
print("one-click:", {k: res.get(k) for k in ("fixes", "found", "flagged")}, res["adopted"])
for rid in ("x_0031", "x_0032"):
    show(project, rid, "after one-click")
print("textfix_used (button grey):", tf.textfix_used(project))

res2 = pc.find_suspects(project, cfg)
print("auto check:", {k: res2[k] for k in ("checked", "flagged")}, res2["note"])
for rid in ("x_0031", "x_0032"):
    show(project, rid, "after auto check")
print("textfix_used (button grey):", tf.textfix_used(project))
try:
    wf.run_transcript_fix(cfg, "v", once=True)
except ValueError as e:
    print("one-click again ->", str(e)[:60])
