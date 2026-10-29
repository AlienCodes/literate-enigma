#!/usr/bin/env python3
"""确认按位置迁移（2026-10-15 方法升级）：重建后配音指纹变了，核对确认.非人声 按规矩作废；但确认是按“S# w 起–止s”（每句原始合成 w 里的秒）
写的，w 是配音模型的输出，删别处的非人声不会改它。本程序把依据里写着“S# w a–bs”的确认，对到当前 疑点清单（dossier_NN.json）里同一句、
w 位置重叠的疑点，换成当前指纹和当前成片时刻的键；这一段 w 碰到本句任何 非人声区间/停顿删除区间 的不迁（声音真变了，交人重看）。
“碰到”按重叠超过 10 ms 算（K28，27 S12：确认按 10 ms 一格量，w 4.205–4.240 与紧贴词头的非人声区间 4.01–4.206083 只重叠 1 ms，
每次重建都被当成碰到删除区间删掉）；确认整段落在区间里、或盖住整个区间（不到 10 ms 的停顿删除）照旧算碰到。
在视频工作目录下运行（先跑 疑点清单.py NN）：python3 <工具目录>/确认按位置迁移.py NN；--自检"""
import json, re, sys, hashlib
TOL = 0.010

def 碰到(a, b, x, y):
    ov = min(b, y) - max(a, x)
    return ov > TOL or (ov > 0 and (ov >= b - a - 1e-9 or ov >= y - x - 1e-9))

def 自检():
    f = []
    if 碰到(4.205, 4.240, 4.01, 4.206083): f.append('误删：27 S12 词头浊音确认 w 4.205–4.240 只和紧贴词头的区间 4.01–4.206083 重叠 1 ms，被当成碰到')
    if not 碰到(4.10, 4.15, 4.01, 4.206083): f.append('没抓到：确认整段在非人声区间里')
    if not 碰到(2.06, 2.08, 2.065, 2.0725): f.append('没抓到：确认盖住整个 7.5 ms 的停顿删除区间')
    if not 碰到(4.18, 4.24, 4.01, 4.206083): f.append('没抓到：确认和区间重叠 26 ms')
    if 碰到(4.21, 4.24, 4.01, 4.206083): f.append('误删：不重叠也算碰到')
    # K136：两条旧确认依据写同一段 w，迁过去要各认各的（按旧时刻最接近），实测不许互相覆盖
    import tempfile, os, subprocess
    with tempfile.TemporaryDirectory() as td:
        os.makedirs(f'{td}/scripts'); os.makedirs(f'{td}/work_99'); open(f'{td}/work_99/a.wav', 'wb').write(b'x')
        json.dump({'核对确认': {'非人声': {'33.13–33.22s': {'配音指纹': 'old', '依据': 'S3 w 9.785–9.800s', '实测': {'最响dB': -36.2}}, '33.17–33.19s': {'配音指纹': 'old', '依据': 'S3 w 9.785–9.800s', '实测': {'最响dB': -39.1}}}}}, open(f'{td}/scripts/99.json', 'w'), ensure_ascii=False)
        json.dump([{'si': 3, 'w0': 9.78, 'w1': 9.81, 't0': 33.13, 't1': 33.22}, {'si': 3, 'w0': 9.78, 'w1': 9.81, 't0': 33.17, 't1': 33.19}], open(f'{td}/dossier_99.json', 'w'))
        subprocess.run([sys.executable, os.path.abspath(__file__), '99'], cwd=td, capture_output=True)
        c = json.load(open(f'{td}/scripts/99.json'))['核对确认']['非人声']
        if c.get('33.13–33.22s', {}).get('实测', {}).get('最响dB') != -36.2 or c.get('33.17–33.19s', {}).get('实测', {}).get('最响dB') != -39.1: f.append(f'迁移把两条确认的实测弄混了（K136 28 S3）：{c}')
    return f

if sys.argv[1:2] == ['--自检']:
    e = 自检(); print(('✘ 确认按位置迁移 自检：' + '；'.join(e)) if e else '✔ 确认按位置迁移 自检：边上重叠 ≤10 ms 迁、整段在区间里或盖住整个短区间不迁（K28）'); sys.exit(1 if e else 0)
no = sys.argv[1]; js = f'scripts/{no}.json'; d = json.load(open(js)); D = json.load(open(f'dossier_{no}.json'))
fp = hashlib.md5(open(f'work_{no}/a.wav', 'rb').read()).hexdigest()[:12]
cf = d['核对确认'].get('非人声', {}); keep = {k: v for k, v in cf.items() if v.get('配音指纹') == fp}; moved = 0; drop = []; 候选 = {}
for k, v in cf.items():
    if v.get('配音指纹') == fp: continue
    m = re.search(r'S(\d+) w ([\d.]+)–([\d.]+)s', v.get('依据', ''))
    if not m: drop.append(k); continue
    si, a, b = int(m.group(1)), float(m.group(2)), float(m.group(3))
    ivs = [x[:2] for x in d.get('非人声区间', {}).get(f'S{si}', [])] + [x[:2] for x in d.get('停顿删除区间', {}).get(f'S{si}', {}).values() if isinstance(x, list)]
    ivs += [[x[0] - 0.01, x[0] + 0.08] for x in d.get('词尾除阻', {}).get(f'S{si}', {}).values() if isinstance(x, list)]   # 移植的除阻也改了声音
    if any(碰到(a, b, x, y) for x, y in ivs): drop.append(k + '（碰到删除区间）'); continue
    km = re.match(r'([\d.]+)–([\d.]+)s', k); o0, o1 = (float(km.group(1)), float(km.group(2))) if km else (None, None)
    for e in D:
        if e['si'] == si and e['w0'] < b and a < e['w1']:
            nk = f"{e['t0']:.2f}–{e['t1']:.2f}s"; dist = abs(o0 - e['t0']) + abs(o1 - e['t1']) if km else 9e9
            if nk in 候选 and 候选[nk][0] <= dist: continue   # K136（28 S3）：两条旧确认（呼吸声、噗声）依据写同一段 w，迁到同一个新疑点时后一条盖掉前一条、实测对不上；每个新疑点只认旧时刻最接近的那条
            候选[nk] = (dist, dict(v, 配音指纹=fp))
for nk, (_, v) in 候选.items(): keep[nk] = v; moved += 1
d['核对确认']['非人声'] = keep; json.dump(d, open(js, 'w'), ensure_ascii=False, indent=1)
print(f'{no} 确认迁移：迁了 {moved} 条，没迁 {len(drop)} 条', drop[:5])
