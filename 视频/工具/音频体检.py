#!/usr/bin/env python3
"""音频体检（2026-10-25 用户：“做音频这个环节，坚决不可以出任何问题，你要想方设法，想方设法想尽一切手段把我们这个音频做好”）
现有的声音门是一类事故补一道，只防踩过的坑；体检反过来找没踩过的：能测的全测，以用户听过、认可的 01–24 已定稿为基准，
超出 01–24 最差的一篇就报（25 起停）。每一项都有造坑自检（把那种毛病造进成片声音的副本，必须报出这一项；原样不误报）。

项目（每句按 ≥0.7 秒静音切，片头标题算第 0 句不参与句间比较）：
  削波       全片 |样本| ≥ 0.999 的个数
  直流偏移   每句样本均值 / 本句 RMS 的最大值
  咔哒       每 10 ms 内相邻样本最大差 / 本句最响 10 ms 的 RMS（切点处的爆音、数字断口）
  齿音       每句 20 ms 帧 5–10 kHz 能量最大值（相对本句最响帧），减去全片各句的中位数（某句齿音突然尖）
  句尾截断   每句最后 10 ms 相对本句最响 10 ms 的电平（声音没落下去就断了）
  句首突起   每句最开头 10 ms 相对本句最响 10 ms 的电平（起音被切、没有渐起）
  语速突变   每句 字母数字个数 / 时长，与全片中位数的相对差（需要脚本句数对得上）
  音色突变   每句频谱质心与全片中位数的相对差（换了音色、发闷或发尖）
  句内分段响度、整句响度：响度一致性核对.py 已有的门（交付核查另跑），这里不重复
用法：python3 音频体检.py 成片.mp4|a.wav [篇号]；--基准 视频目录（重算 01–24 基准，写 音频体检基准.json）；--自检 成片 [篇号]；--清单 视频目录
"""
import sys, os, re, json, subprocess, tempfile, numpy as np
T = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, T)
import 响度一致性核对 as R
SR = R.SR; BASE = f'{T}/音频体检基准.json'; V = os.path.dirname(T)
项 = ['削波', '直流偏移', '咔哒', '齿音', '句尾截断', '句首突起', '语速突变', '音色突变']

def 读(src):
    """成片声音（48 kHz 单声道）。a.wav（出片前）先过与出片程序同一套后期（../tts/AF.txt），与成片一致"""
    if src.endswith('.wav'):
        af = os.path.join(os.path.dirname(os.path.abspath(src)), '..', '..', 'tts', 'AF.txt')
        if os.path.exists(af):
            with tempfile.TemporaryDirectory() as td:
                o = os.path.join(td, 'x.m4a')
                subprocess.run([R.FF, '-y', '-loglevel', 'error', '-i', src, '-af', open(af).read().strip(), '-c:a', 'aac', '-b:a', '256k', o], check=True)
                return R.pcm(o)
    return R.pcm(src)

def 句段(a):
    z = np.concatenate([[0], (np.abs(a) < 1e-6).astype(np.int8), [0]]); d = np.diff(z)
    sil = [(s, e) for s, e in zip(np.where(d == 1)[0], np.where(d == -1)[0]) if e - s >= 0.7 * SR]
    out, prev = [], 0
    for s, e in sil:
        if s > prev: out.append((prev, s))
        prev = e
    return [(s, e) for s, e in out if e - s > 0.3 * SR]

def 文本(no):
    if not no: return None
    js = next((p for p in (f'scripts/{no}.json', f'{V}/脚本/{no}.json') if os.path.exists(p)), None)   # K109（30 草稿）：草稿脚本只在工作目录 scripts/，先找它，语速突变才量得出
    if not js: return None
    d = json.load(open(js))
    return [d['title_en']] + [' '.join(re.sub(r'\{\{.*?\}\}|\*\*', '', c['en']) for c in s_['chunks']) for s_ in d['sentences']]

