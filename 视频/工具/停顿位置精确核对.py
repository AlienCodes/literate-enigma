#!/usr/bin/env python3
"""停顿位置精确核对（A9：停顿必须正好落在标点处的两个词之间，不能落在词中间或别的词缝里）。
在视频工作目录下运行：python3 <工具目录>/停顿位置精确核对.py NN [NN ...]
做法（与出片程序的定位方法不同，属于独立复核）：
  ① 用出片程序同一套代码，取得每个标点处实际删除/插入的位置 [ca, cb]（只在内存里给出片程序加一行记录，不改文件）；
  ② 带时长输出的模型给出每个音素的准确时间（在它自己合成的音频 tb 里）；
  ③ 把 tb 与成片用的整句音频 w 逐帧做动态时间规整（对数梅尔谱 + DTW），把"标点前一个词最后一个音素的开头"和"后一个词第一个音素的开头"
     准确映射到 w 上（模型把标点处的停顿算进前词最后一个音素里，所以不能用它的结尾）；
  ④ 要求插入的停顿完全落在这两个点之间（容差 30 ms）：这中间只有前词最后一个音素和标点，停顿落在别处即判错。
另报告：停顿前一个词的结尾、后一个词的开头离停顿各有多远（毫秒）。
两类停顿分开判定：
  删静音（说话人自然停顿过）：逐帧对齐判位置（第03篇 17 处校准全对）；段长比只做粗查（0.6–1.5）。
  插入（说话人连读，程序插停顿）：逐帧对齐在连读处会偏 60–70 ms，段长比（0.78 的正确与 0.74 的错误分不开）、两侧频谱比对也都不可靠，
  所以每一处都必须用实际声音（逐 5 ms 响度与频谱）核实，写进 核对确认.停顿位置（键里带位置，位置一变核实作废）；
  自动规则选错的，用脚本里的"停顿插入点"指定核实过的位置（A15）。"""
import sys, os, re, json, numpy as np
sys.path.insert(0, '.')
src = open('make_video.py').read().split("if __name__")[0]
hook = "        cuts.append((ca,cb,max(0.03,gaps[gi]-keep)))\n"
assert src.count(hook) == 1, '出片程序结构变了，核对程序需要同步更新'
src = src.replace(hook, hook + "        _LOG.append((ca,cb))\n")
src = src.replace("    clips=[];tmap=[];t=0.0;prev=0\n", "    _W.append(w)\n    clips=[];tmap=[];t=0.0;prev=0\n", 1)
_LOG = []; _W = []
exec(src)
TOL = 0.030
RLO, RHI = float(os.environ.get('RLO', '0.80')), float(os.environ.get('RHI', '1.25'))   # 插入处前后两段的段长比范围（用 01–04 校准）
NOSOUND = set(',;:.!?"\'“”‘’()[]—–-…')


