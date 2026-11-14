"""Preserve only the completed publication's small records, never its MP4s."""
from pathlib import Path
import datetime
import hashlib
import json
import zipfile
import prepare_safe_user_review_records as collect

B=Path(__file__).resolve().parent
SOURCE=Path('/workspace/work/book24-26-release-v1')
W=B/'book24-26-publication-record-assets-20261114'
PREFIX=Path('发行记录/2026-11-14-书24至26三篇4K原件发布')

def main():
    collect.DST=W/'payload'/PREFIX
    collect.DST.mkdir(parents=True,exist_ok=True)
    rows=[];excluded=[]
    for p in sorted(SOURCE.rglob('*')):
        if not p.is_file() or '__pycache__' in p.parts:continue
        if p.suffix.lower()=='.mp4':
            excluded.append({'name':str(p.relative_to(SOURCE)),'bytes':p.stat().st_size,'excluded_without_reading_or_copying_media':True})
            continue
        assert p.suffix.lower() in ['.json','.py','.md','.log','.yml','.yaml','.txt','.csv','.diff','.patch','.zip']
        assert p.stat().st_size<=4*1024*1024, 'Only small publication records authorized'
        if p.suffix.lower()=='.zip':
            assert p.name=='book24-26-release-verification.zip' and p.stat().st_size==805
            assert hashlib.sha256(p.read_bytes()).hexdigest()=='2459e22ce00ee4cdfbd615a5edcac1179ef0c7fa38cd2b52e0f1398c0df8ad7d'
            with zipfile.ZipFile(p) as z:
                assert z.testzip() is None and z.namelist()==['RELEASE-VERIFICATION.json']
                assert z.read('RELEASE-VERIFICATION.json')==(SOURCE/'RELEASE-VERIFICATION.json').read_bytes()
        relative=p.relative_to(SOURCE);collect.put(p,Path('原发布小记录')/relative)
        rows.append({'original_path':str(p),'archive_relative_path':str(Path('原发布小记录')/relative),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
    assert len(excluded)==3
    for name in ['archive_book24_26_publication_records.py','prepare_safe_user_review_records.py']:
        collect.put(B/name,Path('归档程序')/name)
    collect.save(collect.DST/'保存范围及原文件绑定.json',{'kind':'completed-book24-26-publication-records-only','recorded_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'files':rows,'three_MP4s_explicitly_excluded':excluded,'release_id':445087105,'release_tag':'kaoyanxueren-book24-26-4k-v1','actual_native_run':43568699374,'canonical_refs_modified':False,'existing_release_or_tag_modified':False,'new_media_generated_or_QC_repeated':False})
    index=[]
    for q in sorted(collect.DST.rglob('*')):
        if q.is_file():index.append({'repo_path':str(q.relative_to(W/'payload')),'bytes':q.stat().st_size,'sha256':hashlib.sha256(q.read_bytes()).hexdigest()})
    collect.save(W/'payload-file-index.json',index)
    collect.save(W/'prepared-archive.json',{'prefix':str(PREFIX),'asset_branch':'codex/book24-26-publication-records-20261114','scope':'Completed publication small records and exact805B verification ZIP only; three MP4s excluded'})
    print(json.dumps({'work_dir':str(W),'files':len(index),'bytes':sum(r['bytes'] for r in index),'copied_media':0,'canonical_mutation':False},ensure_ascii=False))

if __name__=='__main__':main()
