#!/bin/bash
# Stop 钩子（T31，用户 2026-10-16：“一边干活一边记到底花了多少的token……不要靠每次你去记”）：每轮结束自动把当前篇到现在花的 token 写进 制作记录/NN.md。
# 以 postgraduate-vocabulary 为准（工作分支只是镜像，写那边会让两仓库不一致）；后台跑、不挡对话。
P=/home/user/postgraduate-vocabulary/视频; [ -d $P ] || P="$CLAUDE_PROJECT_DIR/视频"
no=$(cat ~/.当前篇 2>/dev/null) || exit 0   # 只认本容器自己的当前篇：仓库那份是别的会话写的，退回去读它会把 token 记进别人的篇（2026-10-23 新会话串进 23.md）
( python3 $P/工具/收工记录.py "$no" --进行中 >/dev/null 2>&1 & ) ; exit 0
