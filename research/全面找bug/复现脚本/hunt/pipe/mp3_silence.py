"""MP3 output (offered in the web page's 格式 radio): are the pauses between sentences still exact digital silence?"""
import json, subprocess, numpy as np, soundfile as sf
from pathlib import Path
from common import cleanup, lecture, make_cfg, workspace
from voicetwin import workflows as wf

ws = workspace("mp3"); cfg = make_cfg(ws, synth={"output_format": "mp3"}) if False else make_cfg(ws)
wf.run_prepare(cfg, "张老师", [str(lecture(2))])
script = "大家好，这是第一句话。\n\n这是第二句话，我们来看看。\n\n最后一句。"
r = wf.run_narrate(cfg, "张老师", script, out=str(ws / "讲稿.mp3"), quality="fast")
print("output:", r.audio_path.name)
from voicetwin.utils import ffmpeg as ff
exe = ff.find_ffmpeg() if hasattr(ff, "find_ffmpeg") else "ffmpeg"
dec = ws / "decoded.wav"
subprocess.run([str(exe), "-y", "-loglevel", "error", "-i", str(r.audio_path), "-c:a", "pcm_s16le", str(dec)], check=True)
wav, sr = sf.read(str(dec), dtype="int16")
rep = json.loads(r.report_path.read_text(encoding="utf-8"))
prev = 0.0
for s in rep["segments"]:
    a, b = int(round(prev * sr)), int(round(s["start"] * sr))
    g = wav[a:b]; nz = np.flatnonzero(g)
    mid = g[len(g)//4: 3*len(g)//4]
    print(f"  gap before {s['index']}: {len(g)} samples, nonzero {len(nz)}, max |x| {int(np.abs(g).max()) if len(g) else 0}, "
          f"nonzero in middle half {int(np.count_nonzero(mid))}, first/last nonzero offsets {nz[:1].tolist()} {(len(g)-nz[-1:]).tolist()}")
    prev = s["end"]
cleanup()
