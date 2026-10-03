"""v18.5 浏览器实测的准备：用老师修缮前的 1004 句（research/文字校正/老师的母本/母本_原文.csv）建一个声音，
每句配一段 4 秒的合成声音（能点开试听，「确认训练素材」重新统计时也算能用）；放两条「自动查错字」的建议：
- 第 3 句：多一个「到」（两个引擎听得不一样的中文，标准库证明不了）→ 一键校正不自动采用，还是红色、有建议；
- 后面一句本来就对、有 which 的句子：把 which 写成「威驰」，自动查错字建议改回 which（读音像英文、不是常用词，
  标准库能证明）→ 一键校正一起采用。"""
import csv
import sys
from pathlib import Path

import numpy as np
import soundfile as sf

REPO = Path("/home/user/literate-enigma")
sys.path.insert(0, str(REPO))
root = Path(sys.argv[1]).resolve()
root.mkdir(parents=True, exist_ok=True)
(root / "config.yaml").write_text("workspace: ./ws\nbackend: dummy\nspeaker_encoder: mfcc\nprepare:\n  asr:\n    engine: none\n"
                                  "similarity:\n  model_dir: ./sv\n", encoding="utf-8")
import os  # noqa: E402

os.chdir(root)
from voicetwin import workflows as wf  # noqa: E402
from voicetwin.config import load_config  # noqa: E402

cfg = load_config()
project = wf.Project(cfg, "我的声音").ensure()
rows = list(csv.DictReader(open(REPO / "research/文字校正/老师的母本/母本_原文.csv", encoding="utf-8-sig")))
# 4 秒「像人声」的合成声音（150 Hz 的谐波 + 每秒 4 个音节的起伏）：静音的话「确认训练素材」重新统计时会判定都不能用
sr = 16000
tt = np.arange(int(4.0 * sr)) / sr
f0 = 150 + 8 * np.sin(2 * np.pi * 0.7 * tt)
phase = 2 * np.pi * np.cumsum(f0) / sr
voice = sum(np.sin(k * phase) / k for k in range(1, 12))
env = 0.5 * (1 - np.cos(2 * np.pi * 4 * tt)) * (np.abs(tt - 2) < 1.9)
silence = (0.15 * voice * env / np.max(np.abs(voice))).astype(np.float32)
recs = []
for i, r in enumerate(rows):
    wav = project.clips_dir / f"{r['id']}.wav"
    sf.write(str(wav), silence, sr)
    rec = {"id": r["id"], "path": f"clips/{wav.name}", "text": r["text"], "lang": "zh", "duration": 4.0,
           "voiced": 3.4, "keep": r["keep"] == "1", "split": "val" if i % 50 == 7 else "train", "asr_done": True,
           "source": "第1课", "start": float(i * 4), "end": float(i * 4 + 4)}
    if r["drop_reason"]:
        rec["drop_reason"] = r["drop_reason"]
    if r["drop_reason"] == "老师删除":
        rec["deleted"] = True
    recs.append(rec)
recs[2]["suspect"] = {"spans": [[0, 2]], "alt": "其次" + recs[2]["text"][2:].replace("最常见", "最常见到"), "reasons": ["测试用的自动查错字建议"],
                      "score": 0.7}
clean = {r["id"]: r["text"] for r in csv.DictReader(open(REPO / "research/文字校正/老师的母本/母本_修缮后.csv",
                                                           encoding="utf-8-sig"))}
k = next(i for i, r in enumerate(recs) if i > 3 and r["text"] == clean[r["id"]] and r.get("keep") and not r.get("deleted")
         and r["text"].count("which") == 1 and "威驰" not in r["text"])
at = recs[k]["text"].index("which")
good = recs[k]["text"]
recs[k]["text"] = good[:at] + "威驰" + good[at + 5:]
recs[k]["suspect"] = {"spans": [[at, at + 2]], "alt": good, "reasons": ["测试用的自动查错字建议（另一个引擎听到 which）"],
                      "score": 0.7}
print("威驰 →", recs[k]["id"])
project.save_manifest(recs)
project.export_csv(recs)
print("ok", len(recs))
