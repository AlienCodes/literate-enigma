#!/bin/bash
# Stop 钩子（T31，用户 2026-10-16：“一边干活一边记到底花了多少的token……不要靠每次你去记”）：每轮结束自动把当前篇到现在花的 token 写进 制作记录/NN.md。
# 以 postgraduate-vocabulary 为准（工作分支只是镜像，写那边会让两仓库不一致）；后台跑、不挡对话。
P=/home/user/postgraduate-vocabulary/视频; [ -d $P ] || P="$CLAUDE_PROJECT_DIR/视频"
no=$(cat ~/.当前篇 2>/dev/null) || { ( python3 $P/工具/收工记录.py --只会话 >/dev/null 2>&1 & ) ; exit 0; }   # G65：改门、主会话没有当前篇，也记本会话的进化记录（篇 = 角色）
( python3 $P/工具/收工记录.py "$no" --进行中 >/dev/null 2>&1 & ) ; exit 0
