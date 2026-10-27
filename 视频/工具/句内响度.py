#!/usr/bin/env python3
"""句内响度（2026-10-25，用户看 25 S2：“这块这个声音在这一块声响是不是变小了？是不是没有统计起来？你帮我认真核查一下。”）
整句响度在 ±2 LU 内，句内逗号停顿前后两段却差 3～5 LU，听起来一段突然变小。这个程序按出片程序记下的分段（work_NN/分段.json）
量 a.wav 里每句每段的响度（与交付核查的门同一个量法：响度一致性核对.py 的 段响度），句内相邻两段差超过 IN_ADJ 的句子，
把偏离各段中位数超过 1 LU 的段算出增益（拉回中位数，0.5 dB 一档，累计 ±6 dB 以内），--写入 写进脚本 "分段增益dB"。
只调音量（接点在标点停顿的静音里），不改音色。草稿声音.sh 自动跑：写入后重建，再查一遍。

用法（视频工作目录）：python3 句内响度.py NN [--写入]；python3 句内响度.py --自检
"""
import sys, os, json, tempfile, subprocess, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import 响度一致性核对 as R

def 量(wav, seg_rec, TM=None):
    """{句: [(这一组的段号, 起, 止, 响度)]}：后面停顿 < IN_GAP 的段（列举逗号 0.2 秒）并进下一段，与门的切法一致。"""
    TM = R.momentary(wav) if TM is None else TM; out = {}
    for s, rec in seg_rec.items():
        gs = [[rec[0]]]
        for r0, r in zip(rec, rec[1:]):
            if (r0['停顿'] or 0) >= R.IN_GAP: gs.append([r])
            else: gs[-1].append(r)
        out[s] = [([r['段'] for r in g], g[0]['时刻'][0], g[-1]['时刻'][1], R.段响度(TM, g[0]['时刻'][0], g[-1]['时刻'][1])) for g in gs]
    return out, TM

def 算增益(m, TM, old):
    """{句: {段号: 新增益}}：只算有相邻两组超标的句子。"""
    new = {}
    for s, gs in m.items():
        L = [g[3] for g in gs]
        if not any(x is not None and y is not None and abs(y - x) > R.IN_ADJ for x, y in zip(L, L[1:])): continue
        I = float(np.median([x for x in L if x is not None]))   # 参照：各段响度的中位数（整句综合响度会被段间静音块拉低）
        for ks, _, _, v in gs:
            if v is None or abs(I - v) <= 1.0: continue
            dlt = round((I - v) * 2) / 2
            for k in ks:
                g = max(-6.0, min(6.0, float(old.get(s, {}).get(str(k), 0)) + dlt))
                if g: new.setdefault(s, {})[str(k)] = g
    return new

def 自检():
    """造一句四段的“声音”（0.4 秒停顿隔开），第 3 段轻 4 dB：必须只给第 3 段算出约 +4 dB（别的段不动）；四段一样响的句子不算增益。"""
    SR = R.SR; rng = np.random.default_rng(1); f = []
    with tempfile.TemporaryDirectory() as td:
        def mk(gs_):
            a = [np.zeros(int(2 * SR))]; rec = []; t = 2.0
            for i, g in enumerate(gs_):
                n = int(1.2 * SR); x = rng.standard_normal(n) * 0.05 * 10 ** (g / 20) * np.hanning(n) ** 0.1
                rec.append({'段': i + 1, '原始': [0, 0], '停顿': 0.4 if i < len(gs_) - 1 else None, '时刻': [t, t + 1.2]})
                a += [x, np.zeros(int(0.4 * SR))]; t += 1.6
            a.append(np.zeros(int(2 * SR))); w = os.path.join(td, f'{len(gs_)}{gs_[2]}.wav')
            subprocess.run([R.FF, '-loglevel', 'error', '-y', '-f', 's16le', '-ar', str(SR), '-ac', '1', '-i', '-', w], input=(np.concatenate(a) * 32767).astype(np.int16).tobytes(), check=True)
            return w, {'S1': rec}
        w, sr = mk([0, 0, -4, 0]); m, TM = 量(w, sr); g = 算增益(m, TM, {})
        if set(g.get('S1', {})) != {'3'} or not 3.0 <= g['S1']['3'] <= 4.5: f.append(f'没抓到：第 3 段轻 4 dB，算出的增益是 {g}（应只有第 3 段约 +4 dB）')
        g2 = 算增益(m, TM, {'S1': {'3': 1.0}})
        if not 4.0 <= g2.get('S1', {}).get('3', 0) <= 5.5: f.append(f'没抓到：已有 +1 dB 时没有累加（{g2}）')
        w, sr = mk([0, 0, 0, 0]); m, TM = 量(w, sr)
        if 算增益(m, TM, {}): f.append('误报：四段一样响也算出了增益')
    import subprocess as _sp, tempfile as _tf   # 缺前提（没出过声音、没有 分段.json）必须停，不许接着量（G79 门变异）
    r = _sp.run([sys.executable, os.path.abspath(__file__), '99'], cwd=_tf.mkdtemp(prefix='句内响度自检_'), capture_output=True, text=True)
    if '【停止】没有 work_99/分段.json' not in r.stdout + r.stderr: f.append('没抓到：没有 work_NN/分段.json 也开量（缺前提要停）')
    return f

if __name__ == '__main__':
    if '--自检' in sys.argv:
        e = 自检(); print('\n'.join(e) or '句内响度 自检通过（一段轻 4 dB 只给这一段算出约 +4 dB、已有增益累加、一样响不误报）'); sys.exit(1 if e else 0)
    no = sys.argv[1]; sj = f'work_{no}/分段.json'
    if not os.path.exists(sj): raise SystemExit(f'【停止】没有 {sj}：先用现行出片程序出一次声音（快速重建核查.sh {no}）')
    d = json.load(open(f'scripts/{no}.json')); old = d.get('分段增益dB', {})
    m, TM = 量(f'work_{no}/a.wav', json.load(open(sj))); new = 算增益(m, TM, old)
    for s, v in new.items(): print(f'{no} {s} 分段增益dB {old.get(s, {})} → {v}')
    if '--写入' in sys.argv and new:
        d.setdefault('分段增益dB', {}).update(new); json.dump(d, open(f'scripts/{no}.json', 'w'), ensure_ascii=False, indent=1)
        print(f'{no} 已写入 {len(new)} 句的分段增益dB：重建后再查')
    print(f'{no} 句内相邻两段超过 {R.IN_ADJ} LU 的句子：{len(new)}')
