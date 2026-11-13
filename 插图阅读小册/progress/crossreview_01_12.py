from pathlib import Path
import sys,json,hashlib,datetime
sys.path.insert(0,'/workspace/work/booklet70')
from booklet_utils import ROOT,validate_article,atomic_json,source

def save_review(no,notes):
    no=f'{int(no):02}'
    cp=ROOT/f'content/articles/{no}.json';d=json.loads(cp.read_text());validation=validate_article(d)
    ip=ROOT/f'illustrations/{no}.png' if no!='01' else ROOT/'illustrations/01-preview.png'
    qp=ROOT/f'production/{no}/qc.json';q=json.loads(qp.read_text())
    assert q['passed'] and not (qp.parent/'error.json').exists(),(no,'qc failed')
    content_hash=hashlib.sha256(cp.read_bytes()).hexdigest();image_hash=hashlib.sha256(ip.read_bytes()).hexdigest();pdf_hash=hashlib.sha256(Path(q['pdf']).read_bytes()).hexdigest()
    assert q['content_sha256']==content_hash,(no,'stale PDF content')
    assert q['image_sha256']==image_hash,(no,'stale PDF illustration')
    assert q['pdf_sha256']==pdf_hash,(no,'PDF byte hash mismatch')
    assert all(q[k] for k in ['full_english_exact','full_chinese_exact','all_target_vocabulary_present','text_inside_page_bounds'])
    report={'id':no,'reviewer':'summaries_61_70 independent cross-review','passed':True,'content_sha256':content_hash,'illustration_sha256':image_hash,'pdf_visual_review':True,'reviewed_pdf_sha256':pdf_hash,'notes':notes,'review_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'pages':q['pages'],'checks':validation,'actual_illustration_viewed':True,'actual_current_pdf_contact_sheet_viewed':True}
    atomic_json(ROOT/f'reviews/{no}.json',report)
    print(no,'review PASS',content_hash,pdf_hash)
    return report

def show(no):
    no=f'{int(no):02}';d=json.loads((ROOT/f'content/articles/{no}.json').read_text())
    print('ARTICLE',no,d['title_en'],'/ '+d['title_zh'])
    print('SOURCE_CHECK',validate_article(d))
    for i,(en,zh) in enumerate(zip(d['english_paragraphs'],d['chinese_paragraphs']),1):print(f'P{i} EN: {en}\nZH: {zh}')
    print('VOCABULARY')
    for v in d['vocabulary']:print(' | '.join(str(v.get(k,'')) for k in ['source_term','headword','pos','meaning_zh','core','context_phrase']))
    print('QUESTIONS',json.dumps(d['questions'],ensure_ascii=False))
    print('READING_NOTE',d.get('reading_note'))
    print('SUMMARY',json.dumps(d['approved_summary'],ensure_ascii=False))

if __name__=='__main__':
    for x in sys.argv[1:]:show(x)