def 指标(a, no=None):
    """{项: (值, 在哪一句)}"""
    seg = 句段(a); F = int(0.01 * SR); W = int(0.02 * SR); m = {}
    m['削波'] = (int(np.sum(np.abs(a) >= 0.999)), '')
    per = {k: [] for k in ('直流偏移', '咔哒', '齿音', '句尾截断', '句首突起', '质心')}
    for s, e in seg:
        x = a[s:e]; n = len(x) // F; rms = np.sqrt(np.mean(x[:n * F].reshape(n, F) ** 2, axis=1)); ref = rms.max() + 1e-12
        per['直流偏移'].append(abs(float(x.mean())) / (np.sqrt(np.mean(x ** 2)) + 1e-12))
        dx = np.abs(np.diff(x[:n * F])); per['咔哒'].append(float(np.max(dx)) / ref)
        k = len(x) // W; fr = x[:k * W].reshape(k, W) * np.hanning(W); Y = np.abs(np.fft.rfft(fr, axis=1)) ** 2; ff = np.fft.rfftfreq(W, 1 / SR)
        per['齿音'].append(float(10 * np.log10(Y[:, (ff > 5000) & (ff < 10000)].sum(axis=1).max() + 1e-20) - 20 * np.log10(ref * W)))
        per['句尾截断'].append(float(20 * np.log10(rms[-1] / ref + 1e-12))); per['句首突起'].append(float(20 * np.log10(rms[0] / ref + 1e-12)))
        X = np.abs(np.fft.rfft(x * np.hanning(len(x)))) ** 2; f = np.fft.rfftfreq(len(x), 1 / SR); per['质心'].append(float((X * f).sum() / X.sum()))
    at = lambda i: f'第{i}句' if i else '片头'
    for k in ('直流偏移', '咔哒', '句尾截断', '句首突起'):
        i = int(np.argmax(per[k])); m[k] = (per[k][i], at(i))
    sb = np.array(per['齿音']); i = int(np.argmax(sb)); m['齿音'] = (float(sb[i] - np.median(sb)), at(i))
    c = np.array(per['质心'][1:]); dv = np.abs(c - np.median(c)) / np.median(c); i = int(np.argmax(dv)); m['音色突变'] = (float(dv[i]), at(i + 1))
    txt = 文本(no)
    if txt and len(txt) == len(seg):
        r = np.array([len(re.sub(r'[^A-Za-z0-9]', '', t)) / ((e - s) / SR) for t, (s, e) in zip(txt[1:], seg[1:])])
        dv = np.abs(r - np.median(r)) / np.median(r); i = int(np.argmax(dv)); m['语速突变'] = (float(dv[i]), at(i + 1))
    elif txt: m['语速突变'] = (None, f'句数对不上（声音 {len(seg)} 段、脚本 {len(txt)} 句）')
    return m

def 超限(m, base):
    bad = []
    for k in 项:
        v, w = m.get(k, (None, ''))
        if v is None: bad.append(f'{k}：量不出来（{w}）') if w else None; continue
        if v > base[k]['上限'] + 1e-6: bad.append(f'{k} {v:.3g}（{w}）超过 01–24 最差 {base[k]["上限"]:.3g}（{base[k]["篇"]}）')
    return bad

