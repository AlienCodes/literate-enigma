"""Collect completed single-article publication records; exclude all media/cache."""
from pathlib import Path
import hashlib
import json
import os
import zipfile
import prepare_safe_user_review_records as collect

B=Path(__file__).resolve().parent
W=B/'reviewed-book21-23-publication-record-assets-20261114'
PREFIX=Path('发行记录/2026-11-14-审核后书21与23单篇4K发布')
ASSET_BRANCH='codex/reviewed-book21-23-publication-records-20261114'
ADDITIONAL_PROGRAMS=[]
PUBLICATIONS=[
 ('book21',Path('/workspace/work/zombie-ants-reviewed-4k-v1'),445105221,814,'b91ecbd28feffce837c769ae46afdafe5c886ad32b99d10411fc1c71737a1e84'),
 ('book23',Path('/workspace/work/eleven-days-reviewed-4k-v1'),445107351,804,'4bf12bfcf0b66d422ef58cfec49acafd7b00a31bfea2ec3647a06659ea7321f9'),
]

def main():
    collect.DST=W/'payload'/PREFIX;collect.DST.mkdir(parents=True,exist_ok=True)
    bindings=[];excluded=[]
    for label,source,release_id,size,sha in PUBLICATIONS:
        identity=json.loads((source/'ACTUAL-NATIVE-PUBLICATION-IDENTITY.json').read_text());assert identity['release_id']==release_id and identity['exact_native_verification_ZIP_sha256']==sha
        for directory,dirs,files in os.walk(source):
            dirs[:]=[name for name in dirs if name not in ['__pycache__','cache','.cache','.git','node_modules']]
            for name in sorted(files):
                p=Path(directory)/name;rel=p.relative_to(source)
                if p.suffix.lower() in ['.mp4','.mov','.mkv','.wav','.mp3','.pyc']:
                    excluded.append({'source_path':str(p),'not_read_or_copied':True});continue
                assert p.suffix.lower() in ['.py','.json','.yml','.yaml','.md','.log','.txt','.csv','.diff','.patch','.zip']
                assert p.stat().st_size<=4*1024*1024
                if p.suffix.lower()=='.zip':
                    assert p.name=='native-release-verification.zip' and p.stat().st_size==size and hashlib.sha256(p.read_bytes()).hexdigest()==sha
                    with zipfile.ZipFile(p) as archive:
                        assert archive.testzip() is None and archive.namelist()==['RELEASE-VERIFICATION.json'] and archive.read('RELEASE-VERIFICATION.json')==(source/'RELEASE-VERIFICATION.json').read_bytes()
                collect.put(p,Path(label)/rel);bindings.append({'source_path':str(p),'archive_relative_path':str(Path(label)/rel),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
    for name in ['archive_reviewed_publication_records.py','observe_single_publication_records.py','prepare_safe_user_review_records.py']+ADDITIONAL_PROGRAMS:
        collect.put(B/name,Path('archivist-record-programs')/name)
    collect.save(collect.DST/'EXACT-PUBLICATION-RECORD-BINDINGS.json',{'kind':'completed-reviewed-single-publications-small-records-only','files':bindings,'excluded_media_and_pyc':excluded,'cache_directories_pruned_without_recursion':True,'historical_environment_failures_and_immutable_sources_where_observed_preserved':True,'actual_native_verification_ZIPs_CRC_and_members_exact':True,'no_video_media_source_quality_gates_or_release_changed':True,'canonical_count_not_incremented_by_publication_records':True})
    index=[]
    for p in sorted(collect.DST.rglob('*')):
        if p.is_file():index.append({'repo_path':str(p.relative_to(W/'payload')),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
    collect.save(W/'payload-file-index.json',index)
    collect.save(W/'prepared-archive.json',{'prefix':str(PREFIX),'asset_branch':ASSET_BRANCH,'scope':'Only actual completed publication small evidence; all media and caches excluded'})
    print(json.dumps({'work_dir':str(W),'files':len(index),'bytes':sum(r['bytes'] for r in index),'copied_media':0},ensure_ascii=False))

if __name__=='__main__':main()
