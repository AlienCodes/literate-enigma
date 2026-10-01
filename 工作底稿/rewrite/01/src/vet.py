import sys, json
sys.path.insert(0, '/tmp/claude-0/-home-user-literate-enigma/df763388-3805-5b4c-bf94-30b7788b9986/scratchpad/quality')
import word_tier as wt
SYL = "/home/user/postgraduate-vocabulary/exports/syllabus.json"
used = {}
for w in json.load(open(SYL, encoding='utf-8'))['words']:
    if w['a'] == '01': continue
    for l in wt.lemmas(w['w']):
        used.setdefault(l, set()).add(w['a'])
    used.setdefault(w['w'].lower(), set()).add(w['a'])
cands = sys.argv[1:]
ok, bad = [], []
for c in cands:
    t, z, why = wt.tier(c)
    owners = set()
    if ' ' in c:
        owners |= used.get(c.lower(), set())
    else:
        for l in wt.lemmas(c):
            owners |= used.get(l, set())
    row = (c, t, round(z,2), why, ','.join(sorted(owners)))
    (ok if t.startswith('✓') and not owners else bad).append(row)
print('=== 可用（✓档且全库未占用）', len(ok))
for r in sorted(ok, key=lambda r:r[0]): print('  %-16s %-8s %.2f %s' % r[:4])
print('=== 不可用/待判', len(bad))
for r in sorted(bad, key=lambda r:(r[1], r[0])): print('  %-16s %-10s %.2f %-30s %s' % (r[0], r[1], r[2], r[3][:30], ('占用:'+r[4]) if r[4] else ''))
