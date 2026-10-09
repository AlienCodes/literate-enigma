#!/usr/bin/env python3
"""纯人声核对（用户 2026-10-09：“不要有任何的呼吸声 语气声 这些都不要 底噪也不要 就要绝对的纯人声”；踩坑总表 A19）。
在视频工作目录下运行：python3 <工具目录>/纯人声核对.py NN [--自检]
逐句扫配音 work_NN/a.wav（每句以 ≥0.6 秒的数字静音分开；电平都相对本句最响的 5 ms 帧）：
  ① 呼吸声：连续 ≥80 ms 的声音、电平在 -55～-35 dB 之间、没有周期（不是嗓音：20 ms 窗自相关中位数 <0.35）、频谱重心 0.8–4 kHz；
  ② 噗声（嘴唇、声门的低频声）：连续 ≥15 ms、150 Hz 以下占一半以上能量、电平 ≥-55 dB，且前面 30 ms 里没有说话（排除词尾的鼻音）；
  ③ 底噪：数字静音以外、比本句最响低 55 dB 以下的声音，单段超过 50 ms 的（句中词与词之间留下的底噪）；
  ④ 孤立杂音：能听见（≥-55 dB）的一小团声音，前后都隔着 ≥15 ms 听不见的部分（与别的声音不相连），整团都比 -30 dB 轻，且 ≥-45 dB 或长 ≥20 ms
     （咔哒声、咂嘴声；词尾塞音 /t/ /k/ /d/ 的除阻也会报出，用实际声音核实是词的一部分后确认）；
  ⑤ 起音前过长：每段声音（句首、标点停顿之后）从第一次能听见到真正开口（10 ms 窗比本句最响的 10 ms 低不到 30 dB，与 A19、L14 同一口径）≥0.10 秒；
  ⑥ 收尾过长：每段声音（句尾、标点停顿之前）从最后一次 ≥-30 dB 到最后一次能听见 ≥0.25 秒。
  （④⑤⑥ 的门槛用已核实为纯人声的 06 配音校准：06 起音前最长 0.055 秒，收尾最长 0.22 秒（词的自然衰减），孤立杂音 7 处须逐处核实；
   01–04 旧配音起音前长到 0.43 秒 = 吸气声。）
报出的每一处：是非人声的，写进脚本"非人声区间"/"停顿删除区间"去掉；是词的一部分（如句末 /v/ 的擦音）的，用实际声音（逐 2.5 ms 电平、频谱、周期）核实后
写进 核对确认.非人声：{"12.34–12.56s": {"配音指纹": a.wav 的 md5 前 12 位, "依据": …}}，配音一变确认作废。
自检（阳性对照）：在副本的停顿静音里分别放进一段假呼吸声（0.15 秒、-42 dB、1–2.5 kHz 噪声）、一个假噗声（25 ms、90 Hz、-45 dB）、
一个假咔哒声（10 ms、-38 dB 宽带噪声），再在一句开口前紧贴着放一段 0.15 秒、-45 dB 的假吸气声；每一处都必须被对应的那一项报出，别处不得多报。"""
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
        # ④ 孤立杂音：能听见的连续帧组成一团（中间只隔 1–2 帧听不见的仍算同一团），前后都隔着 ≥3 帧（15 ms）听不见的部分
        isl = []; k = 0
        while k < m:
            if e[k] < -55: k += 1; continue
            j = k
            while j < m and e[j] >= -55: j += 1
            if isl and k - isl[-1][1] < 3: isl[-1][1] = j
            else: isl.append([k, j])
            k = j
        for k, j in isl:
            mx = float(e[k:j].max())
            if mx < -30 and (mx >= -45 or (j - k) * F / SR >= 0.02):
                x = seg[k * F:j * F]; c, lo = spec(x) if len(x) >= 64 else (0.0, 0.0); found.append(('孤立杂音', t(k), t(j), mx, c, per(x) if len(x) >= 480 else 0.0, lo))
        # ⑤ 起音前过长、⑥ 收尾过长：每段声音 = 被 ≥0.15 秒数字静音隔开的一段（句首句尾、标点停顿前后）
        n10 = 2 * F; m10 = len(seg) // n10; d10 = 10 * np.log10(np.mean(seg[:m10 * n10].reshape(m10, n10) ** 2, axis=1) + 1e-20); d10 -= d10.max()
        z = np.append((seg == 0).astype(np.int8), 0); bnd = []; st = None
        for i, v in enumerate(z):
            if v and st is None: st = i
            if not v and st is not None:
                if i - st >= 0.15 * SR: bnd.append((st, i))
                st = None
        for p0, p1 in zip([0] + [b[1] for b in bnd], [b[0] for b in bnd] + [len(seg)]):
            if p1 <= p0 or not np.any(seg[p0:p1] != 0): continue
            au = [f for f in range(p0 // F, min(m, (p1 + F - 1) // F)) if e[f] >= -55]
            ld = [g for g in range(p0 // n10, min(m10, (p1 + n10 - 1) // n10)) if d10[g] >= -30]
            if not au or not ld: continue
            hd = ld[0] * n10 / SR - au[0] * F / SR; tl = (au[-1] + 1) * F / SR - (ld[-1] + 1) * n10 / SR
            if hd >= 0.10: found.append(('起音前过长', t(au[0]), (s0 + ld[0] * n10) / SR, float(e[au[0]:ld[0] * 2].max()) if ld[0] * 2 > au[0] else -99.0, hd, 0.0, 0.0))
            if tl >= 0.25: found.append(('收尾过长', (s0 + (ld[-1] + 1) * n10) / SR, t(au[-1] + 1), float(e[(ld[-1] + 1) * 2:au[-1] + 1].max()), tl, 0.0, 0.0))
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
        r3 = runs[len(runs) // 2]; n3 = int(0.010 * SR); ck = rng.standard_normal(n3) * np.hanning(n3); i3 = (r3[0] + r3[1]) // 2
        ck *= ref_at(i3) * 10 ** (-38 / 20) / np.sqrt(np.mean(ck ** 2)); b[i3:i3 + n3] = ck
        sg = segments(a); s4 = sg[len(sg) // 2][0]; n4 = int(0.15 * SR); hb = rng.standard_normal(n4); X4 = np.fft.rfft(hb); f4 = np.fft.rfftfreq(n4, 1 / SR)
        X4[(f4 < 1000) | (f4 > 2500)] = 0; hb = np.fft.irfft(X4, n4) * np.linspace(0.3, 1, n4); i4 = s4 - n4
        hb *= ref_at(s4 + 10) * 10 ** (-45 / 20) / np.sqrt(np.mean(hb ** 2)); b[i4:s4] = hb
        new = [f for f in scan(b) if key(f) not in base]
        plan = [(i1, '呼吸声', '假呼吸声'), (i2, '噗声', '假噗声'), (i3, '孤立杂音', '假咔哒声'), (i4, '起音前过长', '开口前假吸气声')]
        hit = [any(f[0] == kind and f[1] - 0.05 <= i / SR <= f[2] + 0.05 for f in new) for i, kind, _ in plan]
        stray = [f for f in new if not any(f[1] - 0.2 <= i / SR <= f[2] + 0.2 for i, _, _ in plan)]
        ok = all(hit) and not stray
        print(f"{'✔' if ok else '✘'} 纯人声核对 自检：" + '、'.join(f'{i / SR:.2f}s {nm}{"报出" if h else "没报出"}' for (i, _, nm), h in zip(plan, hit))
              + (f"；别处多报 {[(f[0], key(f)) for f in stray]}" if stray else '；别处没有多报'))
        sys.exit(0 if ok else 1)
    d = json.load(open(f'scripts/{no}.json')); fp = hashlib.md5(open(f'work_{no}/a.wav', 'rb').read()).hexdigest()[:12]
    conf = d.get('核对确认', {}).get('非人声', {}); bad = 0; rows = []
    for f in scan(a):
        cf = conf.get(key(f)); ok = isinstance(cf, dict) and cf.get('配音指纹') == fp
        bad += not ok
        if f[0] in ('起音前过长', '收尾过长'):
            rows.append(f"{no} {'OK（已用实际声音核实是词的一部分）' if ok else 'BAD'} {f[0]} {key(f)} 长 {1000 * f[4]:.0f} ms（标准：起音前 <100 ms、收尾 <250 ms） 这一段最响 {f[3]:.1f} dB")
        else:
            rows.append(f"{no} {'OK（已用实际声音核实是词的一部分）' if ok else 'BAD'} {f[0]} {key(f)} 长 {1000 * (f[2] - f[1]):.0f} ms 最响 {f[3]:.1f} dB 重心 {f[4]:.0f} Hz 周期 {f[5]:.2f} 低频占比 {f[6]:.1f} dB")
    print('\n'.join(rows)); print(f'{no} 纯人声核对（配音指纹 {fp}）问题数', bad)
    sys.exit(1 if bad else 0)
