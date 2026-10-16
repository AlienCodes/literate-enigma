#!/usr/bin/env python3
"""自动切点（2026-10-15 方法升级，省 token：第10篇这一步派 4 位判定员逐段判，最费 token）。
在视频工作目录下运行：python3 <工具目录>/自动切点.py NN [--写入]
接在 疑点清单.py 后面（exec 它，拿到同一份候选、同一份 w），对每段疑点（呼吸声、噗声、孤立杂音、A19 停顿后吸气……）只做“一眼能定”的：
  ① 疑点里没有词的声音（5 ms 帧都 < -30 dB，基准 = 本句最响 5 ms 帧，与出片程序 _nonvoice 守门同一口径）；
  ② 往左、往右各走到第一个 < -55 dB 的帧（静音低谷），中途不碰到 ≥ -30 dB 的帧（不贴词）——切点就在两个低谷里，词的声音一点不碰；
  ③ 不是被闭塞隔开的词尾除阻/擦音：前一个词以塞音、塞擦音、擦音结尾，且疑点离前面最后一个 ≥ -30 dB 帧不到 0.15 秒 → 交人看
     （hit, 的 /t/ 除阻和元音之间隔着闭塞静音，看起来像孤立的一段，A6/A21 的坑）；后一个词以 h、擦音、清塞音开头、疑点离后面第一个响帧不到 0.06 秒 → 交人看。
满足的写进 非人声区间（--写入）；不满足的列出来交人看（逐段看声音.py）。写入后照常重建、跑全部核查和独立复核把关。"""
import sys, os, json
T = os.path.dirname(os.path.abspath(__file__))
WRITE = '--写入' in sys.argv; sys.argv = [a for a in sys.argv if a != '--写入']
src = open(f'{T}/疑点清单.py').read()
exec(src.split("os.makedirs(outdir, exist_ok=True)")[0], globals())
auto = {}; human = []
ONLY = [x for x in os.environ.get('ONLY', '').split(',') if x]   # 只算这几句（人已用实际声音看过、放宽门槛时用），如 ONLY=S3,S14
for n_, c in enumerate(cands, 1):
    i0 = int(round(c['t0'] * SR)); it = next((x for x in info if x['off'] <= i0 < x['off'] + x['n']), None)
    if it is None: human.append((n_, '标题', c['kind'], '标题里的疑点交人看')); continue
    tc0 = (i0 - it['off']) / SR; tc1 = (int(round(c['t1'] * SR)) - it['off']) / SR
    p0 = to_w(it, tc0); p1 = to_w(it, max(tc0, tc1 - 1 / SR))
    if ONLY and f"S{it['si']}" not in ONLY: continue
    if p0 is None or p1 is None: human.append((n_, it['si'], c['kind'], '落在插入的静音里')); continue
    w = it['w0']; m = len(w) // F5; env = 20 * np.log10(np.sqrt(np.mean(w[:m * F5].reshape(m, F5) ** 2, axis=1)) + 1e-12); env -= env.max()
    k0, k1 = p0 // F5, min(m - 1, p1 // F5)
    if env[k0:k1 + 1].max() >= -30: human.append((n_, it['si'], c['kind'], '疑点里有 ≥-30 dB 的声音（可能是词）')); continue
    L = k0
    while L > 0 and -55 <= env[L - 1] < -30: L -= 1
    Rr = k1
    while Rr < m - 1 and -55 <= env[Rr + 1] < -30: Rr += 1
    tl, tr = (L == 0 or env[L - 1] >= -30), (Rr == m - 1 or env[Rr + 1] >= -30)   # 左/右贴着词（中间没有 -55 dB 低谷）
    x0, x1 = L * F5, (Rr + 1) * F5                                   # 不贴的一侧：外面紧挨的 5 ms 是 < -55 dB 的帧
    loud = np.where(env >= -30)[0]; pl = loud[loud < L]; nl = loud[loud > Rr]
    # 贴着的一侧看实际声音，不看时长模型的词时间（11 S2 模型偏了 0.3 秒，把 DeepMind 前的吸气声当成贴着 fifteen）：
    # 紧挨着的 20 ms 像擦音（s ʃ f θ：重心 >3500 Hz、低频 < -10 dB、周期 < 0.3）→ 擦音和吸气分不开，交人看；
    # 否则切在紧挨词的 40 ms 里最安静的 2.5 ms 的过零点（词的气声开口、收尾一点不碰）；要删的段里听得见的部分七成以上要“像呼吸”
    # （重心 >1800 Hz、低频 < -10 dB、周期 < 0.35）。
    def feat(i): c_, lo_ = spec(w[max(0, i - 90):i + 150]); return c_, lo_, per(w[max(0, i - 210):i + 270])
    def breathy(i): c_, lo_, p_ = feat(i); return 1800 < c_ < 3800 and lo_ < -10 and p_ < 0.35   # 上限：f/s/ʃ 的摩擦重心 >4 kHz（11 S9 itself 的 /f/ 4.3–6 kHz 差点被当成呼吸删掉）
    def fric(i0, i1): fs = [feat(i) for i in range(i0, i1, 60)]; return np.mean([c_ > 3500 and lo_ < -10 and p_ < 0.3 for c_, lo_, p_ in fs]) >= 0.5
    def zc(i, step):
        while 0 < i < len(w) and not (w[i - 1] * w[i] <= 0): i += step
        return i
    if (tl and not pl.size) or (tr and not nl.size): human.append((n_, it['si'], c['kind'], '在句首/句尾贴着')); continue
    if tr:
        j = nl[0] * F5
        if fric(j, j + int(0.02 * SR)): human.append((n_, it['si'], c['kind'], '右边贴着擦音（和吸气分不开）')); continue
        a_ = max(x0, j - int(0.04 * SR)); b_ = min(range(a_, j - 59, 60), key=lambda i: np.sqrt(np.mean(w[i:i + 60] ** 2)))
        x1 = zc(b_ + 30, -1)                                          # 现行做法：切在最深低谷的过零点（11 S4：按“像不像呼吸”切，切进了 a 的气声开口 10 ms，复核抓出）
    if tl:
        j = (pl[-1] + 1) * F5
        if fric(j - int(0.02 * SR), j): human.append((n_, it['si'], c['kind'], '左边贴着擦音（和吸气分不开）')); continue
        b_ = min(range(j, min(x1, j + int(0.04 * SR)) - 59, 60), key=lambda i: np.sqrt(np.mean(w[i:i + 60] ** 2)))
        x0 = zc(b_ + 30, 1)
    ref_ = np.sqrt(np.mean(w[:m * F5].reshape(m, F5) ** 2, axis=1)).max()
    aud = [i for i in range(x0, x1 - 60, 60) if 20 * np.log10(np.sqrt(np.mean(w[i:i + 60] ** 2)) / ref_ + 1e-9) > -50]
    # 词尾/词头很轻的擦音（itself 的 /f/、odds 的 /z/、sixteen 的 /s/）也在 -30 dB 以下、也“像呼吸”（A6 ink 的 /k/ 被切的同类坑）：
    # 要删的段里听得见的头 30 ms 重心 >3500 Hz、离前面的词不到 0.2 秒 → 可能是词尾擦音，交人看；尾 30 ms 同理对后面的词。
    if aud and pl.size and (aud[0] - (pl[-1] + 1) * F5) / SR < 0.2 and np.mean([feat(i)[0] for i in aud[:12]]) > 3500:
        human.append((n_, it['si'], c['kind'], '紧跟在词后、开头像擦音（可能是词尾 f/s/z）')); continue
    if aud and nl.size and (nl[0] * F5 - aud[-1] - 60) / SR < 0.2 and np.mean([feat(i)[0] for i in aud[-12:]]) > 3500:
        human.append((n_, it['si'], c['kind'], '紧挨着后面的词、结尾像擦音（可能是词头 s/f/h）')); continue
    if not tl and pl.size and (x0 - (pl[-1] + 1) * F5) / SR < 0.25 and len(aud) * 60 / SR < 0.06:   # 0.15→0.25（13 S4 intrigued. 的 /d/ 闭塞 160 ms 后才除阻，被当成杂音切掉）
        human.append((n_, it['si'], c['kind'], '紧跟在词后、听得见的不到 60 ms（可能是被闭塞隔开的词尾除阻）')); continue
    cs_ = [feat(i)[0] for i in range(x0, x1 - 60, 60)]
    if any(np.mean(cs_[q:q + 8]) > 4000 for q in range(0, max(1, len(cs_) - 7))):
        human.append((n_, it['si'], c['kind'], '要删的段里有连续 20 ms 重心 >4 kHz（像 f/s/ʃ 擦音，可能是词的一部分）')); continue
    if x1 - x0 < 0.015 * SR: human.append((n_, it['si'], c['kind'], '像呼吸的部分不到 15 ms')); continue
    aud = [i for i in range(x0, x1 - 60, 60) if 20 * np.log10(np.sqrt(np.mean(w[i:i + 60] ** 2)) / ref_ + 1e-9) > -50]   # 只看听得见的（-50 dB 以上），快到静音的帧特征是乱的
    if aud and np.mean([breathy(i) for i in aud]) < float(os.environ.get('BREATH_FRAC', 0.7)): human.append((n_, it['si'], c['kind'], f'要删的段里听得见的部分像呼吸的不到七成（{np.mean([breathy(i) for i in aud]):.0%}）')); continue
    auto.setdefault(it['si'], []).append([x0, x1, tl, tr])
