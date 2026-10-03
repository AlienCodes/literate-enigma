"""文字校正（v18.5）的评测：逐字稿能不能找出识别错的字，会不会把老师当时换的说法当成错。

数据是开发时自己写的（不是老师的录音或文字）：
- 场景一「同一节课的讲稿」：逐字稿 = LECTURE_A（定语从句）；老师实际说的话 = SPOKEN_A（约三分之一的句子和讲稿不一样：
  多了「那、呢、啊、一下」，换了说法，改了页码）；识别出来的文字 = ASR_A（在老师实际说的话里放进识别错误）。
- 场景二「平时讲课的习惯」：逐字稿 = LECTURE_B（另一节课：名词性从句）；识别出来的是第三节课（状语从句，C 开头），
  逐字稿里没有这些句子，只有老师常说的话（同学们好、我们先来看一下、大家一定要记住……）。另外放了几句容易误报的句子。

放进去的识别错误分几种（和真实识别引擎常见的错一样）：
  near  读音很像、声调或者前后鼻音不一样的别字（定语 → 定于，宾语 → 冰语）
  same  读音完全一样的别字（最高级 → 最高集）
  style 读音一样、两种写法都常见（它 → 他）：按设计不标
  en    英文写成读音一样的词（there → their，know → no）
  cjk_en 英文被写成汉字（which → 维奇，reason → 瑞森）

运行：python research/文字校正/评测.py（在仓库根目录；装了 pypinyin 时才能查出读音相近的别字）
结果写到 research/文字校正/评测结果.txt。
"""

import difflib
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from voicetwin.data import transcript_fix as tf  # noqa: E402
from voicetwin.data.proofcheck import tokenize  # noqa: E402

LECTURE_A = """同学们好，今天我们来讲定语从句。
定语从句在高考里几乎每年都会考到，所以大家一定要认真听。
首先我们要知道什么是定语。
定语就是用来修饰名词或者代词的成分。
比如 a beautiful girl，这里的 beautiful 就是定语。
那如果用一个句子来修饰名词，这个句子就叫做定语从句。
被修饰的那个名词，我们叫它先行词。
引导定语从句的词叫做关系词，关系词分为关系代词和关系副词。
常见的关系代词有 who、whom、whose、which 和 that。
常见的关系副词有 when、where 和 why。
我们先来看第一个例句。
The girl who is standing there is my sister.
在这个句子里，先行词是 the girl，关系代词是 who。
who 在从句里面做主语，所以不能省略。
大家注意，关系代词在从句中做宾语的时候是可以省略的。
比如 This is the book that I bought yesterday.
这里的 that 在从句里做 bought 的宾语，所以可以省掉。
接下来我们看 that 和 which 的区别。
当先行词是物的时候，that 和 which 一般都可以用。
但是有几种情况只能用 that，不能用 which。
第一种情况，先行词是不定代词的时候，比如 all、everything、nothing。
第二种情况，先行词被序数词或者最高级修饰的时候。
第三种情况，先行词既有人又有物的时候。
反过来，也有只能用 which 不能用 that 的情况。
最常见的就是非限制性定语从句，也就是前面有逗号隔开的。
还有一种情况是关系词前面有介词的时候，要用 which。
下面我们来讲 as 引导的定语从句。
as 引导的定语从句可以放在句首，也可以放在句中或者句末。
比如 As we all know, the earth is round.
这里的 as 指代的是后面整个句子的内容。
很多同学容易把 as 和 which 搞混，我们来对比一下。
which 引导的非限制性定语从句只能放在主句后面。
而 as 引导的从句位置比较灵活，前面后面都可以。
好，我们来做几道练习题巩固一下。
请大家翻到课本第三十五页，看第二大题。
第一小题，空格前面的先行词是 the reason。
很多同学看到 reason 就选 why，这是不对的。
我们要看从句里面缺不缺成分。
如果从句缺主语或者宾语，就要用关系代词 that 或者 which。
如果从句不缺成分，才用关系副词 why。
这个是考试的高频考点，大家一定要记住。
最后我们来总结一下今天的内容。
判断用什么关系词，关键是看先行词和从句里缺什么成分。
回去以后把今天的笔记整理一下，下节课我们讲名词性从句。
好，今天就讲到这里，下课。"""

