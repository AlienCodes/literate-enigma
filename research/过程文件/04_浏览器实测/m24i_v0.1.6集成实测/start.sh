#!/bin/bash
# Start the VoiceTwin web UI (integration worktree) on port 7876 under gradio 4.24 / py3.9; writes webui.pid.
M=<草稿目录>/m24i
cd "$M" || exit 1
export PYTHONPATH=<仓库>
export BROWSER=true
export FAKE_GSV_CLIP_SLEEP="${FAKE_GSV_CLIP_SLEEP:-0.2}"
nohup <草稿目录>/gsv39/bin/python run_webui.py > webui.log 2>&1 &
echo $! > webui.pid
echo "started pid $(cat webui.pid)"
