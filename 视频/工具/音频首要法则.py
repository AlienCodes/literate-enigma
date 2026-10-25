#!/usr/bin/env python3
"""音频首要法则（2026-10-25 用户：“每次只要开始我都要先读一下这个音频的这个要求我们之前踩过的坑，具体要怎么去想方设法做出最高……质量的音频”）
视频/音频首要法则.md 由本程序从 CLAUDE.md 首要法则（用户原话）、《制作硬性标准与踩坑总结》一、音频的硬性标准、踩坑总表里的全部音频坑自动生成，
不手抄：踩坑总表加了音频坑、标准改了，文件没重新生成，核对就停（规则执行核查每次跑）。开工提醒、开工记录 先打印 --要点。
用法：python3 音频首要法则.py [--写入|--核对|--要点|--自检]
"""
import os, re, sys
T = os.path.dirname(os.path.abspath(__file__)); V = os.path.dirname(T); P = os.path.dirname(V)
STD = f'{V}/制作硬性标准与踩坑总结.md'; OUT = f'{V}/音频首要法则.md'; CL = f'{P}/CLAUDE.md'
音频词 = r'声音|配音|响度|停顿|读音|音频|读成|听出|听起来|发音|多音|除阻|辅音|呼吸|底噪|削波|噗|音色|语速'

def 首要(cl):
    m = re.search(r'^0\. (\*\*首要法则.+?)(?=^1\. )', cl, re.M | re.S)
    return m.group(1).strip() if m else None

def 坑(std):
    """(编号, 出了什么问题, 以后怎么防)：一、音频 那一节表里的全部，加上别的节里问题写到声音的"""
    out = []; sec = None
    for line in std.splitlines():
        if line.startswith('## '): sec = line[3:5]
        m = re.match(r'^\| *([A-Z]\d+b?|音\d+) *\|(.*)\|\s*$', line)
        if not m: continue
        c = [x.strip() for x in m.group(2).split('|')]
        if sec == '一、' or re.search(音频词, c[0]): out.append((m.group(1), c[0], c[-1]))
    return out

def 标准(std):
    s = std.split('## 一、音频', 1)[1].split('\n## ', 1)[0]
    return [m.group(1) for m in re.finditer(r'^\d+\. \*\*(.+?)\*\*', s, re.M)]

def 演练(i):
    """这个坑由哪一场演练重放（规则执行表 的“演练”，执行效应演练 自动写）；核对时不比这一段（演练一重跑它就可能改写）"""
    import json
    try: e = json.load(open(f'{T}/规则执行表.json')).get(i, {}).get('演练') or []
    except Exception: e = []
    return ' ｜演练：' + ('；'.join(x.replace('执行效应声音演练 ', '声音演练 ').replace('执行效应演练 ', '主演练 ') for x in e[:3]) if e else '（还没有演练场景）')
去演练 = lambda t: re.sub(r' ｜演练：.*$', '', t, flags=re.M)
短 = lambda x, n: re.sub(r'\s+', ' ', x)[:n] + ('…' if len(x) > n else '')

