"""Shared helpers: build one prepared voice (synthetic lecture, srt text, asr none) once, copy it per scenario."""
import json, shutil, sys, tempfile, os
from pathlib import Path

ROOT = "/home/user/literate-enigma"
sys.path.insert(0, ROOT)
sys.path.insert(0, ROOT + "/tests")
HERE = Path(__file__).resolve().parent
BASE = HERE / "base"          # prepared base workspace (kept between runs, deleted at the end)
TMP = HERE / "tmp"            # per-scenario copies
TMP.mkdir(exist_ok=True)

from conftest import make_cfg, make_lecture  # noqa: E402
from voicetwin import workflows as wf  # noqa: E402
from voicetwin.data import review, transcript_fix as tf  # noqa: E402

VOICE = "测试声音"


def ensure_base():
    marker = BASE / "ok"
    if marker.exists():
        return
    shutil.rmtree(BASE, ignore_errors=True)
    lec = BASE / "lectures"
    make_lecture(lec / "第1课.wav")
    cfg = make_cfg(BASE / "ws")
    wf.run_prepare(cfg, VOICE, [str(lec)])
    marker.write_text("1")


def fresh(name="s"):
    """copy the base voice into a new workspace; returns (cfg, project, ui)."""
    ensure_base()
    d = Path(tempfile.mkdtemp(prefix=name + "_", dir=TMP))
    shutil.copytree(BASE / "ws" / VOICE, d / "ws" / VOICE)
    cfg = make_cfg(d / "ws")
    from voicetwin.webui import app as A
    ui = A.WebUI(cfg)
    return cfg, wf.Project(cfg, VOICE), ui


def act(ui, action, cid, only=False, **extra):
    payload = json.dumps(dict(action=action, id=cid, no="1", seq="t", **extra), ensure_ascii=False)
    return ui.do_clip_action(VOICE, payload, only)


def cur(project, rid):
    rec = {r["id"]: r for r in project.load_manifest()}[rid]
    return review.current_values(rec, review.load_draft(project).get(rid))


def recs(project):
    return {r["id"]: r for r in project.load_manifest()}


def run_stream(gen):
    outs = list(gen)
    return outs
