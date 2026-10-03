"""Side check: 🔍 stopped half-way after one-click cleared red marks. Do they come back until the next full run?"""
import re
from common import *
from voicetwin.utils import progress as P
install_fake()
mother = [x for _, x in tf.builtin_mother() if not re.search(r"[A-Za-z0-9]", x) and 12 <= len(x) <= 40][:30]
swap = {"的": "得", "是": "事", "这": "着", "我": "握", "们": "门", "一": "医", "个": "各", "在": "再", "有": "又", "来": "莱"}
texts, heard = [], []
for x in mother:
    pos = next((i for i, ch in enumerate(x) if ch in swap and 3 <= i <= len(x) - 3), None)
    if pos is None: continue
    texts.append(x); heard.append(x[:pos] + swap[x[pos]] + x[pos + 1:])
cfg, project = voice(texts)
ids = [r["id"] for r in project.load_manifest()]
ANS.update(dict(zip(ids, heard)))
red = lambda: sorted(i for i in ids if state(project, i)["active"])
wf.run_proofcheck(cfg, "v"); print("before one-click red rows", len(red()))
wf.run_transcript_fix(cfg, "v", once=True); print("after one-click red rows", len(red()))
n = [0]
def prog(f, msg):
    if msg.startswith("已检查"):
        n[0] += 1
        if n[0] == len(ids) - 2: P.request_cancel()
try:
    wf.run_proofcheck(cfg, "v", progress=prog)
except P.TaskCancelled:
    print("stopped")
finally:
    P.clear_cancel()
print("after stopped 🔍 red rows", len(red()), "(button grey:", tf.textfix_used(project), ")")
wf.run_proofcheck(cfg, "v"); print("after full 🔍 red rows", len(red()))