def 生成(cl, std):
    h = 首要(cl)
    if not h: raise SystemExit('【停止】CLAUDE.md 第一条（0.）不是“首要法则”：音频首要法则要放在最前面')
    ps = 坑(std); ss = 标准(std)
    return '\n'.join([
        '# 音频首要法则（每次开工先读；本文件由 工具/音频首要法则.py --写入 生成，不要手改）', '',
        '## ① 用户原话（CLAUDE.md 0.）', '', h, '',
        f'## ② 音频的全部硬性要求（《制作硬性标准与踩坑总结》一、音频，{len(ss)} 条）', '',
        *[f'{i}. {x}' for i, x in enumerate(ss, 1)], '',
        f'## ③ 踩过的音频坑（{len(ps)} 个；坑 → 现在由哪道门挡）', '',
        *[f'- **{i}** {短(q, 70)} → {短(f, 90)}' + 演练(i) for i, q, f in ps], '',
        '## ④ 做出最高质量音频的步骤（一步不过就停，修好再往下）', '',
        '1. 草稿声音.sh NN：结尾句接点、切点、除阻、停顿、句内响度（26 起出片程序已在拼接前自动调平）、读音待核实清单。',
        '2. 读音核对：人名、地名、机构名、缩写逐个查权威来源；多音词每一处按语境核对（A23/A24）。',
        '3. 音频体检.py：能测的全测（削波、直流、咔哒、齿音、句尾截断、句首突起、语速突变、音色突变），超过 01–24 最差的就停。',
        '4. 交付核查 出片前 / 出片后：停顿、纯人声、响度（整句、句内分段）、独立复核逐样本比对、音频体检；音频门的“确认”只认实测数据（G38）。',
        '5. 发给用户的声音只用出片程序生成、一次只发一个、先过全部核查（A25）。', ''])

def 自检():
    cl = open(CL).read(); std = open(STD).read(); f = []
    ps = 坑(std)
    if not ps: return ['自检前提不成立：踩坑总表里找不到音频坑']
    i0 = ps[0][0]; std2 = '\n'.join(l for l in std.splitlines() if not re.match(rf'^\| *{i0} *\|', l))
    if 去演练(生成(cl, std2)) == 去演练(生成(cl, std)): f.append(f'没抓到：踩坑总表删掉 {i0}，生成的首要法则没变（核对发现不了漏坑）')
    global 演练
    原 = 演练; 演练 = lambda i: ' ｜演练：（还没有演练场景）' if i == ps[0][0] else 原(i)
    if '还没有演练场景' not in 生成(cl, std): f.append('没抓到：音频坑没有演练重放')
    演练 = 原
    if 首要(cl.replace('0. **首要法则', '0. **别的', 1)) is not None: f.append('没抓到：CLAUDE.md 第一条不是首要法则')
    if '25 S2' not in 生成(cl, std) and not any('句内' in q or '句内' in x for _, q, x in ps): f.append('没抓到：25 S2 句内一段变小（G36）不在音频坑里')
    return f

if __name__ == '__main__':
    a = sys.argv[1:]
    if '--自检' in a:
        e = 自检(); print('\n'.join(e) or '音频首要法则 自检通过（删一条音频坑必被发现、第一条不是首要法则必停、G36 在音频坑里）'); sys.exit(1 if e else 0)
    t = 生成(open(CL).read(), open(STD).read())
    if '--写入' in a: open(OUT, 'w').write(t); print(f'已写 {OUT}'); sys.exit(0)
    if '--要点' in a:
        cl = open(CL).read(); ps = 坑(open(STD).read())
        print('【音频首要法则（用户 2026-10-25：音频是最重要的环节，坚决不可以出现任何问题）】开工先读 视频/音频首要法则.md；踩过的音频坑：')
        print('\n'.join(f'  {i} {短(q, 40)}' for i, q, _ in ps)); sys.exit(0)
    if not os.path.exists(OUT) or 去演练(open(OUT).read()) != 去演练(t):
        print('【停止】视频/音频首要法则.md 与 CLAUDE.md 首要法则、踩坑总表的音频坑、音频硬性标准对不上（漏了或改了没重新生成）：python3 视频/工具/音频首要法则.py --写入'); sys.exit(1)
    缺 = [i for i, _, _ in 坑(open(STD).read()) if '还没有演练场景' in 演练(i)]
    if 缺: print(f'提示：这些音频坑还没有演练重放：{缺}（执行效应演练 跑完会写上；没有场景的算缺口，缺口基线只许减少，演练那边就停）')   # 新坑刚写进来时演练还没跑，这里停会把演练自己挡住
    print(f'音频首要法则 与踩坑总表、标准一致（{len(坑(open(STD).read()))} 个音频坑，每个都有演练重放）')
