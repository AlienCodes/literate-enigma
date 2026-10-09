#!/usr/bin/env python3
"""词尾辅音核对（A21，2026-10-09 用户：“Date后面那个t都没有翻译。Intelligent后面那个特也没有翻译……坚决防止以后这样的问题出现”）。
铁规矩：停顿前（, ; : 和句末，标题也算）的词尾清塞音，成片里必须听得清除阻（t 那一下爆破送气）：
  /t/ /k/：除阻里 2 kHz 以上的声音（爆破送气）最响 5 ms 帧 ≥ -36 dB；/p/：全频带最响 ≥ -33 dB（基准 = 这一句最响的 5 ms 帧）。
  （01–07 实测：清楚的词尾 t 在 -17～-34 dB；06 date, 只有 -53 dB、intelligent. 的被句尾修剪剪掉——用户听出来没有 t。
   配音模型在停顿前常常只闭塞、不除阻，“除阻”那一下重心只有 0.2–1 kHz，不是 t。）
  /d/ /b/ /ɡ/ 只列电平供参考（浊塞音靠声带振动和元音过渡，不判）。
做法：exec 出片程序，逐句（含标题）取这一句最终的声音 out 和每个停顿在 out 里开始的位置；从停顿开始处（句末 = out 结尾）往回：
  跳过听不见的帧 → 除阻 → 闭塞（比除阻最响低 ≥6 dB 的低谷）。往回 80 ms 内找不到闭塞 = 没有除阻 → 不合格。
用法（视频工作目录）：python3 词尾辅音核对.py NN [NN ...]       核对（出片前）
                     python3 词尾辅音核对.py NN --写入            不合格的 t/k 按出片程序的“词尾除阻”（_graft）算出位置写进 scripts/NN.json，重跑核对必须全过
                     python3 词尾辅音核对.py NN --自检            阳性对照：把一处合格的除阻在 out 里换成静音、另一份压低 20 dB，两份都必须报出；原样不报
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


def release(x, hp, P, ref):
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
    if c is None: return None
    return float(L[q:c].max()), float(H[q:c].max()), (c - q) * 5, (P - c * F5, P - q * F5)


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
    items.append(('标题', t, tout, [len(tout)], finals(list(tk)), []))
    for si, s in enumerate(d['sentences'], 1):
        sent = ' '.join(re.sub(r'\*\*', '', R.strip_gloss(c['en'])).strip() for c in s['chunks'])
        lst = set()
        for ml in re.finditer(r"(?:\b[\w'-]+(?: [\w'-]+){0,4}, ){2,}(?:and|or) ", sent):
            for mc in re.finditer(r',', ml.group(0)): lst.add(ml.start() + mc.start())
        pieces = []; p0 = 0; gaps = []
        for mm in re.finditer(r'[,;:](?=\s)', sent): pieces.append((p0, mm.end())); p0 = mm.end() + 1; gaps.append(P_LIST if mm.start() in lst else P_COMMA)
        pieces.append((p0, len(sent)))
        clips, _ = sentence_audio(sent, pieces, gaps); out = np.concatenate(clips); ln = [len(c) for c in clips]
        starts = [sum(ln[:2 * g + 1]) for g in range(len(LAST['cuts']))] + [len(out)]
        items.append((f'S{si}', sent, out, starts, finals(LAST['toks']), [(c[0], c[1]) for c in LAST['cuts']]))
    return items


def check(no, d, mutate=None):
    rows = []; bad = []; info = []
    for lab, text, out, starts, fin, cuts in sentence_items(d):
        if mutate: out = mutate(lab, out, starts, fin)
        m = len(out) // F5; ref = np.sqrt(np.mean(np.asarray(out[:m * F5], np.float64).reshape(m, F5) ** 2, axis=1)).max()
        hp = ss.sosfiltfilt(HP, np.asarray(out, np.float64))
        for g, (word, ph) in enumerate(fin):
            if ph not in 'tkpdbɡg': continue
            where = '句末' if g == len(fin) - 1 else f'第{g + 1}个标点'
            z = release(out, hp, starts[g], ref)
            desc = '没有除阻' if z is None else f'除阻全频 {z[0]:.1f} dB、2 kHz 以上 {z[1]:.1f} dB、{z[2]} ms'
            if ph in 'dbɡg': info.append(f'{no} {lab} {where} {word}（浊塞音，不判）{desc}'); continue
            ok = z is not None and (z[1] >= TH_HF if ph in 'tk' else z[0] >= TH_P)
            line = f"{no} {lab} {where} {word} /{ph}/ {'OK ' if ok else 'BAD'} {desc}（门槛：{'2 kHz 以上 ≥ %.0f' % TH_HF if ph in 'tk' else '全频 ≥ %.0f' % TH_P} dB）"
            rows.append(line)
            if not ok: bad.append((lab, g, len(fin) - 1, ph, line))
    return rows, bad, info


def write_grafts(no, d, bad):
    """不合格的 t/k：在 w（clean_tail + _keep_tail + 非人声区间之后、移植之前）里找闭塞最低点之后的位置，写进 scripts/NN.json 的"词尾除阻\""""
    gj = d.setdefault('词尾除阻', {}); n = 0
    for lab, g, last, ph, line in bad:
        if ph not in 'tk': print('不能自动补（只有 t、k 有供体）：', line); continue
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
                pos_c = c; deep = True
                if y >= end_lim: break
                f = y
        if deep: on = pos_c + 1
        else:
            on = fL + 1
            while on < len(e) and e[on] >= AUD_DB: on += 1
            on += 3
        sec = round(on * F5 / SR, 6); gj.setdefault('标题' if lab == '标题' else lab, {})[('句末' if g == last else str(g + 1))] = [sec, ph]; n += 1
        print(f'写入 {no} {lab} {"句末" if g == last else "第%d个标点" % (g + 1)} /{ph}/ 位置 w {sec:.6f}s（{"闭塞最低点之后" if deep else "没有真正的闭塞：词的声音衰减到 -55 dB 后再留 15 ms 闭塞"}）')
    if n:
        json.dump(d, open(f'scripts/{no}.json', 'w'), ensure_ascii=False, indent=1)
    return n


