#!/bin/bash
# usage: native-ok.sh words... ; prints CLEAN words then flagged lines
S=/tmp/claude-0/-home-user-literate-enigma/df763388-3805-5b4c-bf94-30b7788b9986/scratchpad
f=$S/rewrite/63/native-t.md
{ printf '# EN: t\n\n## 英文\n\n'; for x in "$@"; do printf '**%s** ' "$x"; done; echo; } > $f
out=$(python3 $S/quality/en_check.py $f)
bad=$(echo "$out" | grep -E '^  (✗|✓|△)' | awk '{print $2}')
printf 'CLEAN: '; for x in "$@"; do echo "$bad" | grep -qx "$x" || printf '%s ' "$x"; done; echo
echo "$out" | grep -E '^  (✗|✓|△)'
