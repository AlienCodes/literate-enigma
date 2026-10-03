"""Independent repro: are pauses in MP3 output exact zeros? Compare with WAV."""
import sys, tempfile, shutil
from pathlib import Path
ROOT = "/home/user/literate-enigma"
sys.path.insert(0, ROOT); sys.path.insert(0, ROOT + "/tests")
import numpy as np
from voicetwin.eval import sv_models
sv_models.download = lambda cfg, progress=None, keys=None: []
from conftest import make_cfg, make_lecture
from voicetwin import workflows as wf
from voicetwin.utils.ffmpeg import decode_to_array

base = Path(tempfile.mkdtemp(dir="/tmp/claude-0/-home-user-literate-enigma/a7bf493d-04b5-5828-bb09-9d8cecef37ad/scratchpad/sweep/traingen-verify-mp3"))
try:
    lec = make_lecture(base / "lec" / "第1课.wav", repeats=1)
    cfg = make_cfg(base / "ws")
    wf.run_prepare(cfg, "v", [str(lec.parent)])
    wf.review_confirm(cfg, "v")
    script = "大家好，今天我们讲第一课。\n\n这一句是第二段，用来看段落停顿。为什么要这样做呢？\n\n好，我们下节课再见。"
    for fmt in ("wav", "mp3"):
        res = wf.run_narrate(cfg, "v", script, out=str(base / f"out.{fmt}"), quality="fast")
        p = Path(res.audio_path)
        if fmt == "wav":
            import soundfile as sf
            wav, sr = sf.read(str(p), dtype="float32")
        else:
            wav, sr = decode_to_array(p, sample_rate=24000)
        segs = res.segments
        m = int(0.005 * sr)
        nz = tot = 0; mx = 0.0
        for a, b in zip(segs, segs[1:]):
            lo, hi = int(round(a["end"] * sr)) + m, int(round(b["start"] * sr)) - m
            g = wav[lo:hi]; tot += len(g); nz += int(np.count_nonzero(g))
            if len(g): mx = max(mx, float(np.max(np.abs(g))))
        lead = wav[: max(0, int(segs[0]["start"] * sr) - m)]
        tail = wav[int(round(segs[-1]["end"] * sr)) + m:]
        print(fmt, p.name, "sr", sr, "segments", len(segs), f"pause non-zero {nz}/{tot}",
              f"peak {20*np.log10(mx) if mx else float('-inf'):.1f} dBFS",
              "lead max", float(np.max(np.abs(lead))) if len(lead) else None,
              "tail max", float(np.max(np.abs(tail))) if len(tail) else None)
finally:
    shutil.rmtree(base, ignore_errors=True)
