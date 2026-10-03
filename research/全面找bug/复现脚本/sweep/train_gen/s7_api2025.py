"""Full flow with the 2025 api_v2.py (20250606v2pro) incl. perfect tier (aux refs), English-only, speed extremes, redo."""
import sys, json, time
from pathlib import Path
import common
from common import fresh, calls, wf, VOICE, build_fake_root
from checks import gaps
from fake_gptsovits import REAL_API_V2_2025
import shutil
cfg, project, root, tmp = fresh("api25")
shutil.rmtree(root)
build_fake_root(root, real_api=REAL_API_V2_2025)
info = wf.run_train(cfg, VOICE, "gptsovits", select=True, sovits_save_every=1, gpt_save_every=1)
print("selection_error", info.get("selection_error"), info.get("selection_error_detail"))
script = "大家好，今天我们讲第一课。\n\nThis sentence is English only.\n\n最后一句话，谢谢大家！"
probs = []
for q, spd, tag in (("perfect", None, "perfect"), ("fast", 1.3, "fast13"), ("fast", 0.7, "fast07")):
    res = wf.run_narrate(cfg, VOICE, script, out=str(tmp / f"{tag}.wav"), backend_name="gptsovits", quality=q, speed=spd)
    p, wav, sr = gaps(res.audio_path, res.segments, label=tag); probs += p
    print(tag, "dur", round(res.duration, 2), "warnings", res.warnings[:3])
res = wf.run_narrate(cfg, VOICE, script, out=str(tmp / "redo.wav"), backend_name="gptsovits", quality="fast", redo=[2])
p, wav, sr = gaps(res.audio_path, res.segments, label="redo"); probs += p
print("redo cached flags", [s["cached"] for s in res.segments])
runs = [c for c in calls(root) if c["kind"] == "run"]
print("runs", len(runs), "langs", sorted({(c["req"]["text_lang"], c["req"]["prompt_lang"]) for c in runs}))
print("aux used", max(len(c["req"].get("aux_ref_audio_paths") or []) for c in runs), "speeds", sorted({round(c["req"]["speed_factor"], 3) for c in runs}))
api = (project.logs_dir / "gptsovits_api.log").read_text(encoding="utf-8", errors="replace")
print("Traceback in api log:", api.count("Traceback"), "| 不存在:", api.count("不存在"))
print("PROBLEMS", probs or "none")
