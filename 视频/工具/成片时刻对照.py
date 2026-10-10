#!/usr/bin/env python3
"""成片时刻对照（2026-10-09）：把 a.wav 里的时刻换算成“第几句、整句合成声音 w 里的秒”，并列出附近的音素。
核对确认里分析员写的都是 w 秒；纯人声核对报的是 a.wav 时刻——用这个程序对上，判断报出的是不是已核实过的同一段声音。
用法（视频工作目录）：python3 成片时刻对照.py NN 时刻 [时刻 ...]"""
import re, json, sys
import numpy as np, soundfile as sf
sys.path.insert(0, '.')
exec(open('make_video.py').read().split("if __name__")[0])   # 注意：不要用 k、V、R、T、F 等出片程序的全局名（k 是配音模型）
no = sys.argv[1]; ts = [float(x) for x in sys.argv[2:]]
a, _ = sf.read(f'work_{no}/a.wav', dtype='int16'); d = json.load(open(f'scripts/{no}.json'))
z = np.append((a == 0).astype(np.int8), 0); runs = []; st = None
for i, v in enumerate(z):
    if v and st is None: st = i
    if not v and st is not None:
        if (i - st) / SR >= 0.85: runs.append((st, i))   # 句间静音 ≥1.0 秒、句中停顿最长 0.70 秒（07 结尾句，2026-10-10）：分界取 0.85
        st = None
b = [0] + [r[1] for r in runs]; e = [r[0] for r in runs] + [len(a)]
segs_a = [(x + int(np.nonzero(a[x:y])[0][0]), y) for x, y in zip(b, e) if y > x and np.any(a[x:y] != 0)]
for t in ts:
    i = int(t * SR); sk = next((j for j, (x, y) in enumerate(segs_a) if x <= i < y), None)
    if sk is None: print(f'{t:.3f}s 不在任何一句里'); continue
    if sk == 0: print(f'{t:.3f}s 在标题里（标题 w 秒 ≈ {(i - segs_a[0][0]) / SR:.3f}，未计句中压缩）'); continue
    s = d['sentences'][sk - 1]; sent = ' '.join(re.sub(r'\*\*', '', R.strip_gloss(c['en'])).strip() for c in s['chunks'])
    lst = set()
    for ml in re.finditer(r"(?:\b[\w'-]+(?: [\w'-]+){0,4}, ){2,}(?:and|or) ", sent):
        for mc in re.finditer(r',', ml.group(0)): lst.add(ml.start() + mc.start())
    pieces = []; p0 = 0; gaps = []
    for mm in re.finditer(r'[,;:](?=\s)', sent): pieces.append((p0, mm.end())); p0 = mm.end() + 1; gaps.append(P_LIST if mm.start() in lst else P_COMMA)
    pieces.append((p0, len(sent)))
    clips, _ = sentence_audio(sent, pieces, gaps); tout = (i - segs_a[sk][0]) / SR
    wsec = None
    for a0, b0, t0, rm in LAST['segs']:
        q_end = b0 - a0 - sum(y - x for x, y in rm)
        if t0 <= tout < t0 + q_end / SR:
            q = int(round((tout - t0) * SR)); p = q
            for x, y in sorted(rm):
                if x <= p: p += y - x
            wsec = (a0 + p) / SR; break
    near = ' '.join(f'{x.phoneme}[{x.start * LAST["scale"] - LAST["head"] / SR:.3f}]' for x in LAST['toks'] if x.phoneme.strip() and wsec is not None and abs(x.start * LAST['scale'] - LAST['head'] / SR - wsec) < 0.25)
    print(f'{t:.3f}s = S{sk} 成片内 {tout:.3f}s = w {"停顿里插入的静音" if wsec is None else "%.4f s" % wsec}｜w 全长 {(LAST["segs"][-1][1]) / SR:.3f}s｜附近音素 {near}｜「{sent[-50:]}」')
