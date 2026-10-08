#!/usr/bin/env python3
"""每篇视频的交付核查（硬性条件：不通过不得交付）。在视频工作目录（含 make_video.py、scripts/、work_NN/）下运行：
  python3 <工具目录>/交付核查.py NN 对照表     # 开工第一步：生成"踩坑对照记录"模板，逐条填写
  python3 <工具目录>/交付核查.py NN 出片前     # 合成配音前：数字读法、标点停顿、句首句尾、无标点停顿
  python3 <工具目录>/交付核查.py NN 出片后     # 出片后：自动音频检查、独立复核（逐样本比对原始合成）、生成标点试听
对应踩坑：A8 分段合成发闷、A9 停顿放错、A10/A10b 词尾被切、A11 数字读错、A12 连读处停顿越界、L13 换行。
最高铁律（硬性条件第〇节）：出片前先过《踩坑核查》（踩坑对照记录逐条写全、能用程序查的坑逐条查、换行比对）；出片后先做核查程序自检（故意剪坏一份副本，必须全部抓到），自检不过 = 核查失灵，不得交付。"""
import sys, os, re, json, subprocess
T = os.path.dirname(os.path.abspath(__file__)); no, stage = sys.argv[1].zfill(2), sys.argv[2]
ok = True; out = []
def run(cmd, env=None):
    r = subprocess.run(cmd, capture_output=True, text=True, env={**os.environ, **(env or {})})
    return r.returncode, r.stdout + r.stderr
def step(name, passed, detail=''):
    global ok
    ok &= passed; out.append(f"{'✔' if passed else '✘'} {name}" + (f"\n    {detail}" if detail else ''))

if stage == '对照表':
    # 生成"踩坑对照记录"模板，追加到 制作记录/NN.md；逐条填"涉及/不涉及"和"怎么防的、核查结果"
    rec = f'{T}/../制作记录/{no}.md'; txt = open(rec).read() if os.path.exists(rec) else f'# 第{no}篇制作记录\n'
    if '## 踩坑对照记录' in txt: sys.exit(f'制作记录/{no}.md 已有"## 踩坑对照记录"，不覆盖')
    rows = re.findall(r'^\| *([A-Z]\d+b?) *\|([^|]*)\|', open(f'{T}/../踩坑总表.md').read(), re.M)
    tab = ['', '## 踩坑对照记录', '', '> 开工前逐条重读《踩坑总表》后填写；交付前再对照一遍。第三列只写"涉及"或"不涉及"，第四列写怎么防的、核查结果。', '',
           '| 编号 | 坑（摘要） | 本篇是否涉及 | 怎么防的、核查结果 |', '|---|---|---|---|']
    tab += [f"| {i} | {re.sub(r'[*`]', '', d).strip()[:40]} | 待填 | 待填 |" for i, d in rows]
    open(rec, 'w').write(txt.rstrip('\n') + '\n' + '\n'.join(tab) + '\n'); print(f'已生成 制作记录/{no}.md 的踩坑对照记录模板（{len(rows)} 条），逐条填完才能通过出片前核查'); sys.exit(0)
elif stage == '出片前':
    # 0 踩坑核查（最高铁律）：核查程序自检 + 踩坑对照记录逐条填完 + 能用程序查的坑逐条查 + 换行与用户看过的版本比对（L13）
    c, o = run(['python3', f'{T}/踩坑核查.py', no, '出片'])
    step('踩坑核查（核查程序自检、踩坑对照记录、逐条程序核查、换行比对）', c == 0, '' if c == 0 else '\n    '.join(o.strip().splitlines()))
    # 1 数字读法（A11）：列出全文所有数字及配音实际读法，供人工逐个核对；出现未处理的格式即不合格
    src = open('make_video.py').read(); exec(src[src.index('# 朗读用的数字读法'):src.index('def say(t):')])
    d = json.load(open(f'scripts/{no}.json'))
    texts = [d['title_en']] + [' '.join(re.sub(r'\*\*|\{\{.*?\}\}', '', c['en']).strip() for c in s['chunks']) for s in d['sentences']]
    rows = []; odd = []
    for x in texts:
        for m in re.finditer(r"\S*\d\S*", x):
            ctx = x[max(0, m.start()-12):m.end()+12]
            rows.append(f"{m.group(0):>14}  →  {spoken(ctx)}")
            if re.search(r'\d+\.\d+|%|\$|£|€|\d+/\d+', m.group(0)): odd.append(m.group(0))
    step('数字读法清单（请人工逐个确认读法）', not odd, '\n    '.join(rows) + (f"\n    未处理的数字格式：{odd}" if odd else ''))
    # 2–4 停顿与词尾
    c, o = run(['python3', f'{T}/标点停顿核对.py', no]); step('标点停顿核对（A9/A10：停顿时长、不切词）', '问题数 0' in o, '' if '问题数 0' in o else '\n    '.join(l for l in o.splitlines() if 'BAD' in l or 'FAIL' in l))
    c, o = run(['python3', f'{T}/句首句尾与停顿位置核对.py', no]); step('句首句尾与停顿位置核对', '问题数 0' in o, '' if '问题数 0' in o else '\n    '.join(l for l in o.splitlines() if 'BAD' in l))
    c, o = run(['python3', f'{T}/无标点停顿核对.py', no])
    long = [l for l in o.splitlines() if re.search(r'停顿 (\d+\.\d+)s', l) and float(re.search(r'停顿 (\d+\.\d+)s', l).group(1)) > 0.22]
    step('无标点处停顿 ≤ 0.22 秒', not long, '\n    '.join(long))
