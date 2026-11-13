import json, sys, hashlib
from pathlib import Path
sys.path.insert(0, '/workspace/work/booklet70')
from booklet_utils import ROOT
from publication_payloads import payload

def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

ready, pending, failures, known = [], [], [], []
for number in range(1, 71):
    no = f'{number:02}'
    journal_path = ROOT / 'publication' / f'{no}.json'
    if not journal_path.exists():
        pending.append({'id': no, 'reason': 'publication journal not yet present'})
        continue
    try:
        j = json.loads(journal_path.read_text())
        if j.get('page_id'):
            known.append({'id': no, 'page_id': j['page_id']})
        if j.get('status') != 'complete':
            pending.append({'id': no, 'page_id': j.get('page_id'), 'reason': 'publication status ' + str(j.get('status'))})
            continue
        p = payload(no)
        q = json.loads((ROOT / 'production' / no / 'qc.json').read_text())
        art = ROOT / 'illustrations' / ('01-preview.png' if no == '01' else f'{no}.png')
        assert sha(art) == q['image_sha256'], 'current illustration hash mismatch'
        assert not (ROOT / 'production' / no / 'error.json').exists(), 'production error present'
        assert j['pdf_sha256'] == p['pdf_sha256'] == j['pdf_attachment']['sha256'], 'PDF digest mismatch'
        assert j['content_sha256'] == p['content_sha256'], 'content digest mismatch'
        assert j['pages'] == p['pages'] == len(j['previews']), 'preview count mismatch'
        assert j['pdf_attachment']['file_access_confirmed'], 'PDF access unconfirmed'
        assert j['pdf_attachment']['page_id'] == j['page_id'], 'PDF uploaded to another Page'
        assert j['pdf_attachment']['mime_type'] == 'application/pdf', 'PDF MIME mismatch'
        assert j['user_preview_matches_download'], 'preview/download identity unconfirmed'
        expected = {v['page']: v for v in p['preview_pages']}
        uploaded = sorted(j['previews'], key=lambda v: v['page'])
        assert [v['page'] for v in uploaded] == list(range(1, p['pages'] + 1)), 'page numbers not contiguous'
        for v in uploaded:
            e = expected[v['page']]
            assert v['file_access_confirmed'], 'preview access unconfirmed'
            assert v['sha256'] == e['sha256'] == sha(e['path']), 'preview digest mismatch'
            assert v['page_id'] == j['page_id'], 'preview uploaded to another Page'
            assert v['mime_type'].startswith('image/'), 'preview MIME mismatch'
        assert len({v['reference'] for v in uploaded}) == p['pages'], 'reused preview asset'
        ready.append({'id': no, 'page_id': j['page_id'], 'url': j['url'], 'title': j['title'],
                      'pages': p['pages'], 'pdf_sha256': p['pdf_sha256'],
                      'content_sha256': p['content_sha256'], 'journal_sha256': sha(journal_path),
                      'pdf_markdown': j['pdf_attachment']['markdown'],
                      'previews': [{k: v[k] for k in ['page', 'sha256', 'markdown', 'reference']} for v in uploaded],
                      'local_checks_passed': True})
    except Exception as exc:
        failures.append({'id': no, 'error': str(exc)})
ids = [v['page_id'] for v in known]
duplicates = [{'page_id': value, 'ids': [v['id'] for v in known if v['page_id'] == value]}
              for value in sorted(set(ids)) if ids.count(value) > 1]
print(json.dumps({'ready': ready, 'pending': pending, 'local_failures': failures,
                  'known_page_ids_unique': not duplicates, 'duplicate_page_ids': duplicates}, ensure_ascii=False))
