#!/usr/bin/env python3
"""词头渐强核对（K131，62 S15 13 clones, | four：人工插入点落在 /z/→/f/ 交界，下一段开头 15 ms 渐强把只有 10 ms 的 /f/ 压低 20 dB，用户听成 our）。
每个停顿接点（work_NN/淡入淡出.json：原始合成里的 淡出起点、切点、淡入终点）：在原始合成里找切点后紧跟的辅音
（从切点起、电平 ≥ -45 dB、直到幅度谱重心 < 1500 Hz 的元音开始），算渐强（余弦）把它压低 6 dB 以上的部分占多少：
辅音最响 ≥ -40 dB、长 ≥ 7.5 ms（更短的是前一个词擦音的残尾，如 64 S20 farmers, | and），且被压掉的占 ≥ 40% → BAD（辅音整段被渐强吃掉，听不出来）。修法：插入点往前挪、写成 [秒,"交界"]（8 ms 渐变），让短辅音整段留在停顿后面。
用法（出片工作目录）：python3 词头渐强核对.py NN ；python3 词头渐强核对.py --自检"""
import sys, os, json, re
import numpy as np
SR = 24000; F = int(0.0025 * SR)

def 重心(x):
    X = np.abs(np.fft.rfft(x * np.hanning(len(x)), n=1024)); f = np.fft.rfftfreq(1024, 1 / SR)
    return float((X * f).sum() / (X.sum() + 1e-12))

def 判(raw, c, b, ref=None):
    """raw：原始合成；c：切点（样本）；b：淡入终点。返回 (BAD?, 说明)"""
    if ref is None:
        m = len(raw) // F; ref = np.sqrt(np.mean(raw[:m * F].reshape(m, F) ** 2, axis=1)).max()
    lv = lambda x: 20 * np.log10(np.sqrt(np.mean(x ** 2)) / ref + 1e-12) if len(x) else -200
    n_in = max(1, b - c); fr = []; i = c
    while i + F <= len(raw) and i < c + int(0.08 * SR):
        x = raw[i:i + F]; L = lv(x); cen = 重心(raw[max(0, i - F):i + 2 * F])
        if cen < 1500 and L > -30: break                       # 元音开始
        if L < -45 and fr: break
        if L >= -45:
            k = np.arange(i, i + F) - c; g = np.where(k < n_in, 0.5 - 0.5 * np.cos(np.pi * np.clip(k, 0, n_in) / n_in), 1.0)
            fr.append((L, 20 * np.log10(np.sqrt(np.mean((x * g) ** 2)) / (np.sqrt(np.mean(x ** 2)) + 1e-12) + 1e-12)))
        i += F
    if not fr: return False, '切点后没有辅音（直接元音或静音）'
    n = len(fr) * 2.5; pk = max(L for L, _ in fr); 压 = sum(1 for _, d in fr if d <= -6) / len(fr)
    s = f'辅音 {n:.1f} ms、最响 {pk:.1f} dB，渐强 {n_in / SR * 1000:.0f} ms 压低 6 dB 以上的占 {压:.0%}'
    return (pk >= -40 and n >= 7.5 and 压 >= 0.4), s   # 7.5 ms：64 S20 farmers, | and 切点后只剩 /z/ 残尾 5 ms 就接元音（and 元音开头），压掉残尾是对的，不算

def 自检():
    rng = np.random.default_rng(3); t = np.arange(int(0.2 * SR)) / SR
    vowel = sum(np.sin(2 * np.pi * 180 * h * t) / h for h in range(1, 8)) * 0.3
    def 样(fric_ms):
        n = int(fric_ms / 1000 * SR); fz = rng.standard_normal(n); fz = np.diff(fz, prepend=0) * 0.05   # 高频擦音
        return np.concatenate([np.zeros(int(0.05 * SR)), fz, vowel]), int(0.05 * SR)
    e = []
    x, c = 样(10)
    if not 判(x, c, c + int(0.015 * SR))[0]: e.append('没抓到：10 ms 擦音被 15 ms 渐强吃掉（K131 62 S15 four）')
    x, c = 样(90)
    if 判(x, c, c + int(0.008 * SR))[0]: e.append('误报：90 ms 擦音只被 8 ms 交界渐强压了开头（62 S1 Scotland 的 /s/）')
    x, c = 样(22)
    if 判(x, c, c + int(0.008 * SR))[0]: e.append('误报：22 ms 擦音、8 ms 交界渐强（62 S15 修好后）')
    x, c = 样(4)   # 量出来约 5 ms（窗口跨到元音），同 64 S20
    if 判(x, c, c + int(0.015 * SR))[0]: e.append('误报：切点后只剩 5 ms 擦音残尾就接元音（64 S20 farmers, | and）')
    x, c = 样(0)
    if 判(x, c, c + int(0.015 * SR))[0]: e.append('误报：切点后直接元音')
    print('词头渐强核对 自检：' + ('通过（10 ms 擦音被 15 ms 渐强吃掉必抓；90 ms、22 ms 擦音配 8 ms 交界渐强、5 ms 擦音残尾、直接元音必放）' if not e else '；'.join(e)))
    return 1 if e else 0

if __name__ == '__main__':
    if sys.argv[1:2] == ['--自检']: sys.exit(自检())
    no = sys.argv[1].zfill(2)
    fades = json.load(open(f'work_{no}/淡入淡出.json'))
    if not fades: print(f'{no} 词头渐强核对：没有渐变接点 问题数 0'); sys.exit(0)
    sys.argv = [sys.argv[0]]
    sys.path.insert(0, '.')
    exec(open('make_video.py').read().split("if __name__")[0], globals())
    d = json.load(open(f'scripts/{no}.json')); ok = d.get('核对确认', {}).get('词头渐强', {}); bad = 0
    for S, L in fades.items():
        s = d['sentences'][int(S[1:]) - 1]; sent = ' '.join(re.sub(r'\*\*', '', R.strip_gloss(c['en'])).strip() for c in s['chunks'])
        raw = _ending_raw(sent, ENDING[sent]) if sent in ENDING else k.create(spoken(sent), voice=V, speed=SPEED, lang='en-us')[0]
        raw = np.asarray(raw, np.float64)
        for a, c, b in L:
            B, why = 判(raw, c, b); key = f'{S} raw {c / SR:.4f}'
            if B and key in ok: print(f'{no} OK（已核实：{ok[key][:40]}）{key} {why}')
            elif B: bad += 1; print(f'{no} BAD {key}：{why}；插入点往前挪、写成 [秒,"交界"]，让辅音整段留在停顿后面（K131）')
            else: print(f'{no} OK {key} {why}')
    print(f'{no} 词头渐强核对 问题数 {bad}'); sys.exit(1 if bad else 0)
