#!/bin/bash
# 在一台新机器（GitHub 机器或新容器）上，从仓库搭出和本地一样的出片工作目录（2026-10-17）。
# 用法：bash 视频/工具/环境/准备机器.sh <仓库根目录> <工作目录>   结果：<工作目录>/video（出片目录）、<工作目录>/tts（模型、音色、配音缓存）
set -e; R=$(cd "$1" && pwd); B=$2; V=$R/视频; mkdir -p $B/video/scripts $B/tts
pip install -q -r $V/工具/环境/requirements.txt 2>/dev/null || pip install -q --break-system-packages -r $V/工具/环境/requirements.txt   # 新容器缺 imageio_ffmpeg 等，规则执行核查的当场自检会停（2026-10-23 第14篇会话报）
# 程序里有几处写死了本机路径：建同名路径指向仓库
if [ ! -e /home/user/postgraduate-vocabulary ]; then sudo mkdir -p /home/user && sudo ln -s $R /home/user/postgraduate-vocabulary; fi
python3 $V/工具/出片指纹.py --拷 $B/video ; cp $V/工具/clean.py $B/tts/ ;   # G27：出片程序清单从 make_video 的 import 自动找全（手写清单漏过 对正量.py）
 cp -r $V/工具/fonts $B/video/fonts ; cp $V/脚本/*.json $B/video/scripts/
cp $V/工具/配音/* $B/tts/ ; mkdir -p $B/tts/cache_tts ; cp $V/配音缓存/*.pkl $V/配音缓存/调平_*.json $B/tts/cache_tts/ 2>/dev/null || true; cp $V/配音缓存/*.单线程 $B/tts/cache_tts/ 2>/dev/null || true   # 新条目的 .单线程 标记一起拷（G72）   # G51 调平缓存一起拷
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
# 2026-10-25 机器复听（音频保障第 4 层）：离线语音识别 sherpa-onnx + whisper small.en（huggingface 被网络挡，GitHub release 通），下载到 ~/asr 并核对校验码
python3 -c "import sherpa_onnx" 2>/dev/null || pip install -q sherpa-onnx==2.0.0 2>/dev/null || pip install -q --break-system-packages sherpa-onnx==2.0.0
# K54（2026-10-27 新容器）：经代理下载 tar.bz2 被截断，管道直接解压留下半截 encoder，重跑 [ -f ] 成立就跳过下载、只剩校验码失败。
# 先整个下到临时文件、解压成功才算；失败就清掉半截目录（最多试两次）
取模型() { local d=$1 f=$2 u=$3 t; [ -f $d/$f ] && return 0; mkdir -p ~/asr
  for _i in 1 2; do t=$(mktemp ~/asr/.下载_XXXXXX); if curl -sSL --retry 3 -o $t $u && tar xjf $t -C ~/asr; then rm -f $t; return 0; fi; rm -rf $d $t; done
  echo "✘ 识别模型下载或解压失败（K54：半截目录已清掉，重跑即可）：$u"; return 1; }
A=~/asr/sherpa-onnx-whisper-small.en; 取模型 $A small.en-encoder.int8.onnx https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/sherpa-onnx-whisper-small.en.tar.bz2
python3 - "$A" "$V/工具/环境/模型校验码.json" <<'PY3'
import sys,json,hashlib,os
d,j=sys.argv[1],json.load(open(sys.argv[2])); bad=0
fs=('small.en-encoder.int8.onnx','small.en-decoder.int8.onnx'); hs={}
for f in fs:
    h=hashlib.sha256(open(os.path.join(d,f),'rb').read()).hexdigest()[:16]; want=j[f].split(':')[1]; hs[f]=h
    print(f, h, '✔ 识别模型对' if h==want else '✘ 识别模型不对'); bad|=(h!=want)
if bad and all(hs[a]==j[b].split(':')[1] for a,b in (fs,fs[::-1])): print('✘ 是校验码表里 encoder、decoder 两项写反了（2026-10-25 出过一次），改 模型校验码.json')
sys.exit(bad)
PY3
# 2026-10-26 机器复听第二路 parakeet（NeMo TDT 0.6B int8，任一路报就报；改门_音频上GitHub.md 第二阶段 2），同样 GitHub release 下载、核对校验码
P=~/asr/sherpa-onnx-nemo-parakeet-tdt-0.6b-v2-int8; 取模型 $P encoder.int8.onnx https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/sherpa-onnx-nemo-parakeet-tdt-0.6b-v2-int8.tar.bz2
python3 - "$P" "$V/工具/环境/模型校验码.json" <<'PY4'
import sys,json,hashlib,os
d,j=sys.argv[1],json.load(open(sys.argv[2])); bad=0
for f in ('encoder.int8.onnx','decoder.int8.onnx','joiner.int8.onnx','tokens.txt'):
    h=hashlib.sha256(open(os.path.join(d,f),'rb').read()).hexdigest()[:16]; want=j['parakeet/'+f].split(':')[1]
    print('parakeet/'+f, h, '✔ 识别模型对' if h==want else '✘ 识别模型不对'); bad|=(h!=want)
sys.exit(bad)
PY4
echo "机器准备好了：$B/video"
