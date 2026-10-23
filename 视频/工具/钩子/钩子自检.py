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
if not 拦了('命令', {'tool_input': {'command': 'npx vercel --prod'}}): fails.append('没抓到：没经同意就部署（C1/C2/流16）')
if not 拦了('命令', {'tool_input': {'command': 'git push origin master'}}): fails.append('没抓到：推 master（C1/C2）')
if not 拦了('命令', {'tool_input': {'command': 'cd x && git push -f origin main'}}): fails.append('没抓到：强推（C1/C2）')
if 拦了('命令', {'tool_input': {'command': 'git push -q origin main'}}): fails.append('误拦：正常推送')
if 拦了('命令', {'tool_input': {'command': "echo 'vercel deploy 是什么'"}}): fails.append('误拦：文字里提到部署')
r6 = G.判('发文件后', {'tool_input': {'files': ['/x/a-文本.docx']}}); r6b = G.判('发文件后', {'tool_input': {'files': ['/x/a.mp4']}})
if not (r6 and '打印背景色' in json.dumps(r6, ensure_ascii=False)) or r6b: fails.append('没抓到：发 Word 没提醒打印背景色（W6）')
o = subprocess.run(['bash', os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '开工提醒.sh')], capture_output=True, text=True).stdout
if '【开工必做' not in o or '【规则执行机器】' not in o: fails.append('没抓到：开工提醒没打印（守则1：开工必读、规则执行机器状态）')
shutil.rmtree(tmp)
print('钩子自检：' + ('通过（子代理、发文件、跳过核查、部署、收工闸门和发 Word 提醒：造的违规全部拦下，正常的放行）' if not fails else '失灵！' + '；'.join(fails)))
sys.exit(1 if fails else 0)
