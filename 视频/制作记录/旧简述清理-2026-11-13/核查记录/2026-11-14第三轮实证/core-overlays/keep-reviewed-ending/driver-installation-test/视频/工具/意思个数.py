#!/usr/bin/env python3
"""重点词中文最多两个意思（文36，27 起）。用户 2026-10-24 看 24 S8：“狂暴的/猛烈的 只用这两个意思就就这两个表示。”
24–26 用户给的都是语境里的一两个意思（逼退/击退、算数/计算、转接器/转换插头、框架/结构、一整套/全部）。
门：中文 **甲/乙/丙**(word) 用“/”分出 3 个以上意思 → 停；用户原话亲自给了这几个意思（用户同意记录 里同一篇的原话含每一个意思）才放行（文2）。
用法：python3 意思个数.py --自检"""
import re, os, sys, json
T = os.path.dirname(os.path.abspath(__file__))
起 = 27
def 多义(d):
    out = []
    for si, s in enumerate(d.get('sentences', []), 1):
        for c in s.get('chunks', []):
            for m in re.finditer(r'\*\*([^*]+)\*\*\(([^)]+)\)', c.get('zh', '')):
                ps = [x for x in re.split(r'[/／]', m.group(1)) if x.strip()]
                if len(ps) >= 3: out.append((si, m.group(2), ps))
    return out
def 查(d, no, 记录=None):
    if not str(no).isdigit() or int(no) < 起: return []
    if 记录 is None:
        try: 记录 = json.load(open(f'{T}/用户同意记录.json'))['记录']
        except Exception: 记录 = []
    话 = ' '.join(r.get('原话', '') for r in 记录 if str(r.get('篇', '')).zfill(2) == str(no).zfill(2))
    return [f'[文36] S{si} {w}：中文给了 {len(ps)} 个意思（{"/".join(ps)}），重点词只留语境里的一两个意思（用户：“只用这两个意思”）；用户原话亲自给的，记进用户同意记录'
            for si, w, ps in 多义(d) if not all(p in 话 for p in ps)]
def 自检():
    d = {'sentences': [{'chunks': [{'zh': '**狂暴的/猛烈的**(ferocious)大风'}]}, {'chunks': [{'zh': '**极低/渺茫/非常微小**(slim)'}]}]}
    f = []
    if not any('slim' in x for x in 查(d, '27', [])): f.append('没抓到：重点词中文三个意思')
    if any('ferocious' in x for x in 查(d, '27', [])): f.append('误报：两个意思')
    if 查(d, '27', [{'篇': '27', '原话': '极低/渺茫/非常微小 就这么写'}]): f.append('误报：用户原话亲自给的三个意思')
    if 查(d, '11', []): f.append('误报：27 以前的篇目不回头查')
    return ['意思个数 自检：' + x for x in f]
if __name__ == '__main__':
    e = 自检(); print('\n'.join(e) or '意思个数 自检通过（三个意思必停、两个不报、用户原话给的放行、27 以前不查）'); sys.exit(1 if e else 0)
