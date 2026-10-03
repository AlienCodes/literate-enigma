"""Undo memory made BEFORE the first click on a batch (auto suggestion adopted then undone / typed back / row revert)
must stop the one-click from applying the same change."""
from h import *
t = "我们先来看艾子引导的这个定语从句的例子"
cfg, p = voice([t, t, t])
recs = p.load_manifest()
for r in recs:
    r["suspect"] = {"spans": [[5, 7]], "alt": "我们先来看as引导的这个定语从句的例子", "reasons": ["另一个引擎"], "score": 0.6}
p.save_manifest(recs)
review.adopt_suggestion(p, "c000"); review.unadopt_suggestion(p, "c000")           # red button
review.adopt_suggestion(p, "c001"); review.set_draft(p, "c001", text=t)              # typed back
review.adopt_suggestion(p, "c002"); review.save_rows(p, ["c002"])
review.set_draft(p, "c002", text=t)                                                  # typed back after save
print("rejected:", review.load_rejected(p))
wf.run_transcript_fix(cfg, "v", once=True)
for k in ("c000", "c001", "c002"): print(k, cur(p, k)[1])
