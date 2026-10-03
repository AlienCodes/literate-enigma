"""Perfect tier with the real api_v2.py: two variants, choose_variant, SRT, silence; then mp3 + variants."""
import sys, json, time
from pathlib import Path
import common
from common import fresh, calls, wf, VOICE
from checks import gaps
import numpy as np
from voicetwin.utils.audio import load_audio
cfg, project, root, tmp = fresh("perf")
info = wf.run_train(cfg, VOICE, "gptsovits", select=True, sovits_save_every=1, gpt_save_every=1)
print("selection_error", info.get("selection_error"))
script = "大家好，今天我们讲第一课。为什么要学这个呢？\n\n因为它很重要。"
for fmt in ("wav", "mp3"):
    t = time.time()
    res = wf.run_narrate(cfg, VOICE, script, out=str(tmp / f"p.{fmt}"), backend_name="gptsovits", quality="perfect")
    print(fmt, "took", round(time.time()-t,1), "s; final", res.audio_path.name, "variants", [(v["name"], Path(v["path"]).name, v.get("pct"), v["recommended"]) for v in res.variants])
    print("   tries", [s["tries"] for s in res.segments], "srt", res.srt_path.name if res.srt_path else None)
    for v in res.variants:
        p, wav, sr = gaps(v["path"], res.segments, label=f"{fmt}/{v['name']}")
        print("   ", v["name"], "dur", round(len(wav)/sr, 2), "problems", p[:3] if fmt == "wav" else len(p))
    other = next(v for v in res.variants if not v["final"])
    out = wf.choose_variant(cfg, VOICE, str(res.report_path), other["name"])
    a, _ = load_audio(out["audio"]); b, _ = load_audio(other["path"])
    print("   choose ->", out["final"], "final file equals chosen:", len(a) == len(b) and np.allclose(a, b))
    rep = json.loads(Path(res.report_path).read_text(encoding="utf-8"))
    print("   report final", rep["final"], "overall_pct", rep["overall_pct"], "other pct", other.get("pct"))
print("tmp", tmp)
