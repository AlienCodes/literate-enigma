from pathlib import Path
import json, re, hashlib

ROOT=Path(__file__).resolve().parent
SOURCE_COMMIT='9374187e740fcefef39e42259a2f057ae504ebc9'

def atomic_json(path,data):
    p=Path(path);p.parent.mkdir(parents=True,exist_ok=True)
    tmp=p.with_name(p.name+'.tmp')
    tmp.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
    tmp.replace(p)

def source(no):
    return json.loads((ROOT/'sources'/f'{int(no):02}.json').read_text())

def terms(no):
    return list(dict.fromkeys(x['term'] for x in source(no)['highlighted_occurrences']))

def seed_meanings(no):
    s=source(no);out={}
    for x in s['highlighted_occurrences']:
        for zh,en in re.findall(r'\*\*([^*]+)\*\*\s*[（(]([^）)]+)[）)]',x['chinese_context']):
            if en.lower().strip()==x['term'].lower():out.setdefault(x['term'],zh)
    return out

def validate_article(d):
    n=d['id'];s=source(n);t=terms(n)
    assert d['source_commit']==SOURCE_COMMIT
    assert d['english_paragraphs']==s['english_paragraphs'],f'{n}: English changed'
    assert d['title_en']==s['title_en'] and d['title_zh']==s['title_zh']
    assert len(d['chinese_paragraphs'])==len(s['english_paragraphs']),f'{n}: paragraph count'
    assert all(isinstance(x,str) and x.strip() and '**' not in x for x in d['chinese_paragraphs'])
    v=d['vocabulary'];assert [x['source_term'] for x in v]==t,f'{n}: vocabulary coverage/order'
    assert sum(x['core'] is True for x in v)==22,f'{n}: expected22 core items'
    full=' '.join(s['english_paragraphs'])
    for e in v:
        assert all(isinstance(e.get(k),str) and e[k].strip() for k in ['source_term','headword','form_in_text','pos','meaning_zh'])
        assert e['form_in_text']==e['source_term']
        assert isinstance(e['core'],bool)
        if e['core']:
            assert e.get('context_phrase') and e['context_phrase'] in full,(n,e['headword'],'context not exact')
            assert len(e['context_phrase'])<=38,(n,e['headword'],'context too long')
    assert len(d['questions'])==4
    for q in d['questions']:
        assert q['text_with_blank'].count('______')==1
        assert q['answer'] and q['text_with_blank'].replace('______',q['answer']) in full,(n,q,'question not exact')
    assert isinstance(d['cover_question'],str) and 5<=len(d['cover_question'])<=40
    assert d['approved_summary']==s['approved_summary']
    return {'id':n,'paragraphs':len(d['english_paragraphs']),'vocabulary':len(v),'core':22,'valid':True}

def save_article(no,chinese_paragraphs,vocabulary,questions,cover_question,reading_note='',illustration_prompt='',**other):
    s=source(no)
    d={'id':s['id'],'source_commit':SOURCE_COMMIT,'title_en':s['title_en'],'title_zh':s['title_zh'],
       'english_paragraphs':s['english_paragraphs'],'chinese_paragraphs':chinese_paragraphs,
       'vocabulary':vocabulary,'questions':questions,'cover_question':cover_question,
       'reading_note':reading_note,'illustration_prompt':illustration_prompt,
       'approved_summary':s['approved_summary'],**other}
    validate_article(d)
    atomic_json(ROOT/'content/articles'/f'{s["id"]}.json',d)
    return d
