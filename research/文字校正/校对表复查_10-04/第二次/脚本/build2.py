"""第二轮：老师按清单改完以后又发来的 transcripts.csv → 再改的句子 + 标黄表格 + 查找替换清单。
用法：python3 build2.py 老师的transcripts.csv 输出目录"""
import csv, io, json, re, difflib, sys
sys.path.insert(0, '.')
from spec2 import EDITS, UNSURE
SRC, OUT = sys.argv[1], sys.argv[2]
raw = open(SRC, 'rb').read()
rows = list(csv.reader(io.StringIO(raw.decode('utf-8-sig'), newline='')))
head, data = rows[0], rows[1:]
TI, KI = head.index('text'), head.index('keep')

def dump(rs):
    b = io.StringIO(newline='')
    csv.writer(b, lineterminator='\r\n').writerows(rs)
    return ('﻿' + b.getvalue()).encode('utf-8')
assert dump(rows) == raw, '原样写回和原文件不一样'

new = {}
for no, a, b, why in EDITS:
    cur = new.get(no, [data[no - 1][TI], []])
    assert cur[0].count(a) == 1, (no, a, cur[0])
    cur[0] = cur[0].replace(a, b)
    cur[1].append(why)
    new[no] = cur
for no, a, g, why in UNSURE:
    t = new.get(no, [data[no - 1][TI]])[0]
    assert a in t, (no, a)

def pattern(q):
    q = q.strip()
    body = re.escape(q)
    if re.fullmatch(r"[A-Za-z0-9]+(?:[ '\-][A-Za-z0-9]+)*", q):
        body = r"(?<![A-Za-z0-9])" + body + r"(?![A-Za-z0-9])"
    return re.compile(body, re.IGNORECASE)
texts = [r[TI] for r in data]
live = [i for i, r in enumerate(data)]  # 查找不管用不用（只跳过删除的；删除的行这里没有）
def count(q):
    p = pattern(q)
    return sum(len(p.findall(t)) for t in texts)

W = lambda c: c.isascii() and c.isalnum()
pairs = []
for no in sorted(new):
    old, nt = data[no - 1][TI], new[no][0]
    ops = [o for o in difflib.SequenceMatcher(None, old, nt, autojunk=False).get_opcodes() if o[0] != 'equal']
    groups = []
    for o in ops:
        if groups and o[1] - groups[-1][2] < 6:
            g = groups[-1]; groups[-1] = (g[0], g[1], o[2], g[3], o[4])
        else:
            groups.append(o)
    def span(g, k):
        _, a1, a2, b1, b2 = g
        l, r = max(0, a1 - k), min(len(old), a2 + k)
        while l > 0 and W(old[l - 1]) and W(old[l]): l -= 1
        while r < len(old) and W(old[r - 1]) and W(old[r]): r += 1
        return l, r
    k = 2
    while True:
        spans = [span(g, k) for g in groups]
        merged = False
        for i in range(1, len(groups)):
            if spans[i][0] <= spans[i - 1][1]:
                g0, g1 = groups[i - 1], groups[i]
                groups[i - 1:i + 1] = [(g0[0], g0[1], g1[2], g0[3], g1[4])]
                merged = True
                break
        if merged:
            continue
        if all(old[l:r] and old[l:r].strip() == old[l:r] and count(old[l:r]) == 1 for l, r in spans):
            break
        k += 1
        assert k < 60, (no, old)
    for g, (l, r) in zip(groups, spans):
        _, a1, a2, b1, b2 = g
        pairs.append((no, data[no - 1][0], old[l:r], nt[b1 - (a1 - l): b2 + (r - a2)]))
sim = list(texts)
for no, rid, f, t in pairs:
    p = pattern(f)
    hits = [i for i, s in enumerate(sim) if p.search(s)]
    assert hits == [no - 1], (no, f, hits)
    sim[no - 1] = p.sub(lambda m: t, sim[no - 1])
for i, s in enumerate(sim):
    assert s == new.get(i + 1, [texts[i]])[0], (i + 1, s)

fixed = [list(r) for r in data]
for no, (t, _) in new.items():
    fixed[no - 1][TI] = t
open(f'{OUT}/transcripts.csv', 'wb').write(dump([head] + fixed))
json.dump({'new': {str(k): v for k, v in new.items()}, 'pairs': pairs}, open(f'{OUT}/result.json', 'w'), ensure_ascii=False, indent=1)
print('改了', len(new), '句；查找替换', len(pairs), '条；没把握', len(UNSURE), '处')
