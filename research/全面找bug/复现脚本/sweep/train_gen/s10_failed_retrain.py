"""Train; later fix a sentence (save + confirm) and retrain, but the retrain fails (out of VRAM even at batch 1 /
or the teacher presses Stop). The old model (trained on the old text) is still the one used for generation.
Does the program still warn that the model was trained on the old text?"""
import os
import common
from common import fresh, wf, VOICE
from voicetwin.data import review
cfg, project, root, tmp = fresh("retrainfail")
wf.run_train(cfg, VOICE, "gptsovits", select=True, sovits_save_every=1, gpt_save_every=1)
sel_before = project.load_models()["gptsovits"]["selected"]["id"]
rec = next(r for r in project.load_manifest() if r.get("keep") and r.get("split", "train") == "train")
review.set_draft(project, rec["id"], text="老师后来改好的一句话。")
wf.review_save(cfg, VOICE, ids=[rec["id"]])
wf.review_confirm(cfg, VOICE)
print("1) note after editing (before retrain):", bool(wf.material_changed_note(cfg, VOICE, "gptsovits")))
os.environ["FAKE_GSV_OOM_ABOVE"] = "0"      # every batch size runs out of VRAM
try:
    wf.run_train(cfg, VOICE, "gptsovits", select=True, sovits_save_every=1, gpt_save_every=1)
    print("retrain: succeeded?!")
except Exception as exc:
    print("2) retrain failed:", str(exc).splitlines()[0][:90])
del os.environ["FAKE_GSV_OOM_ABOVE"]
m = project.load_models()["gptsovits"]
print("3) model still selected:", m["selected"]["id"], "(same as before:", m["selected"]["id"] == sel_before, ")",
      "file exists:", os.path.exists(m["selected"]["sovits"]))
note = wf.material_changed_note(cfg, VOICE, "gptsovits")
print("4) note after failed retrain:", repr(note[:50]))
from voicetwin.webui import app as A
pv = A.WebUI(cfg).train_plan_preview(VOICE, "gptsovits")
print("5) train tab mentions old material:", "上次训练以后改过" in pv)
