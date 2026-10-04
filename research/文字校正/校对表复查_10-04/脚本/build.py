import csv, io, json, re, difflib, sys
sys.path.insert(0, '.')
from spec import MASTER, EDITS, UNSURE
SRC = sys.argv[1]  # 老师的 transcripts.csv（没放进仓库）
raw = open(SRC, 'rb').read()
rows = list(csv.reader(io.StringIO(raw.decode('utf-8-sig'), newline='')))
head, data = rows[0], rows[1:]
TI = head.index('text')

def dump(rs):
    b = io.StringIO(newline='')
    w = csv.writer(b, lineterminator='\r\n')
    w.writerows(rs)
    return ('﻿' + b.getvalue()).encode('utf-8')
assert dump(rows) == raw, '原样写回和原文件不一样'

items = {r['no']: r for r in json.load(open('items.json'))}
for no, r in items.items():
    assert data[no - 1][0] == r['id'] and data[no - 1][TI] == r['now'], no

new = {}   # no -> (新文字, [原因])
for no, why in MASTER.items():
    t = items[no]['after_master']
    assert t and t != data[no - 1][TI], no
    new[no] = [t, [why]]
for no, a, b, why in EDITS:
    cur = new.get(no, [data[no - 1][TI], []])
    assert cur[0].count(a) == 1, (no, a)
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
def count(q, ts):
    p = pattern(q)
    return sum(len(p.findall(t)) for t in ts)

# 查找替换清单：每处改动给一个全表只出现一次的「查找」字
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
    W = lambda c: c.isascii() and c.isalnum()
    def span(g, k):
        _, a1, a2, b1, b2 = g
        l, r = max(0, a1 - k), min(len(old), a2 + k)
        while l > 0 and W(old[l - 1]) and W(old[l]):
            l -= 1
        while r < len(old) and W(old[r - 1]) and W(old[r]):
            r += 1
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
        bad = False
        for g, (l, r) in zip(groups, spans):
            f = old[l:r]
            if not (f.strip() == f and f and count(f, texts) == 1):
                bad = True
        if not bad:
            break
        k += 1
        assert k < 60, (no, old)
    for g, (l, r) in zip(groups, spans):
        _, a1, a2, b1, b2 = g
        pairs.append((no, data[no - 1][0], old[l:r], nt[b1 - (a1 - l): b2 + (r - a2)]))
# 照清单一条条「全部替换」，结果必须和改好的一模一样
sim = list(texts)
for no, rid, f, t in pairs:
    p = pattern(f)
    hits = [i for i, s in enumerate(sim) if p.search(s)]
    assert hits == [no - 1], (no, f, hits)
    sim[no - 1] = p.sub(lambda m: t, sim[no - 1])
for i, s in enumerate(sim):
    want = new.get(i + 1, [texts[i]])[0]
    assert s == want, (i + 1, s, want)

fixed = [list(r) for r in data]
for no, (t, _) in new.items():
    fixed[no - 1][TI] = t
json.dump({'new': {str(k): v for k, v in new.items()}, 'pairs': pairs}, open('out/result.json', 'w'), ensure_ascii=False, indent=1)
open('out/transcripts.csv', 'wb').write(dump([head] + fixed))
print('改了', len(new), '句；查找替换', len(pairs), '条；没把握', len(UNSURE), '处')