elif stage == '出片后':
    c, o = run(['python3', f'{T}/audio_qc.py', f'{no}.mp4'])
    step('自动音频检查（削波、电流音、停顿超长、响度骤降）', c == 0, o.strip() + ('\n    → 标出的位置必须剪成试听交用户确认' if c else ''))
    env = {'VIDEO_ROOT': os.path.abspath('..')}
    for sc in ('synth.py', 'labels.py'):
        c, o = run(['python3', f'{T}/独立复核/{sc}', no], env); 
        if c: step(f'独立复核准备 {sc}', False, o[-500:])
    # 核查程序自检（阳性对照，防"自己检查自己""门槛靠估计"）：在 a.wav 副本上故意造 5 处瑕疵，独立复核必须在对应位置全部抓到：
    #   词尾轻切 / 词头轻切：剪到还有 -52 dB 声音的地方（比 -55 dB 标准只高 3 dB，A10 那类弱音）
    #   词尾重切 / 词头重切：剪进 -40 dB 以上的词音（gastritis、himself 那类）
    #   杂音：在一处停顿里加 5 ms 杂音
    import numpy as np, soundfile as sf, tempfile, shutil
    a, sr = sf.read(f'work_{no}/a.wav', dtype='int16'); W = os.environ.get('QC_DIR', os.path.abspath('..') + '/qc_independent')
    x = a.astype(float) / 32768; ms = sr // 1000; F5 = 5 * ms
    cs = np.concatenate([[0], np.cumsum(x ** 2)])
    def lv(p0, p1, ref):   # [p0,p1) 内每个 5 ms 窗（逐样本滑动）的 dB，返回 (最小, 最大)
        e = (cs[p0 + F5:p1 + 1] - cs[p0:p1 - F5 + 1]) / F5; v = 10 * np.log10(np.maximum(e, 1e-20) / ref ** 2); return v.min(), v.max()
    z = np.concatenate([[0], (a == 0).astype(np.int8), [0]]); d = np.diff(z); zs = list(zip(np.where(d == 1)[0], np.where(d == -1)[0]))
    big = [r for r in zs if (r[1] - r[0]) / sr >= 0.6]                                   # 句与句之间
    zr = [r for r in zs if 0.1 <= (r[1] - r[0]) / sr <= 0.5 and r[0] / sr > 1.0]        # 句内标点停顿（插入的静音）
    def sref(r):           # 本句最响 5 ms（逐样本滑动的最大值 ≥ 复核用的分帧最大值，故这里算出的电平只会偏低，判定偏保守）
        s0 = max([q[1] for q in big if q[1] <= r[0]] or [0]); s1 = min([q[0] for q in big if q[0] >= r[1]] or [len(a)])
        e = (cs[s0 + F5:s1 + 1] - cs[s0:s1 - F5 + 1]) / F5; return np.sqrt(e.max())
    def tail_cut(r, th):   # 从停顿起点往前找：剪掉 [p, 停顿起点)，使 p 之前 20 ms 每个 5 ms 窗都 > th dB
        ref = sref(r)
        if lv(r[0] - F5, r[0], ref)[1] > -52: return None                                # 连读插入处（没删声音），不用于自检
        for p in range(r[0] - 10 * ms, r[0] - 150 * ms, -ms):
            if lv(p - 20 * ms, p, ref)[0] > th: return p
    def onset_cut(r, th):  # 从停顿终点往后找：剪掉 [停顿终点, p)
        ref = sref(r)
        if lv(r[1], r[1] + F5, ref)[1] > -52: return None
        for p in range(r[1] + 10 * ms, r[1] + 150 * ms, ms):
            if lv(p, p + 20 * ms, ref)[0] > th: return p
    plan = {}; used_t = set(); used_o = set()
    for name, kind, th in (('词尾轻切', 't', -52), ('词头轻切', 'o', -52), ('词尾重切', 't', -40), ('词头重切', 'o', -40)):
        for k, r in enumerate(zr):
            if k in (used_t if kind == 't' else used_o): continue
            p = (tail_cut if kind == 't' else onset_cut)(r, th)
            if p is not None: plan[name] = (kind, r, p); (used_t if kind == 't' else used_o).add(k); break
    if len(plan) < 4 or not zr: step('核查程序自检', False, f'本篇找不到足够的标点停顿来造瑕疵（{list(plan)}），需人工处理')
    else:
        b = a.copy()
        for kind, r, p in plan.values():
            if kind == 't': b[p:r[0]] = 0
            else: b[r[1]:p] = 0
        rc = zr[-1]; m = (rc[0] + rc[1]) // 2; b[m:m + F5] = (600 * np.sin(2 * np.pi * 1000 * np.arange(F5) / sr)).astype(np.int16)
        tmp = tempfile.mkdtemp(prefix='自检_', dir=f'work_{no}')
        try:
            os.makedirs(f'{tmp}/video/work_{no}'); os.makedirs(f'{tmp}/qc'); os.symlink(os.path.abspath(f'{W}/gt'), f'{tmp}/qc/gt')
            sf.write(f'{tmp}/video/work_{no}/a.wav', b, sr, subtype='PCM_16')
            c, o = run(['python3', f'{T}/独立复核/audit.py', no], {'VIDEO_ROOT': tmp, 'QC_DIR': f'{tmp}/qc'})
        finally: shutil.rmtree(tmp)
        # 只认复核程序自己的判定（词尾/词头被切 ms、A10_VIOLATION 标出的那一侧），不在这里另算门槛
        ed = [(float(tl), float(on), float(p0), float(p1), v) for tl, on, p0, p1, v in re.findall(
            r'cut tail=([\d.]+)ms onset=([\d.]+)ms.*\n\s*edit raw \S+ A ([\d.]+)-([\d.]+).*\n\s*edge .*? (ok|A10_VIOLATION\([a-z,]*\))', o)]
        res = []
        for name, (kind, r, p) in plan.items():
            t0 = (r[0] if kind == 't' else r[1]) / sr
            hit = any(p0 - 0.01 <= t0 <= p1 + 0.01 and ((tl > 0 or 'pre' in v) if kind == 't' else (on > 0 or 'post' in v)) for tl, on, p0, p1, v in ed)
            res.append((f'{name}（{t0:.2f}s，剪 {abs(p - (r[0] if kind == "t" else r[1])) / ms:.0f} ms）', hit))
        hitc = any(abs(float(t) - m / sr) < 0.02 for t in re.findall(r'extra at ([\d.]+) s', o)); res.append((f'杂音（{m / sr:.2f}s）', hitc))
        allhit = all(h for _, h in res)
        step('核查程序自检：' + '、'.join(f'{n}{"抓到" if h else "没抓到"}' for n, h in res), allhit,
             '' if allhit else '【核查程序失灵，下面的独立复核结果不可信，不得交付】\n    ' + o[-800:])
    c, o = run(['python3', f'{T}/独立复核/audit.py', no], env)
    cuts = re.findall(r'cut tail=([\d.]+)ms onset=([\d.]+)ms', o); bad = [x for x in cuts if float(x[0]) > 0 or float(x[1]) > 0]
    extra = re.findall(r'extra non-zero runs not explained by raw copies: (\d+)', o)
    edge = re.findall(r'A10 edge violations [^:]*: (\d+)', o); viol = '\n    '.join(l.strip() for l in o.splitlines() if 'A10_VIOLATION' in l)
    good = c == 0 and not bad and extra == ['0'] and edge == ['0']
    step(f'独立复核：{len(cuts)} 处改动，词尾/词头被切 = {len(bad)}，删除处两侧未衰减到 -55 dB 或删掉了 -40 dB 以上的声音 = {edge}，多余声音 = {extra}', good, '' if good else (viol + '\n    ' + o[-800:]))
    # 标点试听（交用户逐处听）
    import imageio_ffmpeg
    FF = imageio_ffmpeg.get_ffmpeg_exe(); a, sr = sf.read(f'work_{no}/a.wav')
    subprocess.run([FF, '-v', 'error', '-y', '-i', f'{no}.mp4', '-vn', '-ac', '1', '-ar', str(sr), f'work_{no}/final.wav'], check=True)
    f, _ = sf.read(f'work_{no}/final.wav'); z = np.append((a == 0).astype(np.int8), 0); runs = []; st = None
    for i, v in enumerate(z):
        if v and st is None: st = i
        if not v and st is not None:
            if 0.1 <= (i - st) / sr <= 0.5 and st / sr > 1.0: runs.append((st / sr, i / sr))
            st = None
    beep = 0.15 * np.sin(2 * np.pi * 880 * np.arange(int(0.12 * sr)) / sr) * np.hanning(int(0.12 * sr)); parts = []
    for s0, s1 in runs: parts += [f[int((s0 - 1.6) * sr):int((s1 + 0.7) * sr)], np.zeros(int(0.35 * sr)), beep, np.zeros(int(0.35 * sr))]
    if parts:
        sf.write(f'work_{no}/punct.wav', np.concatenate(parts), sr)
        subprocess.run([FF, '-v', 'error', '-y', '-i', f'work_{no}/punct.wav', '-c:a', 'libmp3lame', '-b:a', '192k', f'标点试听_{no}.mp3'], check=True)
    step(f'生成标点试听 标点试听_{no}.mp3（{len(runs)} 处，需交用户试听）', True)
print(f'第{no}篇 {stage}核查：\n' + '\n'.join(out) + f"\n{'全部通过' if ok else '【不通过，不得交付】'}")
sys.exit(0 if ok else 1)
