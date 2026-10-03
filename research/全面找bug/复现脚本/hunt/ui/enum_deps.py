import os, sys, inspect
os.chdir(sys.argv[1])
sys.path.insert(0, "/home/user/literate-enigma")
from voicetwin.config import load_config
from voicetwin.webui.app import WebUI
ui = WebUI(load_config())
app = ui.build()
id2name = {}
for k, comp in ui.c.items():
    id2name[comp._id] = k
for i, bf in enumerate(app.fns):
    dep = app.dependencies[i]
    fn = bf.fn
    name = getattr(fn, "__name__", str(fn)) if fn else None
    ins = [id2name.get(b._id, f"{type(b).__name__}#{b._id}") for b in bf.inputs]
    outs = [id2name.get(b._id, f"{type(b).__name__}#{b._id}") for b in bf.outputs]
    trig = [(id2name.get(t[0]._id if hasattr(t[0], '_id') else t[0], str(t[0])), t[1]) for t in getattr(bf, 'targets', [])] if hasattr(bf,'targets') else dep.get('targets')
    print(i, name, "trig=", dep.get("targets"), "conc=", bf.concurrency_limit, bf.concurrency_id, "js=", bool(dep.get("js")), "\n   in=", ins, "\n   out=", outs)
