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
if git diff --cached --name-only | grep -qE '^视频/工具/.*\.(py|sh)$'; then   # G54：推门程序的会话先把超期没入表的坑收进总表
  python3 $P/视频/工具/报坑.py --查 --严 || { echo "【停止】这次推送改了门程序，但有报坑登记超期还没进踩坑总表（G54）：先写进总表、配门"; git reset -q; exit 1; }; fi
big=$(git diff --cached --name-only -z | xargs -0 -r du -b 2>/dev/null | awk '$1>95*1024*1024{print $2}')
[ -z "$big" ] || { echo "【停止】有文件超过 GitHub 单个文件 100MB 上限（G1）：$big——先拆成几段（附 SHA256 和还原脚本）"; git reset -q; exit 1; }
if ! git diff --cached --quiet; then git commit -qm "$1$T"; fi
git pull -q --no-rebase --no-edit origin main   # 2026-10-22：别的会话（每篇新开会话）可能先推了，先合并远端再算差异、再推
(cd $L; git checkout -q -- 视频 2>/dev/null; git pull -q --no-rebase --no-edit origin $B)   # 镜像分支先合并别的会话推的
# G58（2026-10-26 GitHub 化）：GitHub 工作流（github-actions[bot]）写回镜像的印章、结果，先反向拷回主仓库，不被主仓库的旧版本覆盖。
# 只限下面这几样工作流写的文件；镜像上这次提交比主仓库这份新才拷（主仓库后来又改了，以主仓库为准）。
WF='视频/工具/执行效应演练通过.json 视频/工具/执行效应声音演练通过.json 视频/工具/全篇重查通过.json 视频/云端/结果'
for f in $(cd $L; git -c core.quotepath=off ls-files -- $WF); do
  read -r la lt < <(cd $L; git log -1 --format='%an %ct' -- "$f"); pt=$(git log -1 --format=%ct -- "$f" 2>/dev/null); pt=${pt:-0}
  if [ "$la" = 'github-actions[bot]' ] && [ "$lt" -gt "$pt" ] && ! cmp -s "$L/$f" "$P/$f"; then mkdir -p "$(dirname "$P/$f")"; cp "$L/$f" "$P/$f"; git add -- "$f"; echo "回写（G58）：$f（GitHub 工作流结果）"; fi
done
git diff --cached --quiet || git commit -qm "回写：GitHub 工作流结果（G58）$T"
D='视频 最终版4K视频 新版定稿'   # G20：三个都镜像（只镜像 视频/ 时，定稿流水线 ⑥ 中断后用本脚本补推，镜像里的 4K 和文章一直是旧的）
# 2026-10-23：按两边 git 指纹逐文件比对来拷（只拷“这次改动”会漏掉两个会话合并出来的文件）
git -c core.quotepath=off ls-tree -r HEAD $D | awk -F'\t' '{split($1,a," "); print a[3]"\t"$2}' | sort -k2 > /tmp/_p.txt
(cd $L; git -c core.quotepath=off ls-tree -r HEAD $D | awk -F'\t' '{split($1,a," "); print a[3]"\t"$2}' | sort -k2) > /tmp/_l.txt
python3 - "$P" "$L" <<'PY2'
import sys,shutil,os
P,L=sys.argv[1:3]
p=dict(l.rstrip('\n').split('\t')[::-1] for l in open('/tmp/_p.txt')); q=dict(l.rstrip('\n').split('\t')[::-1] for l in open('/tmp/_l.txt'))
for f,h in p.items():
    if q.get(f)!=h: os.makedirs(os.path.dirname(f'{L}/{f}'),exist_ok=True); shutil.copy2(f'{P}/{f}',f'{L}/{f}')
for f in q:
    if f not in p and os.path.exists(f'{L}/{f}'): os.remove(f'{L}/{f}')
PY2
git push -q origin main || { git pull -q --no-rebase --no-edit origin main && git push -q origin main; }   # 别的会话刚推了：合并一次再推
cp $P/CLAUDE.md $L/CLAUDE.md   # CLAUDE.md 以 postgraduate-vocabulary 为准（G11：定稿流水线用它覆盖工作分支，只改工作分支那份会被冲掉）
cd $L; git symbolic-ref -q HEAD >/dev/null || git checkout -q -B $B   # 新容器 L 可能是游离 HEAD：分支挪到 HEAD 再推（2026-10-23 T34 九篇因此停）
git add -A
if ! git diff --cached --quiet; then git commit -qm "镜像：$1$T"; fi
git push -q -u origin $B || { git pull -q --no-rebase --no-edit origin $B && git push -q -u origin $B; }
diff <(git -C $P ls-tree -r HEAD $D | awk '{print $3,$4}') <(git -C $L ls-tree -r HEAD $D | awk '{print $3,$4}') >/dev/null \
  && cmp -s $P/CLAUDE.md $L/CLAUDE.md && [ -z "$(git -C $P status --short)" ] && [ -z "$(git -C $L status --short)" ] \
  && git -C $P fetch -q origin main && git -C $L fetch -q origin $B \
  && git -C $P merge-base --is-ancestor HEAD origin/main && git -C $L merge-base --is-ancestor HEAD origin/$B \
  && echo "两仓库已推送，视频/ 逐文件一致，云端已含这次提交（G2；别的会话紧接着推了也算对）" || { echo "【停止】两仓库 视频/ 不一致、有没提交的改动，或云端与本地不一致（G2）"; exit 1; }
