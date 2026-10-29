#!/usr/bin/env python3
"""合回镜像（主会话 2026-10-29：31 的配音缓存、31.md 被冲了两次）：推送两仓库 / 定稿 拿 main 的 视频/ 盖镜像之前，
先把“只能推镜像的会话”提交到镜像分支、main 里还没有的改动按文件合回 main，不许盖掉。

怎么认：镜像上 主仓库同步的提交说明以“镜像：”开头、带一行“主仓库提交：<哈希>”（推送两仓库、定稿.sh 写的；老历史只认开头）。最近一次这样的提交 S 之后，
视频/、新版定稿/、最终版4K视频/ 下被改过的文件 = 别的会话直接推到镜像的改动（GitHub 工作流 bot 写回的不算，归 G58 白名单管）。每个文件三方比（S 时的镜像 / 现在的镜像 / main 现在）：
  main 和现在的镜像一样            → 不用动
  main 还是 S 时那一版（main 没改） → 拿镜像的（新增、修改、删除都照搬）进 main
  两边都改了                      → 文本按三方合并（git merge-file），合得干净就写进 main；合不了的停下报出来，不许盖
用法：python3 合回镜像.py <主仓库> <镜像>   改了的文件已 git add 到主仓库（不提交）；冲突返回 1
      python3 合回镜像.py --自检"""
import sys, os, subprocess, tempfile, shutil
D = ('视频/', '新版定稿/', '最终版4K视频/')
同步前缀 = '镜像：'

def g(r, *a, 字节=False):
    x = subprocess.run(['git', '-c', 'core.quotepath=off', '-C', r, *a], capture_output=True)
    return x if 字节 else x.stdout.decode('utf-8', 'replace')

def 上次同步(L):
    for _ in range(2):
        cs = [c.split('\0', 1) for c in g(L, 'log', '-500', '--format=%H%x00%B%x1e').split('\x1e') if c.strip()]
        for h, m in cs:   # 先认带“主仓库提交：”的（推送两仓库、定稿.sh 写的）；只看“镜像：”开头不够，别的会话也可能这样写说明
            if '\n主仓库提交：' in m: return h.strip()
        for h, m in cs:   # 老历史里还没有这一行：退回认“镜像：”开头
            if m.startswith(同步前缀): return h.strip()
        if os.path.exists(f'{L}/.git/shallow'): g(L, 'fetch', '-q', '--deepen=500', 'origin')   # 浅克隆：往回多取一些再找
        else: break
    return None

def 读(L, rev, f):
    r = g(L, 'show', f'{rev}:{f}', 字节=True)
    return r.stdout if r.returncode == 0 else None

def 合回(P, L):
    S = 上次同步(L)
    if not S: return [], ['镜像分支上找不到“镜像：”开头的同步提交，判断不了哪些是只在镜像的改动（先别推，报给主会话）']
    动, 机 = set(), 'github-actions[bot]'   # 工作流（bot）写回的由 推送两仓库 的 G58 白名单管，这里只管会话推的
    for 段 in g(L, 'log', '--no-merges', '--name-only', '--format=@%an', f'{S}..HEAD', '--', *D).split('@')[1:]:
        作者, *fs = 段.strip('\n').split('\n')
        if 作者 != 机: 动 |= {f for f in fs if f}
    动 = sorted(动)
    做了, 冲突 = [], []
    for f in 动:
        base, 镜 = 读(L, S, f), 读(L, 'HEAD', f)
        pf = f'{P}/{f}'; 主 = open(pf, 'rb').read() if os.path.exists(pf) else None
        if 主 == 镜: continue
        if 主 == base:
            if 镜 is None: os.remove(pf); g(P, 'rm', '-q', '--cached', '--ignore-unmatch', '--', f); 做了.append(f'删 {f}')
            else:
                os.makedirs(os.path.dirname(pf), exist_ok=True); open(pf, 'wb').write(镜); g(P, 'add', '--', f); 做了.append(f'取镜像 {f}')
            continue
        if None not in (base, 镜, 主) and b'\0' not in base + 镜 + 主:   # 两边都改了的文本：三方合并
            with tempfile.TemporaryDirectory() as td:
                for n, v in (('主', 主), ('底', base), ('镜', 镜)): open(f'{td}/{n}', 'wb').write(v)
                r = subprocess.run(['git', 'merge-file', '-p', f'{td}/主', f'{td}/底', f'{td}/镜'], capture_output=True)
            if r.returncode == 0:
                open(pf, 'wb').write(r.stdout); g(P, 'add', '--', f); 做了.append(f'三方合并 {f}'); continue
        冲突.append(f)
    return 做了, ([f'两边都改了、合不了（不许盖）：{f}' for f in 冲突])