# (老师实际说的话, 识别出来的文字, 放进去的错误种类)。实际说的话和讲稿不一样的句子后面写了「改口」。
CASES_A = [
    ("同学们好，那今天呢我们来讲一下定语从句。", "同学们好，那今天呢我们来讲一下定于从句。", "near"),  # 改口
    ("定语从句在高考里几乎每年都会考到，所以大家一定要认真听。", "定语从句在高考里几乎每年都会考到，所以大家一定要认真听。", ""),
    ("首先呢我们要知道什么是定语。", "首先呢我们要知道什么是定雨。", "same"),  # 改口
    ("定语就是用来修饰名词或者代词的成分。", "定语就是用来修饰名词或者代词的成分。", ""),
    ("比如 a beautiful girl，这里的 beautiful 就是定语。", "比如 a beautiful 格尔，这里的 beautiful 就是定语。", "cjk_en"),
    ("那如果我们用一个句子来修饰名词，这个句子就叫做定语从句。", "那如果我们用一个句子来修饰名词，这个句子就叫做定语从句。", ""),  # 改口
    ("被修饰的这个名词，我们把它叫做先行词。", "被修饰的这个名词，我们把他叫做先行次。", "style+near"),  # 改口
    ("引导定语从句的词叫做关系词，关系词分为关系代词和关系副词。", "因导定语从句的词叫做关系词，关系词分为关系代词和关系副词。", "near"),
    ("常见的关系代词有 who、whom、whose、which 和 that。", "常见的关系代词有 who、whom、who's、which 和 that。", "en"),
    ("常见的关系副词有 when、where 和 why。", "常见的关系副词有 when、where 和 why。", ""),
    ("我们先来看第一个例句啊。", "我们先来看第一个例句啊。", ""),  # 改口
    ("The girl who is standing there is my sister.", "The girl who is standing their is my sister.", "en"),
    ("在这个句子里，先行词是 the girl，关系代词是 who。", "在这个句子里，鲜行词是 the girl，关系代词是 who。", "same"),
    ("who 在从句里面是做主语的，所以不能省略。", "who 在从句里面是做猪语的，所以不能省略。", "near"),  # 改口
    ("大家注意，关系代词在从句中做宾语的时候是可以省略的。", "大家注意，关系代词在从句中做宾鱼的时候是可以省略的。", "near"),
    ("比如 This is the book that I bought yesterday.", "比如 This is the book that I boat yesterday.", "en"),
    ("这里的 that 在从句里做 bought 的宾语，所以可以省略。", "这里的 that 在从句里做 bought 的冰语，所以可以省略。", "near"),  # 改口
    ("接下来我们看 that 和 which 的区别。", "接下来我们看 that 和 which 的区别。", ""),
    ("当先行词是指物的时候，that 和 which 一般都可以用。", "当先行词是指物的时候，that 和维奇一般都可以用。", "cjk_en"),  # 改口
    ("但是有几种情况只能用 that，不能用 which。", "但是有几种情况只能用 that，不能用 which。", ""),
    ("第一种情况，先行词是不定代词的时候，比如 all、everything、nothing。",
     "第一种情况，先行词是不定代词的时候，比如 all、everything、nothing。", ""),
    ("第二种情况，先行词被序数词或者最高级修饰的时候。", "第二种情况，先行词被序数词或者最高集修饰的时候。", "same"),
    ("第三种情况，先行词既有人又有物的时候。", "第三种情况，先行词既有人又有物的时候。", ""),
    ("反过来说，也有只能用 which 不能用 that 的情况。", "反过来说，也有只能用 which 不能用 that 的情况。", ""),  # 改口
    ("最常见的就是非限制性定语从句，也就是前面有逗号隔开的。", "最常见的就是非现制性定语从句，也就是前面有逗号隔开的。", "same"),
    ("还有一种情况是关系词前面有介词的时候，要用 which。", "还有一种情况是关系词前面有借词的时候，要用 which。", "same"),
    ("下面我们来看 as 引导的定语从句。", "下面我们来看艾子引导的定语从句。", "cjk_en"),  # 改口
    ("as 引导的定语从句可以放在句首，也可以放在句中或者句末。", "as 引导的定语从句可以放在句手，也可以放在句中或者句末。", "same"),
    ("比如 As we all know, the earth is round.", "比如 As we all no, the earth is round.", "en"),
    ("这里的 as 指代的是后面整个句子的内容。", "这里的 as 只代的是后面整个句子的内容。", "same"),
    ("很多同学呢容易把 as 和 which 搞混，我们对比一下。", "很多同学呢容易把 as 和 which 搞浑，我们对比一下。", "near"),  # 改口
    ("which 引导的非限制性定语从句只能放在主句后面。", "which 引导的非限制性定语从句只能放在主剧后面。", "same"),
    ("而 as 引导的从句位置比较灵活，前面后面都可以。", "而 as 引导的从句位置比较零活，前面后面都可以。", "same"),
    ("好，下面我们来做几道练习题。", "好，下面我们来做几道练习题。", ""),  # 改口
    ("请大家翻到课本第三十六页，看第二大题。", "请大家翻到课本第三十六页，看第二大题。", ""),  # 改口（页码）
    ("第一小题，空格前面的先行词是 the reason。", "第一小题，空格前面的先行词是 the 瑞森。", "cjk_en"),
    ("很多同学看到 reason 就选 why，这是不对的。", "很多同学看到 reason 就选外，这是不对的。", "cjk_en"),
    ("我们要看从句里面缺不缺成分。", "我们要看从句里面缺不缺程分。", "same"),
    ("如果从句缺主语或者宾语，就要用关系代词 that 或者 which。", "如果从句缺主语或者宾语，就要用关系带词 that 或者 which。", "same"),
    ("如果从句不缺成分，才用关系副词 why。", "如果从句不缺成分，才用关系复词 why。", "same"),
    ("这个是高考的高频考点，大家一定要记住。", "这个是高考的高频靠点，大家一定要记住。", "near"),  # 改口
    ("最后我们来总结一下今天的内容。", "最后我们来总结一下今天的内容。", ""),
    ("判断用什么关系词，关键是看先行词和从句里缺什么成分。", "判断用什么关系词，关键是看先行此和从句里缺什么成分。", "near"),
    ("回去以后把今天的笔记整理一下，下节课我们讲名词性从句。", "回去以后把今天的笔记整理一下，下节课我们讲明词性从句。", "same"),
    ("好，今天就讲到这里，下课。", "好，今天就讲到这里，下课。", ""),
]

