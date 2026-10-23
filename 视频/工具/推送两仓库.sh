#!/bin/bash
# 一条命令备份两个仓库（2026-10-15 方法升级，省 token）：提交 postgraduate-vocabulary → 只把这次改动的 视频/ 文件拷进 literate-enigma
# → 提交 → 推送两边 → 用 git 记录的文件指纹比对两边 视频/ 逐文件一致（不再逐个读大视频，几秒完成）。
# 用法：bash 视频/工具/推送两仓库.sh "提交说明"
set -e
exec 9>/tmp/推送两仓库.lock; flock 9   # 几篇同时做时排队推送
P=/home/user/postgraduate-vocabulary; L=/home/user/literate-enigma; B=claude/adoring-hamilton-5qskmm
T=$'\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\nClaude-Session: https://claude.ai/code/session_01XbsiuYS9p9y2vNiB4h6ZZU'
cd $P; git add -A 视频 CLAUDE.md 新版定稿   # 新版定稿：文章本身也会改（撞词去掉重点词等）
if ! git diff --cached --quiet; then git commit -qm "$1$T"; fi
git pull -q --no-rebase --no-edit origin main   # 2026-10-22：别的会话（每篇新开会话）可能先推了，先合并远端再算差异、再推
git -c core.quotepath=off diff --name-status origin/main HEAD -- 视频 > /tmp/_chg.txt || true
(cd $L; git checkout -q -- 视频 2>/dev/null; git pull -q --no-rebase --no-edit origin $B)   # 镜像分支先合并别的会话推的，再拷贝（2026-10-23：先拷后合并会被挡住）
while IFS=$'\t' read -r st f g; do
  case $st in D) rm -f "$L/$f";; R*) rm -f "$L/$f"; f=$g; mkdir -p "$L/$(dirname "$f")"; cp "$P/$f" "$L/$f";; *) mkdir -p "$L/$(dirname "$f")"; cp "$P/$f" "$L/$f";; esac
  [ -e "$L/$f" ] && chmod --reference="$P/$f" "$L/$f"   # 文件权限也一致（14：草稿声音.sh 一边 755 一边 644，两仓库比对不过）
done < /tmp/_chg.txt
git push -q origin main
cp $P/CLAUDE.md $L/CLAUDE.md   # CLAUDE.md 以 postgraduate-vocabulary 为准（G11：定稿流水线用它覆盖工作分支，只改工作分支那份会被冲掉）
cd $L; git add -A
if ! git diff --cached --quiet; then git commit -qm "镜像：$1$T"; fi
git push -q -u origin $B
diff <(git -C $P ls-tree -r HEAD 视频 | awk '{print $3,$4}') <(git -C $L ls-tree -r HEAD 视频 | awk '{print $3,$4}') >/dev/null \
  && cmp -s $P/CLAUDE.md $L/CLAUDE.md && [ -z "$(git -C $P status --short)" ] && [ -z "$(git -C $L status --short)" ] \
  && echo "两仓库已推送，视频/ 逐文件一致" || { echo "【停止】两仓库 视频/ 不一致或有没提交的改动"; exit 1; }
