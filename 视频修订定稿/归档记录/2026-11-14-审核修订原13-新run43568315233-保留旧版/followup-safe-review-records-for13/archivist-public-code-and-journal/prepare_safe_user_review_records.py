"""Collect exact declared public source/static records, never recursive mirrors."""
from pathlib import Path
import datetime
import hashlib
import json

B=Path(__file__).resolve().parent
A=Path('/workspace/work/video-audit70-20261113')
W=B/'user-review-source-record-assets-14-13-20261114'
PREFIX=Path('视频修订定稿/归档记录/2026-11-14-逐篇审核14与13源稿及修订保存机制')
DST=W/'payload'/PREFIX

def save(path,value):
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')

def put(src,rel,sha=None,size=None):
    src=Path(src);raw=src.read_bytes()
    assert sha is None or hashlib.sha256(raw).hexdigest()==sha
    assert size is None or len(raw)==size
    rel=Path(rel);assert not rel.is_absolute() and '..' not in rel.parts
    target=DST/rel;target.parent.mkdir(parents=True,exist_ok=True)
    if target.exists():assert target.read_bytes()==raw
    elif src.suffix.lower() in ['.png','.jpg','.zip']:target.hardlink_to(src)
    else:target.write_bytes(raw)

def main():
    DST.mkdir(parents=True,exist_ok=True)
    source_counts=[]
    for sid,sha in [('14','399144b0c5062258f4a58abec50b2b325e97ce925024d25e98cdf967c9145182'),('13','9d03a8aa06e846ca2fd85490ccf4b9678d41128ba85e59286ce09a4a54a97814')]:
        p=A/f'article{sid}-user-review-20261114/safe-public-evidence-manifest.json'
        raw=p.read_bytes();assert hashlib.sha256(raw).hexdigest()==sha
        manifest=json.loads(raw)
        for row in manifest['files']:
            source=Path(row['path'])
            assert source.suffix.lower() in ['.json','.md','.py','.log','.txt','.png','.jpg','.diff','.csv','.sh','.yml','.yaml','.zip']
            relative=row.get('safe_archive_relative_path',row.get('relative_path'))
            assert relative
            put(source,Path('明确清单公开源稿与静态实证')/sid/relative,row['sha256'],row['bytes'])
        put(p,Path('明确清单公开源稿与静态实证')/sid/'safe-public-evidence-manifest.json',sha)
        source_counts.append({'source_id':sid,'exact_declared_files':len(manifest['files']),'bytes':sum(r['bytes'] for r in manifest['files']),'source_and_static_only_not_new_video_pass':True})
    programs=['archive_revision_policy.py','test_archive_revision_policy.py','prepare_operation.py','integrate_verified_batch.py','user-review-revisions-14-27-13-authorization.json','user-review-revisions-program-before.json','user-review-revisions-program-change-record.json','user-review-revision-policy-tests.log','prepare_operation-user-review-revisions.diff','integrate_verified_batch-user-review-revisions.diff','history/prepare_operation-before-user-review-revisions.py','history/integrate_verified_batch-before-user-review-revisions.py','article14-review-source-safe-records-snapshot.json','article14-preexisting-revision-and-window-20261114.json','prepare_safe_user_review_records.py']
    for name in programs:put(B/name,Path('归档机制及保旧证据')/name)
    reviews=Path('/workspace/work/first50-review-release')
    for n in range(1,14):
        p=reviews/f'USER-REVIEW-2026-11-14-{n:03d}.json'
        if p.exists():put(p,Path('逐条用户审核记录')/p.name)
    put(reviews/'REVIEW-010-013-DUAL-SAVE-OBSERVATION.json',Path('逐条用户审核记录/REVIEW-010-013-DUAL-SAVE-OBSERVATION.json'))
    save(DST/'本次保存范围.json',{'kind':'isolated-record-only-source14-and13-user-authorized-revisions','recorded_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'no_new_native_video_acceptance_claimed':True,'canonical_count_remains':55,'old40_review_release_tags_and_media_unchanged':True,'only_explicit_safe_file_lists_collected':True,'private_PCM_GT_model_or_cache_collected':False,'source27_authorization_records_only_no_candidate_or_native_artifacts_collected':True,'source_lists':source_counts,'initial_interrupted_attempt':'KeyError safe_archive_relative_path on13 manifest with relative_path; partial14 snapshot exact and no remote mutation. This version accepts both explicitly declared manifest keys.'})
    index=[]
    for p in sorted(DST.rglob('*')):
        if p.is_file():index.append({'repo_path':str(p.relative_to(W/'payload')),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
    save(W/'payload-file-index.json',index)
    save(W/'prepared-archive.json',{'prefix':str(PREFIX),'asset_branch':'codex/user-review-source-records-14-13-20261114','scope':'Explicit safe source/static and metadata code only, not new video acceptance'})
    print(json.dumps({'work_dir':str(W),'files':len(index),'bytes':sum(x['bytes'] for x in index),'canonical_mutation':False},ensure_ascii=False))

if __name__=='__main__':main()
