"""两个成片逐采样、逐屏比对（2026-10-17：证明 GitHub 机器出的片与本地存档一致）。
用法：python3 对比成片.py 新.mp4 存档.mp4    声音：解码后逐采样比（必须完全相同）；画面：每 0.5 秒取一帧，逐像素最大差（编码噪声以内才算一致）"""
import sys, subprocess, hashlib, numpy as np, imageio_ffmpeg
F = imageio_ffmpeg.get_ffmpeg_exe(); a, b = sys.argv[1:3]
def pcm(f): return subprocess.run([F,'-v','quiet','-i',f,'-map','0:a','-f','s16le','-'],capture_output=True).stdout
def frames(f):
    r = subprocess.run([F,'-v','quiet','-i',f,'-vf','fps=2,scale=960:540','-f','rawvideo','-pix_fmt','gray','-'],capture_output=True).stdout
    return np.frombuffer(r,np.uint8).reshape(-1,540,960)
pa, pb = pcm(a), pcm(b); ok_a = pa == pb
fa, fb = frames(a), frames(b); n = min(len(fa), len(fb))
d = np.abs(fa[:n].astype(int) - fb[:n].astype(int)).reshape(n,-1); mx = d.max(1); bad = int((mx > 24).sum())
print(f'声音：{"✔ 逐采样相同" if ok_a else "✘ 不同"}（{hashlib.md5(pa).hexdigest()[:12]} / {hashlib.md5(pb).hexdigest()[:12]}）')
print(f'画面：{n} 帧（两边 {len(fa)}/{len(fb)}），每帧最大差中位 {int(np.median(mx))}、最大 {int(mx.max())}，差超过 24 的 {bad} 帧')
ok = ok_a and len(fa) == len(fb) and bad == 0
print('结论：✔ 一致' if ok else '结论：✘ 不一致'); sys.exit(0 if ok else 1)