def 造坑(a, no):
    """每一项造一种毛病（成片副本上），返回 {项: 副本}"""
    seg = 句段(a); s, e = seg[len(seg) // 2]; L = e - s; out = {}
    rng = np.random.default_rng(3)
    b = a.copy(); r = slice(s + L // 3, s + L // 3 + int(0.2 * SR)); b[r] = np.clip(b[r] * 50, -1, 1); out["削波"] = b
    b = a.copy(); b[s:e] += 0.05; out['直流偏移'] = b
    b = a.copy(); p = s + L // 2; b[p] = np.clip(b[p] + 0.9 * np.sign(-b[p] or 1), -0.99, 0.99); out['咔哒'] = b
    b = a.copy(); n = int(0.03 * SR); t = np.arange(n) / SR; b[s + L // 2:s + L // 2 + n] += 0.5 * np.sin(2 * np.pi * 7000 * t); out['齿音'] = b
    b = a.copy(); q = int(0.01 * SR); src = a[s + L // 2:s + L // 2 + 3 * q]; b[e - 3 * q:e] = src / (np.abs(src).max() + 1e-9) * np.abs(a[s:e]).max(); out['句尾截断'] = b
    b = a.copy(); b[s:s + 3 * q] = src / (np.abs(src).max() + 1e-9) * np.abs(a[s:e]).max(); out['句首突起'] = b
    cut = int(0.45 * L); out['语速突变'] = np.concatenate([a[:s + L // 4], a[s + L // 4 + cut:]])
    b = a.copy(); X = np.fft.rfft(a[s:e]); f = np.fft.rfftfreq(L, 1 / SR); X[f < 3000] *= 0.03; b[s:e] = np.fft.irfft(X, L); out['音色突变'] = b
    return out

def 自检(src, no):
    base = json.load(open(BASE)); a = 读(src); m0 = 指标(a, no); bad0 = {x.split(' ')[0].split('：')[0] for x in 超限(m0, base)}; f = []
    for k, b in 造坑(a, no).items():
        got = {x.split(' ')[0].split('：')[0] for x in 超限(指标(b, no), base)}
        if k in bad0: f.append(f'自检前提不成立：原样 {k} 已超限，造坑看不出来')
        elif k not in got: f.append(f'没抓到：造了“{k}”，体检没报（报了 {sorted(got - bad0)}）')
    return f, sorted(bad0)

if __name__ == '__main__':
    a_ = sys.argv[1:]
    if a_[0] == '--基准':
        import glob
        base = {k: {'上限': -1e9, '篇': ''} for k in 项}
        for f in sorted(glob.glob(os.path.join(a_[1], '[0-2][0-9].mp4'))):
            nn = os.path.basename(f)[:2]
            if int(nn) >= 25: continue
            m = 指标(读(f), nn)
            for k in 项:
                v = m.get(k, (None,))[0]
                if v is not None and v > base[k]['上限']: base[k] = {'上限': round(float(v), 6), '篇': f'{nn} {m[k][1]}'}
        json.dump({**base, '_说明': '01–24 已定稿（用户听过认可）每一项最差的一处；体检超过它就报。由 音频体检.py --基准 视频/视频 算出'}, open(BASE, 'w'), ensure_ascii=False, indent=1)
        print('基准：' + '；'.join(f'{k} {v["上限"]:.3g}（{v["篇"]}）' for k, v in base.items())); sys.exit(0)
    if a_[0] == '--清单':
        import glob
        base = json.load(open(BASE)); print('# 音频体检清单（01–24 已定稿：只列不改；基准就是 01–24 各项最差的一处，所以每一项最差的那篇就是基准本身）\n')
        for f in sorted(glob.glob(os.path.join(a_[1], '[0-2][0-9].mp4'))):
            nn = os.path.basename(f)[:2]
            if int(nn) >= 25: continue
            m = 指标(读(f), nn); top = [k for k in 项 if m.get(k, (None,))[0] is not None and base[k]['上限'] > 0 and m[k][0] >= base[k]['上限'] - 1e-9]
            print(f'- **{nn}**：' + ('；'.join(f'{k} {m[k][0]:.3g}（{m[k][1]}）是 01–24 最差' for k in top) or '各项都不是最差'))
        sys.exit(0)
    if a_[0] == '--自检':
        e, b0 = 自检(a_[1], a_[2] if len(a_) > 2 else None)
        print(('✘ ' if e else '✔ ') + '音频体检 自检：' + ('；'.join(e) if e else f'{len(项)} 项各造一种毛病全部报出、原样不误报')); sys.exit(1 if e else 0)
    base = json.load(open(BASE)); m = 指标(读(a_[0]), a_[1] if len(a_) > 1 else None); bad = 超限(m, base)
    print(f'音频体检 {len(项)} 项：超过 01–24 最差的 {len(bad)} 处')
    for x in bad: print('  ' + x)
    sys.exit(1 if bad else 0)
