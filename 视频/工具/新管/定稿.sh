#!/bin/bash
# 定稿 NN：同一根管子出 4K、归档、推送（在出片工作目录下运行）。用户说定稿、主会话把原话记进 用户同意记录 后才跑。
# 和 做.sh 的区别：出 4K；疑点必须清零（出片前/出片后核查全部通过 = 文本“？”为 0、响度骤降有确认）；
# 成片指纹：数据、声音必须和用户看过的草稿（制作记录/NN_做指纹.json）一致；然后归档 → 定稿视频核对 → 推两仓库 → 镜像核对。
# 用法：bash <新管目录>/定稿.sh NN
H=$(cd "$(dirname "$0")" && pwd); [ -f "$(dirname $H)/交付核查.py" ] && T0=$(dirname $H) || T0=$(dirname $H)/视频/工具
T=${XG_TOOLS:-$T0}; P=${XG_P:-/home/user/postgraduate-vocabulary}; L=${XG_L:-/home/user/literate-enigma}; BR=claude/adoring-hamilton-5qskmm
no=$(printf '%02d' "$((10#$1))"); W=$(pwd); LOG=$W/定稿_$no; mkdir -p "$LOG"; export XG_TOOLS=$T; unset OLD_IV_VOID
t0=$(date +%s)
stop() { echo "【停】$1（$(( $(date +%s) - t0 )) 秒；记录在 $LOG）"; exit 1; }
step() { echo "== $(date +%H:%M:%S) $1"; }
push() { for t in 0 2 4 8 16; do sleep $t; git pull -q --no-rebase --no-edit origin "$1"; git push -q -u origin "$1" && return 0; done; return 1; }
exec 9>"$W/.做_$no.lock"; flock -n 9 || stop "第${no}篇已经有一条 做/定稿 在跑"
[ -f make_video.py ] && [ -f "scripts/$no.json" ] && [ -d fonts ] || stop "请在出片工作目录下运行（要有 make_video.py、scripts/$no.json、fonts/）"
python3 $H/印章.py > "$LOG/印章.log" 2>&1 || { cat "$LOG/印章.log"; stop "快测印章对不上"; }
python3 $T/出片指纹.py --核对工作目录 . > /dev/null 2>&1 || { python3 $T/出片指纹.py --拷 . > /dev/null && echo "（工作目录的出片程序比仓库旧，已拷过来，G27）"; } || stop "拷出片程序失败（G27）"
python3 $T/方法进化表.py --门 $no || stop "方法进化（G65）：本篇比前三篇中位数变差，方法复盘里还没有查得到的“进化落地：<提交号|G##|K##>”"
python3 $T/报坑.py --查 > "$LOG/报坑.log" 2>&1 || { grep "✘" "$LOG/报坑.log"; stop "报坑登记有硬问题（撞号、总表新行没取号，G54）"; }
grep -q "超期" "$LOG/报坑.log" && echo "（提醒：有报坑登记超期还没入表，只提醒不拦；用户 2026-10-29：“直接一刀切把它砍掉了”）"
python3 $T/放行口子核查.py --定稿 $no || stop "用户还没说定稿（用户原话记进 用户同意记录.json）"
python3 $T/工作稿核对.py $no || stop "工作目录的脚本是旧稿（G19）"
python3 $T/补对照记录.py $no > /dev/null || stop "补对照记录失败"
[ -f "work_$no/a.wav" ] || { AUDIO_ONLY=1 python3 make_video.py scripts/$no.json $no.mp4 > "$LOG/重建声音.log" 2>&1 || stop "重建声音失败"; }
python3 - "$no" "$P/视频/制作记录/${no}_做指纹.json" <<'PY' || stop "成片指纹对不上：定稿的不是用户看过的那一版（数据或声音变了），先 做.sh 出草稿给用户看"
import sys, json, hashlib, os
no, f = sys.argv[1:3]; h = lambda p: hashlib.sha256(open(p, 'rb').read()).hexdigest()[:16]
if not os.path.exists(f): sys.exit(print(f'没有 {f}（草稿不是 做.sh 出的）') or 1)
z = json.load(open(f)); bad = [k for k, p in (('数据', f'scripts/{no}.json'), ('声音', f'work_{no}/a.wav')) if z[k] != h(p)]
print('成片指纹：' + ('数据、声音与用户看过的草稿一致' if not bad else '变了：' + '、'.join(bad))); sys.exit(1 if bad else 0)
PY
[ -f "$P/视频/视频/草稿1080p/${no}_1080p.mp4" ] && mv "$P/视频/视频/草稿1080p/${no}_1080p.mp4" "$LOG/"   # 用户看过的草稿（指纹已对上）挪进记录：G7 已定稿篇的草稿不许留在 草稿1080p/
step "① 出片前核查（疑点必须清零）"; python3 $T/交付核查.py $no 出片前 > "$LOG/出片前.log" 2>&1 || { grep -A3 "^✘" "$LOG/出片前.log" | head -30; stop "出片前核查不通过（疑点没清零或有错）"; }
step "② 出 4K"; VIDEO_S=2 python3 make_video.py scripts/$no.json $no.mp4 > "$LOG/出片.log" 2>&1 || { tail -15 "$LOG/出片.log"; stop "出片失败"; }
step "③ 出片后核查"; python3 $T/交付核查.py $no 出片后 > "$LOG/出片后.log" 2>&1 || { grep -A3 "^✘" "$LOG/出片后.log" | head -30; stop "出片后核查不通过"; }
step "④ 文本核查、文章同步"
python3 $T/生成文本.py $no $([ -n "$YAOWENBEN" ] && echo --出文档 || echo --只核查) > "$LOG/文本.log" 2>&1 || { tail -15 "$LOG/文本.log"; stop "文本核查不通过"; }
md=$(ls $P/新版定稿/$no-*.md 2>/dev/null | head -1); [ -n "$md" ] || stop "找不到文章 新版定稿/$no-*.md"
(cd $P && python3 视频/工具/sync_article.py 视频/脚本/$no.json "$md") > "$LOG/文章同步.log" 2>&1 || stop "文章同步失败"
[ -n "$XG_NOPUSH" ] && { step "到此为止（XG_NOPUSH：不归档、不推送，验收用）"; ls -la $no.mp4; exit 0; }
step "⑤ 归档（替换旧视频 + 定稿视频核对）"
cp $no.mp4 $P/视频/视频/$no.mp4 || stop "复制失败"
python3 $T/归档定稿视频.py $no > "$LOG/归档.log" 2>&1 || { tail -15 "$LOG/归档.log"; stop "归档或定稿视频核对不通过"; }
step "⑥ 推送两个仓库"
cat "$LOG/出片前.log" "$LOG/出片后.log" > $P/视频/音频核对/交付核查_${no}_4K定稿.txt
awk '/^① 清点/{f=1} f' "$LOG/归档.log" > $P/视频/音频核对/定稿视频核对_${no}.txt
MSG="第${no}篇 4K 定稿（定稿.sh）：出片前/出片后核查全部通过，指纹与草稿一致，归档、定稿视频核对通过

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
exec 7>"${PUSH_LOCK:-/tmp/推送两仓库.lock}"; flock 7   # 与 推送两仓库.sh 同一把锁排队（G17）
(cd $P && git add -A && { git diff --cached --quiet || git commit -q -m "$MSG"; } && push main) || stop "postgraduate-vocabulary 提交或推送失败"
(cd $P && python3 视频/工具/镜像同步.py > "$LOG/镜像.log" 2>&1 && cp CLAUDE.md $L/CLAUDE.md && cp 新版定稿/*.md $L/新版定稿/) || stop "镜像同步失败"
(cd $L && { git symbolic-ref -q HEAD >/dev/null || git checkout -q -B $BR; } && git add -A 视频 最终版4K视频 新版定稿 CLAUDE.md && { git diff --cached --quiet || git commit -q -m "镜像：$MSG"; } && push $BR) || stop "literate-enigma 提交或推送失败"
flock -u 7
python3 $T/定稿视频核对.py --只查清点和镜像 > "$LOG/镜像核对.log" 2>&1 || { tail -10 "$LOG/镜像核对.log"; stop "镜像核对不通过"; }
python3 $T/缓存进仓库核对.py $no || stop "这一篇用到的配音缓存没全进仓库（G51）"
if python3 $T/全篇核查.py --欠着; then step "⑦ 出片程序改过：全篇重查（铁4）"; python3 $T/全篇核查.py --视频 > "$LOG/全篇重查.log" 2>&1 && tail -1 "$LOG/全篇重查.log" || { tail -6 "$LOG/全篇重查.log"; echo "【欠着】全篇重查没过（铁4）"; }; fi
echo "第${no}篇 定稿完成（$(( $(date +%s) - t0 )) 秒）：4K 已归档替换，两个仓库已推送，镜像一致"
