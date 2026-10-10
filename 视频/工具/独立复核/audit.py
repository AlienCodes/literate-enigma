"""Independent completeness audit v2: sample-exact edit map of each raw Kokoro sentence inside a.wav.

For every text (title + sentences):
  * raw = deterministic Kokoro output (gt/NN_XX.npy); gx = g*raw (g = global gain, LS-estimated)
  * walk the raw in 10 ms blocks; each block with RMS > -60 dB re the sentence's peak 5 ms RMS is
    located in a.wav as an exact copy (|residual| <= TOL, ~2 LSB). Offset changes = splice points.
  * each splice is refined to the sample: raw[k1:k2) not reproduced (lost), A[k1+o1:k2+o2) inserted.
  * the raw is then reconstructed from a.wav through the offset map and compared to gx sample by sample.
Audible islands (5 ms frames within 45 dB of the sentence's peak frame RMS, merged if gap < 15 ms)
are then scored: lost audible samples, altered frames, silence inserted inside the island, NCC.
Also: everything in a.wav that is not a mapped raw sample must be digital zero (extra-content check).
A10 edge check (硬性条件): wherever raw audio was removed, the 15 ms kept on each side must already be below -55 dB
(the word tail had decayed / the next word had not started) and the removed part must stay below -40 dB.
"""
import sys, json, numpy as np, soundfile as sf
import os
S = os.environ.get('VIDEO_ROOT', os.path.abspath(os.path.join(os.getcwd(), '..')))  # 工作根目录：其下有 video/ 与 tts/
W = os.environ.get('QC_DIR', S + '/qc_independent'); os.makedirs(W, exist_ok=True)
SR = 24000; FR = 120; BL = 240
AUD = -45.0; SIG = -60.0; MERGE = 3
TOL = 2.2 / 32768
EDGE = -55.0; EDGE_W = 360; PAUSE_MAX = -40.0   # 硬性条件 A10：删除处两侧 15 ms 内必须已衰减到 -55 dB 以下；删掉的部分不得高于 -40 dB


def frms(x, fr=FR):
    n = int(np.ceil(len(x) / fr)); y = np.zeros(n * fr, np.float64); y[:len(x)] = x
    return np.sqrt(np.mean(y.reshape(n, fr) ** 2, axis=1))


def db(v, ref):
    return 20 * np.log10(np.maximum(np.asarray(v, float), 1e-12) / ref)


def islands(x):
    r = frms(x); pk = r.max(); m = db(r, pk) > AUD
    runs = []; i = 0; n = len(m)
    while i < n:
        if m[i]:
            j = i
            while j < n and m[j]: j += 1
            runs.append([i, j]); i = j
        else: i += 1
    merged = []
    for a, b in runs:
        if merged and a - merged[-1][1] < MERGE: merged[-1][1] = b
        else: merged.append([a, b])
    return [(a * FR, min(b * FR, len(x))) for a, b in merged], pk


def nextpow2(n):
    return 1 << int(np.ceil(np.log2(max(n, 2))))


def ncc_search(A, t, lo, hi):
    L = len(t); lo = max(0, lo); hi = min(len(A) - L, hi)
    if hi < lo: return None, -1.0
    seg = A[lo:hi + L]
    n = nextpow2(len(seg) + L)
    c = np.fft.irfft(np.fft.rfft(seg, n) * np.conj(np.fft.rfft(t, n)), n)[:hi - lo + 1]
    cs = np.concatenate([[0], np.cumsum(seg ** 2)])
    e = cs[L:L + hi - lo + 1] - cs[:hi - lo + 1]
    ncc = c / (np.linalg.norm(t) * np.sqrt(np.maximum(e, 1e-20)) + 1e-20)
    k = int(np.argmax(ncc))
    return lo + k, float(ncc[k])


def sliding_max_db(y, ref, win=FR):
    """max 5 ms RMS (1 ms hop) over y, in dB re ref; short y -> its own RMS"""
    if len(y) == 0: return -200.0
    if len(y) <= win: return float(db(np.sqrt(np.mean(y ** 2)), ref))
    c = np.concatenate([[0], np.cumsum(y ** 2)])
    e = (c[win:] - c[:-win]) / win
    return float(db(np.sqrt(e[::24].max()), ref))


