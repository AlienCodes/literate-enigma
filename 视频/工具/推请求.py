#!/usr/bin/env python3
"""推 GitHub 工作流请求的正式入口（K34/G74，2026-10-26）：在镜像工作分支新建 视频/云端/请求/<名字>.txt、提交、推送，
记进本机请求账（~/.云端请求.json），并提醒：GitHub 写回结果不会唤醒会话，推完必须 send_later 约 20 分钟叫回自己；
没约唤醒，收工闸门（钩子/闸门.py 收工）就拦。格式见 视频/云端/请求/说明.md。
用法：python3 视频/工具/推请求.py <名字> "<任务行>" ["# 注释"]    例：推请求.py G72主演练 "主演练 补丁=视频/云端/待演练/G72单线程.diff\""""
import os, sys, json, subprocess, datetime, re, tempfile, shutil
L = '/home/user/literate-enigma'; B = 'claude/adoring-hamilton-5qskmm'
账 = os.path.expanduser('~/.云端请求.json')
def g(*a): return subprocess.run(['git', '-C', L, *a], capture_output=True, text=True)
def 本地慢印章(行, 有效=None, 缺口数=None):
    """K35：带补丁的 主演练 只在 GitHub 跑主演练；本地才跑的慢自检（出片守门自检）印章不在补丁里，GitHub 上每场都先撞“印章对不上”，白跑一轮。
    推之前查本仓库工作树：本地慢自检印章过期就停（先在视频工作目录跑它、再重做补丁）"""
    if '主演练' not in 行 or '补丁=' not in 行: return ''
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import 规则执行核查 as R
    有效 = 有效 or R.印章有效
    bad = [p for p in R.STAMPED if p not in ('执行效应演练.py', '执行效应声音演练.py', '彩排.sh') and not 有效(p)]   # 演练印章本身就是这次请求要盖的；彩排印章也只在 GitHub 上盖，而彩排要先有主演练印章（K60：两头互等，死锁）
    if bad: return f'本地慢自检印章过期：{bad}（K35：先在视频工作目录跑 python3 视频/工具/{bad[0]}，通过后重做补丁再推主演练）'
    import 执行效应演练 as Y   # 2026-10-26 K37v2：新规矩没登记演练覆盖，GitHub 主演练报“缺口变多”白跑一轮；本地几秒就查得出
    g = 缺口数 if 缺口数 is not None else len(Y.缺口()); b = json.load(open(Y.GAPB))['缺口'] if os.path.exists(Y.GAPB) else 0
    return f'执行效应演练缺口 {g} 条 > 基线 {b}：新规矩先在 执行效应演练.py 登记演练（python3 视频/工具/执行效应演练.py --状态 看），再做补丁推主演练' if g > b else ''
def 补丁打不上(行, repo=L):
    """K43：镜像工作分支被主会话同步过，旧补丁打不上，GitHub 上全部 job 两分钟就挂。推之前在拉过的工作分支上 git apply --check"""
    m = re.search(r'补丁=(\S+)', 行)
    if not m: return ''
    p = m.group(1); r = subprocess.run(['git', '-C', repo, 'apply', '--check', p], capture_output=True, text=True)
    return '' if r.returncode == 0 else f'补丁 {p} 在工作分支上打不上（K43：主仓库更新过，先合并最新 main 再重做补丁）：{(r.stderr or r.stdout).strip()[-150:]}'
def 待提交补丁(行, repo=L):
    """K50：补丁文件没提交（新文件或改过），GitHub 上打补丁找不到/打的是旧版：随请求一起提交"""
    m = re.search(r'补丁=(\S+)', 行)
    if not m: return []
    r = subprocess.run(['git', '-C', repo, 'status', '--porcelain', '--', m.group(1)], capture_output=True, text=True).stdout.strip()
    return [m.group(1)] if r else []
