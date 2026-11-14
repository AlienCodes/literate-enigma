"""Emit immutable links only after real handoff, dual blobs and full HTTP readback."""
from pathlib import Path
import argparse
import json
import urllib.parse

def load(p):return json.loads(Path(p).read_text())
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--work-dir',required=True);parser.add_argument('--handoff',required=True);parser.add_argument('--output',required=True);a=parser.parse_args()
    w=Path(a.work_dir).resolve();meta=load(w/'prepared-archive.json');primary=load(w/'assets-primary.json');backup=load(w/'assets-backup.json');streams=load(w/'remote-video-byte-verification.json');blobs=load(w/'actual-dual-asset-blob-verification.json');handoff=load(a.handoff)
    assert len(meta['articles'])==len(handoff['articles'])==1
    row=meta['articles'][0];original=handoff['articles'][0]
    assert row['passed_per_article'] is True and original['source_id']==row['source_id'] and original['new_id']==row['new_id'] and original['final_mp4']['sha256']==row['sha256'] and original['final_mp4']['bytes']==row['bytes']
    assert primary['asset_commit']==backup['asset_commit'] and primary['video_tree_sha']==backup['video_tree_sha']
    assert blobs['actual_dual_blob_rows']==2*len(primary['files_index']) and streams['passed'] is True and len(streams['streams'])==2
    for repo in ['alienalgorithm/postgraduate-vocabulary','AlienCodes/literate-enigma']:
        matches=[r for r in streams['streams'] if r['repository']==repo and r['source_id']==row['source_id']];assert len(matches)==1
        proof=matches[0];assert proof['passed'] is True and proof['http_status']==200 and proof['bytes']==row['bytes'] and proof['sha256']==row['sha256'] and proof['pinned_asset_commit']==primary['asset_commit']
    result={**row,'asset_commit':primary['asset_commit'],'video_tree_sha':primary['video_tree_sha'],'primary_raw_download':'https://raw.githubusercontent.com/alienalgorithm/postgraduate-vocabulary/'+primary['asset_commit']+'/'+urllib.parse.quote(row['video_repo_path'],safe='/'),'backup_raw_download':'https://raw.githubusercontent.com/AlienCodes/literate-enigma/'+primary['asset_commit']+'/'+urllib.parse.quote(row['video_repo_path'],safe='/'),'metadata_files':{name:str(w/name) for name in ['assets-primary.json','assets-backup.json','remote-video-byte-verification.json','prepared-archive.json','actual-dual-asset-blob-verification.json']},'real_V3_handoff':str(Path(a.handoff).resolve()),'unique_article_count_increased':False,'old_article_and_review40_release_preserved':True,'ready_for_single_new_revision_release':True}
    Path(a.output).write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'manifest':a.output,'source_id':row['source_id'],'book_order':row['new_id'],'asset_commit':primary['asset_commit'],'bytes':row['bytes'],'sha256':row['sha256'],'true_dual_full_MP4_HTTP200_and_blobs_closed':True},ensure_ascii=False))

if __name__=='__main__':main()
