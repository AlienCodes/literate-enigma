import json,re,sys
js,md=sys.argv[1],sys.argv[2]
d=json.load(open(js)); t=open(md).read()
head,rest=t.split('## 英文',1); en_old,rest=rest.split('## 中文',1); zh_old,tail=rest.split('## 速查表',1)
tbl_old,after=tail.split('\n## ',1)
old_rows={}
def split_benwen(x):
    """拆成（最后一段“本文：”的内容, 其余释义）。括号里的“；”不算分段（08 inquiry、declined to 的说明里有“；”，还有括号套括号）"""
    bw=''
    while x.startswith('本文：'):
        dep=0; i=len('本文：')
        while i<len(x) and not (x[i]=='；' and dep==0):
            dep+=(x[i]=='（')-(x[i]=='）'); i+=1
        bw=x[len('本文：'):i]; x=x[i+1:]
    return bw,x
old_bw={}
for r in re.findall(r'^\| (.+?) \| (.+?) \| (\d+) \|$',tbl_old,re.M): old_bw[r[0].lower()],old_rows[r[0].lower()]=split_benwen(r[1])
def _gloss(z):
    """画面上词下面的说明（\\n{{…|词}}，可分几行）在文章里接在词后面：本身没有一对括号整个括住的，外面加（）——
    09 resilient 的说明“（人或动物）对困境有承受力的，有复原力的”原样接上会和后文连成一句；08 declined to、set out to 本来就整个括住，不变"""
    def rep(m):
        t=''.join(re.findall(r'\{\{([^|{}]+)\|[^{}]+\}\}',m.group(0))); dep=0; whole=t.startswith('（') and t.endswith('）')
        for i,ch in enumerate(t):
            dep+=(ch=='（')-(ch=='）')
            if whole and dep==0 and i<len(t)-1: whole=False
        return t if whole else '（'+t+'）'
    return re.sub(r'\n?\{\{[^|{}]+\|([^{}]+)\}\}(?:\n?\{\{[^|{}]+\|\1\}\})*',rep,z)   # 只把同一个词的几行连起来（03 unimpressed、assessors 两个说明挨着，各算各的）
paras_en={};paras_zh={}
for s in d['sentences']:
    en=' '.join(re.sub(r'\{\{.*?\}\}','',c['en']) for c in s['chunks'])
    zh=''.join(_gloss(c['zh']).replace('\n','') for c in s['chunks'])  # 去掉格内换行、颜色说明标记
    notes=''.join(c['note'].replace('#Y','').replace('\n','') for c in s['chunks'] if c.get('note'))   # note 里的 \n 只是屏幕上分行，文章里连成一段（06 S18、08 S10）
    paras_en.setdefault(s['para'],[]).append(en); paras_zh.setdefault(s['para'],[]).append(zh+notes)
new_en='\n\n'.join(' '.join(v) for k,v in sorted(paras_en.items()))
strip=lambda x:re.sub(r'[\*\s]','',x)
assert strip(new_en)==strip(en_old), 'English text changed!'
new_zh='\n\n'.join(''.join(v) for k,v in sorted(paras_zh.items()))
# keyword table in order of appearance
rows=[];seen=set()
for s in d['sentences']:
    for c in s['chunks']:
        zmap={}
        for z,e in re.findall(r'\*\*([^*]+)\*\*\(([^)]+)\)',c['zh']):   # 被隔开的同一个意思（T23：证明了……正确的、把……比作）连起来，原来只留最后一段（08 vindicating 成了“正确的”）
            zmap[e.lower()]=zmap[e.lower()]+'……'+z if e.lower() in zmap else z
        ens=re.findall(r'\*\*([^*]+)\*\*',c['en'])
        keys=[e for _,e in re.findall(r'\*\*([^*]+)\*\*\(([^)]+)\)',c['zh'])]
        for w in keys:
            w=next((x for x in ens if x.lower()==w.lower()),w)
            if w.lower() in seen: continue
            seen.add(w.lower())
            old=old_rows.get(w.lower()) or next((v for k,v in old_rows.items() if k in w.lower().split() or w.lower().startswith(k)),'')
            pos=(re.match(r'^([a-z./]+\.)',old) or [None,''])[1] if old else ''
            z_=zmap.get(w.lower(),''); ob_=old_bw.get(w.lower(),'')
            if z_ and ob_.startswith(z_): z_=ob_          # 原来的“本文：”以现在的意思开头（后面跟着括号说明，如 08 inquiry），原样保留
            rows.append(f"| {w} | 本文：{z_}" + (f"；{old}" if old else '') + f" | {s['para']} |")
tbl='| 词 | 释义 | 段 |\n|---|---|---|\n'+'\n'.join(rows)+'\n'
out=head+'## 英文\n'+new_en+'\n\n## 中文\n\n'+new_zh+'\n\n## 速查表\n'+tbl+'\n## '+after
open(md,'w').write(out); print(len(rows),'rows')
