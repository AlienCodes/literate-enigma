#!/bin/bash
# 一条命令备份两个仓库（2026-10-15 方法升级，省 token）：提交 postgraduate-vocabulary → 只把这次改动的 视频/ 文件拷进 literate-enigma
# → 提交 → 推送两边 → 用 git 记录的文件指纹比对两边 视频/ 逐文件一致（不再逐个读大视频，几秒完成）。
# 用法：bash 视频/工具/推送两仓库.sh "提交说明"
set -e
exec 9>${PUSH_LOCK:-/tmp/推送两仓库.lock}; flock 9   # 几篇同时做时排队推送（推送自检用自己的锁，否则在推送里跑自检会自己等自己）
P=${PUSH_P:-/home/user/postgraduate-vocabulary}; L=${PUSH_L:-/home/user/literate-enigma}; B=${PUSH_B:-claude/adoring-hamilton-5qskmm}   # PUSH_* 只给 推送自检.py 在假仓库里测用
T=$'\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\nClaude-Session: https://claude.ai/code/session_01XbsiuYS9p9y2vNiB4h6ZZU'
cd $P
# 规则执行机器（CLAUDE.md 第16条）：提交前先过；git 提交钩子也装上（新容器、别的会话同样生效）
git -C $P config core.hooksPath 视频/工具/githooks; git -C $L config core.hooksPath 视频/工具/githooks 2>/dev/null
python3 $P/视频/工具/规则执行核查.py || { echo "【停止】规则执行核查不通过，不推送（先给新规矩、新坑配好门和自检）"; exit 1; }
git add -A 视频 CLAUDE.md 新版定稿   # 新版定稿：文章本身也会改（撞词去掉重点词等）；路径不存在 git 会报错，set -e 当场停（G3：不许悄悄没提交）
big=$(git diff --cached --name-only -z | xargs -0 -r du -b 2>/dev/null | awk '$1>95*1024*1024{print $2}')
[ -z "$big" ] || { echo "【停止】有文件超过 GitHub 单个文件 100MB 上限（G1）：$big——先拆成几段（附 SHA256 和还原脚本）"; git reset -q; exit 1; }
if ! git diff --cached --quiet; then git commit -qm "$1$T"; fi
git pull -q --no-rebase --no-edit origin main   # 2026-10-22：别的会话（每篇新开会话）可能先推了，先合并远端再算差异、再推
(cd $L; git checkout -q -- 视频 2>/dev/null; git pull -q --no-rebase --no-edit origin $B)   # 镜像分支先合并别的会话推的
# 2026-10-23：按两边 git 指纹逐文件比对来拷（只拷“这次改动”会漏掉两个会话合并出来的文件）
git -c core.quotepath=off ls-tree -r HEAD 视频 | awk -F'\t' '{split($1,a," "); print a[3]"\t"$2}' | sort -k2 > /tmp/_p.txt
(cd $L; git -c core.quotepath=off ls-tree -r HEAD 视频 | awk -F'\t' '{split($1,a," "); print a[3]"\t"$2}' | sort -k2) > /tmp/_l.txt
python3 - "$P" "$L" <<'PY2'
import sys,shutil,os
P,L=sys.argv[1:3]
p=dict(l.rstrip('\n').split('\t')[::-1] for l in open('/tmp/_p.txt')); q=dict(l.rstrip('\n').split('\t')[::-1] for l in open('/tmp/_l.txt'))
for f,h in p.items():
    if q.get(f)!=h: os.makedirs(os.path.dirname(f'{L}/{f}'),exist_ok=True); shutil.copy2(f'{P}/{f}',f'{L}/{f}')
for f in q:
    if f not in p and os.path.exists(f'{L}/{f}'): os.remove(f'{L}/{f}')
PY2
git push -q origin main
cp $P/CLAUDE.md $L/CLAUDE.md   # CLAUDE.md 以 postgraduate-vocabulary 为准（G11：定稿流水线用它覆盖工作分支，只改工作分支那份会被冲掉）
cd $L; git add -A
if ! git diff --cached --quiet; then git commit -qm "镜像：$1$T"; fi
git push -q -u origin $B
diff <(git -C $P ls-tree -r HEAD 视频 | awk '{print $3,$4}') <(git -C $L ls-tree -r HEAD 视频 | awk '{print $3,$4}') >/dev/null \
  && cmp -s $P/CLAUDE.md $L/CLAUDE.md && [ -z "$(git -C $P status --short)" ] && [ -z "$(git -C $L status --short)" ] \
  && git -C $P fetch -q origin main && git -C $L fetch -q origin $B \
  && [ "$(git -C $P rev-parse HEAD)" = "$(git -C $P rev-parse origin/main)" ] && [ "$(git -C $L rev-parse HEAD)" = "$(git -C $L rev-parse origin/$B)" ] \
  && echo "两仓库已推送，视频/ 逐文件一致，云端与本地一致（G2）" || { echo "【停止】两仓库 视频/ 不一致、有没提交的改动，或云端与本地不一致（G2）"; exit 1; }
