"""「查完了：检查了 N 条，其中 M 条可能有错（已标红）」的 M 和表格里真的标红的行数对得上吗？"""
from common import *
import importlib

texts = ["我们今天讲十个函数", "这个主剧的结构也很完整", "下面我们来看第二个例子"]
cfg, project = voice(texts)
# 第二个识别引擎：c000 听成「是个」，c001 也听成原来的「主剧」（一键改好了「主句」），c002 没问题
fake_engine({"c000": "我们今天讲是个函数", "c001": "这个主剧的结构也很完整", "c002": "下面我们来看第二个例子"})

# 老师在表格里把 c000 自己改成「四个」（还没保存）
review.set_draft(project, "c000", text="我们今天讲四个函数")
# 一键全部文字校正：c001 直接改好「主剧 → 主句」（还没保存）
wf.run_transcript_fix(cfg, "v", once=True)

res = pc.find_suspects(project, cfg)
print("find_suspects says flagged =", res["flagged"])
draft = review.load_draft(project)
active = []
for r in project.load_manifest():
    t = review.current_values(r, draft.get(r["id"]))["text"]
    info = review.analyze(r, t)
    if info["active"]:
        active.append(r["id"])
    show(project, r["id"], "table")
print("rows actually red / with suggestions in the table:", active)

try:
    sys.path.insert(0, ROOT)
    from voicetwin.webui.app import _clips_count_md
    md = _clips_count_md(cfg, "v")
    import re
    m = re.search(r"\*\*(\d+)\*\* 条可能有错", md)
    print("header count shown above table:", m.group(1) if m else "(none: no 可能有错 line)")
except Exception as e:
    print("could not import webui:", e)
