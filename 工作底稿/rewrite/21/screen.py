import sys,re,json,os
sys.path.insert(0,'/tmp/claude-0/-home-user-literate-enigma/df763388-3805-5b4c-bf94-30b7788b9986/scratchpad/quality')
sys.path.insert(0,"/home/user/postgraduate-vocabulary/scripts")
import word_tier as T
from draft_check import lemma_key, LEDGER
led=json.load(open(LEDGER))
t=open(sys.argv[1]).read() if len(sys.argv)>1 and os.path.exists(sys.argv[1]) else " ".join(sys.argv[1:])
t=re.sub(r"^#.*$","",t,flags=re.M).replace("*","")
seen=set()
for w in re.findall(r"[A-Za-z][A-Za-z'-]+",t):
    k=w.lower()
    if k in seen: continue
    seen.add(k)
    tr,z,why=T.tier(w)
    if tr.startswith("✓"):
        lk=lemma_key(w)
        used=bool(led.get(lk))
        print(("USED " if used else "OK   ")+w, tr)
