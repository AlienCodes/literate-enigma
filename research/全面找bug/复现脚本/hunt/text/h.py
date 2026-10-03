"""Helper: temp voices under ./tmp (TMPDIR), repo read-only."""
import os, sys, tempfile, json
from pathlib import Path
HERE = Path(__file__).resolve().parent
(HERE / "tmp").mkdir(exist_ok=True); os.environ["TMPDIR"] = str(HERE / "tmp"); tempfile.tempdir = str(HERE / "tmp")
ROOT = "/home/user/literate-enigma"
sys.path.insert(0, ROOT); sys.path.insert(0, ROOT + "/tests")
from conftest import make_cfg
from voicetwin import workflows as wf
from voicetwin.data import review, transcript_fix as tf, lexicon_fix as lf
def voice(texts, ids=None, name="v", extra=None):
    d = Path(tempfile.mkdtemp()); cfg = make_cfg(d / "ws")
    project = wf.Project(cfg, name).ensure()
    ids = ids or [f"c{i:03d}" for i in range(len(texts))]
    recs = [{"id": i, "path": f"clips/{i}.wav", "text": t, "lang": "zh", "duration": 3.0, "keep": True, "split": "train"} for i, t in zip(ids, texts)]
    if extra:
        for r in recs: r.update(extra.get(r["id"], {}))
    project.save_manifest(recs)
    return cfg, project
def cur(project, rid):
    rec = {r["id"]: r for r in project.load_manifest()}[rid]
    return rec, review.current_values(rec, review.load_draft(project).get(rid))["text"]
def table(project, ids=None):
    out = {}
    d = review.load_draft(project)
    for r in project.load_manifest():
        if ids and r["id"] not in ids: continue
        c = review.current_values(r, d.get(r["id"]))["text"]
        i = review.analyze(r, c)
        out[r["id"]] = (c, tuple(i["red"]), tuple(i["edits"]), tuple(i["undo"]), tuple(i["sure"]))
    return out
