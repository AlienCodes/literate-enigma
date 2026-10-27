#!/usr/bin/env python3
"""响度一致性核对（用户 2026-10-09：音频从头到尾响度必须一致，不能这儿突然大、那儿突然小——所有视频的标准）。

用法：python3 响度一致性核对.py 成片.mp4 [--自检]
做法：用 ffmpeg 自带的 EBU R128 响度计（ebur128，K 加权，400 ms 块、每 100 ms 一块）取全片每一块的瞬时响度；
按 ≥0.7 秒的静音把成片切成一句一句（逗号停顿 0.4 秒不切，句号 1.0、段落 1.2 秒会切），每句按 ITU-R BS.1770
的门限（绝对 -70 LUFS、相对 -10 LU）算这一句的综合响度，与全片综合响度比较。
标准：每一句与全片相差不超过 ±2 LU；相邻两句相差不超过 2.5 LU。片头（前 SKIP 秒）不算。
自检（阳性对照）：把中间一句调到比全片响 3 LU、另一句调到比全片轻 3 LU（按这一句原来的响度算增益），必须正好报出这两句，其余不报；自检不过 = 核查失灵。
"""
import sys, re, subprocess, tempfile, os, numpy as np
try:
    import imageio_ffmpeg; FF = imageio_ffmpeg.get_ffmpeg_exe()
except Exception: FF = 'ffmpeg'
SR = 48000; SKIP = 9.0; GAP = 0.7; DEV = 2.0; ADJ = 2.5

def pcm(src):
    r = subprocess.run([FF, '-loglevel', 'error', '-i', src, '-vn', '-ac', '1', '-ar', str(SR), '-f', 's16le', '-'], capture_output=True, check=True)
    return np.frombuffer(r.stdout, np.int16).astype(np.float64) / 32768

def momentary(src):
    """每 100 ms 一个 400 ms 块的瞬时响度 (t_end, M)。"""
    r = subprocess.run([FF, '-nostats', '-v', 'verbose', '-i', src, '-vn', '-af', 'ebur128=framelog=verbose', '-f', 'null', '-'], capture_output=True, text=True)
    out = [(float(t), float(m)) for t, m in re.findall(r't:\s*([\d.]+)\s+TARGET:\S+ LUFS\s+M:\s*(-?[\d.]+|-inf)', r.stderr.replace('-inf', '-200'))]
    if not out: raise SystemExit('【停止】ebur128 没有输出瞬时响度，核查无法进行')
    return np.array(out)

def gated(M):
    M = M[M > -70]
    if not len(M): return None
    e = 10 ** ((M + 0.691) / 10); rel = -0.691 + 10 * np.log10(e.mean()) - 10
    M = M[M > rel]; e = 10 ** ((M + 0.691) / 10)
    return -0.691 + 10 * np.log10(e.mean())

def sentences(a):
    n = int(0.01 * SR); m = len(a) // n
    e = 10 * np.log10(np.mean(a[:m * n].reshape(m, n) ** 2, axis=1) + 1e-20); quiet = e < e.max() - 50
    segs = []; st = None; q = 0; last = 0
    for i, v in enumerate(quiet):
        if not v:
            if st is None: st = i
            q = 0; last = i
        else:
            q += 1
            if st is not None and q >= GAP / 0.01: segs.append((st * 0.01, (last + 1) * 0.01)); st = None
    if st is not None: segs.append((st * 0.01, (last + 1) * 0.01))
    return [(x, y) for x, y in segs if x >= SKIP and y - x >= 0.5]

