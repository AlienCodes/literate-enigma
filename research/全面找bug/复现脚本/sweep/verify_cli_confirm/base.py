"""Build one prepared voice (dummy backend, like the `prepared` fixture) into ./base/ws."""
import sys, shutil, time
from pathlib import Path
ROOT = "/home/user/literate-enigma"
sys.path.insert(0, ROOT); sys.path.insert(0, ROOT + "/tests")
HERE = Path(__file__).resolve().parent
from conftest import make_cfg, make_lecture
from voicetwin.eval import sv_models
sv_models.download = lambda cfg, progress=None, keys=None: []
from voicetwin import workflows as wf
base = HERE / "base"
shutil.rmtree(base, ignore_errors=True)
lec = base / "lectures"
make_lecture(lec / "第1课.wav")
ws = base / "ws"
cfg = make_cfg(ws)
t = time.time()
s = wf.run_prepare(cfg, "测试声音", [str(lec)])
print("prepared", s["clips_kept"], s["clips_total"], round(time.time() - t, 1), "s")
out = wf.review_confirm(cfg, "测试声音")
print("confirmed", out["confirmed"], out["counts"])
