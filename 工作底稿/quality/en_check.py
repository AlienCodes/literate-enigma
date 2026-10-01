#!/usr/bin/env python3
"""英文稿自检（只查英文，作者起草阶段用）。

用法：python3 en_check.py 稿子.md
稿子：第一行 `# EN: 标题`，其后是正文段落（空行分段），候选重点词用 **word** 加粗（短语整体加粗）。
报告：每段词数与总词数（249–271）、句长（>32 词标出）、候选词分档（✗ 的不能当重点词）、
      全库台账里已被新稿占用的词、同一个词重复加粗、视频流水线会踩的写法。
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, "/home/user/postgraduate-vocabulary/scripts")
import word_tier as T  # noqa: E402
from core import count_words  # noqa: E402
from draft_check import lemma_key, LEDGER  # noqa: E402

BOLD = re.compile(r"\*\*([^*]+)\*\*")

t = open(sys.argv[1], encoding="utf-8").read()
title = (re.search(r"^# EN:\s*(.+)$", t, re.M) or [None, ""])[1]
body = re.sub(r"^#.*$", "", t, flags=re.M)
paras = [p.strip() for p in re.split(r"\n\s*\n", body.strip()) if p.strip()]
wc = [count_words(p) for p in paras]
print("标题：%s（%d 字符）" % (title, len(title)))
print("段落词数：%s  合计 %d  %s" % (wc, sum(wc), "✓" if 249 <= sum(wc) <= 271 else "✗ 要 249–271"))
for s in re.split(r"(?<=[.!?])\s+", BOLD.sub(r"\1", " ".join(paras))):
    n = count_words(s)
    if n > 32:
        print("  ✗ 长句 %d 词：%s…" % (n, s[:70]))
cands = [w for p in paras for w in BOLD.findall(p)]
ledger = json.load(open(LEDGER, encoding="utf-8")) if os.path.exists(LEDGER) else {}
seen, cnt = {}, {}
print("候选词 %d 个：" % len(cands))
for w in cands:
    tr, z, why = T.tier(w)
    cnt[tr] = cnt.get(tr, 0) + 1
    k = lemma_key(w)
    extra = []
    if k in seen:
        extra.append("与 %s 是同一个词" % seen[k])
    seen[k] = w
    if ledger.get(k):
        extra.append("已被新第 %s 篇占用" % ledger[k])
    if tr.startswith("✗") or tr.startswith("△") or extra:
        print("  %s %s  %s %s" % (tr, w, why, "；".join(extra)))
print("分档合计：" + "  ".join("%s %d" % kv for kv in sorted(cnt.items())))
for pat, why in [(r"(?<!\*)\*(?!\*)[^*]+\*(?!\*)", "单星号斜体"), (r"\b(?:St|Dr|Mr|Mrs|Ms|No|vs|etc|e\.g|i\.e|U\.S)\.", "带点缩写"),
                 (r"[?!]", "问号或叹号"), (r"\d\.\d", "小数"), (r"[°£±]", "特殊符号")]:
    for m in re.finditer(pat, body):
        print("  △ 视频：%s —— %s" % (m.group(0), why))
