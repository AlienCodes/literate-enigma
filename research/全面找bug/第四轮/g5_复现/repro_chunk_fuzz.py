"""复查（第二次检查意见 synth#7）：随机拼的怪句子（有的分句有逗号、有的没有；英文、数字、网址、很长的单词、
全角空格、表情、括号）× 5 种上限，看 chunk_sentence 切出来的段：
  - 超过上限的段、空的段；
  - 拼回去和原文不一样（空白不算）：只有不是最后一段的末尾可以多一个逗号（真的切开的地方），别的地方多了逗号或者丢了字都算。
用法：VT_ROOT=<仓库目录> python repro_chunk_fuzz.py [随机种子]
"""
import os
import random
import re
import sys
import time

sys.path.insert(0, os.environ.get("VT_ROOT", str(__import__("pathlib").Path(__file__).resolve().parents[4])))
from voicetwin.synth.script import chunk_sentence
from voicetwin.utils.textutil import syllable_count


def inserted_commas(source, pieces):
    src, pos = re.sub(r"\s", "", source), 0
    for i, p in enumerate(pieces):
        p = re.sub(r"\s", "", p)
        if src.startswith(p, pos):
            pos += len(p)
        elif i < len(pieces) - 1 and p[-1:] in "，," and src.startswith(p[:-1], pos):
            pos += len(p) - 1
        else:
            return [p]
    return [] if pos == len(src) else [src[pos:]]


rng = random.Random(int(sys.argv[1]) if len(sys.argv) > 1 else 0)
words = ["我们", "一起", "来看", "这个", "句子", "先行词", "the", "beautiful", "interesting", "book", "特别", "注意",
         " ", "  ", "　", "3.14159", "2024年", "Python3", "错误", "形容词", "，", "which", "we", "know", "such", "as",
         "https://example.com/abc", "supercalifragilisticexpialidocious", "「定语从句」", "😀", "、", "（括号）", "-", "'"]
t0, n, over, ins, empty, examples = time.time(), 0, 0, 0, 0, []
for _ in range(1200):
    s = "".join(rng.choice(words) for _ in range(rng.randint(5, 120))).strip(" ，　") + rng.choice(["。", "", "!"])
    s = re.sub(r"，[\s，]*", "，", s)
    if not s.strip():
        continue
    for mx in (6, 12, 20, 45, 50):
        n += 1
        chunks = chunk_sentence(s, mx)
        o = [c for c in chunks if syllable_count(c) > mx]
        b = inserted_commas(s, chunks)
        e = [c for c in chunks if not c.strip()]
        over, ins, empty = over + bool(o), ins + bool(b), empty + bool(e)
        if (o or b) and len(examples) < 3:
            examples.append((mx, o[:1], b[:1]))
print(f"{n} 次切分：有段超过上限 {over} 次；多了逗号或丢了字 {ins} 次；有空段 {empty} 次（{time.time() - t0:.0f} 秒）")
for x in examples:
    print("  例：上限", x[0], "超过上限的段", x[1], "出问题的段", x[2])
