#!/usr/bin/env python3
"""钩子自检（规则执行机器当场跑）：每道闸门都造一次违规，必须拦下；正常的必须放行。"""
import os, sys, json, tempfile, subprocess, shutil
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import 闸门 as G
fails = []
def 拦了(kind, d, **k): return G.判(kind, d, **k) is not None
# 子代理（T29）
if not 拦了('子代理', {'tool_name': 'Agent', 'tool_input': {'prompt': '审校全文'}}): fails.append('没抓到：没写理由就派子代理（T29）')
# 发文件（A25）
tmp = tempfile.mkdtemp(); G.回执目录 = f'{tmp}/回执'
a, b = f'{tmp}/a.mp4', f'{tmp}/b.mp3'
open(a, 'wb').write(b'video'); open(b, 'wb').write(b'audio')
if not 拦了('发文件', {'tool_input': {'files': [a, b]}}): fails.append('没抓到：一次发两个声音视频（A25）')
if not 拦了('发文件', {'tool_input': {'files': [a]}}): fails.append('没抓到：发没过核查的视频（A25）')
G.记回执([a], '自检')
if 拦了('发文件', {'tool_input': {'files': [a]}}): fails.append('误拦：过了核查的视频')
open(a, 'ab').write(b'x')
if not 拦了('发文件', {'tool_input': {'files': [a]}}): fails.append('没抓到：核查后又改过的视频（A25）')
if 拦了('发文件', {'tool_input': {'files': [f'{tmp}/s.png']}}): fails.append('误拦：截图')
# 命令
if not 拦了('命令', {'tool_input': {'command': 'git commit --no-verify -m x'}}): fails.append('没抓到：--no-verify 跳过提交前核查')
if not 拦了('命令', {'tool_input': {'command': 'git commit -n -m x'}}): fails.append('没抓到：-n 跳过提交前核查')
if not 拦了('命令', {'tool_input': {'command': 'git config core.hooksPath /dev/null'}}): fails.append('没抓到：改 core.hooksPath')
if 拦了('命令', {'tool_input': {'command': 'git commit -qm "x"'}}): fails.append('误拦：正常提交')
if 拦了('命令', {'tool_input': {'command': "python3 - <<'EOF'\nx = 'git commit --no-verify'\nEOF"}}): fails.append('误拦：heredoc 里的文字（G15）')
# 收工（守则3）
r = f'{tmp}/repo'; os.makedirs(f'{r}/视频')
subprocess.run(['git', 'init', '-q', r]); open(f'{r}/视频/x.md', 'w').write('x')
if not 拦了('收工', {}, 仓库=r): fails.append('没抓到：有没推送的改动就收工（守则3）')
if 拦了('收工', {'stop_hook_active': True}, 仓库=r): fails.append('误拦：已经拦过一次又拦（会死循环）')
shutil.rmtree(tmp)
print('钩子自检：' + ('通过（子代理、发文件、跳过核查、收工四道闸门造的违规全部拦下，正常的放行）' if not fails else '失灵！' + '；'.join(fails)))
sys.exit(1 if fails else 0)
