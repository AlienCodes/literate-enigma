#!/bin/bash
# usage: wt.sh w1 w2 ... -> OK / OCC / BAD / TRI  (clean ✓ words are not printed by en_check)
S=/tmp/claude-0/-home-user-literate-enigma/df763388-3805-5b4c-bf94-30b7788b9986/scratchpad
f=$S/twt.md; printf '# EN: x\n\n' > $f; for w in "$@"; do printf "**$w** " >> $f; done
python3 $S/quality/en_check.py $f 2>/dev/null | grep -E "^\s+(✓|✗|△)\S+ " > $S/twt.out
ok=""; occ=""; bad=""; tri=""
for w in "$@"; do l=$(grep -E "^\s+\S+ $w( |$)" $S/twt.out | head -1)
 if [ -z "$l" ]; then ok="$ok $w"
 elif echo "$l" | grep -q "占用"; then occ="$occ $w"
 elif echo "$l" | grep -q "✗"; then bad="$bad $w"
 elif echo "$l" | grep -q "△"; then tri="$tri $w"
 else ok="$ok $w"; fi; done
echo "OK:$ok"; echo "OCC:$occ"; echo "BAD:$bad"; echo "TRI:$tri"
