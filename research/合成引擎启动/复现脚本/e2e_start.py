"""End-to-end: VoiceTwin GPTSoVITSBackend.start() (unchanged repo code) against the REAL api_v2.py of tag
20250606v2pro whose TTS class is stubbed (no models). Shows: child alive the whole time, start() times out."""
import os, shutil, sys, time, subprocess
from pathlib import Path
sys.path.insert(0, "/home/user/literate-enigma"); sys.path.insert(0, "/home/user/literate-enigma/tests")
from voicetwin.config import load_config
from voicetwin.project import Project
from voicetwin.backends.base import get_backend
from fake_gptsovits import build_fake_root
D = Path(__file__).resolve().parent
work = D / "e2e"; shutil.rmtree(work, ignore_errors=True); work.mkdir()
root = build_fake_root(work / "GPT-SoVITS")
# replace the fake api_v2.py with the real one + stub modules
shutil.copy(D / "realapi" / "api_v2.py", root / "api_v2.py")
shutil.copytree(D / "realapi" / "tools", root / "tools", dirs_exist_ok=True)
shutil.copytree(D / "realapi" / "GPT_SoVITS" / "TTS_infer_pack", root / "GPT_SoVITS" / "TTS_infer_pack", dirs_exist_ok=True)
(root / "GPT_SoVITS" / "__init__.py").touch()
cfg = load_config(overrides={"workspace": str(work / "ws"), "backend": "gptsovits",
                             "backends": {"gptsovits": {"root": str(root), "python": sys.executable, "port": 29890,
                                                        "startup_timeout": 14}}}, user_config=False)
project = Project(cfg, "我的声音"); project.ensure()
b = get_backend("gptsovits", cfg, project)
b.STARTUP_NOTE_SECONDS = 4.0
os.environ["STUB_LOAD_SECONDS"] = "2"
t = time.time()
alive_at_timeout = None
orig_stop = b.stop
def spy_stop():
    global alive_at_timeout
    if b.proc is not None and alive_at_timeout is None:
        alive_at_timeout = b.proc.poll() is None
    orig_stop()
b.stop = spy_stop
try:
    b.start()
    print("start() returned OK (unexpected)")
except Exception as e:
    print(f"start() raised after {time.time()-t:.1f}s: {e}")
print("child process was alive when start() gave up:", alive_at_timeout)
log = (project.logs_dir / "gptsovits_api.log").read_text(encoding="utf-8")
print("api log: 'Uvicorn running' present:", "Uvicorn running" in log,
      "| GET /tts 500 lines:", log.count('"GET /tts HTTP/1.1" 500'),
      "| AttributeError lines:", log.count("AttributeError: 'NoneType' object has no attribute 'lower'"))
