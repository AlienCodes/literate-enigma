"""Start the REAL v18.4 web UI (code snapshot from commit 645e9f0^) on a port, like the old black window."""
import os, sys, tempfile
OLD = os.path.join(os.path.dirname(os.path.abspath(__file__)), "old184")
sys.path.insert(0, OLD); sys.path.insert(0, os.path.join(OLD, "tests"))
port = int(sys.argv[1]); ws = sys.argv[2]
open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "old.pid"), "w").write(str(os.getpid()))
import webbrowser; webbrowser.open = lambda *a, **k: True
import voicetwin; print("OLD voicetwin", voicetwin.__version__, voicetwin.__file__, flush=True)
from conftest import make_cfg
from voicetwin.webui import launcher
launcher.launch(make_cfg(ws), port=port)
