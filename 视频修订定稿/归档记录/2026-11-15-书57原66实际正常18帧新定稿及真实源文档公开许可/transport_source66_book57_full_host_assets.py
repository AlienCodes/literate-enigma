"""Original dual asset transport for exact d9cd book57 H after actual 9034 source-publication consent."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import argparse,hashlib,json,os,subprocess,sys
B=Path(__file__).resolve().parent
def load(p):return json.loads(Path(p).read_bytes())
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def run(cmd,path,bound=None):
 with path.open('w') as f:
  r=subprocess.run(list(map(str,cmd)),stdout=f,stderr=subprocess.STDOUT,
   env={**os.environ,'TMPDIR':str(B),'PYTHONDONTWRITEBYTECODE':'1'},timeout=bound)
 assert r.returncode==0,str(path)
def main():
 p=argparse.ArgumentParser();p.add_argument('--work-dir',required=True);a=p.parse_args();w=Path(a.work_dir).resolve()
 assert w.parent==B and B.parent==Path('/workspace/work/video-archive-batches-20261114') and B.name.startswith('book57-source66-full-host-isolated-assets-')
 h=Path('/workspace/work/review66-finalV3/43702972097-normal18/archive-handoff.json')
 assert digest(h)=='f9067006d034b698d7926db45137e8b9627a0bf263a75ac9773c80a66cc05227'
 consent=Path('/dev/shm/USER-EXPLICIT-EIGHT-FINAL-SOURCE-DOCUMENT-PUBLICATION-CONSENT-20261115.json')
 assert digest(consent)=='9034beaf30fc4afcfcaf1a84197f01ca4ed3f1a0b64e2ae4dcf971c823eda3b0'
 m=load(w/'prepared-archive.json');row=m['articles'][0]
 assert len(m['articles'])==1 and row['source_id']=='66' and row['new_id']=='57'
 assert row['passed_per_article'] is True and row['production_delivery_eligible'] is True and row['preview_only'] is False
 assert row['sha256']=='2ef42f9ac36a375d230d94578130e481f7b97e23018a525612bd117cae5028da' and row['bytes']==14891869
 assert row['postprocessing_full_V3_handoff_sha256']==digest(h)
 assert any(x['sha256']==digest(consent) for x in m['material_source_bindings'])
 assert not (w/'assets.git').exists() and not (w/'asset-local.json').exists()
 for role,repo in [('primary','alienalgorithm/postgraduate-vocabulary'),('backup','AlienCodes/literate-enigma')]:
  run([sys.executable,B/'archive_batch.py','push','--work-dir',w,'--repo',repo],w/f'assets-{role}-transport.log',180)
 count=len(load(w/'payload-file-index.json'))
 with ThreadPoolExecutor(max_workers=2) as pool:
  f=pool.submit(run,[sys.executable,B/'archive_batch.py','stream','--work-dir',w],w/'actual-dual-full-MP4-HTTP.log',120)
  g=pool.submit(run,[sys.executable,B/'verify_dual_media_asset_blobs.py','--work-dir',w,'--expected-files',count],w/'actual-dual-Git-blobs.log',300)
  f.result();g.result()
 ready=B/'ready-book57-source66-full.json'
 run([sys.executable,B/'emit_ready_revision_download_manifest.py','--work-dir',w,'--handoff',h,'--output',ready],w/'actual-ready-manifest.log',30)
 print(json.dumps({'ready':str(ready),'ready_sha256':digest(ready),'source_id':'66','book_order':'57','files':count,
  'actual_both_whole_HTTP_and_all_blobs_closed':True,'source_publication_consent_sha256':digest(consent),
  'no_current_change_by_asset_transport':True}),flush=True)
 run([sys.executable,B/'cleanup_closed_media_asset_bare.py','--work-dir',w],w/'own-closed-Git-cleanup.log',90)
 index=w/'assets.index'
 if index.exists():assert not index.is_symlink() and index.parent==w;index.unlink()
 print('own closed host Git cache cleaned; all payload/native/H and new consent retained',flush=True)
if __name__=='__main__':main()
