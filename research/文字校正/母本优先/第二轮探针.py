"""母本优先第二轮：检查的人用的几个「探针」，一句一句直接调 transcript_fix._mother_first（单独一句、片段 id 是新的、
没有前后的句子 = 当成新讲的课 / 没有同一批录音的证据）。量的是「直接按母本改掉了几句」。

1. 换词：母本的句子换一个语法术语（定语从句 ↔ 状语从句、关系代词 → 关系副词、which / as / that、主语 ↔ 宾语……）；
2. 换说法：那么 → 那、就是 → 是、去掉「的话 / 其实」、我们 → 咱们；
3. 短的常说的话（「我们再看一个例句」）；
4. 母本的一句 + 后面几个母本里没有的字（「今天我们」）：后面的字被改掉的句数；
5. 母本的一句前面加几个字（「今天的」）：前面的字被改掉的句数；
6. 和母本不一样的 123 句（修缮以前的识别文字），单独 / 后面跟一句新的话 / 前面有一句新的话：改得和修缮好的一模一样的句数；
7. 在任意两个汉字中间切开的半句（不在标点处）：本来对的半句被改的句数（标点）、有错的改对的句数。

运行：PYTHONPATH=. /tmp/gsv39/bin/python research/文字校正/母本优先/第二轮探针.py <名字>
  （VT_CODE=<另一份代码的文件夹>：用那份代码量）→ 第二轮探针结果_<名字>.txt
"""

import csv
import difflib
import os
import random
import re
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
CODE = Path(os.environ.get("VT_CODE") or ROOT)
sys.path.insert(0, str(CODE))
sys.path.insert(0, str(HERE))

from voicetwin.data import transcript_fix as tf  # noqa: E402
from voicetwin.utils.textutil import clean_transcript as norm  # noqa: E402

from 实测 import NEW_CONTENT  # noqa: E402

D = ROOT / "research" / "文字校正" / "老师的母本"
ORIG = list(csv.DictReader(open(D / "母本_原文.csv", encoding="utf-8-sig")))
CLEAN = {r["id"]: r["text"] for r in csv.DictReader(open(D / "母本_修缮后.csv", encoding="utf-8-sig"))}
NEW_ID = "9999_new000_0000"


def fix(ref, row):
    fixes, cov, _snip, _full = tf._mother_first(row, NEW_ID, ref, (row,))
    return tf._apply(row, [(f.start, f.end, f.rep) for f in fixes if f.direct]), bool(cov)


