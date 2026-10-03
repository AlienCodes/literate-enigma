#!/usr/bin/env python3
"""重写稿自检：写作者每改一稿就跑一次。

用法：
  python3 draft_check.py 草稿.md            # 查一篇
  python3 draft_check.py 草稿.md --claim NN # 查过之后把这 50 个词登记进全库台账（定稿时才用）

草稿格式（严格照写，程序靠这些标题切块）：
  # EN: 英文标题
  # ZH: 中文标题
  ## 英文
  （段数按质量需要，段间空一行；重点词用 **word** 加粗，短语整体加粗 **a variety of**）
  ## 中文
  （与英文同样段数；每个重点词写成 **中文**(english)，括注与英文加粗原样一致）
  ## 速查表
  | 词 | 释义 | 段 |
  |---|---|---|
  | prevailing | adj. 盛行的；占优势的 | 1 |
  ## 史实与来源
  - 每条史实一行，附来源链接

硬性（✗ 必须改）：段数不限（中英段数相同）；重点词 50–70 个（按质量需要定）；词数 249–271；中英加粗逐段一一对应；
  重点词全部在可用档；篇内与全库都不重复（同一个词的不同形态算重复，派生词不算）；
  速查表条数与重点词数相同、与正文一一对应、释义是中文。
提醒（△ 看一眼）：△ 档的词要语言学家写理由；视频流水线会踩的写法。
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

LEDGER = os.path.join(HERE, "used_words.json")
BOLD = re.compile(r"\*\*([^*]+)\*\*")
GLOSS = re.compile(r"\*\*([^*]+)\*\*\(([^)]+)\)")
CJK = re.compile(r"[一-鿿]")


def parse(path):
    t = open(path, encoding="utf-8").read()
    d = {"title": re.search(r"^# EN:\s*(.+)$", t, re.M), "titleZh": re.search(r"^# ZH:\s*(.+)$", t, re.M)}
    d = {k: (v.group(1).strip() if v else "") for k, v in d.items()}
    secs = re.split(r"^## (.+)$", t, flags=re.M)
    blocks = {secs[i].strip(): secs[i + 1] for i in range(1, len(secs) - 1, 2)}
    paras = lambda s: [p.strip() for p in re.split(r"\n\s*\n", s.strip()) if p.strip()]
    d["en"] = paras(blocks.get("英文", ""))
    d["zh"] = paras(blocks.get("中文", ""))
    d["glossary"] = []
    for line in blocks.get("速查表", "").splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) == 3 and cells[0] not in ("词", "") and not set(cells[0]) <= set("-: "):
            d["glossary"].append({"w": cells[0], "zh": cells[1], "p": cells[2]})
    d["facts"] = [l[2:].strip() for l in blocks.get("史实与来源", "").splitlines() if l.startswith("- ")]
    return d


def lemma_key(w):
    w = w.lower().strip()
    if " " in w:
        return " ".join(min(T.lemmas(x), key=len) for x in w.split())
    return min(T.lemmas(w), key=len)


def check(d, aid=None):
    bad, warn = [], []
    en, zh = d["en"], d["zh"]
    if not d["title"] or not d["titleZh"]:
        bad.append("缺英文或中文标题")
    if not en or len(en) != len(zh):
        bad.append("段数：英文 %d 段、中文 %d 段（要相同）" % (len(en), len(zh)))
    words = sum(count_words(p) for p in en)
    keys = [BOLD.findall(p) for p in en]
    nk = sum(len(k) for k in keys)
    dens = 100.0 * nk / words if words else 0
    if not 249 <= words <= 271:
        bad.append("词数 %d（要 249–271）" % words)
    if not 50 <= nk <= 70:
        bad.append("重点词 %d 个（要 50–70 个）" % nk)
    per = [len(k) for k in keys]
    if per and (max(per) - min(per) > 6 or min(per) < 5):
        warn.append("各段重点词 %s——分布太不均，看一眼" % per)
    # 中英逐段对应
    for i, (pe, pz) in enumerate(zip(en, zh), 1):
        ke = sorted(w.lower() for w in BOLD.findall(pe))
        kz = sorted(g.lower() for _, g in GLOSS.findall(pz))
        if ke != kz:
            miss = sorted(set(ke) - set(kz)); extra = sorted(set(kz) - set(ke))
            bad.append("第 %d 段中英加粗不对应：中文缺 %s；中文多 %s" % (i, miss or "无", extra or "无"))
        naked = [b for b in BOLD.findall(re.sub(GLOSS, "", pz))]
        if naked:
            bad.append("第 %d 段中文有加粗没括注：%s" % (i, naked))
    # 分档
    allk = [w for k in keys for w in k]
    rows = [(w,) + T.tier(w) for w in allk]
    for w, t, z, why in rows:
        if t.startswith("✗"):
            bad.append("重点词不在可用范围：%s（%s %s）" % (w, t, why))
        elif t.startswith("△"):
            warn.append("△ %s：%s（语言学家写理由）" % (w, why))
    # 篇内重复
    seen = {}
    for w in allk:
        k = lemma_key(w)
        if k in seen:
            bad.append("篇内同一个词占两格：%s / %s" % (seen[k], w))
        seen[k] = w
    # 全库重复
    ledger = json.load(open(LEDGER, encoding="utf-8")) if os.path.exists(LEDGER) else {}
    for w in allk:
        owner = ledger.get(lemma_key(w))
        if owner and owner != aid:
            bad.append("全库重复：%s 已被第 %s 篇用过" % (w, owner))
    # 速查表
    g = d["glossary"]
    if len(g) != nk:
        bad.append("速查表 %d 条（要与重点词数 %d 相同）" % (len(g), nk))
    gw = sorted(x["w"].lower() for x in g)
    if gw != sorted(w.lower() for w in allk):
        bad.append("速查表词条与正文加粗不一一对应：多 %s；少 %s"
                   % (sorted(set(gw) - {w.lower() for w in allk}) or "无",
                      sorted({w.lower() for w in allk} - set(gw)) or "无"))
    for x in g:
        if not CJK.search(x["zh"]):
            bad.append("速查表释义不是中文：%s" % x["w"])
    # 视频流水线提醒
    body = "\n".join(en)
    for pat, why in [(r"(?<!\*)\*(?!\*)[^*]+\*(?!\*)", "单星号斜体会原样上屏"),
                     (r"\b(?:St|Dr|Mr|Mrs|Ms|Mt|No|vs|etc|e\.g|i\.e|U\.S|U\.K)\.", "带点缩写会被当成句号切开"),
                     (r"[?!](?=\s+[a-z])", "问号叹号后接小写，会被切成两句")]:
        for m in re.finditer(pat, body):
            warn.append("视频：%s —— %s" % (m.group(0), why))
    for s in re.split(r"(?<=[.!?])\s+", re.sub(r"\*\*", "", body)):
        if len(s.split()) >= 35:
            warn.append("视频：长句 %d 词 —— 一帧字会很小：%s…" % (len(s.split()), s[:50]))
    for i, pz in enumerate(zh, 1):
        if "：" in pz and zh:
            warn.append("视频：中文第 %d 段有冒号「：」——若它把两句英文并成一句，视频会错位" % i)
    return bad, warn, {"words": words, "keywords": nk, "density": round(dens, 1)}, rows


def main():
    a = sys.argv[1:]
    d = parse(a[0])
    aid = a[a.index("--claim") + 1].zfill(2) if "--claim" in a else None
    bad, warn, m, rows = check(d, aid)
    print("《%s / %s》 %d 词 · %d 重点词 · 密度 %.1f%%" % (d["title"], d["titleZh"], m["words"], m["keywords"], m["density"]))
    cnt = {}
    for _, t, _, _ in rows:
        cnt[t] = cnt.get(t, 0) + 1
    print("分档：" + "  ".join("%s %d" % kv for kv in sorted(cnt.items())))
    for x in bad:
        print("  ✗ " + x)
    for x in warn:
        print("  △ " + x)
    print("  %s" % ("硬性全过" if not bad else "**%d 处必须改**" % len(bad)))
    if aid and not bad:
        ledger = json.load(open(LEDGER, encoding="utf-8")) if os.path.exists(LEDGER) else {}
        for w, *_ in rows:
            ledger[lemma_key(w)] = aid
        json.dump(ledger, open(LEDGER, "w", encoding="utf-8"), ensure_ascii=False, indent=0, sort_keys=True)
        print("  已登记第 %s 篇 %d 个词进全库台账（共 %d 个）" % (aid, len(rows), len(ledger)))
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
