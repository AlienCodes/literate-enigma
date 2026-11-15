"""Transport only exact148 frozen source54 final, host-only owned Git/temp, no main writes."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import argparse,hashlib,json,os,subprocess,sys
B=Path(__file__).resolve().parent
def load(p):return json.loads(Path(p).read_text())
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def run(cmd,path,bound=None):
 with path.open('w')as f:r=subprocess.run(list(map(str,cmd)),stdout=f,stderr=subprocess.STDOUT,env={**os.environ,'TMPDIR':str(B),'PYTHONDONTWRITEBYTECODE':'1'},timeout=bound)
 assert r.returncode==0,str(path)
def main():
 p=argparse.ArgumentParser();p.add_argument('--work-dir',required=True);a=p.parse_args();w=Path(a.work_dir).resolve();assert w.parent==B and B.parent==Path('/workspace/work/video-archive-batches-20261114') and B.name.startswith('user148-source54-host-isolated-assets-')
 h=Path('/workspace/work/review47-source54-user148-E41-actual-hold06-intake/validated/54/archive-handoff.json');assert digest(h)=='46a63b140490b461852010212e1fc850221bc0ae4bced15b482673f921cb50e7'
 m=load(w/'prepared-archive.json');row=m['articles'][0];assert len(m['articles'])==1 and row['source_id']=='54'and row['new_id']=='47'and row['passed_per_article']is True and row['production_delivery_eligible']is True and row['preview_only']is False
 assert row['sha256']=='dffa42ac5cc04d93a52a414a371d278037568f0485a3814f2f09cba86edf2fe2' and row['bytes']==22100097
 assert not(w/'assets.git').exists()and not(w/'asset-local.json').exists()
 for role,repo in [('primary','alienalgorithm/postgraduate-vocabulary'),('backup','AlienCodes/literate-enigma')]:run([sys.executable,B/'archive_batch.py','push','--work-dir',w,'--repo',repo],w/f'assets-{role}-transport.log',85)
 count=len(load(w/'payload-file-index.json'))
 with ThreadPoolExecutor(max_workers=2)as pool:
  f=pool.submit(run,[sys.executable,B/'archive_batch.py','stream','--work-dir',w],w/'actual-dual-full-MP4-HTTP.log',120);g=pool.submit(run,[sys.executable,B/'verify_dual_media_asset_blobs.py','--work-dir',w,'--expected-files',count],w/'actual-dual-Git-blobs.log',120);f.result();g.result()
 ready=B/'ready-user148-source54.json';run([sys.executable,B/'emit_ready_revision_download_manifest.py','--work-dir',w,'--handoff',h,'--output',ready],w/'actual-ready-download-manifest.log',30)
 print(json.dumps({'ready':str(ready),'ready_sha256':digest(ready),'source_id':'54','new_id':'47','files':count,'actual_both_whole_HTTP_and_blobs_closed':True,'only_host_Git_payload_TMPDIR_used':True,'current_not_changed_by_asset_transport':True}),flush=True)
 run([sys.executable,B/'cleanup_closed_media_asset_bare.py','--work-dir',w],w/'own-closed-Git-cleanup.log',90)
 index=w/'assets.index'
 if index.exists():assert not index.is_symlink()and index.parent==w;index.unlink()
 print('own closed host Git cache cleaned; all payload/native/H preserved',flush=True)
if __name__=='__main__':main()
