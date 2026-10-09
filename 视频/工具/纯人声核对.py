#!/usr/bin/env python3
"""纯人声核对（用户 2026-10-09：“不要有任何的呼吸声 语气声 这些都不要 底噪也不要 就要绝对的纯人声”；踩坑总表 A19）。
在视频工作目录下运行：python3 <工具目录>/纯人声核对.py NN [--自检]
逐句扫配音 work_NN/a.wav（每句以 ≥0.6 秒的数字静音分开；电平都相对本句最响的 5 ms 帧）：
  ① 呼吸声：连续 ≥80 ms 的声音、电平在 -55～-35 dB 之间、没有周期（不是嗓音：20 ms 窗自相关中位数 <0.35）、频谱重心 0.8–4 kHz；
  ② 噗声（嘴唇、声门的低频声）：连续 ≥15 ms、150 Hz 以下占一半以上能量、电平 ≥-55 dB，且前面 30 ms 里没有说话（排除词尾的鼻音）；
  ③ 底噪：数字静音以外、比本句最响低 55 dB 以下的声音，单段超过 50 ms 的（句中词与词之间留下的底噪）。
报出的每一处：是非人声的，写进脚本"非人声区间"/"停顿删除区间"去掉；是词的一部分（如句末 /v/ 的擦音）的，用实际声音（逐 2.5 ms 电平、频谱、周期）核实后
写进 核对确认.非人声：{"12.34–12.56s": {"配音指纹": a.wav 的 md5 前 12 位, "依据": …}}，配音一变确认作废。
自检（阳性对照）：在副本的两处停顿静音里分别放进一段假呼吸声（0.15 秒、-42 dB、1–2.5 kHz 噪声）和一个假噗声（25 ms、90 Hz、-45 dB），必须正好多报出这两处。"""
import sys, os, json, hashlib, numpy as np, soundfile as sf
SR = 24000; F = 120

def per(x):
    x = x - x.mean()
    if np.sqrt(np.mean(x ** 2)) < 1e-9: return 0.0
    ac = np.correlate(x, x, 'full')[len(x) - 1:]; ac = ac / (ac[0] + 1e-12)
    return float(ac[60:343].max())

def spec(x):
    X = np.abs(np.fft.rfft(x * np.hanning(len(x)), n=4096)) ** 2; f = np.fft.rfftfreq(4096, 1 / SR)
    return float((np.sqrt(X) * f).sum() / (np.sqrt(X).sum() + 1e-12)), float(10 * np.log10(X[f < 150].sum() / (X.sum() + 1e-20) + 1e-12))

def segments(a):
    z = np.append((a == 0).astype(np.int8), 0); runs = []; st = None
    for i, v in enumerate(z):
        if v and st is None: st = i
        if not v and st is not None:
            if (i - st) / SR >= 0.6: runs.append((st, i))
            st = None
    b = [0] + [r[1] for r in runs]; e = [r[0] for r in runs] + [len(a)]
    return [(x, y) for x, y in zip(b, e) if y - x > SR * 0.2 and np.abs(a[x:y]).max() > 0]

def scan(a):
    found = []
    for s0, s1 in segments(a):
        seg = a[s0:s1]; m = len(seg) // F
        r = np.sqrt(np.mean(seg[:m * F].reshape(m, F) ** 2, axis=1)); ref = r.max()
        e = 20 * np.log10(r / ref + 1e-9); dz = np.array([np.all(seg[k * F:(k + 1) * F] == 0) for k in range(m)])
        t = lambda k: (s0 + k * F) / SR
        # ① 呼吸声
        k = 0
        while k < m:
            if not (-55 <= e[k] < -35) or dz[k]: k += 1; continue
            j = k
            while j < m and -55 <= e[j] < -35 and not dz[j]: j += 1
            if (j - k) * F / SR >= 0.08:
                x = seg[k * F:j * F]; c, lo = spec(x)
                pp = np.median([per(seg[i:i + 480]) for i in range(k * F, max(k * F + 1, j * F - 480), 240)])
                if pp < 0.35 and 800 <= c <= 4000: found.append(('呼吸声', t(k), t(j), float(e[k:j].max()), c, pp, lo))
            k = j
        # ② 噗声
        k = 0
        while k < m:
            ok = lambda q: e[q] >= -55 and not dz[q] and e[q] < -30 and spec(seg[max(0, q * F - 120):q * F + 240])[1] >= -3
            if not ok(k): k += 1; continue
            j = k
            while j < m and ok(j): j += 1
            if (j - k) * F / SR >= 0.015 and not (e[max(0, k - 6):k] >= -35).any():
                x = seg[k * F:j * F]; c, lo = spec(x); found.append(('噗声', t(k), t(j), float(e[k:j].max()), c, per(x) if len(x) >= 480 else 0.0, lo))
            k = j
        # ③ 底噪（数字静音以外、低于 -55 dB 的一长段）
        k = 0
        while k < m:
            if not (e[k] < -55 and not dz[k]): k += 1; continue
            j = k
            while j < m and e[j] < -55 and not dz[j]: j += 1
            if (j - k) * F / SR > 0.05: found.append(('底噪', t(k), t(j), float(e[k:j].max()), 0.0, 0.0, 0.0))
            k = j
    return found

