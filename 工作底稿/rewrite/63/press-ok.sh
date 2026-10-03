#!/bin/bash
# usage: press-ok.sh words... ; prints OK words, then flagged lines
S=/tmp/claude-0/-home-user-literate-enigma/df763388-3805-5b4c-bf94-30b7788b9986/scratchpad
f=$S/rewrite/63/press-t.md
{ printf '# EN: t\n\n## 英文\n\n'; for x in "$@"; do printf '**%s** ' "$x"; done; echo; } > $f
out=$(python3 $S/quality/en_check.py $f)
flag=$(echo "$out" | grep -E '^  (✗|✓|△)')
echo "OK:"; for x in "$@"; do echo "$flag" | grep -qE "^  [^ ]+ $x  " || printf '%s ' "$x"; done; echo
echo "FLAGGED:"; echo "$flag"
