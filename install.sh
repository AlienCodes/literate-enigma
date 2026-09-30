#!/usr/bin/env bash
# VoiceTwin 声音分身 - Linux / macOS 安装脚本
#   bash install.sh                            # 独立虚拟环境 .venv
#   bash install.sh --gsv /path/GPT-SoVITS     # 装进当前已激活的 GPT-SoVITS 环境（推荐，共用 PyTorch/显卡）
#   bash install.sh --clone-gsv                # 额外克隆 GPT-SoVITS 到 third_party/（其环境需用 conda 按提示安装）
#   加 --mirror 使用清华 PyPI 镜像
set -euo pipefail
cd "$(dirname "$0")"
HERE="$(pwd)"
MIRROR="${PIP_INDEX_URL:-}"
GSV=""
CLONE_GSV=0
while [[ $# -gt 0 ]]; do
  case "$1" in
    --gsv) GSV="$2"; shift 2 ;;
    --clone-gsv) CLONE_GSV=1; shift ;;
    --mirror) MIRROR="https://pypi.tuna.tsinghua.edu.cn/simple"; shift ;;
    *) echo "未知参数 $1"; exit 1 ;;
  esac
done
pipi() { if [[ -n "$MIRROR" ]]; then "$PY" -m pip install -i "$MIRROR" "$@"; else "$PY" -m pip install "$@"; fi; }

if [[ $CLONE_GSV -eq 1 ]]; then
  mkdir -p third_party
  [[ -d third_party/GPT-SoVITS ]] || git clone --depth 1 https://github.com/RVC-Boss/GPT-SoVITS.git third_party/GPT-SoVITS
  echo
  echo "GPT-SoVITS 已克隆到 third_party/GPT-SoVITS。请按官方方式安装它的环境（需要 conda），例如："
  echo "  conda create -n GPTSoVits python=3.10 -y && conda activate GPTSoVits"
  echo "  cd third_party/GPT-SoVITS && bash install.sh --device CU128 --source ModelScope"
  echo "然后在该环境中执行：bash install.sh --gsv $HERE/third_party/GPT-SoVITS"
  echo
fi

if [[ -n "$GSV" ]]; then
  PY="$(command -v python)"
  echo "==> 安装到当前 Python 环境（$PY），不改动已有依赖版本"
  pipi --no-deps -e "$HERE"
  pipi pyloudnorm imageio-ffmpeg zhconv webrtcvad-wheels
  pipi --no-deps resemblyzer
  "$PY" -m voicetwin init-config --gptsovits-root "$GSV" --backend gptsovits --force
else
  SYSPY="$(command -v python3.11 || command -v python3.10 || command -v python3)"
  echo "==> 创建虚拟环境 .venv（$SYSPY）"
  "$SYSPY" -m venv .venv
  PY="$HERE/.venv/bin/python"
  "$PY" -m pip install -U pip >/dev/null
  pipi -e "$HERE[asr,webui,denoise,docx]"
  pipi torch --index-url https://download.pytorch.org/whl/cpu || pipi torch
  pipi webrtcvad-wheels
  pipi --no-deps resemblyzer
  [[ -f config.yaml ]] || "$PY" -m voicetwin init-config
fi

printf '#!/usr/bin/env bash\ncd "$(dirname "$0")"\nexec "%s" -m voicetwin webui "$@"\n' "$PY" > start_webui.sh
printf '#!/usr/bin/env bash\ncd "$(dirname "$0")"\nexec "%s" -m voicetwin "$@"\n' "$PY" > voicetwin.sh
chmod +x start_webui.sh voicetwin.sh
"$PY" -m voicetwin doctor || true
echo
echo "安装完成！运行 ./start_webui.sh 打开网页界面，或 ./voicetwin.sh -h 查看命令。"
