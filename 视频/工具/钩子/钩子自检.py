#!/usr/bin/env python3
"""钩子自检（规则执行机器当场跑）：每道闸门都造一次违规，必须拦下；正常的必须放行。"""
import os, sys, json, tempfile, subprocess, shutil
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import 闸门 as G
fails = []
def 拦了(kind, d, **k): r = G.判(kind, d, **k); return bool(r) and 'systemMessage' not in r
def 提醒了(kind, d, **k): r = G.判(kind, d, **k); return bool(r) and 'systemMessage' in r
# 子代理（T29）
if not 拦了('子代理', {'tool_name': 'Agent', 'tool_input': {'prompt': '审校全文'}}): fails.append('没抓到：没写理由就派子代理（T29）')
# 发文件（A25）
tmp = tempfile.mkdtemp(); G.回执目录 = f'{tmp}/回执'
G.请求账 = f'{tmp}/云端请求.json'   # K38：自检用隔离的请求账，不读本会话真实的 ~/.云端请求.json（推了请求还没约唤醒时，模拟的正常收工被 K34 闸门误拦）
if G.请求账.startswith(os.path.expanduser('~') + os.sep): fails.append('钩子自检读了真实的请求账（K38）')
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
if 拦了('命令', {'tool_input': {'command': 'git config core.hooksPath'}}): fails.append('误拦：只是读 core.hooksPath')
if not 拦了('命令', {'tool_input': {'command': 'git config --unset core.hooksPath'}}): fails.append('没抓到：取消 core.hooksPath')
if 拦了('命令', {'tool_input': {'command': "python3 - <<'EOF'\nx = 'git commit --no-verify'\nEOF"}}): fails.append('误拦：heredoc 里的文字（G15）')
if 拦了('命令', {'tool_input': {'command': "cat > /tmp/x.md <<'EOF'\ngit push -f origin master\nnpx vercel --prod\nEOF"}}): fails.append('误拦：heredoc 正文里以 git/vercel 开头的行（G15）')
if not 拦了('命令', {'tool_input': {'command': "cat > /tmp/x.md <<'EOF'\nx\nEOF\ngit push -f origin master"}}): fails.append('没抓到：heredoc 结束后的强推（G15 去 heredoc 去多了）')
# 收工（守则3）
r = f'{tmp}/repo'; os.makedirs(f'{r}/视频')
subprocess.run(['git', 'init', '-q', r]); open(f'{r}/视频/x.md', 'w').write('x')
if not 提醒了('收工', {}, 仓库=r): fails.append('没提醒：有没推送的改动就收工（守则3，只提醒）')
if 拦了('收工', {}, 仓库=r): fails.append('误拦：收工只许提醒，不许拦（用户 2026-10-29：只有质量问题能拦）')
if 提醒了('收工', {'stop_hook_active': True}, 仓库=r): fails.append('误报：已经提醒过一次又提醒（会死循环）')
_r3 = f'{tmp}/repo3'; os.makedirs(f'{_r3}/视频/工具'); subprocess.run(['git', 'init', '-q', _r3]); open(f'{_r3}/视频/工具/全篇重查通过.json', 'w').write('{}')
subprocess.run(['git', '-C', _r3, '-c', 'user.name=x', '-c', 'user.email=x@example.com', 'add', '-A']); subprocess.run(['git', '-C', _r3, '-c', 'user.name=x', '-c', 'user.email=x@example.com', 'commit', '-qm', 'x', '--date=2000-01-01T00:00:00'], env={**os.environ, 'GIT_COMMITTER_DATE': '2000-01-01T00:00:00'})
open(f'{_r3}/视频/工具/全篇重查通过.json', 'w').write('{"篇": {}}')   # 已跟踪的进度文件被改了（真实情形）
if 提醒了('收工', {}, 仓库=_r3): fails.append('误拦：全篇重查边查边记的进度文件')
_r4 = f'{tmp}/repo4'; os.makedirs(f'{_r4}/视频/制作记录/方法进化'); subprocess.run(['git', 'init', '-q', _r4]); open(f'{_r4}/视频/制作记录/方法进化/s1.json', 'w').write('{}')
_e4 = {k: v for k, v in os.environ.items() if not k.startswith('GIT_')}
subprocess.run(['git', '-C', _r4, '-c', 'user.name=x', '-c', 'user.email=x@example.com', 'add', '-A'], env=_e4); subprocess.run(['git', '-C', _r4, '-c', 'user.name=x', '-c', 'user.email=x@example.com', 'commit', '-qm', 'y'], env=_e4)
open(f'{_r4}/视频/制作记录/方法进化/s1.json', 'w').write('{"等效": 2}')
if 提醒了('收工', {}, 仓库=_r4): fails.append('误拦：已推过的本会话 token 记录每轮重写（K33）')
open(f'{_r4}/视频/制作记录/方法进化/s2.json', 'w').write('{}')
if not 提醒了('收工', {}, 仓库=_r4): fails.append('没抓到：新的 token 记录从没推过就收工（K33 放得太宽）')
import datetime as _dt   # 方法进化闸门：今天改了工具、方法升级记录没写今天 → 拦；写了 → 放行
q = f'{tmp}/repo2'; os.makedirs(f'{q}/视频/工具'); subprocess.run(['git', 'init', '-q', q])
for k, v in (('user.name', '自检'), ('user.email', 'selftest@example.com')): subprocess.run(['git', '-C', q, 'config', k, v])
open(f'{q}/视频/工具/x.py', 'w').write('x'); open(f'{q}/视频/制作硬性标准与踩坑总结.md', 'w').write('- **方法升级记录**\n- 2000-01-01 旧的\n')
subprocess.run(['git', '-C', q, 'add', '-A']); subprocess.run(['git', '-C', q, 'commit', '-qm', 'x'])
if not 提醒了('收工', {}, 仓库=q): fails.append('没抓到：改了工具没写方法升级记录（守则12）')
open(f'{q}/视频/制作硬性标准与踩坑总结.md', 'w').write(f'- **方法升级记录**\n- {_dt.datetime.utcnow():%Y-%m-%d} 新的\n')
subprocess.run(['git', '-C', q, 'commit', '-qam', 'y'])
if 提醒了('收工', {}, 仓库=q): fails.append('误拦：方法升级记录写了今天的')
if not 拦了('命令', {'tool_input': {'command': 'npx vercel --prod'}}): fails.append('没抓到：没经同意就部署（C1/C2/流16）')
if not 拦了('命令', {'tool_input': {'command': 'git push origin master'}}): fails.append('没抓到：推 master（C1/C2）')
if not 拦了('命令', {'tool_input': {'command': 'cd x && git push -f origin main'}}): fails.append('没抓到：强推（C1/C2）')
if 拦了('命令', {'tool_input': {'command': 'git push -q origin main'}}): fails.append('误拦：正常推送')
if 拦了('命令', {'tool_input': {'command': "echo 'vercel deploy 是什么'"}}): fails.append('误拦：文字里提到部署')
if not 拦了('命令', {'tool_input': {'command': "python3 -c \"from docx import Document; d=Document('用户改.docx')\""}}): fails.append('没抓到：不用 read_docx2 读用户改过的 Word（W2）')
if 拦了('命令', {'tool_input': {'command': 'python3 read_docx2.py 用户改.docx'}}): fails.append('误拦：read_docx2')
if not 拦了('命令', {'tool_input': {'command': 'while pgrep -f "定稿流水线.sh 12" >/dev/null; do sleep 20; done'}}): fails.append('没抓到：pgrep 认不出中文路径（G10）')
if 拦了('命令', {'tool_input': {'command': 'pgrep -f make_video'}}): fails.append('误拦：pgrep 英文字')
r6 = G.判('发文件后', {'tool_input': {'files': ['/x/a-文本.docx']}}); r6b = G.判('发文件后', {'tool_input': {'files': ['/x/a.mp4']}})
if not (r6 and '打印背景色' in json.dumps(r6, ensure_ascii=False)) or r6b: fails.append('没抓到：发 Word 没提醒打印背景色（W6）')
o = subprocess.run(['bash', os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '开工提醒.sh')], capture_output=True, text=True).stdout
if '【开工必做' not in o: fails.append('没抓到：开工提醒没打印（守则1）')
# K16（G59）：绕提交钩子的写法逐个试，必须全拦；正常命令放行
for _c in ['git -c core.hooksPath=/dev/null commit -m x', 'git -c core.HooksPath= commit -m x', 'GIT_CONFIG_COUNT=1 GIT_CONFIG_KEY_0=core.hooksPath GIT_CONFIG_VALUE_0=/x git commit -m x',
           'export GIT_CONFIG_PARAMETERS="x"; git commit -m y', 'env GIT_DIR=/tmp/x git commit -m x', 'rm .git/hooks/pre-commit', 'rm -f 视频/工具/githooks/pre-commit',
           'echo exit 0 > 视频/工具/githooks/pre-commit', 'cat x | tee .git/hooks/pre-commit', 'chmod -x 视频/工具/githooks/pre-commit', 'mv 视频/工具/githooks /tmp/',
           'sed -i s/exit/x/ 视频/工具/githooks/pre-commit', 'git commit --no-veri -m x', 'git -C /x commit -an -m x', 'git config alias.ci "commit --no-verify"',
           'git -c alias.ci=commit ci -m x', 'git commit-tree HEAD^{tree} -m x', 'git update-ref refs/heads/main abc', 'echo Z2l0 | base64 -d | sh', 'alias gc="git commit -n"',
           'cd .git/hooks && rm pre-commit', 'git config --global include.path /tmp/x', 'git --config-env=core.hooksPath=X commit', '/usr/bin/git commit --no-verify -m x',
           'command git commit -n -m x', 'echo x >> ~/.gitconfig', 'ln -sf /dev/null .git/hooks/pre-commit', 'bash -c "git commit --no-verify"']:
    if not 拦了('命令', {'tool_input': {'command': _c}}): fails.append(f'没抓到：绕提交钩子 {_c}（K16）')
for _c in ['git commit -qm "x"', 'git -C /x config core.hooksPath', 'ls .git/hooks 2>/dev/null', 'cat 视频/工具/githooks/pre-commit', 'git add 视频/工具/githooks/pre-commit',
           'du -sh .git', 'git -C x symbolic-ref -q HEAD', 'GIT_LFS_SKIP_SMUDGE=1 git clone x', 'git -c core.quotepath=off status --porcelain', 'git push -n origin main']:
    if 拦了('命令', {'tool_input': {'command': _c}}): fails.append(f'误拦：{_c}（K16）')
if not 拦了('改文件', {'tool_input': {'file_path': '/home/user/postgraduate-vocabulary/.git/hooks/pre-commit'}}): fails.append('没抓到：Edit 改 .git/hooks（K16）')
if 拦了('改文件', {'tool_input': {'file_path': '/home/user/postgraduate-vocabulary/视频/脚本/28.json'}}): fails.append('误拦：改本篇脚本')
shutil.rmtree(tmp)
print('钩子自检：' + ('通过（子代理、发文件、跳过核查、部署、收工闸门和发 Word 提醒：造的违规全部拦下，正常的放行）' if not fails else '失灵！' + '；'.join(fails)))
sys.exit(1 if fails else 0)
