#!/bin/bash
# Docs screenshot instance: port 7877, fake RTX 4070 on PATH; writes webui.pid.
cd "<草稿目录>/m24d" || exit 1
export PYTHONPATH=<仓库>
export BROWSER=true
export PATH="<草稿目录>/m24d/bin:$PATH"
export FAKE_GSV_CLIP_SLEEP="${FAKE_GSV_CLIP_SLEEP:-0.1}"
nohup <草稿目录>/gsv39/bin/python run_webui.py > webui.log 2>&1 &
echo $! > webui.pid
echo "started pid $(cat webui.pid)"
