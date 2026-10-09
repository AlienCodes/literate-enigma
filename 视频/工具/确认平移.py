#!/usr/bin/env python3
"""确认平移（2026-10-09，A21 重建时用；以后任何重建都用）：配音重建后，核对确认按 a.wav 的配音指纹作废；但大部分句子的声音一个采样都没变，
只是前面的句子长短变了、整体往后挪了。这个程序逐样本比对新旧 a.wav，把“声音完全没变、只是挪了位置”的确认自动挪到新位置、换上新指纹；
声音变了的（哪怕一个采样）一律不挪，留给人用实际声音重新核实。不做任何判断，只认逐样本相同。
用法（视频工作目录）：python3 确认平移.py NN 旧a.wav [--写入]       不加 --写入 只列出结果
  核对确认.非人声（键 = a.wav 里的时段）：旧时段前后各 20 ms 在新 a.wav 里逐样本找到唯一的同一段 → 新键取 纯人声核对 在新配音里报出的那一处（位置差 ≤10 ms）；
  核对确认.删除段（键 = 原始合成里的区间，与 a.wav 位置无关）：原始合成不变，删掉的是同一段声音 → 只换指纹（复核仍逐处重算两侧是否干净）；
  核对确认.高亮（"开始读" = a.wav 里的时刻）：这一时刻前后各 20 ms 逐样本找到 → 时刻加上位移；
  核对确认.响度骤降（键 = 成片里的时段）：同 非人声 的找法，新键按原来的写法（保留 1 位小数）加上位移；"低" 不变（核查时仍要求这次报的 ≤ 确认时 +0.3 dB）。"""
import sys, os, json, re, hashlib, importlib.util
import numpy as np, soundfile as sf
SR = 24000
T = os.path.dirname(os.path.abspath(__file__))
no, oldp = sys.argv[1], sys.argv[2]
old, _ = sf.read(oldp, dtype='int16'); new, _ = sf.read(f'work_{no}/a.wav', dtype='int16')
fo = hashlib.md5(open(oldp, 'rb').read()).hexdigest()[:12]; fn = hashlib.md5(open(f'work_{no}/a.wav', 'rb').read()).hexdigest()[:12]
spec = importlib.util.spec_from_file_location('pv', f'{T}/纯人声核对.py'); sys.argv_bak = sys.argv
pv_src = open(f'{T}/纯人声核对.py').read().split("if __name__")[0]; pv = {}; exec(pv_src, pv)


def segs(a):
    z = np.append((a == 0).astype(np.int8), 0); runs = []; st = None
    for i, v in enumerate(z):
        if v and st is None: st = i
        if not v and st is not None:
            if (i - st) / SR >= 0.6: runs.append((st, i))
            st = None
    b = [0] + [r[1] for r in runs]; e = [r[0] for r in runs] + [len(a)]
    return [(x, y) for x, y in zip(b, e) if y > x and np.any(a[x:y] != 0)]


so, sn = segs(old), segs(new)
if len(so) != len(sn): sys.exit(f'新旧配音分段数不同（{len(so)} / {len(sn)}），不能平移')


def shift(t0, t1, ctx=0.02):
    """旧 a.wav 的 [t0-ctx, t1+ctx] 在新 a.wav 同一段里逐样本相同的唯一位置 → 位移（秒）；找不到或不唯一 → None"""
    i0 = int(round((t0 - ctx) * SR)); i1 = int(round((t1 + ctx) * SR))
    k = next((j for j, (x, y) in enumerate(so) if x - int(0.6 * SR) <= i0 < y + int(0.6 * SR)), None)
    if k is None: return None
    blk = old[i0:i1]
    if not len(blk) or not np.any(blk != 0): return None
    an = int(np.argmax(np.abs(blk.astype(int)))); x, y = sn[k]; lo = max(0, x - int(0.6 * SR)); hi = min(len(new), y + int(0.6 * SR))
    cand = np.where(new[lo:hi] == blk[an])[0] + lo - an
    hits = [c for c in cand if c >= 0 and c + len(blk) <= len(new) and np.array_equal(new[c:c + len(blk)], blk)]
    return (hits[0] - i0) / SR if len(hits) == 1 else None


