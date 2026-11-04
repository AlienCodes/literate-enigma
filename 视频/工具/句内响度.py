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
    """{句: [(这一组的段号, 起, 止, 响度)]}：K144（40 S8：门量成片报后段轻 2.6 LU，这里量 a.wav、按出片程序记的停顿并段，报 0，永远修不好）：
    切段、量响度全用门的函数（响度一致性核对.分段 / 段响度：句内 ≥IN_GAP 秒的静音切段），段号按出片程序记的各段中点落在哪一组。"""
    TM = R.momentary(wav) if TM is None else TM; a = R.pcm(wav); out = {}
    rg = [(k, v[0]['时刻'][0], v[-1]['时刻'][1]) for k, v in seg_rec.items()]
    for (s, _, _), cur in zip(rg, R.分段(a, [(x, y) for _, x, y in rg])):
        out[s] = [([r['段'] for r in seg_rec[s] if x - 1e-6 <= (r['时刻'][0] + r['时刻'][1]) / 2 <= y + 1e-6], x, y, R.段响度(TM, x, y)) for x, y in cur]
    return out, TM

def 成片声(wav, td):
    """K144：a.wav 先过出片程序同一套后期（../tts/AF.txt + AAC 256k，make_video 出 a.m4a/成片的写法），与门量的成片 mp4 一致；没有 AF.txt 就量原 wav"""
    af = os.path.join(os.path.dirname(os.path.abspath(wav)), '..', '..', 'tts', 'AF.txt')
    if not os.path.exists(af): return wav
    o = os.path.join(td, 'a.m4a'); subprocess.run([R.FF, '-y', '-loglevel', 'error', '-i', wav, '-af', open(af).read().strip(), '-c:a', 'aac', '-b:a', '256k', o], check=True); return o

def 共段(m, seg_rec):
    """K163（49 S14 无标点，中间一处停顿，门切成两组、按标点只有 1 段）：{句: {段号: [(组中点在段内的位置 0–1, 组号)]}}，一段里落着两组以上的才列。
    这种段用 分段增益dB 只能整段（= 整句）抬压，句内前后差不变、整句反而偏离全片，改写 段内渐变dB。"""
    out = {}
    for s, gs in m.items():
        for r in seg_rec.get(s, []):
            t0, t1 = r['时刻']; hit = [((max(x, t0) + min(y, t1)) / 2, j) for j, (_, x, y, _) in enumerate(gs) if min(y, t1) - max(x, t0) > 0.5 * (y - x)]
            if len(hit) > 1 and t1 > t0: out.setdefault(s, {})[str(r['段'])] = [((c - t0) / (t1 - t0), j) for c, j in hit]
    return out

