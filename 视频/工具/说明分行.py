#!/usr/bin/env python3
"""说明分行（L19，用户 2026-10-16：“这个长度最好不要超过这个上面这个正文的长度……如果超过的话，最好折叠一下就隔成两行。以后记住这个标准”）：
找出比这一句英文正文最宽一行还宽的说明行（render.wide_notes，与出片程序的 L19 守门同一个函数），自动在标点处折成两行（字一个不改）：
优先“；”，其次“，”“。”“！”“、”“：”，选两段都放得下、两段最均匀的那一处；“（@词 …”彩色行的续行写成“@词|…”保持同色。
用法（视频工作目录）：python3 说明分行.py NN          只列出要折的行和折法
                     python3 说明分行.py NN --写入   写进 scripts/NN.json 和 初稿生成/genNN.py（两处一起改，重新生成也不丢）"""
import sys, re, json, os
sys.path.insert(0, '.'); import render as R
no = sys.argv[1]; T = os.path.dirname(os.path.abspath(__file__)); p = f'scripts/{no}.json'; d = json.load(open(p)); R.apply_script(d)
PRI = {'；': 0, '，': 1, '。': 1, '！': 1, '、': 2, '：': 2}
def split(raw, ew, nf):
    m = re.match(r'^(（@(\S+) )', raw); pre = m.group(1) if m else ''; cont = f'@{m.group(2)}|' if m else ''
    t = R._note_txt(raw); best = None
    for i, ch in enumerate(t[:-1]):
        if ch in PRI:
            a, b = t[:i + 1], t[i + 1:]
            wa, wb = nf.getlength(a), nf.getlength(b)
            if wa <= ew and wb <= ew:
                k = (PRI[ch], abs(wa - wb))
                if best is None or k < best[0]: best = (k, i + 1)
    if best is None: return None
    i = best[1]; a = t[:i]; b = t[i:]
    if pre: a = pre + a[len('（' + m.group(2) + ' '):]
    return a, cont + b
fix = []
for si, s in enumerate(d['sentences'], 1):
    colors = {k: (1, 1, 1) for c in s['chunks'] for k in re.findall(r'\*\*(.+?)\*\*', c['en'])}
    ch = [[tuple(q) for q in c['align']] for c in s['chunks']]; nt = [c.get('note') for c in s['chunks']]
    rowsets, _, _, (zs, *_r) = R._measure(ch, colors, nt, 100, R._grouping(ch, colors)); nf = R.ZH(int(zs * 0.9), 400)
    for gi, ln, wn, ew in R.wide_notes(ch, colors, nt, 100):
        raw = next(x for x in nt[gi].split('\n') if R._note_txt(x) == ln); r = split(raw, ew, nf)
        print(f'S{si} 超宽 {wn}>{ew}：{ln[:40]}… → ' + (f'折成「{R._note_txt(r[0])}」/「{R._note_txt(r[1])}」' if r else '找不到合适的标点，交人处理'))
        if r: fix.append((si, gi, raw, r))
if '--写入' in sys.argv and fix:
    g = f'{T}/初稿生成/gen{no}.py'; src = open(g).read()
    for si, gi, raw, (a, b) in fix:
        c = d['sentences'][si - 1]['chunks'][gi]; c['note'] = c['note'].replace(raw, a + '\n' + b, 1)
        if src.count(raw) == 1: src = src.replace(raw, a + '\\n' + b)
        else: print(f'  gen{no}.py 里找不到唯一的这一行，只改了脚本：{raw[:30]}')
    json.dump(d, open(p, 'w'), ensure_ascii=False, indent=1); open(g, 'w').write(src); print(f'已写入 {len(fix)} 处')
print(f'{no} 说明分行：要折 {len(fix)} 处')
