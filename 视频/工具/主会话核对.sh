#!/usr/bin/env bash
# 主会话收到会话回报后一条命令核对（T29 省 token：原来 pull、规则执行核查、欠查、记交接、推送 要 3–4 次调用）
# 用法：bash 视频/工具/主会话核对.sh "交接里要记的一行（可空）"
cd "$(dirname "$0")/../.." || exit 1
git pull -q 2>&1 | tail -1
git -C /home/user/literate-enigma pull -q origin claude/adoring-hamilton-5qskmm 2>&1 | tail -1   # 规则执行核查读镜像的 .claude/settings.json，不拉会误报钩子没配上（2026-10-26 主会话踩过）
timeout 300 python3 视频/工具/规则执行核查.py 2>&1 | tail -1 | cut -c1-60
python3 -c "import sys; sys.path.insert(0,'视频/工具'); import 重查记录 as R; print('欠查:', [n for n in R.欠着() if n in R.已出片()])" 2>&1 | tail -1
if [ -n "$1" ]; then
  python3 - "$1" <<'PY'
import sys; f='视频/制作记录/主会话交接.md'; t=open(f).read(); i=t.find('## 三、')
t=t[:i].rstrip('\n')+'\n- '+sys.argv[1].strip()+'\n\n'+t[i:]; open(f,'w').write(t)
PY
  bash 视频/工具/推送两仓库.sh "主会话交接：${1:0:40}" 2>&1 | tail -1
fi
