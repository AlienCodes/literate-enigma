#!/bin/bash
# 推送两仓库（新管外壳）：几个会话同时推时，推完的“两边一致”核对（G2）可能因为别人正好在两次推送之间推了而不一致；
# 这种情况自动从头再推一遍（拉两边、重拷、再推），最多 5 遍；别的停照旧停。追加型记录的合并冲突由 合并追加.py 在 推送两仓库.sh 里自动解决。
# 用法：bash 新管/推送.sh "说明"
H=$(cd "$(dirname "$0")" && pwd); [ -f "$(dirname $H)/推送两仓库.sh" ] && S=$(dirname $H)/推送两仓库.sh || S=${XG_TOOLS:-$(dirname $H)/视频/工具}/推送两仓库.sh
for i in 1 2 3 4 5; do
  o=$(bash "$S" "$1" 2>&1); rc=$?; echo "$o" > "${TMPDIR:-/tmp}/推送_第${i}遍.log"; echo "$o" | tail -3
  [ $rc -eq 0 ] && exit 0
  echo "$o" | grep -qE "【停止】两|rejected|fetch first|non-fast-forward|cannot lock ref|Could not read from remote|unable to access" || exit $rc   # 只有“别人正好在中间推了”（G2 两边不一致、推送被拒）和网络这几种自动重推
  P=${PUSH_P:-/home/user/postgraduate-vocabulary}; L=${PUSH_L:-/home/user/literate-enigma}
  for r in $P $L; do git -C $r merge --abort 2>/dev/null; done   # 上一遍停在半截合并：先退回，再从头推
  echo "（第 $i 遍：两边一致核对没过，多半是别的会话正好在中间推了，自动重推）"; sleep $((i * 2 + RANDOM % 3))
done; exit 1
