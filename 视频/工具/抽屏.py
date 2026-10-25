"""从成片按句子抽屏、拼成一张图，截图核对只看要看的那几屏（13 改稿手工做了两次后写成程序）。
用法（在视频工作目录下）：python3 抽屏.py NN.mp4 句号… 输出.png   例：python3 $T/抽屏.py 15.mp4 7 8 10 18 /tmp/x.png
做法：每 0.5 秒抽一帧；文字轮廓（含变暗的字）大变 = 换了一句；每句取最后一帧（全句都已出现）；第 0 屏是标题。"""
import sys, os, glob, subprocess, tempfile, numpy as np, imageio_ffmpeg
from PIL import Image
mp4, *ss, out = sys.argv[1:]; ss = [int(x) for x in ss]
if not mp4.endswith('.mp4'):   # 直接按脚本画（与出片同一套画法，定稿视频核对保证视频与它一致）：python3 抽屏.py NN 句号… 输出.png，按句号准确取屏，不靠画面分句（16 画面分句只分出 16 句，实际 18 句）
    import json, re
    sys.path.insert(0, '.'); import render as R
    d = json.load(open(f'scripts/{mp4}.json')); R.apply_script(d)
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import 颜色核对 as _YS; colors = _YS.颜色(d)   # G50：和出片程序同一个分色（26 起 PAL26 + 每屏回溯挑色）
    d_ = tempfile.mkdtemp(); fs = []
    for n in ss:
        s_ = d['sentences'][n - 1]; sc = R.sent_colors(colors, s_); ch = [[tuple(p) for p in c['align']] for c in s_['chunks']]; nt = [c.get('note') for c in s_['chunks']]
        es = R.max_es(ch, sc, nt); cap = d.get('字号上限', {}).get(f'S{n}')
        R.ES_FIXED = min(es, 100 * R.S, float(cap) * R.S if cap else 1e9); f = f'{d_}/S{n}.png'
        R.frame_interlinear(ch, sc, mp4, 0.5, f, active=len(ch) - 1, notes=nt); fs.append(f)
    cols = 2 if len(fs) > 1 else 1; rows = (len(fs) + cols - 1) // cols
    T = Image.new('RGB', (960 * cols, 540 * rows))
    for j, f in enumerate(fs): T.paste(Image.open(f).convert('RGB').resize((960, 540)), ((j % cols) * 960, (j // cols) * 540))
    T.save(out); print('已画', ' '.join(f'S{n}' for n in ss), '→', out); sys.exit()
d = tempfile.mkdtemp(); subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), '-v', 'quiet', '-i', mp4, '-vf', 'fps=2,scale=960:540', f'{d}/%05d.png'], check=True)
fs = sorted(glob.glob(f'{d}/*.png')); grp = []; prev = None
for f in fs:
    g = np.asarray(Image.open(f).convert('L').resize((480, 270)), dtype=np.int16)[:250]
    m = g > 30
    if prev is None or (m ^ prev).mean() > 0.04: grp.append([])
    grp[-1].append(f); prev = m
print(f'{len(grp) - 1} 句（第 0 屏是标题）')
_n = os.path.basename(mp4)[:2]
if os.path.exists(f'scripts/{_n}.json'):
    import json as _j; _k = len(_j.load(open(f'scripts/{_n}.json'))['sentences'])
    if _k != len(grp) - 1: print(f'【注意】画面分出 {len(grp) - 1} 句，脚本是 {_k} 句，句号对不上——改用 python3 抽屏.py {_n} 句号… 输出.png 按脚本画（定稿视频核对已保证视频每屏与脚本画的一致）')
sel = [grp[i][-1] for i in ss if i < len(grp)]
cols = 2 if len(sel) > 1 else 1; rows = (len(sel) + cols - 1) // cols
T = Image.new('RGB', (960 * cols, 540 * rows))
for j, f in enumerate(sel): T.paste(Image.open(f).convert('RGB'), ((j % cols) * 960, (j // cols) * 540))
T.save(out); print('已存', out)
