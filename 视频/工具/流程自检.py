#!/usr/bin/env python3
"""流程自检（规则执行机器当场跑）：
  G10 同一篇同时只能跑一条定稿流水线：占着锁再启动，必须停；
  画17/守则9 定稿流水线的步骤顺序固定：⓪ 规则执行核查 → ① 出片前核查 → ② 出 4K → ③ 出片后核查 → ④ 对照文本、文章同步 → ⑤ 归档 → ⑥ 推送；
  顺序被改乱必须报出（造一个调换了的样本）。"""
import os, sys, re, subprocess, tempfile, fcntl, shutil
T = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, T); fails = []
ORDER = ['⓪ 规则执行核查', '① 出片前核查', '② 出 4K', '③ 出片后核查', '④ 对照文本', '⑤ 归档', '⑥ 存记录、推送']
def 顺序(txt):
    pos = [txt.find(f'step "{s}') for s in ORDER]
    return [] if all(p >= 0 for p in pos) and pos == sorted(pos) else [f'定稿流水线步骤缺了或顺序乱了：{[s for s, p in zip(ORDER, pos) if p < 0] or "顺序不对"}']
src = open(f'{T}/定稿流水线.sh').read()
if 顺序(src): fails.append('原样就报：' + 顺序(src)[0])
sw = src.replace('step "② 出 4K', 'step "TMP').replace('step "③ 出片后核查', 'step "② 出 4K').replace('step "TMP', 'step "③ 出片后核查')
if not 顺序(sw): fails.append('没抓到：定稿流水线步骤顺序乱了（画17）')
def 推送锁(txt):   # G17：⑥ 的提交、镜像同步、推送要占 推送两仓库 的锁
    ls = txt.splitlines(); i = [k for k, l in enumerate(ls) if '镜像同步.py' in l and not l.lstrip().startswith('#')]
    j = [k for k, l in enumerate(ls) if re.match(r'exec 7>.*推送两仓库\.lock.*; flock 7', l)]
    u = [k for k, l in enumerate(ls) if l.strip() == 'flock -u 7']
    return [] if i and j and u and j[0] < i[0] < u[0] else ['⑥ 镜像同步没在推送锁里（G17）']
if 推送锁(src): fails.append('原样就报：' + 推送锁(src)[0])
if not 推送锁(re.sub(r'(?m)^exec 7>.*\n', '', src)): fails.append('没抓到：⑥ 不占推送锁（G17）')
import 工作稿核对 as _G; _d = tempfile.mkdtemp(); _w, _p = f'{_d}/w.json', f'{_d}/p.json'   # G19：工作稿比仓库旧必停
open(_w, 'w').write('旧'); open(_p, 'w').write('新'); os.utime(_w, (1, 1))
if not _G.旧了(_w, _p): fails.append('没抓到：工作目录脚本比仓库旧（G19）')
open(_p, 'w').write('旧')
if _G.旧了(_w, _p): fails.append('误报：工作稿与仓库一致（G19）')
shutil.rmtree(_d, ignore_errors=True)
td = tempfile.mkdtemp(); lk = open(f'{td}/.定稿流水线_99.lock', 'w'); fcntl.flock(lk, fcntl.LOCK_EX)
r = subprocess.run(['bash', f'{T}/定稿流水线.sh', '99'], capture_output=True, text=True, cwd=td, timeout=60)
if r.returncode == 0 or '已经有一条定稿流水线在跑' not in r.stdout + r.stderr: fails.append('没抓到：同一篇同时跑两条定稿流水线（G10）')
lk.close(); shutil.rmtree(td, ignore_errors=True)
print('流程自检：' + ('通过（占着锁再启动定稿流水线必停；步骤顺序被调换必报）' if not fails else '失灵！' + '；'.join(fails)))
sys.exit(1 if fails else 0)
