"""Give rows 1..15 (odd indexes, not deleted) an auto-proofcheck suggestion: replace char 1 with 好."""
import os, sys
os.chdir(sys.argv[1])
sys.path.insert(0, "/home/user/literate-enigma")
from voicetwin.config import load_config
from voicetwin import workflows as wf
from voicetwin.data import review as rv
cfg = load_config()
p = wf.Project(cfg, "我的声音")
recs = p.load_manifest()
n = 0
for i, r in enumerate(recs[:30]):
    if i % 2 == 0 or r.get("deleted") or not r.get("keep") or len(r["text"]) < 4:
        continue
    t = r["text"]
    alt = t[0] + "好" + t[2:]
    if alt == t:
        continue
    r["suspect"] = {"spans": [[1, 2]], "alt": alt, "reasons": ["测试"], "score": 0.7}
    info = rv.analyze(r, t)
    print(i, r["id"], bool(info["edits"]), t[:12], "->", alt[:12])
    n += 1
p.save_manifest(recs)
p.export_csv(recs)
print("suspects", n)
