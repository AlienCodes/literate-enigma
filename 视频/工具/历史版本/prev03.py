import json,re,sys
sys.path.insert(0,'.')
import render as R
d=json.load(open('scripts/03.json'))
colors={}; i=0
for s in d['sentences']:
    for c in s['chunks']:
        for w in re.findall(r'\*\*([^*]+)\*\*',c['en']):
            if w.lower() not in colors: colors[w.lower()]=R.PAL[i%len(R.PAL)]; i+=1
R.unify_colors(colors,d['sentences'])
for si in [int(x) for x in sys.argv[1:]]:
    s=d['sentences'][si-1]
    ch=[[tuple(p) for p in c['align']] for c in s['chunks']]; notes=[c.get('note') for c in s['chunks']]
    R.ES_FIXED=min(R.max_es(ch,colors,notes),100*R.S)
    print(si,R.ES_FIXED)
    R.frame_interlinear(ch,colors,'',0.5,f'{sys.argv[0][:-3]}_S{si}.png',active=None,notes=notes)
