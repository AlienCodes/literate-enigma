#!/usr/bin/env python3
"""重点词分档：这个词该不该占 50 个名额之一。

用法：
  python3 word_tier.py 01                 # 查第01篇的 50 个重点词
  python3 word_tier.py --all              # 全库统计
  python3 word_tier.py --words foul stench cesspit

分档（用户 2026-09-30 定：要高中中上难度 + 考研词；不要基础词，不要八百年见不到的偏词）：
  ✓ 考研     在考研词表、不在高中词表
  ✓ 高中中上 在高中词表、不在初中词表，且词频 Zipf < 4.5（高中词里偏难的那一半多）
  ✓ 派生     本身不在表里，但由上面两档的词加常见词缀构成（infect → infection）
  ✓ 四六级   只在四六级词表，词频 Zipf ≥ 3.0（用户 2026-09-30 同意纳入：70 篇×50 词不重复需要这部分余量）
  △ 高中较常用 高中词、Zipf 4.5–4.8（variety、zone 这一层）：语言学家逐个判定
  ✗ 基础     在初中词表；或在高中词表且 Zipf ≥ 4.8（opinion、address 这一层）
  ✓ 雅思     在雅思词表（有道、新东方两本）
  ✓ 常用     不在任何词表，但正常英文里常见（Zipf ≥ 3.3）——用户 2026-09-30：不要被词库困住
  ✗ 冷僻     不在任何词表且 Zipf < 3.3；或 Zipf < 2.5（cesspit、miasma 这一层）
词表：github.com/KyleBing/english-vocabulary 的初中／高中／四级／六级／考研词表。
词频：wordfreq 的 Zipf 值（按词元取最大）。
"""
import json
import os
import sys

from lemminflect import getAllLemmas
from wordfreq import zipf_frequency

HERE = os.path.dirname(os.path.abspath(__file__))
LISTS = json.load(open(os.path.join(HERE, "..", "wordlists", "lists.json")))
J, G, K, C = (set(LISTS[k]) for k in "JGKC")
I = set(LISTS.get("I", []))
COMMON_MIN = 3.3
HS_HARD_MAX = 4.5
HS_GREY_MAX = 4.8
RARE_MIN = 2.5
CET_MIN = 3.0
SUFFIXES = ["ation", "ition", "tion", "sion", "ion", "ment", "ness", "ity", "ance", "ence",
            "er", "or", "ist", "ive", "al", "ous", "ful", "less", "ly", "ish", "ery", "age", "ing"]
PREFIXES = ["un", "dis", "re", "mis", "non", "over", "under"]
SYL = "/home/user/postgraduate-vocabulary/exports/syllabus.json"


def lemmas(w):
    w = w.lower()
    out = {w}
    for ls in getAllLemmas(w).values():
        out |= set(ls)
    if w.endswith("ies"):
        out.add(w[:-3] + "y")
    elif w.endswith("s"):
        out.add(w[:-1])
    return out


def zipf(ls):
    return max(zipf_frequency(x, "en") for x in ls)


def derived_from(ls, pool):
    forms = set(ls)
    for w in ls:
        for p in PREFIXES:
            if w.startswith(p) and len(w) - len(p) >= 5:
                rest = w[len(p):]
                for r in lemmas(rest):
                    if r in pool:
                        return r
                forms.add(rest)
    for w in forms:
        for s in SUFFIXES:
            if w.endswith(s):
                stem = w[: -len(s)]
                cands = {stem, stem + "e"}
                if len(stem) > 2 and stem[-1] == stem[-2]:
                    cands.add(stem[:-1])
                if stem.endswith("i"):
                    cands.add(stem[:-1] + "y")
                for cand in cands:
                    if len(cand) >= 4 and cand in pool:
                        return cand
    return None


PHRASES = set(LISTS.get("PJ", [])) | set(LISTS.get("PX", []))
FUNC = {"a", "an", "the", "of", "in", "on", "to", "for", "with", "by", "at", "up", "out", "off",
        "as", "from", "into", "onto", "over", "down", "away", "back", "about", "one's", "oneself"}