def key(f): return f'{f[1]:.2f}–{f[2]:.2f}s'

if __name__ == '__main__':
    no = sys.argv[1]; a, sr = sf.read(f'work_{no}/a.wav'); assert sr == SR; a = np.asarray(a, float)
    if '--自检' in sys.argv:
        base = {key(f) for f in scan(a)}; b = a.copy()
        z = np.append((a == 0).astype(np.int8), 0); runs = []; st = None
        for i, v in enumerate(z):
            if v and st is None: st = i
            if not v and st is not None:
                if 0.3 <= (i - st) / SR <= 0.5: runs.append((st, i))
                st = None
        r1, r2 = runs[len(runs) // 3], runs[2 * len(runs) // 3]
        def ref_at(i):
            for s0, s1 in segments(a):
                if s0 <= i < s1:
                    seg = a[s0:s1]; m = len(seg) // F; return np.sqrt(np.mean(seg[:m * F].reshape(m, F) ** 2, axis=1)).max()
            # 停顿的静音在句子中间：取前后 3 秒
            seg = a[max(0, i - 3 * SR):i + 3 * SR]; m = len(seg) // F; return np.sqrt(np.mean(seg[:m * F].reshape(m, F) ** 2, axis=1)).max()
        rng = np.random.default_rng(1); n = int(0.15 * SR); nz = rng.standard_normal(n); X = np.fft.rfft(nz); f = np.fft.rfftfreq(n, 1 / SR)
        X[(f < 1000) | (f > 2500)] = 0; nz = np.fft.irfft(X, n) * np.hanning(n); i1 = (r1[0] + r1[1]) // 2 - n // 2
        nz *= ref_at(i1) * 10 ** (-42 / 20) / np.sqrt(np.mean(nz[n // 2 - 120:n // 2 + 120] ** 2)); b[i1:i1 + n] = nz
        n2 = int(0.025 * SR); pf = np.sin(2 * np.pi * 90 * np.arange(n2) / SR) * np.hanning(n2); i2 = (r2[0] + r2[1]) // 2
        pf *= ref_at(i2) * 10 ** (-45 / 20) / np.sqrt(np.mean(pf ** 2)); b[i2:i2 + n2] = pf
        new = [f for f in scan(b) if key(f) not in base]
        kinds = sorted(f[0] for f in new); want = sorted(['呼吸声', '噗声'])
        near = all(any(abs(f[1] - i / SR) < 0.1 for f in new) for i in (i1, i2))
        ok = kinds == want and near
        print(f"{'✔' if ok else '✘'} 纯人声核对 自检：在 {i1 / SR:.2f}s 放假呼吸声、{i2 / SR:.2f}s 放假噗声，新报出 {[(f[0], key(f)) for f in new]}")
        sys.exit(0 if ok else 1)
    d = json.load(open(f'scripts/{no}.json')); fp = hashlib.md5(open(f'work_{no}/a.wav', 'rb').read()).hexdigest()[:12]
    conf = d.get('核对确认', {}).get('非人声', {}); bad = 0; rows = []
    for f in scan(a):
        cf = conf.get(key(f)); ok = isinstance(cf, dict) and cf.get('配音指纹') == fp
        bad += not ok
        rows.append(f"{no} {'OK（已用实际声音核实是词的一部分）' if ok else 'BAD'} {f[0]} {key(f)} 长 {1000 * (f[2] - f[1]):.0f} ms 最响 {f[3]:.1f} dB 重心 {f[4]:.0f} Hz 周期 {f[5]:.2f} 低频占比 {f[6]:.1f} dB")
    print('\n'.join(rows)); print(f'{no} 纯人声核对（配音指纹 {fp}）问题数', bad)
    sys.exit(1 if bad else 0)
