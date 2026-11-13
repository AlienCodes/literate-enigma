#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "$0")"
mkdir -p 成品
# The visual design is generated with imagegen. Only mechanical size/format export happens here.
magick 原始生成/横版原图.png -auto-orient -colorspace sRGB -filter Lanczos -resize '1600x900^' -gravity center -extent 1600x900 -strip 成品/BILIBILI-COVER-16x9.png
magick 原始生成/四比三原图.png -auto-orient -colorspace sRGB -filter Lanczos -resize '1440x1080^' -gravity center -extent 1440x1080 -strip 成品/BILIBILI-COVER-4x3.png
for ratio in 16x9 4x3; do
  magick "成品/BILIBILI-COVER-${ratio}.png" -sampling-factor 4:4:4 -quality 95 -interlace Plane -strip "成品/BILIBILI-COVER-${ratio}.jpg"
done
