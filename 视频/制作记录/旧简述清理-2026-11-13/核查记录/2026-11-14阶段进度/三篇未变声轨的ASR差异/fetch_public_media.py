"""Materialize only public MP4s for the authorized read-only comparison."""
from pathlib import Path
import argparse,hashlib,json,urllib.parse,urllib.request,zipfile

HERE=Path(__file__).resolve().parent
BASE=Path('/workspace/work/video-audit70-20261113/ci63-final-43523430839/public-evidence')
p=argparse.ArgumentParser();p.add_argument('--id',required=True);p.add_argument('--artifact-url',required=True);a=p.parse_args();n=a.id
assert n in ('46','49','55')
source=BASE/n;status=json.loads((source/f'{n}-status.json').read_text());receipt=json.loads((source/'artifact-retrieval-receipt.json').read_text())
dest=HERE/'public-media'/n;dest.mkdir(parents=True,exist_ok=True)
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def fetch(url,path):
 with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Codex-readonly-public-audio-diagnosis'}),timeout=30)as r,path.open('wb')as f:
  for b in iter(lambda:r.read(1024*1024),b''):f.write(b)
 return path
archive=fetch(a.artifact_url,dest/'temporary-public-artifact.zip')
assert sha(archive)==receipt['actual_zip_sha256']
with zipfile.ZipFile(archive)as z:
 matches=[x for x in z.namelist() if Path(x).name==n+'-failed-draft.mp4'];assert len(matches)==1
 failed=dest/(n+'-failed-draft.mp4');failed.write_bytes(z.read(matches[0]))
assert sha(failed)==status['failed_current_video']['sha256']
archive.unlink()
accepted=status['accepted_source'];pin='3d82f20ce7ecfea2e4e0a2aa93c340a779e646d3'
url='https://raw.githubusercontent.com/alienalgorithm/postgraduate-vocabulary/'+pin+'/'+urllib.parse.quote(accepted['path'],safe='/')
old=fetch(url,dest/(n+'-accepted.mp4'))
assert old.stat().st_size==accepted['bytes'] and sha(old)==accepted['sha256']
report={'article':n,'public_media_only':True,'failed':{'path':str(failed),'bytes':failed.stat().st_size,'sha256':sha(failed),'purpose':'diagnosis only; not an accepted deliverable'},'accepted':{'path':str(old),'bytes':old.stat().st_size,'sha256':sha(old),'repository':'alienalgorithm/postgraduate-vocabulary','pinned_commit':pin,'repo_path':accepted['path']},'original_artifact_id':receipt['artifact_id'],'artifact_zip_sha256':receipt['actual_zip_sha256'],'artifact_zip_removed_after_MP4_extraction':True,'private_GT_cache_models_or_PCM_extracted':False}
(dest/'public-media-retrieval.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(report,ensure_ascii=False),flush=True)
