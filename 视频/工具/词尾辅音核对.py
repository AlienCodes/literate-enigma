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
import re, json, sys
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


def judge(x, z, ph):
    if z is None: return False
    if ph in 'tk': return z[1] >= TH_HF and z[2] <= DUR_MAX and centroid(x, *z[3]) >= CEN_MIN
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
            if z is not None and ph in 'tk': desc += f'、重心 {centroid(out, *z[3])} Hz'
            line = f"{no} {lab} {where} {word} /{ph}/ {'OK ' if ok else 'BAD'} {desc}（门槛：{'2 kHz 以上 ≥ %.0f dB、≤ %d ms、重心 ≥ %d Hz' % (TH_HF, DUR_MAX, CEN_MIN) if ph in 'tk' else '全频 ≥ %.0f dB' % TH_P}）"
            rows.append(line)
            if not ok: bad.append((lab, g, len(fin) - 1, ph, line))
    return rows, bad, info


def write_grafts(no, d, bad):
    """不合格的 t/k：在 w（clean_tail + _keep_tail + 非人声区间之后、移植之前）里找闭塞最低点之后的位置，写进 scripts/NN.json 的"词尾除阻\""""
    gj = d.setdefault('词尾除阻', {}); n = 0
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
            gdb = min(6.0, round((TH_P - float(m_.group(1)) + 3) * 2) / 2)
            if float(m_.group(1)) + gdb < TH_P + 1: print('不能自动补（/p/ 除阻太弱，加 6 dB 也不够）：', line); continue
            ra, rb = pos_r[0], min(pos_r[1] + 2, pos_r[0] + 16)
            d.setdefault('除阻加强', {}).setdefault(lab, {})['句末' if g == last else str(g + 1)] = [round(ra * F5 / SR, 6), round(rb * F5 / SR, 6), gdb]; n += 1
            print(f'写入 {no} {lab} {"句末" if g == last else "第%d个标点" % (g + 1)} /p/ 除阻加强 w {ra * F5 / SR:.3f}–{rb * F5 / SR:.3f}s +{gdb} dB'); continue
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
                if not judge(out, z, ph):
                    print(f'✘ 词尾辅音核对 自检：{no} {lab} {word} 原样就不合格，自检前提不成立'); sys.exit(1)
                n_ok += 1
                for name, gain in (('换成静音', 0.0), ('压低 20 dB', 0.1)):
                    o = out.copy(); o[z[3][0]:z[3][1]] *= gain
                    z2 = release(o, ss.sosfiltfilt(HP, np.asarray(o, np.float64)), starts[g], ref)
                    if judge(o, z2, ph): miss.append(f'{lab} {word} {name}')
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
