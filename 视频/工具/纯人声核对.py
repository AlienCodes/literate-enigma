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
import sys, os, json, hashlib, numpy as np
try: import soundfile as sf   # --确认自检 是纯数值，不要声音库（主会话容器没有）
except ImportError: sf = None
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
            if (i - st) / SR >= 0.85: runs.append((st, i))   # 句间静音 ≥1.0 秒、句中停顿最长 0.70 秒（07 结尾句，2026-10-10）：分界取 0.85
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

# G43（主对话 2026-10-25：25 S10 “17th | the” 两条 AI 写的确认说是“底噪、the 的起音”，实测是可闻吸气，被确认放过）：25 起非人声确认只认实测数据。
# ① 确认里必须有“实测”（程序当场量的 最响dB、重心Hz、周期、低频dB，--写实测 自动填），和当场量的对不上就作废；
# ② 实测像可闻吸气（呼吸声/噗声/孤立杂音，长 ≥60 ms，重心 1.8–3.8 kHz，低频 < -10 dB，周期 < 0.35，最响 ≥ -45 dB）的，确认一律不收，只能用 非人声区间 去掉
#    （长 ≥60 ms：/p/ /t/ 的除阻也是这种频谱，但只有 10–20 ms，25 S13 upgraded 的 /p/ 除阻 20 ms）
def 实测(f): return {'最响dB': round(float(f[3]), 1), '重心Hz': round(float(f[4])), '周期': round(float(f[5]), 2), '低频dB': round(float(f[6]), 1)}
def 像吸气(f): return f[0] in ('呼吸声', '噗声', '孤立杂音') and f[2] - f[1] >= 0.06 and 1800 <= f[4] <= 3800 and f[6] < -10 and f[5] < 0.35 and f[3] >= -45
def 确认可收(no, f, cf):
    if not (str(no).isdigit() and int(no) >= 25): return True, ''
    if 像吸气(f): return False, f'实测像可闻吸气（{实测(f)}），确认不收，用 非人声区间 去掉（G43）'
    m = cf.get('实测') if isinstance(cf, dict) else None
    if not isinstance(m, dict): return False, '确认里没有实测数据（G43：python3 纯人声核对.py NN --写实测）'
    t = 实测(f)
    if any(abs(float(m.get(k, 1e9)) - v) > tol for (k, v), tol in zip(t.items(), (1.0, 150, 0.05, 1.0))): return False, f'确认里的实测 {m} 与当场量的 {t} 对不上（G43）'
    return True, ''
def 确认自检():
    e = []; b = ('呼吸声', 10.0, 10.12, -36.0, 2185.0, 0.21, -11.7)   # 25 S10 实测的那处可闻吸气
    if 确认可收('25', b, {'实测': 实测(b)})[0]: e.append('没抓到：25 实测像可闻吸气（2185 Hz、低频 -11.7、周期 0.21），确认照样收了（G43 重放 25 S10）')
    p_ = ('孤立杂音', 104.31, 104.33, -35.9, 2528.0, 0.22, -13.7)   # 25 S13 upgraded /p/ 除阻 20 ms
    if not 确认可收('25', p_, {'实测': 实测(p_)})[0]: e.append('误报：20 ms 的 /p/ 除阻被当成吸气')
    w = ('噗声', 6.30, 6.32, -42.2, 2959.0, 0.0, -2.2)
    if 确认可收('25', w, {'依据': '是词头'})[0]: e.append('没抓到：只写判断、没有实测数据的确认照样收了')
    if 确认可收('25', w, {'实测': {**实测(w), '最响dB': -30.0}})[0]: e.append('没抓到：确认里的实测和当场量的对不上')
    if not 确认可收('24', b, {})[0]: e.append('误报：24 以前的不回头查')
    return e

