"""SRT-timed narration (配音): next cue starts a little (<20 ms) before the previous sentence ends."""
import common
from common import fresh, wf, VOICE
from checks import gaps
import numpy as np
from voicetwin.utils.audio import load_audio
cfg, project, _, tmp = fresh("timed", gsv=False)
s1, s2 = "第一句话在一秒开始，稍微长一点。", "第二句紧接着开始。"
srt = tmp / "a.srt"
srt.write_text(f"1\n00:00:01,000 --> 00:00:03,000\n{s1}\n\n2\n00:00:20,000 --> 00:00:22,000\n{s2}\n", encoding="utf-8")
r = wf.run_narrate(cfg, VOICE, str(srt), out=str(tmp / "a.wav"), quality="fast")
end1 = r.segments[0]["end"]
print("sentence 1 ends at", end1)
for delta in (0.010, 0.019, 0.030, 0.6):
    st = end1 - delta
    ms = int(round((st % 1) * 1000)); sec = int(st)
    srt.write_text(f"1\n00:00:01,000 --> 00:00:03,000\n{s1}\n\n2\n00:00:{sec:02d},{ms:03d} --> 00:00:{sec+2:02d},{ms:03d}\n{s2}\n", encoding="utf-8")
    r = wf.run_narrate(cfg, VOICE, str(srt), out=str(tmp / f"b{delta}.wav"), quality="fast")
    a, b = r.segments
    p, wav, sr = gaps(r.audio_path, r.segments, margin=0.0, label=f"delta={delta}")
    srt_out = r.srt_path.read_text(encoding="utf-8").split("\n")
    print(f"cue2 asked {st:.3f}: seg1 [{a['start']:.3f},{a['end']:.3f}] seg2 [{b['start']:.3f},{b['end']:.3f}] "
          f"overlap {max(0, a['end']-b['start'])*1000:.1f} ms | srt: {srt_out[1]} / {srt_out[5]} | warnings {r.warnings}")
    for x in p: print("   ", x)
