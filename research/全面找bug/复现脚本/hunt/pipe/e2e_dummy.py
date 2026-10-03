"""End-to-end with the dummy backend: prepare -> proofread edits -> save -> confirm -> list -> narrate -> silence check."""
import json
import sys
import time

import numpy as np
import soundfile as sf

from common import REPO, cleanup, lecture, make_cfg, workspace

from voicetwin import workflows as wf
from voicetwin.data import review
from voicetwin.data.exporters import gptsovits_list_text, train_records

VOICE = "王老师 的声音（第2版）& #1"
ws = workspace("e2e")
cfg = make_cfg(ws)
t0 = time.time()
summary = wf.run_prepare(cfg, VOICE, [str(lecture(2))])
print("prepare", round(time.time() - t0, 1), "s; kept", summary["clips_kept"], "/", summary["clips_total"])
proj = wf.open_project(cfg, VOICE, must_exist=True)
recs = proj.load_manifest()
kept = [r for r in recs if r.get("keep") and r.get("text")]
print("kept with text", len(kept), "val", sum(1 for r in kept if r.get("split") == "val"))

a, b, c, d = kept[0], kept[1], kept[2], kept[3]
review.set_draft(proj, a["id"], text="老师改好的第一句｜带竖线|和换行\n第二行。")
review.set_draft(proj, b["id"], text="  第二句改过  ")
review.set_draft(proj, c["id"], text="第三句改了但是要删掉")
wf.review_delete(cfg, VOICE, c["id"])
print("unsaved", review.unsaved_count(proj))
res = wf.review_confirm(cfg, VOICE)
print("confirm:", res["confirmed"], res["counts"], "saved", res["saved"])
print("blocker:", repr(wf.training_blocker(proj)))
recs2 = {r["id"]: r for r in proj.load_manifest()}
print("a text saved:", repr(recs2[a["id"]]["text"]))
print("b text saved:", repr(recs2[b["id"]]["text"]))
print("c deleted:", recs2[c["id"]].get("deleted"), "draft still:", c["id"] in review.load_draft(proj))
lst = gptsovits_list_text(proj, "spk")
lines = lst.strip().split("\n")
print("list lines", len(lines), "train records", len(train_records(proj)))
bad = [l for l in lines if len(l.split("|")) != 4]
print("malformed list lines:", bad[:3])
print("c in list:", any(c["id"] in l for l in lines))
print("a line:", [l for l in lines if a["id"] in l])

# Narrate with dummy backend and check silences
script = "大家好，这是第一句话。\n\n这是第二句话，我们来看看。\n\nHello everyone, this is English.\n\n[停顿 1.5 秒]\n\n最后一句。"
out = ws / "out 输出" / "讲稿 测试.wav"
r = wf.run_narrate(cfg, VOICE, script, out=str(out), quality="fast")
wav, sr = sf.read(str(r.audio_path), dtype="int16")
print("narrate:", r.audio_path.name, r.duration, "sr", sr, "segments", len(r.segments))
rep = json.loads(r.report_path.read_text(encoding="utf-8"))
segs = rep["segments"]
prev_end = 0.0
for s in segs:
    a_ = int(round(prev_end * sr)) + 2
    b_ = int(round(s["start"] * sr)) - 2
    gap = wav[a_:b_]
    print(f"  gap before seg {s['index']}: {prev_end:.3f}-{s['start']:.3f} nonzero={int(np.count_nonzero(gap))} of {len(gap)}")
    prev_end = s["end"]
tail = wav[int(round(prev_end * sr)) + 2:]
print("  tail nonzero", int(np.count_nonzero(tail)), "of", len(tail))
print(r.audio_path)
if "--keep" not in sys.argv:
    cleanup()
