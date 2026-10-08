#!/usr/bin/env python3
"""高亮同步核对（L14：读到哪一块，哪一块高亮；不能还没读完就跳到下一块，也不能读到了还没亮）。
在视频工作目录下运行（出片后）：python3 <工具目录>/高亮同步核对.py NN [NN ...]
  可选：HL_LIST=别的list.txt（自检用：拿别的时间表核对同一份配音）  HL_WORK=dry（读 dry_NN/ 而不是 work_NN/）
        HL_ONLY=3,10（只核这几句，自检用）  HL_LIMIT=0.15
① 从 work_NN/list.txt 读出成片里每一屏实际出现的时刻（每一块开始高亮的时间）。
② 从成片配音 work_NN/a.wav 里，用与出片程序不同的办法找"这一块开始读"的时刻：
   乙：每一块单独合成后首尾相接（接缝就是块的开头，完全不用音素时间），与成片这一句逐帧对齐（对数梅尔谱 + DTW），把接缝映射到成片时间。
   甲：带时长模型合成同一句，与成片这一句逐帧对齐映射到成片时间。逗号、分号、冒号后的块取这一块第一个音素的开头
       （停顿后的空格可能落在停顿或吸气声里；音素开头比真正开口晚 0.01–0.11 秒）；其余块取第一个音前面那个空格的开头
       （出片程序也用空格开头，但用的是算术换算；甲用逐帧对齐，所以这时甲主要核对出片程序的换算有没有算错）。
   出片程序在标点后用"停顿后第一个比最响处低不到 30 dB 的 10 ms"（跳过吸气声），核查不用这个办法。
③ 每一块：高亮时刻与 甲、乙 都相差 ≤ LIMIT 秒。提前 = 还没读完就跳到下一块；推后 = 已经读到了还没亮。
④ 各办法的已知盲区（01–04 用实际声音核对过 12 处）：乙 在成片有换气声、停顿与单独合成差别大时，无标点处会整段对错（错 0.5–1 秒）；
   甲 偶尔晚 0.2 秒（how 的 /h/ 很弱）。"停顿结束处"不能当开口：停顿后常有 0.3–0.45 秒的吸气声（第一版核查因此量错）。
   所以任何一处不合格，都必须用实际声音（逐 10 ms 响度与频谱重心）找出这一块真正开始读的时刻，
   写进 scripts/NN.json 的 核对确认.高亮："S7 第3块": {"开始读": 秒（a.wav 里的时刻）, "配音指纹": a.wav 的 md5 前 12 位, "依据": "……"}；
   配音一变（指纹不同）确认就作废。有确认的，高亮时刻与确认的时刻相差 ≤ LIMIT 才算合格。"""
import sys, os, re, json, hashlib, numpy as np, soundfile as sf
sys.path.insert(0, '.')
src = open('make_video.py').read().split("if __name__")[0]
exec(src)
LIMIT = float(os.environ.get('HL_LIMIT', '0.15')); WK = os.environ.get('HL_WORK', 'work')
ONLY = {int(x) for x in os.environ.get('HL_ONLY', '').split(',') if x.strip()}


