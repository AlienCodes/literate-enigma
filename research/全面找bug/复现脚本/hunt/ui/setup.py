"""Build a small test voice (dummy backend) in <root>; N rows from the teacher's mother text."""
import csv, os, sys
from pathlib import Path
import numpy as np, soundfile as sf
REPO = Path("/home/user/literate-enigma")
sys.path.insert(0, str(REPO))
root = Path(sys.argv[1]).resolve()
N = int(sys.argv[2]) if len(sys.argv) > 2 else 40
voice_name = sys.argv[3] if len(sys.argv) > 3 else "我的声音"
root.mkdir(parents=True, exist_ok=True)
(root / "config.yaml").write_text("workspace: ./ws\nbackend: dummy\nspeaker_encoder: mfcc\nprepare:\n  asr:\n    engine: none\n"
                                  "similarity:\n  model_dir: ./sv\n", encoding="utf-8")
os.chdir(root)
from voicetwin import workflows as wf
from voicetwin.config import load_config
cfg = load_config()
project = wf.Project(cfg, voice_name).ensure()
rows = list(csv.DictReader(open(REPO / "research/文字校正/老师的母本/母本_原文.csv", encoding="utf-8-sig")))[:N]
sr = 16000
tt = np.arange(int(4.0 * sr)) / sr
f0 = 150 + 8 * np.sin(2 * np.pi * 0.7 * tt)
phase = 2 * np.pi * np.cumsum(f0) / sr
v = sum(np.sin(k * phase) / k for k in range(1, 12))
env = 0.5 * (1 - np.cos(2 * np.pi * 4 * tt)) * (np.abs(tt - 2) < 1.9)
sig = (0.15 * v * env / np.max(np.abs(v))).astype(np.float32)
recs = []
for i, r in enumerate(rows):
    wav = project.clips_dir / f"{r['id']}.wav"
    sf.write(str(wav), sig, sr)
    rec = {"id": r["id"], "path": f"clips/{wav.name}", "text": r["text"], "lang": "zh", "duration": 4.0,
           "voiced": 3.4, "keep": r["keep"] == "1", "split": "val" if i % 10 == 7 else "train", "asr_done": True,
           "source": "第1课", "start": float(i * 4), "end": float(i * 4 + 4)}
    if r["drop_reason"]:
        rec["drop_reason"] = r["drop_reason"]
    if r["drop_reason"] == "老师删除":
        rec["deleted"] = True
    recs.append(rec)
recs[2]["suspect"] = {"spans": [[0, 2]], "alt": "其次" + recs[2]["text"][2:], "reasons": ["测试"], "score": 0.7}
project.save_manifest(recs)
project.export_csv(recs)
print("ok", len(recs), project.root)
