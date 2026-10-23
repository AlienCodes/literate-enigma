#!/usr/bin/env python3
"""全篇核查（2026-10-23 用户问“做完的视频到底有没有严格按标准来”）：用现行程序把每一篇重新查一遍，每篇一行结论。
  ① 踩坑核查 NN 文本（现行全部文本门：排版、重点词、译文、对齐、读音登记、对照记录……；有“从第N篇起”的门按原定范围）
  ② 定稿视频核对 --只查清点和镜像（每篇只存一个最终版、两仓库一致）
在视频工作目录下运行：python3 <工具目录>/全篇核查.py [NN …]（不写就查全部有脚本的篇目）"""
import os, sys, re, glob, subprocess
T = os.path.dirname(os.path.abspath(__file__)); V = os.path.dirname(T); sys.path.insert(0, T)
nos = sys.argv[1:] or sorted(os.path.basename(p)[:2] for p in glob.glob(f'{V}/脚本/[0-9][0-9].json'))
bad = 0
import 工作稿核对 as _G
for no in nos:
    if _G.旧了(f'scripts/{no}.json', f'{V}/脚本/{no}.json'): print(f'{no} ✘ 工作目录的脚本是旧稿（G19），先同步'); bad += 1; continue
    try: r = subprocess.run(['python3', f'{T}/踩坑核查.py', no, '文本'], capture_output=True, text=True, timeout=900)
    except subprocess.TimeoutExpired: print(f'{no} ✘ 超时'); bad += 1; continue
    x = [l.strip() for l in (r.stdout + r.stderr).splitlines() if '✘' in l or '【停止】' in l or 'Traceback' in l]
    bad += bool(r.returncode)
    print(f'{no} ' + ('✔ 文本门全部通过' if not r.returncode else f'✘ {len(x)} 处：' + ' ｜ '.join(x[:3])[:300]), flush=True)
r = subprocess.run(['python3', f'{T}/定稿视频核对.py', '--只查清点和镜像'], capture_output=True, text=True)
print('清点和镜像 ' + ('✔' if not r.returncode else '✘ ' + ' ｜ '.join(r.stdout.strip().splitlines()[-3:])[:300]))
sys.exit(1 if bad or r.returncode else 0)
