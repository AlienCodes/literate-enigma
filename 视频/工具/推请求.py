#!/usr/bin/env python3
"""推 GitHub 工作流请求的正式入口（K34/G74，2026-10-26）：在镜像工作分支新建 视频/云端/请求/<名字>.txt、提交、推送，
记进本机请求账（~/.云端请求.json），并提醒：GitHub 写回结果不会唤醒会话，推完必须 send_later 约 20 分钟叫回自己；
没约唤醒，收工闸门（钩子/闸门.py 收工）就拦。格式见 视频/云端/请求/说明.md。
用法：python3 视频/工具/推请求.py <名字> "<任务行>" ["# 注释"]    例：推请求.py G72主演练 "主演练 补丁=视频/云端/待演练/G72单线程.diff\""""
import os, sys, json, subprocess, datetime
L = '/home/user/literate-enigma'; B = 'claude/adoring-hamilton-5qskmm'
账 = os.path.expanduser('~/.云端请求.json')
def g(*a): return subprocess.run(['git', '-C', L, *a], capture_output=True, text=True)
def main():
    a = sys.argv[1:]
    if len(a) < 2: print(__doc__); return 1
    名字, 行 = a[0], a[1]; 注 = a[2] if len(a) > 2 else ''
    f = f'视频/云端/请求/{名字}.txt'
    g('pull', '-q', '--no-rebase', '--no-edit', 'origin', B)
    if os.path.exists(f'{L}/{f}'): print(f'【停止】请求 {f} 已经有了（只认新加的文件）：换个名字'); return 1
    os.makedirs(f'{L}/视频/云端/请求', exist_ok=True)
    open(f'{L}/{f}', 'w').write((f'# {注}\n' if 注 else '') + 行 + '\n')
    g('add', f); c = g('commit', '-qm', f'GitHub 请求：{名字}（{行[:60]}）\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>')
    if c.returncode: print('【停止】提交没成功：' + (c.stdout + c.stderr)[-300:]); return 1
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
