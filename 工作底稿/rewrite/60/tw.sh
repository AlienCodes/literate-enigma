#!/bin/bash
S=/tmp/claude-0/-home-user-literate-enigma/df763388-3805-5b4c-bf94-30b7788b9986/scratchpad
f=$S/rewrite/60/t.md; printf '# EN: x\n\n' > $f; for w in "$@"; do printf "**$w** " >> $f; done
python3 $S/quality/en_check.py $f > $S/rewrite/60/t.out
python3 $S/stem.py "$@" > $S/rewrite/60/s.out
python3 - "$@" <<'P'
import re,sys
S='/tmp/claude-0/-home-user-literate-enigma/df763388-3805-5b4c-bf94-30b7788b9986/scratchpad/rewrite/60/'
o=open(S+'t.out').read(); flag=set(re.findall(r'[✓✗△]\S+ (\S+)',o))
st={l.split()[0]:l.split('->')[1].strip() for l in open(S+'s.out') if '->' in l}
for w in sys.argv[1:]:
  if w in flag: continue
  print(w, ('STEM '+st[w.lower()]) if w.lower() in st else '')
P
