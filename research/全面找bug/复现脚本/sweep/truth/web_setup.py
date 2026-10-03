import sys, os
from pathlib import Path
import numpy as np, soundfile as sf
sys.path.insert(0, "/home/user/literate-enigma")
root = Path(sys.argv[1]).resolve(); root.mkdir(parents=True, exist_ok=True)
(root / "config.yaml").write_text("workspace: ./ws\nbackend: dummy\nspeaker_encoder: mfcc\nprepare:\n  asr:\n    engine: none\n"
                                  "similarity:\n  model_dir: ./sv\n", encoding="utf-8")
os.chdir(root)
from voicetwin import workflows as wf
from voicetwin.config import load_config
cfg = load_config()
sr = 16000; tt = np.arange(int(3.0 * sr)) / sr
sig = (0.1 * np.sin(2 * np.pi * 150 * tt) * (np.abs(tt - 1.5) < 1.4)).astype(np.float32)
def mk(name, texts):
    project = wf.Project(cfg, name).ensure()
    recs = []
    for i, t in enumerate(texts):
        rid = f"c{i:03d}"; wav = project.clips_dir / f"{rid}.wav"; sf.write(str(wav), sig, sr)
        recs.append({"id": rid, "path": f"clips/{wav.name}", "text": t, "lang": "zh", "duration": 3.0, "voiced": 2.8,
                     "keep": True, "split": "train", "asr_done": bool(t), "source": "第1课", "start": i * 3.0, "end": i * 3.0 + 3})
    project.save_manifest(recs)
mk("我的声音", ["我们先来看艾子引导的定语从剧。", "关系代词that不能和借词一起提前。", "这个句子完全没有错。"])
mk("没文字", ["", "", ""])
print("ok")
