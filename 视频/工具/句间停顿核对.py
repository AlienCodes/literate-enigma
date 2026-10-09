#!/usr/bin/env python3
"""句间停顿核对（A20：句号、段落、标题、片头片尾的停顿也按“词到词”量）。
在视频工作目录下运行：python3 <工具目录>/句间停顿核对.py NN [--自检]
读 work_NN/a.wav（不经出片程序，独立量）：按 ≥0.6 秒的数字静音分出标题和每一句；每一段用自己的 5 ms 帧（从这一段第一个非零采样起分帧），
电平相对本段最响的 5 ms 帧；“能听见” = 不低于 -55 dB（A13：一律以 -55 dB 为准）。
量：片头（文件开头 → 标题第一个能听见的帧）、标题 → 第一句、句 → 句、片尾（最后一句最后一个能听见的帧 → 文件结尾），
与停顿表比：片头 0.4 秒；标题读完 0.6 + 0.4 = 1.0 秒；句号 1.0 秒；换段 1.2 秒；片尾 2 秒。误差超过 ±0.01 秒即报。
标准值按停顿表写在这里，不从出片程序里读（不自己检查自己）。
自检（阳性对照）：在副本里把第 1/3 处句间停顿加长 0.05 秒、第 2/3 处缩短 0.05 秒，并在另一句开头前 90–60 ms 放一个 30 ms、-45 dB 的杂音，
必须正好报出这三处，其余不报；自检不过 = 核查失灵。"""
import sys, json, numpy as np, soundfile as sf
SR = 24000; F = 120; AUD = -55.0; TOL = 0.01
P_START, P_TITLE, P_SENT, P_PARA, P_END = 0.4, 1.0, 1.0, 1.2, 2.0


def segments(a):
    z = np.append((a == 0).astype(np.int8), 0); runs = []; st = None
    for i, v in enumerate(z):
        if v and st is None: st = i
        if not v and st is not None:
            if (i - st) / SR >= 0.6: runs.append((st, i))
            st = None
    b = [0] + [r[1] for r in runs]; e = [r[0] for r in runs] + [len(a)]
    out = []
    for x, y in zip(b, e):
        if y - x <= 0 or not np.any(a[x:y] != 0): continue
        nz = np.nonzero(a[x:y])[0]; out.append((x + int(nz[0]), x + int(nz[-1]) + 1))
    return out


def audible(a, x, y):
    s = a[x:y]; m = (len(s) + F - 1) // F; s = np.pad(s, (0, m * F - len(s)))
    r = np.sqrt(np.mean(s.reshape(m, F) ** 2, axis=1)); db = 20 * np.log10(r / (r.max() + 1e-12) + 1e-9)
    idx = np.where(db >= AUD)[0]
    return x + int(idx[0]) * F, min(y, x + int(idx[-1] + 1) * F)


def check(a, d):
    segs = segments(a); n = len(d['sentences'])
    if len(segs) != n + 1: return None, [f'分段数 {len(segs)} ≠ 标题 + {n} 句（有句子内部的停顿 ≥0.6 秒，或句间停顿不到 0.6 秒）']
    au = [audible(a, x, y) for x, y in segs]
    want = [('片头（文件开头→标题）', P_START, au[0][0] / SR)]
    want.append(('标题→S1', P_TITLE, (au[1][0] - au[0][1]) / SR))
    for k in range(1, n):
        para = d['sentences'][k]['para'] != d['sentences'][k - 1]['para']
        want.append((f'S{k}→S{k + 1}{"（换段）" if para else ""}', P_PARA if para else P_SENT, (au[k + 1][0] - au[k][1]) / SR))
    want.append((f'片尾（S{n}→文件结尾）', P_END, (len(a) - au[-1][1]) / SR))
    rows = []; bad = []
    for name, std, got in want:
        ok = abs(got - std) <= TOL
        rows.append(f"{'OK ' if ok else 'BAD'} {name} 标准 {std:.2f}s 词到词实际 {got:.3f}s（差 {got - std:+.3f}）")
        if not ok: bad.append(name)
    return bad, rows


if __name__ == '__main__':
    no = sys.argv[1]; a, sr = sf.read(f'work_{no}/a.wav'); assert sr == SR; a = np.asarray(a, float)
    d = json.load(open(f'scripts/{no}.json'))
    if '--自检' in sys.argv:
        bad0, _ = check(a, d)
        if bad0 is None or bad0: print(f'✘ 句间停顿核对 自检：原样已有报警，自检前提不成立 {bad0}'); sys.exit(1)
        segs = segments(a); n = len(d['sentences']); k1, k2 = max(1, n // 3), max(2, 2 * n // 3)
        k3 = next(k for k in [n // 2] + list(range(1, n + 1)) if k - 1 not in (k1, k2) and k not in (k1, k2))
        b = a.copy()
        # 第 k3 句开头前 90–60 ms 放杂音（与加长、缩短的两处不是同一处静音）
        i3 = segs[k3][0] - int(0.09 * SR); nb = int(0.03 * SR); rng = np.random.default_rng(3)
        x = segs[k3]; s = a[x[0]:x[1]]; m = len(s) // F; ref = np.sqrt(np.mean(s[:m * F].reshape(m, F) ** 2, axis=1)).max()
        nz = rng.standard_normal(nb) * np.hanning(nb); nz *= ref * 10 ** (-45 / 20) / np.sqrt(np.mean(nz ** 2)); b[i3:i3 + nb] = nz
        def mid(k): return (segs[k][1] + segs[k + 1][0]) // 2      # 第 k 段与第 k+1 段之间静音的中点
        cut0 = mid(k2); add0 = mid(k1); g = int(0.05 * SR)
        parts = [b[:add0], np.zeros(g), b[add0:cut0], b[cut0 + g:]] if add0 < cut0 else [b[:cut0], b[cut0 + g:add0], np.zeros(g), b[add0:]]
        b = np.concatenate(parts)
        bad1, rows = check(b, d)
        want = sorted([f'S{k1}→S{k1 + 1}', f'S{k2}→S{k2 + 1}', f'S{k3 - 1}→S{k3}' if k3 > 1 else '标题→S1'])
        got = sorted(x.replace('（换段）', '') for x in (bad1 or []))
        ok = got == want
        print(f"{'✔' if ok else '✘'} 句间停顿核对 自检：S{k1} 后加长 0.05 秒、S{k2} 后缩短 0.05 秒、S{k3} 开头前放杂音，必须报 {want}，报出 {got}")
        sys.exit(0 if ok else 1)
    bad, rows = check(a, d)
    print('\n'.join(f'{no} {r}' for r in rows))
    print(f'{no} 句间停顿核对 问题数', len(bad) if bad is not None else 1)
    sys.exit(0 if bad == [] else 1)
