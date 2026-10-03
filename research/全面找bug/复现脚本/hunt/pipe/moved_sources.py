"""Incremental prepare identifies already-processed videos by source_id = name + hash(ABSOLUTE path, size).
Same videos at a different absolute path (USB disk got another drive letter; VoiceTwin unpacked into a new
folder so workspace/<voice>/uploads moved) are treated as NEW: every clip is cut again and added a second time,
with the raw (uncorrected) text, next to the teacher's corrected copy -> both go into training."""
import shutil, sys
from pathlib import Path
from common import HERE, cleanup, lecture, make_cfg, workspace
from voicetwin import workflows as wf
from voicetwin.data import review
from voicetwin.data.exporters import train_records
from voicetwin.webui import app as webapp

# --- variant 1: videos folder path changed (E:\ -> F:\)
ws = workspace("moved"); cfg = make_cfg(ws); V = "张老师"
usb_e = ws / "E盘" / "讲课视频"; shutil.copytree(lecture(2), usb_e)
wf.run_prepare(cfg, V, [str(usb_e)])
p = wf.Project(cfg, V)
first = [r for r in p.load_manifest() if r.get("text")][0]
fixed = first["text"].replace("Python", "派森")
review.set_draft(p, first["id"], text=fixed); wf.review_confirm(cfg, V)
n1 = len(p.load_manifest())
usb_f = ws / "F盘" / "讲课视频"; shutil.move(str(usb_e.parent), str(usb_f.parent))   # same disk, new letter
s = wf.run_prepare(cfg, V, [str(usb_f)])
recs = p.load_manifest()
print(f"[videos moved] clips before {n1}, after re-running prepare on the same videos: {len(recs)}; "
      f"files_new reported: {s['files_new']}")
tr = train_records(p, include_val=True)
same_audio = [r for r in tr if abs(r['start'] - first['start']) < 0.01 and abs(r['end'] - first['end']) < 0.01]
print("   training rows for the SAME stretch of audio:", [(r['id'][-12:], r['text'][:16]) for r in same_audio])
from collections import Counter
c = Counter((round(r['start'], 2), round(r['end'], 2)) for r in tr)
print("   training rows total", len(tr), "; audio stretches used twice:", sum(1 for v in c.values() if v > 1))

# --- variant 2: web uploads, then VoiceTwin unpacked to a new folder (workspace copied along)
ws2 = workspace("moved2"); cfg2 = make_cfg(ws2); V2 = "李老师"
lec = next(Path(lecture(2)).glob("*.wav"))
webapp._prepare_job(cfg2, V2, [str(lec)], "", {})
n_a = len(wf.Project(cfg2, V2).load_manifest())
new_ws = ws2.parent / "moved2_v18.5" ; shutil.rmtree(new_ws, ignore_errors=True)
shutil.move(str(ws2), str(new_ws)); cfg3 = make_cfg(new_ws)
extra = HERE / "lecture_cache" / "second"; extra_f = next(extra.glob("*.wav")) if extra.exists() else None
if extra_f is None:
    from common import make_lecture; extra_f = make_lecture(extra / "第2课.wav", repeats=1, seed=7)
s2 = webapp._prepare_job(cfg3, V2, [str(extra_f)], "", {})   # teacher uploads ONE new lecture
print(f"[uploads + new install folder] clips before {n_a}; after uploading one new 10-sentence lecture: "
      f"{len(wf.Project(cfg3, V2).load_manifest())} (files_new reported {s2['files_new']})")
shutil.rmtree(new_ws, ignore_errors=True)
cleanup()
