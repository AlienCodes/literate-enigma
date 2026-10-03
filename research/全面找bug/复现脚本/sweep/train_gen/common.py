"""Shared helpers: copy base voice into a fresh temp workspace, build a fake GPT-SoVITS (real api_v2.py)."""
import os, sys, shutil, socket, sysconfig, tempfile, json
from pathlib import Path
ROOT = "/home/user/literate-enigma"
sys.path.insert(0, ROOT); sys.path.insert(0, ROOT + "/tests")
HERE = Path(__file__).resolve().parent
from conftest import make_cfg
from fake_gptsovits import build_fake_root
from voicetwin.eval import sv_models
sv_models.download = lambda cfg, progress=None, keys=None: []
from voicetwin import workflows as wf
from voicetwin.backends.gptsovits import GPTSoVITSBackend
VOICE = "测试声音"
GPTSoVITSBackend.ensure_users_pth = lambda self: None
GPTSoVITSBackend._gpu_memory = lambda self, quick=False: (11.99, 11.2, "test")
GPTSoVITSBackend.POLL_SECONDS = 0.05
GPTSoVITSBackend.STARTUP_NOTE_SECONDS = 0.4
os.environ["FAKE_GSV_CLIP_SLEEP"] = "0.0"
paths = [sysconfig.get_paths()["purelib"], sysconfig.get_paths()["platlib"], os.environ.get("PYTHONPATH", "")]
os.environ["PYTHONPATH"] = os.pathsep.join(p for p in dict.fromkeys(paths) if p)

def port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0)); return s.getsockname()[1]

def fresh(tag, gsv=True, real_api=True, **extra):
    tmp = Path(tempfile.mkdtemp(prefix=f"{tag}_", dir=str(HERE / "tmp")))
    ws = tmp / "ws"
    shutil.copytree(HERE / "base" / "ws" / VOICE, ws / VOICE)
    if not gsv:
        cfg = make_cfg(ws, **extra)
        return cfg, wf.open_project(cfg, VOICE, must_exist=True), None, tmp
    root = build_fake_root(tmp / "GPT-SoVITS", real_api=real_api)
    b = {"root": str(root), "python": sys.executable, "port": port(), "startup_timeout": 60, "is_half": True,
         "train": {"sovits_epochs": 2, "gpt_epochs": 2, "batch_size": 2}}
    b.update(extra.pop("gsv", {}))
    cfg = make_cfg(ws, backend="gptsovits", backends={"gptsovits": b}, **extra)
    return cfg, wf.open_project(cfg, VOICE, must_exist=True), root, tmp

def calls(root):
    f = Path(root) / "_real_api_calls.jsonl"
    return [json.loads(x) for x in f.read_text(encoding="utf-8").splitlines() if x.strip()] if f.exists() else []
(HERE / "tmp").mkdir(exist_ok=True)