def logmel(x, sr=24000, n_fft=600, hop=240, nm=40):
    win = np.hanning(n_fft); n = 1 + max(0, (len(x) - n_fft) // hop)
    fr = np.stack([x[i * hop:i * hop + n_fft] * win for i in range(n)])
    sp = np.abs(np.fft.rfft(fr, axis=1)) ** 2
    f = np.fft.rfftfreq(n_fft, 1 / sr); mel = lambda h: 2595 * np.log10(1 + h / 700)
    pts = 700 * (10 ** (np.linspace(mel(60), mel(8000), nm + 2) / 2595) - 1)
    fb = np.zeros((nm, len(f)))
    for m in range(nm):
        l, c, r = pts[m:m + 3]
        fb[m] = np.clip(np.minimum((f - l) / (c - l), (r - f) / (r - c)), 0, None)
    z = np.log(sp @ fb.T + 1e-8)
    return (z - z.mean(0)) / (z.std(0) + 1e-6)


def dtw_map(a, b, band=60):
    """a: tb 特征, b: w 特征；返回 tb 帧 → w 帧 的映射（带状 DTW）"""
    na, nb = len(a), len(b); sc = nb / na; INF = 1e18
    D = np.full((na + 1, nb + 1), INF); D[0, 0] = 0; P = np.zeros((na + 1, nb + 1), np.int8)
    for i in range(1, na + 1):
        c = int(i * sc); lo = max(1, c - band); hi = min(nb, c + band)
        cost = np.sqrt(((b[lo - 1:hi] - a[i - 1]) ** 2).sum(1))
        for j in range(lo, hi + 1):
            m = D[i - 1, j - 1]; k = 0
            if D[i - 1, j] < m: m = D[i - 1, j]; k = 1
            if D[i, j - 1] < m: m = D[i, j - 1]; k = 2
            D[i, j] = cost[j - lo] + m; P[i, j] = k
    i, j = na, nb; path = []
    while i > 0 and j > 0:
        path.append((i - 1, j - 1)); k = P[i, j]
        if k == 0: i, j = i - 1, j - 1
        elif k == 1: i -= 1
        else: j -= 1
    m = {}
    for i, j in path: m.setdefault(i, []).append(j)
    return np.array([np.median(m.get(i, [0])) for i in range(na)]), D[na, nb] / len(path)


bad = 0; rows = []
for no in sys.argv[1:]:
    d = json.load(open(f'scripts/{no}.json'))
    for si, s in enumerate(d['sentences'], 1):
        sent = ' '.join(re.sub(r'\*\*', '', R.strip_gloss(c['en'])).strip() for c in s['chunks'])
        ms = list(re.finditer(r'[,;:](?=\s)', sent))
        if not ms: continue
        pieces = []; p0 = 0
        for mm in ms: pieces.append((p0, mm.end())); p0 = mm.end() + 1
        pieces.append((p0, len(sent)))
        _LOG.clear(); _W.clear()
        _, tm = sentence_audio(sent, pieces, [0.4] * len(ms))
        w = _W[0]
        ratio = [(t1 - t0) / (len(say(sent[x0:x1])) / SR) for x0, x1, t0, t1 in tm]   # 每段：句中时长 ÷ 单独朗读时长
        tb, _, sp = KT.create_timed(spoken(sent), voice=V, speed=SPEED, lang='en-us', clause_pause=0, sentence_pause=0)
        mp, cost = dtw_map(logmel(np.asarray(tb, float)), logmel(np.asarray(w, float)))
        to_w = lambda t: float(np.interp(t * 100, np.arange(len(mp)), mp)) / 100   # tb 秒 → w 秒（帧距 10 ms）
        toks = list(sp); idx = [i for i, x in enumerate(toks) if x.phoneme in ',;:']
        for gi, (i, (ca, cb)) in enumerate(zip(idx, _LOG)):
            # 引号、括号、破折号等在带时长模型里也是带时长的"音素"（例：Knowledge" 的 " 占 175 ms），不是声音，跳过
            prv = next(x for x in reversed(toks[:i]) if x.phoneme.strip() and x.phoneme not in NOSOUND)
            nxt = next(x for x in toks[i + 1:] if x.phoneme.strip() and x.phoneme not in NOSOUND)
            # 注意：带时长模型把标点处的自然停顿算进前一个词最后一个音素的时长里（例：held 的 /d/ 2.784–3.109s，声音在 2.805s 就停了），
            # 所以下界用"前词最后一个音素的开头"：在它和"后词第一个音素的开头"之间，只有前词最后一个音素和标点本身。
            pe, ns = to_w(prv.start), to_w(nxt.start); a, b = ca / SR, cb / SR
            pos_ok = a >= pe - TOL and b <= ns + TOL
            rb, ra = ratio[gi], ratio[gi + 1]
            if cb > ca:   # 说话人自然停顿过、程序删掉部分静音：位置看逐帧对齐（第03篇校准全对）；段长只做粗查
                ok = pos_ok and 0.6 < rb < 1.5 and 0.6 < ra < 1.5; kind = '删静音'
            else:         # 连读、程序插入停顿：逐帧对齐在连读处会偏 60–70 ms（A16），必须同时看前后两段的段长比（A15 两处错都是靠它抓到的）
                ok = pos_ok and RLO < rb < RHI and RLO < ra < RHI; kind = '插入'
            word = sent[:ms[gi].end()].split()[-1]; nword = sent[ms[gi].end():].split()[0]
            # 报警处必须用实际声音（逐 5 ms 响度与频谱）核实后写进 核对确认.停顿位置，键里带停顿位置（位置一变，核实作废）
            key = f'S{si} {word} / {nword} @{a:.3f}'
            conf = d.get('核对确认', {}).get('停顿位置', {}).get(key)
            if kind == '插入':   # 程序插入的停顿（连读处）一律要用实际声音核实并记录，自动判定只作初筛（A15/A16）
                ok = bool(conf); bad += not conf
            else:
                bad += not ok and not conf
            rows.append(f"{no} S{si} {('OK（已用实际声音核实）' if conf else 'OK ') if (ok or conf) else 'BAD（用实际声音核实后写进 核对确认.停顿位置：' + key + '）'} {kind} 「{word} | {nword}」 段长比 前 {rb:.2f} 后 {ra:.2f} ｜ 前词末音素起 {pe:.3f}s 后词开头 {ns:.3f}s ｜ 停顿 {a:.3f}–{b:.3f}s"
                        f"（离前词末音素起点 {1000 * (a - pe):+.0f} ms，离后词 {1000 * (ns - b):+.0f} ms）对齐代价 {cost:.2f}")
print('\n'.join(rows)); print('问题数', bad)
