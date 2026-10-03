"""Independent helper: one prepared voice (synthetic lecture with srt, asr none), copied per scenario."""
import json, re, shutil, sys, tempfile
from pathlib import Path

ROOT = "/home/user/literate-enigma"
sys.path.insert(0, ROOT)
sys.path.insert(0, ROOT + "/tests")
HERE = Path(__file__).resolve().parent
BASE = HERE / "base"
TMP = HERE / "tmp"
TMP.mkdir(exist_ok=True)

from conftest import make_cfg, make_lecture  # noqa: E402
from voicetwin import workflows as wf  # noqa: E402
from voicetwin.data import review  # noqa: E402

VOICE = "测试声音"
strip = lambda s: re.sub("<[^>]+>", "", str(s or ""))


def ensure_base():
    if (BASE / "ok").exists():
        return
    shutil.rmtree(BASE, ignore_errors=True)
    make_lecture(BASE / "lectures" / "第1课.wav", repeats=1)
    wf.run_prepare(make_cfg(BASE / "ws"), VOICE, [str(BASE / "lectures")])
    (BASE / "ok").write_text("1")


def fresh(name):
    ensure_base()
    d = Path(tempfile.mkdtemp(prefix=name + "_", dir=TMP))
    shutil.copytree(BASE / "ws" / VOICE, d / "ws" / VOICE)
    cfg = make_cfg(d / "ws")
    from voicetwin.webui import app as A
    return cfg, wf.Project(cfg, VOICE), A.WebUI(cfg)


def act(ui, action, cid, only=False, **extra):
    payload = json.dumps(dict(action=action, id=cid, no="1", seq="t", **extra), ensure_ascii=False)
    return ui.do_clip_action(VOICE, payload, only)


def recs(project):
    return {r["id"]: r for r in project.load_manifest()}
