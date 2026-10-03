"""(c) one-click clears auto red marks because the mother text proves the sentence right; then 🔍 (wf.run_proofcheck)
and a prepare-style auto check run again. Do the red marks come back?"""
import re
from common import *
install_fake()
mother = [x for _, x in tf.builtin_mother() if not re.search(r"[A-Za-z0-9]", x) and 12 <= len(x) <= 40][:30]
# second engine hears a different char in the middle of every sentence (as if the auto check doubts it)
swap = {"的": "得", "是": "事", "这": "着", "我": "握", "们": "门", "一": "医", "个": "各", "在": "再", "有": "又", "来": "莱"}
texts, heard = [], []
for x in mother:
    pos = next((i for i, ch in enumerate(x) if ch in swap and 3 <= i <= len(x) - 3), None)
    if pos is None: continue
    texts.append(x); heard.append(x[:pos] + swap[x[pos]] + x[pos + 1:])
cfg, project = voice(texts)
ids = [r["id"] for r in project.load_manifest()]
ANS.update(dict(zip(ids, heard)))
def red_rows():
    return sorted(i for i in ids if state(project, i)["active"])
r0 = wf.run_proofcheck(cfg, "v")
before = red_rows()
print("auto check before one-click: flagged", r0["flagged"], "red rows", len(before))
res = wf.run_transcript_fix(cfg, "v", once=True)
after1 = red_rows()
print("one-click: cleared", res.get("cleared"), "fixes", res.get("fixes"), "-> red rows", len(after1), "button grey", tf.textfix_used(project))
r2 = wf.run_proofcheck(cfg, "v")
after2 = red_rows()
print("🔍 again: flagged", r2["flagged"], "-> red rows", len(after2), "came back:", sorted(set(after2) - set(after1)))
review.save_rows(project)
r3 = wf.run_proofcheck(cfg, "v")
after3 = red_rows()
print("save + 🔍 again: flagged", r3["flagged"], "-> red rows", len(after3), "came back:", sorted(set(after3) - set(after1)))
for i in sorted(set(after2) - set(after1))[:3]:
    print(" example", i, state(project, i))