LECTURE_B = """同学们好，上节课我们讲了定语从句，今天我们来讲名词性从句。
名词性从句包括主语从句、宾语从句、表语从句和同位语从句。
我们先来看一下宾语从句。
宾语从句就是在句子里做宾语的从句。
比如 I know that he is a good teacher.
这里的 that 引导的从句做 know 的宾语。
大家注意，宾语从句要用陈述句的语序。
很多同学容易在这里出错，把语序写成疑问句的语序。
接下来我们看主语从句。
主语从句经常用 it 做形式主语，把真正的主语放到后面。
比如 It is important that we should study hard.
这个句子里，it 是形式主语，that 引导的从句才是真正的主语。
下面我们来对比一下同位语从句和定语从句。
同位语从句是解释说明前面名词的内容，而定语从句是修饰限制先行词的。
同位语从句里面 that 不做成分，定语从句里面关系代词要做成分。
这是一个高频考点，大家一定要记住。
好，我们来做一下练习，请大家翻到课本第四十页。
最后我们来总结一下，判断从句的类型关键是看它在句子里做什么成分。
回去以后把笔记整理一下，下节课我们讲状语从句。"""

CASES_C = [
    ("同学们好，上节课我们讲了名词性从句，今天我们来讲状语从句。", "同学们好，上节课我们将了名词性从句，今天我们来讲状语从句。", "near"),
    ("状语从句就是在句子里做状语的从句。", "状语从句就是在句子里做状语的从句。", ""),
    ("状语从句分为时间、地点、原因、条件、让步等等。", "状语从句分为时间、地点、原因、条件、让步等等。", ""),
    ("我们先来看一下时间状语从句。", "我们先来砍一下时间状语从句。", "near"),
    ("引导时间状语从句的连词有 when、while、before 和 after。", "引导时间状语从句的连词有温、while、before 和 after。", "cjk_en"),
    ("大家注意，when 和 while 的用法是有区别的。", "大家主意，when 和 while 的用法是有区别的。", "near"),
    ("很多同学容易在这里出错，把 when 和 while 搞混。", "很多同学容一在这里出错，把 when 和 while 搞混。", "near"),
    ("接下来我们看原因状语从句。", "接下来我们看原因状语从句。", ""),
    ("原因状语从句常用 because、since 和 as 来引导。", "原因状语从句常用 because、since 和艾子来引导。", "cjk_en"),
    ("这是一个高频考点，大家一定要记住。", "这是一个高频靠点，大家一定要记住。", "near"),
    ("好，我们来做一下练习，请大家翻到课本第五十页。", "好，我们来做一下联系，请大家翻到课本第五十页。", "near"),
    ("最后我们来总结一下，判断状语从句的类型要看连词的意思。", "最后我们来宗结一下，判断状语从句的类型要看连词的意思。", "near"),
    ("回去以后把笔记整理一下，下节课我们讲倒装句。", "回去以后把笔记正理一下，下节课我们讲倒装句。", "near"),
    # 容易误报的句子（识别是对的，只是和逐字稿里的说法读音相近）
    ("我们来联系一下家长，问问孩子在家的情况。", "我们来联系一下家长，问问孩子在家的情况。", ""),
    ("这是一个很重要的事实。", "这是一个很重要的事实。", ""),
    ("他的这个主意很好。", "他的这个主意很好。", ""),
    ("今天天气很好，我们出去走走。", "今天天气很好，我们出去走走。", ""),
    ("他们在讨论这个问题的时候很认真。", "他们在讨论这个问题的时候很认真。", ""),
    ("请大家把作业交上来。", "请大家把作业交上来。", ""),
]


