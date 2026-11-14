"""Preserve a frozen preview metadata addendum without uploading existing media again."""
from pathlib import Path
import hashlib
import json
import shutil

B=Path(__file__).resolve().parent
W=B/'preview28-hold18-current-metadata-sidecar-20261114'
P=Path('审核样片记录/2026-11-14-书29新版0.6实际引用元数据旁证')
OLD=B/'run43576642418-28-hold18-preview051-v2'
H=Path('/workspace/work/video-revision-delivery/post-only-hold18-validated/28/preview-handoff.json')
EXPECTED='9a8718c1ce2d62f4017d7a7adb55e5a87bb5a61209ad3d806864514e0a663860'
DENIED={'b9a257a23820944ee95d568b67d1cd78947b1c1814bb70dc99a45871f488f778','55026ce1b7cdb7e9c1a72da2f715e3d9e6e6f45050a8ddd575dc052b09dca872','bcb37d8930d804988c95da94b9cfeaaab2c7b026df96e6e4567f9b698ce88fbf'}
def load(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def add(src,rel):
    assert src.suffix in {'.json','.py'} and sha(src) not in DENIED
    dst=W/'payload'/P/rel;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dst)
    assert dst.read_bytes()==src.read_bytes()
def main():
    assert sha(H)==EXPECTED
    h=load(H);assert h['kind']=='source28-book29-hold18-user-review-preview'
    assert h['preview_only'] is True and h['production_delivery_eligible'] is False
    assert h['source_run']==43576642418 and h['local_postprocessing_only'] is True
    assert len(h['validation_files'])==98
    primary=load(OLD/'assets-primary.json');backup=load(OLD/'assets-backup.json')
    assert primary['asset_commit']==backup['asset_commit']=='dd7a3d7badbdcae587f11522f69c0ebaef21853f'
    assert load(OLD/'actual-dual-preview-blob-verification.json')['actual_dual_blob_rows']==736
    assert load(OLD/'remote-video-byte-verification.json')['passed'] is True
    retained={}
    for r in primary['files_index']:retained.setdefault((r['bytes'],r['sha256']),r)
    mappings=[];new=[]
    for r in h['validation_files']:
        src=Path(r['path']);assert src.stat().st_size==r['bytes'] and sha(src)==r['sha256'] and r['sha256'] not in DENIED
        key=(r['bytes'],r['sha256']);relative=r.get('relative_validation_path',r.get('validation_relative_path'));assert relative and not Path(relative).is_absolute() and '..' not in Path(relative).parts
        if key in retained:
            old=retained[key]
            mappings.append({'validation_relative_path':relative,'bytes':r['bytes'],'sha256':r['sha256'],'preserved_immutable_asset_commit':primary['asset_commit'],'preserved_repo_path':old['repo_path'],'preserved_git_blob_sha':old['git_blob_sha'],'already_whole_dual_archive_verified':True})
        else:
            assert src.suffix in {'.json','.py'},'No media can be newly uploaded by a metadata sidecar'
            rel=Path('新增实际引用元数据')/relative;add(src,rel);new.append({'validation_relative_path':relative,'bytes':r['bytes'],'sha256':r['sha256'],'new_sidecar_repo_path':str(P/rel)})
    assert len(mappings)==93 and len(new)==5
    video=h['articles'][0]['preview_mp4'];assert video['sha256']=='1e1685c5b0eff4ebb2d3e8bab3f368336ea31a313b38c10a0ef0f7a1ae365163'
    assert (video['bytes'],video['sha256']) in retained
    add(H,Path('current-frozen-preview-handoff.json'));add(Path(__file__),Path('archivist-program.py'))
    save(W/'payload'/P/'current-98-file-reference-bindings.json',{'kind':'frozen-preview-metadata-reference-addendum','current_handoff_sha256':EXPECTED,'old_published_asset_commit':primary['asset_commit'],'existing_exact_objects':mappings,'new_text_metadata_only':new,'preview_only':True,'production_delivery_eligible':False,'final_user_acceptance':False,'canonical_active_58_or_alias_changed':False,'old_asset_manifest_QA_Release_or_tag_rewritten':False,'media_or_audio_retested_or_uploaded_by_this_sidecar':False,'original_source_run_preserved':43576642418,'local_postprocessing_only':True,'new_native_or_TTS_run_claimed':False})
    save(W/'prepared-archive.json',{'prefix':str(P),'asset_branch':'codex/preview28-hold18-current-metadata-sidecar-20261114','scope':'Only five newly frozen metadata files and full98 object references; original media and published archive remain unchanged'})
    files=[{'repo_path':str(p.relative_to(W/'payload')),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted((W/'payload').rglob('*')) if p.is_file()]
    save(W/'payload-file-index.json',files);print(json.dumps({'files':len(files),'bytes':sum(r['bytes'] for r in files),'old_objects_referenced_without_reupload':len(mappings),'new_metadata_files':len(new)}))
if __name__=='__main__':main()
