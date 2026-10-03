import json,sys,re,io,contextlib
S='/tmp/claude-0/-home-user-literate-enigma/df763388-3805-5b4c-bf94-30b7788b9986/scratchpad'
sys.path.insert(0,S+'/quality'); sys.path.insert(0,"/home/user/postgraduate-vocabulary/scripts")
with contextlib.redirect_stdout(io.StringIO()):
    import word_tier as T
    from draft_check import lemma_key
led=json.load(open(S+'/quality/used_words.json')); keys=list(led)
t=open(sys.argv[1]).read().split('## 中文')[0]
t=re.sub(r'^#.*$','',t,flags=re.M)
bold=set(w.lower() for w in re.findall(r'\*\*([^*]+)\*\*',t))
plain=re.sub(r'\*\*[^*]+\*\*',' ',t)
seen=set()
for w in re.findall(r"[A-Za-z][A-Za-z'-]*",plain):
    lw=w.lower()
    if lw in seen or lw in bold: continue
    seen.add(lw)
    tr,z,why=T.tier(lw); occ=led.get(lemma_key(lw))
    if tr.startswith('✓') and not occ:
        n=5 if len(lw)>6 else 4
        h=[x for x in keys if x.lower().startswith(lw[:n]) or (len(lw)>=5 and lw[:-1] in x.lower())]
        print(f"{lw:16s} {tr} {'stem:'+','.join(h[:5]) if h else ''}")