def 自检():
    f = []
    d = tempfile.mkdtemp(prefix='推请求自检_'); sh = lambda c: subprocess.run(c, shell=True, cwd=d, capture_output=True)
    sh('git init -q && printf "a\\nb\\n" > x.txt && git add x.txt && git -c user.name=t -c user.email=t@t commit -qm 0')
    open(f'{d}/好.diff', 'w').write('--- a/x.txt\n+++ b/x.txt\n@@ -1,2 +1,2 @@\n a\n-b\n+c\n'); open(f'{d}/坏.diff', 'w').write('--- a/x.txt\n+++ b/x.txt\n@@ -1,2 +1,2 @@\n a\n-zzz\n+c\n')
    if not 补丁打不上('门变异 x 补丁=坏.diff', d): f.append('没抓到：补丁在工作分支上打不上还让推（K43）')
    if 补丁打不上('门变异 x 补丁=好.diff', d) or 补丁打不上('主演练', d): f.append('误报：补丁打得上或没有补丁也拦（K43）')
    if 待提交补丁('门变异 x 补丁=好.diff', d) != ['好.diff']: f.append('没抓到：补丁文件没提交，请求照样推（K50）')
    sh('git add 好.diff && git -c user.name=t -c user.email=t@t commit -qm 1')
    if 待提交补丁('门变异 x 补丁=好.diff', d) or 待提交补丁('主演练', d): f.append('误报：补丁已提交或没有补丁也要再提交（K50）')
    shutil.rmtree(d, ignore_errors=True)
    if not 本地慢印章('主演练 补丁=视频/云端/待演练/x.diff', lambda p: p == '执行效应演练.py'): f.append('没抓到：出片守门自检印章过期还让推带补丁的主演练（K35）')
    if 本地慢印章('主演练 补丁=视频/云端/待演练/x.diff', lambda p: p != '彩排.sh', 缺口数=0): f.append('误拦：只有彩排印章过期就不让推主演练（彩排要先有主演练印章，两头互等，K60）')
    if not 本地慢印章('主演练 补丁=视频/云端/待演练/x.diff', lambda p: True, 缺口数=99): f.append('没抓到：演练缺口变多还让推带补丁的主演练')
    if 本地慢印章('主演练 补丁=视频/云端/待演练/x.diff', lambda p: p != '执行效应演练.py', 缺口数=0) or 本地慢印章('声音演练 补丁=x', lambda p: False): f.append('误报：印章有效或不是主演练也拦（K35）')
    return f
def main():
    a = sys.argv[1:]
    if a[:1] == ['--自检']: e = 自检(); print('\n'.join(e) or '推请求 自检通过（本地慢自检印章过期时带补丁的主演练必停，K35；补丁文件没提交随请求提交，K50）'); return 1 if e else 0
    if len(a) < 2: print(__doc__); return 1
    名字, 行 = a[0], a[1]; 注 = a[2] if len(a) > 2 else ''
    e = 本地慢印章(行)
    if e: print('【停止】' + e); return 1
    f = f'视频/云端/请求/{名字}.txt'
    g('pull', '-q', '--no-rebase', '--no-edit', 'origin', B)
    e = 补丁打不上(行)
    if e: print('【停止】' + e); return 1
    if os.path.exists(f'{L}/{f}'): print(f'【停止】请求 {f} 已经有了（只认新加的文件）：换个名字'); return 1
    os.makedirs(f'{L}/视频/云端/请求', exist_ok=True)
    open(f'{L}/{f}', 'w').write((f'# {注}\n' if 注 else '') + 行 + '\n')
    g('add', f, *待提交补丁(行)); c = g('commit', '-qm', f'GitHub 请求：{名字}（{行[:60]}）\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>')   # K50：补丁文件一起提交
    if c.returncode:
        g('reset', '-q', '--', f); os.remove(f'{L}/{f}')   # 提交没成功：请求文件收回，改好了用同一个名字再推
        print('【停止】提交没成功：' + (c.stdout + c.stderr)[-300:]); return 1
    for _ in range(3):
        if g('push', '-q', 'origin', B).returncode == 0: break
        g('pull', '-q', '--no-rebase', '--no-edit', 'origin', B)
    else: print('【停止】推送没成功'); return 1
    t = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
    try: d = json.load(open(账))
    except Exception: d = {}
    d.setdefault('请求', []).append({'名字': 名字, '行': 行, '时刻': t, '提交': g('rev-parse', '--short', 'HEAD').stdout.strip()})
    json.dump(d, open(账, 'w'), ensure_ascii=False)
    print(f'已推请求 {名字}（{t}）。【必须】现在 send_later 约 20 分钟后叫回自己：GitHub 写回结果不会唤醒会话（K34）；结果在 {L}/视频/云端/结果/')
    return 0
if __name__ == '__main__': sys.exit(main())
