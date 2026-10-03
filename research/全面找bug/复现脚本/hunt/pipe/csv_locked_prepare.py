"""transcripts.csv open in Excel (Windows locks it: open(..., 'w') -> PermissionError [Errno 13]) while the teacher
adds a new lecture video and clicks 「开始准备素材」.  The review table save/delete paths tolerate this (csv_locked),
but prepare() calls project.export_csv() unguarded at the very end."""
import builtins, time
from pathlib import Path
from common import HERE, cleanup, lecture, make_cfg, make_lecture, workspace
import voicetwin.project as projmod
from voicetwin import workflows as wf
from voicetwin.errors import explain

ws = workspace("csvlock")
cfg = make_cfg(ws)
V = "张老师"
wf.run_prepare(cfg, V, [str(lecture(2))])
new_dir = HERE / "lecture_cache" / "second"
if not (new_dir / "第2课.wav").exists():
    make_lecture(new_dir / "第2课.wav", repeats=1, seed=7)
p = wf.Project(cfg, V)
csv_path = str(p.csv_path)
real_open = builtins.open
def excel_lock_open(file, mode="r", *a, **k):
    if str(file) == csv_path and any(m in mode for m in "wa+"):
        raise PermissionError(13, "Permission denied", csv_path)   # what Windows raises while Excel has the file open
    return real_open(file, mode, *a, **k)
projmod.open = excel_lock_open   # module-level name lookup -> only voicetwin.project's writes see the lock
n_before = len(p.load_manifest())
mt = (p.root / "prepare_summary.json").stat().st_mtime
try:
    s = wf.run_prepare(cfg, V, [str(lecture(2)), str(new_dir)])
    print("run_prepare OK, csv_locked flag:", s.get("csv_locked"), "warnings:", s.get("warnings")[:2])
except Exception as exc:
    f = explain(exc)
    print("run_prepare FAILED:", type(exc).__name__, exc)
    print("teacher sees:", f.title, "|", f.advice[:50])
print("manifest records before/after:", n_before, len(p.load_manifest()))
print("prepare_summary.json updated:", (p.root / "prepare_summary.json").stat().st_mtime != mt)
del projmod.open
cleanup()