def min_db(y, ref, win=FR):
    """min 5 ms RMS over every 5 ms window (1-sample hop) fully inside y, in dB re ref"""
    if len(y) < win: return 0.0
    c = np.concatenate([[0], np.cumsum(y ** 2)])
    return float(db(np.sqrt(max((c[win:] - c[:-win]).min() / win, 0)), ref))


def word_of(lab, t0, t1, pad=0.0):
    return ' '.join(w for w, a, b in lab['words'] if b > t0 - pad and a < t1 + pad)


def matches(A, gx, n0, n1, o):
    if n0 + o < 0 or n1 + o > len(A): return False
    return np.abs(A[n0 + o:n1 + o] - gx[n0:n1]).max() <= TOL


def audit(no, g=None, wav=None):
    A, sr = sf.read(wav or f'{S}/video/work_{no}/a.wav', dtype='float64'); assert sr == SR
    meta = json.load(open(f'{W}/gt/{no}_meta.json'))
    # 2026-10-10（10 S12 it.）：手动跑复核前没先跑 synth.py，标准答案还是改移植位置之前的，报出的“多余声音、错开 15 ms”是假的，白查了很久——
    # 标准答案比脚本、连读淡入淡出表、读音改正表旧就停（交付核查每次先跑 synth.py；自检的临时目录里没有脚本，只比读音改正表）
    mt_ = os.path.getmtime(f'{W}/gt/{no}_meta.json')
    for f_ in (f'{S}/video/scripts/{no}.json', f'{S}/video/work_{no}/淡入淡出.json', '/home/user/postgraduate-vocabulary/视频/工具/发音词典/读音改正.json'):
        if os.path.exists(f_) and os.path.getmtime(f_) > mt_: raise SystemExit(f'【停止】标准答案比 {f_} 旧，先跑 独立复核/synth.py {no}')
    labs ={l['idx']: l for l in json.load(open(f'{W}/gt/{no}_labels.json'))}
    if g is None:
        g = 0.89 / max(np.abs(np.load(it['file'])).max() for it in meta)
    rep = {'no': no, 'g': g, 'texts': [], 'n_islands': 0}
    cursor = int(0.2 * SR)
    explained = np.zeros(len(A), bool)
    for it in meta:
        x = np.load(it['file']).astype(np.float64); gx = g * x; N = len(x)
        isl, pk = islands(x); ref = pk * g; spk = np.abs(gx).max()
        lab = labs[it['idx']]
        br = frms(gx, BL); sig = db(br, ref) > SIG
        # anchor
        cand = max(range(min(3, len(isl))), key=lambda i: isl[i][1] - isl[i][0])
        a0 = isl[cand][0]; L0 = min(isl[cand][1] - a0, int(0.1 * SR))
        p, c = ncc_search(A, gx[a0:a0 + L0], cursor, cursor + int(6 * SR))
        o = p - a0
        # block walk
        blk = []   # (n0, n1, offset or None)
        for j in range(len(br)):
            n0 = j * BL; n1 = min(N, n0 + BL)
            if not sig[j]: continue
            if matches(A, gx, n0, n1, o):
                blk.append((n0, n1, o)); continue
            pj, cj = ncc_search(A, gx[n0:n1], n0 + o - int(1.0 * SR), n0 + o + int(1.6 * SR))
            if pj is not None and matches(A, gx, n0, n1, pj - n0):
                o = pj - n0; blk.append((n0, n1, o))
            else:
                blk.append((n0, n1, None))
        matched = [b for b in blk if b[2] is not None]
        # segments of constant offset; an unmatched block always breaks a segment
        segs = []; brk = False
        for n0, n1, oo in blk:
            if oo is None: brk = True; continue
            if segs and segs[-1][2] == oo and not brk: segs[-1][1] = n1
            else: segs.append([n0, n1, oo])
            brk = False
        # refine segment boundaries to the sample
        for s in segs:
            n0, n1, oo = s
            while n0 > 0 and n0 + oo > 0 and abs(A[n0 - 1 + oo] - gx[n0 - 1]) <= TOL: n0 -= 1
            while n1 < N and n1 + oo < len(A) and abs(A[n1 + oo] - gx[n1]) <= TOL: n1 += 1
            s[0], s[1] = n0, n1
        # build per-sample offset map; boundaries between segments may overlap (near-zero samples)
        edits = []
        for k in range(1, len(segs)):
            e1 = segs[k - 1]; s2 = segs[k]
            k1 = e1[1]; k2 = s2[0]; o1 = e1[2]; o2 = s2[2]
            if k2 < k1:   # overlapping match region (quiet) -> put splice where both still match: choose k1=k2=mid
                m = (k1 + k2) // 2; k1 = k2 = max(m, s2[0])
                k1 = min(k1, e1[1]); k2 = k1
            lost = gx[k1:k2]
            ins = A[k1 + o1:k2 + o2] if k2 + o2 > k1 + o1 else np.zeros(0)
            pre = gx[max(0, k1 - FR):k1]; post = gx[k2:k2 + FR]
            thr = ref * 10 ** (AUD / 20); thr_s = spk * 10 ** (AUD / 20)
            def run_ms(seq_start, step, limit, th):
                n = 0; pos_ = seq_start
                while n < limit:
                    fr_ = gx[pos_:pos_ + FR] if step > 0 else gx[max(0, pos_ - FR):pos_]
                    if len(fr_) == 0 or np.sqrt(np.mean(fr_ ** 2)) <= th: break
                    n += FR; pos_ += step * FR
                return n / SR * 1000
            lim = max(0, k2 - k1)
            edits.append({
                'tail_cut_ms': run_ms(k1, 1, lim, thr), 'onset_cut_ms': run_ms(k2, -1, lim, thr),
                'tail_cut_ms_spk': run_ms(k1, 1, lim, thr_s), 'onset_cut_ms_spk': run_ms(k2, -1, lim, thr_s),
                'first5_db': float(db(np.sqrt(np.mean(gx[k1:k1 + FR] ** 2)), ref)) if k2 > k1 else None,
                'last5_db': float(db(np.sqrt(np.mean(gx[max(k1, k2 - FR):k2] ** 2)), ref)) if k2 > k1 else None,
                'raw_k1': k1, 'raw_k2': k2, 'A_k1': k1 + o1, 'A_k2': k2 + o2,
                'lost_ms': (k2 - k1) / SR * 1000, 'shift_ms': (o2 - o1) / SR * 1000,
                'ins_ms': max(0, (k2 + o2) - (k1 + o1)) / SR * 1000,
                'ins_nonzero': int(np.sum(np.abs(ins) > 0.5 / 32768)),
                'lost_max_db': sliding_max_db(lost, ref),
                'lost_max_db_spk': sliding_max_db(lost, spk) if len(lost) else -200.0,
                'pre_db': float(db(np.sqrt(np.mean(pre ** 2)) if len(pre) else 0, ref)),
                'post_db': float(db(np.sqrt(np.mean(post ** 2)) if len(post) else 0, ref)),
                'pre_abs_last': float(abs(gx[k1 - 1])) if k1 > 0 else 0.0,
                'post_abs_first': float(abs(gx[k2])) if k2 < N else 0.0,
                'pre_min_db': min_db(gx[max(0, k1 - EDGE_W):k1], ref) if k2 > k1 else None,
                'post_min_db': min_db(gx[k2:k2 + EDGE_W], ref) if k2 > k1 else None,
                'words': word_of(lab, k1 / SR, k2 / SR, 0.05)})
            e_ = edits[-1]
            e_['edge_sides'] = [n for n, v in (('pre', k2 > k1 and e_['pre_min_db'] > EDGE), ('post', k2 > k1 and e_['post_min_db'] > EDGE),
                                               ('lost', k2 > k1 and e_['lost_max_db'] > PAUSE_MAX)) if v]
            e_['edge_bad'] = bool(e_['edge_sides'])
        offmap = np.full(N, np.nan)
        for k, s in enumerate(segs):
            lo_ = 0 if k == 0 else max(segs[k - 1][1], s[0]) if segs[k - 1][1] <= s[0] else s[0]
            lo_ = s[0] if k > 0 else 0
            hi_ = s[1] if k < len(segs) - 1 else N
            offmap[lo_:hi_] = s[2]
        for e in edits:  # lost ranges
            offmap[e['raw_k1']:e['raw_k2']] = np.nan
        # leading/trailing raw samples beyond A bounds
        idx = np.arange(N)
        ok = ~np.isnan(offmap)
        tgt = np.where(ok, idx + np.nan_to_num(offmap).astype(int), -1)
        ok &= (tgt >= 0) & (tgt < len(A))
        recon = np.zeros(N); recon[ok] = A[tgt[ok]]
        explained[tgt[ok]] = True
        # 相邻两段的匹配区重叠时（拼接点两侧是近零样本，两种偏移都在 TOL 内），offmap 只记后一段的偏移，
        # 前一段那份拷贝会被误判成"多余声音"（第06篇 S1 过零点精确插入处的 2 个 1 LSB 样本）。
        # 重叠区里逐样本核对：前一段偏移下与 raw 相差不超过 TOL 的，同样算已解释。
        for k in range(1, len(segs)):
            a0, a1, oa = segs[k - 1]; b0 = segs[k][0]
            for n in range(max(0, b0), min(a1, N)):
                if 0 <= n + oa < len(A) and abs(A[n + oa] - gx[n]) <= TOL: explained[n + oa] = True
        res = recon - gx
        # trailing/leading: where is the first/last sample of raw that actually exists in A (non-zero copy or faded)
        lead = gx[:segs[0][0]]; trail = gx[segs[-1][1]:]
        lead_A = recon[:segs[0][0]]; trail_A = recon[segs[-1][1]:]
        def lostdb(y, yA):
            d = y - yA
            return sliding_max_db(d, ref) if len(d) else -200.0
        leadtrail = {'lead_ms': segs[0][0] / SR * 1000, 'lead_max_db': sliding_max_db(lead, ref), 'lead_err_db': lostdb(lead, lead_A),
                     'trail_ms': (N - segs[-1][1]) / SR * 1000, 'trail_max_db': sliding_max_db(trail, ref), 'trail_err_db': lostdb(trail, trail_A),
                     'trail_first5_db': float(db(np.sqrt(np.mean(trail[:FR] ** 2)), ref)) if len(trail) else -200.0,
                     'last_isl_end_ms_before_trail': (segs[-1][1] - isl[-1][1]) / SR * 1000}
        tr = {'leadtrail': leadtrail, 'idx': it['idx'], 'text': it['text'], 'n_isl': len(isl), 'anchor_ncc': c,
              'A_start': (isl[0][0] + segs[0][2]) / SR, 'A_end': (isl[-1][1] + segs[-1][2]) / SR,
              'peak_rms_ref': ref, 'sample_peak': spk, 'n_unmatched_blocks': len(blk) - len(matched),
              'unmatched_blocks': [(b[0] / SR, b[1] / SR, round(float(db(br[b[0] // BL], ref)), 1)) for b in blk if b[2] is None],
              'edits': edits, 'segs': [(s[0], s[1], s[2]) for s in segs], 'islands': []}
        for i, (a, b) in enumerate(isl):
            t = gx[a:b]; r_ = recon[a:b]
            ncc = float(np.dot(r_, t) / (np.linalg.norm(r_) * np.linalg.norm(t) + 1e-20))
            lost_mask = np.isnan(offmap[a:b])
            # frames: altered = error > -20 dB re template frame and frame audible
            tf = frms(t); ef = frms(res[a:b]); rf = frms(r_)
            lv = db(tf, ref)
            alt = np.where((ef > 0.1 * tf + 2 * TOL) & (lv > AUD))[0]
            splits = [e for e in edits if a < e['raw_k1'] < b or a < e['raw_k2'] < b or (e['raw_k1'] <= a and e['raw_k2'] >= b)]
            rec = {'i': i, 'raw_t0': a / SR, 'raw_t1': b / SR,
                   'A_t0': float(a + np.nan_to_num(offmap[a]) ) / SR if not np.isnan(offmap[a]) else None,
                   'A_t1': float(b - 1 + offmap[b - 1]) / SR if not np.isnan(offmap[b - 1]) else None,
                   'dur_ms': (b - a) / SR * 1000, 'ncc': ncc, 'lvl_db': float(lv.max()),
                   'lost_samples': int(lost_mask.sum()),
                   'lost_audible_db': sliding_max_db(t[lost_mask], ref) if lost_mask.any() else None,
                   'alt_frames': [(int(f), round(float(lv[f]), 1), round(float(db(rf[f] + 1e-12, tf[f])), 1)) for f in alt],
                   'n_splits': len(splits),
                   'words': word_of(lab, a / SR, b / SR)}
            rec['ok'] = ncc >= 0.98 and rec['lost_samples'] == 0 and len(alt) == 0 and len(splits) == 0
            tr['islands'].append(rec)
        rep['n_islands'] += len(isl)
        rep['texts'].append(tr)
        last_seg = segs[-1]; cursor = last_seg[1] + last_seg[2]
    # extra content: A samples not explained by any mapped raw sample and not digital zero
    nz = (np.abs(A) > 0.5 / 32768) & ~explained
    runs = []; i = 0; n = len(A)
    idxs = np.where(nz)[0]
    if len(idxs):
        st = idxs[0]; pv = idxs[0]
        for v in idxs[1:]:
            if v - pv > 24: runs.append((st, pv + 1)); st = v
            pv = v
        runs.append((st, pv + 1))
    rep['extra_runs'] = [(s / SR, (e - s) / SR * 1000, float(np.abs(A[s:e]).max())) for s, e in runs]
    return rep


def fmt(no, rep):
    out = []
    P = out.append
    P(f'== {no}: texts={len(rep["texts"])} islands={rep["n_islands"]} g={rep["g"]:.7f}')
    for tr in rep['texts']:
        P(f"[{tr['idx']:>2}] {tr['A_start']:8.3f}-{tr['A_end']:8.3f}  isl={tr['n_isl']:3d} anchor={tr['anchor_ncc']:.4f} unmatched_blocks={tr['n_unmatched_blocks']} | {tr['text'][:80]}")
        for b in tr['unmatched_blocks']:
            if b[2] > -45: P(f"     unmatched block raw {b[0]:.3f}-{b[1]:.3f} lvl {b[2]} dB")
        lt = tr['leadtrail']
        P(f"     lead {lt['lead_ms']:.1f}ms max {lt['lead_max_db']:.1f} err {lt['lead_err_db']:.1f} | trail {lt['trail_ms']:.1f}ms max {lt['trail_max_db']:.1f} err {lt['trail_err_db']:.1f} first5 {lt['trail_first5_db']:.1f} lastIslEnd->trail {lt['last_isl_end_ms_before_trail']:.1f}ms")
        for e in tr['edits']:
            P(f"     cut tail={e['tail_cut_ms']:.0f}ms onset={e['onset_cut_ms']:.0f}ms (smpPk: {e['tail_cut_ms_spk']:.0f}/{e['onset_cut_ms_spk']:.0f}) first5={e['first5_db']} last5={e['last5_db']}")
            P(f"     edit raw {e['raw_k1']/SR:.4f}-{e['raw_k2']/SR:.4f} A {e['A_k1']/SR:.4f}-{e['A_k2']/SR:.4f} lost={e['lost_ms']:.1f}ms "
              f"(max {e['lost_max_db']:.1f} dB re rmsPk, {e['lost_max_db_spk']:.1f} re smpPk) shift={e['shift_ms']:+.1f}ms ins_nz={e['ins_nonzero']} "
              f"pre={e['pre_db']:.1f} post={e['post_db']:.1f} | {e['words']}")
            if e['raw_k2'] > e['raw_k1']:
                P(f"     edge pre_min={e['pre_min_db']:.1f} post_min={e['post_min_db']:.1f} lost_max={e['lost_max_db']:.1f} {'A10_VIOLATION(' + ','.join(e['edge_sides']) + ')' if e['edge_bad'] else 'ok'}")
        for r in tr['islands']:
            if not r['ok']:
                P(f"     ISL{r['i']:>3} raw {r['raw_t0']:.3f}-{r['raw_t1']:.3f} A {r['A_t0']}-{r['A_t1']} dur={r['dur_ms']:.0f}ms ncc={r['ncc']:.5f} "
                  f"lost={r['lost_samples']} lostdb={r['lost_audible_db']} alt={r['alt_frames'][:6]} splits={r['n_splits']} | {r['words']}")
    P('A10 edge violations (cut not inside -55 dB on both sides, or removed part above -40 dB): %d' % sum(e['edge_bad'] for tr in rep['texts'] for e in tr['edits']))
    P('extra non-zero runs not explained by raw copies: %d' % len(rep['extra_runs']))
    for e in rep['extra_runs'][:40]:
        P('   extra at %.4f s, %.1f ms, max %.6f' % e)
    return '\n'.join(out)


if __name__ == '__main__':
    for no in sys.argv[1:]:
        rep = audit(no)
        json.dump(rep, open(f'{W}/report2_{no}.json', 'w'), indent=0, ensure_ascii=False, default=float)
        txt = fmt(no, rep)
        open(f'{W}/report2_{no}.txt', 'w').write(txt)
        print(txt)
