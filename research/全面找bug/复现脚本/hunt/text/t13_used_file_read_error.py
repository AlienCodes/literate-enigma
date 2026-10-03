"""mark_textfix_used: if reading textfix_used.json fails for a moment (Windows: antivirus / backup tool holding the file
-> PermissionError), the OSError is swallowed and the file is REWRITTEN with only this batch's ids. All earlier batches
are forgotten: their rows count as 'new' again, the button lights up and the next click re-processes old rows."""
import pathlib
from h import *
cfg, p = voice(["这个借词是一个定语从剧。", "我们看关系带词。"])
wf.run_transcript_fix(cfg, "v", once=True)            # batch 1 used
review.save_rows(p)
recs = p.load_manifest()
recs.append({"id": "n000", "path": "clips/n000.wav", "text": "新的一句里有借词。", "lang": "zh", "duration": 3.0, "keep": True, "split": "train"})
p.save_manifest(recs)
print("before: new ids =", tf.textfix_new_ids(p))
orig_read = pathlib.Path.read_text
state = {"n": 0}
def flaky(self, *a, **kw):
    if self.name == tf.USED_FILE:
        state["n"] += 1
        if state["n"] == 2:   # 1st read (textfix_new_ids) works, 2nd read (inside mark_textfix_used) is blocked for a moment
            raise PermissionError(13, "The process cannot access the file because it is being used by another process")
    return orig_read(self, *a, **kw)
pathlib.Path.read_text = flaky
wf.run_transcript_fix(cfg, "v", once=True)            # batch 2
pathlib.Path.read_text = orig_read
print("textfix_used.json now:", (Path(p.root) / tf.USED_FILE).read_text(encoding="utf-8"))
print("after: new ids =", tf.textfix_new_ids(p), "(expected [] - batch 1 rows were already used)")