for si_ in list(auto):                                                # 同一句重叠的合并：左右两头的“贴着词”各跟着提供这一头的那段
    iv = sorted(auto[si_]); mg = [iv[0]]
    for x in iv[1:]:
        if x[0] <= mg[-1][1]:
            if x[1] > mg[-1][1]: mg[-1][1], mg[-1][3] = x[1], x[3]
            elif x[1] == mg[-1][1]: mg[-1][3] = mg[-1][3] and x[3]
        else: mg.append(list(x))
    it = next(x for x in info if x['si'] == si_); ok_ = []
    for x0, x1, tl, tr in mg:                                         # 用出片程序同一个守门函数先验一遍，过不了的不写、交人看
        fl = '紧贴两头' if tl and tr else ('紧贴词尾' if tl else ('紧贴词头' if tr else ''))
        iv_ = [round(x0 / SR, 6), round(x1 / SR, 6)] + ([fl] if fl else [])
        try: _nonvoice(it['w0'], [iv_], 'check'); ok_.append(iv_)
        except SystemExit: human.append(('合并段', si_, '非人声', f'{iv_} 过不了出片程序的守门'))
    auto[si_] = ok_
auto = {f'S{k}': v for k, v in auto.items() if v}
print(f'{no} 疑点 {len(cands)} 处：程序可定 {len(cands) - len(human)} 处 → 非人声区间 {sum(len(v) for v in auto.values())} 段；交人看 {len(human)} 处')
for k, v in auto.items(): print('  删', k, v)
for h in human: print('  人看', f'#{h[0]} S{h[1]} {h[2]}：{h[3]}')
print('  （非人声区间的秒数都是 w 里的秒，与 疑点清单、逐段看声音 同一时间轴）')
if WRITE and auto:
    js_ = f'scripts/{no}.json'; dd = json.load(open(js_)); nv = dd.setdefault('非人声区间', {})
    for k, v in auto.items():
        old = nv.setdefault(k, [])
        for x_ in v:
            if not any(x_[0] < y and x < x_[1] for x, y, *_ in old): old.append(x_)
        old.sort()
    json.dump(dd, open(js_, 'w'), ensure_ascii=False, indent=1); print('已写进', js_)