if __name__ == '__main__':
    if sys.argv[1:2] == ['--复查清单']:   # 01–24 已定稿：用成片声音按 G43 同一标准重量每条非人声确认，只列不改
        import glob, subprocess, shutil
        vdir = sys.argv[2]; print('# 声音确认复查清单（01–24 已定稿：非人声确认按 G43 同一标准用成片声音重量；只列不改，等用户统一处理）\n'); tot = 0; tb = 0
        for f_ in sorted(glob.glob(os.path.join(vdir, '[0-2][0-9].mp4'))):
            nn = os.path.basename(f_)[:2]; js = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '脚本', f'{nn}.json')
            if int(nn) >= 25 or not os.path.exists(js): continue
            cf_ = json.load(open(js)).get('核对确认', {}).get('非人声', {})
            # 在视频工作目录跑：用现行出片程序只出声音（配音缓存命中，十几秒），按 a.wav 的时刻与确认一一对上（成片 AAC 解码后时刻对不上）
            shutil.copy(js, f'scripts/{nn}.json'); subprocess.run(['python3', 'make_video.py', f'scripts/{nn}.json', f'{nn}.mp4'], env={**os.environ, 'AUDIO_ONLY': '1'}, capture_output=True, check=True)
            a_, _ = sf.read(f'work_{nn}/a.wav'); a_ = np.asarray(a_, float); got = {key(x): x for x in scan(a_)}
            br = [(k, got[k]) for k in cf_ if k in got and 像吸气(got[k])]; nodata = [k for k in cf_ if not (isinstance(cf_[k], dict) and cf_[k].get('实测'))]
            tot += len(cf_); tb += len(br)
            print(f'- **{nn}**：非人声确认 {len(cf_)} 条（对上 {sum(k in got for k in cf_)} 条；只有判断、没有实测数据 {len(nodata)} 条）；实测像可闻吸气 {len(br)} 条' + ''.join(f'\n  - {k} {x[0]}：{实测(x)}' for k, x in br))
        print(f'\n共 {tot} 条确认，实测像可闻吸气的 {tb} 条（用现行出片程序重出的 a.wav 量，时刻与确认一一对上）。要改哪篇，用户说了再改（改了要重出 4K、过交付核查、重新归档，G9）。'); sys.exit(0)
    if sys.argv[1:2] == ['--确认自检']:
        e = 确认自检(); print('\n'.join(e) or '纯人声核对 确认自检通过（25 起像可闻吸气的确认不收、没有实测或实测对不上不收；/p/ 除阻、24 以前照收）'); sys.exit(1 if e else 0)
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
    # A21：出片程序移植的词尾除阻（work_NN/词尾除阻.json，a.wav 里的时刻），整团落在移植段里的 = 供体的 /t/ /k/ 除阻本身，不是杂音
    gr = json.load(open(f'work_{no}/词尾除阻.json')) if os.path.exists(f'work_{no}/词尾除阻.json') else []
    for f in scan(a):
        g = next((x for x in gr if f[0] in ('孤立杂音', '噗声', '呼吸声') and x['开始'] - 0.005 <= f[1] and f[2] <= x['结束'] + 0.005), None)
        if g:
            rows.append(f"{no} OK（A21 移植的词尾除阻：{g['句']} {g['位置']}，{g['开始']:.3f}–{g['结束']:.3f}s）{f[0]} {key(f)} 最响 {f[3]:.1f} dB"); continue
        cf = conf.get(key(f)); ok = isinstance(cf, dict) and cf.get('配音指纹') == fp
        if ok and '--写实测' in sys.argv and isinstance(cf, dict) and not 像吸气(f): cf['实测'] = 实测(f); 写_ = True
        if ok:
            ok, why_ = 确认可收(no, f, cf)
            if not ok: rows.append(f'{no} BAD（{why_}）{f[0]} {key(f)}')
        bad += not ok
        if f[0] in ('起音前过长', '收尾过长'):
            rows.append(f"{no} {'OK（已用实际声音核实是词的一部分）' if ok else 'BAD'} {f[0]} {key(f)} 长 {1000 * f[4]:.0f} ms（标准：起音前 <100 ms、收尾 <250 ms） 这一段最响 {f[3]:.1f} dB")
        else:
            rows.append(f"{no} {'OK（已用实际声音核实是词的一部分）' if ok else 'BAD'} {f[0]} {key(f)} 长 {1000 * (f[2] - f[1]):.0f} ms 最响 {f[3]:.1f} dB 重心 {f[4]:.0f} Hz 周期 {f[5]:.2f} 低频占比 {f[6]:.1f} dB")
    if '--写实测' in sys.argv and globals().get('写_'): json.dump(d, open(f'scripts/{no}.json', 'w'), ensure_ascii=False, indent=1); print(f'{no} 已把当场量的实测写进 核对确认.非人声（像可闻吸气的不写）')
    print('\n'.join(rows)); print(f'{no} 纯人声核对（配音指纹 {fp}）问题数', bad)
    sys.exit(1 if bad else 0)
