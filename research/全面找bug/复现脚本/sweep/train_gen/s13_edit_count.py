"""Training log says 'N of them are sentences you corrected, trained with the corrected text'. Edit only a 考试题
(validation) sentence and one sentence changed and then changed back; what number is shown?"""
import logging
import common
from common import fresh, wf, VOICE
from voicetwin.data import review
cfg, project, root, tmp = fresh("editcount")
recs = project.load_manifest()
val = next(r for r in recs if r.get("keep") and r.get("split") == "val")
tr = next(r for r in recs if r.get("keep") and r.get("split", "train") == "train")
review.set_draft(project, val["id"], text="考试题这一句老师改过。")
wf.review_save(cfg, VOICE, ids=[val["id"]])
old = tr["text"]
review.set_draft(project, tr["id"], text=old + "改")
wf.review_save(cfg, VOICE, ids=[tr["id"]])
review.set_draft(project, tr["id"], text=old)          # changed back to exactly what was recognised
wf.review_save(cfg, VOICE, ids=[tr["id"]])
wf.review_confirm(cfg, VOICE)
m = {r["id"]: r for r in project.load_manifest()}
print("val still val:", m[val["id"]].get("split"), "| train row text back to original:", m[tr["id"]]["text"] == m[tr["id"]].get("orig_text"))
lines = []
class H(logging.Handler):
    def emit(self, rec): lines.append(rec.getMessage())
logging.getLogger("voicetwin").addHandler(H())
wf.run_train(cfg, VOICE, "gptsovits", select=False, sovits_save_every=1, gpt_save_every=1)
print([l for l in lines if l.startswith("这次训练用")])
trained = (project.exports_dir / "gptsovits" / "train.list").read_text(encoding="utf-8")
import pathlib
print("edited val clip in train.list:", pathlib.Path(m[val["id"]]["path"]).name in trained)
