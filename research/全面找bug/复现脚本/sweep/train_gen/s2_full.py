"""Full flow with real api_v2.py: confirm -> train(+select) -> narrate in several modes; check silence/clicks/SRT."""
import sys, json, time
from pathlib import Path
import common
from common import fresh, calls, wf, VOICE
from checks import gaps
import numpy as np
cfg, project, root, tmp = fresh("full")
t = time.time()
info = wf.run_train(cfg, VOICE, "gptsovits", select=True, sovits_save_every=1, gpt_save_every=1)
print("train+select", round(time.time() - t, 1), "s; selected", info.get("selected"), "err", info.get("selection_error"))
m = project.load_models()["gptsovits"]
print("models.json keys", sorted(m), "speed", m.get("speed"))
sel = m.get("selection") or {}
print("selection best", sel.get("best"), "n results", len(sel.get("results") or []))
script = "大家好，今天我们讲第一课。\n\n这一句是第二段，用来看段落停顿。为什么要这样做呢？\n\nHello everyone, this is English."
problems = []
for q, spd, tag in (("fast", None, "fast"), ("balanced", 0.8, "bal_slow"), ("fast", 1.2, "fast_quick")):
    res = wf.run_narrate(cfg, VOICE, script, out=str(tmp / f"{tag}.wav"), backend_name="gptsovits", quality=q, speed=spd)
    p, wav, sr = gaps(res.audio_path, res.segments, label=tag)
    problems += p
    srt = res.srt_path.read_text(encoding="utf-8") if res.srt_path else ""
    print(tag, "dur", round(res.duration, 2), "segs", len(res.segments), "sr", sr, "srt cues", srt.count("-->"),
          "starts", [s["start"] for s in res.segments])
print("PROBLEMS:", problems or "none")
print("tmp", tmp)
