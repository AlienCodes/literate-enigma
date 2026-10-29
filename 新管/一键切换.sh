#!/bin/bash
# 一键切换到新管（主会话 2026-10-29 用户亲口同意后跑；用户原话已在 用户同意记录）。在当前 origin/main 上一次做完，不提交：
#   拷新管 → K102（读音核对 自检）→ 切换.py --停用（含 ② 报坑超期只提醒、K76/K101、K97、G35、推送合并、冻结时刻）→ 提交前钩子只查快测印章
#   → CLAUDE.md 一页版 + 视频/用户原话.md（先存原话、核对 0 丢）+ 第一条“永远的大坑（病毒）” → 规则表、写稿须知 重生成
#   → 快测（盖印章）→ 做.sh 27 --不推 回归（做完把它在主仓库留下的草稿、疑点表、记录改动全部还原）→ 打印结论
# 用法：bash 一键切换.sh <主仓库根目录> <出片工作目录（…/video）>
set -o pipefail
P=$(cd "$1" && pwd); W=$(cd "$2" && pwd); H=$(cd "$(dirname "$0")" && pwd); L=$(dirname "$H"); T=$P/视频/工具
stop() { echo "【停】$1"; exit 1; }
RES=()
[ -f "$T/交付核查.py" ] || stop "$P 不是主仓库根目录"
[ -f "$W/make_video.py" ] || stop "$W 不是出片工作目录（要有 make_video.py；先 准备机器.sh）"

echo "== ① 拷新管"
rm -rf "$T/新管" && cp -r "$H" "$T/新管" && sed -i '/^快测通过.json$/d' "$T/新管/.gitignore" || stop "拷新管失败"
RES+=("新管已拷进 视频/工具/新管（快测印章随提交进仓库）")

echo "== ② K102 读音核对 自检"
if grep -q "读音改正生效（" "$T/读音核对.py"; then
  RES+=("K102 已在 main 上")
else
  (cd "$P" && git apply "$L/改门待演练/K102读音自检.diff") || stop "K102 补丁打不上"
  RES+=("K102 已打")
fi

echo "== ③ 切换.py --停用"
python3 "$T/新管/切换.py" "$T" --停用 || stop "切换失败（锚对不上或没有同意记录）"
RES+=("切换：$(cat "$T/管道.json")")

echo "== ④ 提交前钩子只查快测印章（主会话已批：命令、发文件、子代理、收工闸门不动）"
python3 - "$T" <<'PY' || stop "改钩子失败"
import sys; t = sys.argv[1]; p = f'{t}/githooks/pre-commit'; s = open(p).read()
加 = '''if python3 -c "import sys;sys.path.insert(0,'$d/视频/工具');sys.exit(0 if __import__('管道').看门停用() else 1)" 2>/dev/null; then
  python3 "$d/视频/工具/新管/印章.py" || { echo "【停止】快测印章对不上，不能提交：先 python3 视频/工具/新管/快测.py"; exit 1; }; exit 0
fi
'''
if 加 not in s:
    a = s.index('|| exit 0\n') + len('|| exit 0\n'); s = s[:a] + 加 + s[a:]; open(p, 'w').write(s)
PY
RES+=("提交前钩子：看门停用时只查 新管/印章.py")

echo "== ⑤ CLAUDE.md 一页版 + 用户原话存档"
cp "$P/CLAUDE.md" /tmp/旧CLAUDE_$$.md
python3 "$T/新管/原话存档.py" --写入 /tmp/旧CLAUDE_$$.md "$P/视频/用户原话.md" "$T/新管/原话_20261028.md" > /tmp/原话_$$.log || { cat /tmp/原话_$$.log; stop "原话存档有丢"; }
python3 - "$P" "$T" <<'PY' || stop "写 CLAUDE.md 失败"
import sys; P, T = sys.argv[1:3]
大坑原话 = "你这是怎么做的呀？你做一个机制你都做不好，然后你你看你你做出来这么一个机制，本来我们是要优化的，结果被你弄得越来越烂了。然后动不动被一层这个东西卡住好几个小时，动不动被那个东西卡住好几个小时，你到底会不会做这个东西啊？把这个东西作为一个永远的教训给我记录起来以后永远不要再犯这个毛病，这是一个绝对的超级无敌大坑，好吗？这个东西它很而且这个东西它很耗token，而且是没有用的一个东西，你把这个把这个东西给我彻底彻底的杜绝以后永远永远永永远再犯，把这个东西给我彻底记住，把这个东西给我彻底记住，这个东西是永远的坑，你知道吗？这是一个特别特别无敌巨大的坑，把这个东西给我彻底彻底弄掉，作为一个病毒，以后永远防范。"
一刀切 = "直接一刀切把它砍掉了……所有的东西都直接一刀切掉……全是误报"
c = open(f'{T}/新管/CLAUDE.一页.md').read()
坑 = ('**永远的大坑（病毒）**（用户 2026-10-29 原话：“' + 大坑原话 + '”）\n'
     '① 绝不再造“检查的检查”（看门、证据链、闲置报警、用上核查、门变异、演练印章、时限门、彩排这类不看视频本身的东西）。\n'
     '② 检查只查视频本身（声音、文字、画面）；改检查只用快测验证，不等 GitHub。\n'
     '③ 任何检查误报，当天修好、配坏样本；一道检查让流程停了、却不是视频本身的问题，当场砍掉或改掉，不许让它再卡第二次。\n\n')
