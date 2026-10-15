#!/usr/bin/env python3
"""确认按位置迁移（2026-10-15 方法升级）：重建后配音指纹变了，核对确认.非人声 按规矩作废；但确认是按“S# w 起–止s”（每句原始合成 w 里的秒）
写的，w 是配音模型的输出，删别处的非人声不会改它。本程序把依据里写着“S# w a–bs”的确认，对到当前 疑点清单（dossier_NN.json）里同一句、
w 位置重叠的疑点，换成当前指纹和当前成片时刻的键；这一段 w 碰到本句任何 非人声区间/停顿删除区间 的不迁（声音真变了，交人重看）。
在视频工作目录下运行（先跑 疑点清单.py NN）：python3 <工具目录>/确认按位置迁移.py NN"""
import json, re, sys, hashlib
no = sys.argv[1]; js = f'scripts/{no}.json'; d = json.load(open(js)); D = json.load(open(f'dossier_{no}.json'))
fp = hashlib.md5(open(f'work_{no}/a.wav', 'rb').read()).hexdigest()[:12]
cf = d['核对确认'].get('非人声', {}); keep = {k: v for k, v in cf.items() if v.get('配音指纹') == fp}; moved = 0; drop = []
for k, v in cf.items():
    if v.get('配音指纹') == fp: continue
    m = re.search(r'S(\d+) w ([\d.]+)–([\d.]+)s', v.get('依据', ''))
    if not m: drop.append(k); continue
    si, a, b = int(m.group(1)), float(m.group(2)), float(m.group(3))
    ivs = [x[:2] for x in d.get('非人声区间', {}).get(f'S{si}', [])] + [x[:2] for x in d.get('停顿删除区间', {}).get(f'S{si}', {}).values() if isinstance(x, list)]
    ivs += [[x[0] - 0.01, x[0] + 0.08] for x in d.get('词尾除阻', {}).get(f'S{si}', {}).values() if isinstance(x, list)]   # 移植的除阻也改了声音
    if any(x < b and a < y for x, y in ivs): drop.append(k + '（碰到删除区间）'); continue
    for e in D:
        if e['si'] == si and e['w0'] < b and a < e['w1']:
            keep[f"{e['t0']:.2f}–{e['t1']:.2f}s"] = dict(v, 配音指纹=fp); moved += 1
d['核对确认']['非人声'] = keep; json.dump(d, open(js, 'w'), ensure_ascii=False, indent=1)
print(f'{no} 确认迁移：迁了 {moved} 条，没迁 {len(drop)} 条', drop[:5])
