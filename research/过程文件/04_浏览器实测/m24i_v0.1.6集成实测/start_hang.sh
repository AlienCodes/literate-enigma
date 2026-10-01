#!/bin/bash
# Same as start.sh, but the fake GPT-SoVITS SoVITS training never finishes (to see the amber "stall" bar and Stop).
export FAKE_GSV_HANG=1
exec bash <草稿目录>/m24i/start.sh
