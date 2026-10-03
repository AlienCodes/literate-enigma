"""Second path: a clip that had no text (not recognized) at one-click time; she types its text and marks it 要用."""
from common import *  # noqa
cfg, p, ui = fresh("empty")
rs = p.load_manifest()
rid = rs[3]["id"]
rs[3]["text"] = ""; rs[3]["keep"] = False
p.save_manifest(rs)
outs = list(ui.do_textfix(VOICE)); last = dict(zip(ui.TEXTFIX_OUT, outs[-1]))
print("1 after one-click: page button interactive", last["tr_btn"]["interactive"], "| backend used", wf.textfix_used(cfg, VOICE))
r1 = act(ui, "edit", rid, text="这是老师自己打上去的一句话。")
r2 = act(ui, "use", rid)
print("2 typed text + 要用 (handlers return", len(r1), len(r2), "outputs, no button):", "backend used", wf.textfix_used(cfg, VOICE),
      "| new ids", tf.textfix_new_ids(p), "| reload would show interactive", ui.textfix_btn(VOICE)["interactive"])
