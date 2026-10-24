#!/usr/bin/env python3
"""重点词对正（用户 2026-10-24：“尽量让他放在这个就是正对着这个英文的底下，尽量尽可能在不影响这个整体布局的情况下”）。
在视频工作目录下运行（与出片程序同一套排版：render.col_place，4K 坐标，下面像素按 1080p 折算）：
  python3 对正量.py NN [NN…]      每篇：重点词英文中心与同色中文中心的水平偏移（改前=格内居中，改后=对正排法）
  python3 对正量.py NN --门       24 起：没开对正排法、或偏移超过阈值又说不出几何原因的，停
  python3 对正量.py --自检         造坑：关掉对正排法、伪造一处可对正却没对正的，门必须停；真实 24 必须过"""
import sys, os, re, json
os.environ['VIDEO_S'] = '2'
sys.path.insert(0, os.getcwd())
import render as R
T = os.path.dirname(os.path.abspath(__file__))
门起 = 24   # 门自己记篇号，不跟 render 的开关走（开关被改了门照样查）
阈值 = 4.0   # 1080p 像素：对正排法下做得到的都在 1 像素内；超过 4 像素必须是几何上做不到（格边顶住、同格几个重点词牵制）

def load(no):
    for p in (f'scripts/{no}.json', f'{T}/../脚本/{no}.json'):
        if os.path.exists(p): return json.load(open(p, encoding='utf-8'))
    raise SystemExit(f'找不到脚本 {no}')

def measure(d, align):
    colors = {}; i = 0
    for s in d['sentences']:
        for c in s['chunks']:
            for w in re.findall(r'\*\*([^*]+)\*\*', c['en']):
                if w.lower() not in colors: colors[w.lower()] = R.PAL[i % len(R.PAL)]; i += 1
    R.unify_colors(colors, d['sentences']); R.apply_script(d); R.ES_FIXED = None
    res = []; 不同格 = 0; 整块 = 0
    for si, s in enumerate(d['sentences']):
        ch = [[tuple(p) for p in c['align']] for c in s['chunks']]; sc = R.sent_colors(colors, s); notes = [c.get('note') for c in s['chunks']]
        es = R.max_es(ch, sc, notes)
        k_ = f'S{si + 1}'
        if k_ in d.get('字号上限', {}): es = min(es, float(d['字号上限'][k_]) * R.S)
        es = min(es, 100 * R.S)
        rowsets, _, _, (zs, ef, zf, gapx, *_) = R._measure(ch, sc, notes, es, R._grouping(ch, sc))
        for bi, rows in enumerate(rowsets):
            for r in rows:
                if isinstance(r, tuple):
                    整块 += len(re.findall(r'\*\*', r[1].get('er', ''))) // 2; continue
                tw = sum(c['w'] for c in r) + gapx * (len(r) - 1); x = (R.W - tw) / 2
                for c in r:
                    xe, xz = R.col_place(c, ef, zf, x, align)
                    ek = R._key_spans(c['se'], ef, xe, set(re.findall(r'\*\*([^*]+)\*\*', c['er'])))
                    最优 = local_opt(c, ef, zf, x, xe, xz)
                    seen = set()
                    for k, l in enumerate(c['zl']):
                        if k and re.fullmatch(R.ZCOL, c['zr'][k].strip()): continue
                        zk = R._key_spans(l, zf, xz[k], R._zh_keys(c['zr'][k]))
                        nk = len(zk)
                        for col, b in zk.items():
                            if col not in ek: continue
                            seen.add(col); e = ek[col]; off = ((b[0] + b[1]) / 2 - (e[0] + e[1]) / 2) / R.S
                            边 = (xe <= x + .5 or xe >= x + c['w'] - c['we'] - .5) and (xz[k] <= x + .5 or xz[k] >= x + c['w'] - c['wl'][k] - .5)
                            多 = nk > 1 or sum(1 for kk, ll in enumerate(c['zl']) if R._key_spans(ll, zf, 0, R._zh_keys(c['zr'][kk]))) > 1
                            词 = ''.join(t for t, cc in c['se'] if cc == col).strip()
                            res.append(dict(句=si + 1, 词=词, 偏=round(off, 1), 宽=round((e[1] - e[0]) / R.S), 原因=('' if not 最优 else '同格几个重点词牵制' if 多 else '格边顶住' if 边 else '格内已最近')))
                    不同格 += len([1 for col in ek if col not in seen and any(cc == col for l in c['zl'] for _, cc in l) is False])
    return res, 不同格, 整块

