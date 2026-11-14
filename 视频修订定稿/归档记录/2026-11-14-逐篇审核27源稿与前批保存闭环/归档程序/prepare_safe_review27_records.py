"""Exact safe-list-only source27 records plus prior small closure receipts."""
from pathlib import Path
import datetime
import hashlib
import json
import prepare_safe_user_review_records as collect

B=Path(__file__).resolve().parent
W=B/'user-review-source-record-assets-27-20261114'
PREFIX=Path('视频修订定稿/归档记录/2026-11-14-逐篇审核27源稿与前批保存闭环')

def main():
    collect.DST=W/'payload'/PREFIX
    collect.DST.mkdir(parents=True,exist_ok=True)
    p=Path('/workspace/work/video-audit70-20261113/article27-user-review-20261114/safe-public-evidence-manifest.json')
    assert hashlib.sha256(p.read_bytes()).hexdigest()=='6218eb110730ae607f5e6e88e222dafd54b2079c34a180baf767af12ece8a26b'
    manifest=json.loads(p.read_text())
    assert len(manifest['files'])==58 and sum(r['bytes'] for r in manifest['files'])==5535417
    for row in manifest['files']:
        source=Path(row['path'])
        assert source.suffix.lower() in ['.json','.md','.py','.log','.txt','.png','.jpg','.diff','.csv','.sh','.yml','.yaml','.zip']
        collect.put(source,Path('明确清单27公开源稿与静态实证')/row['safe_archive_relative_path'],row['sha256'],row['bytes'])
    collect.put(p,Path('明确清单27公开源稿与静态实证/safe-public-evidence-manifest.json'))
    previous=B/'user-review-source-record-assets-14-13-20261114'
    for name in ['actual-dual-record-verification.json','closed-own-bare-cleanup-receipt.json']:
        collect.put(previous/name,Path('前批14与13双存闭环')/name)
    for name in ['verify_safe_user_review_records.py','prepare_safe_user_review_records.py','prepare_safe_review27_records.py']:
        collect.put(B/name,Path('归档程序')/name)
    collect.save(collect.DST/'本次保存范围.json',{'recorded_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'kind':'source27-safe-text-and-static-only-plus-previous-record-closure','source27_declared_files':58,'source27_declared_bytes':5535417,'source27_new_video_pass_claimed':False,'audio_controls_not_changed_by_archivist':True,'canonical_count_still':55,'old40_review_release_unchanged':True,'thin_mirror_private_PCM_GT_models_or_cache_collected':False})
    index=[]
    for q in sorted(collect.DST.rglob('*')):
        if q.is_file():index.append({'repo_path':str(q.relative_to(W/'payload')),'bytes':q.stat().st_size,'sha256':hashlib.sha256(q.read_bytes()).hexdigest()})
    collect.save(W/'payload-file-index.json',index)
    collect.save(W/'prepared-archive.json',{'prefix':str(PREFIX),'asset_branch':'codex/user-review-source-records-27-20261114','scope':'Source/static only, no new native video acceptance'})
    print(json.dumps({'work_dir':str(W),'files':len(index),'bytes':sum(r['bytes'] for r in index),'canonical_mutation':False},ensure_ascii=False))

if __name__=='__main__':main()
