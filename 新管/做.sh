#!/bin/bash
# 做 NN：一条命令从数据到 1080p 草稿（在出片工作目录下运行）。详见 做.py 开头。
# 用法：bash <新管目录>/做.sh NN [--不推]
H=$(cd "$(dirname "$0")" && pwd)
no=$(printf '%02d' "$((10#$1))"); shift
exec 9>".做_$no.lock"; flock -n 9 || { echo "【停】第${no}篇已经有一条 做/定稿 在跑"; exit 1; }
unset OLD_IV_VOID
exec python3 "$H/做.py" "$no" "$@"
