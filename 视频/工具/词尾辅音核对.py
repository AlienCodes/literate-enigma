#!/usr/bin/env python3
"""词尾辅音核对（A21，2026-10-09 用户：“Date后面那个t都没有翻译。Intelligent后面那个特也没有翻译……坚决防止以后这样的问题出现”）。
铁规矩：停顿前（, ; : 和句末，标题也算）的词尾清塞音，成片里必须听得清除阻（t 那一下爆破送气）：
  /t/ /k/：除阻里 2 kHz 以上的声音（爆破送气）最响 5 ms 帧 ≥ -36 dB；/p/：全频带最响 ≥ -33 dB（基准 = 这一句最响的 5 ms 帧）。
  （01–07 实测：清楚的词尾 t 在 -17～-34 dB；06 date, 只有 -53 dB、intelligent. 的被句尾修剪剪掉——用户听出来没有 t。
   配音模型在停顿前常常只闭塞、不除阻，“除阻”那一下重心只有 0.2–1 kHz，不是 t。）
  /d/ /b/ /ɡ/ 只列电平供参考（浊塞音靠声带振动和元音过渡，不判）。
做法：exec 出片程序，逐句（含标题）取这一句最终的声音 out 和每个停顿在 out 里开始的位置；从停顿开始处（句末 = out 结尾）往回：
  跳过听不见的帧 → 除阻 → 闭塞（比除阻最响低 ≥6 dB 的低谷，且最低处 < -50 dB 的真正静音）。往回 80 ms 内找不到闭塞 = 没有除阻 → 不合格。
  （/st/ /ft/ 结尾：除阻若被删，前面的擦音与元音之间只有小低谷、不是静音，不会被当成除阻。）
用法（视频工作目录）：python3 词尾辅音核对.py NN [NN ...]       核对（出片前）
                     python3 词尾辅音核对.py NN --写入            不合格的 t/k 按出片程序的“词尾除阻”（_graft）算出位置写进 scripts/NN.json，重跑核对必须全过
                     python3 词尾辅音核对.py NN --自检            阳性对照：每一处合格的除阻逐个换成静音、压低 20 dB，每一次都必须报出；原样不报
"""
import re, json, sys, os
import numpy as np, scipy.signal as ss
sys.path.insert(0, '.')
exec(open('make_video.py').read().split("if __name__")[0])
F5 = int(0.005 * SR); HP = ss.butter(6, 2000, 'highpass', fs=SR, output='sos')
TH_HF = -36.0; TH_P = -33.0


