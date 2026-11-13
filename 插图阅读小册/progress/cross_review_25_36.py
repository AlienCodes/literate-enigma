import sys,json,hashlib
from pathlib import Path
sys.path.insert(0,'/workspace/work/booklet70')
import booklet_utils as U
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def finish(no,notes):
    no=f'{int(no):02}';assert 25<=int(no)<=36
    p=U.ROOT/'content/articles'/f'{no}.json';d=json.loads(p.read_text());U.validate_article(d)
    prod=U.ROOT/'production'/no;assert not (prod/'error.json').exists()
    q=json.loads((prod/'qc.json').read_text());image=U.ROOT/'illustrations'/f'{no}.png';pdf=Path(q['pdf'])
    assert q['passed'] and q['content_sha256']==sha(p) and q['image_sha256']==sha(image) and q['pdf_sha256']==sha(pdf)
    assert (prod/'contact-sheet.jpg').is_file()
    out={'id':no,'reviewer':'summaries_37_48','passed':True,'content_sha256':sha(p),'illustration_sha256':sha(image),'pdf_visual_review':True,'reviewed_pdf_sha256':sha(pdf),'engine_revision':q.get('engine_revision'),'notes':notes}
    U.atomic_json(U.ROOT/'reviews'/f'{no}.json',out)
    print(json.dumps(out,ensure_ascii=False))