def 算增益(m, TM, old, seg_rec=None, old_rg=None):
    """{句: {段号: 新增益}}：只算有相邻两组超标的句子。给了 seg_rec 时第二个返回值是 段内渐变dB {句: {段号: [开头, 结尾]}}（K163 一段里有两组以上的段）。"""
    new = {}; rg = {}; sh = 共段(m, seg_rec) if seg_rec else {}
    for s, gs in m.items():
        L = [g[3] for g in gs]
        if not any(x is not None and y is not None and abs(y - x) > R.IN_ADJ for x, y in zip(L, L[1:])): continue
        I = float(np.median([x for x in L if x is not None]))   # 参照：各段响度的中位数（整句综合响度会被段间静音块拉低）
        for ks, _, _, v in gs:
            if v is None or abs(I - v) <= 1.0: continue
            dlt = round((I - v) * 2) / 2
            for k in ks:
                if str(k) in sh.get(s, {}): continue
                g = max(-6.0, min(6.0, float(old.get(s, {}).get(str(k), 0)) + dlt))
                if g: new.setdefault(s, {})[str(k)] = g
        for k, hs in sh.get(s, {}).items():   # 段内从第一组的差渐变到最后一组的差（不外推，偏保守；不够时下一轮在原渐变上再加）
            hs = sorted(hs); d0, d1 = [(I - L[j]) if L[j] is not None else 0.0 for _, j in (hs[0], hs[-1])]
            o0, o1 = (old_rg or {}).get(s, {}).get(k, [0, 0])
            g0, g1 = [max(-6.0, min(6.0, round((float(o) + x) * 2) / 2)) for o, x in ((o0, d0), (o1, d1))]
            if (g0, g1) != (float(o0), float(o1)): rg.setdefault(s, {})[k] = [g0, g1]
    return (new, rg) if seg_rec is not None else new

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
        # K157 好样本：第 3 段轻 4 dB，这一句有停顿处除阻 → --写入 照常写分段增益（K156 时不写，K157 起出片程序和独立复核都收）
        import shutil
        w, sr = mk([0, 0, -4, 0]); wd = tempfile.mkdtemp(prefix='句内响度K157_'); os.makedirs(f'{wd}/work_99'); os.makedirs(f'{wd}/scripts')
        shutil.copy(w, f'{wd}/work_99/a.wav'); json.dump(sr, open(f'{wd}/work_99/分段.json', 'w'))
        json.dump({'no': '99', '停顿处除阻': {'S1': {'1': [1.0, 1.005, 't']}}}, open(f'{wd}/scripts/99.json', 'w'))
        subprocess.run([sys.executable, os.path.abspath(__file__), '99', '--写入'], cwd=wd, capture_output=True, text=True)
        if '3' not in json.load(open(f'{wd}/scripts/99.json')).get('分段增益dB', {}).get('S1', {}): f.append('误拦：有停顿处除阻的句子没写分段增益（K157）')
        shutil.rmtree(wd, ignore_errors=True)
        w, sr = mk([0, 0, -3.5, 0]); sr['S1'][1]['停顿'] = 0.25   # K144 坏样本：记的停顿比实际短（门照样在 0.4 秒静音处切开、报第 3 段轻），增益必须照门的切法算出来
        m, TM = 量(w, sr); g = 算增益(m, TM, {}); js = os.path.join(td, 'seg.json'); json.dump(sr, open(js, 'w')); rs = R.句内报(R.句内(w, None, TM, js))
        if not rs: f.append('自检前提不成立：门没报第 3 段轻 3.5 dB')
        elif set(g.get('S1', {})) != {'3'}: f.append(f'没抓到：门报了 {[(r[0], r[1]) for r in rs]}，这里算出的增益是 {g}（量法和门不一致，K144 40 S8）')
        # K163 坏样本（49 S14）：一句没有 , ; :（按标点 1 段），中间 0.4 秒停顿，前半响 3.5 dB：必须写段内渐变（前低后高），不许写整段分段增益；原来误写的整段增益要撤掉
        n = int(1.2 * SR); a2 = [np.zeros(2 * SR)]
        for g in (0, -3.5): a2 += [rng.standard_normal(n) * 0.05 * 10 ** (g / 20) * np.hanning(n) ** 0.1, np.zeros(int(0.4 * SR))]
        a2.append(np.zeros(2 * SR)); w = os.path.join(td, 'k163.wav')
        subprocess.run([R.FF, '-loglevel', 'error', '-y', '-f', 's16le', '-ar', str(SR), '-ac', '1', '-i', '-', w], input=(np.concatenate(a2) * 32767).astype(np.int16).tobytes(), check=True)
        sr = {'S1': [{'段': 1, '原始': [0, 0], '停顿': None, '时刻': [2.0, 4.8]}]}
        m, TM = 量(w, sr); g, rgk = 算增益(m, TM, {}, sr, {})
        if g or not rgk.get('S1', {}).get('1') or not rgk['S1']['1'][0] < 0 < rgk['S1']['1'][1]: f.append(f'没抓到：无标点一句前半响 3.5 dB，算出 分段增益 {g}、段内渐变 {rgk}（应只有段内渐变、前低后高，K163 49 S14）')
        wd = tempfile.mkdtemp(prefix='句内响度K163_'); os.makedirs(f'{wd}/work_99'); os.makedirs(f'{wd}/scripts')
        shutil.copy(w, f'{wd}/work_99/a.wav'); json.dump(sr, open(f'{wd}/work_99/分段.json', 'w')); json.dump({'no': '99', '分段增益dB': {'S1': {'1': 3.0}}}, open(f'{wd}/scripts/99.json', 'w'))
        subprocess.run([sys.executable, os.path.abspath(__file__), '99', '--写入'], cwd=wd, capture_output=True, text=True); d9 = json.load(open(f'{wd}/scripts/99.json'))
        if d9.get('分段增益dB', {}).get('S1', {}).get('1') or not d9.get('段内渐变dB', {}).get('S1', {}).get('1'): f.append(f'没抓到：--写入 没撤掉误写的整段增益或没写段内渐变（{d9}）')
        shutil.rmtree(wd, ignore_errors=True)
    import subprocess as _sp, tempfile as _tf   # 缺前提（没出过声音、没有 分段.json）必须停，不许接着量（G79 门变异）
    r = _sp.run([sys.executable, os.path.abspath(__file__), '99'], cwd=_tf.mkdtemp(prefix='句内响度自检_'), capture_output=True, text=True)
    if '【停止】没有 work_99/分段.json' not in r.stdout + r.stderr: f.append('没抓到：没有 work_NN/分段.json 也开量（缺前提要停）')
    return f

