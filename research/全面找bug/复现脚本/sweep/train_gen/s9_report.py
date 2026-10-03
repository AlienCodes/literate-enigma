"""Generation failure through the web UI handler (real api_v2.py; GPT-SoVITS refuses the reference audio and answers
200 + 1 s of silence): is the reason shown and a problem report produced?"""
import common
from common import fresh, wf, VOICE
from voicetwin.webui import app as A
from voicetwin.utils.audio import load_audio, save_audio
cfg, project, root, tmp = fresh("rep")
wf.run_train(cfg, VOICE, "gptsovits", select=False, sovits_save_every=1, gpt_save_every=1)
for r in project.load_references():  # make every reference 2.5 s long (GPT-SoVITS needs 3~10 s)
    p = project.abspath(r["path"]); w, sr = load_audio(p); save_audio(p, w[: int(2.5 * sr)], sr)
ui = A.WebUI(cfg)
O = ui.GEN_OUT
outs = list(ui.do_generate(VOICE, "大家好，今天我们讲第一课。", None, "gptsovits", "balanced", 0, "", "", "", "wav"))
last = dict(zip(O, outs[-1]))
print("gen_md:", str(last.get("gen_md"))[:700])
reps = sorted(project.logs_dir.glob("问题报告_*.txt"))
print("reports:", [p.name for p in reps])
