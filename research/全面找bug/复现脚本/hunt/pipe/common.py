"""Shared helpers for the pipeline bug hunt (read-only on the repo)."""
import os
import shutil
import sys
from pathlib import Path

REPO = Path("/home/user/literate-enigma")
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tests"))

# block model downloads like tests/conftest.py does
from voicetwin.eval import sv_models  # noqa: E402

sv_models.download = lambda cfg, progress=None, keys=None: []

from conftest import make_cfg, make_lecture  # noqa: E402


def workspace(name: str) -> Path:
    ws = HERE / "tmp ws 工作区" / name
    if ws.exists():
        shutil.rmtree(ws)
    ws.mkdir(parents=True)
    return ws


LECTURE_CACHE = HERE / "lecture_cache"


def lecture(repeats: int = 2) -> Path:
    d = LECTURE_CACHE / f"r{repeats}"
    f = d / "第1课 讲座（上）.wav"
    if not f.exists():
        make_lecture(f, repeats=repeats)
    return d


def cleanup():
    shutil.rmtree(HERE / "tmp ws 工作区", ignore_errors=True)
