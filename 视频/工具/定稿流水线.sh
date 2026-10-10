#!/bin/bash
# 定稿流水线（G8、G9）：用户定稿后，一条命令把 4K 定稿做完、替换旧视频、存进文件夹、备份到两个仓库，任何一步不通过就停。
# 用户 2026-10-10 原话：“最终做完的这个，我们的定稿，最终的定稿视频都要抓紧时间，就是及时去替换掉那些老的视频，然后及时要保存在我们的这个文件夹……
# 而且一定要确定我们的这个音频绝对不能再出问题……坚决要防止再出现以前踩过的那些坑那些问题。”
# 在视频工作目录（含 make_video.py、scripts/NN.json、fonts/）下运行：bash <工具目录>/定稿流水线.sh NN
# 顺序固定（最高铁律第 5 条：先核查，后交付）：
#   ① 出片前核查（踩坑核查、读音、词尾辅音、停顿位置、纯人声等，全部带自检）
#   ② 出 4K（VIDEO_S=2）
#   ③ 出片后核查（自动音频检查、响度、纯人声、句间停顿、独立复核、高亮同步，全部带自检）
#   ④ 生成对照文本（先过踩坑核查文本阶段；把脚本存进仓库、存为已发版本）、同步文章与速查表
#   ⑤ 归档：替换 视频/视频/NN.mp4 和 最终版4K视频/ 里的旧版本，删掉这一篇的草稿和试听视频（G7），
#      再跑 定稿视频核对：视频里每一屏与现行定稿脚本重新画的一致、声音与现行脚本重新出的逐样本一致（G9）
#   ⑥ 存核查记录；提交推送 postgraduate-vocabulary；镜像同步、提交推送 literate-enigma；定稿视频核对 --只查清点和镜像
set -o pipefail
no=$(printf '%02d' "$((10#$1))"); T=/home/user/postgraduate-vocabulary/视频/工具; P=/home/user/postgraduate-vocabulary; L=/home/user/literate-enigma
BR=claude/adoring-hamilton-5qskmm; W=$(pwd); LOG=$W/定稿流水线_$no; mkdir -p "$LOG"
stop() { echo "【停止】$1（记录在 $LOG）"; exit 1; }
step() { echo "== $(date +%H:%M:%S) $1"; }
push() {  # 网络失败才重试（2、4、8、16 秒）
  for t in 0 2 4 8 16; do sleep $t; git push -q -u origin "$1" && return 0; done; return 1; }
# 同一篇只能有一条流水线在跑（2026-10-10 第09篇第二轮：一条用 & 启动、以为没起来又启动一条，两条同时写 09.mp4，声音坏了，出片后核查拦下；pgrep 认不出中文路径，没发现还有一条在跑）
exec 9>"$W/.定稿流水线_$no.lock"; flock -n 9 || { echo "【停止】第${no}篇已经有一条定稿流水线在跑（$W/.定稿流水线_$no.lock 被占用），不能同时跑两条"; exit 1; }
[ -f make_video.py ] && [ -f "scripts/$no.json" ] && [ -d fonts ] || stop "请在视频工作目录下运行（要有 make_video.py、scripts/$no.json、fonts/）"
cmp -s make_video.py $T/make_video.py && cmp -s render.py $T/render.py || stop "工作目录里的 make_video.py / render.py 与仓库工具不一致，先同步（出片和核查必须用同一份程序）"

step "① 出片前核查"; python3 $T/交付核查.py $no 出片前 > "$LOG/出片前.log" 2>&1 || { tail -25 "$LOG/出片前.log"; stop "出片前核查不通过"; }
step "② 出 4K"; VIDEO_S=2 python3 make_video.py scripts/$no.json $no.mp4 > "$LOG/出片.log" 2>&1 || { tail -15 "$LOG/出片.log"; stop "出片失败"; }
step "③ 出片后核查"; python3 $T/交付核查.py $no 出片后 > "$LOG/出片后.log" 2>&1 || { tail -25 "$LOG/出片后.log"; stop "出片后核查不通过"; }
step "④ 对照文本、文章同步"
python3 $T/生成文本.py $no > "$LOG/文本.log" 2>&1 || { tail -15 "$LOG/文本.log"; stop "对照文本生成或文本核查不通过"; }
md=$(ls $P/新版定稿/$no-*.md 2>/dev/null | head -1); [ -n "$md" ] || stop "找不到文章 新版定稿/$no-*.md"
(cd $P && python3 视频/工具/sync_article.py 视频/脚本/$no.json "$md") > "$LOG/文章同步.log" 2>&1 || stop "文章同步失败"
step "⑤ 归档（替换旧视频 + 定稿视频核对）"
cp $no.mp4 $P/视频/视频/$no.mp4 || stop "复制失败"
python3 $T/归档定稿视频.py $no > "$LOG/归档.log" 2>&1 || { tail -15 "$LOG/归档.log"; stop "归档或定稿视频核对不通过"; }
step "⑥ 存记录、推送两个仓库"
cat "$LOG/出片前.log" "$LOG/出片后.log" > $P/视频/音频核对/交付核查_${no}_4K定稿.txt
awk '/^① 清点/{f=1} f' "$LOG/归档.log" > $P/视频/音频核对/定稿视频核对_${no}.txt
MSG="第${no}篇 4K 定稿：出片前/出片后核查全部通过，替换旧视频归档，定稿视频核对逐屏逐样本通过（定稿流水线）

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01XbsiuYS9p9y2vNiB4h6ZZU"
(cd $P && git add -A && { git diff --cached --quiet || git commit -q -m "$MSG"; } && push main) || stop "postgraduate-vocabulary 提交或推送失败"
(cd $P && python3 视频/工具/镜像同步.py > "$LOG/镜像.log" 2>&1 && cp CLAUDE.md $L/CLAUDE.md && cp 新版定稿/*.md $L/新版定稿/) || stop "镜像同步失败"
(cd $L && git add -A 视频 最终版4K视频 新版定稿 CLAUDE.md && { git diff --cached --quiet || git commit -q -m "镜像：$MSG"; } && push $BR) || stop "literate-enigma 提交或推送失败"
python3 $T/定稿视频核对.py --只查清点和镜像 > "$LOG/镜像核对.log" 2>&1 || { tail -10 "$LOG/镜像核对.log"; stop "镜像核对不通过"; }
tail -3 "$LOG/归档.log"; echo "第${no}篇 定稿流水线全部完成：最终版4K视频/ 已替换为这一版，两个仓库已推送，各处拷贝逐字节一致"
