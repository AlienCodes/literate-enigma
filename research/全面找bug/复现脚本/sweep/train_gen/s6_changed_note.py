"""Train, then change+save a sentence in the proofreading table, then generate from the web UI handler.
Is the "text changed after training" warning visible in the generation result (not only the collapsed log)?"""
import common
from common import fresh, wf, VOICE
from voicetwin.data import review
from voicetwin.webui import app as A
cfg, project, root, tmp = fresh("note")
wf.run_train(cfg, VOICE, "gptsovits", select=True, sovits_save_every=1, gpt_save_every=1)
rec = next(r for r in project.load_manifest() if r.get("keep") and r.get("split", "train") == "train")
review.set_draft(project, rec["id"], text="训练以后又改过的一句话。")
wf.review_save(cfg, VOICE, ids=[rec["id"]])
print("material_changed_note:", wf.material_changed_note(cfg, VOICE, "gptsovits")[:60])
ui = A.WebUI(cfg)
O = ui.GEN_OUT
outs = list(ui.do_generate(VOICE, "大家好，今天我们讲第一课。", None, "gptsovits", "fast", 0, "", "", "", "wav"))
last = dict(zip(O, outs[-1]))
md = str(last.get("gen_md"))
log = str(last.get("gen_log"))
print("gen_md has note:", "上次训练以后改过" in md)
print("gen_log has note:", "上次训练以后改过" in log)
print("--- gen_md ---\n" + md[:600])
pv = ui.train_plan_preview(VOICE, "gptsovits")
print("train tab preview has note:", "上次训练以后改过" in pv)
