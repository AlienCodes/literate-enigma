#!/usr/bin/env python3
"""验收：新管 定稿.sh 出的 4K 与存档的定稿 4K 是不是同一个片：文件逐字节相同，或者解码后的声音逐样本相同、画面逐帧逐像素相同。
用法：python3 对比4K.py 新.mp4 存档.mp4"""
import sys, hashlib, subprocess
import imageio_ffmpeg
FF = imageio_ffmpeg.get_ffmpeg_exe()
a, b = sys.argv[1:3]
md5 = lambda p: hashlib.md5(open(p, 'rb').read()).hexdigest()
if md5(a) == md5(b): print('逐字节相同'); sys.exit(0)
def h(p, sel): return subprocess.run([FF, '-v', 'error', '-i', p, '-map', sel, '-f', 'md5', '-'], capture_output=True, text=True).stdout.strip()
sa, sb = h(a, '0:a:0'), h(b, '0:a:0'); va, vb = h(a, '0:v:0'), h(b, '0:v:0')
print(f'文件不同；声音 {"逐样本相同" if sa == sb else "不同"}，画面 {"逐帧逐像素相同" if va == vb else "不同"}')
sys.exit(0 if sa == sb and va == vb else 1)
