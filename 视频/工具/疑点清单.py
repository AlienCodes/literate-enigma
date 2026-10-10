"""（疑点清单.py）每篇的“待查清单”：把 纯人声核对（①–⑥）和 A19（标点停顿后吸气）报出的每一处，换算到这一句整句合成声音 w 里的位置（脚本覆盖项用的就是 w 的秒数），
列出前后的词和音素（带时长模型的位置，换到 w 里）、逐 2.5 ms 的电平/周期/低频占比/重心，供逐处判定“是不是词的声音、切在哪里”。
用法（在视频工作目录，work_NN/a.wav 必须是当前出片程序刚做的）：python3 <工具目录>/疑点清单.py NN [输出目录]
输出：<输出目录>/dossier_NN.txt 与 dossier_NN.json。先核对重建的整片声音与 work_NN/a.wav 逐采样一致（差 ≤2 LSB），不一致就停。"""
import re, json, sys, os, importlib.util
import numpy as np, soundfile as sf
sys.path.insert(0, '.')
TOOLS = '/home/user/postgraduate-vocabulary/视频/工具'
src = open('make_video.py').read().split("if __name__")[0]
h1 = "    w=clean_tail(raw)\n"   # 出片程序：raw 是这一句的原始合成（结尾句是两遍接起来的），下一行起处理
assert src.count(h1) == 1, '出片程序结构变了'
src = src.replace(h1, h1 + "    _W0.append(w.copy())\n")
_W0 = []
exec(src, globals())
spec_ = importlib.util.spec_from_file_location('pv', f'{TOOLS}/纯人声核对.py'); pv = importlib.util.module_from_spec(spec_); spec_.loader.exec_module(pv)
no = sys.argv[1]; outdir = sys.argv[2] if len(sys.argv) > 2 else '.'
d = json.load(open(f'scripts/{no}.json'))
F5 = int(0.005 * SR)

# ---------- 重建整片（与 build() 完全相同的拼接） ----------
audio = [sil(0.4)]; title = title_audio(d['title_en'])
_tw0 = say(d['title_en']); _twz = _nonvoice(_tw0, NONVOICE['标题::' + d['title_en']], '标题') if '标题::' + d['title_en'] in NONVOICE else _tw0
_tcap = _purify(_cap_inner(_twz)); _ths = _edges(_tcap)[0]; _trm = sorted(_cap_spans(_twz))
audio += [title, sil(P_TITLE)]; cur = sum(len(x) for x in audio)
info = []; prev_para = None
for si, s in enumerate(d['sentences']):
    ch = s['chunks']; lead = P_FIRST if si == 0 else P_LEAD + (P_PARA_EXTRA if prev_para is not None and s['para'] != prev_para else 0)
    prev_para = s['para']
    texts = [re.sub(r'\*\*', '', R.strip_gloss(c['en'])).strip() for c in ch]; sent = ' '.join(texts)
    lst = set()
    for ml in re.finditer(r"(?:\b[\w'-]+(?: [\w'-]+){0,4}, ){2,}(?:and|or) ", sent):
        for mc in re.finditer(r',', ml.group(0)): lst.add(ml.start() + mc.start())
    pieces = []; p0 = 0; gaps = []
    for mm in re.finditer(r'[,;:](?=\s)', sent): pieces.append((p0, mm.end())); p0 = mm.end() + 1; gaps.append(P_LIST if mm.start() in lst else P_COMMA)
    pieces.append((p0, len(sent)))
    _W0.clear(); clips, tmap = sentence_audio(sent, pieces, gaps); a = np.concatenate(clips)
    off = cur + len(sil(lead))
    info.append(dict(si=si + 1, sent=sent, off=off, n=len(a), tmap=tmap, segs=[tuple(x[:3]) + (list(x[3]),) for x in LAST['segs']],
                     cuts=LAST['cuts'], toks=[(x.phoneme, x.start, x.end) for x in LAST['toks']], scale=LAST['scale'], head=LAST['head'], w0=_W0[-1], out=a))
    audio += [sil(lead), a, sil(P_HOLD)]; cur += len(sil(lead)) + len(a) + len(sil(P_HOLD))
audio.append(sil(2.0 - P_HOLD)); A = np.concatenate(audio); A = A / np.abs(A).max() * 0.89
B, sr = sf.read(f'work_{no}/a.wav'); B = np.asarray(B, float)
if len(A) != len(B) or np.abs(A - B).max() > 2 / 32768: raise SystemExit(f'【停止】重建的声音与 work_{no}/a.wav 不一致（长度 {len(A)} vs {len(B)}），work_{no} 不是当前程序做的')

