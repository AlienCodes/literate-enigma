#!/bin/bash
cd "$(dirname "$0")"
export SETS=en_eval,en_cohort,zh,clone,en_short,zh_short THREADS=4 PREPS=raw,vad
W="tvenv/bin/python ort_wave_embed.py"
E="python3 embed_all.py"
run() { echo "=== $(date +%H:%M:%S) $*"; "$@" 2>&1 | grep --line-buffered -v -i warn; }
run $W redimnet2_b6_cnc
run $E campplus_sv_zh_en eres2netv2_sv_zh-cn eres2net_base_200k campplus_sv_zh-cn
run $W redimnet2_b3_cnc redimnet2_b6_vb2
run $E wespeaker_zh_cnceleb_resnet34_LM eres2net_large titanet_large resnet293_LM CAM++_LM resnet34_LM
run $E resnet221_LM eres2net_sv_zh-cn eres2net_sv_en titanet_small resnet152
echo "=== $(date +%H:%M:%S) QUEUE DONE"
