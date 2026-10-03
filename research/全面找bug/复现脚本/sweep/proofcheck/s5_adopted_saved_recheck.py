"""老师点「采用」→ 保存 → 按钮变红「已采用」（还能撤销）。再点一次「🔍 自动查找」（或者加新素材时自动查）以后呢？"""
from common import *
cfg, project = voice(["我们今天讲十个函数", "下面我们来看第二个列子"])
fake_engine({"c000": "我们今天讲是个函数", "c001": "下面我们来看第二个例子"})
pc.find_suspects(project, cfg)
review.adopt_suggestion(project, "c000")
show(project, "c000", "adopted, unsaved")
pc.find_suspects(project, cfg)
show(project, "c000", "auto check again (unsaved)")
review.save_rows(project)
show(project, "c000", "saved")
try:
    from voicetwin.webui.app import _suggest_cell
    rec, t = cur(project, "c000"); print("   button:", "已采用" in _suggest_cell(review.analyze(rec, t)))
except Exception as e:
    print(e)
pc.find_suspects(project, cfg)
info = show(project, "c000", "saved, then auto check again")
rec, t = cur(project, "c000"); print("   button:", "已采用" in _suggest_cell(review.analyze(rec, t)))
try:
    review.unadopt_suggestion(project, "c000")
except ValueError as e:
    print("   unadopt ->", e)
