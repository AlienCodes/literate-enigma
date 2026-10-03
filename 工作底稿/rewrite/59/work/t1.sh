#!/bin/bash
# test each word individually with wt.sh, then stem.py
S=/tmp/claude-0/-home-user-literate-enigma/df763388-3805-5b4c-bf94-30b7788b9986/scratchpad
for w in "$@"; do r=$(bash $S/wt.sh "$w" | grep -v ':$' | head -1); st=$(python3 $S/stem.py "$w"); echo "$w => $r | ${st:-clean}"; done
