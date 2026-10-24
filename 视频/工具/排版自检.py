#!/usr/bin/env python3
"""排版自检（规则执行机器，CLAUDE.md 第16条）：画面、片头的规矩写在排版程序（render.py、title2.py）的做法里，
这里直接调用同一套函数，每条规矩造一个错例（必须报出/必须不同）和一个正例（不得误报），自检不过 = 排版程序失灵。
  L1/L4 每屏字号铺满（放得下的最大字号，大一号就放不下；按句算，不全片统一）  L5 中文 = 英文 × 0.72
  L2 一行放得下就不拆   L3 整组折行后末行孤词查得出   L6 数字不拆   L7 说明计入字号   L8 正文页不画标题
  L10 “另译”（#Y）黄字   L11 重点词中文两侧留 1/4 字宽间隙、标点旁不加   L15 中文意思找不到颜色就停
  L12 只有 3840×2160 能归档   H1 片头色块水平居中   H2 色块是圆角长方形   H3 色块里的字上下居中
在工具目录运行（规则执行机器当场跑）：python3 排版自检.py"""
import os, sys, re, ast, subprocess, tempfile, shutil
T = os.path.dirname(os.path.abspath(__file__)); os.chdir(T); sys.path.insert(0, T)
import numpy as np
from PIL import Image
import render as R
fails = []; ok_ = []
def 判(name, cond, why=''):
    (ok_ if cond else fails).append(name if cond else f'没抓到：{name}' + (f'（{why}）' if why else ''))

ch1 = [[('Prices of prized', '名贵的'), ('"broken" tulips,', '“碎色”郁金香，'), ('with streaked petals,', '有着带条纹的花瓣，'), ('soared.', '价格一路飙升。')]]
cols = {}
# L1/L4：放得下的最大字号；大一号放不下（或已到上限）；不同的句子字号不同（按句算）
es = R.max_es(ch1, cols); _, t1, w1, _ = R._measure(ch1, cols, [None], es, R._grouping(ch1, cols))
_, t2, w2, _ = R._measure(ch1, cols, [None], es + 1, R._grouping(ch1, cols))
判('L1/L4 每屏字号铺满', t1 <= R.MAXH2 and w1 <= R.MAXW2 and (es >= 130 * R.S or t2 > R.MAXH2 or w2 > R.MAXW2), f'es={es}')
ch2 = [[('It was a long sentence with many words that keep going and going until it fills the screen,', '这是一个很长的句子……')]] * 3
判('L4 字号按句算（长句小、短句大，不全片统一）', R.max_es(ch2, cols) < es)
# L5：中文字号 = 英文 × 0.72
_, _, _, (zs, *_r) = R._measure(ch1, cols, [None], 80, R._grouping(ch1, cols))
判('L5 中文 = 英文 × 0.72', R.ZR == 0.72 and zs == int(80 * 0.72), f'ZR={R.ZR} zs={zs}')
# L7：说明计入字号（加一条长说明，字号必须变小）
判('L7 说明计入字号', R.max_es(ch1, cols, ['这是一条很长很长的说明，用来检查说明会不会被算进字号里，' * 3]) < es)
# L6：数字、英文连续字符不拆
ef = R.EN(80, 600); lines = R.layout([('On 19 September 1991 two hikers found a body in the 1,234-metre ice', R.FG_EN)], ef, 600)
words = [''.join(u for u, _ in ln).split() for ln in lines]
判('L6 数字不拆', all(w in ('19', '1991', '1,234-metre') or not re.search(r'\d', w) for ln in words for w in ln) and len(lines) > 1)
# L2：一行放得下就不拆（宽度足够时只有一行）
判('L2 放得下不拆行', len(R.layout([('Prices of prized tulips soared.', R.FG_EN)], ef, 5000)) == 1)
# L3：整组折行后末行孤词查得出（造一组越来越长的英文，必须在某个字号查出孤词）
hit = False
for k in range(6, 40):
    c3 = [[(' '.join(['tulip'] * k) + ' end,', '郁金香' * k)]]
    for e3 in (60, 70, 80, 90):
        if R.orphan_lines(c3, cols, [None], e3 * R.S): hit = True; break
    if hit: break