a = c.index('0. 首要法则'); b = c.index('\n', a) + 1
c = c[:b] + '\n' + 坑 + c[b:]
open(f'{P}/CLAUDE.md', 'w').write(c)
u = open(f'{P}/视频/用户原话.md').read()
u += '\n## 2026-10-29 切换（用户原话，主会话记）\n- “' + 大坑原话 + '”\n- “' + 一刀切 + '”\n- “同意切换到新系统，停用旧的看门检查”\n'
open(f'{P}/视频/用户原话.md', 'w').write(u)
PY
python3 "$T/新管/原话存档.py" --查 /tmp/旧CLAUDE_$$.md "$P/视频/用户原话.md" | tail -1
RES+=("CLAUDE.md 一页版（$(wc -c < "$P/CLAUDE.md") 字节，第一条永远的大坑）；视频/用户原话.md：$(python3 "$T/新管/原话存档.py" --查 /tmp/旧CLAUDE_$$.md "$P/视频/用户原话.md" | tail -1)")

echo "== ⑥ 规则表、写稿须知 重生成"
python3 "$T/新管/生成规则表.py" --写入 | tail -2 && python3 "$T/新管/生成写稿须知.py" --写入 || stop "规则表或写稿须知生成失败"
RES+=("规则表：$(python3 -c "import json;t=json.load(open('$T/新管/规则表.json'));print(len(t['规则']), '条，版本', t['版本'])")")

echo "== ⑦ 快测（约 5 分钟）"
python3 "$T/出片指纹.py" --拷 "$W" > /dev/null
(cd "$W" && XG_WORK="$W" python3 "$T/新管/快测.py") 2>&1 | tail -14 | tee /tmp/快测_$$.log
grep -q "快测通过" /tmp/快测_$$.log && RES+=("快测：$(tail -1 /tmp/快测_$$.log)") || { RES+=("快测：不通过（见上）"); QBAD=1; }

echo "== ⑧ 做.sh 27 --不推 回归"
BEFORE=$(cd "$P" && git -c core.quotepath=off status --porcelain | sort)
(cd "$W" && XG_P="$P" bash "$T/新管/做.sh" 27 --不推) 2>&1 | tail -12 | tee /tmp/做27_$$.log
grep -q "做完" /tmp/做27_$$.log && RES+=("做.sh 27：$(grep '做完' /tmp/做27_$$.log | head -1)") || { RES+=("做.sh 27：停了（见上）"); ZBAD=1; }
AFTER=$(cd "$P" && git -c core.quotepath=off status --porcelain | sort)
comm -13 <(echo "$BEFORE") <(echo "$AFTER") | while IFS= read -r l; do f="${l:3}"; f="${f%\"}"; f="${f#\"}"
  case "$l" in '??'*) rm -rf "$P/$f";; *) git -C "$P" checkout -q -- "$f";; esac; done   # 做.sh 是回归：它在主仓库留下的草稿、疑点表、记录改动一律还原
RES+=("做.sh 留在主仓库的改动已还原（$(comm -13 <(echo "$BEFORE") <(echo "$AFTER") | wc -l) 处）")

echo; echo "======== 一键切换结论（没有提交）========"
for x in "${RES[@]}"; do echo "- $x"; done
echo "- 主仓库改动：$(cd "$P" && git status --porcelain | wc -l) 处；看过没问题就提交、推送两仓库（推送两仓库.sh 停用分支：查印章 + 报坑 --查）"
[ -n "$QBAD$ZBAD" ] && { echo "【有不通过的，先别提交】"; exit 1; }
exit 0
