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
STAMP = f'{T}/全篇重查通过.json'
def 程序指纹(t=T):   # 铁4：出片程序、排版程序（配音处理、停顿规则都在 make_video.py 里）
    return hashlib.sha256(b''.join(open(f'{t}/{f}', 'rb').read() for f in ('make_video.py', 'render.py'))).hexdigest()[:16]
def _sha(p): return hashlib.sha256(open(p, 'rb').read()).hexdigest()[:16]
def 已出片():
    P = os.path.dirname(V); out = {}
    for f in sorted(os.listdir(f'{P}/最终版4K视频')):
        if f.endswith('.mp4') and f[:2].isdigit(): out[f[:2]] = f'{P}/最终版4K视频/{f}'
    return out
def 键(no, mp4, fp=None):   # 程序 + 这一篇存的视频 + 现行脚本：三样都没变，上次的重查结论就还算数
    return f'{fp or 程序指纹()}-{_sha(mp4)}-{_sha(f"{V}/脚本/{no}.json")}'
def 欠着(stamp=STAMP, keys=None):
    """还没用现行程序重查过的已出片篇目（铁4/音29/画21：改一处，全部重查）；按篇记，查一篇记一篇，中途停了不白查"""
    if keys is None: fp = 程序指纹(); keys = {no: 键(no, p, fp) for no, p in 已出片().items()}
    try: st = json.load(open(stamp)).get('篇', {})
    except Exception: st = {}
    return [no for no, k in sorted(keys.items()) if st.get(no) != k]
if sys.argv[1:2] == ['--欠着']: sys.exit(0 if 欠着() else 1)
if sys.argv[1:2] == ['--视频']:   # 铁4：用现行程序把欠着的篇目逐屏、逐样本重查（定稿视频核对），一篇过了记一篇
    fp = 程序指纹(); mp = 已出片(); todo = 欠着(); bad = []
    try: st = json.load(open(STAMP))
    except Exception: st = {}
    st.setdefault('篇', {}); print(f'要重查 {len(todo)} 篇：{" ".join(todo) or "无"}', flush=True)
    for no in todo:
        r = subprocess.run(['python3', f'{T}/定稿视频核对.py', no], capture_output=True, text=True)
        x = [l for l in r.stdout.splitlines() if '✘' in l][:3]
        print(f'{no} ' + ('✔' if not r.returncode else '✘ ' + ' ｜ '.join(x)[:300]), flush=True)
        if r.returncode: bad.append(no); continue
        st['篇'][no] = 键(no, mp[no], fp); st['时间'] = f'{datetime.datetime.utcnow():%Y-%m-%dT%H:%M}（UTC）'
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
