#!/bin/bash
# 快速重建 + 程序核查（合成缓存后一篇约 10–60 秒）：bash <工具目录>/快速重建核查.sh NN（在视频工作目录里）
no=$1; T=/home/user/postgraduate-vocabulary/视频/工具
AUDIO_ONLY=1 python3 make_video.py scripts/$no.json $no.mp4 2>&1 | tail -1
echo "配音指纹 $(md5sum work_$no/a.wav | cut -c1-12)"
python3 $T/纯人声核对.py $no 2>&1 | grep -E "BAD|问题数"
python3 $T/标点停顿核对.py $no 2>&1 | grep -E "BAD|FAIL|问题数|停止"
python3 $T/句间停顿核对.py $no 2>&1 | grep -E "BAD|问题数|分段数"
