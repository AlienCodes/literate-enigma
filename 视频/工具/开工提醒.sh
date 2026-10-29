#!/bin/bash
# SessionStart 钩子（T31）：每次开会话先把必做的事摆出来——不靠记忆。
P=/home/user/postgraduate-vocabulary/视频; [ -d $P ] || P="$CLAUDE_PROJECT_DIR/视频"
python3 $P/工具/方法进化表.py --状态 2>/dev/null   # G65：第一屏先看方法进化趋势和 GitHub 工作流最近结果
python3 $P/工具/音频首要法则.py --要点 2>/dev/null   # 首要法则（CLAUDE.md 0.，用户 2026-10-25）：开工先读音频要求和全部音频坑
no=$(cat ~/.当前篇 2>/dev/null || cat $P/制作记录/当前篇.txt 2>/dev/null)
echo "【开工必做】只读 视频/工具/新管/写稿须知.md；做片子：写 genNN → bash 视频/工具/新管/做.sh NN（到 1080p）→ 用户说定稿后 bash 视频/工具/新管/定稿.sh NN；一次只做一篇。"
[ -n "$no" ] && f=$P/制作记录/$no.md && [ -f $f ] && echo "当前篇：$no；方法设计：$(grep -q '预计调用：\s*\S' $f && echo 已写 || echo 未写，先写)；$(grep -E '^- (进行中|收工)' $f | tail -1 | python3 -c 'import sys; print(sys.stdin.read().strip()[:60])')"
[ -n "$no" ] && python3 $P/工具/重点词被去掉.py $no 2>/dev/null
# 装上 git 提交钩子（提交前只查快测印章）
for r in /home/user/postgraduate-vocabulary /home/user/literate-enigma; do [ -d $r/视频/工具/githooks ] && git -C $r config core.hooksPath 视频/工具/githooks; done
python3 $P/工具/报坑.py --状态 2>/dev/null   # G54：待入表、超期的报坑登记
python3 -c "import sys; sys.path.insert(0,'$P/工具'); import 重查记录 as R; q=[n for n in R.欠着() if n in R.已出片()]; print('【存的视频】欠重查或欠重出 4K（G9/G22）：'+(' '.join(q) if q else '无'))" 2>/dev/null
exit 0
