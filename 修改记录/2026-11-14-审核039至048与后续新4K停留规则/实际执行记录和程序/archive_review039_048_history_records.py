"""Save explicit public review/history evidence while all PDF work is paused."""
from pathlib import Path
import json
import os
import shutil
from archive_batch import digest, load, now, write

B=Path(__file__).resolve().parent
A=Path('/workspace/work/video-audit70-20261113')
W=B/'review039-048-history-record-assets-20261114'
P=Path('修改记录/2026-11-14-审核039至048与后续新4K停留规则')
ALLOWED={'.json','.py','.sh','.md','.txt','.log','.csv','.diff','.patch','.yml','.yaml','.png','.jpg'}

def main():
    pay=W/'payload';bindings=[]
    def add(source,rel,size=None,sha=None):
        source=Path(source);assert source.suffix.lower() in ALLOWED and '__pycache__' not in source.parts
        actual=digest(source);assert size is None or source.stat().st_size==size;assert sha is None or actual==sha
        target=pay/P/rel;target.parent.mkdir(parents=True,exist_ok=True)
        if target.exists():assert digest(target)==actual
        elif source.suffix.lower() in {'.png','.jpg'}:os.link(source,target)
        else:shutil.copyfile(source,target)
        bindings.append({'original_path':str(source),'repo_path':str(P/rel),'bytes':source.stat().st_size,'sha256':actual})
    for row in load(B/'review039-048-validated-inputs.json'):
        add(row['local_path'],Path('用户原话')/Path(row['remote_path']).name,row['bytes'],row['sha256'])
    for name in ['review039-048-actual-dual-immutable-byte-receipts.json','review039-048-validated-inputs.json','new-final-prepublication-hold9-hold-20261114.json','review17-33-36-historical-originals-dual-storage-closure.json','PDF-PAUSE-USER-INSTRUCTION-20261114.json','owned-cache-registration-schema-correction-17-33.json','review039048-relative-manifest-routing-correction.json','archive_revision_policy.py','verify_closed_small_record_asset.py','archive_batch.py']:
        add(B/name,Path('实际执行记录和程序')/name)
    for ids in ['14-27-13-26-15-17-36-33','14-27-13-26-15-17-36-33-47','14-27-13-26-15-17-36-33-47-34','14-27-13-26-15-17-36-33-47-34-62']:
        name='user-review-revisions-'+ids+'-authorization.json';add(B/name,Path('逐版授权原件')/name)
    for work in ['run43574943542-36-review-revision1','run43575885608-17-review-before-hold9-history','run43576211956-33-review-before-hold9-history']:
        for name in ['prepared-archive.json','assets-primary.json','assets-backup.json','actual-dual-asset-blob-verification.json','remote-video-byte-verification.json','closed-own-media-asset-bare-cleanup-receipt.json']:
            source=B/work/name
            if name.startswith('closed-') and not source.exists():
                alternatives=[p for p in (B/work).glob('*cleanup*.json') if p.is_file()]
                assert len(alternatives)==1;source=alternatives[0]
            add(source,Path('原生历史双仓回执')/work/source.name)
    manifests=[
        (A/'article36-user-review-20261114/safe-public-evidence-manifest.json','9a299df5decdd1596e2153d11d9e114a1bfc00e33a564a34f720b7c9a370049b','source36文字与静态'),
        (A/'article33-user-review-20261114/safe-public-evidence-manifest.json','ca77b68e3eb1688d618cbdea6ec43ca297b762724f21790e04a10d700954dbad','source33文字与静态'),
        (A/'article47-user-review-20261114/safe-public-evidence-manifest.json','9b83f0e02db35683273067d68027d46c2c737149061fee9dc7e20edf5fced772','source47文字与静态'),
        (A/'article47-user-review-20261114/final-independent-addendum-safe-manifest.json','d9aeaa90976d3766d5f8a4e3a50461d619313c40411b048426e3d0c3af557195','source47相邻旁证扩展'),
        (Path('/workspace/work/tetris34-audio-user-review-20261114/safe-public-evidence-manifest.json'),'ad9aaeee829b23ad29a22ce3c25a724617840154f465067ec1a4a2abd4459d44','source34只读音频核查'),
        (Path('/workspace/work/dolly62-audio-user-review-20261114/safe-public-evidence-manifest.json'),'42b2ac28e36ec71aa80e86a3214f489df119a653d59c9bb2a5821757216e2ef8','source62只读接缝诊断不是修复通过'),
    ]
    for path,sha,label in manifests:
        assert digest(path)==sha;manifest=load(path);add(path,Path(label)/path.name)
        for row in manifest['files']:
            source=Path(row.get('path',row.get('name','')));assert str(source) not in {'','.'};source=source if source.is_absolute() else ((Path('/workspace')/source) if source.parts[0]=='work' else path.parent/source);assert source.resolve().is_relative_to(path.parent.resolve())
            rel=Path(row.get('safe_archive_relative_path',row.get('relative_path',row.get('name',source.name))));assert not rel.is_absolute() and '..' not in rel.parts
            add(source,Path(label)/rel,row['bytes'],row['sha256'])
    supplement=A/'article17-user-review-20261114/native17/actual-new-vocabulary-and-ending-frames/files-sha256.json'
    assert digest(supplement)=='04e19f2bcc1ce4a45f81ed40f767b69b50d29683e98a56dec34417e0be66519e'
    add(supplement,Path('source17实际4K帧补证')/supplement.name)
    for name,row in load(supplement).items():
        rel=Path(name);assert not rel.is_absolute() and '..' not in rel.parts
        add(supplement.parent/rel,Path('source17实际4K帧补证')/rel,row['bytes'],row['sha256'])
    add(Path(__file__),Path('实际执行记录和程序')/Path(__file__).name)
    write(pay/P/'source47独审旁证命名澄清.json',{'original_56c_independent_review_still_valid_and_retained':True,'adjacent_7f2_extension_is_original_tool_consumption_side_evidence_not_a_replacement_or_revocation':True,'frozen_original_safe_manifests_and_reports_not_rewritten':True,'source47_new_video_pass_claimed':False})
    write(pay/P/'逐项安全原件绑定.json',{'files':bindings,'only_individual_explicit_public_files':True,'no_recursive_mirrors_private_PCM_GT_or_cache':True,'all_PDF_read_modify_archive_publish_work_paused':True})
    meta={'kind':'review039-048-historical-public-evidence-records-only','created_utc':now(),'prefix':str(P),'asset_branch':'codex/review039-048-history-records-20261114','articles':[],'new_video_generation_quality_acceptance_or_final_promotion_claimed':False,'all_PDF_work_paused':True,'active_final_index_or_alias_changed':False,'source28_preview_accepted_as_final':False}
    write(pay/P/'记录范围.json',meta);write(W/'prepared-archive.json',meta)
    index=[{'repo_path':str(p.relative_to(pay)),'bytes':p.stat().st_size,'sha256':digest(p)} for p in sorted(pay.rglob('*')) if p.is_file()]
    write(W/'payload-file-index.json',index);print(json.dumps({'work_dir':str(W),'files':len(index),'bytes':sum(r['bytes'] for r in index),'media_or_PDF_copied':False},ensure_ascii=False))

if __name__=='__main__':main()
