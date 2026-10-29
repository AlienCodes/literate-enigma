#!/usr/bin/env python3
"""颜色核对（G49）：同一屏的重点词颜色要分得开（用户 2026-10-25 看 26 S10：“ripen into 和rapidly他们的这个颜色太相似了，你换成换成不能这么相似的颜色。”）。
分色、门都在 render.py（分色 / 同屏色差，出片程序和定稿视频核对同一个入口）；这里给踩坑核查用的 查(d, no)、01–24 清单、造坑自检。
用法：python3 颜色核对.py --自检 | --清单"""
import os, sys, json, re
T = os.path.dirname(os.path.abspath(__file__)); V = os.path.dirname(T); sys.path.insert(0, T)
import render as R
def 颜色(d):
    c = R.分色(d); R.unify_colors(c, d['sentences']); return c
def 查(d, no):
    return [f'[G49] 同一屏重点词颜色太像：{x}（出片程序 25 起按色相自动挑色，仍不过的把这一屏的重点词顺序或单元交人处理）' for x in R.同屏色差(d, 颜色(d))] if str(no).isdigit() and int(no) >= R.色相起 else []
def 清单():
    L = ['# 颜色太像清单（程序生成：python3 视频/工具/颜色核对.py --清单）', '',
         '用户 2026-10-25：“ripen into 和rapidly他们的这个颜色太相似了”。25 起出片程序按色相挑色（2026-10-26 从 26 移到 25）（同屏相邻差 ≥60°、任意两个 ≥25°）；01–24 照旧轮流取色、画面不改，这里列出按新门不过的屏，交用户看。', '']
    tot = 0
    for p in sorted(__import__('glob').glob(f'{V}/脚本/[0-9][0-9].json')):
        n = os.path.basename(p)[:2]
        if int(n) >= R.色相起: continue
        d = json.load(open(p)); R.apply_script(d); e = R.同屏色差(dict(d, no=str(R.色相起)), 颜色(d))
        if e: L += [f'## 第{n}篇（{len({x.split()[0] for x in e})} 屏）', ''] + [f'- {x}' for x in e] + ['']; tot += len({x.split()[0] for x in e})
    open(f'{V}/制作记录/颜色太像清单.md', 'w').write('\n'.join(L) + '\n'); return tot
