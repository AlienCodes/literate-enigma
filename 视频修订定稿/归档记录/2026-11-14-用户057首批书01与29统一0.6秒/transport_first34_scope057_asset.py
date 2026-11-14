"""Transport one owner-frozen passed asset branch; no media or QA mutations."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import argparse
import datetime
import hashlib
import json
import os
import signal
import subprocess
import sys
import uuid

P=argparse.ArgumentParser()
for key in ['work-dir','handoff','handoff-sha','source-id','new-id','ready','video-sha']:
    P.add_argument('--'+key,required=True)
P.add_argument('--files',required=True,type=int)
A=P.parse_args();W=Path(A.work_dir).resolve();B=Path(__file__).parent.resolve();H=Path(A.handoff)
assert W.parent==B and W.name.startswith('user057-book')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
load=lambda p:json.loads(p.read_text())
def write(p,r):p.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n')
assert sha(H)==A.handoff_sha
meta=load(W/'prepared-archive.json');index=load(W/'payload-file-index.json');h=load(H)
assert len(index)==A.files and len(meta['articles'])==len(h['articles'])==1
row=meta['articles'][0];actual=h['articles'][0]
assert row['source_id']==actual['source_id']==A.source_id and row['new_id']==actual['new_id']==A.new_id
assert row['sha256']==actual['final_mp4']['sha256']==A.video_sha and row['bytes']==actual['final_mp4']['bytes']
assert row['passed_per_article'] is True and row['current_uniform_timing_authorized_by_user057'] is True
assert not(W/'assets.git').exists()and not(W/'assets.git').is_symlink()and not(W/'asset-local.json').exists()
cache=Path('/dev/shm')/('codex-public-approved-asset-git-'+str(meta['source_run'])+'-'+A.source_id+'-hold18-'+uuid.uuid4().hex)
subprocess.run(['git','init','--bare',str(cache)],check=True,capture_output=True)
link=cache/'probe-index-link';target=cache/'probe-index-target';link.symlink_to(target)
subprocess.run(['git','--git-dir='+str(cache),'read-tree','--empty'],env={**os.environ,'GIT_INDEX_FILE':str(link)},check=True,capture_output=True)
assert link.is_symlink()and target.exists();link.unlink();target.unlink()
(W/'assets.git').symlink_to(cache,target_is_directory=True)
assert not(W/'assets.index').exists()and not(W/'assets.index').is_symlink()
(W/'assets.index').symlink_to(cache/'public-assets.index');temp=cache/'temp';temp.mkdir()
write(W/'tmpfs-owned-git-cache-location.json',dict(work_dir=str(W),cache_symlink=str(W/'assets.git'),owned_tmpfs_target=str(cache),only_public_passed_asset_Git_objects_not_unique_media=True,git_index_symlink=str(W/'assets.index'),git_index_tmpfs_target=str(cache/'public-assets.index'),actual_git_index_symlink_lock_test_passed=True,TMPDIR=str(temp),owner='/root/resume_archive_writer',main_master_canonical_or_final_alias_writes_authorized=False))
env={**os.environ,'TMPDIR':str(temp)}
def stage(name,cmd,bound=None):
    log=W/(name+'.log')
    with log.open('w')as f:
        p=subprocess.Popen(list(map(str,cmd)),stdout=f,stderr=subprocess.STDOUT,env=env,start_new_session=True)
        try:rc=p.wait(timeout=bound);timed=False
        except subprocess.TimeoutExpired:
            timed=True;os.killpg(p.pid,signal.SIGTERM)
            try:rc=p.wait(timeout=5)
            except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);rc=p.wait()
    record=dict(stage=name,exit_code=rc,timed_out=timed,bound_seconds=bound,command=list(map(str,cmd)),log=str(log),automatic_retry_performed=False,completed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
    write(W/(name+'-attempt.json'),record)
    print(json.dumps(record,ensure_ascii=False),flush=True)
    print(log.read_text()[-4500:],flush=True)
    if rc or timed:raise RuntimeError('Stopped after actual transport error: '+name)
for role,repo in [('primary','alienalgorithm/postgraduate-vocabulary'),('backup','AlienCodes/literate-enigma')]:
    stage('asset-'+role+'-transport',[sys.executable,B/'archive_batch.py','push','--work-dir',W,'--repo',repo],85)
with ThreadPoolExecutor(max_workers=2)as pool:
    f1=pool.submit(stage,'actual-dual-full-MP4-HTTP',[sys.executable,B/'archive_batch.py','stream','--work-dir',W])
    f2=pool.submit(stage,'actual-dual-Git-blobs',[sys.executable,B/'verify_dual_media_asset_blobs.py','--work-dir',W,'--expected-files',A.files])
    f1.result();f2.result()
stage('actual-ready-download-manifest',[sys.executable,B/'emit_ready_revision_download_manifest.py','--work-dir',W,'--handoff',H,'--output',A.ready])
print(json.dumps(dict(ready=A.ready,ready_sha256=sha(Path(A.ready)),source_id=A.source_id,new_id=A.new_id,all_actual_dual_blobs_and_full_MP4_HTTP_closed=True,local_Git_cache_cleanup_still_pending=True),ensure_ascii=False),flush=True)
