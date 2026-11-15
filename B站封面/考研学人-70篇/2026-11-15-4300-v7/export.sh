#!/usr/bin/env bash
set -euo pipefail
cover_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
# All image content changes used image_gen. FFmpeg only exports size/format.
ffmpeg -v error -nostdin -n -i "$cover_dir/原始生成/4300-4x3-书名及珊瑚橙版.png" -vf scale=1440:1080:flags=lanczos -frames:v 1 -update 1 "$cover_dir/成品/BILIBILI-COVER-4300-4x3.png"
ffmpeg -v error -nostdin -n -i "$cover_dir/原始生成/4300-16x9-书名及珊瑚橙版.png" -vf scale=1600:900:flags=lanczos -frames:v 1 -update 1 "$cover_dir/成品/BILIBILI-COVER-4300-16x9.png"
ffmpeg -v error -nostdin -n -i "$cover_dir/成品/BILIBILI-COVER-4300-4x3.png" -frames:v 1 -q:v 2 -update 1 "$cover_dir/成品/BILIBILI-COVER-4300-4x3.jpg"
ffmpeg -v error -nostdin -n -i "$cover_dir/成品/BILIBILI-COVER-4300-16x9.png" -frames:v 1 -q:v 2 -update 1 "$cover_dir/成品/BILIBILI-COVER-4300-16x9.jpg"
