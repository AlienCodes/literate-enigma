#!/usr/bin/env python3
"""可闻声保全核对（A21，2026-10-09 用户发现 06 的 date、intelligent 词尾 /t/ 没了）。
铁规矩：原始合成里任何听得见的声音（5 ms 帧 ≥-55 dB，基准 = 本句最响 5 ms 帧），在成片里必须原样保留（逐采样相同）；
只有落在脚本“非人声区间”“停顿删除区间”里（已逐处核实是呼吸声、噗声、杂音）的才允许删掉。
别的任何处理（句首句尾修剪、淡入淡出、停顿处自动删除、句中长停顿压缩、去底噪）都只许动听不见的部分；动了听得见的 = 删了词的声音 → BAD。
用法（视频工作目录）：python3 可闻声保全核对.py NN [NN ...] [--自检]
做法：exec 出片程序，逐句（含标题）取原始合成 raw 和这一句最终的声音 out，用出片程序自己的换算表把 raw 每个采样对到 out，
逐个比较是否相同；被删或被改的采样，按 raw 的 5 ms 帧算“损失能量”，≥-55 dB 的帧连成一段报出，并写出附近的音素（带时长模型）。
自检（阳性对照）：在一句的 out 里把一个词尾塞音的除阻（原本听得见的一小段）换成静音，必须报出这一处；原样不得多报。"""
import re, json, sys
import numpy as np
sys.path.insert(0, '.')
src = open('make_video.py').read().split("if __name__")[0]
h1 = "    raw,_=k.create(spoken(sent),voice=V,speed=SPEED,lang='en-us'); w=clean_tail(raw)\n"
assert src.count(h1) == 1, '出片程序结构变了，核对程序需要同步更新'
src = src.replace(h1, h1 + "    _RAW.append(np.asarray(raw,np.float32))\n")
_RAW = []
exec(src, globals())
F5 = int(0.005 * SR)


