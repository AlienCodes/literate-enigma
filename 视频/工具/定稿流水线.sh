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
no=$(printf '%02d' "$((10#$1))"); T=$(cd "$(dirname "$0")" && pwd); P=$(dirname "$(dirname "$T")"); L=/home/user/literate-enigma
BR=claude/adoring-hamilton-5qskmm; W=$(pwd); LOG=$W/定稿流水线_$no; mkdir -p "$LOG"
stop() { echo "【停止】$1（记录在 $LOG）"; python3 "$T/丝滑.py" 记 定稿流水线 "$no" "$1" 2>/dev/null || true; exit 1; }   # K 丝滑记录
[ -n "$OLD_IV_VOID" ] && stop "环境里带着 OLD_IV_VOID（跳过旧区间的草稿开关），定稿不许带：先 unset OLD_IV_VOID（A45 开关，G24）"
step() { echo "== $(date +%H:%M:%S) $1"; }
push() {  # 网络失败才重试（2、4、8、16 秒）
  for t in 0 2 4 8 16; do sleep $t; git pull -q --no-rebase --no-edit origin "$1"; git push -q -u origin "$1" && return 0; done; return 1; }   # 2026-10-22：别的会话可能先推了，先合并远端再推
# 同一篇只能有一条流水线在跑（2026-10-10 第09篇第二轮：一条用 & 启动、以为没起来又启动一条，两条同时写 09.mp4，声音坏了，出片后核查拦下；pgrep 认不出中文路径，没发现还有一条在跑）
exec 9>"$W/.定稿流水线_$no.lock"; flock -n 9 || { echo "【停止】第${no}篇已经有一条定稿流水线在跑（$W/.定稿流水线_$no.lock 被占用），不能同时跑两条"; exit 1; }
# 阶段 B（2026-10-27）云端定稿：GitHub 机器上两个仓库路径都链到同一份镜像检出（准备机器.sh、drill.yml 搭机器），⑥ 不许自己 git push（会把镜像推成 main）：
# 只存记录，提交推送由 drill.yml 写回步骤按 G58 白名单做；云端必须严格缓存（缺一条配音缓存就停、绝不现合成 = 用到的缓存都在仓库里，代替推送后的 缓存进仓库核对）
YUN=; [ "$(readlink -f $P)" = "$(readlink -f $L)" ] && YUN=1 && { [ "$STRICT_CACHE" = 1 ] || stop "云端定稿（两个仓库是同一份检出）必须 STRICT_CACHE=1：只用仓库里的配音缓存（G51）"; }
[ -f make_video.py ] && [ -f "scripts/$no.json" ] && [ -d fonts ] || stop "请在视频工作目录下运行（要有 make_video.py、scripts/$no.json、fonts/）"
python3 $T/出片指纹.py --核对工作目录 . || stop "工作目录的出片程序缺模块或与仓库工具不一致（G27：清单从 make_video 的 import 自动找全），先 python3 $T/出片指纹.py --拷 . 同步"

