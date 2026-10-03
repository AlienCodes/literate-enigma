import sys, os, re
OLD = sys.argv[1]
sys.path.insert(0, OLD); sys.path.insert(0, os.path.join(OLD, "tests"))
import tempfile
from conftest import make_cfg
from voicetwin.webui.app import build_app
build_app(make_cfg(tempfile.mkdtemp()), local=True)
loaded = {m for m in sys.modules if m.startswith("voicetwin")}
src = open(os.path.join(OLD, "voicetwin/webui/app.py"), encoding="utf-8").read()
refs = set(re.findall(r"^\s+from (voicetwin[\w.]*) import", src, re.M)) | set(re.findall(r"^\s+import (voicetwin[\w.]*)", src, re.M))
print("loaded at startup:", len(loaded))
print("lazily imported in handlers but NOT loaded at startup:", sorted(r for r in refs if r not in loaded))
