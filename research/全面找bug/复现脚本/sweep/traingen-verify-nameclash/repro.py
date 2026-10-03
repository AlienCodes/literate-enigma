"""Independent repro: web UI output naming + _write_audio temp WAV.
usage: python repro.py <code_root> <workdir>
Builds a prepared dummy voice, then:
 T1 WAV then MP3 with web-UI names, same minute (path computed at click time, like do_generate)
 T2 WAV then WAV (e.g. redo) with web-UI names, same minute
 T3 perfect tier: WAV then MP3 with same explicit stem (engine-level)
"""
import sys, os, time, hashlib, json, shutil
from pathlib import Path
code_root, work = sys.argv[1], Path(sys.argv[2])
sys.path.insert(0, code_root); sys.path.insert(0, code_root + "/tests")
import voicetwin
assert voicetwin.__file__.startswith(code_root), voicetwin.__file__
from conftest import make_cfg, make_lecture
from voicetwin.eval import sv_models
sv_models.download = lambda cfg, progress=None, keys=None: []
from voicetwin import workflows as wf
from voicetwin.webui import app as A
VOICE = "测试声音"
shutil.rmtree(work, ignore_errors=True)
lec = work / "lectures"; make_lecture(lec / "第1课.wav")
ws = work / "ws"; cfg = make_cfg(ws)
t = time.time(); wf.run_prepare(cfg, VOICE, [str(lec)]); wf.review_confirm(cfg, VOICE)
print("prepare took", round(time.time() - t, 1), "s")
project = wf.open_project(cfg, VOICE, must_exist=True)
out_dir = Path(project.outputs_dir)
md5 = lambda p: hashlib.md5(Path(p).read_bytes()).hexdigest()[:10]
ls = lambda: sorted(p.name for p in out_dir.iterdir()) if out_dir.exists() else []

def wait_fresh_minute():
    # make sure both runs land in the same minute: start right after a minute boundary if we are late in the minute
    if time.localtime().tm_sec > 30:
        time.sleep(61 - time.localtime().tm_sec)

script = "大家好，今天我们讲第一课。为什么要学这个呢？"
script2 = "大家好，今天我们讲第二课。"
# warm up the cache so later runs are fast like the teacher's regenerations
wf.run_narrate(cfg, VOICE, script, out=str(work / "warm.wav"), quality="fast")
wf.run_narrate(cfg, VOICE, script2, out=str(work / "warm2.wav"), quality="fast")
for p in out_dir.glob("*"): p.unlink()

print("\n=== T1: WAV then MP3, web UI names, same minute ===")
wait_fresh_minute(); m0 = A._time_suffix()
w = A._output_path(project, "第3课", "wav", "x")
r1 = wf.run_narrate(cfg, VOICE, script, out=str(w), quality="fast")
h_wav = md5(r1.audio_path); rep1 = json.loads(Path(r1.report_path).read_text(encoding="utf-8"))
print("run1 ->", r1.audio_path.name, r1.report_path.name, "| files:", ls())
m = A._output_path(project, "第3课", "mp3", "x")   # computed at the 2nd click, like do_generate
r2 = wf.run_narrate(cfg, VOICE, script, out=str(m), quality="fast")
print("run2 ->", r2.audio_path.name, r2.report_path.name, "| files:", ls())
print("same minute:", m0 == A._time_suffix())
print("T1 RESULT: WAV of run1 still exists:", Path(r1.audio_path).exists(),
      "| run1 report still points to run1 audio:", Path(r1.report_path).exists() and json.loads(Path(r1.report_path).read_text(encoding='utf-8'))['audio'] == rep1['audio'])
for p in out_dir.glob("*"): p.unlink()

print("\n=== T2: WAV then WAV (different script, e.g. corrected text), web UI names, same minute ===")
wait_fresh_minute(); m0 = A._time_suffix()
w1 = A._output_path(project, "第3课", "wav", "x")
r1 = wf.run_narrate(cfg, VOICE, script, out=str(w1), quality="fast"); h1 = md5(r1.audio_path)
w2 = A._output_path(project, "第3课", "wav", "x")
r2 = wf.run_narrate(cfg, VOICE, script2, out=str(w2), quality="fast")
print("paths:", w1.name, w2.name, "| same minute:", m0 == A._time_suffix(), "| files:", ls())
print("T2 RESULT: run1 audio still has run1 content:", Path(r1.audio_path).exists() and md5(r1.audio_path) == h1)
for p in out_dir.glob("*"): p.unlink()

print("\n=== T3: perfect tier, WAV then MP3 with the same stem (engine level) ===")
pdir = work / "perf"; pdir.mkdir()
r1 = wf.run_narrate(cfg, VOICE, script, out=str(pdir / "p.wav"), quality="perfect")
print("variants run1:", [(v["name"], Path(v["path"]).name) for v in r1.variants], "| files:", sorted(x.name for x in pdir.iterdir()))
rep1 = Path(r1.report_path).read_text(encoding="utf-8")
r2 = wf.run_narrate(cfg, VOICE, script, out=str(pdir / "p.mp3"), quality="perfect")
print("files after mp3 run:", sorted(x.name for x in pdir.iterdir()))
print("T3 RESULT: p.wav exists:", (pdir / "p.wav").exists(),
      "| variant wavs exist:", [Path(v['path']).exists() for v in r1.variants],
      "| p.report.json unchanged:", Path(r1.report_path).read_text(encoding='utf-8') == rep1)
