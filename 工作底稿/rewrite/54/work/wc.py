import sys, json
Q="/tmp/claude-0/-home-user-literate-enigma/df763388-3805-5b4c-bf94-30b7788b9986/scratchpad/quality"
sys.path.insert(0,Q); sys.path.insert(0,"/home/user/postgraduate-vocabulary/scripts")
import word_tier as T
from draft_check import lemma_key, LEDGER
led=json.load(open(LEDGER))
for w in sys.argv[1:]:
    w=w.replace('_',' ')
    tr,z,why=T.tier(w); k=lemma_key(w)
    ok = not (tr.startswith('✗') or tr.startswith('△') or led.get(k))
    print(("OK  " if ok else "BAD ")+"%-18s %-10s %s %s"%(w,tr,why,("占用 %s"%led[k]) if led.get(k) else ""))