def tier_phrase(phrase):
    ws = phrase.lower().split()
    content = [w for w in ws if w not in FUNC] or ws
    ts = [(w,) + tier(w) for w in content]
    z = min(t[2] for t in ts)
    good = [w for w, t, _, _ in ts if t.startswith("✓")]
    if good:
        return "✓短语", z, "含 %s" % "、".join(good)
    grey = [w for w, t, _, _ in ts if t.startswith("△")]
    if grey:
        return "△短语", z, "含 %s（高中较常用），语言学家判定" % "、".join(grey)
    if any(t == "✗冷僻" for _, t, _, _ in ts):
        return "✗冷僻", z, "含冷僻词"
    lem = " ".join(min(lemmas(w), key=len) if w not in FUNC else w for w in ws)
    if phrase.lower() in PHRASES or lem in PHRASES:
        return "△短语", z, "由基础词组成的固定搭配：语言学家判定够不够中上难度（rule out 算，take part in 不算）"
    return "✗基础", z, "由基础词组成，且不是词典收录的固定搭配"


def tier(word):
    if " " in word.strip():
        return tier_phrase(word.strip())
    ls = lemmas(word)
    z = zipf(ls)
    inJ, inG, inK, inC, inI = (any(x in S for x in ls) for S in (J, G, K, C, I))
    if inJ or (inG and z >= HS_GREY_MAX):
        return "✗基础", z, "初中词" if inJ else "高中常用词（Zipf %.2f ≥ %.1f）" % (z, HS_GREY_MAX)
    if inG and z >= HS_HARD_MAX:
        return "△高中较常用", z, "Zipf %.2f：语言学家判定是否达中等以上（variety 算）" % z
    if z < RARE_MIN:
        return "✗冷僻", z, "词频过低（Zipf %.2f）" % z
    if inK and not inG:
        return "✓考研", z, ""
    if inG:
        return "✓高中中上", z, ""
    if inI:
        return "✓雅思", z, ""
    base = derived_from(ls, G | K | I)
    if base:
        return "✓派生", z, "由 %s 派生" % base
    if inC and z >= CET_MIN:
        return "✓四六级", z, ""
    if z >= COMMON_MIN:
        return "✓常用", z, "不在考试词表，但正常英文里常见（Zipf %.2f）" % z
    return "✗冷僻", z, "不在任何考试词表，也不常见（Zipf %.2f < %.1f）" % (z, COMMON_MIN)


def article_words(aid):
    return [w["w"] for w in json.load(open(SYL, encoding="utf-8"))["words"] if w["a"] == aid]


def report(words):
    rows = [(w,) + tier(w) for w in words]
    seen, dup = {}, []
    for w, *_ in rows:
        key = min(lemmas(w), key=len)
        if key in seen:
            dup.append((seen[key], w))
        seen[key] = w
    for w, t, z, why in sorted(rows, key=lambda r: (r[1], -r[2])):
        print("  %-8s %-16s %.2f  %s" % (t, w, z, why))
    cnt = {}
    for _, t, _, _ in rows:
        cnt[t] = cnt.get(t, 0) + 1
    print("  —— " + "  ".join("%s %d" % kv for kv in sorted(cnt.items())))
    if dup:
        print("  —— 同词占两格：" + "；".join("%s / %s" % d for d in dup))
    return rows, dup


if __name__ == "__main__":
    a = sys.argv[1:]
    if "--words" in a:
        report(a[a.index("--words") + 1:])
    elif "--all" in a:
        total = {}
        for w in json.load(open(SYL, encoding="utf-8"))["words"]:
            t = tier(w["w"])[0]
            total[t] = total.get(t, 0) + 1
        print("全库 3500 词：" + "  ".join("%s %d" % kv for kv in sorted(total.items())))
    else:
        aid = (a[0] if a else "01").zfill(2)
        print("第%s篇重点词分档" % aid)
        report(article_words(aid))
