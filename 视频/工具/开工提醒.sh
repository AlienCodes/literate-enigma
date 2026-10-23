#!/bin/bash
# SessionStart 钩子（T31）：每次开会话先把必做的事摆出来——不靠记忆。
P=/home/user/postgraduate-vocabulary/视频; [ -d $P ] || P="$CLAUDE_PROJECT_DIR/视频"
no=$(cat $P/制作记录/当前篇.txt 2>/dev/null)
echo "【开工必做（T31，程序提醒）】先读 CLAUDE.md 的 T29/T31、视频/工具/草稿流程.md、视频/制作记录/草稿进度.md（只读要用的段落）；动手前在 制作记录/NN.md 写好“## 方法设计”（踩坑核查 [T31] 没写就停）；一次只做一篇，方法一出问题立刻停。"
[ -n "$no" ] && f=$P/制作记录/$no.md && [ -f $f ] && echo "当前篇：$no；方法设计：$(grep -q '预计调用：\s*\S' $f && echo 已写 || echo 未写，先写)；$(grep -E '^- (进行中|收工)' $f | tail -1 | cut -c1-90)"
[ -n "$no" ] && python3 $P/工具/重点词被去掉.py $no 2>/dev/null
# 规则执行机器（CLAUDE.md 第16条）：装上 git 提交钩子，打印机器状态
for r in /home/user/postgraduate-vocabulary /home/user/literate-enigma; do [ -d $r/视频/工具/githooks ] && git -C $r config core.hooksPath 视频/工具/githooks; done
python3 $P/工具/规则执行核查.py --状态 2>/dev/null
exit 0