def check(src, a=None):
    a = pcm(src) if a is None else a
    TM = momentary(src); segs = sentences(a)
    I = gated(TM[TM[:, 0] >= SKIP + 0.4, 1])
    L = []
    for x, y in segs:
        blk = TM[(TM[:, 0] >= x + 0.4 - 1e-6) & (TM[:, 0] <= y + 0.05), 1]
        L.append(gated(blk) if len(blk) else None)
    bad = []
    for k, ((x, y), v) in enumerate(zip(segs, L), 1):
        if v is None: continue
        if abs(v - I) > DEV: bad.append((k, f'第{k}段 {x:.1f}–{y:.1f}s 比全片{"响" if v > I else "轻"} {abs(v - I):.1f} LU（标准 ±{DEV}）'))
        if k > 1 and L[k - 2] is not None and abs(v - L[k - 2]) > ADJ: bad.append((k, f'第{k - 1}→{k}段（{x:.1f}s）相邻两句相差 {abs(v - L[k - 2]):.1f} LU（标准 ≤{ADJ}）'))
    pk = 20 * np.log10(np.abs(a).max() + 1e-12)
    dev = [v - I for v in L if v is not None]
    summ = f'全片 {I:.1f} LUFS，峰值 {pk:.1f} dBFS，{len(segs)} 句，逐句与全片差 {min(dev):+.1f}～{max(dev):+.1f} LU'
    return I, segs, L, bad, summ

# 句内分段响度（2026-10-25 用户看 25 S2：“这块这个声音在这一块声响是不是变小了？是不是没有统计起来？”）：
# 整句在 ±2 LU 内，句内逗号停顿前后两段却差 3～5 LU，听起来突然变小。按句内 ≥IN_GAP 秒的静音（逗号停顿 0.4 秒；列举逗号 0.2 秒不切）
# 把每句切成段，每段按 BS.1770 门限算响度（不足 0.4 秒的段取最贴近的一块），相邻两段差超过 IN_ADJ 就报。
IN_GAP = 0.3; IN_ADJ = 2.5   # 与“相邻两句 ≤2.5 LU”同一个标准；25 S2 用户听出变小的那处是 2.8
def 分段(a, segs):
    n = int(0.01 * SR); m = len(a) // n
    e = 10 * np.log10(np.mean(a[:m * n].reshape(m, n) ** 2, axis=1) + 1e-20); quiet = e < e.max() - 50
    out = []
    for x, y in segs:
        i0, i1 = int(round(x / 0.01)), int(round(y / 0.01)); cur = []; st = i0; q = 0
        for i in range(i0, i1):
            if quiet[i]: q += 1
            else:
                if q >= IN_GAP / 0.01 and i - q > st: cur.append((st * 0.01, (i - q) * 0.01)); st = i
                q = 0
        cur.append((st * 0.01, i1 * 0.01)); out.append(cur)
    return out
def 段响度(TM, x, y):
    blk = TM[(TM[:, 0] >= x + 0.4 - 1e-6) & (TM[:, 0] <= y + 0.05), 1]
    if not len(blk): blk = TM[[int(np.argmin(np.abs(TM[:, 0] - min(y + 0.05, x + 0.4))))], 1]
    return gated(blk)
def 句范围(a, seg_json=None):
    """[(句名, 起, 止)]：有出片程序的 work_NN/分段.json 就按它（S1 也查、句名对得上），没有就按 ≥0.7 秒静音切（片头前 SKIP 秒不算）。"""
    if seg_json and os.path.exists(seg_json):
        import json
        return [(k, v[0]['时刻'][0], v[-1]['时刻'][1]) for k, v in json.load(open(seg_json)).items()]
    return [(f'第{k}句', x, y) for k, (x, y) in enumerate(sentences(a), 1)]
def 句内(src, a=None, TM=None, seg_json=None):
    """返回 [(句名, 第几段→下一段, 前段时刻, 后段时刻, 差 LU)]，差 = 后段 - 前段；段按句内 ≥IN_GAP 秒的静音切（不看出片程序记的停顿）。"""
    a = pcm(src) if a is None else a
    TM = momentary(src) if TM is None else TM
    rg = 句范围(a, seg_json); rs = []
    for (nm, _, _), cur in zip(rg, 分段(a, [(x, y) for _, x, y in rg])):
        L = [段响度(TM, x, y) for x, y in cur]
        for j in range(1, len(cur)):
            if L[j] is None or L[j - 1] is None: continue
            rs.append((nm, j, cur[j - 1], cur[j], L[j] - L[j - 1]))
    return rs