def main():
    label = sys.argv[1] if len(sys.argv) > 1 else "新代码"
    t0 = time.time()
    builtin = list(tf.builtin_mother())
    ref = tf.Reference(builtin, own_from=len(builtin), vetted_lines=len(builtin))
    texts = [x for _, x in builtin]
    out = [f"母本优先第二轮探针（{label}，代码：{CODE}，{time.strftime('%Y-%m-%d %H:%M')}，"
           f"pypinyin：{'有' if tf.has_pinyin() else '没有'}）", ""]

    subs = [("定语从句", "状语从句"), ("状语从句", "定语从句"), ("主语", "宾语"), ("宾语", "主语"), ("关系代词", "关系副词"),
            ("which", "that"), ("that", "which"), ("as", "which"), ("非限定性", "限定性"), ("先行词", "主句"),
            ("第一", "第二"), ("中文", "英文"), ("英文", "中文"), ("名词", "动词"), ("过去", "现在")]
    tot = changed = 0
    ex = []
    for text in texts:
        for a, b in subs:
            if a.isascii():
                if not re.search(r"(?<![A-Za-z])%s(?![A-Za-z])" % a, text):
                    continue
                new = re.sub(r"(?<![A-Za-z])%s(?![A-Za-z])" % a, b, text, count=1)
            else:
                if a not in text:
                    continue
                new = text.replace(a, b, 1)
            if new == text or new in texts:
                continue
            tot += 1
            got, _c = fix(ref, new)
            if got != new:
                changed += 1
                ex.append(f"{new[:40]} → {got[:40]}")
            break
    out.append(f"1. 换词（新讲的课）：{tot} 句，被直接改掉 {changed} 句" + (f"；例如 {ex[0]}" if ex else ""))

    tot = changed = 0
    for text in texts:
        for a, b in (("那么", "那"), ("就是", "是"), ("的话", ""), ("其实", ""), ("我们", "咱们")):
            if a in text:
                new = text.replace(a, b, 1)
                if new in texts:
                    break
                tot += 1
                changed += int(fix(ref, new)[0] != new)
                break
    out.append(f"2. 换说法（新讲的课）：{tot} 句，被直接改掉 {changed} 句")

    pieces = []
    for s in NEW_CONTENT:
        for p in re.split(r"[，。,？！、]", s):
            p = p.strip()
            if 4 <= len(tf.tokens(p)) <= 12:
                pieces.append(p)
    pieces += ["好，我们来看第二道题", "我们来看下一个例子", "这是一个非常重要的知识点", "大家先自己做一下", "这道题选C",
               "答案是B", "我们来翻译一下这句话", "这里的it是形式主语", "这个句子的主语是什么呢", "这个词是一个副词",
               "注意这里是复数", "所以这里要用过去式", "我们再看一个例句", "这句话翻译成中文就是", "这里的that不能省略",
               "它在从句中作宾语", "下面我们来做一道练习"]
    changed = [p for p in pieces if fix(ref, p)[0] != p]
    out.append(f"3. 短的常说的话：{len(pieces)} 句，被直接改掉 {len(changed)} 句" + (f"（{'、'.join(changed[:3])}）" if changed else ""))

    tot = bad = 0
    for i in range(len(texts) - 1):
        for tl in ("好，那我们", "今天我们", "下面我们来看", "所以我们", "然后呢我们"):
            row = texts[i] + tl
            tot += 1
            got = fix(ref, row)[0]
            bad += int(not got.endswith(tl))
    out.append(f"4. 母本的一句 + 后面几个新的字：{tot} 句，后面的字被改掉 {bad} 句")
    tot = bad = 0
    for i in range(1, len(texts)):
        for hd in ("今天的", "好，", "那你看", "大家注意"):
            row = hd + texts[i]
            tot += 1
            bad += int(not fix(ref, row)[0].startswith(hd))
    out.append(f"5. 前面几个新的字 + 母本的一句：{tot} 句，前面的字被改掉 {bad} 句")

    res = {"单独": [0, 0], "后面跟一句新的话": [0, 0], "前面有一句新的话": [0, 0]}
    k = 0
    for r in ORIG:
        if r["keep"] != "1" or r["drop_reason"] == "老师删除":
            continue
        t, c = r["text"], CLEAN[r["id"]]
        if norm(t) == norm(c):
            continue
        nw = NEW_CONTENT[k % len(NEW_CONTENT)]
        k += 1
        for key, row, want in (("单独", t, c), ("后面跟一句新的话", t + nw, c + nw), ("前面有一句新的话", nw + t, nw + c)):
            fixes, _cov, _s, _f = tf._mother_first(row, NEW_ID, ref, (row,))
            got = tf._apply(row, [(f.start, f.end, f.rep) for f in fixes])  # 包括没把握的（看对上的范围对不对）
            res[key][0] += 1
            res[key][1] += int(norm(got) == norm(want))
    out.append("6. 和母本不一样的 123 句（按对上的那一段的全部改法改，包括没把握的）：" +
               "，".join(f"{k}{v[1]}/{v[0]}" for k, v in res.items()))

    rnd = random.Random(7)
    st = {"diff": 0, "diff_exact": 0, "same": 0, "same_changed": 0}
    ex = []
    for r in ORIG:
        if r["keep"] != "1" or r["drop_reason"] == "老师删除":
            continue
        t, c = r["text"], CLEAN[r["id"]]
        if len(t) < 14:
            continue
        cands = []
        for tag, i1, i2, j1, _j2 in difflib.SequenceMatcher(None, t, c, autojunk=False).get_opcodes():
            if tag == "equal":
                for p in range(i1 + 1, i2):
                    if 5 <= p <= len(t) - 5 and "一" <= t[p - 1] <= "鿿" and "一" <= t[p] <= "鿿":
                        cands.append((p, j1 + p - i1))
        if not cands:
            continue
        p, q = rnd.choice(cands)
        for a, b in ((t[:p], c[:q]), (t[p:], c[q:])):
            got = fix(ref, a)[0]
            if norm(a) == norm(b):
                st["same"] += 1
                if got != a:
                    st["same_changed"] += 1
                    ex.append(f"{a} → {got}")
            else:
                st["diff"] += 1
                st["diff_exact"] += int(norm(got) == norm(b))
    out.append(f"7. 在汉字中间切开的半句：本来对的 {st['same']} 句里被改 {st['same_changed']} 句"
               + (f"（例如 {ex[0]}）" if ex else "") + f"；有错的 {st['diff']} 句里直接改对 {st['diff_exact']} 句"
               "（单独一句、没有前后的证据：读音不像听错的只给没把握的建议，所以不会全对）")
    out += ["", f"用时 {time.time() - t0:.1f} 秒"]
    text = "\n".join(out)
    print(text)
    (HERE / f"第二轮探针结果_{label}.txt").write_text(text + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
