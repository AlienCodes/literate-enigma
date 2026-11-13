import sys,json,re,hashlib,shutil
from pathlib import Path
sys.path.insert(0,'/workspace/work/booklet70')
import booklet_utils as U
ROOT=U.ROOT
PROGRESS=ROOT/'progress/group_37_48.json'

def progress():
    content=[];images=[]
    for n in range(37,49):
        no=f'{n:02}'
        if (ROOT/'content/articles'/f'{no}.json').exists():content.append(no)
        if (ROOT/'illustrations'/f'{no}.png').exists() and (ROOT/'illustrations'/f'{no}.json').exists():images.append(no)
    U.atomic_json(PROGRESS,{'group':'37_48','content_ready':content,'illustrations_ready':images,'complete_ids':[x for x in content if x in images],'blockers':[]})

def context(full,term):
    m=re.search(r'(?<!\w)'+re.escape(term)+r'(?!\w)',full)
    if not m:raise ValueError(('term not found',term))
    lo=m.start();hi=m.end()
    # Add surrounding complete words without changing one source character.
    for _ in range(2):
        prev=full.rfind(' ',0,max(0,lo-1))+1
        if hi-prev>38 or prev==lo:break
        lo=prev
    for _ in range(3):
        nxt=full.find(' ',hi+1)
        if nxt<0:nxt=len(full)
        if nxt-lo>38 or nxt==hi:break
        hi=nxt
    out=full[lo:hi].strip()
    assert term in out and out in full and len(out)<=38,(term,out)
    return out

def build(no,zh,entry_rows,core,answers,question,prompt,note=''):
    no=f'{int(no):02}';s=U.source(no);full=' '.join(s['english_paragraphs'])
    info={}
    for line in entry_rows.strip().splitlines():
        t,h,p,m=line.split('|',3);info[t]=(h,p,m)
    ts=U.terms(no);assert set(ts)==set(info),(no,set(ts)-set(info),set(info)-set(ts))
    assert len(core)==22 and len(set(core))==22,(no,len(core))
    vocab=[]
    for t in ts:
        h,p,m=info[t];vocab.append({'source_term':t,'form_in_text':t,'headword':h,'pos':p,'meaning_zh':m,'core':t in core,'context_phrase':context(full,t) if t in core else ''})
    questions=[]
    sentences=[x.strip() for para in s['english_paragraphs'] for x in re.split(r'(?<=[.!?])\s+',para)]
    for ans in answers:
        sent=next(x for x in sentences if re.search(r'(?<!\w)'+re.escape(ans)+r'(?!\w)',x))
        if len(sent)>180:
            m=re.search(r'(?<!\w)'+re.escape(ans)+r'(?!\w)',sent);lo=sent.rfind(' ',0,max(0,m.start()-55))+1;hi=sent.find(' ',min(len(sent)-1,lo+175));hi=len(sent) if hi<0 else hi;sent=sent[lo:hi]
        q=re.sub(r'(?<!\w)'+re.escape(ans)+r'(?!\w)','______',sent,count=1)
        assert q.replace('______',ans) in full
        questions.append({'text_with_blank':q,'answer':ans})
    U.save_article(no,zh,vocab,questions,question,reading_note=note,illustration_prompt=prompt)
    progress();print(json.dumps(U.validate_article(json.loads((ROOT/'content/articles'/f'{no}.json').read_text())),ensure_ascii=False))

def record_image(no,path,prompt,notes):
    no=f'{int(no):02}';src=Path(path);assert src.is_file(),str(src)
    dest=ROOT/'illustrations'/f'{no}.png';dest.parent.mkdir(exist_ok=True,parents=True);shutil.copy2(src,dest)
    from PIL import Image
    size=Image.open(dest).size
    U.atomic_json(dest.with_suffix('.json'),{'article':no,'original_generation_path':str(src),'illustration_prompt':prompt,'sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'size':list(size),'visual_source_review':notes,'actual_imagegen':True})
    progress();print(json.dumps({'article':no,'image':str(dest),'size':size,'sha256':hashlib.sha256(dest.read_bytes()).hexdigest()},ensure_ascii=False))

if __name__=='__main__':progress()
