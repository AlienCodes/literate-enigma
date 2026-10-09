#!/usr/bin/env python3
"""每篇视频的交付核查（硬性条件：不通过不得交付）。在视频工作目录（含 make_video.py、scripts/、work_NN/）下运行：
  python3 <工具目录>/交付核查.py NN 对照表     # 开工第一步：生成"踩坑对照记录"模板，逐条填写
  python3 <工具目录>/交付核查.py NN 出片前     # 合成配音前：数字读法、标点停顿、句首句尾、无标点停顿
  python3 <工具目录>/交付核查.py NN 出片后     # 出片后：自动音频检查、响度一致性（EBU R128 逐句）、纯人声核对、句间停顿核对（A20）、独立复核（逐样本比对原始合成）、高亮同步核对、生成标点试听
对应踩坑：A8 分段合成发闷、A9 停顿放错、A10/A10b 词尾被切、A11 数字读错、A12 连读处停顿越界、L13 换行、L14 高亮没跟上朗读。
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
    # 引号不停顿（A17）：带引号的句子，朗读文字里必须已经去掉引号
    qbad = [x for x in texts if re.search(r'["“”‘’]|(?<![A-Za-z])\'|\'(?![A-Za-z])', x) and re.search(r'["“”‘]|(?<![A-Za-z])[\'’]|[\'’](?![A-Za-z])', spoken(x))]
    qn = sum(1 for x in texts if re.search(r'["“”‘’]|(?<![A-Za-z])\'|\'(?![A-Za-z])', x))
    step(f'引号不停顿（A17）：{qn} 句带引号，配音时都不读引号', not qbad, '\n    '.join(qbad))
    # 2–4 停顿与词尾
    c, o = run(['python3', f'{T}/标点停顿核对.py', no, '--自检']); step(o.strip().splitlines()[-1].lstrip('✔✘ ') if o.strip() else 'A19 自检没有输出', c == 0, '' if c == 0 else '【核查程序失灵，下面的停顿核对不可信】\n    ' + o[-400:])
    c, o = run(['python3', f'{T}/标点停顿核对.py', no]); step('标点停顿核对（A9/A10：停顿时长、不切词；A19：停顿后不留吸气声）', '问题数 0' in o, '' if '问题数 0' in o else '\n    '.join(l for l in o.splitlines() if 'BAD' in l or 'FAIL' in l))
    c, o = run(['python3', f'{T}/句首句尾与停顿位置核对.py', no]); step('句首句尾核对（修剪掉的只有听不见的部分）', '问题数 0' in o, '' if '问题数 0' in o else '\n    '.join(l for l in o.splitlines() if 'BAD' in l))
    c, o = run(['python3', f'{T}/停顿位置精确核对.py', no]); step('停顿位置核对（A9/A15：停顿正好落在标点处两个词之间）', '问题数 0' in o, '\n    '.join(l for l in o.splitlines() if 'BAD' in l or '插入' in l))
    c, o = run(['python3', f'{T}/无标点停顿核对.py', no])
    long = [l for l in o.splitlines() if re.search(r'停顿 (\d+\.\d+)s', l) and float(re.search(r'停顿 (\d+\.\d+)s', l).group(1)) > 0.22]
    step('无标点处停顿 ≤ 0.22 秒', not long, '\n    '.join(long))
elif stage == '出片后':
    c, o = run(['python3', f'{T}/audio_qc.py', f'{no}.mp4'])
    # 标出的"响度骤降"要剪成试听交用户确认。确认过、并用实际声音核实的，写进 核对确认.响度骤降：
    # {"108.7–109.3s": {"配音指纹": a.wav 的 md5 前 12 位, "低": 6.0（确认时 audio_qc 报的 dB）, "句子": …, "依据": …, "用户原话": …}}。
    # 放行条件：时段、配音指纹都对上，且这次报的 dB 不超过确认时 +0.3；配音一变（指纹不同）确认就作废。只认这一类：削波、电流音、停顿超长、
    # 程序出错（返回非 0 却没有输出）一律不能放行
    import hashlib
    fpa = hashlib.md5(open(f'work_{no}/a.wav', 'rb').read()).hexdigest()[:12]
    okq = json.load(open(f'scripts/{no}.json')).get('核对确认', {}).get('响度骤降', {})
    qlines = [l.strip() for l in o.splitlines() if l.strip()] if c else []
    def _qok(l):
        m = re.match(r'(\d+\.\d–\d+\.\ds) 响度比全片低 ([\d.]+) dB', l); cf = okq.get(m.group(1), {}) if m else {}
        return bool(m) and cf.get('配音指纹') == fpa and isinstance(cf.get('低'), (int, float)) and float(m.group(2)) <= cf['低'] + 0.3
    qconf = [l for l in qlines if _qok(l)]
    qrest = [l for l in qlines if l not in qconf]
    step('自动音频检查（削波、电流音、停顿超长、响度骤降）', c == 0 or (bool(qconf) and not qrest),
         (o.strip() if c == 0 else '\n    '.join(qrest + [f"{l}  → 已确认（配音指纹 {fpa}）：{okq[l.split(' ')[0]].get('句子', '')}" for l in qconf])
          + ('' if qlines else f'audio_qc 返回 {c} 却没有输出（程序出错）')) + ('\n    → 标出的位置必须剪成试听交用户确认' if c and not (qconf and not qrest) else ''))
    # 响度一致性（用户 2026-10-09：从头到尾响度一致，不能这儿突然大、那儿突然小）：EBU R128 逐句综合响度。先自检（阳性对照）再核对
    c, o = run(['python3', f'{T}/响度一致性核对.py', f'{no}.mp4', '--自检']); step(o.strip().lstrip('✔✘ ') or '响度一致性核对 自检', c == 0, '' if c == 0 else '【核查程序失灵，下面的响度结果不可信，不得交付】')
    c, o = run(['python3', f'{T}/响度一致性核对.py', f'{no}.mp4']); step('响度一致性（逐句与全片 ±2 LU、相邻两句 ≤2.5 LU）：' + o.strip().splitlines()[0], c == 0, '\n    '.join(o.strip().splitlines()[1:]))
    # 纯人声（用户 2026-10-09：“不要有任何的呼吸声 语气声……底噪也不要 就要绝对的纯人声”）：先自检（假呼吸声、假噗声必须抓到），再逐句核对
    c, o = run(['python3', f'{T}/纯人声核对.py', no, '--自检']); step(o.strip().splitlines()[-1].lstrip('✔✘ ') if o.strip() else '纯人声核对 自检没有输出', c == 0, '' if c == 0 else '【核查程序失灵，下面的纯人声核对不可信】\n    ' + o[-400:])
    c, o = run(['python3', f'{T}/纯人声核对.py', no]); step('纯人声核对（呼吸声、噗声、底噪、孤立杂音、起音前过长、收尾过长）：' + (o.strip().splitlines()[-1] if o.strip() else '没有输出'), c == 0 and '问题数 0' in o,
         '\n    '.join(l for l in o.splitlines() if ' BAD ' in l or 'OK（' in l))
    # A20：句号、段落、标题、片头片尾的停顿也按词到词量（停顿表）。先自检（加长、缩短、句首前放杂音，必须正好报出这三处），再核对
    c, o = run(['python3', f'{T}/句间停顿核对.py', no, '--自检']); step(o.strip().splitlines()[-1].lstrip('✔✘ ') if o.strip() else '句间停顿核对 自检没有输出', c == 0, '' if c == 0 else '【核查程序失灵，下面的句间停顿核对不可信】\n    ' + o[-400:])
    c, o = run(['python3', f'{T}/句间停顿核对.py', no]); step('句间停顿核对（A20：片头 0.4、标题后 1.0、句号 1.0、换段 1.2、片尾 2 秒，词到词 ±0.01 秒）：' + (o.strip().splitlines()[-1] if o.strip() else '没有输出'), c == 0 and '问题数 0' in o,
         '\n    '.join(l for l in o.splitlines() if ' BAD ' in l or '分段数' in l))
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
    cuts = re.findall(r'cut tail=([\d.]+)ms onset=([\d.]+)ms', o)
    extra = re.findall(r'extra non-zero runs not explained by raw copies: (\d+)', o)
    edge = re.findall(r'A10 edge violations [^:]*: (\d+)', o); viol = '\n    '.join(l.strip() for l in o.splitlines() if 'A10_VIOLATION' in l)
    # 删掉的部分偏响（只有 lost 一项、两侧都干净）的，必须用实际声音确认是停顿中间的换气声/底噪，写进 核对确认.删除段（键带位置）；
    # 两侧没衰减完（pre/post）、词尾/词头被切的，一律不能放行（A10、A18）——只有一种例外（用户 2026-10-09“就要绝对的纯人声”）：
    # 呼吸声/噗声与词尾或词头之间没有 -55 dB 低谷，只能紧贴着词切掉（切在过零点、词本身不动）。这一处必须用实际声音核实，写进
    # 核对确认.删除段：{"S17 raw a-b": {"类型": "紧贴词尾的非人声" / "紧贴词头的非人声" / "紧贴两头的非人声", "配音指纹": a.wav 的 md5 前 12 位, "依据": …}}。
    # 紧贴词尾只放行 词尾被切(tail) 与 pre/lost；紧贴词头只放行 词头被切(onset) 与 post/lost；紧贴两头放行两边；配音一变（指纹不同）确认作废
    import hashlib
    fpd = hashlib.md5(open(f'work_{no}/a.wav', 'rb').read()).hexdigest()[:12]
    okd = json.load(open(f'scripts/{no}.json')).get('核对确认', {}).get('删除段', {}); idx = None; last = None; unconf = 0; bad = []; pend = None
    def _typ(key):
        v = okd.get(key)
        return v.get('类型') if isinstance(v, dict) and v.get('配音指纹') == fpd else None
    for l in o.splitlines():
        m = re.match(r'\[\s*(-?\d+)\]', l)
        if m: idx = int(m.group(1))
        m = re.search(r'cut tail=([\d.]+)ms onset=([\d.]+)ms', l)
        if m: pend = (float(m.group(1)), float(m.group(2)))
        m = re.search(r'edit raw ([\d.]+)-([\d.]+)', l)
        if m:
            last = f"{'标题' if idx == -1 else 'S%d' % (idx + 1)} raw {m.group(1)}-{m.group(2)}"; t = _typ(last)
            if pend and (pend[0] > 0 or pend[1] > 0):
                if (pend[0] > 0 and t not in ('紧贴词尾的非人声', '紧贴两头的非人声')) or (pend[1] > 0 and t not in ('紧贴词头的非人声', '紧贴两头的非人声')): bad.append((last, pend))
                else: viol += f"\n    {last}：{t}（词尾/词头被切 {pend[0]:.0f}/{pend[1]:.0f} ms 是切掉的呼吸声/噗声），已用实际声音确认——{okd[last]['依据']}"
            pend = None
        m = re.search(r'A10_VIOLATION\(([a-z,]*)\)', l)
        if m:
            sides = set(m.group(1).split(',')); t = _typ(last)
            allow = {'lost'} if (last in okd and not isinstance(okd[last], dict)) else {'pre', 'lost'} if t == '紧贴词尾的非人声' else {'post', 'lost'} if t == '紧贴词头的非人声' else {'pre', 'post', 'lost'} if t == '紧贴两头的非人声' else set()
            if not sides <= allow: unconf += 1
            elif sides == {'lost'} and not isinstance(okd.get(last), dict): viol += f"\n    {last}：已用实际声音确认——{okd[last]}"
    good = c == 0 and not bad and extra == ['0'] and unconf == 0
    step(f'独立复核：{len(cuts)} 处改动，词尾/词头被切 = {len(bad)}，删除处两侧未衰减到 -55 dB 或删掉了 -40 dB 以上的声音 = {edge}（未经实际声音确认的 {unconf}），多余声音 = {extra}', good, viol if good else (viol + '\n    ' + o[-800:]))
    # 高亮同步（L14：读到哪一块，哪一块高亮）。先做核查程序自检（阳性对照）：在时间表副本里故意把两处切换挪动 0.4 秒
    # （标点后的块提前、无标点处的块推后，各一处），高亮同步核对必须正好在这两处报出、其余不变；自检不过 = 核查失灵
    ent = re.findall(r"file '([^']+)'\nduration ([\d.]+)", open(f'work_{no}/list.txt').read())
    dj = json.load(open(f'scripts/{no}.json')); nch = sum(len(s['chunks']) for s in dj['sentences']); base = len(ent) - nch
    cand = []; ix = base
    for si, s in enumerate(dj['sentences'], 1):
        if len(s['chunks']) > 1: cand.append((si, ix, bool(re.search(r'[,;:]$', re.sub(r'\*\*|\{\{.*?\}\}', '', s['chunks'][0]['en']).strip()))))
        ix += len(s['chunks'])
    pP = next((c for c in cand if c[2]), cand[0]); pN = next((c for c in cand if not c[2] and c[0] != pP[0]), cand[-1])
    du = [float(x) for _, x in ent]
    du[pP[1]] -= 0.4; du[pP[1] + 1] += 0.4; du[pN[1]] += 0.4; du[pN[1] + 1] -= 0.4
    bad_list = f'work_{no}/list_自检.txt'
    open(bad_list, 'w').write(''.join(f"file '{f}'\nduration {x:.3f}\n" for (f, _), x in zip(ent, du)) + f"file '{ent[-1][0]}'\n")
    c, o = run(['python3', f'{T}/高亮同步核对.py', no], {'HL_LIST': bad_list, 'HL_ONLY': f'{pP[0]},{pN[0]}'})
    got = set(re.findall(rf'^{no} (S\d+) BAD (第\d+块)', o, re.M)); want = {(f'S{pP[0]}', '第2块'), (f'S{pN[0]}', '第2块')}
    step(f'高亮同步核对 自检：S{pP[0]} 第2块故意提前 0.4 秒、S{pN[0]} 第2块故意推后 0.4 秒，必须正好报出这两处', got == want,
         f'报出：{sorted(got)}' + ('' if got == want else '\n    ' + o[-600:]))
    c, o = run(['python3', f'{T}/高亮同步核对.py', no])
    step('高亮同步核对（L14：每一块的高亮在这一块开始读时切换，误差 ≤ 0.15 秒；两种独立办法都要满足，不一致处须用实际声音核实）',
         c == 0 and '问题数 0' in o, '\n    '.join(l for l in o.splitlines() if 'BAD' in l or '核实' in l or '共核对' in l))
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
