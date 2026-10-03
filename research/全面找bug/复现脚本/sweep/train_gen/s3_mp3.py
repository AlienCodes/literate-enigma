"""MP3 output chosen in the web UI ("MP3（文件小，方便发微信、上传）"): are pauses still exact digital silence?"""
import common
from common import fresh, wf, VOICE
from checks import gaps
import numpy as np
cfg, project, _, tmp = fresh("mp3", gsv=False)
script = "大家好，今天我们讲第一课。\n\n这一句是第二段，用来看段落停顿。为什么要这样做呢？\n\n好，我们下节课再见。"
for fmt in ("wav", "mp3"):
    res = wf.run_narrate(cfg, VOICE, script, out=str(tmp / f"x.{fmt}"), quality="fast")
    p, wav, sr = gaps(res.audio_path, res.segments, label=fmt)
    # how much of the "pause" area is non-zero, and the loudest sample there (dBFS)
    nz = 0; tot = 0; mx = 0.0
    m = int(0.002 * sr)
    for a, b in zip(res.segments, res.segments[1:]):
        lo, hi = int(round(a["end"] * sr)) + m, int(round(b["start"] * sr)) - m
        g = wav[lo:hi]; tot += len(g); nz += int(np.count_nonzero(g)); mx = max(mx, float(np.max(np.abs(g))) if len(g) else 0)
    print(fmt, res.audio_path.name, "sr", sr, f"pause samples non-zero: {nz}/{tot}", f"max {20*np.log10(mx) if mx else -999:.1f} dBFS",
          "| lead-in max", float(np.max(np.abs(wav[: int(res.segments[0]['start'] * sr) - m]))))
    for x in p[:4]:
        print("   ", x)
print("tmp", tmp)
