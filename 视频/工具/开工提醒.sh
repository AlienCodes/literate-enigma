#!/bin/bash
# SessionStart 钩子（T31）：每次开会话先把必做的事摆出来——不靠记忆。
P=/home/user/postgraduate-vocabulary/视频; [ -d $P ] || P="$CLAUDE_PROJECT_DIR/视频"
python3 $P/工具/方法进化表.py --状态 2>/dev/null   # G65：第一屏先看方法进化趋势和 GitHub 工作流最近结果
python3 $P/工具/证据.py --闲置 --提醒 2>/dev/null   # G71：机制连续两篇该用没用（或建好后第一篇就没用上），第一屏标红
python3 $P/工具/音频首要法则.py --要点 2>/dev/null   # 首要法则（CLAUDE.md 0.，用户 2026-10-25）：开工先读音频要求和全部音频坑
no=$(cat ~/.当前篇 2>/dev/null || cat $P/制作记录/当前篇.txt 2>/dev/null)
echo "【开工必做（T31，程序提醒）】先读 CLAUDE.md 的 T29/T31、视频/工具/草稿流程.md、视频/制作记录/草稿进度.md（只读要用的段落）；动手前在 制作记录/NN.md 写好“## 方法设计”（踩坑核查 [T31] 没写就停）；一次只做一篇，方法一出问题立刻停。"
[ -n "$no" ] && f=$P/制作记录/$no.md && [ -f $f ] && echo "当前篇：$no；方法设计：$(grep -q '预计调用：\s*\S' $f && echo 已写 || echo 未写，先写)；$(grep -E '^- (进行中|收工)' $f | tail -1 | python3 -c 'import sys; print(sys.stdin.read().strip()[:60])')"
[ -n "$no" ] && python3 $P/工具/重点词被去掉.py $no 2>/dev/null
# 规则执行机器（CLAUDE.md 第16条）：装上 git 提交钩子，打印机器状态
for r in /home/user/postgraduate-vocabulary /home/user/literate-enigma; do [ -d $r/视频/工具/githooks ] && git -C $r config core.hooksPath 视频/工具/githooks; done
python3 $P/工具/规则执行核查.py --状态 2>/dev/null
python3 $P/工具/开工必读.py --要点 2>/dev/null
python3 $P/工具/会话开工.py --状态 2>/dev/null   # G63：第一件事 会话开工.py <角色>（没开工不能提交）
[ -n "$no" ] && python3 $P/工具/证据.py --状态 $no 2>/dev/null   # G60：本篇哪些步骤已留使用证据   # G55：先读 视频/开工必读.md 再照它做
python3 $P/工具/报坑.py --状态 2>/dev/null   # G54：待入表、超期的报坑登记
python3 $P/工具/执行效应演练.py --状态 2>/dev/null   # 执行效应（CLAUDE.md 第19条）：开工先看演练是否全挡住，不全挡住先修门再干活
python3 -c "import sys; sys.path.insert(0,'$P/工具'); import 重查记录 as R; q=[n for n in R.欠着() if n in R.已出片()]; print('【存的视频】欠重查或欠重出 4K（G9/G22）：'+(' '.join(q) if q else '无'))" 2>/dev/null
exit 0
