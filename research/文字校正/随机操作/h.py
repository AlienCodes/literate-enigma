"""随机操作脚本共用的小工具：建一个临时的声音、读一行现在的文字。仓库根目录自动找。"""
import sys, tempfile, json
from pathlib import Path
ROOT = str(Path(__file__).resolve().parents[3])
sys.path.insert(0, ROOT); sys.path.insert(0, ROOT + "/tests")
from conftest import make_cfg
from voicetwin import workflows as wf
from voicetwin.data import review, transcript_fix as tf, lexicon_fix as lf
def voice(texts, ids=None, name="v"):
    d = Path(tempfile.mkdtemp()); cfg = make_cfg(d / "ws")
    project = wf.Project(cfg, name).ensure()
    ids = ids or [f"c{i:03d}" for i in range(len(texts))]
    project.save_manifest([{"id": i, "path": f"clips/{i}.wav", "text": t, "lang": "zh", "duration": 3.0, "keep": True, "split": "train"} for i, t in zip(ids, texts)])
    return cfg, project
def cur(project, rid):
    rec = {r["id"]: r for r in project.load_manifest()}[rid]
    return rec, review.current_values(rec, review.load_draft(project).get(rid))["text"]
