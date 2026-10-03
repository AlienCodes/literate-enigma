"""用真的网页处理函数（WebUI.do_proofcheck，后台任务 + 进度）点「🔍 自动查找可能的错字」：
老师在表格里已经把错字改好（还没保存）时，网页说「其中 1 条可能有错（已在表格里标红）」，表格里却没有红字。"""
from common import *
from voicetwin.webui import app as A
cfg, project = voice(["我们今天讲十个函数", "下面我们来看第二个例子"])
fake_engine({"c000": "我们今天讲是个函数", "c001": "下面我们来看第二个例子"})
review.set_draft(project, "c000", text="我们今天讲四个函数")  # 老师自己改好了（还没保存）
ui = A.WebUI(cfg)
outs = list(ui.do_proofcheck("v", False))
last = dict(zip(ui.PROOF_OUT, outs[-1]))
print("proof_md   :", last["proof_md"].splitlines()[0])
count, rows = ui.refresh_clips("v", False, None)
import re
print("header     :", re.search(r"可能有错", count) and "has 可能有错" or "no 「可能有错」 line in header")
col = A.CLIP_HEADERS.index(A.COL_SUSPECT)
print("red cells  :", sum('vt-red' in str(r[col]) for r in rows))
count2, rows2 = ui.refresh_clips("v", True, None)
print("只看可能有错的 rows:", [r[1] for r in rows2], "(c000 shows only because it has an unsaved edit)")
