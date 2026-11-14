"""Verify storage identity and emit review-only links; never promote a final."""
from pathlib import Path
import argparse
import datetime
import json
import shutil
import subprocess
import urllib.parse
import urllib.request

B=Path(__file__).resolve().parent
FLAGS={'preview_only':True,'production_delivery_eligible':False,'final_user_acceptance':False,'normal70_final_assembly_eligible':False}
def load(p):return json.loads(Path(p).read_text())
def save(p,q):Path(p).write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n')
def checked(w):
    meta=load(w/'prepared-archive.json');assert meta['kind']=='user032-source28-preview-only-assets-not-final' and all(meta.get(k) is v for k,v in FLAGS.items())
    assert len(meta['articles'])==1;row=meta['articles'][0];assert row['source_id']=='28' and row['new_id']=='29' and all(row.get(k) is v for k,v in FLAGS.items()) and row['active_final_replacement_authorized'] is False
    return meta,row
def main():
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['blobs','ready','cleanup']);parser.add_argument('--work-dir',required=True);parser.add_argument('--output');a=parser.parse_args();w=Path(a.work_dir).resolve();assert w.parent==B
    meta,row=checked(w);primary=load(w/'assets-primary.json');backup=load(w/'assets-backup.json');assert primary['asset_commit']==backup['asset_commit'] and primary['video_tree_sha']==backup['video_tree_sha']
    if a.action=='blobs':
        token=subprocess.check_output(['gh','auth','token'],text=True).strip();archives=[]
        def api(repo,path):
            with urllib.request.urlopen(urllib.request.Request('https://api.github.com/repos/'+repo+'/'+urllib.parse.quote(path,safe='/?=&%'),headers={'Authorization':'Bearer '+token,'Accept':'application/vnd.github+json','User-Agent':'Codex-user032-preview-storage-only'}),timeout=30) as response:return json.loads(response.read())
        for repo,asset in [('alienalgorithm/postgraduate-vocabulary',primary),('AlienCodes/literate-enigma',backup)]:
            assert api(repo,'git/ref/heads/'+asset['asset_branch'])['object']['sha']==asset['asset_commit'];tree=api(repo,'git/trees/'+asset['video_tree_sha']+'?recursive=1');assert not tree.get('truncated');leaves={e['path']:e for e in tree['tree'] if e['type']=='blob'};assert len(leaves)==len(asset['files_index'])
            for item in asset['files_index']:
                entry=leaves[item['repo_path'][len(meta['prefix'])+1:]];assert entry['mode']=='100644' and entry['sha']==item['git_blob_sha'] and entry['size']==item['bytes']
            archives.append({'repository':repo,'asset_commit':asset['asset_commit'],'record_subtree':asset['video_tree_sha'],'files':len(leaves),'all_blob_modes_sizes_SHA_exact':True})
        result={'kind':'preview_only_actual_dual_storage_blob_verification',**FLAGS,'recorded_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'archives':archives,'actual_dual_blob_rows':2*len(primary['files_index']),'active_index_or_alias_replaced':False};save(w/'actual-dual-preview-blob-verification.json',result);print(json.dumps(result,ensure_ascii=False));return
    blob=load(w/'actual-dual-preview-blob-verification.json');stream=load(w/'remote-video-byte-verification.json');assert blob['actual_dual_blob_rows']==2*len(primary['files_index']) and stream['passed'] is True and len(stream['streams'])==2
    for repo in ['alienalgorithm/postgraduate-vocabulary','AlienCodes/literate-enigma']:
        matches=[r for r in stream['streams'] if r['repository']==repo and r['source_id']=='28'];assert len(matches)==1;proof=matches[0];assert proof['http_status']==200 and proof['passed'] is True and proof['bytes']==row['bytes'] and proof['sha256']==row['sha256'] and proof['pinned_asset_commit']==primary['asset_commit']
    if a.action=='ready':
        assert a.output
        result={**row,'kind':'user032_source28_review_download_not_final_promotion','asset_commit':primary['asset_commit'],'video_tree_sha':primary['video_tree_sha'],'primary_raw_download':'https://raw.githubusercontent.com/alienalgorithm/postgraduate-vocabulary/'+primary['asset_commit']+'/'+urllib.parse.quote(row['video_repo_path'],safe='/'),'backup_raw_download':'https://raw.githubusercontent.com/AlienCodes/literate-enigma/'+primary['asset_commit']+'/'+urllib.parse.quote(row['video_repo_path'],safe='/'),'metadata_files':{name:str(w/name) for name in ['prepared-archive.json','assets-primary.json','assets-backup.json','actual-dual-preview-blob-verification.json','remote-video-byte-verification.json']},'ready_for_preview_prerelease_download':True,'ready_for_final_active_replacement':False,'user032_effect_acceptance_pending':True,'active58_inventory_and_book29_final_alias_unchanged':True};save(a.output,result);print(json.dumps(result,ensure_ascii=False));return
    bare=w/'assets.git';assert bare.is_dir();actual_refs=[]
    for repo,asset in [('alienalgorithm/postgraduate-vocabulary',primary),('AlienCodes/literate-enigma',backup)]:
        head=subprocess.check_output(['gh','api','repos/'+repo+'/git/ref/heads/'+asset['asset_branch'],'--jq','.object.sha'],text=True).strip();assert head==asset['asset_commit'];actual_refs.append({'repository':repo,'asset_commit':head})
    test=subprocess.run(['git','--git-dir='+str(bare),'fsck','--full','--no-reflogs'],text=True,capture_output=True);assert test.returncode==0
    cache=bare;link=None
    if bare.is_symlink():
        spec=load(w/'tmpfs-owned-git-cache-location.json');target=Path(spec['owned_tmpfs_target']).resolve(strict=True);assert target.parent==Path('/dev/shm') and target.name.startswith('codex-public-approved-asset-git-') and bare.readlink()==target and spec['work_dir']==str(w) and spec['cache_symlink']==str(bare);cache=target;link=str(bare)
    size=sum(p.stat().st_size for p in cache.rglob('*') if p.is_file());shutil.rmtree(cache)
    if link:bare.unlink()
    result={'kind':'closed_preview_only_owned_Git_cache_cleanup',**FLAGS,'only_deleted':str(cache),'removed_owned_symlink':link,'logical_bytes_removed':size,'actual_dual_refs':actual_refs,'actual_dual_blob_rows':blob['actual_dual_blob_rows'],'actual_full_MP4_HTTP200_SHA256_reads':2,'fsck_exit_code':test.returncode,'all_payload_original_Mp4_ZIP_QC_sources_kept':True,'active_index_aliases_or_PDF_unchanged':True};save(w/'closed-preview-only-owned-cache-cleanup.json',result);print(json.dumps(result,ensure_ascii=False))

if __name__=='__main__':main()
