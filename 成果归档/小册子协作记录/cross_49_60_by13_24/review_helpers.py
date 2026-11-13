from pathlib import Path
import hashlib,json,sys
sys.path.insert(0,'/workspace/work/booklet70')
import booklet_utils as b
R=b.ROOT

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def sign(no,notes):
    cp=R/'content/articles'/f'{no}.json';ip=R/'illustrations'/f'{no}.png';folder=R/'production'/no
    d=json.loads(cp.read_text());b.validate_article(d)
    q=json.loads((folder/'qc.json').read_text());pp=Path(q['pdf'])
    assert q['passed'] is True and q['engine_revision']==3
    assert not (folder/'error.json').exists()
    assert sha(cp)==q['content_sha256'] and sha(ip)==q['image_sha256'] and sha(pp)==q['pdf_sha256']
    assert (folder/'contact-sheet.jpg').is_file()
    doc={'id':no,'reviewer':'summaries_13_24','passed':True,'content_sha256':sha(cp),'illustration_sha256':sha(ip),'pdf_visual_review':True,'reviewed_pdf_sha256':sha(pp),'engine_revision':q['engine_revision'],'notes':notes}
    b.atomic_json(R/'reviews'/f'{no}.json',doc)
    print({'id':no,'signed':True,'engine_revision':q['engine_revision'],'pages':q['pages'],'pdf_sha256':doc['reviewed_pdf_sha256']})

def pending(no,blocker,notes):
    cp=R/'content/articles'/f'{no}.json';ip=R/'illustrations'/f'{no}.png'
    b.atomic_json(R/'reviews'/f'{no}.json',{'id':no,'reviewer':'summaries_13_24','passed':False,'content_sha256':sha(cp),'illustration_sha256':sha(ip),'pdf_visual_review':False,'reviewed_pdf_sha256':None,'requested_engine_revision':3,'blocker':blocker,'notes':notes})
    print({'id':no,'signed':False,'blocker':blocker})
