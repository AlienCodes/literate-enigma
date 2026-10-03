#!/bin/bash
S=/tmp/claude-0/-home-user-literate-enigma/df763388-3805-5b4c-bf94-30b7788b9986/scratchpad
{ echo "# EN: t"; echo "## 英文"; for x in "$@"; do printf "**%s** " $x; done; echo; } > /tmp/okt.md 2>/dev/null || true
f=$S/rewrite/61/okt.md; { echo "# EN: t"; echo "## 英文"; for x in "$@"; do printf "**%s** " $x; done; echo; } > $f
bad=$(python3 $S/quality/en_check.py $f | grep -E '^  [✗△✓]' | grep -v 视频 | awk '{print $2}')
for x in "$@"; do echo "$bad" | grep -qx "$x" || printf "%s " $x; done; echo
