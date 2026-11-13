from pathlib import Path
import importlib.util
import json
import re
import hashlib
import shutil
from datetime import datetime, timezone
from PIL import Image

ROOT = Path('/workspace/work/booklet70')
spec = importlib.util.spec_from_file_location('booklet_utils_49_60', ROOT/'booklet_utils.py')
U = importlib.util.module_from_spec(spec)
spec.loader.exec_module(U)
IDS = [f'{i:02}' for i in range(49,61)]

def update_progress():
    content = [n for n in IDS if (ROOT/'content/articles'/f'{n}.json').is_file()]
    art = [n for n in IDS if (ROOT/'illustrations'/f'{n}.png').is_file() and (ROOT/'illustrations'/f'{n}.json').is_file()]
    U.atomic_json(ROOT/'progress/group_49_60.json', {
        'group':'49–60', 'assigned_ids':IDS, 'content_ready':content,
        'illustrations_ready':art, 'ready_ids':[n for n in IDS if n in content and n in art],
        'blockers':[], 'updated_utc':datetime.now(timezone.utc).isoformat()
    })

def context_phrase(no, term):
    s=U.source(no)
    full=' '.join(s['english_paragraphs'])
    for occurrence in s['highlighted_occurrences']:
        if occurrence['term'] != term:
            continue
        context=occurrence['english_context']
        if context not in full:
            continue
        match=re.search(r'(?<![A-Za-z])'+re.escape(term)+r'(?![A-Za-z])',context)
        if not match:
            match=re.search(re.escape(term),context)
        if not match:
            continue
        if len(context)<=38:
            return context
        tokens=list(re.finditer(r'\S+',context))
        a=next(i for i,t in enumerate(tokens) if t.end()>match.start())
        b=next(i for i,t in enumerate(tokens) if t.end()>=match.end())
        while True:
            candidates=[]
            if a>0 and tokens[b].end()-tokens[a-1].start()<=38:
                candidates.append((a-1,b))
            if b+1<len(tokens) and tokens[b+1].end()-tokens[a].start()<=38:
                candidates.append((a,b+1))
            if not candidates:
                break
            a,b=max(candidates,key=lambda z:tokens[z[1]].end()-tokens[z[0]].start())
        phrase=context[tokens[a].start():tokens[b].end()]
        if len(phrase)<=38 and term in phrase and phrase in full:
            return phrase
    raise ValueError(('No exact short context',no,term))

def save(no, zh, lexicon, core, question_specs, cover, scene, reading_note=''):
    no=f'{int(no):02}'
    assert no in IDS
    entries={}
    for line in lexicon.strip().splitlines():
        term,headword,pos,meaning=line.split('|')
        assert term not in entries,(no,term)
        entries[term]={'source_term':term,'headword':headword,'form_in_text':term,
                       'pos':pos,'meaning_zh':meaning,'core':term in core,
                       'context_phrase':context_phrase(no,term) if term in core else ''}
    terms=U.terms(no)
    assert set(entries)==set(terms),(no,'missing',set(terms)-set(entries),'extra',set(entries)-set(terms))
    assert len(core)==len(set(core))==22 and set(core)<=set(terms)
    questions=[]
    full=' '.join(U.source(no)['english_paragraphs'])
    for excerpt,answer in question_specs:
        assert excerpt in full and answer in excerpt and len(excerpt)<=180,(no,excerpt)
        questions.append({'text_with_blank':excerpt.replace(answer,'______',1),'answer':answer})
    style=(ROOT/'illustration-style-standard.txt').read_text().strip()
    prompt=style+'\n\nARTICLE-SPECIFIC SCENE:\n'+scene
    d=U.save_article(no,zh,[entries[t] for t in terms],questions,cover,reading_note,prompt)
    update_progress()
    return U.validate_article(d)

def record_image(no, generation_path, review_notes):
    no=f'{int(no):02}'
    assert no in IDS
    generated=Path(generation_path)
    assert generated.is_file(),generation_path
    output=ROOT/'illustrations'/f'{no}.png'
    output.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(generated,output)
    with Image.open(output) as im:
        dimensions=list(im.size)
        assert im.format=='PNG'
    article=json.loads((ROOT/'content/articles'/f'{no}.json').read_text())
    U.atomic_json(ROOT/'illustrations'/f'{no}.json',{
        'id':no,'generation_path':str(generated),'prompt':article['illustration_prompt'],
        'sha256':hashlib.sha256(output.read_bytes()).hexdigest(),'dimensions':dimensions,
        'visual_source_review':review_notes,'created_utc':datetime.now(timezone.utc).isoformat()
    })
    update_progress()
    return {'id':no,'path':str(output),'dimensions':dimensions}

update_progress()