def lost_frames(raw, out, head, segs, ref, allowed=(), hs=0):
    """返回 raw 每个 5 ms 帧的“损失能量”（dB，相对 ref）：
    ① 整段删掉的采样（在成片里没有位置：句首句尾修剪、停顿处删除、句中长停顿压缩）按 raw 的 5 ms 帧量；
    ② 留在成片里但被改了的采样（淡入淡出、去底噪、非人声区间清零）按成片的 5 ms 帧量——去底噪本来就是按成片的帧判断“听不见”（_purify），
       同一口径才不会因为两套帧错开而误报；两种都不放宽 -55 dB。落在已核实区间（w 坐标）里的不算。"""
    n = len(raw) // F5
    o_of = np.full(len(raw), -1, np.int64)
    for a0, b0, t0, rm in segs:
        base = int(round(t0 * SR)); rm = sorted(rm)
        q = np.arange(b0 - a0); removed = np.zeros(len(q), bool); shift = np.zeros(len(q), np.int64)
        for x, y in rm:
            removed[x:y] = True; shift[y:] += (y - x)
        idx = np.where(~removed)[0]
        o_of[head + a0 + idx] = base + idx - shift[idx]
    ok_mask = np.zeros(len(raw), bool)
    for x, y in allowed: ok_mask[max(0, head + x):max(0, head + y)] = True
    # 句首 clean_tail 剪掉的部分：与留下的第一个能听见的帧之间隔着 ≥3 帧（15 ms）听不见的，是开口前孤立的杂音（句首句尾核对同一判据），不算
    lv = 20 * np.log10(np.sqrt(np.mean(raw[:n * F5].reshape(n, F5) ** 2, axis=1)) / ref + 1e-12)
    hf = head // F5; first = next((f for f in range(hf, n) if lv[f] >= AUD_DB), n)
    f = hf - 1
    while f >= 0 and lv[f] < AUD_DB: f -= 1
    if f >= 0 and first - f - 1 >= 3: ok_mask[:head] = True
    iv = np.arange(len(raw)); inside = (o_of >= 0) & (o_of < len(out))
    deleted = (~inside) & (~ok_mask)
    dl = np.where(deleted, raw.astype(np.float64), 0.0)[:n * F5]
    L_del = 20 * np.log10(np.sqrt(np.mean(dl.reshape(n, F5) ** 2, axis=1)) / ref + 1e-12)
    # 改动：按成片的帧（与 _purify 同一格：成片在裁两头前的位置 = o + hs）
    alt = inside & (~ok_mask)
    oi = o_of[alt] + hs; diff = raw[alt].astype(np.float64) - out[o_of[alt]].astype(np.float64)
    L_alt = np.full(n, -200.0)
    if len(oi):
        nb = oi.max() // F5 + 1; acc = np.zeros(nb); np.add.at(acc, oi // F5, diff ** 2)
        e_o = 20 * np.log10(np.sqrt(acc / F5) / ref + 1e-12)        # 成片每帧被改动的能量
        bad_o = e_o >= AUD_DB
        ri = iv[alt]; hit = bad_o[oi // F5]
        for r in np.unique(ri[hit] // F5):
            if r < n: L_alt[r] = max(L_alt[r], float(e_o[(o_of[r * F5:(r + 1) * F5][o_of[r * F5:(r + 1) * F5] >= 0] + hs) // F5].max()))
    return np.maximum(L_del, L_alt)


def check_sentence(label, raw, out, head, segs, allowed, toks, scale, hs=0):
    m = len(raw) // F5; ref = np.sqrt(np.mean(raw[:m * F5].reshape(m, F5) ** 2, axis=1)).max()
    L = lost_frames(raw, out, head, segs, ref, allowed, hs); bad = []
    f = 0
    while f < len(L):
        if L[f] < AUD_DB: f += 1; continue
        g = f
        while g < len(L) and L[g] >= AUD_DB: g += 1
        r0, r1 = f * F5, g * F5                      # raw 样本范围
        w0, w1 = r0 - head, r1 - head                # w 坐标
        if True:
            t = (r0 + r1) / 2 / SR
            near = ''.join(x.phoneme for x in toks if x.phoneme.strip() and abs(x.start * scale - t) < 0.15) if toks else ''
            bad.append(f"{label} raw {r0 / SR:.3f}–{r1 / SR:.3f}s（w {w0 / SR:.3f}–{w1 / SR:.3f}）删掉/改动了听得见的声音，最响 {L[f:g].max():.1f} dB，附近音素「{near}」")
        f = g
    return bad


def run(no, selftest=False):
    d = json.load(open(f'scripts/{no}.json')); rows = []
    # 允许删的：已核实的非人声区间、停顿删除区间（w 秒）
    nv = d.get('非人声区间', {}); da = d.get('停顿删除区间', {})
    def allowed_for(key):
        out = [(int(round(float(iv[0]) * SR)), int(round(float(iv[1]) * SR))) for iv in nv.get(key, [])]
        out += [(int(round(float(v[0]) * SR)), int(round(float(v[1]) * SR))) for v in da.get(key, {}).values()]
        return out
    # 标题
    tw = say(d['title_en']); traw = None
    title = d['title_en']; rawt, _ = k.create(spoken(re.sub(r'\*\*', '', R.strip_gloss(title))), voice=V, speed=SPEED, lang='en-us')
    rawt = np.asarray(rawt, np.float32); wt = clean_tail(rawt); ht = _head_offset(rawt, wt)
    wz = _nonvoice(wt, NONVOICE['标题::' + title], '标题') if '标题::' + title in NONVOICE else wt
    cap = _cap_inner(wz); pur = _purify(cap); hs, te = _edges(pur); outt = pur[hs:te]
    rm = sorted(_cap_spans(wz)); segs_t = [(0, len(wz), -hs / SR, rm)]
    rows += check_sentence('标题', rawt, outt, ht, segs_t, allowed_for('标题'), None, 1, hs)
    for si, s in enumerate(d['sentences'], 1):
        texts = [re.sub(r'\*\*', '', R.strip_gloss(c['en'])).strip() for c in s['chunks']]; sent = ' '.join(texts)
        lst = set()
        for ml in re.finditer(r"(?:\b[\w'-]+(?: [\w'-]+){0,4}, ){2,}(?:and|or) ", sent):
            for mc in re.finditer(r',', ml.group(0)): lst.add(ml.start() + mc.start())
        pieces = []; p0 = 0; gaps = []
        for mm in re.finditer(r'[,;:](?=\s)', sent): pieces.append((p0, mm.end())); p0 = mm.end() + 1; gaps.append(P_LIST if mm.start() in lst else P_COMMA)
        pieces.append((p0, len(sent)))
        _RAW.clear(); clips, tm = sentence_audio(sent, pieces, gaps); out = np.concatenate(clips); raw = _RAW[-1]
        if selftest:
            return raw, out, LAST, allowed_for(f'S{si}'), sent
        rows += check_sentence(f'S{si}', raw, out, LAST['head'], LAST['segs'], allowed_for(f'S{si}'), LAST['toks'], LAST['scale'], int(round(-LAST['segs'][0][2] * SR)))
    return rows


if __name__ == '__main__':
    if '--自检' in sys.argv:
        no = sys.argv[1]
        raw, out, last, allowed, sent = run(no, selftest=True)
        base = check_sentence('S1', raw, out, last['head'], last['segs'], allowed, last['toks'], last['scale'])
        # 找第一个词尾塞音（t d k p）之后的一小段听得见的声音，在 out 里换成静音
        toks = last['toks']; sc = last['scale']; m = len(raw) // F5
        ref = np.sqrt(np.mean(raw[:m * F5].reshape(m, F5) ** 2, axis=1)).max()
        target = None
        for i, x in enumerate(toks[:-1]):
            if x.phoneme in 'tdkp' and not toks[i + 1].phoneme.strip():
                r0 = int(x.start * sc * SR); r1 = int((x.end * sc + 0.03) * SR)
                fr = [f for f in range(r0 // F5, min(m, r1 // F5)) if 20 * np.log10(np.sqrt(np.mean(raw[f * F5:(f + 1) * F5] ** 2)) / ref + 1e-12) >= -50]
                if len(fr) >= 2: target = (fr[0] * F5, (fr[0] + 2) * F5); break
        if target is None: print('✘ 可闻声保全核对 自检：第一句找不到词尾塞音，换一篇自检'); sys.exit(1)
        o_bad = out.copy(); segs = last['segs']; head = last['head']
        for i in range(*target):
            p = i - head
            for a0, b0, t0, rm in segs:
                if a0 <= p < b0:
                    q = p - a0; q -= sum(min(q, y) - x for x, y in rm if x < q); o = int(round(t0 * SR)) + q
                    if 0 <= o < len(o_bad): o_bad[o] = 0
        got = check_sentence('S1', raw, o_bad, head, segs, allowed, toks, sc)
        new = [r for r in got if r not in base]
        hit = any(f'raw {target[0] / SR:.3f}' in r or abs(float(r.split('raw ')[1].split('–')[0]) - target[0] / SR) < 0.02 for r in new)
        ok = (not base) and hit
        print(f"{'✔' if ok else '✘'} 可闻声保全核对 自检：{no} S1 原样{'不报' if not base else '已有报警（自检前提不成立）'}；把 {target[0] / SR:.3f}s 的词尾塞音除阻换成静音，{'报出' if hit else '没报出'}")
        sys.exit(0 if ok else 1)
    bad = 0
    for no in [a for a in sys.argv[1:] if not a.startswith('--')]:
        rows = run(no); bad += len(rows)
        print('\n'.join(f'{no} BAD {r}' for r in rows) if rows else f'{no} 全部听得见的声音都原样保留')
    print('问题数', bad)
    sys.exit(1 if bad else 0)
