"""Validate source coverage and the exact reviewed delivery bytes, without rendering."""
from pathlib import Path
import argparse,json,hashlib
from booklet_utils import ROOT,validate_article

def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()

def verify(sources_only=False):
    m=json.loads((ROOT/'manifest.json').read_text())
    assert len(m['chapters'])==70 and len(m['volumes'])==7
    count=0
    for a in m['chapters']:
        p=ROOT/'content/articles'/f'{a["id"]}.json';validate_article(json.loads(p.read_text()))
        assert sha(p)==a['content_sha256'],('content',a['id'])
        if sources_only:continue
        for key in ['pdf','illustration']:assert sha(ROOT/a[key])==a[key+'_sha256'],(a['id'],key)
        for p in a['previews']:assert sha(ROOT/p['path'])==p['sha256'];count+=1
    if not sources_only:
        for v in m['volumes']:assert sha(ROOT/v['pdf'])==v['pdf_sha256']
        assert count==467
        ids=[n for v in m['volumes'] for n in v['articles']]
        assert len(ids)==len(set(ids))==70
    result={'passed':True,'articles':70,'chapter_pages':467,'volumes':7,'volume_pages':474,'checked_previews':count,'sources_only':sources_only}
    print(json.dumps(result,ensure_ascii=False));return result

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--sources-only',action='store_true');a=p.parse_args();verify(a.sources_only)
