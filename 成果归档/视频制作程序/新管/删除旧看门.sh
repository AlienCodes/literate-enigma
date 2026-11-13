#!/bin/bash
# 删除旧看门（用户 2026-10-29：“把之前那些臃肿的……这检查那检查会把我们拖很久的那些所有东西全都给我直接砍掉，全都删掉，全都不要了”；
# “能卡住出稿、出片的只有质量问题（声音、文字、画面）；质量没问题，任何东西都不许卡”）。在主仓库上一次做完，不提交：
#   ① 删 8 套看门机制的程序和数据（删除清单.txt）→ ② 打补丁 删除旧看门.diff（调用点、快测、印章自动跑快测、只提醒的改动）
#   → ③ 重新生成 音频首要法则.md、写稿须知.md → ④ 快测（盖印章）→ ⑤ 做.sh 27 --不推 回归（做完把它在主仓库留下的改动还原）→ 打印结论
# 用法：bash 删除旧看门.sh <主仓库根目录> <出片工作目录（…/video）>
set -o pipefail
P=$(cd "$1" && pwd); W=$(cd "$2" && pwd); H=$(cd "$(dirname "$0")" && pwd); T=$P/视频/工具
stop() { echo "【停】$1"; exit 1; }
RES=()
[ -f "$T/交付核查.py" ] || stop "$P 不是主仓库根目录"
[ -f "$W/make_video.py" ] || stop "$W 不是出片工作目录（要有 make_video.py）"
[ -f "$T/新管/印章.py" ] || stop "主仓库还没切换到新管"

echo "== ① 先试补丁（不改任何文件）"
(cd "$P" && git apply --check "$H/删除旧看门.diff") || stop "补丁打不上（主仓库这些文件和补丁的底不一样）：把 git apply --check 的报错发给精简会话"

echo "== ② 删程序和数据"
n=0; while IFS= read -r f; do [ -n "$f" ] && [ -e "$P/$f" ] && { git -C "$P" rm -r -q -- "$f" || stop "删 $f 失败"; n=$((n + 1)); }; done < "$H/删除清单.txt"
RES+=("删了 $n 项（删除清单.txt）")

echo "== ③ 打补丁"
(cd "$P" && git apply "$H/删除旧看门.diff") || stop "补丁打不上"
RES+=("补丁：$(cd "$P" && git apply --numstat "$H/删除旧看门.diff" | wc -l) 个文件")

echo "== ④ 重新生成 音频首要法则.md、写稿须知.md"
python3 "$T/音频首要法则.py" | tail -1 && python3 "$T/新管/生成写稿须知.py" --写入 || stop "重新生成失败"

echo "== ⑤ 快测（约 5 分钟）"
python3 "$T/出片指纹.py" --拷 "$W" > /dev/null
(cd "$W" && XG_WORK="$W" python3 "$T/新管/快测.py") 2>&1 | tail -14 | tee /tmp/快测_$$.log
grep -q "快测通过" /tmp/快测_$$.log && RES+=("快测：$(tail -1 /tmp/快测_$$.log)") || { RES+=("快测：不通过（见上）"); QBAD=1; }

echo "== ⑥ 做.sh 27 --不推 回归"
cp "$P/视频/脚本/27.json" "$W/scripts/27.json"
BEFORE=$(cd "$P" && git -c core.quotepath=off status --porcelain | sort)
(cd "$W" && XG_P="$P" bash "$T/新管/做.sh" 27 --不推) > /tmp/做27_$$.log 2>&1; grep -v "人看" /tmp/做27_$$.log | tail -12   # 全文存下再判（疑点多时 tail 会把“做完”那行截掉）
grep -q "做完" /tmp/做27_$$.log && RES+=("做.sh 27：$(grep '做完' /tmp/做27_$$.log | head -1)") || { RES+=("做.sh 27：停了（见上）"); ZBAD=1; }
AFTER=$(cd "$P" && git -c core.quotepath=off status --porcelain | sort)
comm -13 <(echo "$BEFORE") <(echo "$AFTER") | while IFS= read -r l; do f="${l:3}"; f="${f%\"}"; f="${f#\"}"
  case "$l" in '??'*) rm -rf "$P/$f";; *) git -C "$P" checkout -q -- "$f";; esac; done   # 回归：做.sh 留在主仓库的草稿、疑点表、记录改动一律还原

echo; echo "======== 删除旧看门 结论（没有提交）========"
for x in "${RES[@]}"; do echo "- $x"; done
echo "- 主仓库改动：$(cd "$P" && git status --porcelain | wc -l) 处；看过没问题就提交、推送两仓库"
[ -n "$QBAD$ZBAD" ] && { echo "【有不通过的，先别提交】"; exit 1; }
exit 0
