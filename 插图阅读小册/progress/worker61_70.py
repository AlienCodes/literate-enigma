from pathlib import Path
import sys,json,hashlib,shutil,datetime
sys.path.insert(0,'/workspace/work/booklet70')
from booklet_utils import ROOT,source,terms,save_article,atomic_json,validate_article

PROGRESS=ROOT/'progress/group_61_70.json'

def update_progress():
    d=json.loads(PROGRESS.read_text())
    assigned=[f'{i:02}' for i in range(61,71)]
    d['content_ready']=[n for n in assigned if (ROOT/f'content/articles/{n}.json').exists()]
    d['illustrations_ready']=[n for n in assigned if (ROOT/f'illustrations/{n}.png').exists() and (ROOT/f'illustrations/{n}.json').exists()]
    d['ready']=[n for n in assigned if n in d['content_ready'] and n in d['illustrations_ready']]
    d['updated_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
    d['status']='complete' if len(d['ready'])==10 else 'producing content and unique artwork progressively'
    atomic_json(PROGRESS,d)

def write(no,zh,rows,core,questions,cover,scene,reading_note=''):
    no=f'{int(no):02}'
    s=source(no);full=' '.join(s['english_paragraphs'])
    parsed={}
    for line in rows.strip().splitlines():
        term,head,pos,meaning=line.split('|')
        assert term not in parsed,(no,'duplicate vocabulary row',term)
        parsed[term]={'source_term':term,'headword':head or term.lower(),'form_in_text':term,'pos':pos,'meaning_zh':meaning,'core':term in core,'context_phrase':core.get(term,'')}
    assert set(parsed)==set(terms(no)),(no,'vocabulary rows mismatch',set(terms(no))-set(parsed),set(parsed)-set(terms(no)))
    assert len(core)==22,(no,'core count',len(core))
    for t,c in core.items():
        assert t in c and c in full and len(c)<=38,(no,t,c,len(c))
    q=[]
    for answer,phrase in questions:
        assert len(phrase)<=180 and phrase in full,(no,'question source',phrase)
        assert answer in phrase,(no,'question answer',answer)
        q.append({'text_with_blank':phrase.replace(answer,'______',1),'answer':answer})
    meta=ROOT/f'illustrations/{no}.json'
    prompt=json.loads(meta.read_text())['exact_prompt'] if meta.exists() else (ROOT/'illustration-style-standard.txt').read_text().strip()+'\n\n'+scene
    d=save_article(no,chinese_paragraphs=zh,vocabulary=[parsed[t] for t in terms(no)],questions=q,cover_question=cover,reading_note=reading_note,illustration_prompt=prompt)
    atomic_json(ROOT/f'progress/scene_{no}.json',{'id':no,'scene':scene,'prompt':prompt})
    update_progress()
    print(json.dumps(validate_article(d),ensure_ascii=False))
    return d

def register_art(no,path,prompt,output_hint,notes):
    no=f'{int(no):02}'
    src=Path(path);dst=ROOT/f'illustrations/{no}.png';dst.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(src,dst)
    atomic_json(dst.with_suffix('.json'),{'id':no,'source_commit':source(no)['source_commit'],'original_generation_path':str(src),'output_hint':output_hint,'exact_prompt':prompt,'image_path':str(dst),'sha256':hashlib.sha256(dst.read_bytes()).hexdigest(),'visual_source_review':{'status':'PASS','notes':notes}})
    content=ROOT/f'content/articles/{no}.json'
    if content.exists():
        d=json.loads(content.read_text());d['illustration_prompt']=prompt;validate_article(d);atomic_json(content,d)
    update_progress()
    print(no,'artwork copied from its exact generation path',hashlib.sha256(dst.read_bytes()).hexdigest())
