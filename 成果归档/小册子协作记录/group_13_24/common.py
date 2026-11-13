from pathlib import Path
import hashlib,json,sys
from PIL import Image
sys.path.insert(0,'/workspace/work/booklet70')
import booklet_utils as b
ROOT=b.ROOT
OWN=[f'{i:02}' for i in range(13,25)]

def lex(no,tsv):
    out=[]
    for row in tsv.strip().splitlines():
        x=row.split('|')
        assert len(x)==5,(no,row)
        term,head,pos,meaning,phrase=x
        out.append(dict(source_term=term,headword=head or term.lower(),form_in_text=term,pos=pos,meaning_zh=meaning,core=bool(phrase),context_phrase=phrase))
    assert [x['source_term'] for x in out]==b.terms(no),(no,'vocabulary source order or coverage differs')
    assert sum(x['core'] for x in out)==22,(no,'core count',sum(x['core'] for x in out))
    for x in out:
        assert len(x['meaning_zh'])<=26,(no,x['source_term'],'meaning too long')
        if x['core']:assert x['source_term'] in x['context_phrase'],(no,x['source_term'],'core context misses term')
    return out

def questions(no,items):
    full=' '.join(b.source(no)['english_paragraphs']);out=[]
    for excerpt,answer in items:
        assert excerpt in full,(no,excerpt)
        assert excerpt.count(answer)==1,(no,answer)
        assert len(excerpt)<=180,(no,'question too long')
        out.append({'text_with_blank':excerpt.replace(answer,'______'),'answer':answer})
    return out

def progress():
    cr=[];ir=[]
    for no in OWN:
        cp=ROOT/'content/articles'/f'{no}.json';ip=ROOT/'illustrations'/f'{no}.png';meta=ROOT/'illustrations'/f'{no}.json'
        if cp.exists():
            b.validate_article(json.loads(cp.read_text()));cr.append(no)
        if ip.exists() and meta.exists():
            m=json.loads(meta.read_text())
            assert hashlib.sha256(ip.read_bytes()).hexdigest()==m['sha256']
            ir.append(no)
    b.atomic_json(ROOT/'progress/group_13_24.json',{'group':'13_24','assigned':OWN,'content_ready':cr,'illustrations_ready':ir,'ready':[n for n in OWN if n in cr and n in ir],'status':'complete' if len(cr)==len(ir)==12 else 'in_progress','actual_blockers':[]})

def save(no,zh,vocab,qa,question,note=''):
    prompt=(ROOT/'workers/group_13_24'/f'{no}-prompt.txt').read_text().strip()
    d=b.save_article(no,chinese_paragraphs=zh,vocabulary=lex(no,vocab),questions=questions(no,qa),cover_question=question,reading_note=note,illustration_prompt=prompt)
    progress();print(b.validate_article(d))

def artwork(no,path,visual_notes,source_notes):
    assert no in OWN
    import shutil
    src=Path(path);dest=ROOT/'illustrations'/f'{no}.png'
    assert src.is_file() and src.suffix=='.png'
    shutil.copy2(src,dest)
    with Image.open(dest) as im:size=list(im.size)
    assert size[0]*2==size[1]*3,(no,size)
    prompt=(ROOT/'workers/group_13_24'/f'{no}-prompt.txt').read_text().strip()
    b.atomic_json(ROOT/'illustrations'/f'{no}.json',{'id':no,'original_generation_path':str(src),'image_path':str(dest),'prompt':prompt,'sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'image_size':size,'visual_review':visual_notes,'source_review':source_notes,'status':'generated_and_visually_reviewed'})
    progress();print({'artwork':no,'size':size,'sha256':hashlib.sha256(dest.read_bytes()).hexdigest()})
