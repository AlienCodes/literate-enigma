"""Independent repro: SRT-timed generation, next cue starts slightly before / right at previous sentence end.

usage: python repro_timed.py <code_root>   (code_root = repo checkout or exported HEAD)
Uses a prepared dummy-backend voice copied from the reporter's base (built exactly like tests' `prepared`).
"""
import os, sys, shutil, tempfile, re
from pathlib import Path

CODE = sys.argv[1]
sys.path.insert(0, CODE); sys.path.insert(0, CODE + "/tests")
HERE = Path(__file__).resolve().parent
BASE = Path("/tmp/claude-0/-home-user-literate-enigma/a7bf493d-04b5-5828-bb09-9d8cecef37ad/scratchpad/sweep/train_gen/base/ws/测试声音")

from conftest import make_cfg  # noqa
from voicetwin.eval import sv_models  # noqa
sv_models.download = lambda cfg, progress=None, keys=None: []
from voicetwin import workflows as wf  # noqa
import voicetwin.synth.engine as eng  # noqa
print("engine file:", eng.__file__)
import numpy as np  # noqa
from voicetwin.utils.audio import load_audio  # noqa

VOICE = "测试声音"
tmp = Path(tempfile.mkdtemp(prefix="timed_", dir=str(HERE)))
try:
    ws = tmp / "ws"
    shutil.copytree(BASE, ws / VOICE)
    cfg = make_cfg(ws)

    def fmt(t):
        ms = int(round(t * 1000)); s, ms = divmod(ms, 1000); m, s = divmod(s, 60)
        return f"00:{m:02d}:{s:02d},{ms:03d}"

    s1, s2, s3 = "第一句话在一秒开始，稍微长一点。", "第二句紧接着开始。", "第三句也挨着上一句。"
    srt = tmp / "a.srt"

    def run(cues, tag):
        body = "".join(f"{i+1}\n{fmt(a)} --> {fmt(b)}\n{t}\n\n" for i, (a, b, t) in enumerate(cues))
        srt.write_text(body, encoding="utf-8")
        return wf.run_narrate(cfg, VOICE, str(srt), out=str(tmp / f"{tag}.wav"), quality="fast", variants=False)

    r = run([(1.0, 3.0, s1), (20.0, 22.0, s2)], "probe")
    end1 = r.segments[0]["end"]
    print("sentence 1 ends at", round(end1, 4))

    for delta in (0.010, 0.019, 0.0, -0.05, 0.030, 0.6):
        st = end1 - delta
        r = run([(1.0, 3.0, s1), (st, st + 2.0, s2)], f"d{delta}")
        a, b = r.segments[0], r.segments[1]
        wav, sr = load_audio(r.audio_path)
        lo, hi = int(round(a["end"] * sr)), int(round(b["start"] * sr))
        gap_ms = (b["start"] - a["end"]) * 1000
        zeros = None
        if hi > lo:
            zeros = bool(np.all(wav[lo:hi] == 0.0))
        out_srt = r.srt_path.read_text(encoding="utf-8")
        times = re.findall(r"(\d\d:\d\d:\d\d,\d\d\d) --> (\d\d:\d\d:\d\d,\d\d\d)", out_srt)
        def sec(x):
            h, m, rest = x.split(":"); s, ms = rest.split(",")
            return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000
        srt_overlap = sec(times[1][0]) < sec(times[0][1])
        print(f"delta={delta*1000:5.0f}ms cue2={st:.3f} | seg1 [{a['start']:.3f},{a['end']:.3f}] seg2 [{b['start']:.3f},{b['end']:.3f}]"
              f" gap={gap_ms:7.1f}ms all-zero-gap={zeros} | srt {times[0][1]} vs {times[1][0]} overlap={srt_overlap}"
              f" | warnings={[w for w in r.warnings if '字幕' in w]}")

    # three back-to-back cues (common in video subtitles: next cue starts exactly where previous ends)
    # make cue slots shorter than speech so they get pushed
    r = run([(1.0, 2.0, s1), (2.0, 3.0, s2), (3.0, 4.0, s3)], "b2b")
    segs = r.segments
    for x, y in zip(segs, segs[1:]):
        print(f"back-to-back: seg{x['index']} end {x['end']:.3f} -> seg{y['index']} start {y['start']:.3f} gap {(y['start']-x['end'])*1000:.1f}ms")
    print("b2b warnings:", r.warnings)
finally:
    shutil.rmtree(tmp, ignore_errors=True)