def 句内报(rs): return [r for r in rs if abs(r[4]) > IN_ADJ]
def 句内自检(src, seg_json=None):
    """阳性对照：挑一句相邻段都不超标的，把它的第 2 段调到与前一段差 IN_ADJ+1 LU，必须报出这一处；原样的报出不变（不误报）。
    原样和改过的都先写成同样的 wav 再量（原来原样按成片 AAC 量、改过的按 wav 量，瞬时响度差一点，20 改号 25 的 S7 在门槛边上翻过去、多报，G79 原样自检揭出）"""
    a = pcm(src)
    with tempfile.TemporaryDirectory() as td:
        def 量(x, n):
            w = os.path.join(td, n)
            subprocess.run([FF, '-loglevel', 'error', '-f', 's16le', '-ar', str(SR), '-ac', '1', '-i', '-', w], input=(np.clip(x, -1, 1) * 32767).astype(np.int16).tobytes(), check=True)
            return 句内(w, x, None, seg_json)
        rs = 量(a, 'o.wav'); bad0 = {(r[0], r[1]) for r in 句内报(rs)}
        cand = [r for r in rs if r[1] == 1 and not any(q[0] == r[0] for q in 句内报(rs))]
        if not cand: return False, '自检前提不成立：没有一句相邻段都不超标、又有两段以上的'
        nm, j, (px, py), (x, y), dv = cand[len(cand) // 2]
        g = -(IN_ADJ + 1.0) - dv; b = a.copy(); b[int(x * SR):int(y * SR)] *= 10 ** (g / 20)
        bad1 = {(r[0], r[1]) for r in 句内报(量(b, 't.wav'))}
    ok = (nm, 1) in bad1 and bad1 - bad0 <= {(nm, 1), (nm, 2)}
    return ok, f'故意把 {nm} 第 2 段（{x:.1f}–{y:.1f}s）调 {g:+.1f} dB，{"报出" if (nm, 1) in bad1 else "没报出"}；多报 {sorted(bad1 - bad0 - {(nm, 1), (nm, 2)})}'

# G40（主对话 2026-10-25：25 第一稿 cartridges 偏轻 8.5 dB，AI 写了一条 响度骤降 确认放过去）：音频门上的确认只认实测数据。
# 25 起，响度骤降 确认只收不超过 01–24 用户听过认可的最深一处（20 的 7.1 dB）；更深的必须修（重合成、分段增益），确认不放行
骤降确认上限 = 7.1
def 骤降确认可收(no, 低):
    return not (str(no).isdigit() and int(no) >= 25 and float(低) > 骤降确认上限)
def 确认自检():
    f = []
    if 骤降确认可收('25', 8.5): f.append('没抓到：25 偏轻 8.5 dB 写了响度骤降确认，照样收了（G40 重放 25 cartridges）')
    if not 骤降确认可收('25', 6.1): f.append('误报：25 偏轻 6.1 dB（在 01–24 认可范围内）的确认也不收')
    if not 骤降确认可收('20', 8.5): f.append('误报：24 以前的不回头查')
    return f

def selftest(src):
    a = pcm(src); I, segs, L, bad, _ = check(src, a)
    if bad or len(segs) < 6: return False, f'自检前提不成立：原片已有报警或句数太少（{len(segs)}）'
    i1, i2 = len(segs) // 3, 2 * len(segs) // 3
    # 按这一句原来的响度算增益：把第 i1 句推到比全片响 3 LU、第 i2 句推到比全片轻 3 LU（2026-10-10 04：固定 ±3 dB 时，
    # 第 11 句原本比全片响 1.1 LU，调轻 3 dB 后只差 1.9 LU、没超过 ±2，自检误判“失灵”——阳性对照必须保证造出来的坑真的越线）
    if L[i1] is None or L[i2] is None: return False, '自检前提不成立：选中的句子没有响度'
    b = a.copy()
    for (x, y), g in ((segs[i1], I + 3.0 - L[i1]), (segs[i2], I - 3.0 - L[i2])):
        b[int(x * SR):int(y * SR)] *= 10 ** (g / 20)
    b = np.clip(b, -1, 1)
    with tempfile.TemporaryDirectory() as td:
        w = os.path.join(td, 't.wav')
        subprocess.run([FF, '-loglevel', 'error', '-f', 's16le', '-ar', str(SR), '-ac', '1', '-i', '-', w], input=(b * 32767).astype(np.int16).tobytes(), check=True)
        _, _, _, bad2, _ = check(w, b)
    got = sorted({k for k, _ in bad2 if '比全片' in _})
    want = [i1 + 1, i2 + 1]
    return got == want, f'故意把第{want[0]}段调到比全片响 3 LU、第{want[1]}段调到比全片轻 3 LU，报出 {got}'

if __name__ == '__main__':
    src = sys.argv[1]
    if src == '--确认自检':
        e = 确认自检(); print('\n'.join(e) or f'响度骤降确认 自检通过（25 起超过 {骤降确认上限} dB 的确认不收；范围内、24 以前照收）'); sys.exit(1 if e else 0)
    sj = sys.argv[sys.argv.index('--分段') + 1] if '--分段' in sys.argv else None
    if '--句内清单' in sys.argv:   # 01–24 已定稿的不回头改（G36 25 起），列给用户看：python3 响度一致性核对.py 视频目录 --句内清单 > 制作记录/句内响度清单.md
        import glob
        print('# 句内分段响度清单（01–24 已定稿，G36 25 起才查，这里只列不改）\n')
        print(f'用户 2026-10-25 看 25 S2：“这块这个声音在这一块声响是不是变小了？是不是没有统计起来？你帮我认真核查一下。”')
        print(f'量法与交付核查的门相同：句内 ≥{IN_GAP} 秒静音切段，相邻两段差超过 {IN_ADJ} LU 列出（句号按片头 {SKIP} 秒后数起，第1句可能是 S2；时刻是成片里的秒）。由 `python3 工具/响度一致性核对.py 视频/视频 --句内清单` 生成。\n')
        tot = 0
        for f in sorted(glob.glob(os.path.join(src, '[0-2][0-9].mp4'))):
            nn = os.path.basename(f)[:2]
            if int(nn) >= 25: continue
            bad = 句内报(句内(f)); tot += len(bad)
            print(f'- **{nn}**：{len(bad)} 处' + ''.join(f'\n  - {nm} 第{j}→{j + 1}段 {px:.1f}–{py:.1f}s → {x:.1f}–{y:.1f}s 后段{"响" if dv > 0 else "轻"} {abs(dv):.1f} LU' for nm, j, (px, py), (x, y), dv in bad))
        print(f'\n共 {tot} 处。要改哪篇，用户说了再改（改了就要重出 4K、过交付核查、重新归档，G9）。'); sys.exit(0)
    if '--句内' in sys.argv:
        if '--自检' in sys.argv:
            ok, msg = 句内自检(src, sj); print(('✔ ' if ok else '✘ ') + '句内分段响度 自检：' + msg); sys.exit(0 if ok else 1)
        rs = 句内(src, seg_json=sj); bad = 句内报(rs)
        print(f'句内相邻两段 {len(rs)} 处，差超过 {IN_ADJ} LU 的 {len(bad)} 处')
        for nm, j, (px, py), (x, y), dv in bad: print(f'  {nm} 第{j}→{j + 1}段（{px:.1f}–{py:.1f}s → {x:.1f}–{y:.1f}s）后段{"响" if dv > 0 else "轻"} {abs(dv):.1f} LU（标准 ≤{IN_ADJ}）')
        sys.exit(1 if bad else 0)
    if '--自检' in sys.argv:
        ok, msg = selftest(src); print(('✔ ' if ok else '✘ ') + '响度一致性核对 自检：' + msg); sys.exit(0 if ok else 1)
    I, segs, L, bad, summ = check(src)
    print(summ)
    for _, m in bad: print('  ' + m)
    sys.exit(1 if bad else 0)
