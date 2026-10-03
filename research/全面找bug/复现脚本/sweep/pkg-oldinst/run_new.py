"""Run the CURRENT (v18.5) launcher on the same port, exactly as start_webui.bat (python -m voicetwin webui) does."""
import os, sys
sys.path.insert(0, "/home/user/literate-enigma"); sys.path.insert(0, "/home/user/literate-enigma/tests")
port = int(sys.argv[1]); ws = sys.argv[2]
import webbrowser
opened = []
webbrowser.open = lambda url, *a, **k: opened.append(url) or True
import voicetwin; print("NEW voicetwin", voicetwin.__version__, voicetwin.__file__, flush=True)
from conftest import make_cfg
from voicetwin.webui import launcher
built = []
orig_build = launcher._build
def spy(cfg, local):
    built.append(1)
    raise SystemExit("[spy] new v18.5 app WOULD be built now (stopping here)")
launcher._build = spy
try:
    launcher.launch(make_cfg(ws), port=port)
except SystemExit as e:
    print(e)
print("RESULT opened_in_browser=%r new_app_built=%r" % (opened, bool(built)), flush=True)