# ---------- 候选：纯人声核对 ①–⑥ + A19 ----------
cands = [dict(kind=f[0], t0=f[1], t1=f[2], db=f[3], c=f[4], per=f[5], lo=f[6]) for f in pv.scan(B)]
BREATH_GAP = 0.10
def breath_after(out, t1):   # 与 标点停顿核对.py 的 breath_after 逐字相同（A19）
    e5 = _env5(out); F5_ = int(0.005 * SR); b = int(t1 * SR) // F5_
    while b < len(e5) and e5[b] < AUD_DB: b += 1
    n = int(0.01 * SR); m = len(out) // n; d10 = 10 * np.log10(np.mean(out[:m * n].reshape(m, n) ** 2, axis=1) + 1e-20); d10 -= d10.max()
    g = next((x for x in range((b * F5_) // n, m) if d10[x] >= -30), m)
    return max(0.0, g * n / SR - b * F5_ / SR)
for it in info:
    for k2 in range(len(it['tmap']) - 1):
        t1 = it['tmap'][k2 + 1][2]; g = breath_after(it['out'], t1)
        if g >= BREATH_GAP:
            e5 = _env5(it['out']); b = int(t1 * SR) // F5
            while b < len(e5) and e5[b] < AUD_DB: b += 1
            cands.append(dict(kind='A19停顿后吸气', t0=(it['off'] + b * F5) / SR, t1=(it['off'] + b * F5) / SR + g, db=0, c=0, per=0, lo=0))
cands.sort(key=lambda c: c['t0'])

# ---------- 换算 ----------
def to_w(it, tc):
    """成片这一句里的时刻 tc（秒，相对这一句声音开头）→ w 里的样本位置；落在插入的静音里返回 None"""
    for a0, b0, t0, rm in it['segs']:
        L = (b0 - a0) - sum(y - x for x, y in rm)
        if t0 - 1e-9 <= tc < t0 + L / SR:
            pr = int(round((tc - t0) * SR))
            for x, y in sorted(rm):
                if x <= pr: pr += y - x
            return a0 + pr
    return None

def words(it):
    out = []; grp = []
    for ph, st, en in it['toks'] + [(' ', None, None)]:
        if not ph.strip():
            if grp:
                p = ''.join(x[0] for x in grp)
                if p.strip(',;:.!?'): out.append((p, (grp[0][1] * it['scale'] * SR - it['head']) / SR, (grp[-1][2] * it['scale'] * SR - it['head']) / SR))
            grp = []
        else: grp.append((ph, st, en))
    return out

def per(x):
    x = x - x.mean()
    if np.sqrt(np.mean(x ** 2)) < 1e-9: return 0.0
    ac = np.correlate(x, x, 'full')[len(x) - 1:]; ac = ac / (ac[0] + 1e-12); return float(ac[60:343].max())

def spec(x):
    X = np.abs(np.fft.rfft(x * np.hanning(len(x)), n=4096)) ** 2; f = np.fft.rfftfreq(4096, 1 / SR)
    return float((np.sqrt(X) * f).sum() / (np.sqrt(X).sum() + 1e-12)), float(10 * np.log10(X[f < 150].sum() / (X.sum() + 1e-20) + 1e-12))

lines = []; js = []
ov = {k_: d.get(k_, {}) for k_ in ('非人声区间', '停顿删除区间', '停顿插入点')}
for n_, c in enumerate(cands, 1):
    i0 = int(round(c['t0'] * SR)); it = next((x for x in info if x['off'] <= i0 < x['off'] + x['n']), None)
    if it is None:
        tl0 = int(round(0.4 * SR))
        if not (tl0 <= i0 < tl0 + len(title)): raise SystemExit(f'【停止】{c} 不在任何一句里')
        def tw(i):   # 标题：成片 → 标题声音（去底噪、裁两头后）→ 压缩前 → w（say() 的输出）
            pr = i - tl0 + _ths
            for x, y in _trm:
                if x <= pr: pr += y - x
            return pr
        it = dict(si='标题', sent=d['title_en'], off=tl0, n=len(title), tmap=[(0, 0, 0.0, len(title) / SR)], cuts=[], w0=_tw0, toks=[], scale=1, head=0)
        p0 = tw(i0); p1 = tw(max(i0, int(round(c['t1'] * SR)) - 1)); tc0 = (i0 - tl0) / SR; tc1 = (int(round(c['t1'] * SR)) - tl0) / SR
    else:
        tc0 = (i0 - it['off']) / SR; tc1 = (int(round(c['t1'] * SR)) - it['off']) / SR
        p0 = to_w(it, tc0); p1 = to_w(it, max(tc0, tc1 - 1 / SR))
    w = it['w0']; m = len(w) // F5; ref = np.sqrt(np.mean(w[:m * F5].reshape(m, F5) ** 2, axis=1)).max()
    lv = lambda x: 20 * np.log10(np.sqrt(np.mean(x ** 2)) / ref + 1e-9) if len(x) else -99
    wd = words(it); wp0 = (p0 or 0) / SR; wp1 = (p1 or 0) / SR
    near = [(p, round(a, 3), round(b, 3)) for p, a, b in wd if b > wp0 - 0.35 and a < wp1 + 0.35]
    pos = '句首' if tc0 < 0.02 else ('句尾' if tc1 > it['n'] / SR - 0.02 else '句中')
    for k2 in range(len(it['tmap']) - 1):
        if abs(tc0 - it['tmap'][k2 + 1][2]) < 0.03: pos = f'第{k2 + 1}个标点停顿之后'
        if abs(tc1 - it['tmap'][k2][3]) < 0.03: pos = f'第{k2 + 1}个标点停顿之前'
    head = f"\n#{n_} {c['kind']} 成片 {c['t0']:.3f}–{c['t1']:.3f}s ｜ {'' if it['si'] == '标题' else 'S'}{it['si']} {pos} ｜ w 里 {wp0:.4f}–{wp1 + 1 / SR:.4f}s ｜ 最响 {c['db']:.1f} dB 重心 {c['c']:.0f} 周期 {c['per']:.2f} 低频 {c['lo']:.1f}"
    lines.append(head); lines.append(f"   句子：{it['sent']}")
    lines.append('   附近的词（带时长模型，w 秒）：' + '  '.join(f'{p}[{a:.3f}–{b:.3f}]' for p, a, b in near))
    cs = [(round(a / SR, 4), round(b / SR, 4), round(ins, 3)) for a, b, ins in it['cuts']]
    lines.append(f"   本句标点处的删除/插入（w 秒，补静音秒）：{cs}")
    kk = '标题' if it['si'] == '标题' else f"S{it['si']}"; so = {k_: v.get(kk) for k_, v in ov.items() if v.get(kk) is not None}
    if so: lines.append(f'   本句现有覆盖项：{so}')
    lines.append('   逐 2.5 ms（w 秒｜电平 dB，基准 = 本句最响 5 ms 帧｜20 ms 周期｜10 ms 低频占比 dB｜10 ms 重心 Hz｜该 2.5 ms 内过零点）：')
    a_ = max(0, (p0 or 0) - int(0.08 * SR)); b_ = min(len(w), (p1 or 0) + int(0.08 * SR))
    prof = []
    for i in range(a_, b_, 60):
        x = w[i:i + 60]; xx = w[max(0, i - 210):i + 270]; c_, lo_ = spec(w[max(0, i - 90):i + 150])
        zc = [round((i + j) / SR, 6) for j in range(1, len(x)) if x[j - 1] * x[j] <= 0]
        mark = ' ◀候选' if p0 is not None and p0 <= i <= (p1 or p0) else ''
        lines.append(f"   {i / SR:.4f} {lv(x):6.1f} {per(xx):5.2f} {lo_:6.1f} {c_:5.0f}  过零 {zc[:3]}{'…' if len(zc) > 3 else ''}{mark}")
        prof.append([round(i / SR, 4), round(lv(x), 1), round(per(xx), 2), round(lo_, 1), round(c_), zc])
    js.append(dict(c, id=n_, si=it['si'], pos=pos, w0=round(wp0, 4), w1=round(wp1 + 1 / SR, 4), words=near, profile=prof))
os.makedirs(outdir, exist_ok=True)
open(f'{outdir}/dossier_{no}.txt', 'w').write(f'{no} 待查清单：共 {len(cands)} 处（配音指纹 {__import__("hashlib").md5(open(f"work_{no}/a.wav","rb").read()).hexdigest()[:12]}）\n' + '\n'.join(lines) + '\n')
json.dump(js, open(f'{outdir}/dossier_{no}.json', 'w'), ensure_ascii=False, default=float)
print(no, '共', len(cands), '处 →', f'{outdir}/dossier_{no}.txt')
