"""Verify the two actual videos' public remote bytes in both repositories."""
from pathlib import Path
import datetime,hashlib,json,urllib.parse,urllib.request

HERE=Path(__file__).resolve().parent
meta=json.loads((HERE/'prepared-archive.json').read_text())
asset=json.loads((HERE/'asset-local.json').read_text())
rows=[]
for repo in ['alienalgorithm/postgraduate-vocabulary','AlienCodes/literate-enigma']:
 for video in meta['articles']:
  url='https://raw.githubusercontent.com/'+repo+'/'+asset['asset_commit']+'/'+urllib.parse.quote(video['video_repo_path'],safe='/')
  h=hashlib.sha256();n=0
  with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Codex-archive-byte-verification'}),timeout=30) as r:
   status=r.status
   while True:
    chunk=r.read(1024*1024)
    if not chunk:break
    n+=len(chunk);h.update(chunk)
  assert n==video['bytes'] and h.hexdigest()==video['sha256']
  row={'repository':repo,'source_id':video['source_id'],'new_id':video['new_id'],'pinned_asset_commit':asset['asset_commit'],
       'repo_path':video['video_repo_path'],'http_status':status,'bytes':n,'sha256':h.hexdigest(),'passed':True}
  rows.append(row);print(json.dumps(row,ensure_ascii=False),flush=True)
report={'passed':True,'scope':'Actual new book35 and63 only; no all70 or Release assertion',
        'method':'Pinned public HTTPS MP4 bytes streamed without writing duplicate videos',
        'checked_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'streams':rows,'temporary_videos_written':False}
(HERE/'remote-video-byte-verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(report,ensure_ascii=False),flush=True)
