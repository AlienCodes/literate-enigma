import sys, json, os
sys.path.insert(0, "/tmp/claude-0/-home-user-literate-enigma/df763388-3805-5b4c-bf94-30b7788b9986/scratchpad/quality")
sys.path.insert(0, "/home/user/postgraduate-vocabulary/scripts")
import word_tier as T
from draft_check import lemma_key, LEDGER
ledger = json.load(open(LEDGER, encoding="utf-8"))
for w in sys.argv[1:]:
    w = w.replace("_", " ")
    tr, z, why = T.tier(w)
    k = lemma_key(w)
    print("%-20s %-10s %-30s %s" % (w, tr, why, ("占用:" + str(ledger[k])) if ledger.get(k) else ""))
