# 复现 proofcheck#5：英文例句说了两遍，删掉一遍以后「重复了 2 遍」还标着
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]  # 仓库根目录
sys.path[:0] = [str(ROOT), str(ROOT / "tests")]
from voicetwin.data import proofcheck as pc, review
for t, cur in [("I have a sister I have a sister who is a doctor.", "I have a sister who is a doctor."),
               ("翻译成英文就是I have a sister I have a sister who is a doctor。", "翻译成英文就是I have a sister who is a doctor。"),
               ("we need the the the answer here", "we need the the answer here"),
               ("we need the the the answer here", "we need the answer here"),
               ("定语从句定语从句很重要", "定语从句很重要"),
               ("I have a sister I have a sister who is a doctor.", "I have a brother I have a sister who is a doctor.")]:
    sus = pc.build_suspect(t)
    rec = {"id": "x", "text": t, "orig_text": t, "suspect": sus}
    info = review.analyze(rec, cur)
    print(repr(cur), "red:", [cur[s:e] for s, e in info["red"]], "active:", info["active"], "| fresh:", pc.build_suspect(cur))