python3 $T/方法进化表.py --门 $no || stop "方法进化（G65）：本篇比前三篇中位数变差，方法复盘里还没有落成程序的“进化落地：<提交号|G##|K##>”"
python3 $T/用上核查.py --严 || stop "用上核查（G83）：有程序、工作流或管执行的机制没用上，或门变异没按时跑（上面列出的 ✘ 先补）"
python3 $T/证据.py --闲置 || stop "机制闲置（G71）：有机制连续两篇该用没用（或建好后第一篇就没用上）；查清是坏了（修）还是不该存在（用户同意后下线）"
python3 $T/证据.py --查 $no 定稿 || stop "本篇草稿的机制证据不全（G60：开工记录 → 文本门 → 草稿声音 → 出片前 → 出片后，少一步或顺序不对；按 视频/开工必读.md ⑤ 步骤表补跑）"
python3 $T/放行口子核查.py --定稿 $no || stop "用户还没说定稿（画19/流7：用户试听确认后才算定稿；用户原话记进 用户同意记录.json，用于写“定稿 $no”）"
python3 $T/工作稿核对.py $no || stop "工作目录的脚本是旧稿（G19）"
python3 $T/补对照记录.py $no > /dev/null || stop "补对照记录失败"   # 新加的、程序把关的坑自动补进对照记录；只有人能判的不补（缺了 ① 照样停）
python3 $T/报坑.py --查 --严 || stop "有报坑登记超期还没进踩坑总表（G54：坑一律进总表、配门、演练；python3 $T/报坑.py --状态 看是哪条）"
step "⓪ 规则执行核查（守则16）"; python3 $T/规则执行核查.py > "$LOG/规则执行.log" 2>&1 || { tail -25 "$LOG/规则执行.log"; stop "规则执行核查不通过"; }
[ -f "work_$no/a.wav" ] || { step "①前 重建声音（新容器没有 work_$no/a.wav，K36：只出声音，配音缓存命中）"; AUDIO_ONLY=1 python3 make_video.py scripts/$no.json $no.mp4 > "$LOG/重建声音.log" 2>&1 || { tail -15 "$LOG/重建声音.log"; stop "重建声音失败（K36）"; }; }
step "① 出片前核查"; python3 $T/交付核查.py $no 出片前 > "$LOG/出片前.log" 2>&1 || { tail -25 "$LOG/出片前.log"; stop "出片前核查不通过"; }
step "② 出 4K"; VIDEO_S=2 python3 make_video.py scripts/$no.json $no.mp4 > "$LOG/出片.log" 2>&1 || { tail -15 "$LOG/出片.log"; stop "出片失败"; }
step "③ 出片后核查"; python3 $T/交付核查.py $no 出片后 > "$LOG/出片后.log" 2>&1 || { tail -25 "$LOG/出片后.log"; stop "出片后核查不通过"; }
step "④ 对照文本、文章同步"
YAOWENBEN="${YAOWENBEN:-$(printenv 要文本)}"   # K37：bash 不认中文变量名（${要文本:+…} 直接 bad substitution，文本门被静默跳过）；用户入口 env 要文本=1 照样认
python3 $T/生成文本.py $no $([ -n "$YAOWENBEN" ] && echo --出文档 || echo --只核查) > "$LOG/文本.log" 2>&1 || { tail -15 "$LOG/文本.log"; stop "对照文本生成或文本核查不通过"; }   # 守则17：默认只核查不出 Word/PDF；用户要文本时 YAOWENBEN=1（或 env 要文本=1）
md=$(ls $P/新版定稿/$no-*.md 2>/dev/null | head -1); [ -n "$md" ] || stop "找不到文章 新版定稿/$no-*.md"
(cd $P && python3 视频/工具/sync_article.py 视频/脚本/$no.json "$md") > "$LOG/文章同步.log" 2>&1 || stop "文章同步失败"
[ -n "$CAIPAI" ] && { step "彩排到此（L：⑤ 归档、⑥ 推送不做；彩排.sh 用）"; exit 0; }
step "⑤ 归档（替换旧视频 + 定稿视频核对）"
cp $no.mp4 $P/视频/视频/$no.mp4 || stop "复制失败"
python3 $T/归档定稿视频.py $no > "$LOG/归档.log" 2>&1 || { tail -15 "$LOG/归档.log"; stop "归档或定稿视频核对不通过"; }
python3 $T/证据.py --记 $no 定稿 || stop "定稿证据没写进去（G60）"
step "⑥ 存记录、推送两个仓库"
cat "$LOG/出片前.log" "$LOG/出片后.log" > $P/视频/音频核对/交付核查_${no}_4K定稿.txt
awk '/^① 清点/{f=1} f' "$LOG/归档.log" > $P/视频/音频核对/定稿视频核对_${no}.txt
[ -n "$YUN" ] && { python3 $T/证据.py --查 $no 定稿 > /dev/null || stop "云端定稿：定稿证据没齐（G60）"; tail -3 "$LOG/归档.log"; echo "第${no}篇 云端定稿到 ⑥ 存记录：推送由 drill.yml 按 G58 白名单写回镜像，会话 推送两仓库.sh 回写主仓库后跑 定稿视频核对 --只查清点和镜像"; exit 0; }
MSG="第${no}篇 4K 定稿：出片前/出片后核查全部通过，替换旧视频归档，定稿视频核对逐屏逐样本通过（定稿流水线）

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01XbsiuYS9p9y2vNiB4h6ZZU"
exec 7>"${PUSH_LOCK:-/tmp/推送两仓库.lock}"; flock 7   # G17：提交、镜像同步、推送与 推送两仓库.sh 同一把锁排队（2026-10-23 两篇同时到这一步，镜像同步撞同一个 .part 文件）
(cd $P && git add -A && { git diff --cached --quiet || git commit -q -m "$MSG"; } && push main) || stop "postgraduate-vocabulary 提交或推送失败"
(cd $P && python3 视频/工具/镜像同步.py > "$LOG/镜像.log" 2>&1 && cp CLAUDE.md $L/CLAUDE.md && cp 新版定稿/*.md $L/新版定稿/) || stop "镜像同步失败"
(cd $L && { git symbolic-ref -q HEAD >/dev/null || git checkout -q -B $BR; } && git add -A 视频 最终版4K视频 新版定稿 CLAUDE.md && { git diff --cached --quiet || git commit -q -m "镜像：$MSG"; } && push $BR) || stop "literate-enigma 提交或推送失败"   # 2026-10-23 T34：新容器里 L 是游离 HEAD，推的是 95 个提交前的旧分支，九篇全停在这一步；现在先把分支挪到 HEAD
flock -u 7
python3 $T/定稿视频核对.py --只查清点和镜像 > "$LOG/镜像核对.log" 2>&1 || { tail -10 "$LOG/镜像核对.log"; stop "镜像核对不通过"; }
python3 $T/缓存进仓库核对.py $no || stop "这一篇用到的配音缓存、调平缓存没全进仓库（G51：别的机器重出会不逐样本相同）"   # 推送后核对：严格缓存模式出声音，用到的缓存都在 git 里、已推送
tail -3 "$LOG/归档.log"; echo "第${no}篇 定稿流水线全部完成：最终版4K视频/ 已替换为这一版，两个仓库已推送，各处拷贝逐字节一致"
if [ -n "$QP_LATER" ]; then echo "（全篇重查留给排在后面的那条定稿流水线：没重查完一直算欠着，铁4）"; elif python3 $T/全篇核查.py --欠着; then   # 铁4：出片/排版程序改过，所有已出片的篇目都要重查（全过才记指纹；没过就一直欠着，收工闸门会拦）
  step "⑦ 出片程序改过：全篇重查（铁4，改一处，全部重查）"
  python3 $T/全篇核查.py --视频 > "$LOG/全篇重查.log" 2>&1 && (cd $P && bash $T/推送两仓库.sh "全篇重查通过（铁4）" > /dev/null 2>&1) && tail -1 "$LOG/全篇重查.log" || { tail -6 "$LOG/全篇重查.log"; echo "【欠着】全篇重查没过（铁4）：本篇已完成；上面的篇目要按现行程序重出（记录在 $LOG/全篇重查.log）"; }
fi
if [ "$((10#$no))" -ge 28 ]; then python3 $T/用上核查.py --报告 $no; fi   # G83/I：28 起最后打印本篇执行报告（主会话报用户时附结论行）