d = json.load(open(f'scripts/{no}.json')); cf = d.setdefault('核对确认', {}); rows = []; moved = 0; left = 0
note = f'（{os.path.basename(oldp)} → 新配音：这一段声音逐样本相同，位置挪了 %+.3f 秒；确认平移.py 自动挪，配音指纹 {fo} → {fn}）'
# 非人声
pvs = pv['scan'](new.astype(float) / 32768) if 'scan' in pv else []
nv = cf.get('非人声', {}); out = {}
for k, v in nv.items():
    if not isinstance(v, dict) or v.get('配音指纹') != fo: out[k] = v; continue
    m = re.match(r'([\d.]+)–([\d.]+)s', k); s = shift(float(m.group(1)), float(m.group(2))) if m else None
    f = None if s is None else next((f for f in pvs if abs(f[1] - float(m.group(1)) - s) <= 0.0105 and abs(f[2] - float(m.group(2)) - s) <= 0.0105), None)
    if f is None:
        rows.append(f"非人声 {k}：{'声音变了（找不到逐样本相同的一段）' if s is None else '新配音里这里已经不报了（移植或接长后不再是孤立的声音）'}，不挪"); left += 1; out[k] = v; continue
    nk = pv['key'](f); out[nk] = {**v, '配音指纹': fn, '依据': v.get('依据', '') + note % s}; moved += 1
    rows.append(f'非人声 {k} → {nk}（位移 {s:+.3f} s）')
cf['非人声'] = out
# 删除段：原始合成里的区间，原始合成没变（A21 只在 w 里移植，不改原始合成）→ 换指纹
for k, v in cf.get('删除段', {}).items():
    if isinstance(v, dict) and v.get('配音指纹') == fo:
        v['配音指纹'] = fn; v['依据'] = v.get('依据', '') + f'（原始合成里的区间不变，删掉的是同一段声音；配音指纹 {fo} → {fn}，复核仍逐处重算两侧）'; moved += 1
        rows.append(f'删除段 {k}：换指纹')
# 高亮
for k, v in cf.get('高亮', {}).items():
    if isinstance(v, dict) and v.get('配音指纹') == fo:
        s = shift(float(v['开始读']), float(v['开始读']))
        if s is None: rows.append(f'高亮 {k}：声音变了，不挪'); left += 1; continue
        v['开始读'] = round(float(v['开始读']) + s, 4); v['配音指纹'] = fn; v['依据'] = v.get('依据', '') + note % s; moved += 1
        rows.append(f'高亮 {k} → {v["开始读"]}（位移 {s:+.3f} s）')
# 响度骤降
lq = cf.get('响度骤降', {}); out = {}
for k, v in lq.items():
    m = re.match(r'([\d.]+)–([\d.]+)s', k)
    if not (isinstance(v, dict) and v.get('配音指纹') == fo and m): out[k] = v; continue
    s = shift(float(m.group(1)), float(m.group(2)), 0.0)
    if s is None: rows.append(f'响度骤降 {k}：声音变了，不挪'); left += 1; out[k] = v; continue
    nk = f'{float(m.group(1)) + s:.1f}–{float(m.group(2)) + s:.1f}s'; out[nk] = {**v, '配音指纹': fn, '依据': v.get('依据', '') + note % s}; moved += 1
    rows.append(f'响度骤降 {k} → {nk}（位移 {s:+.3f} s）')
cf['响度骤降'] = out
print('\n'.join(f'{no} {r}' for r in rows)); print(f'{no} 确认平移：挪了 {moved} 处，留给人核实 {left} 处（旧指纹 {fo} → 新指纹 {fn}）')
if '--写入' in sys.argv: json.dump(d, open(f'scripts/{no}.json', 'w'), ensure_ascii=False, indent=1); print('已写入 scripts/%s.json' % no)
