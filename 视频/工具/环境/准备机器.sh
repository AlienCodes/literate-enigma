#!/bin/bash
# 在一台新机器（GitHub 机器或新容器）上，从仓库搭出和本地一样的出片工作目录（2026-10-17）。
# 用法：bash 视频/工具/环境/准备机器.sh <仓库根目录> <工作目录>   结果：<工作目录>/video（出片目录）、<工作目录>/tts（模型、音色、配音缓存）
set -e; R=$(cd "$1" && pwd); B=$2; V=$R/视频; mkdir -p $B/video/scripts $B/tts
# 程序里有几处写死了本机路径：建同名路径指向仓库
if [ ! -e /home/user/postgraduate-vocabulary ]; then sudo mkdir -p /home/user && sudo ln -s $R /home/user/postgraduate-vocabulary; fi
cp $V/工具/make_video.py $V/工具/render.py $V/工具/title_anim.py $V/工具/title2.py $B/video/ ; cp $V/工具/clean.py $B/tts/ ; cp -r $V/工具/fonts $B/video/fonts ; cp $V/脚本/*.json $B/video/scripts/
cp $V/工具/配音/* $B/tts/ ; mkdir -p $B/tts/cache_tts ; cp $V/配音缓存/*.pkl $B/tts/cache_tts/ 2>/dev/null || true
# 官方模型：按地址下载、按校验码核对（自制的带时长模型不用，带时长结果全部来自缓存）
U=https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0
for f in kokoro-v1.0.onnx voices-v1.0.bin; do [ -f $B/tts/$f ] || curl -sSL -o $B/tts/$f $U/$f; done
python3 - "$B/tts" "$V/工具/环境/模型校验码.json" <<'PY'
import sys,json,hashlib,os
d,j=sys.argv[1],json.load(open(sys.argv[2])); f='kokoro-v1.0.onnx'; h=hashlib.sha256(open(os.path.join(d,f),'rb').read()).hexdigest()[:16]
want=j[f].split(':')[1]; print(f, h, '✔ 与本地同一个模型' if h==want else '✘ 与本地模型不同'); sys.exit(0 if h==want else 1)
PY
echo "机器准备好了：$B/video"
