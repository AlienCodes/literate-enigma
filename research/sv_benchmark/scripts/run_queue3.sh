#!/bin/bash
# continue after the current ReDimNet job: remaining models, raw audio only (VAD variants only for the finalists)
cd "$(dirname "$0")"
while kill -0 29166 2>/dev/null; do sleep 5; done
export SETS=en_eval,en_cohort,zh,clone,en_short,zh_short THREADS=4 PREPS=raw
E="python3 embed_all.py"
run() { echo "=== $(date +%H:%M:%S) $*"; "$@" 2>&1 | grep --line-buffered -v -i warn; }
run $E wespeaker_zh_cnceleb_resnet34_LM eres2net_large titanet_large CAM++_LM resnet34_LM
run $E resnet293_LM eres2net_sv_zh-cn resnet221_LM titanet_small eres2net_sv_en resnet152
echo "=== $(date +%H:%M:%S) QUEUE DONE"
