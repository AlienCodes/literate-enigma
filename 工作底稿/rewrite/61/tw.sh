S=/tmp/claude-0/-home-user-literate-enigma/df763388-3805-5b4c-bf94-30b7788b9986/scratchpad
printf '# EN: t\n## 英文\n' > $S/rewrite/61/t.md; for w in "$@"; do printf '**%s** . ' "$w" >> $S/rewrite/61/t.md; done
out=$(python3 $S/quality/en_check.py $S/rewrite/61/t.md 2>&1 | sed -n '/候选词/,$p')
for w in "$@"; do echo "$out" | grep -qE "^ +[^ ]+ $w( |$)" || printf '%s ' "$w"; done; echo
