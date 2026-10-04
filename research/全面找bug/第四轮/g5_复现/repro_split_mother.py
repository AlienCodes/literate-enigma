"""复查（第二次检查意见 synth#7）：硬切以后 chunk_sentence 又把几段并回一段，补的「，」落在一段中间（没有在那里切）。

用程序自带的母本（transcript_fix.builtin_mother()）：去掉标点，拼成 51–100 个音节、中间没有逗号的长句，
看 parse_script 以后有没有哪一段**中间**出现原文里没有的逗号，再看最短的一段有多短。
用法：VT_ROOT=<仓库目录> python repro_split_mother.py
"""
import os
import re
import sys

sys.path.insert(0, os.environ.get("VT_ROOT", str(__import__("pathlib").Path(__file__).resolve().parents[4])))
from voicetwin.data.lexicon_fix import has_jieba
from voicetwin.data.transcript_fix import builtin_mother
from voicetwin.synth.script import parse_script
from voicetwin.utils.textutil import syllable_count

print("jieba:", has_jieba())
S = "今天我们要讲的内容是关于现在完成时和一般过去时的区别以及它们在实际考试当中经常出现的各种各样的陷阱和常见错误。"
print("例句：", [s.display for s in parse_script(S)])

PUNCT = re.compile(r"[，。！？、；：,.!?;:“”\"'‘’（）()《》〈〉【】\[\]…—\-]+")


def strip_punct(t):
    """去掉标点；空格只留英文单词之间的（as which 不粘成 aswhich）。"""
    t = PUNCT.sub(" ", t)
    t = re.sub(r"(?<![A-Za-z0-9])\s+|\s+(?![A-Za-z0-9])", "", t)
    return re.sub(r"\s+", " ", t).strip()


pieces = [strip_punct(t) for _, t in builtin_mother()]
pieces = [p for p in pieces if p]
sents, cur = [], ""
for p in pieces:
    cur = cur + (" " if cur[-1:].isascii() and cur[-1:].isalnum() and p[:1].isascii() and p[:1].isalnum() else "") + p
    n = syllable_count(cur)
    if n > 100:
        cur = ""
    elif n > 50:
        sents.append(cur + "。")
        cur = ""
bad, shortest, examples = 0, [], []
for s in sents:
    segs = [x.display for x in parse_script(s)]
    inner = [d for d in segs if re.search(r"[，,].", d)]
    if inner:
        bad += 1
        if len(examples) < 6:
            examples.append(" | ".join(segs))
    shortest.append(min(syllable_count(d) for d in segs))
print(f"{len(sents)} 句里有 {bad} 句的某一段中间有原文里没有的逗号")
for e in examples:
    print("  ", e)
print("每句最短的一段（音节）：最小", min(shortest), "；不到 10 个音节的句子", sum(1 for x in shortest if x < 10))

# 在英文单词之间的空格处切开的句子（空格本来只是英文单词的分隔，不是停顿）
en_space = 0
for s in sents:
    segs = [x.display for x in parse_script(s)]
    if any(re.search(r"[A-Za-z0-9][，,]$", a) and re.match(r"[A-Za-z0-9]", b) for a, b in zip(segs, segs[1:])):
        en_space += 1
        if en_space <= 3:
            print("  英文单词中间切开：", " | ".join(segs))
print(f"{len(sents)} 句里有 {en_space} 句在两个英文单词之间切开")

# 每段都不超过 50 个音节、一个字都不丢（去掉切开处补的逗号和句号以后和原文一样）
over = lost = 0
for s in sents:
    segs = [x.display for x in parse_script(s)]
    over += sum(1 for d in segs if syllable_count(d) > 50)
    body = "".join(d[:-1] if i < len(segs) - 1 and d.endswith(("，", ",")) else d for i, d in enumerate(segs))
    lost += body.replace(" ", "") != s.replace(" ", "")
print(f"超过 50 个音节的段：{over}；和原文不一样（多了逗号或丢了字）的句子：{lost}")
