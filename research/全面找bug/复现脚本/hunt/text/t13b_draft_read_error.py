"""Same pattern in review.load_draft / load_rejected: a read error (OSError, not just a broken file) is treated as
'no draft', and the next set_draft/adopt writes the file back with only that one row -> every other unsaved change
(e.g. the 123 fixes of the one-click) is gone."""
import pathlib
from h import *
cfg, p = voice(["这个借词是一个定语从剧。", "我们看关系带词。", "它是一个关键代词"])
wf.run_transcript_fix(cfg, "v", once=True)
print("unsaved before:", sorted(review.load_draft(p)))
orig_read = pathlib.Path.read_text
def flaky(self, *a, **kw):
    if self.name == review.DRAFT_FILE:
        pathlib.Path.read_text = orig_read   # fails exactly once
        raise PermissionError(13, "being used by another process")
    return orig_read(self, *a, **kw)
pathlib.Path.read_text = flaky
review.set_draft(p, "c002", text="它是一个关系代词呀")   # teacher edits one row at that moment
print("unsaved after:", {k: v["text"] for k, v in review.load_draft(p).items()}, "(c000/c001 fixes lost)")
