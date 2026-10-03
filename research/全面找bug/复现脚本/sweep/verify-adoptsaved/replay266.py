import sys, json
sys.path.insert(0, "/tmp/claude-0/-home-user-literate-enigma/a7bf493d-04b5-5828-bb09-9d8cecef37ad/scratchpad/sweep/proofcheck")
import fuzz_auto as F
from common import *
orig_find = pc.find_suspects
calls = {"n": 0}
def spy(project, cfg, *a, **k):
    calls["n"] += 1
    rec = {r["id"]: r for r in project.load_manifest()}["c004"]
    d = review.load_draft(project).get("c004")
    t = review.current_values(rec, d)["text"]
    info = review.analyze(rec, t)
    print(f"#{calls['n']} BEFORE text={t!r} saved={rec['text']!r} dirty={review.is_dirty(rec, d)} undo={info['undo']} suspect={json.dumps(rec.get('suspect'), ensure_ascii=False)} auto={json.dumps(rec.get('suspect_auto'), ensure_ascii=False)}")
    res = orig_find(project, cfg, *a, **k)
    rec = {r["id"]: r for r in project.load_manifest()}["c004"]
    d = review.load_draft(project).get("c004")
    t = review.current_values(rec, d)["text"]
    info = review.analyze(rec, t)
    print(f"#{calls['n']} AFTER  text={t!r} undo={info['undo']} edits={info['edits']} suspect={json.dumps(rec.get('suspect'), ensure_ascii=False)} auto={json.dumps(rec.get('suspect_auto'), ensure_ascii=False)}")
    return res
F.pc.find_suspects = spy
F.run(266)
print(dict(F.viol))
