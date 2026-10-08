#!/usr/bin/env python3
"""把定稿的 4K 视频复制到仓库根目录的"最终版4K视频/"，文件名 = 序号 - 英文标题 - 中文标题.mp4（2026-10-08 用户定）。
  python3 视频/工具/归档定稿视频.py 01 02 03 04
只复制、不移动（视频/视频/NN.mp4 留在原处，核查程序要用）；复制后逐字节核对与定稿一致，并重写文件夹里的目录 README.md。
只能归档已经确认是 4K 定稿的篇目：视频必须是 3840×2160。
存视频的文件夹只存定稿（G7，用户 2026-10-08："之前那些有瑕疵的视频要及时删除，就只能存我们最后定稿的这个版本"）：
归档后自动删掉这一篇的旧草稿（视频/视频/草稿1080p/NN_*）和试听视频（视频/试听/NN_*.mp4 等），最后用《踩坑核查》的 G7 检查全部文件夹。"""
import sys, os, re, json, glob, shutil, hashlib, subprocess
T = os.path.dirname(os.path.abspath(__file__)); V = os.path.dirname(T); ROOT = os.path.dirname(V)
DST = f'{ROOT}/最终版4K视频'
md5 = lambda p: hashlib.md5(open(p, 'rb').read()).hexdigest()
safe = lambda s: re.sub(r'[\\/:*?"<>|]', '', s).strip()          # 去掉文件名里不能用的字符


def size_of(p):
    import imageio_ffmpeg
    r = subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), '-i', p], capture_output=True, text=True).stderr
    return re.search(r'Video: .*?, (\d+)x(\d+)', r).groups()


os.makedirs(DST, exist_ok=True)
for no in [a.zfill(2) for a in sys.argv[1:]]:
    d = json.load(open(f'{V}/脚本/{no}.json')); src = f'{V}/视频/{no}.mp4'
    if size_of(src) != ('3840', '2160'): sys.exit(f'第{no}篇不是 4K 定稿视频，不归档')
    name = f"{no} - {safe(d['title_en'])} - {safe(d['title_zh'])}.mp4"
    for old in glob.glob(f'{DST}/{no} - *.mp4'):                   # 同一篇的旧文件（标题改过时）先删掉
        if os.path.basename(old) != name: os.remove(old)
    shutil.copy2(src, f'{DST}/{name}')
    assert md5(src) == md5(f'{DST}/{name}'), f'第{no}篇复制后与定稿不一致'
    print(f'已归档：{name}')
    for old in glob.glob(f'{V}/视频/草稿1080p/{no}_*') + [q for q in glob.glob(f'{V}/试听/{no}_*') if q.lower().endswith(('.mp4', '.mov', '.m4v', '.webm', '.mkv', '.avi'))]:
        os.remove(old); print(f'  已删除旧草稿/试听视频：{os.path.relpath(old, ROOT)}')
if os.path.isdir(f'{V}/视频/草稿1080p') and not os.listdir(f'{V}/视频/草稿1080p'): os.rmdir(f'{V}/视频/草稿1080p')
rows = []
for p in sorted(glob.glob(f'{DST}/[0-9][0-9] - *.mp4')):
    no, en, zh = os.path.basename(p)[:-4].split(' - ', 2)
    rows.append(f'| {no} | {en} | {zh} | {os.path.getsize(p) / 1e6:.1f} MB |')
open(f'{DST}/README.md', 'w').write('# 最终版 4K 视频\n\n> 这里只放已经定稿的 4K 视频（3840×2160），每篇都已通过《交付核查》出片前、出片后全部核查。'
                                     '\n> 每篇只存最后定稿的一个版本；有瑕疵的旧版本、草稿一律及时删除（用户 2026-10-08 要求）。'
                                     '\n> 文件名：序号 - 英文标题 - 中文标题。与 `视频/视频/NN.mp4` 逐字节相同，由 `视频/工具/归档定稿视频.py` 复制并核对。\n\n'
                                     '| 序号 | 英文标题 | 中文标题 | 大小 |\n|---|---|---|---|\n' + '\n'.join(rows) + '\n')
print(f'共 {len(rows)} 篇，目录已写入 最终版4K视频/README.md')
sys.path.insert(0, T); import importlib; K = importlib.import_module('踩坑核查')
vf = K.video_folders(ROOT)
print('存视频的文件夹只存定稿（G7）：' + ('通过' if not vf else '\n  ✘ ' + '\n  ✘ '.join(vf)))
sys.exit(1 if vf else 0)
