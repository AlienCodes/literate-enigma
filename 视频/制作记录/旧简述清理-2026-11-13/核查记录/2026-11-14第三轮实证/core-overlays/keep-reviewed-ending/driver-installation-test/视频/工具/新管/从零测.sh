#!/bin/bash
# 验收 ④：全新浅克隆从零跑 做.sh 27 一次通过（K78/K89 那类“新容器缺东西”）。
# 浅克隆镜像分支 → 准备机器.sh 搭工作目录（重新下载配音模型、拷缓存）→ 快测（盖印章）→ 做.sh 27 --不推。
# 用法：bash 从零测.sh <空目录>   （本容器的 /home/user/postgraduate-vocabulary 链接临时指向这份克隆，跑完改回）
set -e; D=$(mkdir -p "$1" && cd "$1" && pwd); H=$(cd "$(dirname "$0")" && pwd); t0=$(date +%s)
BR=claude/adoring-hamilton-5qskmm; OLD=$(readlink /home/user/postgraduate-vocabulary || true)
trap '[ -n "$OLD" ] && ln -sfn "$OLD" /home/user/postgraduate-vocabulary; echo "（$(( $(date +%s) - t0 )) 秒）"' EXIT
echo "== 浅克隆"; git clone -q --depth 1 -b $BR https://github.com/AlienCodes/literate-enigma "$D/L"
ln -sfn "$D/L" /home/user/postgraduate-vocabulary
echo "== 准备机器"; bash "$D/L/视频/工具/环境/准备机器.sh" "$D/L" "$D/机" > "$D/准备.log" 2>&1 || { tail -5 "$D/准备.log"; exit 1; }; tail -1 "$D/准备.log"
[ -d "$D/L/视频/工具/新管" ] || { echo "【停】克隆里没有 视频/工具/新管"; exit 1; }
cd "$D/机/video"
echo "== 快测"; XG_WORK="$D/机/video" python3 "$D/L/视频/工具/新管/快测.py" 2>&1 | tail -14
echo "== 做.sh 27"; XG_P="$D/L" bash "$D/L/视频/工具/新管/做.sh" 27 --不推 2>&1 | tail -12