if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    if '--自检' in sys.argv:
        no = args[0]; d = json.load(open(f'scripts/{no}.json'))
        rows, bad, _ = check(no, d)
        if bad: print(f'✘ 词尾辅音核对 自检：{no} 原样已有不合格，自检前提不成立'); sys.exit(1)
        okrows = [r for r in rows if ' OK ' in r]
        if not okrows: print(f'✘ 词尾辅音核对 自检：{no} 没有可用来自检的词尾清塞音'); sys.exit(1)
        tgt = okrows[len(okrows) // 2].split(' ')[1:3]
        def mk(gain):
            def mut(lab, out, starts, fin):
                if lab != tgt[0]: return out
                g = len(fin) - 1 if tgt[1] == '句末' else int(re.search(r'\d+', tgt[1]).group()) - 1
                m = len(out) // F5; ref = np.sqrt(np.mean(np.asarray(out[:m * F5], np.float64).reshape(m, F5) ** 2, axis=1)).max()
                z = release(out, ss.sosfiltfilt(HP, np.asarray(out, np.float64)), starts[g], ref)
                o = out.copy(); o[z[3][0]:z[3][1]] *= gain; return o
            return mut
        hits = []
        for name, gain in (('换成静音', 0.0), ('压低 20 dB', 0.1)):
            _, b2, _ = check(no, d, mk(gain))
            hits.append((name, [x[4] for x in b2]))
        ok = all(len(h) == 1 and h[0].split(' ')[1:3] == tgt for _, h in hits)
        print(f"{'✔' if ok else '✘'} 词尾辅音核对 自检：{no} 原样全部合格；把 {tgt[0]} {tgt[1]} 的除阻" + '、'.join(f"{n}{'报出' if len(h) == 1 and h[0].split(' ')[1:3] == tgt else '没报准（%d 处）' % len(h)}" for n, h in hits))
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
