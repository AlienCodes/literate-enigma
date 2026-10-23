#!/bin/bash
# 在一台新机器（GitHub 机器或新容器）上，从仓库搭出和本地一样的出片工作目录（2026-10-17）。
# 用法：bash 视频/工具/环境/准备机器.sh <仓库根目录> <工作目录>   结果：<工作目录>/video（出片目录）、<工作目录>/tts（模型、音色、配音缓存）
set -e; R=$(cd "$1" && pwd); B=$2; V=$R/视频; mkdir -p $B/video/scripts $B/tts
pip install -q -r $V/工具/环境/requirements.txt 2>/dev/null || pip install -q --break-system-packages -r $V/工具/环境/requirements.txt   # 新容器缺 imageio_ffmpeg 等，规则执行核查的当场自检会停（2026-10-23 第14篇会话报）
# 程序里有几处写死了本机路径：建同名路径指向仓库
if [ ! -e /home/user/postgraduate-vocabulary ]; then sudo mkdir -p /home/user && sudo ln -s $R /home/user/postgraduate-vocabulary; fi
cp $V/工具/make_video.py $V/工具/render.py $V/工具/title_anim.py $V/工具/title2.py $B/video/ ; cp $V/工具/clean.py $B/tts/ ; cp -r $V/工具/fonts $B/video/fonts ; cp $V/脚本/*.json $B/video/scripts/
cp $V/工具/配音/* $B/tts/ ; mkdir -p $B/tts/cache_tts ; cp $V/配音缓存/*.pkl $B/tts/cache_tts/ 2>/dev/null || true
# 模型全部来自 kokoro-onnx 官方发布页，按地址下载、按校验码核对：出片模型 = model-files-v1.0 的 kokoro-v1.0.onnx；
# 带时长模型 kokoro-v1.0-timed.onnx = model-files-v1.1 的 kokoro-v1.0.onnx 改名（2026-10-17 重新下载，与本地那份逐字节相同）
G=https://github.com/thewh1teagle/kokoro-onnx/releases/download
for p in "kokoro-v1.0.onnx model-files-v1.0/kokoro-v1.0.onnx" "kokoro-v1.0-timed.onnx model-files-v1.1/kokoro-v1.0.onnx" "voices-v1.0.bin model-files-v1.0/voices-v1.0.bin"; do
  set -- $p; [ -f $B/tts/$1 ] || curl -sSL --retry 3 -o $B/tts/$1 $G/$2; done
python3 - "$B/tts" "$V/工具/环境/模型校验码.json" <<'PY2'
import sys,json,hashlib,os
d,j=sys.argv[1],json.load(open(sys.argv[2])); bad=0
for f in ('kokoro-v1.0.onnx','kokoro-v1.0-timed.onnx'):
    h=hashlib.sha256(open(os.path.join(d,f),'rb').read()).hexdigest()[:16]; want=j[f].split(':')[1]
    print(f, h, '✔ 与本地同一个模型' if h==want else '✘ 与本地模型不同'); bad|=(h!=want)
sys.exit(bad)
PY2
# 2026-10-23（13 重新对齐）：新容器缺 imageio_ffmpeg 等包，定稿流水线⓪就停；按固定版本装好
python3 -c "import imageio_ffmpeg,kokoro_onnx,parselmouth,pyloudnorm,soundfile,scipy" 2>/dev/null || pip install -q -r $V/工具/环境/requirements.txt; python3 -c "import pymupdf,docx" 2>/dev/null || pip install -q pymupdf python-docx   # 生成文本.py（Word/PDF 读回核对）要用
echo "机器准备好了：$B/video"