def keys(s):
    return [t.key for t in tokenize(s)]


def truth_diffs(asr, spoken):
    """识别文字和实际说的话不一样的地方（按字 / 词比，标点不算）：[(开始, 结束, 应该是)]，位置是识别文字里的。"""
    A, B = tokenize(asr), tokenize(spoken)
    out = []
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, [x.key for x in A], [x.key for x in B],
                                                       autojunk=False).get_opcodes():
        if tag == "equal":
            continue
        s = A[i1].start if i1 < len(A) else len(asr)
        e = A[i2 - 1].end if i2 > i1 else s
        out.append((s, e, spoken[B[j1].start:B[j2 - 1].end] if j2 > j1 else ""))
    return out


def evaluate(name, ref_text, cases, lines):
    ref = tf.Reference(ref_text)
    tp = wrong = fp = 0
    missed = []
    by_kind = {}
    t0 = time.time()
    for spoken, asr, kind in cases:
        res = tf.check_text(asr, ref)
        toks = tf.tokens(asr)
        props = [(toks[p.i1].start, toks[p.i2 - 1].end, p.rep, p.kind, p.mode) for p in res.props]
        diffs = truth_diffs(asr, spoken)
        hit = set()
        for s, e, rep, pk, mode in props:
            over = [k for k, (a, b, _) in enumerate(diffs) if s < max(b, a + 1) and a < e]
            if not over:
                fp += 1
                lines.append(f"  ✗ 误报：{asr}  「{asr[s:e]}」→「{rep}」（{pk}/{mode}）")
                continue
            fixed = asr[:s] + rep + asr[e:]
            if len(truth_diffs(fixed, spoken)) == len(diffs) - len(over):
                tp += 1
                hit.update(over)
                lines.append(f"  ✓ 找到：「{asr[s:e]}」→「{rep}」（{pk}/{mode}）")
            else:
                wrong += 1
                hit.update(over)
                lines.append(f"  △ 位置对、建议不对：「{asr[s:e]}」→「{rep}」，应该是「{diffs[over[0]][2]}」")
        for k, (a, b, r) in enumerate(diffs):
            kinds = kind.split("+")
            kd = kinds[min(k, len(kinds) - 1)] if kinds and kinds[0] else "?"
            by_kind.setdefault(kd, [0, 0])
            by_kind[kd][1] += 1
            if k in hit:
                by_kind[kd][0] += 1
            else:
                missed.append((kd, asr, asr[a:b], r))
    secs = time.time() - t0
    n_err = sum(v[1] for v in by_kind.values())
    lines.insert(0, "")
    head = [f"## {name}",
            f"逐字稿 {len(ref)} 个字/词；识别文字 {len(cases)} 句；放进去的错误 {n_err} 处；用时 {secs:.2f} 秒",
            f"找到并且建议正确 {tp} 处；位置对但建议不对 {wrong} 处；误报 {fp} 处"]
    for kd in sorted(by_kind):
        f, t = by_kind[kd]
        head.append(f"  {kd:7s} 找到 {f} / {t}")
    if missed:
        head.append("没找到的：")
        head += [f"  - [{kd}] {asr}  「{a}」应该是「{r}」" for kd, asr, a, r in missed]
    return head + ["逐条：", *lines[1:]], {"tp": tp, "wrong": wrong, "fp": fp, "by_kind": by_kind}


