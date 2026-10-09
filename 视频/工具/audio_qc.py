"""音频交付前自动检查（对应踩坑总表 A1–A8 中能用程序查的部分）：python3 audio_qc.py NN.mp4
人耳试听仍是必须步骤，本程序只防"已知的坑"再犯。"""
import sys, subprocess, numpy as np, soundfile as sf, imageio_ffmpeg, tempfile, os
FF = imageio_ffmpeg.get_ffmpeg_exe()
src = sys.argv[1]; tmp = tempfile.mktemp(suffix='.wav')
subprocess.run([FF, '-v', 'error', '-y', '-i', src, '-vn', '-ac', '1', '-ar', '48000', tmp], check=True)
a, sr = sf.read(tmp); os.remove(tmp); bad = []
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
print('\n'.join(bad) if bad else f'{os.path.basename(src)}：音频自动检查通过（仍需人耳逐句试听）')
sys.exit(1 if bad else 0)
