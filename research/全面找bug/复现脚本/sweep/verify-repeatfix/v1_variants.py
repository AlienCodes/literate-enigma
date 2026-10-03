"""变体：重复中间有标点 / 空格 / 英文单词，老师删掉多余的那遍以后红字还在吗？（当前代码）"""
import logging
from common import *
logging.disable(logging.CRITICAL)
cases = [
    ("定语从句定语从句很重要", "定语从句很重要"),            # reporter case (no gap)
    ("这个这个这个函数很重要", "这个这个函数很重要"),
    ("看看看这个例子", "看看这个例子"),
    ("定语从句，定语从句很重要", "定语从句很重要"),
    ("我们来看一下，我们来看一下这个例子", "我们来看一下这个例子"),
    ("我们来看一下我们来看一下这个例子", "我们来看一下这个例子"),
    ("这个，这个，这个函数很重要", "这个函数很重要"),
    ("这个 这个 这个函数很重要", "这个函数很重要"),
    ("the the the function is important", "the function is important"),
    ("我们讲 the the the 定语从句", "我们讲 the 定语从句"),
    ("Python Python Python 很好用", "Python 很好用"),
    ("这里的这里的这里的意思", "这里的意思"),
    ("非限制性定语从句，非限制性定语从句是什么", "非限制性定语从句是什么"),
]
for saved, fixed in cases:
    cfg, project = voice([saved])
    fake_engine({"c000": saved})
    pc.find_suspects(project, cfg)
    rec, t = cur(project, "c000")
    a0 = review.analyze(rec, t)
    before = [t[s:e] for s, e in a0["red"]]
    review.set_draft(project, "c000", text=fixed)
    rec, t = cur(project, "c000"); i1 = review.analyze(rec, t)
    review.save_rows(project)
    rec, t = cur(project, "c000"); i2 = review.analyze(rec, t)
    flag = "STAYS" if before and (i1["red"] or i2["red"]) else ("ok" if before else "not-marked")
    print(f"[{flag}] {saved!r} red={before} reasons0={a0['reasons']} -> {fixed!r}: unsaved red={[t[s:e] for s,e in i1['red']]} "
          f"saved red={[t[s:e] for s,e in i2['red']]} active={i2['active']} reasons={i2['reasons']} suspect_kept={'suspect' in rec}")
