"""Signature helper for the independently reviewed 13–24 group only.

Call sign only after actually viewing this article's current PDF contact sheet.
No rendering, source rewriting or publication is performed by this helper.
"""
from pathlib import Path
import hashlib
import json
import sys
sys.path.insert(0,'/workspace/work/booklet70')
import booklet_utils as U

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def sign(no,notes):
    no=f'{int(no):02}'
    assert 13<=int(no)<=24
    bundle=U.ROOT/'content/articles'/f'{no}.json'
    d=json.loads(bundle.read_text());U.validate_article(d)
    folder=U.ROOT/'production'/no
    q=json.loads((folder/'qc.json').read_text())
    assert q['passed'] is True and q['engine_revision']==3
    assert not (folder/'error.json').exists()
    assert q['content_sha256']==sha(bundle)
    assert q['image_sha256']==sha(U.ROOT/'illustrations'/f'{no}.png')
    assert q['pdf_sha256']==sha(q['pdf'])
    assert (folder/'contact-sheet.jpg').is_file()
    record={'id':no,'reviewer':'summaries_49_60','passed':True,
            'engine_revision':3,'content_sha256':q['content_sha256'],
            'illustration_sha256':q['image_sha256'],'pdf_visual_review':True,
            'reviewed_pdf_sha256':q['pdf_sha256'],'notes':notes}
    U.atomic_json(U.ROOT/'reviews'/f'{no}.json',record)
    return {'id':no,'passed':True,'pages':q['pages'],'engine_revision':3}
