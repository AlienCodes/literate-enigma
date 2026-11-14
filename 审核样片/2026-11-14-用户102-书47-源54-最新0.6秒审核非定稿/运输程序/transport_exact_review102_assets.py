"""Finite immutable asset lane; no index, final integration or publication writes."""
from pathlib import Path
import argparse,concurrent.futures,json,os,subprocess,sys
from archive_batch import load,write,digest,now
B=Path(__file__).resolve().parent

def run(cmd,log,timeout=None):
 with log.open('w') as f:r=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,env={**os.environ,'TMPDIR':str(B)},timeout=timeout)
 assert r.returncode==0,f'{log}: exit{r.returncode}'

def main():
 p=argparse.ArgumentParser();p.add_argument('--work-dir',required=True);a=p.parse_args();w=Path(a.work_dir).resolve();assert w.parent==B
 m=load(w/'prepared-archive.json');assert m['review_only'] is True and m['production_delivery_eligible'] is False;article=m['articles'][0];sid=article['source_id'];assert sid in ('54',)
 for role,repo in [('primary','alienalgorithm/postgraduate-vocabulary'),('backup','AlienCodes/literate-enigma')]:
  cmd=[sys.executable,str(B/'archive_batch.py'),'push','--work-dir',str(w),'--repo',repo]
  write(w/f'{role}-transport-attempt.json',{'started_utc':now(),'bounded_seconds':85,'automatic_retry':False,'command':cmd})
  run(cmd,w/f'assets-{role}-transport.log',85)
 count=len(load(w/'payload-file-index.json'))
 with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:
  tasks=[ex.submit(run,[sys.executable,str(B/'archive_batch.py'),'stream','--work-dir',str(w)],w/'full-video-readbacks.log',120),ex.submit(run,[sys.executable,str(B/'verify_review102_dual_asset_blobs.py'),'--work-dir',str(w),'--expected-files',str(count)],w/'dual-blobs.log',120)]
  for t in tasks:t.result()
 primary=load(w/'assets-primary.json');backup=load(w/'assets-backup.json');assert primary['asset_commit']==backup['asset_commit'] and primary['video_tree_sha']==backup['video_tree_sha']
 ready={'kind':'actual-qualified-user102-review-only-dual-permanent-archive-ready','source_id':sid,'frozen_book_order':article['new_id'],'current_video_order':article['new_id'],'source_run':m['source_run'],'asset_commit':primary['asset_commit'],'video_tree_sha':primary['video_tree_sha'],'video_repo_path':article['video_repo_path'],'bytes':article['bytes'],'sha256':article['sha256'],'real_V3_handoff_sha256':m['real_V3_handoff_sha256'],'review_only':True,'preview_only':True,'preview_delivery_eligible':True,'actual_dual_permanent_archive_passed':True,'production_delivery_eligible':False,'final_user_acceptance':False,'active_final_replacement_authorized':False,'metadata_files':{n:str(w/n) for n in ('prepared-archive.json','assets-primary.json','assets-backup.json','remote-video-byte-verification.json','actual-dual-asset-blob-verification.json')}}
 output=B/f'ready-review102-source{sid}.json';write(output,ready)
 print(json.dumps({'ready':str(output),'sha256':digest(output),'asset_commit':ready['asset_commit'],'files':count,'dual_blob_rows':2*count,'review_only':True,'active_final_replacement_authorized':False},ensure_ascii=False),flush=True)
 compiler=Path('/dev/shm/latest38-70-review-publisher-preparation-20261114/compile_latest_review.py');h=next(r['original_path'] for r in m['material_source_bindings'] if Path(r['original_path']).name=='review-handoff.json')
 run([sys.executable,str(compiler),'--normalize-review-ready','--handoff',h,'--dual-ready',str(output),'--latest-requests','/dev/shm/archive-writer-main061/latest_requests.json','--output',str(B/f'normalized-ready-review102-source{sid}.json')],w/'ready-normalization.log',30)
 run([sys.executable,str(B/'cleanup_review102_closed_own_bare.py'),'--work-dir',str(w)],w/'own-bare-cleanup.log',90)
 index=w/'assets.index'
 if index.exists() or index.is_symlink():
  assert index.parent==w and index.name=='assets.index';index.unlink()
 print(json.dumps({'source_id':sid,'normalized_ready':str(B/f'normalized-ready-review102-source{sid}.json'),'closed_own_git_only_cleaned':True},ensure_ascii=False),flush=True)
if __name__=='__main__':main()