def logmel(x, sr=24000, n_fft=600, hop=240, nm=40):
    x = np.asarray(x, float); win = np.hanning(n_fft); n = 1 + max(0, (len(x) - n_fft) // hop)
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


def dtw_map(a, b):
    na, nb = len(a), len(b); band = 60 + abs(na - nb); INF = 1e18
    D = np.full((na + 1, nb + 1), INF); D[0, 0] = 0; P = np.zeros((na + 1, nb + 1), np.int8)
    for i in range(1, na + 1):
        c = int(i * nb / na); lo = max(1, c - band); hi = min(nb, c + band)
        cost = np.sqrt(((b[lo - 1:hi] - a[i - 1]) ** 2).sum(1))
        for j in range(lo, hi + 1):
            m = D[i - 1, j - 1]; k = 0
            if D[i - 1, j] < m: m = D[i - 1, j]; k = 1
            if D[i, j - 1] < m: m = D[i, j - 1]; k = 2
            D[i, j] = cost[j - lo] + m; P[i, j] = k
    i, j = na, nb; mp = {}
    while i > 0 and j > 0:
        mp.setdefault(i - 1, []).append(j - 1); k = P[i, j]
        if k == 0: i, j = i - 1, j - 1
        elif k == 1: i -= 1
        else: j -= 1
    return np.array([min(mp.get(i, [0])) for i in range(na)])     # 取最早对上的帧：词的开头


def onset_frame(x, f0):
    """从第 f0 帧（10 ms 一帧）起，第一个比本段最响帧低不到 40 dB 的帧（单独合成的块，开头有约 20 ms 静音）"""
    n = 240; m = len(x) // n; r = np.sqrt(np.mean(np.asarray(x[:m * n], float).reshape(m, n) ** 2, axis=1))
    db = 20 * np.log10(r / (r.max() + 1e-12) + 1e-9)
    return next((f for f in range(f0, m) if db[f] > -40), f0)


bad = 0; rows = []
for no in sys.argv[1:]:
    d = json.load(open(f'scripts/{no}.json'))
    ent = re.findall(r"file '([^']+)'\nduration ([\d.]+)", open(os.environ.get('HL_LIST', f'{WK}_{no}/list.txt')).read())
    nch = sum(len(s['chunks']) for s in d['sentences'])
    scr = ent[-nch:]; t0 = sum(float(x) for _, x in ent[:-nch])        # 片头（动画帧 + 静帧）之后才是正文各屏
    starts = []
    for _, du in scr: starts.append(t0); t0 += float(du)
    A, sr = sf.read(f'{WK}_{no}/a.wav'); A = np.asarray(A, float)
    fp = hashlib.md5(open(f'{WK}_{no}/a.wav', 'rb').read()).hexdigest()[:12]
    conf = d.get('核对确认', {}).get('高亮', {})
    kc = 0; prev_para = None; worst = 0; n_ok = 0
    for si, s in enumerate(d['sentences']):
        ch = s['chunks']; lead = P_FIRST if si == 0 else P_LEAD + (P_PARA_EXTRA if prev_para is not None and s['para'] != prev_para else 0)
        prev_para = s['para']
        if len(ch) == 1 or (ONLY and si + 1 not in ONLY): kc += len(ch); continue
        texts = [re.sub(r'\*\*', '', R.strip_gloss(c['en'])).strip() for c in ch]; sent = ' '.join(texts)
        a0 = starts[kc] + lead; a1 = (starts[kc + len(ch)] if kc + len(ch) < len(starts) else len(A) / sr) - P_HOLD
        seg = A[int(a0 * sr):int(a1 * sr)]; ls = logmel(seg)
        # 甲
        tb, _, sp = KT.create_timed(spoken(sent), voice=V, speed=SPEED, lang='en-us', clause_pause=0, sentence_pause=0)
        toks = list(sp); js = chunk_token_starts(texts, toks)
        mpa = dtw_map(logmel(tb), ls)
        # 乙
        parts = [say(t) for t in texts]; cat = np.concatenate(parts); bnd = np.cumsum([0] + [len(p) for p in parts]) // 240
        mpb = dtw_map(logmel(cat), ls)
        for ci in range(1, len(ch)):
            sw = starts[kc + ci]; ref = {}
            ref['乙'] = a0 + mpb[min(len(mpb) - 1, onset_frame(cat, bnd[ci]))] / 100
            j = js[ci]; i = j - 1
            while i >= 0 and toks[i].phoneme in 'ˈˌ': i -= 1
            punct = bool(re.search(r'[,;:]$', texts[ci - 1]))
            t_ = toks[i].start if not punct and i >= 0 and toks[i].phoneme == ' ' else toks[j].start
            ref['甲'] = a0 + mpa[min(len(mpa) - 1, int(round(t_ * 100)))] / 100
            key = f'S{si + 1} 第{ci + 1}块'; cf = conf.get(key)
            cf = cf if cf and cf.get('配音指纹') == fp else None
            auto_ok = all(abs(sw - v) <= LIMIT for v in ref.values())
            ok = auto_ok or (cf is not None and abs(sw - cf['开始读']) <= LIMIT)
            bad += not ok; n_ok += ok
            dev = [sw - v for v in ref.values()] if auto_ok or cf is None else [sw - cf['开始读']]
            dd = max(dev, key=abs) if dev else 0; worst = max(worst, abs(dd))
            refs = '  '.join(f'{k} {v:7.2f}s' for k, v in ref.items())
            tag = 'OK ' if auto_ok else ('OK（已用实际声音核实）' if ok else 'BAD')
            rows.append(f"{no} S{si + 1} {tag} 第{ci + 1}块「{texts[ci][:28]}」 高亮 {sw:7.2f}s  开始读 {refs}"
                        + (f"  实际声音核实 {cf['开始读']:.2f}s" if cf else '') + f"  {'提前' if dd < 0 else '推后'} {abs(dd):.2f}s"
                        + ('' if ok else f'  ← 用实际声音找出这一块开始读的时刻，写进 核对确认.高亮["{key}"]（配音指纹 {fp}）'))
        kc += len(ch)
    rows.append(f'{no} 共核对 {n_ok} 处合格，最大偏差 {worst:.2f}s（配音指纹 {fp}）')
print('\n'.join(rows)); print('问题数', bad)
sys.exit(1 if bad else 0)
