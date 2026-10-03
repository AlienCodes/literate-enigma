#!/usr/bin/env python3
# usage: native-scan.py file  -> lists clean (✓ tier, unused) tokens in the English text
import sys, re, json, os
Q = "/tmp/claude-0/-home-user-literate-enigma/df763388-3805-5b4c-bf94-30b7788b9986/scratchpad/quality"
sys.path.insert(0, Q); sys.path.insert(0, "/home/user/postgraduate-vocabulary/scripts")
import word_tier as T
from draft_check import lemma_key, LEDGER
led = json.load(open(LEDGER, encoding="utf-8"))
t = open(sys.argv[1], encoding="utf-8").read()
t = re.sub(r"^#.*$", "", t, flags=re.M).replace("**", "")
toks = []
for w in re.findall(r"[A-Za-z][A-Za-z'-]*[A-Za-z]|[A-Za-z]", t):
    if w[0].isupper() and w.lower() not in toks:
        pass
    if w.lower() not in toks:
        toks.append(w.lower())
clean, used, grey = [], [], []
for w in toks:
    tr, z, why = T.tier(w)
    k = lemma_key(w)
    if tr.startswith("✓"):
        if led.get(k): used.append("%s(%s)" % (w, led[k]))
        else: clean.append(w)
    elif tr.startswith("△"):
        if led.get(k): used.append("%s(%s)" % (w, led[k]))
        else: grey.append(w)
print("CLEAN:", " ".join(clean)); print("GREY:", " ".join(grey)); print("USED:", " ".join(used))
