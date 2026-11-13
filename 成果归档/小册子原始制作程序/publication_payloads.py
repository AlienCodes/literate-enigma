import json,hashlib,sys
from pathlib import Path
from booklet_utils import ROOT,validate_article

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def payload(n):
    cp=ROOT/'content/articles'/f'{n}.json';d=json.loads(cp.read_text());validate_article(d)
    q=json.loads((ROOT/'production'/n/'qc.json').read_text())
    if not q['passed'] or q.get('engine_revision')!=3 or q['content_sha256']!=sha(cp):raise ValueError(f'{n}: stale PDF')
    review_path=ROOT/'reviews'/f'{n}.json'
    if not review_path.exists():raise ValueError(f'{n}: independent review pending')
    review=json.loads(review_path.read_text())
    if not review['passed'] or review['content_sha256']!=q['content_sha256'] or review['illustration_sha256']!=q['image_sha256']:raise ValueError(f'{n}: review not current')
    if not review.get('pdf_visual_review') or review.get('reviewed_pdf_sha256')!=q['pdf_sha256']:raise ValueError(f'{n}: finalPDFvisualreviewnotcurrent')
    if sha(q['pdf'])!=q['pdf_sha256']:raise ValueError(f'{n}: PDF changed')
    pm=json.loads((ROOT/'production'/n/'preview-manifest.json').read_text())
    if pm['pdf_sha256']!=q['pdf_sha256']:raise ValueError(f'{n}: stale preview')
    if q['bytes']>10*1024*1024:raise ValueError(f'{n}: PDF over upload cap')
    j=ROOT/'publication'/f'{n}.json'
    return {'id':n,'title_zh':d['title_zh'],'title_en':d['title_en'],'pages':q['pages'],'pdf':q['pdf'],'pdf_sha256':q['pdf_sha256'],'content_sha256':q['content_sha256'],'review_sha256':sha(review_path),'preview_pages':pm['pages'],'previous':json.loads(j.read_text()) if j.exists() else {}}

if __name__=='__main__':
    out=[];pending=[]
    for n in sys.argv[1:]:
        try:out.append(payload(f'{int(n):02d}'))
        except Exception as e:pending.append({'id':n,'pending':str(e)})
    print(json.dumps({'ready':out,'pending':pending},ensure_ascii=False))