def false_alarms(lines):
    """没有识别错误的句子（老师实际说的话）和逐字稿比：标出来的全是误报。两个逐字稿、两组句子交叉比。"""
    out = ["## 场景三：没有任何识别错误的句子（标出来的都算误报）"]
    total = 0
    for rname, rtext in (("逐字稿 A", LECTURE_A), ("逐字稿 B", LECTURE_B), ("逐字稿 A+B", LECTURE_A + "\n" + LECTURE_B)):
        ref = tf.Reference(rtext)
        for cname, cases in (("A 组", CASES_A), ("C 组", CASES_C)):
            n = 0
            for spoken, _asr, _k in cases:
                res = tf.check_text(spoken, ref)
                toks = tf.tokens(spoken)
                for p in res.props:
                    n += 1
                    lines.append(f"  ✗ {rname} / {cname}：{spoken}  「{spoken[toks[p.i1].start:toks[p.i2 - 1].end]}」→「{p.rep}」"
                                 f"（{p.kind}/{p.mode}）")
            total += n
            out.append(f"  {rname} 和 {cname} 的 {len(cases)} 句比：误报 {n} 处")
    out.append(f"合计误报 {total} 处")
    return out + lines, total


def speed():
    """速度：逐字稿 ≈ 4.5 万字 / 词（两节课的讲稿重复 40 遍，每遍改几个字），1000 句识别文字。"""
    parts = []
    for k in range(40):
        parts.append(LECTURE_A.replace("同学们好", f"同学们好，这是第{k}次课") + "\n" + LECTURE_B)
    big = "\n".join(parts)
    t0 = time.time()
    ref = tf.Reference(big)
    t1 = time.time()
    asr = [c[1] for c in CASES_A + CASES_C]
    for i in range(1000):
        tf.check_text(asr[i % len(asr)], ref)
    t2 = time.time()
    return [f"## 速度：逐字稿 {len(ref)} 个字/词，处理逐字稿用 {t1 - t0:.1f} 秒；比对 1000 句用 {t2 - t1:.1f} 秒"]


def main():
    out = [f"文字校正评测（{time.strftime('%Y-%m-%d %H:%M')}，pypinyin：{'有' if tf.has_pinyin() else '没有'}）"]
    a, ra = evaluate("场景一：逐字稿就是这节课的讲稿（三分之一的句子老师改了口）", LECTURE_A, CASES_A, [])
    c, rc = evaluate("场景二：逐字稿只是平时讲课的习惯（另一节课的讲稿）", LECTURE_B, CASES_C, [])
    f, nf = false_alarms([])
    out += [""] + a + [""] + c + [""] + f + [""] + speed()
    text = "\n".join(out) + "\n"
    print(text)
    (Path(__file__).parent / ("评测结果.txt" if tf.has_pinyin() else "评测结果_没有pypinyin.txt")).write_text(
        text, encoding="utf-8")
    return ra, rc, nf


if __name__ == "__main__":
    main()
