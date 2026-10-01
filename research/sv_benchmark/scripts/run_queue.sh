#!/bin/bash
# Sequential embedding queue (one job at a time, all 4 cores), most promising models first.
cd "$(dirname "$0")"
export SETS=en_eval,en_cohort,zh,clone THREADS=4
R="tvenv/bin/python rd_embed.py"
E="python3 embed_all.py"
run() { echo "=== $(date +%H:%M:%S) $*"; "$@" 2>&1 | grep -v -i warn; }
run $E campplus zh_en_16k-common_advanced
run $R redimnet2_b6_cnc
run $E eres2netv2_sv_zh-cn
run $R redimnet2_b3_cnc
run $E wespeaker_zh_cnceleb_resnet34_LM
run $R redimnet_M_cnc
run $E eres2net_large titanet_large resnet293_LM CAM++_LM resnet34_LM eres2net_base_200k
run $R redimnet2_b6_vb2
run $E resnet221_LM eres2net_sv_zh-cn eres2net_sv_en titanet_small cnceleb_resnet34.onnx resnet152
echo "=== $(date +%H:%M:%S) QUEUE DONE"
