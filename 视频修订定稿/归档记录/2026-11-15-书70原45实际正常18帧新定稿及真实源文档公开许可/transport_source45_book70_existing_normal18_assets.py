"""Original dual asset transport for exact existing-source45 book70 fullV3 H and actual new project-wide source-publication consent."""
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
 assert w.parent==B and B.parent==Path('/workspace/work/video-archive-batches-20261114') and B.name.startswith('book70-source45-existing-normal18-host-assets-')
 h=Path('/workspace/work/review45-finalV3/43533004625-normal18-book70-20261115/archive-handoff.json')
 assert digest(h)=='9755327747b30b8e83878836f26f4cf682ebadb851b0fd0c66e72d7e01b0564c'
 consent=Path('/workspace/work/all-project-deliverables-and-final70-release-authorities-20261115/USER-ALL-PROJECT-GENERATED-DELIVERABLES-GITHUB-ARCHIVE-AUTHORITY.json')
 assert digest(consent)=='b00a133cc88ed37496e225a181898863ce52e9a774e6b5c2991a310691fd4312'
 m=load(w/'prepared-archive.json');row=m['articles'][0]
 assert len(m['articles'])==1 and row['source_id']=='45' and row['new_id']=='70'
 assert row['passed_per_article'] is True and row['production_delivery_eligible'] is True and row['preview_only'] is False
 assert row['sha256']=='c72753547d18ca0f9e9041ef41de9502d25d31e39295a2488c2886cec6bccef8' and row['bytes']==15768989
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
 ready=B/'ready-book70-source45-existing-normal18.json'
 run([sys.executable,B/'emit_ready_revision_download_manifest.py','--work-dir',w,'--handoff',h,'--output',ready],w/'actual-ready-manifest.log',30)
 print(json.dumps({'ready':str(ready),'ready_sha256':digest(ready),'source_id':'45','book_order':'70','files':count,
  'actual_both_whole_HTTP_and_all_blobs_closed':True,'source_publication_consent_sha256':digest(consent),
  'no_current_change_by_asset_transport':True}),flush=True)
 run([sys.executable,B/'cleanup_closed_media_asset_bare.py','--work-dir',w],w/'own-closed-Git-cleanup.log',90)
 index=w/'assets.index'
 if index.exists():assert not index.is_symlink() and index.parent==w;index.unlink()
 print('own closed host Git cache cleaned; all payload/native/H and new consent retained',flush=True)
if __name__=='__main__':main()
