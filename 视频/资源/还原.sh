#!/bin/bash
# 还原配音模型与字体到工作目录：bash 视频/资源/还原.sh <目标目录>
set -e
H=$(cd "$(dirname "$0")" && pwd); T=${1:-./work}
mkdir -p "$T/tts" "$T/video/fonts"
cat "$H"/模型/kokoro-v1.0.onnx.part* > "$T/tts/kokoro-v1.0.onnx"
cat "$H"/模型/kokoro-v1.0-timed.onnx.part* > "$T/tts/kokoro-v1.0-timed.onnx"  # 只用于定位标点时间（A9）
cp "$H"/模型/voices-v1.0.bin "$H"/模型/voice_mb.npy "$H"/模型/voice_mf.npy "$T/tts/"
cp "$H"/../工具/AF.txt "$T/tts/"
cp "$H"/字体/*.ttf "$T/video/fonts/"
(cd "$T/tts" && sha256sum -c "$H/模型/SHA256SUMS")
pip install -q kokoro-onnx==0.6.1 soundfile imageio-ffmpeg pillow python-docx
echo "完成：$T"
