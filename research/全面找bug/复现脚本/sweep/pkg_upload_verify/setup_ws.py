"""Build a small workspace: voice 我的声音 with 3 clips, one-click correction already used once."""
import os, sys
from pathlib import Path
import numpy as np, soundfile as sf
REPO = "/home/user/literate-enigma"
sys.path.insert(0, REPO)
root = Path(sys.argv[1]).resolve(); root.mkdir(parents=True, exist_ok=True)
(root / "config.yaml").write_text("workspace: ./ws\nbackend: dummy\nspeaker_encoder: mfcc\nprepare:\n  asr:\n    engine: none\n"
                                  "similarity:\n  model_dir: ./sv\n", encoding="utf-8")
os.chdir(root)
from voicetwin import workflows as wf
from voicetwin.config import load_config
from voicetwin.webui import app as A
cfg = load_config()
project = wf.Project(cfg, "我的声音").ensure()
sr = 16000; tt = np.arange(int(4.0 * sr)) / sr
phase = 2 * np.pi * np.cumsum(150 + 8 * np.sin(2 * np.pi * 0.7 * tt)) / sr
v = sum(np.sin(k * phase) / k for k in range(1, 12))
env = 0.5 * (1 - np.cos(2 * np.pi * 4 * tt)) * (np.abs(tt - 2) < 1.9)
y = (0.15 * v * env / np.max(np.abs(v))).astype(np.float32)
texts = ["这个借词后面要接宾语。", "我们今天讲同位于从句。", "定语从剧要放在名词后面。"]
recs = []
for i, t in enumerate(texts):
    rid = f"c{i:03d}"; sf.write(str(project.clips_dir / f"{rid}.wav"), y, sr)
    recs.append({"id": rid, "path": f"clips/{rid}.wav", "text": t, "lang": "zh", "duration": 4.0, "voiced": 3.4,
                 "keep": True, "split": "train", "asr_done": True, "source": "第1课", "start": i * 4.0, "end": i * 4.0 + 4})
project.save_manifest(recs)
if len(sys.argv) > 2 and sys.argv[2] == "use":
    list(A.WebUI(cfg).do_textfix("我的声音", None))
print("used:", wf.textfix_used(cfg, "我的声音"))