def colcost(c, ef, zf, xe, xz):
    ek = R._key_spans(c['se'], ef, xe, set(re.findall(r'\*\*([^*]+)\*\*', c['er']))); t = 0.0
    for k, l in enumerate(c['zl']):
        if k and re.fullmatch(R.ZCOL, c['zr'][k].strip()): continue
        for col, b in R._key_spans(l, zf, xz[k], R._zh_keys(c['zr'][k])).items():
            if col in ek: t += abs((b[0] + b[1]) / 2 - (ek[col][0] + ek[col][1]) / 2)
    return t
def local_opt(c, ef, zf, x, xe, xz):
    """几何证明：本格内把英文行或任一行中文（或英文连同一行中文）左右挪 2 像素（不出格），总偏移都不会更小 = 做不到更正"""
    c0 = colcost(c, ef, zf, xe, xz); ok = lambda e, z: x - .01 <= e <= x + c['w'] - c['we'] + .01 and all(x - .01 <= z[k] <= x + c['w'] - c['wl'][k] + .01 for k in range(len(z)) if c['w'] >= c['wl'][k])
    for dx in (-2 * R.S, 2 * R.S):
        tries = [(xe + dx, xz)] + [(xe, [z + dx * (j == k) for j, z in enumerate(xz)]) for k in range(len(xz))] + [(xe + dx, [z + dx * (j == k) for j, z in enumerate(xz)]) for k in range(len(xz))]
        for e, z in tries:
            if ok(e, z) and colcost(c, ef, zf, e, z) < c0 - 0.5: return False
    return True

def stat(res):
    a = sorted(abs(r['偏']) for r in res) or [0]
    return f"{len(res)} 处，平均 {sum(a) / len(a):.1f}，中位 {a[len(a) // 2]:.1f}，最差 {a[-1]:.1f} 像素，>4 像素 {sum(1 for v in a if v > 4)} 处"

def gate(no, d=None):
    d = d or load(no); errs = []
    if int(d['no']) >= 门起:
        R.apply_script(d)
        if not R.ALIGN_RULE[0]: errs.append('对正排法没开（24 起必须开）')
        res, *_ = measure(d, None)
        for r in res:
            if abs(r['偏']) > 阈值 and not r['原因']: errs.append(f"S{r['句']} {r['词']} 偏 {r['偏']} 像素，不是格边顶住也不是同格牵制（做得到却没对正）")
    return errs

if __name__ == '__main__':
    a = sys.argv[1:]
    if a == ['--自检']:
        d = load('24'); assert not gate('24', d), gate('24', d)
        R.ALIGN_FROM = 99; 坏 = gate('24', d); R.ALIGN_FROM = 24
        orig = R.col_place
        R.col_place = lambda c, ef, zf, x, align=None: orig(c, ef, zf, x, False)   # 伪造：画法退回居中
        坏2 = gate('24', d); R.col_place = orig
        if not 坏 or not 坏2: raise SystemExit('【停止】对正量 自检失败：造的坑没被挡住')
        print(f'对正量 自检通过：关开关 {len(坏)} 条、退回居中 {len(坏2)} 条，都挡住；真实 24 通过'); sys.exit()
    if '--门' in a:
        for no in [x for x in a if x != '--门']:
            e = gate(no)
            if e: print('\n'.join(f'✘ [T37] {no} {x}' for x in e[:8])); raise SystemExit(f'【停止】{no} 重点词对正 {len(e)} 处不合格（T37）')
            print(f'✔ [T37] {no} 重点词对正通过')
        sys.exit()
    for no in a:
        d = load(no); r0, ng, kb = measure(d, False); r1, *_ = measure(d, True)
        print(f'{no} 改前：{stat(r0)}；改后：{stat(r1)}（另：中文不在同一格 {ng}，整块折行 {kb}）')
        w = sorted(r1, key=lambda r: -abs(r['偏']))[:4]
        print('   改后最差：' + '；'.join(f"S{r['句']} {r['词']} {r['偏']}（{r['原因'] or '—'}）" for r in w))