if __name__ == '__main__':
    if '--自检' in sys.argv:
        e = 自检(); print('\n'.join(e) or '句内响度 自检通过（一段轻 4 dB 只给这一段算出约 +4 dB、已有增益累加、一样响不误报）'); sys.exit(1 if e else 0)
    no = sys.argv[1]; sj = f'work_{no}/分段.json'
    if not os.path.exists(sj): raise SystemExit(f'【停止】没有 {sj}：先用现行出片程序出一次声音（快速重建核查.sh {no}）')
    d = json.load(open(f'scripts/{no}.json')); old = d.get('分段增益dB', {}); org = d.get('段内渐变dB', {}); rec = json.load(open(sj))
    with tempfile.TemporaryDirectory() as td: m, TM = 量(成片声(f'work_{no}/a.wav', td), rec)
    new, rg = 算增益(m, TM, old, rec, org)
    # K156→K157：原来有停顿处除阻的句子出片程序不收分段增益（停下不重建，下一轮按旧声音再加，累加到 ±6 dB）；K157 起独立复核先乘增益再换供体，这种句子也照常写
    drop = {s: [k for k in v if k in old.get(s, {})] for s, v in rg.items()}   # K163：这种段原来写的整段增益是误算（整句抬压），撤掉；渐变按相对差算，撤掉不影响句内前后
    for s, v in new.items(): print(f'{no} {s} 分段增益dB {old.get(s, {})} → {v}')
    for s, v in rg.items(): print(f'{no} {s} 段内渐变dB {org.get(s, {})} → {v}' + (f'（撤掉误写的分段增益dB 段 {drop[s]}）' if drop[s] else ''))
    if '--写入' in sys.argv and (new or rg):
        d.setdefault('分段增益dB', {}).update(new)
        for s, v in rg.items():
            d.setdefault('段内渐变dB', {}).setdefault(s, {}).update(v)
            for k in drop[s]: d['分段增益dB'].get(s, {}).pop(k, None)
            if s in d['分段增益dB'] and not d['分段增益dB'][s]: del d['分段增益dB'][s]
        if not d['分段增益dB']: del d['分段增益dB']
        json.dump(d, open(f'scripts/{no}.json', 'w'), ensure_ascii=False, indent=1)
        print(f'{no} 已写入 {len(set(new) | set(rg))} 句的分段增益dB/段内渐变dB：重建后再查')
    print(f'{no} 句内相邻两段超过 {R.IN_ADJ} LU 的句子：{len(set(new) | set(rg))}')
