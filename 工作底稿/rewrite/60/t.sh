S=/tmp/claude-0/-home-user-literate-enigma/df763388-3805-5b4c-bf94-30b7788b9986/scratchpad
for w in "$@"; do printf '# EN: x\n\n## 英文\nA **%s** b.\n' "$w" > /tmp/claude-0/tt.md 2>/dev/null || printf '# EN: x\n\n## 英文\nA **%s** b.\n' "$w" > $S/tt.md
f=$S/tt.md; [ -f /tmp/claude-0/tt.md ] && f=/tmp/claude-0/tt.md
l=$(python3 $S/quality/en_check.py $f 2>&1 | grep -E "^\s+[✓✗△]" | head -1)
case "$l" in *占用*|*✗*|*△*) echo "NO $w :$l";; *) echo "OK $w :$l";; esac; done
