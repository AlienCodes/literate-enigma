"""Which concurrency group / limit do the review-table buttons get in gradio 4.24?  Different groups = can run at
the same time (each listener's default limit is 1 only within its own group)."""
from common import cleanup, make_cfg, workspace
from voicetwin.webui import app as A
ws = workspace("uiconc"); ui = A.WebUI(make_cfg(ws / "ws")); app = ui.build()
conf = app.get_config_file()
def dep(comp, event="click"):
    cid = ui.c[comp]._id
    for i, d in enumerate(conf["dependencies"]):
        if any(t[0] == cid and t[1] == event for t in d["targets"]):
            fn = app.fns[i]
            return fn.concurrency_id, fn.concurrency_limit, d.get("trigger_mode")
for comp in ("confirm_btn", "clip_action_btn", "find_repall", "gen_btn", "prep_btn"):
    try:
        print(f"{comp:<16}", dep(comp))
    except KeyError:
        print(comp, "not found")
# the 「保存修改」 button is a local variable in build(); find it by the bound function name
for i, d in enumerate(conf["dependencies"]):
    fn = app.fns[i]
    name = getattr(fn.fn, "__name__", "") or ""
    if "save" in name.lower() or "保存修改" in name:
        print(f"{name:<16}", (fn.concurrency_id, fn.concurrency_limit, d.get("trigger_mode")))
print("queue default concurrency limit:", getattr(app, "_queue", None) and getattr(app._queue, "default_concurrency_limit", None))
cleanup()
