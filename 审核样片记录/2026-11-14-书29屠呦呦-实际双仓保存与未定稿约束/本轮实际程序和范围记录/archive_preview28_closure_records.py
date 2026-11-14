"""Preserve preview-only transport closure and explicit public source evidence.

No final inventory, alias, release, PDF, media or quality gate is changed.
"""
from pathlib import Path
import hashlib
import json
import os
import shutil
from archive_batch import digest, load, now, write

B=Path(__file__).resolve().parent
W=B/'preview28-closure-record-assets-20261114'
P=Path('审核样片记录/2026-11-14-书29屠呦呦-实际双仓保存与未定稿约束')
SOURCE=B/'run43576642418-28-hold9-preview032'
ALLOWED={'.json','.py','.sh','.md','.txt','.log','.csv','.diff','.patch','.yml','.yaml','.png','.jpg'}

def main():
    pay=W/'payload';bindings=[]
    def add(source,rel,expected_bytes=None,expected_sha=None):
        source=Path(source);assert source.suffix.lower() in ALLOWED and '__pycache__' not in source.parts
        raw_sha=digest(source);assert expected_bytes is None or source.stat().st_size==expected_bytes;assert expected_sha is None or raw_sha==expected_sha
        target=pay/P/rel;target.parent.mkdir(parents=True,exist_ok=True)
        if target.exists():assert digest(target)==raw_sha
        elif source.suffix.lower() in {'.png','.jpg'}:os.link(source,target)
        else:shutil.copyfile(source,target)
        bindings.append({'original_path':str(source),'repo_path':str(P/rel),'bytes':source.stat().st_size,'sha256':raw_sha})
    ready=load(B/'ready-preview28-book29-endpause032.json')
    assert ready['ready_for_preview_prerelease_download'] is True and ready['ready_for_final_active_replacement'] is False
    for name in ['prepared-archive.json','assets-primary.json','assets-backup.json','actual-dual-preview-blob-verification.json','remote-video-byte-verification.json','closed-preview-only-owned-cache-cleanup.json','tmpfs-owned-git-cache-location.json','payload-file-index.json','asset-local.json']:
        add(SOURCE/name,Path('实际双仓保存回执')/name)
    for name in ['ready-preview28-book29-endpause032.json','prepare_source28_preview_assets.py','prepare_source28_preview_assets-before-actual-preview-field.py','verify_source28_preview_storage.py','archive_batch.py','user-authorized-source28-preview-only-032.json','PDF-PAUSE-USER-INSTRUCTION-20261114.json','new-final-prepublication-hold9-hold-20261114.json','review039-048-actual-dual-immutable-byte-receipts.json','review039-048-validated-inputs.json']:
        add(B/name,Path('本轮实际程序和范围记录')/name)
    add(Path(__file__),Path('本轮实际程序和范围记录')/Path(__file__).name)
    manifests=[(Path('/workspace/work/video-audit70-20261113/article28-user-review-20261114/safe-public-evidence-manifest.json'),'8cafb1f565a66170b9c6626f01cca0a1b41184894f2481021a320e9ebdab70b0','用户两词修改与实际静态证据'),(Path('/workspace/work/video-audit70-20261113/article28-user-review-20261114/hold9-integrator/safe-public-evidence-manifest.json'),'9934f4db21450c5701669fb29c199d1aed85254118ff5b1502d00ba6f7462a58','仅预备程序诊断历史不冒充成片')]
    for path,sha,label in manifests:
        assert digest(path)==sha;manifest=load(path);add(path,Path(label)/'safe-public-evidence-manifest.json')
        for row in manifest['files']:
            source=Path(row['path']);source=source if source.is_absolute() else path.parent/source
            rel=Path(row.get('safe_archive_relative_path',row.get('relative_path',source.name)));assert not rel.is_absolute() and '..' not in rel.parts
            add(source,Path(label)/rel,row['bytes'],row['sha256'])
    write(pay/P/'文件逐项原件绑定.json',{'only_explicit_public_files_no_recursive_mirror':True,'files':bindings,'no_media_PDF_PCM_GT_or_cache_objects':True})
    meta={'kind':'preview28-closure-and-explicit-public-records-only','created_utc':now(),'prefix':str(P),'asset_branch':'codex/preview28-closure-records-20261114','articles':[],'preview_only':True,'production_delivery_eligible':False,'final_user_acceptance':False,'active58_index_or_alias_changed':False,'PDF_work_performed':False,'original_preview_asset_commit':ready['asset_commit']}
    write(pay/P/'记录范围.json',meta);write(W/'prepared-archive.json',meta)
    files=[{'repo_path':str(p.relative_to(pay)),'bytes':p.stat().st_size,'sha256':digest(p)} for p in sorted(pay.rglob('*')) if p.is_file()]
    write(W/'payload-file-index.json',files)
    print(json.dumps({'work_dir':str(W),'files':len(files),'bytes':sum(r['bytes'] for r in files),'preview_only':True,'new_media_or_final_acceptance_claimed':False},ensure_ascii=False))

if __name__=='__main__':main()
