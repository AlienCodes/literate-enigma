"""Read the pinned public PDF chunks over HTTPS without saving another PDF."""
from pathlib import Path
import datetime, hashlib, json, urllib.parse, urllib.request

HERE = Path(__file__).resolve().parent
MANIFEST = HERE/'archive-payload/考研学人印刷版/2026-11-13-v4/整本/parts-manifest.json'
PIN = '8404ddff99dfa094aa005fec70643d9da55e21fc'
m = json.loads(MANIFEST.read_text())
overall = hashlib.sha256()
records = []
total = 0
for part in m['parts']:
    url = 'https://raw.githubusercontent.com/'+m['repository']+'/'+PIN+'/'+urllib.parse.quote(part['repo_path'], safe='/')
    start = overall.copy()
    for attempt in range(1, 4):
        h = hashlib.sha256(); n = 0; overall = start.copy()
        try:
            req = urllib.request.Request(url, headers={'User-Agent':'Codex-PDF-archive-verification'})
            with urllib.request.urlopen(req, timeout=30) as response:
                status = response.status
                while True:
                    chunk = response.read(1024*1024)
                    if not chunk: break
                    h.update(chunk); overall.update(chunk); n += len(chunk)
            assert n == part['bytes'], (n, part['bytes'])
            assert h.hexdigest() == part['sha256'], 'Actual HTTPS PDF-part bytes mismatch'
            break
        except Exception as exc:
            print(json.dumps({'part':part['index'], 'attempt':attempt,'error':str(exc)},ensure_ascii=False),flush=True)
            if attempt == 3: raise
    total += n
    row = {'index':part['index'],'repo_path':part['repo_path'],'http_status':status,
           'bytes':n,'sha256':h.hexdigest(),'expected_sha256':part['sha256'],'passed':True}
    records.append(row); print(json.dumps(row,ensure_ascii=False),flush=True)
assert total == m['bytes'] and overall.hexdigest() == m['sha256']
report = {'passed':True,'method':'actual pinned public HTTPS chunk bytes streamed in manifest order; no PDF written',
          'repository':m['repository'],'pinned_commit':PIN,'parts':records,'bytes':total,
          'sha256':overall.hexdigest(),'pages_from_approved_manifest':m['pages'],
          'checked_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
          'temporary_full_pdf_created':False}
(HERE/'remote-book-stream-verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(report,ensure_ascii=False),flush=True)
