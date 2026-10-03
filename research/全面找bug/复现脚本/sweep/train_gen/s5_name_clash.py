"""Web UI names outputs <name>_<MM月DD日HH点MM分>.<fmt>. Generate WAV, then switch the format radio to MP3 and
generate again in the same minute: the MP3 run writes a temporary WAV at the same path and deletes it."""
import common
from common import fresh, wf, VOICE
from voicetwin.webui import app as A
cfg, project, _, tmp = fresh("clash", gsv=False)
script = "大家好，今天我们讲第一课。"
w = A._output_path(project, "第3课", "wav", "x")
m = A._output_path(project, "第3课", "mp3", "x")
print("wav path:", w.name, "| mp3 path:", m.name)
r1 = wf.run_narrate(cfg, VOICE, script, out=str(w), quality="fast")
print("after WAV run:", sorted(p.name for p in project.outputs_dir.iterdir()))
r2 = wf.run_narrate(cfg, VOICE, script, out=str(m), quality="fast")
print("after MP3 run:", sorted(p.name for p in project.outputs_dir.iterdir()))
print("WAV still exists:", w.exists())
