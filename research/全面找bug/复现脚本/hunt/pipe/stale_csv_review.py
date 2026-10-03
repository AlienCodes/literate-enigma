"""Web 「保存修改」 while transcripts.csv is open in Excel: manifest is saved, CSV is NOT (csv_locked).  Later the teacher
closes Excel and runs the README's `voicetwin review -v ...` (sync Excel edits): the stale CSV silently reverts the
web-saved correction."""
import builtins
from common import cleanup, lecture, make_cfg, workspace
import voicetwin.project as projmod
from voicetwin import workflows as wf
from voicetwin.data import review
from voicetwin.cli import main
ws = workspace("stalecsv"); cfg = make_cfg(ws); V = "张老师"
wf.run_prepare(cfg, V, [str(lecture(2))])
p = wf.Project(cfg, V)
rid = [r["id"] for r in p.load_manifest() if r.get("text")][0]
csv_path = str(p.csv_path); real_open = builtins.open
def locked(file, mode="r", *a, **k):
    if str(file) == csv_path and "w" in mode:
        raise PermissionError(13, "Permission denied", csv_path)
    return real_open(file, mode, *a, **k)
projmod.open = locked
review.set_draft(p, rid, text="老师在网页上改好的这一句。")
res = wf.review_save(cfg, V)
print("web save: saved", res["saved"], "csv_locked", res.get("csv_locked"))
del projmod.open                      # Excel closed
print("manifest text:", next(r for r in p.load_manifest() if r["id"] == rid)["text"])
summary = wf.apply_review(cfg, V)      # what `voicetwin review -v 张老师` runs
print("after `voicetwin review`: changed", summary["changed"], "| manifest text:", next(r for r in p.load_manifest() if r["id"] == rid)["text"])
cleanup()
