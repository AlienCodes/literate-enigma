#!/usr/bin/env python3
"""流程自检（规则执行机器当场跑）：
  G10 同一篇同时只能跑一条定稿流水线：占着锁再启动，必须停；
  画17/守则9 定稿流水线的步骤顺序固定：⓪ 规则执行核查 → ① 出片前核查 → ② 出 4K → ③ 出片后核查 → ④ 对照文本、文章同步 → ⑤ 归档 → ⑥ 推送；
  顺序被改乱必须报出（造一个调换了的样本）。"""
import os, sys, re, subprocess, tempfile, fcntl, shutil
T = os.path.dirname(os.path.abspath(__file__)); fails = []
ORDER = ['⓪ 规则执行核查', '① 出片前核查', '② 出 4K', '③ 出片后核查', '④ 对照文本', '⑤ 归档', '⑥ 存记录、推送']
def 顺序(txt):
    pos = [txt.find(f'step "{s}') for s in ORDER]
    return [] if all(p >= 0 for p in pos) and pos == sorted(pos) else [f'定稿流水线步骤缺了或顺序乱了：{[s for s, p in zip(ORDER, pos) if p < 0] or "顺序不对"}']
src = open(f'{T}/定稿流水线.sh').read()
if 顺序(src): fails.append('原样就报：' + 顺序(src)[0])
sw = src.replace('step "② 出 4K', 'step "TMP').replace('step "③ 出片后核查', 'step "② 出 4K').replace('step "TMP', 'step "③ 出片后核查')
if not 顺序(sw): fails.append('没抓到：定稿流水线步骤顺序乱了（画17）')
td = tempfile.mkdtemp(); lk = open(f'{td}/.定稿流水线_99.lock', 'w'); fcntl.flock(lk, fcntl.LOCK_EX)
r = subprocess.run(['bash', f'{T}/定稿流水线.sh', '99'], capture_output=True, text=True, cwd=td, timeout=60)
if r.returncode == 0 or '已经有一条定稿流水线在跑' not in r.stdout + r.stderr: fails.append('没抓到：同一篇同时跑两条定稿流水线（G10）')
lk.close(); shutil.rmtree(td, ignore_errors=True)
print('流程自检：' + ('通过（占着锁再启动定稿流水线必停；步骤顺序被调换必报）' if not fails else '失灵！' + '；'.join(fails)))
sys.exit(1 if fails else 0)
