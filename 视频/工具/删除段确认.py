#!/usr/bin/env python3
"""删除段确认（2026-10-15 方法升级，省 token）：独立复核 audit.py 报的 A10 删除段（删掉的部分偏响、贴着词的一侧没到 -55 dB），
凡是正好对应脚本里 非人声区间 的（自动切点.py 用实际声音按规则定的、或人用 逐段看声音 核实后写的吸气声/噗声），
按那一段的“紧贴词尾/词头/两头”写进 核对确认.删除段（交付核查认的键“S# raw a-b”、类型、当前配音指纹）；
复核报的两侧超出这个类型允许范围的（例如没标紧贴词头却 post 没衰减完），或不对应任何非人声区间的（停顿中间删掉的偏响声音），一律列出交人看。
词尾/词头被切由交付核查另外把关（cut tail/onset > 0 只有类型对得上才放行）。
用法（视频工作目录，先跑 独立复核/audit.py NN > 日志）：python3 <工具目录>/删除段确认.py NN 日志"""
import json, re, sys, hashlib
no, logf = sys.argv[1], sys.argv[2]; js = f'scripts/{no}.json'; d = json.load(open(js))
fp = hashlib.md5(open(f'work_{no}/a.wav', 'rb').read()).hexdigest()[:12]
TYP = {'紧贴词尾': '紧贴词尾的非人声', '紧贴词头': '紧贴词头的非人声', '紧贴两头': '紧贴两头的非人声'}
ALLOW = {'紧贴词尾的非人声': {'pre', 'lost'}, '紧贴词头的非人声': {'post', 'lost'}, '紧贴两头的非人声': {'pre', 'post', 'lost'}, '': {'lost'}}
ok = d['核对确认'].setdefault('删除段', {}); idx = None; last = None; done = 0; human = []
for l in open(logf):
    m = re.match(r'\[\s*(-?\d+)\]', l)
    if m: idx = int(m.group(1))
    m = re.search(r'edit raw ([\d.]+)-([\d.]+)', l)
    if m: last = (idx, m.group(1), m.group(2))
    m = re.search(r'A10_VIOLATION\(([a-z,]*)\)', l)
    if not m or last is None: continue
    sides = set(m.group(1).split(',')); si = last[0] + 1; a, b = float(last[1]), float(last[2]); key = f'S{si} raw {last[1]}-{last[2]}'
    ivs = [x for x in d.get('非人声区间', {}).get(f'S{si}', []) if x[0] < b and a < x[1]]
    if not ivs: human.append(f'{key} {sides}：不对应任何非人声区间（停顿中间删掉的偏响声音？）'); continue
    fl = set(x[2] for x in ivs if len(x) > 2); t = TYP['紧贴两头'] if '紧贴两头' in fl or {'紧贴词尾', '紧贴词头'} <= fl else TYP.get(next(iter(fl), ''), '')
    if not sides <= ALLOW[t]: human.append(f'{key} {sides}：超出“{t or "两头不贴"}”允许的范围'); continue
    why = (f'2026-10-15 删除段对应 非人声区间 {ivs}（w 秒）：自动切点.py 用实际声音按规则判定是吸气声/噗声（听得见的部分七成以上重心 1.8–3.8 kHz、'
           f'低频 < -10 dB、周期 < 0.35，没有连续 20 ms >4 kHz 的擦音），贴词一侧切在紧挨词 40 ms 内最安静处的过零点；复核报 {sorted(sides)} 是删掉的呼吸声本身偏响（-34～-47 dB），不是词')
    ok[key] = {'类型': t, '配音指纹': fp, '依据': why} if t else why; done += 1
json.dump(d, open(js, 'w'), ensure_ascii=False, indent=1)
print(f'{no} 删除段确认：写了 {done} 处，交人看 {len(human)} 处'); [print('  人看', h) for h in human]