判('L3 末行孤词查得出', hit and not R.orphan_lines(ch1, cols, [None], es))
# L8：正文页不画标题（传了标题，画面也必须一模一样）
td = tempfile.mkdtemp()
R.frame_interlinear(ch1, cols, 'HEADER TITLE XYZ', 0.5, f'{td}/a.png'); R.frame_interlinear(ch1, cols, '', 0.5, f'{td}/b.png')
判('L8 正文页不画标题', np.array_equal(np.asarray(Image.open(f'{td}/a.png')), np.asarray(Image.open(f'{td}/b.png'))))
# L10：#Y 开头的“另译”是黄字（同一条说明不带 #Y 就没有黄字）
Y = np.array((251, 191, 36))
def 黄(p): a = np.asarray(Image.open(p).convert('RGB')).astype(int); return int((np.abs(a - Y).sum(2) < 30).sum())
R.frame_interlinear(ch1, cols, '', 0.5, f'{td}/y.png', notes=['#Y另译：价格猛涨']); R.frame_interlinear(ch1, cols, '', 0.5, f'{td}/n.png', notes=['另译：价格猛涨'])
判('L10 另译黄字', 黄(f'{td}/y.png') > 50 and 黄(f'{td}/n.png') == 0, f'{黄(f"{td}/y.png")}/{黄(f"{td}/n.png")}')
# L11：重点词中文两侧留间隙，标点旁、格子边缘不加
sg = R._segs_zh('他**扫描了**(scanned)文件', {'scanned': (1, 2, 3)}); sg2 = R._segs_zh('**扫描了**(scanned)。', {'scanned': (1, 2, 3)})
判('L11 重点词两侧间隙', [t for t, _ in sg] == ['他', R.KSP, '扫描了', R.KSP, '文件'] and R.KSP not in [t for t, _ in sg2], str([t for t, _ in sg]))
# L15：中文意思找不到颜色（英文没加粗）就停
s15 = {'chunks': [{'en': 'He scanned it.', 'zh': '他**扫描了**(scanned)它。', 'align': [['He scanned it.', '他**扫描了**(scanned)它。']]}]}
try: R.unify_colors({}, [s15]); stop = False
except SystemExit as e: stop = '找不到颜色' in str(e)
try: R.unify_colors({'scanned': (1, 2, 3)}, [s15]); fine = True
except SystemExit: fine = False
stop = stop and fine
判('L15 找不到颜色就停', stop)
# L12：归档只收 3840×2160（取归档程序自己的 size_of 量尺寸）
src = open(f'{T}/归档定稿视频.py').read(); tree = ast.parse(src); ns = {}
fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'size_of')
import imageio_ffmpeg as iff, json, hashlib, glob
exec(compile(ast.Module([n for n in tree.body if isinstance(n, (ast.Import, ast.ImportFrom))] + [fn], []), '归档', 'exec'), ns)
FF = iff.get_ffmpeg_exe()
for s_, nm in (('1920x1080', 'hd'), ('3840x2160', 'k4')):
    subprocess.run([FF, '-v', 'error', '-y', '-f', 'lavfi', '-i', f'color=c=black:s={s_}:d=0.2', '-c:v', 'libx264', f'{td}/{nm}.mp4'])
判('L12 只有 3840×2160 能归档', ns['size_of'](f'{td}/hd.mp4') != ('3840', '2160') and ns['size_of'](f'{td}/k4.mp4') == ('3840', '2160')
   and "if size_of(src) != ('3840', '2160')" in src)
# H1–H3：片头色块水平居中、圆角、字上下居中
import title2 as T2
T2.frame_title2(20, 'The Iceman Who Came In From the Cold', '冰人奥茨', ['Iceman'], [], f'{td}/t.png')
a = np.asarray(Image.open(f'{td}/t.png').convert('RGB')).astype(int)
box = (np.abs(a - np.array(T2.AC1)).sum(2) < 8)
def _run(r):   # 一行里最长的连续色块段 (长度, 起, 止)
    best = (0, 0, 0); st = None
    for i, v in enumerate(list(r) + [False]):
        if v and st is None: st = i
        if not v and st is not None:
            if i - st > best[0]: best = (i - st, st, i - 1)
            st = None
    return best
rr = [_run(box[y]) for y in range(box.shape[0])]; ym = int(np.argmax([r[0] for r in rr]))
if rr[ym][0] > 100 * R.S:
    x0, x1 = rr[ym][1], rr[ym][2]; cxw = (x0 + x1) / 2; cx = int(cxw)
    cxp = x0 + 30 * R.S   # 色块左边留白处（字到不了）量上下边界：在正中量会被字截断，H3 量不出字偏了（2026-10-24 执行效应演练查出）
    y0 = ym
    while y0 > 0 and box[y0 - 1, cxp]: y0 -= 1
    y1 = ym
    while y1 < box.shape[0] - 1 and box[y1 + 1, cxp]: y1 += 1
    判('H1 片头色块水平居中', abs(cxw - T2.W / 2) <= 2 * R.S, f'{cxw} vs {T2.W / 2}')
    判('H2 色块是圆角长方形', not box[y0, x0] and not box[y1, x1] and box[y0, cx] and box[(y0 + y1) // 2, x0])
    ink = (np.abs(a[y0:y1 + 1, x0 + 24 * R.S:x1 - 24 * R.S] - np.array((20, 40, 32))).sum(2) < 60); iy = np.where(ink)[0]   # 去掉圆角外的底色（四角会被当成字）
    判('H3 色块里的字上下居中', len(iy) > 0 and abs((iy.min() + iy.max()) / 2 - (y1 - y0) / 2) <= 3 * R.S, f'{(iy.min() + iy.max()) / 2 if len(iy) else None} vs {(y1 - y0) / 2}')
else: 判('H1–H3 片头色块', False, '画面里找不到色块')
# D5/文24：{{…}} 注解只显示、不朗读（朗读前去掉，括号里的字不进配音）
判('D5 注解只显示不朗读', R.strip_gloss('scraped {{(intensely)}} off the dish') == 'scraped  off the dish')
# D6/文25：中文 \n 是格内换行（拼接时去掉），{{（说明）|词}} 用对应重点词的颜色显示
sg6 = R._segs_zh('{{（刮下来）|scraped}}', {'scraped': (9, 9, 9)})
判('D6 格内分行与彩色说明', R.strip_zh('第一行\n第二行{{（说明）|word}}') == '第一行第二行（说明）' and ('（刮下来）', (9, 9, 9)) in sg6)
# 画1：画面 16:9（1920×1080，4K 时 ×2）
im1 = Image.open(f'{td}/b.png'); 判('画1 画面 16:9', im1.size == (1920 * R.S, 1080 * R.S) and R.W * 9 == R.H * 16)
shutil.rmtree(td)
print('排版自检：' + (f'通过（{len(ok_)} 项：' + '、'.join(x.split(' ')[0] for x in ok_) + ' 造的错都报出、正例不误报）' if not fails else '失灵！' + '；'.join(fails)))
sys.exit(1 if fails else 0)
