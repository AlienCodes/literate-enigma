import json,sys,os
S='/tmp/claude-0/-home-user-literate-enigma/df763388-3805-5b4c-bf94-30b7788b9986/scratchpad'
sys.path.insert(0,S+'/quality'); sys.path.insert(0,"/home/user/postgraduate-vocabulary/scripts")
import io,contextlib
with contextlib.redirect_stdout(io.StringIO()):
    import word_tier as T
    from draft_check import lemma_key
led=json.load(open(S+'/quality/used_words.json'))
keys=list(led.keys())
ok=[];
for w in sys.argv[1:]:
    tr,z,why=T.tier(w); k=lemma_key(w); occ=led.get(k)
    lw=w.lower(); n=5 if len(lw)>6 else 4
    h=[x for x in keys if x.lower().startswith(lw[:n]) or (len(lw)>=5 and lw[:-1] in x.lower())]
    status='OK' if tr.startswith('✓') and not occ else ('OCC' if occ else tr)
    print(f"{w:18s} {status:10s} {tr:8s} {'occ:'+occ if occ else ''} {'stem:'+','.join(h[:6]) if h else ''}")
