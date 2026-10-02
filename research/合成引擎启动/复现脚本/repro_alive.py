"""Reproduce: VoiceTwin's GPT-SoVITS readiness probe never succeeds against the REAL api_v2.py.

Runs the official api_v2.py (any git ref of RVC-Boss/GPT-SoVITS) with the heavy TTS classes stubbed out
(no torch, no models, no GPU), then probes it the way VoiceTwin does (GPTSoVITSBackend._alive) and with
candidate replacement probes.

usage: [SERVER_PY=/path/to/python-with-fastapi] python repro_alive.py [git-ref]   (default ref 20250606v2pro)
"""
import os
import socket
import subprocess
import sys
import tempfile
import time
import types
from pathlib import Path

GSV = Path(__file__).resolve().parent.parent / "gsv_latest"
REPO = Path("/home/user/literate-enigma")
ref = sys.argv[1] if len(sys.argv) > 1 else "20250606v2pro"

root = Path(tempfile.mkdtemp(prefix="gsvstub_"))
(root / "tools/i18n").mkdir(parents=True)
(root / "GPT_SoVITS/TTS_infer_pack").mkdir(parents=True)
for p in ("tools/__init__.py", "tools/i18n/__init__.py", "GPT_SoVITS/__init__.py", "GPT_SoVITS/TTS_infer_pack/__init__.py"):
    (root / p).write_text("")
(root / "tools/i18n/i18n.py").write_text("class I18nAuto:\n    def __call__(self, k): return k\n")
(root / "GPT_SoVITS/TTS_infer_pack/TTS.py").write_text(
    "class TTS_Config:\n    languages=['zh','en','auto']\n    version='v2ProPlus'\n"
    "    def __init__(self,p): pass\n    def __str__(self): return 'stub'\n"
    "class TTS:\n    def __init__(self,c): pass\n")
(root / "GPT_SoVITS/TTS_infer_pack/text_segmentation_method.py").write_text(
    "def get_method_names(): return ['cut0','cut1','cut5']\n")
src = subprocess.run(["git", "-C", str(GSV), "show", f"{ref}:api_v2.py"], capture_output=True, check=True).stdout
(root / "api_v2.py").write_bytes(src)

with socket.socket() as s:
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
log = open(root / "api.log", "w")
proc = subprocess.Popen([os.environ.get("SERVER_PY", sys.executable), "api_v2.py", "-a", "127.0.0.1", "-p", str(port), "-c", "x.yaml"],
                        cwd=root, stdout=log, stderr=subprocess.STDOUT)
try:
    for _ in range(100):
        try:
            socket.create_connection(("127.0.0.1", port), 0.3).close()
            break
        except OSError:
            time.sleep(0.2)
    sys.path.insert(0, str(REPO))
    from voicetwin.backends.gptsovits import GPTSoVITSBackend  # noqa: E402
    import requests  # noqa: E402

    o = types.SimpleNamespace(api_url=f"http://127.0.0.1:{port}", _http=None)
    o._session = types.MethodType(GPTSoVITSBackend._session, o)
    print(f"[{ref}] child alive: {proc.poll() is None}")
    print(f"[{ref}] VoiceTwin _alive() x5:", [GPTSoVITSBackend._alive(o) for _ in range(5)])
    s = requests.Session(); s.trust_env = False
    for path in ("/tts", "/tts?text_lang=zh&prompt_lang=zh", "/control", "/set_gpt_weights", "/openapi.json"):
        r = s.get(o.api_url + path, timeout=3, headers={"Connection": "close"})
        print(f"[{ref}] GET {path:36s} -> {r.status_code} {r.headers.get('content-type')} {r.text[:60]!r}")
finally:
    proc.terminate(); proc.wait(5); log.close()
    text = (root / "api.log").read_text(errors="replace")
    print(f"[{ref}] api.log: {text.count(chr(10))} lines, "
          f"{text.count('ERROR:    Exception in ASGI application')} x 'Exception in ASGI application', "
          f"{text.count(chr(39) + 'NoneType' + chr(39) + ' object has no attribute ' + chr(39) + 'lower')} x AttributeError lower")
