#!/usr/bin/env python3
"""全篇核查（2026-10-23 用户问“做完的视频到底有没有严格按标准来”）：用现行程序把每一篇重新查一遍，每篇一行结论。
  ① 踩坑核查 NN 文本（现行全部文本门：排版、重点词、译文、对齐、读音登记、对照记录……；有“从第N篇起”的门按原定范围）
  ② 定稿视频核对 --只查清点和镜像（每篇只存一个最终版、两仓库一致）
在视频工作目录下运行：python3 <工具目录>/全篇核查.py [NN …]（不写就查全部有脚本的篇目）"""
import os, sys, re, glob, subprocess
T = os.path.dirname(os.path.abspath(__file__)); V = os.path.dirname(T); sys.path.insert(0, T)
nos = sys.argv[1:] or sorted(os.path.basename(p)[:2] for p in glob.glob(f'{V}/脚本/[0-9][0-9].json'))
bad = 0
import hashlib, json, datetime
from 重查记录 import STAMP, 程序指纹, _sha, 已出片, 键, 欠着
if sys.argv[1:2] == ['--欠着']: sys.exit(0 if 欠着() else 1)
if sys.argv[1:2] == ['--视频']:   # 铁4：用现行程序把欠着的篇目逐屏、逐样本重查（定稿视频核对），一篇过了记一篇
    fp = 程序指纹(); mp = 已出片(); todo = 欠着(); bad = []
    try: st = json.load(open(STAMP))
    except Exception: st = {}
    st.setdefault('篇', {}); print(f'要重查 {len(todo)} 篇：{" ".join(todo) or "无"}', flush=True)
    for no in todo:
        k0 = 键(no, mp[no], fp)   # 查之前先取键：查的过程中脚本或视频被别的会话改了，就不能记成查过（2026-10-23 20 篇就差点被记错）
        r = subprocess.run(['python3', f'{T}/定稿视频核对.py', no], capture_output=True, text=True)
        x = [l for l in r.stdout.splitlines() if '✘' in l][:3]
        print(f'{no} ' + ('✔' if not r.returncode else '✘ ' + ' ｜ '.join(x)[:300]), flush=True)
        if r.returncode: bad.append(no); continue
        if 键(no, mp[no], fp) != k0: print(f'{no} 查的过程中脚本或视频变了，不记，下次重查', flush=True); continue
        st['篇'][no] = k0; st['时间'] = f'{datetime.datetime.utcnow():%Y-%m-%dT%H:%M}（UTC）'
        json.dump(st, open(STAMP, 'w'), ensure_ascii=False, indent=0)
    if bad: sys.exit(f'【欠着】全篇重查没过（铁4）：{" ".join(bad)} 存的视频与现行程序、现行脚本出的不一致')
    print(f'全篇重查通过（铁4）：已出片 {len(mp)} 篇都与现行程序一致'); sys.exit(0)
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
