"""音频交付前自动检查（对应踩坑总表 A1–A8 中能用程序查的部分）：python3 audio_qc.py NN.mp4
人耳试听仍是必须步骤，本程序只防"已知的坑"再犯。"""
import sys, subprocess, numpy as np, soundfile as sf, imageio_ffmpeg, tempfile, os, warnings
warnings.filterwarnings('ignore')   # 造错时的空段均值警告不许混进结论行（交付核查取最后一行当步骤名）
FF = imageio_ffmpeg.get_ffmpeg_exe()
src = [x for x in sys.argv[1:] if not x.startswith('--')][0]; tmp = tempfile.mktemp(suffix='.wav')
subprocess.run([FF, '-v', 'error', '-y', '-i', src, '-vn', '-ac', '1', '-ar', '48000', tmp], check=True)
a, sr = sf.read(tmp); os.remove(tmp)


def 查(a, sr):
    bad = []
    # A：削波
    if np.abs(a).max() > 0.99: bad.append(f'削波：峰值 {np.abs(a).max():.3f}')
    # A1/A2：4800 / 9600 Hz 电流音（与两侧频带比较）
    n = 1 << 15; f = np.fft.rfftfreq(n, 1 / sr); spec = np.zeros(len(f))
    for i in range(0, len(a) - n, n): spec += np.abs(np.fft.rfft(a[i:i + n] * np.hanning(n))) ** 2
    for hz in (4800, 9600):
        pk = spec[(f > hz - 15) & (f < hz + 15)].max(); side = np.median(spec[(f > hz - 300) & (f < hz + 300)])
        if 10 * np.log10(pk / side) > 12: bad.append(f'{hz} Hz 电流音突出 {10*np.log10(pk/side):.1f} dB')
    # 停顿：找所有静音段，最长不应超过片尾 2 秒，片中不应有 >1.6 秒的停顿（段间标准 1.2 秒）。这里的 -45 dB 只用来粗找“静音段”报超长停顿、分句量响度，
    # 不是“可闻线”：判断听不听得见、切哪里一律以 -55 dB 为准（A13）；停顿是否合标准由 标点停顿核对、句间停顿核对 按词到词量
    h = int(0.01 * sr); rms = np.array([np.sqrt(np.mean(a[i:i + h] ** 2)) for i in range(0, len(a) - h, h)])
    q = 20 * np.log10(rms / (rms.max() + 1e-9) + 1e-9) < -45; runs = []; st = None
    for i, v in enumerate(q):
        if v and st is None: st = i
        if not v and st is not None: runs.append((st / 100, (i - st) / 100)); st = None
    mid = [r for r in runs if 1.0 < r[0] < len(a) / sr - 3]
    long = [r for r in mid if r[1] > 1.6]
    if long: bad.append('片中停顿过长：' + ', '.join(f'{t:.1f}s 处 {d:.2f}s' for t, d in long))
    # 句与句之间的响度突变（发闷/突然变小的常见表现）：每段语音的 RMS 与全片中位数比
    segs = []; prev = 0
    for t, d in runs:
        if t - prev > 0.4: segs.append((prev, t))
        prev = t + d
    lv = [20 * np.log10(np.sqrt(np.mean(a[int(x * sr):int(y * sr)] ** 2)) + 1e-9) for x, y in segs]
    med = np.median(lv)
    for (x, y), v in zip(segs, lv):
        if v < med - 6: bad.append(f'{x:.1f}–{y:.1f}s 响度比全片低 {med-v:.1f} dB（疑似发闷/变小，需试听）')
    return bad


if '--自检' in sys.argv:
    # 阳性对照：原样不报；削波、4800 Hz 电流音、片中 2 秒停顿、一段突然变轻 10 dB，各造一处，每一种都必须报出
    fails = []; base = 查(a, sr)   # 原片已有、并已在 核对确认 里核实过的报警（如响度骤降）不算；每造一处，这一类报警必须多出一条
    n = lambda xs, kw: sum(kw in x for x in xs)
    mid = len(a) // 2; L5 = int(5 * sr)
    b = a.copy(); b[mid] = 1.0
    if n(查(b, sr), '削波') <= n(base, '削波'): fails.append('没抓到：削波（A2）')
    b = a + 10 ** (-40 / 20) * np.abs(a).max() * np.sin(2 * np.pi * 4800 * np.arange(len(a)) / sr)
    if n(查(b, sr), '4800') <= n(base, '4800'): fails.append('没抓到：4800 Hz 电流音（A2）')
    b = np.concatenate([a[:mid], np.zeros(int(2 * sr)), a[mid:]])
    if n(查(b, sr), '停顿过长') <= n(base, '停顿过长'): fails.append('没抓到：片中停顿过长')
    b = a.copy(); b[mid - L5:mid + L5] *= 10 ** (-10 / 20)
    if n(查(b, sr), '响度比全片低') <= n(base, '响度比全片低'): fails.append('没抓到：一段突然变轻（A8 发闷）')
    print(('✔ audio_qc 自检：削波、4800 Hz 电流音、片中停顿过长、一段变轻全部报出' if not fails else '✘ audio_qc 自检失灵：' + '；'.join(fails)))
    sys.exit(1 if fails else 0)
bad = 查(a, sr)
print('\n'.join(bad) if bad else f'{os.path.basename(src)}：音频自动检查通过（仍需人耳逐句试听）')
sys.exit(1 if bad else 0)