def frames_back(x, P, ref, n=60):
    """x[:P] 最后 n 个 5 ms 帧（帧边界对齐 P）的电平，倒序（第 0 个 = 紧挨 P 的那一帧）"""
    a = max(0, P - n * F5); a = P - ((P - a) // F5) * F5; m = (P - a) // F5
    if m <= 0: return np.zeros(0)
    r = np.sqrt(np.mean(np.asarray(x[a:P], np.float64).reshape(m, F5) ** 2, axis=1))
    return (20 * np.log10(r / ref + 1e-12))[::-1]


def release(x, hp, P, ref, deep=True):
    """返回 (全频最响, 2 kHz 以上最响, 时长 ms, 除阻在 x 里的样本范围) 或 None（没有除阻）"""
    L = frames_back(x, P, ref); H = frames_back(hp, P, ref)
    q = 0
    while q < len(L) and L[q] < AUD_DB: q += 1
    if q == len(L): return None
    q0 = q
    for _try in range(5):   # K152（41 S10 first,：除阻衰减末尾 5 ms -52 dB 的一小截后面隔着一帧 -60 dB 的小凹口，被当成闭塞，判“没除阻”、自动又补了一个，成片双爆破）
        pk = L[q]; c = None; r = q
        while r < len(L):
            if c is None:
                if L[r] > pk: pk = L[r]
                elif L[r] <= pk - 6: c = r
                elif r - q > 16: return None
            else:
                if L[r] < L[c]: c = r
                elif L[r] >= L[c] + 6: break
            r += 1
        # 找到的“除阻”不到 -45 dB、“闭塞”只有一帧低于 -55 dB（前一帧又能听见）：这是除阻衰减里的凹口，接着往前找真正的除阻
        if c is not None and L[q0:c].max() < AUD_DB + 10 and c + 1 < len(L) and L[c + 1] >= AUD_DB and (c == 0 or L[c - 1] >= AUD_DB): q = c + 1; continue
        # K167（46 S5 lamp, 的 /p/：除阻是两下连着的送气 -28.9 → 凹口 -35.5 → -20.5，再往前 -57 才是闭塞）：找到的“闭塞”不到 -50 dB、后面又起来，是除阻里的凹口，接着往前找真闭塞（除阻从 q0 算起，时长、重心照样查）
        if deep and c is not None and L[c] >= -50 and c + 1 < len(L) and L[c + 1] >= L[c] + 6: q = c + 1; continue
        break
    q = q0
    # 闭塞必须是真正的静音（< -50 dB）：04 自检查出，first, 的 /t/ 除阻被换成静音后，前面 /s/ 擦音与元音之间的小低谷（不是闭塞）
    # 被当成了闭塞、/s/ 被当成了除阻，没报。01–07 所有合格处的闭塞最低都在 -58 dB 以下（多数是数字静音）。
    if c is None or (deep and L[c] >= -50): return None     # 浊塞音（deep=False）的闭塞带声带振动，不是静音，只要求是低谷
    return float(L[q:c].max()), float(H[q:c].max()), (c - q) * 5, (P - c * F5, P - q * F5), float(L[c])


def centroid(x, a, b):
    """x[a:b] 的声音重心（Hz）"""
    seg = np.asarray(x[a:b], np.float64)
    if len(seg) < 16: return 0
    sp = np.abs(np.fft.rfft(seg * np.hanning(len(seg)))) ** 2; f = np.fft.rfftfreq(len(seg), 1 / SR)
    return int((sp * f).sum() / (sp.sum() + 1e-20))


# /t/ /k/ 的除阻是爆破送气：声音重心在高频、时长短。14 自检查出 puppet. 的 /t/ 除阻换成静音后，程序往回把 /ɪ/ 元音（重心 544 Hz、105 ms）
# 连同前面 /p/ 的闭塞当成了除阻；19 collapsed. 换成静音后把 /s/ 擦音（120 ms）当成了除阻。01–20 共 82 处合格除阻实测：重心最低 1282 Hz，最长 100 ms。
CEN_MIN = 1000; DUR_MAX = 110


# K149（41 S10 Tested first,：除阻换成静音后，程序往回把 Tested 的 /d/ 后那一下低谷当成闭塞、把 “firs” 整个当成除阻，没报）：
# /t/ /k/ 的除阻是送气噪声，800 Hz 以下很弱；元音 800 Hz 以下最响。04/14/19/25/27/30/33/36/38 共 39 处合格除阻实测：800 Hz 以下最响 5 ms 帧最高 -30.5 dB
# （基准 = 本句最响 5 ms 帧），混进元音的假除阻在 -5～-15 dB；超过 LF_MAX 就不是除阻。
LP8 = ss.butter(6, 800, 'lowpass', fs=SR, output='sos'); LF_MAX = -20.0
def lf_peak(x, a, b):
    m = len(x) // F5; ref = np.sqrt(np.mean(np.asarray(x[:m * F5], np.float64).reshape(m, F5) ** 2, axis=1)).max()
    p0 = max(0, a - 960); seg = ss.sosfiltfilt(LP8, np.asarray(x[p0:b + 960], np.float64))[a - p0:b - p0]; k = len(seg) // F5
    if k == 0: return -200.0
    return float(20 * np.log10(np.sqrt(np.mean(seg[:k * F5].reshape(k, F5) ** 2, axis=1)).max() / ref + 1e-12))


# K170（46 S8 back 自检：/k/ 除阻换成静音后，程序往前把 æ 元音的尾巴当成除阻、判合格；真丢了除阻也会这样漏报）：
# 除阻是送气噪声，没有周期；元音有基频周期。27/43/44 共 18 处合格除阻实测 自相关（基频 70–400 Hz 范围）最高 0.33，超过 PER_MAX 的不是除阻
PER_MAX = 0.6
def periodicity(x, a, b):
    s = np.asarray(x[a:b], np.float64)
    if len(s) < int(0.02 * SR): s = np.asarray(x[max(0, b - int(0.02 * SR)):b], np.float64)
    s = s - s.mean(); r = np.correlate(s, s, 'full')[len(s) - 1:]; r = r / (r[0] + 1e-20)
    return float(r[int(SR / 400):int(SR / 70)].max())


def 双爆破(x, hp, z, ref):
    """K171（46 S4 brightest：原声 /t/ 除阻 -32 dB 不过高频门槛，程序又移植一下，中间只隔 10 ms 静音，听成两个 t）：
    有移植的位置，找到的除阻前 7.5–25 ms 静音之后还有一下 ≥ -40 dB 的非元音爆破 → 返回它 (全频, 隔 ms)，否则 None。
    （-st 词尾 /s/ 擦音只隔 15 ms 闭塞，按时长 ≤110 ms、重心 ≥1 kHz 排除；除阻里不到静音的凹口 K167 不算）"""
    if z is None: return None
    z2 = release(x, hp, z[3][0], ref)
    if z2 is None or z2[0] < -40: return None
    gap = (z[3][0] - z2[3][1]) / SR * 1000
    if not 7.5 <= gap <= 25 or z2[2] > DUR_MAX or centroid(x, *z2[3]) < CEN_MIN or periodicity(x, *z2[3]) > PER_MAX or lf_peak(x, *z2[3]) > LF_MAX: return None   # /s/ 擦音 120–170 ms（02 context、24 collapsed coast、39 fixed 实测）、重心 <1 kHz 的余音（24 boat）都不是爆破
    return z2[0], gap, z2[2], centroid(x, *z2[3])


def 元音前(word):
    """词尾塞音前一个音是元音（46 back = bˈæk）"""
    w = re.sub(r'[ˈˌːˑ]', '', word)
    return len(w) >= 2 and w[-2] in 'aeiouyæɑɒɔəɛɜɪʊʌɚᵻɐɘɵø'


def judge(x, z, ph):
    if z is None: return False
    if periodicity(x, *z[3]) > PER_MAX: return False
    if ph in 'tk': return z[1] >= TH_HF and z[2] <= DUR_MAX and centroid(x, *z[3]) >= CEN_MIN and lf_peak(x, *z[3]) <= LF_MAX
    return z[0] >= TH_P


def finals(toks):
    """每个 , ; : 前和句末的最后一个音素、所在的词"""
    res = []; marks = [i for i, x in enumerate(toks) if x.phoneme in ',;:'] + [len(toks)]
    for i in marks:
        j = i - 1
        while j >= 0 and (not toks[j].phoneme.strip() or toks[j].phoneme in '.!?ˈˌ"\''): j -= 1
        k0 = j
        while k0 > 0 and toks[k0 - 1].phoneme.strip() and toks[k0 - 1].phoneme not in ',;:.!?': k0 -= 1
        res.append((''.join(t.phoneme for t in toks[k0:j + 1]), toks[j].phoneme))
    return res


def sentence_items(d):
    """[(标签, 朗读文字, out, 每个停顿在 out 里开始的位置 + [len(out)], 词尾音素表, w 里每个停顿删除的 (起, 止))]"""
    items = []
    t = d['title_en']; tout = title_audio(t)
    _, _, tk = KT.create_timed(spoken(re.sub(r'\*\*', '', R.strip_gloss(t))), voice=V, speed=SPEED, lang='en-us', clause_pause=0, sentence_pause=0)
    ft = finals(list(tk))   # 标题整句合成、句中标点处不插停顿，只知道句末位置（19 标题 Tulip Mania: …，原来按句中标点取位置越界崩溃）
    items.append(('标题', t, tout, [None] * (len(ft) - 1) + [len(tout)], ft, []))
    for si, s in enumerate(d['sentences'], 1):
        sent = ' '.join(re.sub(r'\*\*', '', R.strip_gloss(c['en'])).strip() for c in s['chunks'])
        lst = list_commas(sent)   # 列举逗号与出片程序同一个函数（make_video.list_commas）
        pieces = []; p0 = 0; gaps = []
        for mm in re.finditer(r'[,;:](?=\s)', sent): pieces.append((p0, mm.end())); p0 = mm.end() + 1; gaps.append(P_LIST if mm.start() in lst else P_COMMA)
        pieces.append((p0, len(sent)))
        clips, _ = sentence_audio(sent, pieces, gaps); out = np.concatenate(clips); ln = [len(c) for c in clips]
        starts = [sum(ln[:2 * g + 1]) for g in range(len(LAST['cuts']))] + [len(out)]
        items.append((f'S{si}', sent, out, starts, finals(LAST['toks']), [(c[0], c[1]) for c in LAST['cuts']]))
    return items


def nograft_items(d):
    """写了“词尾除阻”的句子（含标题）不移植时的 {标签: (out, starts)}——查多余的移植用"""
    res = {}
    for key in [k_ for k_ in list(GRAFT) if k_ == '标题::' + d['title_en'] or any(k_ == ' '.join(re.sub(r'\*\*', '', R.strip_gloss(c['en'])).strip() for c in s['chunks']) for s in d['sentences'])]:
        keep = GRAFT.pop(key)
        try:
            if key.startswith('标题::'): o = title_audio(d['title_en']); res['标题'] = (o, [None] * 9 + [len(o)])
            else:
                si = next(i for i, s in enumerate(d['sentences'], 1) if key == ' '.join(re.sub(r'\*\*', '', R.strip_gloss(c['en'])).strip() for c in s['chunks']))
                lst = list_commas(key); pieces = []; p0 = 0; gaps = []
                for mm in re.finditer(r'[,;:](?=\s)', key): pieces.append((p0, mm.end())); p0 = mm.end() + 1; gaps.append(P_LIST if mm.start() in lst else P_COMMA)
                pieces.append((p0, len(key)))
                clips, _ = sentence_audio(key, pieces, gaps); o = np.concatenate(clips); ln = [len(c) for c in clips]
                res[f'S{si}'] = (o, [sum(ln[:2 * g + 1]) for g in range(len(LAST['cuts']))] + [len(o)])
        finally: GRAFT[key] = keep
    return res


def check(no, d, mutate=None):
    rows = []; bad = []; info = []
    # 多余的移植（2026-10-16，14 S14 ant.：读音改了以后整句重新合成，原声已有清楚的 /t/，旧位置的移植又补了一个，听成两个 t）：
    # 写了移植的那一处，不移植时原声的除阻已经合格 → 不合格（删掉这条移植，或用 --写入 重算）
    if not mutate:
        for lab, (o, st) in nograft_items(d).items():
            ent = d.get('词尾除阻', {}).get(lab, {})
            m = len(o) // F5; ref = np.sqrt(np.mean(np.asarray(o[:m * F5], np.float64).reshape(m, F5) ** 2, axis=1)).max()
            hp = ss.sosfiltfilt(HP, np.asarray(o, np.float64))
            for gk, (sec, ph) in ent.items():
                P = st[-1] if gk == '句末' else (st[int(gk) - 1] if int(gk) - 1 < len(st) - 1 else None)
                if P is not None and judge(o, release(o, hp, P, ref), ph):
                    line = f"{no} {lab} {'句末' if gk == '句末' else '第' + gk + '个标点'} /{ph}/ BAD 多余的移植：不移植时原声的除阻已经合格（读音或合成改过、旧位置没删？会听成两个 {ph}）"
                    rows.append(line); bad.append((lab, -1, -1, ph, line))
    for lab, text, out, starts, fin, cuts in sentence_items(d):
        if mutate: out = mutate(lab, out, starts, fin)
        m = len(out) // F5; ref = np.sqrt(np.mean(np.asarray(out[:m * F5], np.float64).reshape(m, F5) ** 2, axis=1)).max()
        hp = ss.sosfiltfilt(HP, np.asarray(out, np.float64))
        for g, (word, ph) in enumerate(fin):
            if ph not in 'tkpdbɡg': continue
            where = '句末' if g == len(fin) - 1 else f'第{g + 1}个标点'
            if starts[g] is None:
                if ph in 'tkp':                                     # 标题句中标点前的清塞音：位置算不出，不放行，交人听
                    line = f"{no} {lab} {where} {word} /{ph}/ BAD 标题句中标点前，程序定不了停顿位置，需人听"; rows.append(line); bad.append((lab, g, len(fin) - 1, ph, line))
                continue
            z = release(out, hp, starts[g], ref, deep=ph in 'tkp')
            desc = '没有除阻' if z is None else f'除阻全频 {z[0]:.1f} dB、2 kHz 以上 {z[1]:.1f} dB、{z[2]} ms、闭塞最低 {z[4]:.1f} dB'
            if ph in 'dbɡg':
                weak = z is None or z[0] < -40                      # 偏弱的（01 sixty-second, -43 dB、argued, 没有除阻）剪成试听交用户
                info.append(f"{no} {lab} {where} {word}（浊塞音，不判）{desc}{'  ← 偏弱，需试听：剪成试听交用户确认' if weak else ''}"); continue
            ok = judge(out, z, ph)
            gk_ = '句末' if g == len(fin) - 1 else str(g + 1)
            gr_ = gk_ in d.get('词尾除阻', {}).get(lab, {}) or gk_ in d.get('停顿处除阻', {}).get(lab, {})   # 46 S4/S8：停顿处除阻也是移植，双爆破按移植报（删掉这条移植）
            db_ = 双爆破(out, hp, z, ref) if ph in 'tkp' and (gr_ or 元音前(word)) else None   # 没移植的只查元音后的塞音：-pt -kt -st 前一下是 /p k s/ 自己的声音（03 scraped、15 slept、30 east 等 8 处实测），不是重复
            if db_ and not d.get('核对确认', {}).get('双爆破', {}).get(f'{lab} {where}'):   # K172（46 S8 back,：原始合成就有两下 /k/ 爆破，隔 20 ms 静音）：没有移植的也查；用户听过说没问题的写 核对确认.双爆破 {"S8 第2个标点": "用户原话"}
                if gr_: line = f"{no} {lab} {where} {word} /{ph}/ BAD 双爆破：移植的除阻前 {db_[1]:.0f} ms 原声已有一下除阻（{db_[0]:.1f} dB），会听成两个 {ph}（{db_[2]} ms、重心 {db_[3]} Hz）；删掉这条移植，改用 除阻加强 加强原声那一下（46 S4）"
                else: line = f"{no} {lab} {where} {word} /{ph}/ BAD 双爆破：原始合成在停顿前有两下除阻，隔 {db_[1]:.0f} ms 静音（前一下 {db_[0]:.1f} dB、{db_[2]} ms、重心 {db_[3]} Hz），可能听成两个 {ph}；剪试听交用户，用户说没问题写 核对确认.双爆破 \"{lab} {where}\"，有问题用 非人声区间 删掉多的一下（46 S8）"
                rows.append(line); bad.append((lab, -1, -1, ph, line)); continue
            if z is not None and ph in 'tk': desc += f'、重心 {centroid(out, *z[3])} Hz'
            line = f"{no} {lab} {where} {word} /{ph}/ {'OK ' if ok else 'BAD'} {desc}（门槛：{'2 kHz 以上 ≥ %.0f dB、≤ %d ms、重心 ≥ %d Hz' % (TH_HF, DUR_MAX, CEN_MIN) if ph in 'tk' else '全频 ≥ %.0f dB' % TH_P}）"
            rows.append(line)
            if not ok: bad.append((lab, g, len(fin) - 1, ph, line))
    return rows, bad, info


def write_grafts(no, d, bad):
    """不合格的 t/k：在 w（clean_tail + _keep_tail + 非人声区间之后、移植之前）里找闭塞最低点之后的位置，写进 scripts/NN.json 的"词尾除阻\""""
    gj = d.setdefault('词尾除阻', {}); n = 0
    def 加强代替(lab, pos_, pos_r, line, 因, 静=False):
        """K124（47 S6 drought, 的 /t/）：原声已有一下除阻（或这一处已写 除阻加强）时再移植会听成两个 t（双爆破），改为加强原声那一下：
        增益 = 已有的 + 2 kHz 以上差多少再多 3 dB，合计最多 6 dB；重心、时长不合格或加到 6 dB 也不够的，交人看。返回写入条数（0 = 交人看）"""
        hf_ = re.search(r'2 kHz 以上 (-?[\d.]+) dB', line); ms_ = re.search(r'、(\d+) ms', line); ce_ = re.search(r'重心 (\d+) Hz', line)
        old_ = d.get('除阻加强', {}).get(lab, {}).get(pos_)
        if pos_r is None or not hf_ or (ms_ and int(ms_.group(1)) > DUR_MAX) or (ce_ and int(ce_.group(1)) < CEN_MIN):
            静 or print(f'不能自动补（{因}，再移植会听成两个音；原声那一下不是高频不够，加强没用），交人看：', line); return 0
        og_ = float(old_[2]) if old_ else 0.0; ra, rb = pos_r[0], min(pos_r[1] + 2, pos_r[0] + 16)
        gdb = min(6.0, round((og_ + TH_HF - float(hf_.group(1)) + 3) * 2) / 2)
        if float(hf_.group(1)) - og_ + gdb < TH_HF + 1 or gdb <= og_:
            静 or print(f'不能自动补（{因}，再移植会听成两个音；原声那一下加到 6 dB 也不够），交人看：', line); return 0
        d.setdefault('除阻加强', {}).setdefault(lab, {})[pos_] = [round(ra * F5 / SR, 6), round(rb * F5 / SR, 6), gdb]
        print(f'写入 {no} {lab} {pos_} /{line.split("/")[1] if "/" in line else "?"}/ 除阻加强 w {ra * F5 / SR:.3f}–{rb * F5 / SR:.3f}s +{gdb} dB（{因}，不移植）'); return 1
    for lab, g, last, ph, line in bad:
        if g < 0: print('多余的移植，不能自动处理（删掉这条移植后重跑）：', line); continue
        if ph not in 'tkp': print('不能自动补（只有 t、k 有供体，p 用除阻加强）：', line); continue
        if lab == '标题' and g != last: print('标题句中标点，不能自动补，交人听：', line); continue
        text = d['title_en'] if lab == '标题' else ' '.join(re.sub(r'\*\*', '', R.strip_gloss(c['en'])).strip() for c in d['sentences'][int(lab[1:]) - 1]['chunks'])
        raw, _ = k.create(spoken(re.sub(r'\*\*', '', R.strip_gloss(text))), voice=V, speed=SPEED, lang='en-us'); raw = np.asarray(raw, np.float32)
        w = clean_tail(raw); w = _keep_tail(raw, w, _head_offset(raw, w))
        key = '标题::' + text if lab == '标题' else text
        if key in NONVOICE: w = _nonvoice(w, NONVOICE[key], key)
        e = _env5(w)
        if g == last: lim = len(e)
        else:
            # 这一处停顿在 w 里删除开始的位置（出片程序算的）；除阻可能在它前面，也可能被它删掉（在它后面），所以从词的响亮部分结束处往后找
            ca, cb = sentence_items_cache[lab][0][g]; lim = ca // F5
        loud = [f for f in range(min(lim, len(e))) if e[f] >= -30]
        fL = loud[-1]; end_lim = len(e) if g == last else min(len(e), cb // F5 - 2)
        # 从词的响亮部分结束处往后，逐对找“真正的闭塞（< -50 dB 的静音，最长 150 ms）+ 短除阻（≤80 ms）”，取最后一对：
        # subject、effect 是 /kt/，第一对是 /k/ 的除阻，要补的是后面 /t/ 的；06 went, 的除阻后面隔着静音还有换气声（长于 80 ms），到那里就停。
        # 03 habitat.、01 S1 daylight, 是喉化结尾——元音带着嘎裂声慢慢衰减，中间的小低谷（-43 dB）不是闭塞；01 effect. 嘎裂声之后闭塞 110 ms 才除阻。
        # 找不到除阻的：放在词的声音衰减到 -55 dB 之后，再留 15 ms 闭塞。
        deep = False; f = fL + 1
        while f < end_lim and e[f] >= -50: f += 1
        if f < end_lim and f - fL <= 30:
            while True:
                c = f; x = f + 1; rel = None
                while x < end_lim and x - f <= 30:
                    if e[x] < e[c]: c = x
                    elif e[x] >= e[c] + 6 and e[x] >= AUD_DB: rel = x; break
                    x += 1
                if rel is None: break
                y = rel
                while y < end_lim and e[y] >= -50: y += 1
                if y - rel > 16: break
                pos_c = c; deep = True; pos_r = (rel, y)
                if y >= end_lim: break
                f = y
        if ph == 'p':
            # /p/ 没有供体（这个配音停顿前的 /p/ 几乎从不清楚除阻）：原声闭塞之后有除阻、只是偏弱的，写“除阻加强”（make_video._boost），
            # 增益 = 差多少补多少再多 3 dB（最多 6 dB）；20 S3 slope,（-33.7 dB）、19 S6 up.（-33.7 dB）
            m_ = re.search(r'除阻全频 (-?[\d.]+) dB', line)
            if not deep or not m_: print('不能自动补（/p/ 没有供体，原声闭塞之后也没有除阻）：', line); continue
            pos_ = '句末' if g == last else str(g + 1)
            ok8_ = d.get('核对确认', {}).get('除阻加强放宽', {}).get(f'{lab} {pos_}')   # 用户逐处同意的才放宽到 9 dB（21 S7 upkeep.，2026-10-22）
            cap_ = 9.0 if ok8_ and '用户' in str(ok8_) else 6.0
            gdb = min(cap_, round((TH_P - float(m_.group(1)) + 3) * 2) / 2)
            if float(m_.group(1)) + gdb < TH_P + 1: print(f'不能自动补（/p/ 除阻太弱，加 {cap_:g} dB 也不够；用户逐处同意可在 核对确认.除阻加强放宽 写 "{lab} {pos_}"）：', line); continue
            ra, rb = pos_r[0], min(pos_r[1] + 2, pos_r[0] + 16)
            d.setdefault('除阻加强', {}).setdefault(lab, {})['句末' if g == last else str(g + 1)] = [round(ra * F5 / SR, 6), round(rb * F5 / SR, 6), gdb] + ([str(ok8_)] if gdb > 6 else []); n += 1
            print(f'写入 {no} {lab} {"句末" if g == last else "第%d个标点" % (g + 1)} /p/ 除阻加强 w {ra * F5 / SR:.3f}–{rb * F5 / SR:.3f}s +{gdb} dB'); continue
        if ph in 'tk' and ('句末' if g == last else str(g + 1)) in d.get('除阻加强', {}).get(lab, {}):   # K124：这一处已写 除阻加强（原声有除阻），不再移植
            n += 加强代替(lab, '句末' if g == last else str(g + 1), pos_r if deep else None, line, '这一处已有 除阻加强'); continue
        if deep: on = pos_c + 1
        else:
            on = fL + 1
            while on < len(e) and e[on] >= AUD_DB: on += 1
            on += 3
        sec = round(on * F5 / SR, 6)
        if g != last:
            # 2026-10-16（13 S3 project, a voluntary endeavour,）：说话人把 project 的 /t/ 连到 a，找不到闭塞时上面的后备一路往后走过连读的
            # “a voluntary endeavour”，把 /t/ 补到了 endeavour 后面（w 2.17，凭空多一个 t，守门没拦住：那里正好是静音）。
            # 现在：供体放不进这个标点的停顿之前（插入点 / 删除段结束处之前、且不碰到 ≥ -30 dB 的帧），就改用“停顿处除阻”（A39）：
            # 在插入点前 60 ms 内找最晚的 p（前 5 ms < -40 dB 的闭塞，[p, 插入点) 全 < -30 dB）；找不到就交人看，绝不往后写。
            nd = len(_donor(ph)); lim_ = ca if cb == ca else cb
            if on * F5 + nd > lim_ or any(e[f] >= -30 for f in range(on, min(len(e), (on * F5 + nd) // F5 + 1))):
                pf = next((f for f in range(ca // F5 - 1, max(1, ca // F5 - 12), -1) if e[f - 1] < -40 and max(e[f:max(f + 1, ca // F5)]) < -30), None)
                if pf is None or str(g + 1) in d.get('停顿插入点', {}).get(lab, {}):
                    print('放不下、也找不到停顿处除阻的位置，交人看（逐段看声音找闭塞，写 停顿处除阻）：', line); continue
                if str(g + 1) in d.get('停顿删除区间', {}).get(lab, {}):   # K134（34 S5 state, not）：这个标点已有停顿删除区间，出片程序不许再加停顿处除阻（A21 守门），自动写了必停；交人看：删除段起点放在原有除阻之后，或改用除阻加强
                    print('这个标点已有停顿删除区间，不能再加停顿处除阻（出片程序不收），交人看（把删除段起点放在原有除阻之后，或用 除阻加强）：', line); continue
                ma_ = re.search(r'除阻全频 (-?[\d.]+) dB', line)
                if deep and ma_ and float(ma_.group(1)) >= -40:   # K124（47 S6 drought,）：停顿处除阻的供体接在原声除阻之后，原声那一下 ≥ -40 dB 就成了两下（双爆破），改加强原声那一下
                    因_ = f'原声已有一下除阻 {float(ma_.group(1)):.1f} dB'
                    if (k_ := 加强代替(lab, str(g + 1), pos_r, line, 因_, 静=True)): n += k_; continue
                    # 加强不够：供体从原声那一下前面的闭塞起换（把弱的那一下一起换掉，只剩一下）；出片守门同 A21：换掉的部分 < -30 dB、前 5 ms < -40 dB
                    if pos_c >= 1 and e[pos_c - 1] < -40 and max(e[pos_c:max(pos_c + 1, ca // F5)]) < -30:
                        d.setdefault('停顿处除阻', {}).setdefault(lab, {})[str(g + 1)] = [round(pos_c * F5 / SR, 6), round(ca / SR, 6), ph]; n += 1
                        print(f'写入 {no} {lab} 第{g + 1}个标点 /{ph}/ 停顿处除阻 w {pos_c * F5 / SR:.3f}–{ca / SR:.3f}s（{因_}，加强 6 dB 也不够：连原声那一下一起换掉）'); continue
                    print(f'不能自动补（{因_}，加强不够、也换不掉原声那一下），交人看：', line); continue
                d.setdefault('停顿处除阻', {}).setdefault(lab, {})[str(g + 1)] = [round(pf * F5 / SR, 6), round(ca / SR, 6), ph]; n += 1
                print(f'写入 {no} {lab} 第{g + 1}个标点 /{ph}/ 停顿处除阻 w {pf * F5 / SR:.3f}–{ca / SR:.3f}s（连读，供体放不进停顿之前）'); continue
        if g == last:
            # 2026-10-10（10 S12 it.）：句末的移植点放在了句尾淡出（clean_tail 最后 50 ms；_keep_tail 接长的是最后 5 ms）开始之后，
            # 淡出开始到移植点之间被淡出的那一帧夹在中间，与原始合成不同（独立复核报“多余声音”）。移植点最晚放在淡出开始处
            fs_ = len(w) - (F5 if len(w) != len(clean_tail(raw)) else int(0.05 * SR))
            if on * F5 > fs_: sec = round(fs_ / SR, 6); print(f'  {lab} 句末：移植点提前到句尾淡出开始处 {sec:.6f}s')
        gj.setdefault('标题' if lab == '标题' else lab, {})[('句末' if g == last else str(g + 1))] = [sec, ph]; n += 1
        print(f'写入 {no} {lab} {"句末" if g == last else "第%d个标点" % (g + 1)} /{ph}/ 位置 w {sec:.6f}s（{"闭塞最低点之后" if deep else "没有真正的闭塞：词的声音衰减到 -55 dB 后再留 15 ms 闭塞"}）')
    if n:
        json.dump(d, open(f'scripts/{no}.json', 'w'), ensure_ascii=False, indent=1)
    return n


if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    if '--自检' in sys.argv:
        # 阳性对照：每一处合格的词尾清塞音，逐个把除阻换成静音、压低 20 dB，每一处都必须报出（04 的 first, 曾漏报：/s/ 被当成除阻）
        no = args[0]; d = json.load(open(f'scripts/{no}.json')); items = sentence_items(d); n_ok = 0; miss = []
        for lab, text, out, starts, fin, cuts in items:
            m = len(out) // F5; ref = np.sqrt(np.mean(np.asarray(out[:m * F5], np.float64).reshape(m, F5) ** 2, axis=1)).max()
            hp = ss.sosfiltfilt(HP, np.asarray(out, np.float64))
            for g, (word, ph) in enumerate(fin):
                if ph not in 'tkp' or starts[g] is None: continue
                z = release(out, hp, starts[g], ref)
                if (word and (gk_s := ('句末' if g == len(fin) - 1 else str(g + 1))) in d.get('词尾除阻', {}).get(lab, {}) or 元音前(word)) and 双爆破(out, hp, z, ref): continue   # K172：有两下除阻的位置正检查已报 BAD（或用户听过确认），去掉一下还剩一下，不能做阳性对照
                if not judge(out, z, ph):
                    print(f'✘ 词尾辅音核对 自检：{no} {lab} {word} 原样就不合格，自检前提不成立'); sys.exit(1)
                n_ok += 1
                for name, gain in (('换成静音', 0.0), ('压低 20 dB', 0.1)):
                    o = out.copy(); o[z[3][0]:z[3][1]] *= gain
                    z2 = release(o, ss.sosfiltfilt(HP, np.asarray(o, np.float64)), starts[g], ref)
                    if judge(o, z2, ph): miss.append(f'{lab} {word} {name}')
        # K149 坏样本（41 S10 Tested first,）：前面一下静音、后面是 30 ms 元音 + 50 ms /s/，旧判法把它当成 /t/ 除阻；好样本：闭塞后 30 ms 高频爆破
        rng_ = np.random.default_rng(7); n_ = lambda sec: int(sec * SR); tt_ = lambda sec: np.arange(n_(sec)) / SR
        loud_ = 0.9 * np.sin(2 * np.pi * 200 * tt_(0.2)); z0_ = np.zeros(n_(0.05))
        vow_ = 0.3 * np.sin(2 * np.pi * 180 * tt_(0.03)) + 0.15 * np.sin(2 * np.pi * 360 * tt_(0.03)); s_ = ss.sosfiltfilt(HP, rng_.standard_normal(n_(0.05))) * 0.25
        b_ = ss.sosfiltfilt(HP, rng_.standard_normal(n_(0.03))) * 0.3 * np.exp(-tt_(0.03) / 0.01)
        for nm_, x_, want_ in (('元音+s 假除阻', np.concatenate([loud_, z0_, vow_, s_, z0_]), False), ('真除阻', np.concatenate([loud_, z0_, b_, z0_]), True)):
            m_ = len(x_) // F5; ref_ = np.sqrt(np.mean(x_[:m_ * F5].reshape(m_, F5) ** 2, axis=1)).max()
            if judge(x_, release(x_, ss.sosfiltfilt(HP, x_), len(x_), ref_), 't') != want_: miss.append(f'K149 {nm_} 判{"错放" if not want_ else "错拦"}')
        # K152 好样本（41 S10 first, 无补除阻时的实测帧电平，从停顿往回）：除阻衰减末尾一小截 + 一帧凹口，后面才是 -26.8 dB 的真除阻；必须判合格（旧判法判没除阻、又补一个，成片双爆破）
        sq_ = [-240.0, -57.9, -52.4, -60.2, -54.0, -48.6, -43.8, -36.9, -35.2, -29.8, -26.8, -33.5, -32.3, -49.1, -61.6, -240.0, -59.3, -54.2, -45.6, -35.4, -25.7, -16.3, -16.4, -13.6, -11.2, -10.9, -10.8, -10.7, -11.1, -13.5]
        fr_ = [np.ones(F5)] + [np.zeros(F5) if v < -200 else (lambda f: f / (np.sqrt(np.mean(f ** 2)) + 1e-20) * 10 ** (v / 20))(ss.sosfiltfilt(HP, rng_.standard_normal(3 * F5))[F5:2 * F5]) for v in reversed(sq_)]
        x_ = np.concatenate(fr_); m_ = len(x_) // F5; ref_ = np.sqrt(np.mean(x_[:m_ * F5].reshape(m_, F5) ** 2, axis=1)).max()
        if not judge(x_, release(x_, ss.sosfiltfilt(HP, x_), len(x_), ref_), 't'): miss.append('K152 除阻衰减里一帧凹口当成闭塞（41 S10 first,）判错拦')
        # K167 好样本（46 S5 lamp, 实测帧电平，从停顿往回）：两下连着的送气中间 6 dB 凹口，再往前 -57 dB 才是闭塞；必须判合格。坏样本：同样两下送气，前面没有 -50 dB 以下的闭塞（元音连着），必须照报
        for sq_, want_, nm_ in (([-65.4, -56.4, -49.7, -40.0, -37.8, -34.5, -29.1, -28.9, -34.0, -35.5, -25.7, -20.5, -28.4, -57.2, -58.7, -54.8, -60.2, -240.0, -240.0, -30.0, -20.0, -15.0, -12.0, -11.0, -10.0, -10.0], True, '两下送气中间凹口'),
                                ([-65.4, -56.4, -49.7, -40.0, -37.8, -34.5, -29.1, -28.9, -34.0, -35.5, -25.7, -20.5, -28.4, -36.0, -30.0, -20.0, -15.0, -12.0, -11.0, -10.0, -10.0, -10.0, -10.0, -10.0, -10.0, -10.0], False, '凹口前面没有闭塞')):
            fr_ = [np.ones(F5)] + [np.zeros(F5) if v < -200 else (lambda f: f / (np.sqrt(np.mean(f ** 2)) + 1e-20) * 10 ** (v / 20))(ss.sosfiltfilt(HP, rng_.standard_normal(3 * F5))[F5:2 * F5]) for v in reversed(sq_)]
            x_ = np.concatenate(fr_); m_ = len(x_) // F5; ref_ = np.sqrt(np.mean(x_[:m_ * F5].reshape(m_, F5) ** 2, axis=1)).max()
            if bool(judge(x_, release(x_, ss.sosfiltfilt(HP, x_), len(x_), ref_), 'p')) != want_: miss.append(f'K167 {nm_}（46 S5 lamp,）判{"错拦" if want_ else "错放"}')
        # K170 坏样本（46 S8 back）：/k/ 除阻没了，往前是闭塞残响、再往前是 æ 元音尾巴（-42 dB 上下、有基频周期、高频够）：不许判合格；好样本：同样位置是 60 ms 高频送气噪声，照收
        t3_ = tt_(0.06); vw_ = sum(np.sin(2 * np.pi * 180 * h * t3_) * (0.1 if h <= 4 else 1) for h in range(1, 25)) * 0.01 * np.concatenate([np.linspace(0.6, 1, len(t3_) // 3), np.geomspace(1, 0.02, len(t3_) - len(t3_) // 3)])   # 旧判法全过（-26 dB、高频 -28、55 ms、重心 2.6 kHz、800 Hz 以下 -43），只有周期性 0.87 拦得住
        for nm_, x_, want_ in (('元音尾巴当除阻', np.concatenate([loud_, z0_, vw_, np.zeros(n_(0.12)), z0_]), False), ('真除阻', np.concatenate([loud_, z0_, vw_, np.zeros(n_(0.03)), b_, z0_]), True)):
            m_ = len(x_) // F5; ref_ = np.sqrt(np.mean(x_[:m_ * F5].reshape(m_, F5) ** 2, axis=1)).max()
            if judge(x_, release(x_, ss.sosfiltfilt(HP, x_), len(x_), ref_), 'k') != want_: miss.append(f'K170 {nm_}（46 S8 back）判{"错放" if not want_ else "错拦"}')
        # K171 坏样本（46 S4 brightest）：闭塞 40 ms → 原声除阻 → 10 ms 静音 → 移植的除阻：必须报双爆破；好样本：/s/ 擦音 → 40 ms 闭塞 → 一下除阻，不报
        s8_ = ss.sosfiltfilt(HP, rng_.standard_normal(n_(0.12))) * 0.3; zc_ = np.zeros(n_(0.04)); zg_ = np.zeros(n_(0.01))   # 好样本按 24 S8 collapsed 实测：/s/ 120 ms -13 dB、闭塞 15 ms
        for nm_, x_, want_ in (('双爆破', np.concatenate([loud_, zc_, b_ * 0.5, zg_, b_, z0_]), True), ('擦音+闭塞+一下除阻', np.concatenate([loud_, s8_, np.zeros(n_(0.015)), b_, z0_]), False)):
            m_ = len(x_) // F5; ref_ = np.sqrt(np.mean(x_[:m_ * F5].reshape(m_, F5) ** 2, axis=1)).max(); h_ = ss.sosfiltfilt(HP, x_)
            if bool(双爆破(x_, h_, release(x_, h_, len(x_), ref_), ref_)) != want_: miss.append(f'K171 {nm_}（46 S4 brightest）判{"错放" if want_ else "错拦"}')
        # K172 真片坏样本（46 S8 back, 成片声音，样本/46_S8_back_out.npy，停顿在 79920）：原始合成 3.14 和 3.25 秒两下 /k/ 爆破、隔 20 ms 静音：必须报双爆破
        _np46 = os.path.join(os.path.dirname(os.path.abspath(__file__)), '样本', '46_S8_back_out.npy')
        if os.path.exists(_np46):
            x_ = np.load(_np46).astype(np.float64); m_ = len(x_) // F5; ref_ = np.sqrt(np.mean(x_[:m_ * F5].reshape(m_, F5) ** 2, axis=1)).max(); h_ = ss.sosfiltfilt(HP, x_)
            if not 双爆破(x_, h_, release(x_, h_, 79920, ref_), ref_): miss.append('K172 46 S8 back, 原声两下 /k/ 爆破没报双爆破')
        else: miss.append('K172 真片样本 样本/46_S8_back_out.npy 不见了')
        ok = n_ok > 0 and not miss
        print(f"{'✔' if ok else '✘'} 词尾辅音核对 自检：{no} 原样 {n_ok} 处全部合格；逐处把除阻换成静音、压低 20 dB，共 {2 * n_ok} 次" + ('全部报出' if not miss else f'，没报出 {len(miss)} 次：' + '；'.join(miss)))
        sys.exit(0 if ok else 1)
    total = 0
    for no in args:
        d = json.load(open(f'scripts/{no}.json'))
        rows, bad, info = check(no, d)
        if '--写入' in sys.argv and bad:
            sentence_items_cache = {lab: [cuts] for lab, text, out, starts, fin, cuts in sentence_items(d)}
            write_grafts(no, d, bad); print('已写入，请重跑核对'); sys.exit(2)
        print('\n'.join(rows)); print('\n'.join('参考 ' + x for x in info))
        print(f'{no} 词尾辅音核对 问题数 {len(bad)}'); total += len(bad)
    sys.exit(1 if total else 0)
