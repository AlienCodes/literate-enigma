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
    if '--自检' in sys.argv:
        ok, msg = selftest(src); print(('✔ ' if ok else '✘ ') + '响度一致性核对 自检：' + msg); sys.exit(0 if ok else 1)
    I, segs, L, bad, summ = check(src)
    print(summ)
    for _, m in bad: print('  ' + m)
    sys.exit(1 if bad else 0)
