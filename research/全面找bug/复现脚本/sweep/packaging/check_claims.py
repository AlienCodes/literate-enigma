"""Spot-check the WHATS_NEW 18.5 examples: 借词→介词, 艾子→as, 关系带词→关系代词, 定语从剧→定语从句 are fixed;
「凭借词汇」 and 「原型」 are left alone."""
import sys
import os
VT_ROOT = os.environ.get("VT_ROOT", "/home/user/literate-enigma")  # repo checkout to test (for committed HEAD: git archive HEAD | tar -x -C <dir>)
sys.path.insert(0, VT_ROOT + "/research/文字校正/随机操作")
import h
from voicetwin import workflows as wf
texts = ["这个借词后面要接宾语。", "艾子这个关系代词比较特殊。", "这里的关系带词指代前面的先行词。", "这是一个定语从剧。",
         "我们凭借词汇的积累来理解句子。", "动词要还原成原型。"]
cfg, project = h.voice(texts, name="v")
r = wf.run_transcript_fix(cfg, "v", once=True)
for i, t in enumerate(texts):
    print(t, "->", h.cur(project, f"c{i:03d}")[1])
