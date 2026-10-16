"""从成片按句子抽屏、拼成一张图，截图核对只看要看的那几屏（13 改稿手工做了两次后写成程序）。
用法（在视频工作目录下）：python3 抽屏.py NN.mp4 句号… 输出.png   例：python3 $T/抽屏.py 15.mp4 7 8 10 18 /tmp/x.png
做法：每 0.5 秒抽一帧；文字轮廓（含变暗的字）大变 = 换了一句；每句取最后一帧（全句都已出现）；第 0 屏是标题。"""
import sys, os, glob, subprocess, tempfile, numpy as np, imageio_ffmpeg
from PIL import Image
mp4, *ss, out = sys.argv[1:]; ss = [int(x) for x in ss]
d = tempfile.mkdtemp(); subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), '-v', 'quiet', '-i', mp4, '-vf', 'fps=2,scale=960:540', f'{d}/%05d.png'], check=True)
fs = sorted(glob.glob(f'{d}/*.png')); grp = []; prev = None
for f in fs:
    g = np.asarray(Image.open(f).convert('L').resize((480, 270)), dtype=np.int16)[:250]
    m = g > 30
    if prev is None or (m ^ prev).mean() > 0.04: grp.append([])
    grp[-1].append(f); prev = m
print(f'{len(grp) - 1} 句（第 0 屏是标题）')
sel = [grp[i][-1] for i in ss if i < len(grp)]
cols = 2 if len(sel) > 1 else 1; rows = (len(sel) + cols - 1) // cols
T = Image.new('RGB', (960 * cols, 540 * rows))
for j, f in enumerate(sel): T.paste(Image.open(f).convert('RGB'), ((j % cols) * 960, (j // cols) * 540))
T.save(out); print('已存', out)
