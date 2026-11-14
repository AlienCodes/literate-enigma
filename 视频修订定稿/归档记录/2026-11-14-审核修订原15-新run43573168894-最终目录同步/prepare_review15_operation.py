"""Exact relative safe-manifest snapshot and checked operation preparation."""
from pathlib import Path
import datetime
import hashlib
import json
import shutil
import subprocess

B=Path(__file__).resolve().parent
WORK=B/'operations-review15-43573168894-revision1-v2'
def main():
    failed=B/'operations-review15-43573168894-revision1'
    if failed.exists():
        history=B/'history/source15-operation-incomplete-relative-manifest';assert not history.exists();failed.rename(history)
    failure={'kind':'archivist-safe-manifest-packaging-only-interruption','recorded_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'original_error':'source15 manifest paths are relative to its own directory; first collector tried them relative to cwd. Next operation/push could not complete prepared metadata.','all_three_exit_codes':1,'native_source15_quality_and_media_unchanged':True,'remote_refs_or_blobs_written_by_failed_packaging':False,'preserved_incomplete_operation':'history/source15-operation-incomplete-relative-manifest','corrective_change':'Resolve and constrain relative paths under the explicit manifest parent; stop dependent orchestration on nonzero exit.'}
    (B/'source15-relative-manifest-interruption-and-correction.json').write_text(json.dumps(failure,ensure_ascii=False,indent=2)+'\n')
    manifest=Path('/workspace/work/video-audit70-20261113/article15-user-review-20261114/safe-public-evidence-manifest.json');assert hashlib.sha256(manifest.read_bytes()).hexdigest()=='9549c4e3fb7143469e12e541bec19b32dd0216234ae3c4b5a258ee6454e4b5ed';m=json.loads(manifest.read_text());out=B/'safe-source15-records-for-new-revision';out.mkdir(exist_ok=True)
    for row in m['files']:
        relative=Path(row['path']);assert not relative.is_absolute() and '..' not in relative.parts
        src=manifest.parent/relative;raw=src.read_bytes();assert len(raw)==row['bytes'] and hashlib.sha256(raw).hexdigest()==row['sha256'];assert src.suffix.lower() in ['.json','.py','.md','.log','.png','.jpg','.txt','.diff','.csv','.sh','.yml','.yaml']
        dst=out/relative;dst.parent.mkdir(parents=True,exist_ok=True)
        if dst.exists():assert dst.read_bytes()==raw
        elif src.suffix.lower() in ['.png','.jpg']:dst.hardlink_to(src)
        else:dst.write_bytes(raw)
    (out/'safe-public-evidence-manifest.json').write_bytes(manifest.read_bytes());assert len(m['files'])==65
    w=B/'run43573168894-15-review-revision1';d=B/'closure-records-for15-revision1';d.mkdir(exist_ok=True)
    records=[('previous26-final-archive-receipt.json',B/'operations-review26-43569401028-revision1/final-archive-receipt.json'),('previous26-integration-plan.json',B/'integration-plan-review26-43569401028.json'),('previous26-cleanup.json',B/'completed-bare-cleanup-review26-20261114.json'),('initial58-final-directory-receipt.json',B/'final-directory-first58-20261114/actual-final-directory-receipt.json'),('new15-dual-Git-blob-verification.json',w/'actual-dual-asset-blob-verification.json'),('new15-closed-own-bare-cleanup.json',w/'closed-dual-asset-own-bare-cleanup-receipt.json'),('new15-download-manifest.json',B/'ready-new15-book25-exact-download-manifest.json')]
    for name in ['assets-primary.json','assets-backup.json','remote-video-byte-verification.json','prepared-archive.json']:records.append(('new15-'+name,w/name))
    for name,p in records:shutil.copyfile(p,d/name)
    shutil.copyfile(B/'CURRENT-ARCHIVE-STATE.json',d/'before15-revision-and-final-alias-state.json')
    for n in range(1,35):
        p=Path('/workspace/work/first50-review-release')/f'USER-REVIEW-2026-11-14-{n:03d}.json'
        if p.exists():shutil.copyfile(p,d/p.name)
    (d/'AUDIO-REUSE-JOURNAL-NOT-NEW-QC.json').write_text(json.dumps({'scope':'Existing actualV3 handoff facts, not new sound work by archivist','source_id':'15','current_native_run':43573168894,'actual_handoff_sha256':'cff5b8b1674bf14a12290b5d2870cca31a566cfd5e1c99db683ce6994d36d6b2','prior_approved_A21_plus5_native_run':43562525001,'AAC_packets_preserved':7005,'new_audio_repair_applied_this_run':False,'prior_A21_repair_history_and_old_release_preserved':True},ensure_ascii=False,indent=2)+'\n')
    args=['python',str(B/'prepare_operation.py'),'--work-dir',str(WORK),'--batch','2026-11-14-审核修订原15-新run43573168894-最终目录同步','--asset-branch','codex/passed4k-review15-records-43573168894','--previous-inventory',str(B/'operations-review26-43569401028-revision1/final-remote-cumulative-inventory.json'),'--article-work-dir',str(w),'--revision-authorization',str(B/'user-review-revisions-14-27-13-26-15-17-36-33-authorization.json')]
    for p in [d,out,B/'final-directory-first58-record-assets-20261114/payload/视频修订定稿/归档记录/2026-11-14-最终定稿58首次Git别名物化']:args+=['--attach-tree',str(p)]
    for name in ['integrate_verified_batch.py','atomic-final-alias-sync-program-change-record.json','root034-authorization-schema-change-record.json','source15-relative-manifest-interruption-and-correction.json','prepare_review15_operation.py']:args+=['--attach',str(B/name)]
    subprocess.run(args,check=True)

if __name__=='__main__':main()
