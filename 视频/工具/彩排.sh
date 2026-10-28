#!/bin/bash
# L 新容器整条彩排（用户 2026-10-27 丝滑主义：“一定要确保这个流程的运行，中间非常的丝滑……也没有任何程序上之间的冲突”）。
# 改了门程序的推送，必须在 GitHub 全新容器上把真实流程从头到尾跑一遍，一次跑通、0 次不丝滑才算过；过了写 彩排通过.json（门程序的指纹），
# 规则执行核查 对指纹：门程序一改、彩排没重跑 → 提交、推送停。
# 原样重放：K42（新容器缺 soundfile/wordfreq → 会话开工 必须自己装好）、K36（没有 work_NN/a.wav → 定稿流水线 ①前 自动重建）、
#          K37（bash 中文变量名 bad substitution → 流程自检 真跑每道 .sh 门）。
# 用法（GitHub drill.yml “彩排” 任务，在视频工作目录下）：bash $T/彩排.sh [篇号，默认 25]
no=$(printf '%02d' "$((10#${1:-25}))"); T=$(cd "$(dirname "$0")" && pwd); V=$(dirname "$T"); P=$(dirname "$V"); LG=$(mktemp -d)
stop() { echo "【彩排不过】$1"; exit 1; }
[ -f make_video.py ] && [ -f "scripts/$no.json" ] || stop "要在视频工作目录下跑（准备机器.sh 搭的 video/）"
rm -rf "$V/制作记录/丝滑"   # 只数这次彩排的停下
H=$(mktemp -d)   # 新会话：会话开工 用空 HOME（没有开工记录）；定稿流水线 用真 HOME（~/asr 识别模型在那里，L彩排v6 实测空 HOME 机器复听找不到模型）

echo "== K42 重放：卸掉 soundfile、wordfreq，会话开工 必须自己装好"
python3 -m pip uninstall -y -q soundfile wordfreq >/dev/null 2>&1
HOME=$H python3 $T/会话开工.py 出稿 > $LG/开工.log 2>&1 || { tail -8 $LG/开工.log; stop "会话开工 没把环境装好（K42/M）"; }
grep -q '【环境】缺' $LG/开工.log || stop "卸掉的包会话开工没发现（K42 没重放到）"
python3 -c "import soundfile, wordfreq" || stop "会话开工 说装好了，包还是缺（K42/M）"

echo "== K37 重放：流程自检（每道 .sh 门真跑，bash 中文变量名）"
python3 $T/流程自检.py > $LG/流程.log 2>&1 || { tail -8 $LG/流程.log; stop "流程自检 不过（K37）"; }

echo "== K36 重放：没有 work_$no，定稿流水线 第$no篇 一次跑通到 ④（⑤ 归档、⑥ 推送不做）"
rm -rf "work_$no"
CAIPAI=1 bash $T/定稿流水线.sh $no > $LG/流水线.log 2>&1 || { tail -8 $LG/流水线.log; grep -h "✘" "定稿流水线_$no"/*.log 2>/dev/null | head -20; stop "定稿流水线 第$no篇 没一次跑通"; }   # 停在哪一项都打出来（结果.txt 只收 ✘、【 行）
grep -q '①前 重建声音' $LG/流水线.log || stop "没走 ①前 重建声音（K36 没重放到）"
grep -q '彩排到此' $LG/流水线.log || stop "定稿流水线 没跑到 ④ 之后（彩排出口没到）"

n=$(python3 "$T/丝滑.py" --停下数 "$V/制作记录/丝滑")   # K73：只数停下（会话开工 的“开工”记录不算）；程序崩了 n 为空，下一行照样停
[ "$n" -eq 0 ] || { cat "$V"/制作记录/丝滑/*.jsonl | tail -5; stop "停下 $n 次（丝滑记录）"; }
git -C "$P" checkout -q -- 视频 2>/dev/null; git -C "$P" clean -qfd -- 视频/制作记录 视频/音频核对 2>/dev/null   # 彩排在流水线里写的记录不带回去，只留印章
python3 $T/规则执行核查.py --盖彩排印章 || stop "印章没写上"
echo "彩排通过：会话开工（K42 自己装好）→ 流程自检（K37）→ 定稿流水线 第$no篇 ①前重建（K36）→ ① → ② 4K → ③ → ④，0 次停下"
