#!/bin/bash
# usage: bash run_all.sh   (creates and deletes its own workspaces)
cd "$(dirname "$0")"; P=/tmp/gsv39/bin/python; F='^[0-9][0-9]:[0-9][0-9]:[0-9][0-9] |'
rm -rf ws_weak ws_strong; $P setup_ws.py ws_weak/ws | tail -1; cp -r ws_weak ws_strong
echo "== WEAK (no pypinyin/jieba)"; BLOCK_PY=1 $P run_ui.py ws_weak/ws 2>&1 | grep -v "$F"
echo "== AFTER REINSTALL (same ws, full env)"; $P after.py ws_weak/ws 2>&1 | grep -v "$F"
echo "== STRONG (untouched copy, full env)"; $P run_ui.py ws_strong/ws 2>&1 | grep -v "$F"
rm -rf ws_weak ws_strong __pycache__
