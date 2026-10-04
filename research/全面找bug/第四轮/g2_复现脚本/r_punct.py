# 复现 proofcheck#2 / appB#6：clean_transcript 把中文标点改坏
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]  # 仓库根目录
sys.path[:0] = [str(ROOT), str(ROOT / "tests")]
from voicetwin.utils.textutil import clean_transcript
for t in ["那么这个句子……我们先放一放。", "我们先放一放！！然后看下一个？！", "这个句子（定语从句），我们先放一放。",
          "他说“先放一放”，然后看下一个。", "你知道吗？？", "等一下…", "《语法》，很好。", "好的...", "那个...嗯",
          "Hello...world", "温度是3.5度。", "版本1.2.3里", "今天 我们 学习,好吗?", "We call f(x) here.", "which, 我们",
          "这是函数(function)的定义", "f(x), 然后"]:
    out = clean_transcript(t)
    print("SAME" if out == t else "DIFF", repr(t), "->", repr(out), "| twice ok" if clean_transcript(out) == out else "| NOT IDEMPOTENT")
