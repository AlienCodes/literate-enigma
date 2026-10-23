#!/usr/bin/env python3
"""推送自检（规则执行机器当场跑）：在 /tmp 建两个假的远端仓库，真跑一遍 推送两仓库.sh，逐项验证：
  守则3/流12 推完两边都提交、推送；G2 云端与本地一致；G11 CLAUDE.md 以 postgraduate-vocabulary 为准拷到工作分支；
  G4 中文文件名照常同步；镜像里多出来的旧文件被删掉；
造错：G1 塞进一个 101MB 的文件必须停；G3 要提交的路径不存在必须停（不许悄悄没提交还说“已推送”）。"""
import os, sys, subprocess, tempfile, shutil, fcntl
T = os.path.dirname(os.path.abspath(__file__))
G = ['git', '-c', 'user.name=自检', '-c', 'user.email=selftest@example.com', '-c', 'init.defaultBranch=main', '-c', 'core.quotepath=off']
def git(*a, cwd=None): return subprocess.run(G + list(a), cwd=cwd, capture_output=True, text=True)
def 写(p, s):
    os.makedirs(os.path.dirname(p), exist_ok=True); open(p, 'w').write(s)
tmp = tempfile.mkdtemp(); fails = []
try:
    git('init', '-q', '--bare', f'{tmp}/P.git'); git('init', '-q', '--bare', f'{tmp}/L.git')
    P, L = f'{tmp}/P', f'{tmp}/L'
    git('clone', '-q', f'{tmp}/P.git', P); git('clone', '-q', f'{tmp}/L.git', L)
    for r in (P, L):
        git('config', 'user.name', '自检', cwd=r); git('config', 'user.email', 'selftest@example.com', cwd=r)
    写(f'{P}/视频/工具/规则执行核查.py', 'import sys; sys.exit(0)\n'); 写(f'{P}/视频/a.md', 'a\n'); 写(f'{P}/视频/中文名字.md', '中\n')
    写(f'{P}/CLAUDE.md', '新守则\n'); 写(f'{P}/新版定稿/x.md', 'x\n'); 写(f'{P}/最终版4K视频/y.mp4', 'v\n')
    git('add', '-A', cwd=P); git('commit', '-qm', 'init', cwd=P); git('push', '-q', '-u', 'origin', 'HEAD:main', cwd=P)
    git('checkout', '-q', '-b', 'tb', cwd=L); 写(f'{L}/视频/旧文件.md', 'old\n'); 写(f'{L}/CLAUDE.md', '旧守则\n')
    git('add', '-A', cwd=L); git('commit', '-qm', 'init', cwd=L); git('push', '-q', '-u', 'origin', 'tb', cwd=L)
    写(f'{P}/视频/新文件.md', 'new\n')
    env = {**os.environ, 'PUSH_P': P, 'PUSH_L': L, 'PUSH_B': 'tb', 'PUSH_LOCK': f'{tmp}/推送.lock'}   # 自己的锁：在真推送里跑自检不会自己等自己
    run = lambda: subprocess.run(['bash', f'{T}/推送两仓库.sh', '推送自检'], capture_output=True, text=True, env=env, timeout=120)
    lk = open('/tmp/推送两仓库.lock', 'a')   # G16：占着真推送锁（等于在推送当中跑本自检），假仓库推送必须照样跑完、不许自己等自己
    try: fcntl.flock(lk, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError: pass   # 已经在真推送里：锁正被占着，同样的情形
    r = run(); o = r.stdout + r.stderr
    lsp = git('ls-tree', '-r', '--name-only', 'HEAD', '视频', cwd=P).stdout.split(); lsl = git('ls-tree', '-r', '--name-only', 'HEAD', '视频', cwd=L).stdout.split()
    if r.returncode != 0 or '云端已含这次提交' not in o: fails.append(f'正常推送没通过：{o.strip()[-120:]}')
    if sorted(lsp) != sorted(lsl): fails.append('没抓到：两边 视频/ 文件不一致（守则3）')
    _t = lambda r: git('ls-tree', '-r', 'HEAD', '最终版4K视频', '新版定稿', cwd=r).stdout
    if not _t(P) or _t(P) != _t(L): fails.append('没抓到：最终版4K视频、新版定稿 没镜像过去（G20）')
    if '视频/旧文件.md' in lsl: fails.append('没抓到：镜像里多出来的旧文件没删')
    if '视频/中文名字.md' not in lsl: fails.append('没抓到：中文文件名没同步（G4）')
    if open(f'{L}/CLAUDE.md').read() != '新守则\n': fails.append('没抓到：CLAUDE.md 没以 postgraduate-vocabulary 为准（G11）')
    if git('rev-parse', 'HEAD', cwd=P).stdout != git('rev-parse', 'main', cwd=f'{tmp}/P.git').stdout or \
       git('rev-parse', 'HEAD', cwd=L).stdout != git('rev-parse', 'tb', cwd=f'{tmp}/L.git').stdout: fails.append('没抓到：云端与本地不一致（G2）')
    # G1：101MB 的文件必须停，不许推上去
    with open(f'{P}/视频/大文件.bin', 'wb') as f: f.truncate(101 * 1024 * 1024)
    r = run(); o = r.stdout + r.stderr
    if r.returncode == 0 or '100MB' not in o: fails.append('没抓到：超过 100MB 的文件（G1）')
    os.remove(f'{P}/视频/大文件.bin'); git('reset', '-q', cwd=P)
    # G3：要提交的路径不存在，必须停（不许说“已推送”）
    git('rm', '-rq', '新版定稿', cwd=P); git('commit', '-qm', '去掉新版定稿', cwd=P); 写(f'{P}/视频/再一个.md', 'z\n')   # 这个路径从此不存在、也没被跟踪
    r = run(); o = r.stdout + r.stderr
    if r.returncode == 0 or '已推送' in o: fails.append('没抓到：要提交的路径不存在却说已推送（G3）')
except subprocess.TimeoutExpired:
    fails.append('没抓到：推送锁死锁（G16：在推送当中跑自检，自己等自己）')
except Exception as e:
    fails.append(f'推送自检本身出错：{e}')
finally:
    shutil.rmtree(tmp, ignore_errors=True)
print('推送自检：' + ('通过（正常推送两边一致、云端一致、CLAUDE.md 以主仓库为准、中文文件名、删旧文件；101MB 文件和路径不存在都停下）' if not fails else '失灵！' + '；'.join(fails)))
sys.exit(1 if fails else 0)
