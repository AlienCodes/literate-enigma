"""「一模一样」挑模型时用的检查用的句子（设计方案 research/一模一样/设计方案原文.md §1.3、§2 P8）。

挑模型主要靠你没参加训练的真实录音（验证集，最多 20 句：有真实录音，能和你本人直接比）。可验证集里问句、
带英文例句的句子、特别长的句子往往很少，所以另外加 24 句只有文字、没有录音的句子，专门看模型在这几种句子上稳不稳：
- 8 句问句（句末的语气）；
- 8 句中文里夹着英文例句的句子（老师讲课最常见的「中英夹在一起」）；
- 8 句 40 个音节以上的长句（长句子容易漏读、重复、越读越快）。

都是通用的讲课句子，没有任何个人信息；改这里的句子会让以前挑选时存下的结果作废（缓存键里有文字）。
"""

from __future__ import annotations

from typing import Dict, List

#: 每句：id（缓存和报告里用，不要改）、kind（question 问句 / mixed 夹着英文 / long 长句）、text
TEST_TEXTS: List[Dict[str, str]] = [
    # ---------------------------------------------------------------- 8 句问句
    {"id": "q1", "kind": "question", "text": "你们觉得这道题应该怎么做呢？"},
    {"id": "q2", "kind": "question", "text": "大家想一想，为什么这里要用过去完成时呢？"},
    {"id": "q3", "kind": "question", "text": "这个句子的主语到底是哪一个呢？"},
    {"id": "q4", "kind": "question", "text": "有没有同学能告诉我，这两个词有什么区别？"},
    {"id": "q5", "kind": "question", "text": "如果把这个词换掉，句子的意思会变吗？"},
    {"id": "q6", "kind": "question", "text": "上节课我们讲的那个规则，大家还记得吗？"},
    {"id": "q7", "kind": "question", "text": "这里为什么不能用现在进行时呢？"},
    {"id": "q8", "kind": "question", "text": "你们能不能自己再举一个类似的例子？"},
    # ---------------------------------------------------------------- 8 句中文里夹着英文例句
    {"id": "m1", "kind": "mixed", "text": "这句话翻译成英文就是 I have been waiting for you since this morning."},
    {"id": "m2", "kind": "mixed", "text": "我们来看这个例句：She said that she would come back tomorrow."},
    {"id": "m3", "kind": "mixed", "text": "这里的 which 引导的是一个非限定性定语从句。"},
    {"id": "m4", "kind": "mixed", "text": "注意，as soon as 后面要用一般现在时来表示将来。"},
    {"id": "m5", "kind": "mixed",
     "text": "比如说 The book that I bought yesterday is very interesting，这里的 that 可以省略。"},
    {"id": "m6", "kind": "mixed", "text": "大家记住这个固定搭配：look forward to doing something。"},
    {"id": "m7", "kind": "mixed", "text": "如果主语是 everyone，后面的动词要用单数形式。"},
    {"id": "m8", "kind": "mixed", "text": "这个单词 important 的重音在第二个音节上。"},
    # ---------------------------------------------------------------- 8 句 40 个音节以上的长句
    {"id": "l1", "kind": "long",
     "text": "今天这节课我们先把上次留下的几个问题再梳理一遍，然后再用几个新的例子把这个语法规则彻底讲清楚，"
             "大家跟着我的思路一步一步来。"},
    {"id": "l2", "kind": "long",
     "text": "在做阅读理解的时候，我们不要一看到不认识的单词就停下来，而是要先根据上下文去猜它大概的意思，"
             "这样读起来才会又快又准。"},
    {"id": "l3", "kind": "long",
     "text": "很多同学在写作文的时候喜欢用很长很复杂的句子，其实只要把意思表达清楚，简单的句子反而更容易拿到高分，"
             "这一点大家一定要记住。"},
    {"id": "l4", "kind": "long",
     "text": "这个规则看起来有点复杂，但是只要我们把它拆成三个小步骤，先找主语，再找谓语，最后看时间状语，"
             "就会发现其实一点都不难。"},
    {"id": "l5", "kind": "long",
     "text": "下面我们来做几道练习题，每道题大家先自己想一分钟，然后我再把答案和解题的思路给大家讲一讲，"
             "有不明白的地方随时可以问我。"},
    {"id": "l6", "kind": "long",
     "text": "复习的时候不要只是把笔记从头到尾看一遍，更好的办法是合上书本，试着把今天学过的内容自己讲出来，"
             "讲不出来的地方就是需要再看的地方。"},
    {"id": "l7", "kind": "long",
     "text": "我们平时说话的时候，经常会把一些词连在一起读，所以听力考试里听到的发音和单词本来的样子不太一样，"
             "这需要大家多听多练才能适应。"},
    {"id": "l8", "kind": "long",
     "text": "最后给大家布置一下今天的作业，把课本上这一单元的课文朗读三遍，然后把后面的十个句子翻译成中文，"
             "下次上课的时候我们一起检查。"},
]

#: 长句至少要有多少个音节（设计方案：40 个以上）
LONG_MIN_SYLLABLES = 40


def probe_items(n: int = 24) -> List[Dict[str, str]]:
    """挑模型用的前 n 句检查用的句子（n 大于 24 时也只有 24 句）。三种句子轮流取，n 小于 24 时三种都有。"""
    n = max(0, min(int(n), len(TEST_TEXTS)))
    by_kind: Dict[str, List[Dict[str, str]]] = {}
    for t in TEST_TEXTS:
        by_kind.setdefault(t["kind"], []).append(t)
    out: List[Dict[str, str]] = []
    k = 0
    while len(out) < n:
        for kind in ("question", "mixed", "long"):
            group = by_kind.get(kind) or []
            if k < len(group) and len(out) < n:
                out.append(dict(group[k], lang="zh"))
        k += 1
    return out
