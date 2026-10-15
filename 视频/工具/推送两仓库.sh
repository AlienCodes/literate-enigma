#!/bin/bash
# 一条命令备份两个仓库（2026-10-15 方法升级，省 token）：提交 postgraduate-vocabulary → 只把这次改动的 视频/ 文件拷进 literate-enigma
# → 提交 → 推送两边 → 用 git 记录的文件指纹比对两边 视频/ 逐文件一致（不再逐个读大视频，几秒完成）。
# 用法：bash 视频/工具/推送两仓库.sh "提交说明"
set -e
P=/home/user/postgraduate-vocabulary; L=/home/user/literate-enigma; B=claude/adoring-hamilton-5qskmm
T=$'\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\nClaude-Session: https://claude.ai/code/session_01XbsiuYS9p9y2vNiB4h6ZZU'
cd $P; git add -A 视频
if ! git diff --cached --quiet; then git commit -qm "$1$T"; fi
git -c core.quotepath=off diff --name-status origin/main HEAD -- 视频 > /tmp/_chg.txt || true
while IFS=$'\t' read -r st f g; do
  case $st in D) rm -f "$L/$f";; R*) rm -f "$L/$f"; f=$g; mkdir -p "$L/$(dirname "$f")"; cp "$P/$f" "$L/$f";; *) mkdir -p "$L/$(dirname "$f")"; cp "$P/$f" "$L/$f";; esac
done < /tmp/_chg.txt
git push -q origin main
cd $L; git add -A
if ! git diff --cached --quiet; then git commit -qm "镜像：$1$T"; fi
git push -q -u origin $B
diff <(git -C $P ls-tree -r HEAD 视频 | awk '{print $3,$4}') <(git -C $L ls-tree -r HEAD 视频 | awk '{print $3,$4}') >/dev/null \
  && [ -z "$(git -C $P status --short)" ] && [ -z "$(git -C $L status --short)" ] \
  && echo "两仓库已推送，视频/ 逐文件一致" || { echo "【停止】两仓库 视频/ 不一致或有没提交的改动"; exit 1; }
