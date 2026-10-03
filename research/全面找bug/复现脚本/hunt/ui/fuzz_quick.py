"""Call every quick (non-streaming, non-task) event handler with odd inputs, then run gradio 4.24's own
postprocess on the result (catches wrong output counts / bad update dicts / exceptions)."""
import os, sys, inspect, itertools, traceback, json
os.chdir(sys.argv[1])
sys.path.insert(0, "/home/user/literate-enigma")
from voicetwin.config import load_config
from voicetwin.webui.app import WebUI
from gradio.state_holder import SessionState
import gradio as gr
ui = WebUI(load_config())
app = ui.build()
id2name = {comp._id: k for k, comp in ui.c.items()}
VOICES = [None, "", [], ["我的声音"], "[]", "我的声音", "不存在的声音", "..", ".", "a/b", "   ", "我的 声音", "x<y", "声音!@#￥%……&（）", "CON"]
SKIP = {"do_prepare", "do_train", "do_select", "do_generate", "do_speed_preview", "do_verify", "do_blind", "do_download",
        "do_proofcheck", "do_textfix", "on_stop_expire", "lib_pick", "clip_pick", "gen_pick", "do_eval"}
GENERIC = [None, "", [], "[]", 0, "x"]
fails = []
n = 0
for i, bf in enumerate(app.fns):
    fn = bf.fn
    if fn is None:
        continue
    name = getattr(fn, "__name__", "?")
    if name in SKIP:
        continue
    ins = [id2name.get(b._id, type(b).__name__) for b in bf.inputs]
    pools = []
    for nm in ins:
        if nm == "voice":
            pools.append(VOICES)
        else:
            pools.append(GENERIC)
    combos = list(itertools.product(*pools)) if len(pools) <= 2 else [tuple(p[k % len(p)] for p in pools) for k in range(20)]
    for args in combos[:200]:
        n += 1
        try:
            if bf.fn.__code__.co_flags & 0x20:  # generator
                outs = list(fn(*args))
            else:
                outs = [fn(*args)]
            st = SessionState(app)
            for o in outs:
                if len(bf.outputs) == 1:
                    app.postprocess_data(i, o, st)
                    continue
                if not isinstance(o, (list, tuple)):
                    raise TypeError(f"returned {type(o)} for {len(bf.outputs)} outputs")
                app.postprocess_data(i, list(o), st)
        except Exception as exc:
            fails.append((i, name, ins, repr(args)[:120], f"{type(exc).__name__}: {exc}"[:300]))
print("calls", n, "failures", len(fails))
seen = set()
for f in fails:
    key = (f[1], f[4][:80])
    if key in seen:
        continue
    seen.add(key)
    print(f)
