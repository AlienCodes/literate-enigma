from pathlib import Path
import sys,re,json,hashlib,shutil
ROOT=Path('/workspace/work/booklet70');sys.path.insert(0,str(ROOT))
from booklet_utils import source,terms,save_article,atomic_json
ASSIGNED=[f'{n:02}' for n in range(2,13)]

def save_illustration(no,meta,review):
    match=re.search(r'/workspace/generated_images/[^\s]+\.png',meta['output_hint'])
    assert match,'No exact imagegen output path.'
    original=Path(match.group(0));assert original.exists()
    target=ROOT/'illustrations'/f'{no}.png';target.parent.mkdir(exist_ok=True)
    shutil.copy2(original,target)
    atomic_json(ROOT/'illustrations'/f'{no}.json',{'article':no,'original_generation_path':str(original),'prompt':meta['prompt'],'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'visual_source_review':review,'review_passed':True})
    progress()

def progress():
    content=[n for n in ASSIGNED if (ROOT/'content/articles'/f'{n}.json').exists()]
    images=[n for n in ASSIGNED if (ROOT/'illustrations'/f'{n}.png').exists() and (ROOT/'illustrations'/f'{n}.json').exists()]
    atomic_json(ROOT/'progress/group_01_12.json',{'group':'01_12','assigned':ASSIGNED,'content_ready':content,'illustrations_ready':images,'ready':[n for n in ASSIGNED if n in content and n in images],'blockers':[],'article01':'Approved sample untouched.'})

def context(s,term):
    full=' '.join(s['english_paragraphs'])
    oc=next(x for x in s['highlighted_occurrences'] if x['term']==term)
    c=oc['english_context'].strip()
    if c not in full:
        c=next(x['english'] for x in s['sentences'] if term in x['english'])
    if len(c)<=38:return c
    k=c.find(term)
    if k<0:k=c.lower().find(term.lower())
    spans=list(re.finditer(r'\S+',c));i=next(i for i,m in enumerate(spans) if m.end()>k);j=next(i for i,m in enumerate(spans) if m.end()>=k+len(term))
    lo=max(0,i-1);hi=min(len(spans),j+4)
    while len(c[spans[lo].start():spans[hi-1].end()])>38:
        if hi-1>j:hi-=1
        elif lo<i:lo+=1
        else:raise ValueError((term,'term exceeds context budget'))
    while hi-1>j and c[spans[hi-1].start():spans[hi-1].end()].lower().strip('.,;:') in {'and','or','the','a','an','of','to','with','for','in','on','as'}:hi-=1
    out=c[spans[lo].start():spans[hi-1].end()]
    assert out in full and len(out)<=38
    return out

def build(no,zh,rows,core,answers,cover,note='',prompt='',overrides=None):
    s=source(no);data={}
    for line in rows.strip().splitlines():
        t,h,p,m=line.strip().split('|');assert len(m)<=26,(t,m)
        assert t not in data,(no,'duplicate',t)
        data[t]=(h,p,m)
    assert set(data)==set(terms(no)),(no,'missing',set(terms(no))-set(data),'extra',set(data)-set(terms(no)))
    assert len(core)==22 and len(set(core))==22
    vocab=[]
    for t in terms(no):
        h,p,m=data[t];vocab.append({'source_term':t,'form_in_text':t,'headword':h,'pos':p,'meaning_zh':m,'core':t in core,'context_phrase':(overrides or {}).get(t,context(s,t)) if t in core else ''})
    questions=[]
    for answer in answers:
        sent=next(x['english'] for x in s['sentences'] if re.search(r'(?<![A-Za-z])'+re.escape(answer)+r'(?![A-Za-z])',x['english']))
        assert len(sent)<=180,(no,answer,'choose a shorter source sentence')
        questions.append({'text_with_blank':sent.replace(answer,'______',1),'answer':answer})
    d=save_article(no,zh,vocab,questions,cover,note,prompt)
    progress();return d

if __name__=='__main__':progress()
