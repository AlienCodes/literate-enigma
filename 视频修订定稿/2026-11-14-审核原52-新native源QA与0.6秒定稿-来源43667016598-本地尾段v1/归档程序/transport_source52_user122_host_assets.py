"""Transport only exact122 frozen London final, host-only owned Git/temp, no main writes."""
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
 p=argparse.ArgumentParser();p.add_argument('--work-dir',required=True);a=p.parse_args();w=Path(a.work_dir).resolve();assert w.parent==B and B.parent==Path('/workspace/work/video-archive-batches-20261114') and B.name.startswith('user122-source52-host-isolated-assets-')
 h=Path('/workspace/work/review41-source52-three-domain-hold06-intake/validated/52/archive-handoff.json');assert digest(h)=='cea3d75d9bc14f525b1303f494def78fa22ba6868be2d6e785abfef05d59d559'
 m=load(w/'prepared-archive.json');row=m['articles'][0];assert len(m['articles'])==1 and row['source_id']=='52'and row['new_id']=='41'and row['passed_per_article']is True and row['production_delivery_eligible']is True and row['preview_only']is False
 assert row['sha256']=='eebe94ffb6ecaf788178343f068246c431088ce6da6e7cc9c98d20bf64583ccc' and row['bytes']==18732740
 assert not(w/'assets.git').exists()and not(w/'asset-local.json').exists()
 for role,repo in [('primary','alienalgorithm/postgraduate-vocabulary'),('backup','AlienCodes/literate-enigma')]:run([sys.executable,B/'archive_batch.py','push','--work-dir',w,'--repo',repo],w/f'assets-{role}-transport.log',85)
 count=len(load(w/'payload-file-index.json'))
 with ThreadPoolExecutor(max_workers=2)as pool:
  f=pool.submit(run,[sys.executable,B/'archive_batch.py','stream','--work-dir',w],w/'actual-dual-full-MP4-HTTP.log',120);g=pool.submit(run,[sys.executable,B/'verify_dual_media_asset_blobs.py','--work-dir',w,'--expected-files',count],w/'actual-dual-Git-blobs.log',120);f.result();g.result()
 ready=B/'ready-user122-source52.json';run([sys.executable,B/'emit_ready_revision_download_manifest.py','--work-dir',w,'--handoff',h,'--output',ready],w/'actual-ready-download-manifest.log',30)
 print(json.dumps({'ready':str(ready),'ready_sha256':digest(ready),'source_id':'52','new_id':'41','files':count,'actual_both_whole_HTTP_and_blobs_closed':True,'only_host_Git_payload_TMPDIR_used':True,'current_not_changed_by_asset_transport':True}),flush=True)
 run([sys.executable,B/'cleanup_closed_media_asset_bare.py','--work-dir',w],w/'own-closed-Git-cleanup.log',90)
 index=w/'assets.index'
 if index.exists():assert not index.is_symlink()and index.parent==w;index.unlink()
 print('own closed host Git cache cleaned; all payload/native/H preserved',flush=True)
if __name__=='__main__':main()
