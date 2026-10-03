"""不用来训练的行（灰色，keep=False）：查错字不查它，但它以前的红字还在、上面的「N 条可能有错」还算它。"""
from common import *
from voicetwin.webui import app as A
import re
cfg, project = voice(["我们今天讲十个函数", "下面我们来看第二个例子"])
fake_engine({"c000": "我们今天讲是个函数", "c001": "下面我们来看第二个例子"})
pc.find_suspects(project, cfg)
review.set_draft(project, "c000", keep=False); review.save_rows(project)  # 这一行改成不用（保存）
ui = A.WebUI(cfg)
outs = list(ui.do_proofcheck("v", False))
last = dict(zip(ui.PROOF_OUT, outs[-1]))
print("message:", last["proof_md"].splitlines()[0])
count, rows = ui.refresh_clips("v", False, None)
m = re.search(r"\*\*(\d+)\*\* 条可能有错", count)
print("header :", m.group(0) if m else "none")
col = A.CLIP_HEADERS.index(A.COL_SUSPECT)
print("red cells:", [r[1] for r in rows if 'vt-red' in str(r[col])])