def 自检():
    fails = []
    with tempfile.TemporaryDirectory() as td:
        P, L = f'{td}/P', f'{td}/L'
        for r in (P, L):
            os.makedirs(f'{r}/视频'); subprocess.run(['git', 'init', '-q', r])
            for k, v in (('user.name', '自检'), ('user.email', 'x@example.com')): g(r, 'config', k, v)
        w = lambda r, f, s: (os.makedirs(os.path.dirname(f'{r}/{f}'), exist_ok=True), open(f'{r}/{f}', 'w').write(s))
        for r in (P, L):
            w(r, '视频/a.md', '一\n二\n三\n四\n五\n'); w(r, '视频/b.md', 'b\n'); w(r, '视频/c.md', 'c\n'); w(r, '视频/d.md', 'd\n')
            g(r, 'add', '-A'); g(r, 'commit', '-qm', '镜像：同步' if r == L else 'init')
        # 只能推镜像的会话：新加一个文件、改两个文件、删一个文件
        w(L, '视频/制作记录/31.md', '31 交接\n'); w(L, '视频/b.md', 'b 镜像改\n'); w(L, '视频/a.md', '一\n二\n三\n四\n五 镜像改\n'); os.remove(f'{L}/视频/d.md')
        g(L, 'add', '-A'); g(L, 'commit', '-qm', '31 交接（只在镜像）')
        w(P, '视频/a.md', '一 主改\n二\n三\n四\n五\n')   # main 同时改了 a.md 的另一处：三方合并得干净
        做, 冲 = 合回(P, L)
        if 冲: fails.append(f'误报冲突：{冲}')
        if not os.path.exists(f'{P}/视频/制作记录/31.md'): fails.append('没合回：镜像上新加的 31.md 被盖掉了')
        if open(f'{P}/视频/b.md').read() != 'b 镜像改\n': fails.append('没合回：镜像上改的 b.md 被盖掉了')
        if os.path.exists(f'{P}/视频/d.md'): fails.append('没合回：镜像上删的 d.md 还在')
        if open(f'{P}/视频/a.md').read() != '一 主改\n二\n三\n四\n五 镜像改\n': fails.append('三方合并不对：a.md 两边改的不同处没都留下')
        if open(f'{P}/视频/c.md').read() != 'c\n': fails.append('误动：两边都没改的 c.md 变了')
        # 工作流（bot）写回的不归这里管（G58 白名单管），不许合回
        g(P, 'commit', '-qam', 'w'); w(L, '视频/bot.md', 'bot\n'); g(L, 'add', '-A'); subprocess.run(['git', '-C', L, '-c', 'user.name=github-actions[bot]', '-c', 'user.email=b@x', 'commit', '-qm', '工作流'], capture_output=True)
        合回(P, L)
        if os.path.exists(f'{P}/视频/bot.md'): fails.append('误合：工作流 bot 写的文件被合回（归 G58 白名单管）')
        # 两边改了同一行：必须停，main 那份不许被盖，也不许被改
        g(P, 'commit', '-qam', 'x'); w(L, '视频/c.md', 'c 镜像\n'); g(L, 'commit', '-qam', '只在镜像'); w(P, '视频/c.md', 'c 主\n')
        做, 冲 = 合回(P, L)
        if not any('c.md' in x for x in 冲): fails.append('没停：两边改了同一行的 c.md 没报冲突')
        if open(f'{P}/视频/c.md').read() != 'c 主\n': fails.append('冲突时动了 main 那份')
        # 已同步过的（main 和镜像一样）不重复动；镜像同步提交之后没有别的提交 → 什么都不做
        g(P, 'commit', '-qam', 'y'); w(P, '视频/c.md', 'c 镜像\n'); g(P, 'commit', '-qam', 'z')
        g(L, 'commit', '-q', '--allow-empty', '-m', '镜像：再同步')
        做, 冲 = 合回(P, L)
        if 做 or 冲: fails.append(f'同步之后没有新改动却动了：{做 or 冲}')
        # 别的会话的说明也写成“镜像：”开头（但没有“主仓库提交：”一行）：照样算只在镜像的改动，合回
        g(L, 'commit', '-q', '--allow-empty', '-m', '镜像：同步\n\n主仓库提交：abc'); w(L, '视频/e.md', 'e 镜像会话\n'); g(L, 'add', '-A'); g(L, 'commit', '-qm', '镜像：31 交接（会话自己这样写）')
        合回(P, L)
        if not os.path.exists(f'{P}/视频/e.md'): fails.append('没合回：别的会话说明写成“镜像：”开头，就被当成同步、改动被盖（要认“主仓库提交：”一行）')
        # 找不到同步提交：停下报出来，不猜
        L2 = f'{td}/L2'; os.makedirs(L2); subprocess.run(['git', 'init', '-q', L2]); g(L2, 'config', 'user.name', 'x'); g(L2, 'config', 'user.email', 'x@x')
        w(L2, '视频/x.md', 'x\n'); g(L2, 'add', '-A'); g(L2, 'commit', '-qm', 'init')
        if not 合回(P, L2)[1]: fails.append('没停：镜像上没有同步提交时没报')
    return fails

if __name__ == '__main__':
    if sys.argv[1:2] == ['--自检']:
        e = 自检(); print('\n'.join(e) or '合回镜像 自检通过（镜像上新加、改、删的文件合回 main；两边改不同处三方合并；同一行冲突停下、main 不动；同步后不重复动；找不到同步提交停）'); sys.exit(1 if e else 0)
    P, L = sys.argv[1:3]; 做, 冲 = 合回(P, L)
    for x in 做: print(f'合回镜像：{x}')
    if 冲: print('【停止】镜像上有只在镜像的改动，和 main 冲突（不许盖掉，先人工合）：\n  ' + '\n  '.join(冲)); sys.exit(1)
