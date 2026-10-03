import json, sys, os
from pathlib import Path
import numpy as np, soundfile as sf
REPO = Path("/home/user/literate-enigma"); sys.path.insert(0, str(REPO))
root = Path(sys.argv[1]).resolve(); root.mkdir(parents=True, exist_ok=True)
(root / "config.yaml").write_text("workspace: ./ws\nbackend: dummy\nspeaker_encoder: mfcc\nprepare:\n  asr:\n    engine: none\n"
                                  "similarity:\n  model_dir: ./sv\n", encoding="utf-8")
os.chdir(root)
from voicetwin import workflows as wf
from voicetwin.config import load_config
cfg = load_config()
project = wf.Project(cfg, "我的声音").ensure()
sr = 16000; tt = np.arange(int(4.0 * sr)) / sr
f0 = 150 + 8 * np.sin(2 * np.pi * 0.7 * tt); phase = 2 * np.pi * np.cumsum(f0) / sr
voice = sum(np.sin(k * phase) / k for k in range(1, 12))
env = 0.5 * (1 - np.cos(2 * np.pi * 4 * tt)) * (np.abs(tt - 2) < 1.9)
wav = (0.15 * voice * env / np.max(np.abs(voice))).astype(np.float32)
texts = ["我们先来看定语从句。", "关系代词可以省略。", "这个句子的主语是什么？", "接下来我们讲一个例子。",
         "请大家注意这里的时态。", "这是一个非常常见的错误。", "我们再读一遍这个句子。", "下面做一个小练习。",
         "新课的第一句话在这里。", "新课的第二句话在这里。"]
recs = []
for i, t in enumerate(texts):
    cid = f"第{1 if i < 8 else 2}课_x_{i:04d}"
    p = project.clips_dir / f"{cid}.wav"; sf.write(str(p), wav, sr)
    recs.append({"id": cid, "path": f"clips/{p.name}", "text": t, "lang": "zh", "duration": 4.0, "voiced": 3.4,
                 "keep": True, "split": "train", "asr_done": True, "source": cid[:3], "start": float(i*4), "end": float(i*4+4)})
project.save_manifest(recs)
# 前 8 句已经用过一键全部文字校正（第 2 课的两句是新加的素材）
(Path(project.root) / "textfix_used.json").write_text(json.dumps({"used": True, "at": "x", "ids": [r["id"] for r in recs[:8]]},
                                                               ensure_ascii=False), encoding="utf-8")
print("ok", [r["id"] for r in recs[8:]])
