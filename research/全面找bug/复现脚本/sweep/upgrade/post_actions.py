import sys, json, shutil, tempfile
sys.path.insert(0, "/home/user/literate-enigma"); sys.path.insert(0, "/home/user/literate-enigma/tests")
from pathlib import Path
from conftest import make_cfg
from voicetwin import workflows as wf
from voicetwin.data import review
WS0 = Path(sys.argv[1]); V = "我的声音"
work = Path(tempfile.mkdtemp(dir=str(WS0.parent)))
shutil.copytree(WS0 / V, work / "base" / V)
cfg = make_cfg(work / "base"); p = wf.open_project(cfg, V, must_exist=True)
wf.run_transcript_fix(cfg, V, once=True)
ids = [r["id"] for r in p.load_manifest()]
def cur(pp, rid):
    r = {x["id"]: x for x in pp.load_manifest()}[rid]
    return review.current_values(r, review.load_draft(pp).get(rid))["text"], review.analyze(r, review.current_values(r, review.load_draft(pp).get(rid))["text"])
for i, rid in enumerate(ids):
    t, a = cur(p, rid)
    for act in ("adopt", "unadopt"):
        if (act == "adopt" and not a["edits"]) or (act == "unadopt" and not a["undo"]):
            continue
        d = work / f"{i}{act}"; shutil.copytree(work / "base", d)
        c2 = make_cfg(d); p2 = wf.open_project(c2, V, must_exist=True)
        try:
            (review.adopt_suggestion if act == "adopt" else review.unadopt_suggestion)(p2, rid)
            t2, a2 = cur(p2, rid)
            print(f"row {i} {act}: {t}\n         -> {t2}   (undo after={a2['undo']}, edits after={a2['edits']})")
        except Exception as exc:
            print(f"row {i} {act}: ERR {exc}")
shutil.rmtree(work)
