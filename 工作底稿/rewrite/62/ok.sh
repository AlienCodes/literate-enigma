#!/bin/bash
# usage: ok.sh words... ; prints clean words
S=/tmp/claude-0/-home-user-literate-enigma/df763388-3805-5b4c-bf94-30b7788b9986/scratchpad
f=$S/rewrite/62/_t.md
{ printf '# EN: t\n\n## 英文\n\n'; for x in "$@"; do printf '**%s** ' "$x"; done; echo; } > $f
bad=$(python3 $S/quality/en_check.py $f | grep -E '^  (✗|✓|△)' | awk '{print $2}')
for x in "$@"; do echo "$bad" | grep -qx "$x" || printf '%s ' "$x"; done; echo