def 自检():
    f = []
    s = {'chunks': [{'en': 'a **rough** **jumble** **ripened** **rapidly** **into** **coherent** grammar, **entirely**', 'zh': '**粗糙的**(rough)**大杂烩**(jumble)**迅速**(rapidly)**发展成**(ripened into)**连贯的**(coherent)**完全**(entirely)', 'align': []}]}
    d = {'no': '26', 'sentences': [s]}
    旧 = {'rough': (251, 146, 60), 'jumble': (45, 212, 191), 'ripened': (248, 113, 113), 'rapidly': (251, 191, 36), 'into': (248, 113, 113), 'coherent': (244, 114, 182), 'entirely': (74, 222, 128)}
    R.unify_colors(旧, d['sentences'])
    if not any('ripened into↔rapidly' in x for x in R.同屏色差(d, 旧)): f.append('没抓到：26 S10 ripened into（珊瑚红）↔rapidly（琥珀黄）相邻颜色太像（G49 重放）')
    if R.同屏色差(d, 颜色(d)): f.append(f'新分色还不合格：{R.同屏色差(d, 颜色(d))[:2]}')
    if R.同屏色差(dict(d, no='24'), 旧): f.append('误报：01–24 不回头查')
    big = {'no': '26', 'sentences': [{'chunks': [{'en': ' '.join(f'**w{i}**' for i in range(10)), 'zh': '', 'align': []}]}]}
    if R.同屏色差(big, 颜色(big)): f.append('一屏 10 个单元，新色板应能全部分开（两两 ≥25°、不重复）')
    for n_ in (11, 13):   # K115（29 S6 同屏 11 个单元）：11 个用补的第 11 色全部分开；13 个只许离开 ≥5 个单元的相近，相邻照样 ≥60°
        bn = {'no': '26', 'sentences': [{'chunks': [{'en': ' '.join(f'**w{i}**' for i in range(n_)), 'zh': '', 'align': []}]}]}
        if R.同屏色差(bn, 颜色(bn)): f.append(f'一屏 {n_} 个单元，分色后还不合格：{R.同屏色差(bn, 颜色(bn))[:2]}')
    P_ = R.PAL26 + R.PAL补; e13 = {'no': '26', 'sentences': [{'chunks': [{'en': ' '.join(f'**v{i}**' for i in range(13)), 'zh': '', 'align': []}]}]}
    近 = {f'v{i}': P_[[0, 5, 2, 7, 4, 9, 6, 1, 8, 3, 10, 0, 5][i]] for i in range(13)}; 近['v2'] = P_[0]   # v0 和 v2 只隔 2 个单元却同色
    if not any('v0↔v2' in x for x in R.同屏色差(e13, 近)): f.append('没抓到：一屏 13 个单元，隔 2 个单元的两个用同一种颜色')
    远_ = {f'v{i}': P_[[0, 5, 2, 7, 4, 9, 6, 1, 8, 3, 10, 0, 5][i]] for i in range(13)}   # v0/v11 同色、v1/v12 同色，都隔 ≥5 个单元
    if any('v0↔v11' in x or 'v1↔v12' in x for x in R.同屏色差(e13, 远_)): f.append('误报：一屏 13 个单元，隔 ≥5 个单元的同色也报了')
    # K140：重点词颜色 用户指定的颜色要用上，同屏别的单元围着它挑色、仍然分得开；两个相邻单元都被指定成相近的颜色，门照样报
    ov = {'no': '34', '重点词颜色': {'puzzle': '#FBBF24'}, 'sentences': [{'chunks': [{'en': 'a **simple** **puzzle** that **hooked** **millions**', 'zh': '', 'align': []}]}]}
    if 颜色(ov).get('puzzle') != (251, 191, 36): f.append('没用上：重点词颜色 指定的 puzzle 颜色（K140）')
    if R.同屏色差(ov, 颜色(ov)): f.append(f'指定颜色后同屏还不合格：{R.同屏色差(ov, 颜色(ov))[:2]}（K140）')
    ov2 = dict(ov, 重点词颜色={'puzzle': '#FBBF24', 'simple': '#FBC024'})
    if not R.同屏色差(ov2, 颜色(ov2)): f.append('没抓到：两个相邻单元被指定成几乎一样的颜色（K140）')
    dup = {'no': '26', 'sentences': [{'chunks': [{'en': '**a1** x **b2** y **c3**', 'zh': '', 'align': []}]}]}
    if not R.同屏色差(dup, {'a1': (251, 191, 36), 'b2': (56, 189, 248), 'c3': (251, 191, 36)}): f.append('没抓到：同屏两个不同重点词用同一种颜色（一律不许，不设口子）')
    s11 = {'no': '26', 'sentences': [{'chunks': [{'en': 'by **American Sign Language** **linguist**', 'zh': '', 'align': []}]}]}
    if not any('american sign language↔linguist' in x for x in R.同屏色差(s11, {'american sign language': (167, 139, 250) if False else (248, 113, 113), 'linguist': (251, 191, 36)})): f.append('没抓到：26 S11 American Sign Language（浅橙红）↔linguist（琥珀黄）相邻（G49 第二个样本）')
    s1 = {'no': '26', 'sentences': [{'chunks': [{'en': 'their **wrists** **flicking**', 'zh': '', 'align': []}]}]}
    if not any('wrists↔flicking' in x for x in R.同屏色差(s1, {'wrists': (248, 113, 113), 'flicking': (251, 191, 36)})): f.append('没抓到：26 S1 wrists↔flicking 相邻颜色太像（G49 第三个样本）')
    f += 各算各的()
    return ['颜色核对 自检：' + x for x in f]
def 各算各的(files=None):
    """G50：工具目录里自己给重点词配色的程序（调 unify_colors 的）都要用出片程序的同一个分色 render.分色（抽屏 26 S10 画出旧配色，和成片不一致）"""
    out = []
    if files is None:
        假 = 各算各的({'假抽屏.py': "colors={}\nfor w in ws: colors[w]=R.PAL[i%8]\nR.unify_colors(colors,d['sentences'])\n"})
        if not 假: out.append('没抓到：造的“假抽屏.py 自己轮流取色”（G50 重放）')
        files = {fn: open(f'{T}/{fn}', errors='ignore').read() for fn in sorted(os.listdir(T)) if fn.endswith('.py')}
    for fn, t in files.items():
        if fn in ('render.py', '颜色核对.py', '排版自检.py'): continue   # 排版自检 用自造的测试颜色，不给实际篇目配色
        if 'unify_colors(' in t and not re.search(r'分色\(|颜色\(', t): out.append(f'没抓到：{fn} 自己算颜色，没用出片程序的分色（render.分色 / 颜色核对.颜色）（G50）')
    return out
if __name__ == '__main__':
    if '--自检' in sys.argv:
        e = 自检(); print('\n'.join(e) or '颜色核对 自检通过（26 S1、S10、S11 浅橙红↔琥珀黄相邻必停、同屏重复同色必停、新分色合格、10 个单元也分得开、01–24 不回头查）'); sys.exit(1 if e else 0)
    if '--清单' in sys.argv: print(f'颜色太像清单：01–24 共 {清单()} 屏，写进 制作记录/颜色太像清单.md'); sys.exit(0)
    print(__doc__)
