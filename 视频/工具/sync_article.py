import json,re,sys
js,md=sys.argv[1],sys.argv[2]
d=json.load(open(js)); t=open(md).read()
head,rest=t.split('## 英文',1); en_old,rest=rest.split('## 中文',1); zh_old,tail=rest.split('## 速查表',1)
tbl_old,after=tail.split('\n## ',1)
old_rows={}
for r in re.findall(r'^\| (.+?) \| (.+?) \| (\d+) \|$',tbl_old,re.M): old_rows[r[0].lower()]=r[1]
paras_en={};paras_zh={}
for s in d['sentences']:
    en=' '.join(c['en'] for c in s['chunks'])
    zh=''.join(c['zh'] for c in s['chunks'])
    notes=''.join(c['note'].replace('#Y','') for c in s['chunks'] if c.get('note'))
    paras_en.setdefault(s['para'],[]).append(en); paras_zh.setdefault(s['para'],[]).append(zh+notes)
new_en='\n\n'.join(' '.join(v) for k,v in sorted(paras_en.items()))
strip=lambda x:re.sub(r'[\*\s]','',x)
assert strip(new_en)==strip(en_old), 'English text changed!'
new_zh='\n\n'.join(''.join(v) for k,v in sorted(paras_zh.items()))
# keyword table in order of appearance
rows=[];seen=set()
for s in d['sentences']:
    for c in s['chunks']:
        zmap={e.lower():z for z,e in re.findall(r'\*\*([^*]+)\*\*\(([^)]+)\)',c['zh'])}
        for w in re.findall(r'\*\*([^*]+)\*\*',c['en']):
            if w.lower() in seen: continue
            seen.add(w.lower())
            old=old_rows.get(w.lower()) or next((v for k,v in old_rows.items() if k in w.lower().split() or w.lower().startswith(k)),'')
            pos=(re.match(r'^([a-z./]+\.)',old) or [None,''])[1] if old else ''
            rows.append(f"| {w} | 本文：{zmap.get(w.lower(),'')}" + (f"；{old}" if old else '') + f" | {s['para']} |")
tbl='| 词 | 释义 | 段 |\n|---|---|---|\n'+'\n'.join(rows)+'\n'
out=head+'## 英文\n'+new_en+'\n\n## 中文\n\n'+new_zh+'\n\n## 速查表\n'+tbl+'\n## '+after
open(md,'w').write(out); print(len(rows),'rows')
