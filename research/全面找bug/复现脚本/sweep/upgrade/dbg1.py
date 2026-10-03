import sys, json
sys.path.insert(0, "/home/user/literate-enigma"); sys.path.insert(0, "/home/user/literate-enigma/tests")
from pathlib import Path
from conftest import make_cfg
from voicetwin import workflows as wf
from voicetwin.data import review, transcript_fix as tf
WS = Path(sys.argv[1]); V = "我的声音"
cfg = make_cfg(WS); project = wf.open_project(cfg, V, must_exist=True)
recs = project.load_manifest(); r0 = recs[0]
print(json.dumps({k: r0.get(k) for k in ("text","orig_text","suspect","text_edited","edited")}, ensure_ascii=False, indent=1))
a = review.analyze(r0)
print("analyze:", {k: a[k] for k in ("red","edits","sure","undo","adopted","active","to_alt","to_base")})
res = wf.run_transcript_fix(cfg, V, once=True)
recs = project.load_manifest(); r0 = recs[0]
d = review.load_draft(project)
print("after:", review.current_values(r0, d.get(r0["id"]))["text"])
print(json.dumps(r0.get("suspect"), ensure_ascii=False, indent=1))
a = review.analyze(r0, review.current_values(r0, d.get(r0["id"]))["text"])
print("analyze:", {k: a[k] for k in ("red","edits","sure","undo","adopted","active","to_alt","to_base")})
