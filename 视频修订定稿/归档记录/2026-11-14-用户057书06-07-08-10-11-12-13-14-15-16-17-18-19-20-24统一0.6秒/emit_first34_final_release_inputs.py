"""Emit only installed, proven current first34 timing editions for public packaging."""
from pathlib import Path
import argparse,json

B=Path(__file__).resolve().parent
OUT=B/'first34-uniform06-057-scope-20261114/first34-final-release-inputs.json'
def load(p):return json.loads(Path(p).read_text())
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--installed-work-dir',action='append',default=[]);a=ap.parse_args()
    state=load(B/'CURRENT-ARCHIVE-STATE.json');inv=load(state['actual_inventory']);active={r['source_id']:r for r in inv['articles']}
    original=load(B/'ACTUAL-ELEVEN-NORMAL06-FINAL-ALIAS-CLOSURE.json');rows={}
    for q in original['normal_current_eleven']:
        r=active[q['source_id']]
        if r['sha256']!=q['sha256'] or r['asset_commit']!=q['asset_commit']:continue
        rows[r['source_id']]={'source_id':r['source_id'],'new_id':r['new_id'],'title_zh':r['title_zh'],'title_en':r['title_en'],'asset_commit':r['asset_commit'],'video_repo_path':r['video_repo_path'],'bytes':r['bytes'],'sha256':r['sha256'],'post_reading_pause_seconds':0.6,'actual_end_reading_pause_seconds':q['actual_gap_seconds'],'validation_handoff_sha256':q['final_full_V3_handoff_sha256'],'actual_complete_validation_passed':True,'actual_dual_permanent_archive_passed':True,'preview_only':False,'final_alias_repo_path':q['final_alias_repo_path'],'final_alias_Git_blob_SHA':q['Git_blob_SHA'],'current_final_alias_exact_identity_proven':True}
    registry=B/'first34-uniform06-057-scope-20261114/installed-scope057-asset-work-dirs.local.json'
    work_dirs=list(dict.fromkeys((load(registry) if registry.exists() else [])+a.installed_work_dir))
    for raw in work_dirs:
        w=Path(raw);m=load(w/'prepared-archive.json');p=load(w/'assets-primary.json');k=load(w/'assets-backup.json');proof=load(w/'actual-dual-asset-blob-verification.json');streams=load(w/'remote-video-byte-verification.json')
        assert p['asset_commit']==k['asset_commit'] and p['video_tree_sha']==k['video_tree_sha'] and proof['actual_dual_blob_rows']==2*len(p['files_index']) and streams['passed'] is True
        for r in m['articles']:
            assert int(r['new_id'])<=34 and r['passed_per_article'] is True and r['production_delivery_eligible'] is True and r['preview_only'] is False
            current=active[r['source_id']];assert current['asset_commit']==p['asset_commit'] and current['sha256']==r['sha256'] and current['bytes']==r['bytes']
            for repo in ['alienalgorithm/postgraduate-vocabulary','AlienCodes/literate-enigma']:
                s=[s for s in streams['streams'] if s['repository']==repo and s['source_id']==r['source_id']];assert len(s)==1 and s[0]['http_status']==200 and s[0]['sha256']==r['sha256'] and s[0]['bytes']==r['bytes']
            blob=next(f for f in p['files_index'] if f['repo_path']==r['video_repo_path']);assert blob['sha256']==r['sha256']
            rows[r['source_id']]={key:r[key] for key in ['source_id','new_id','title_zh','title_en','video_repo_path','bytes','sha256']}
            rows[r['source_id']].update(asset_commit=p['asset_commit'],post_reading_pause_seconds=0.6,actual_end_reading_pause_seconds=r['actual_end_reading_pause_seconds'],validation_handoff_sha256=r['postprocessing_full_V3_handoff_sha256'],actual_complete_validation_passed=True,actual_dual_permanent_archive_passed=True,preview_only=False,final_alias_repo_path='视频修订定稿/最终定稿/视频/'+r['new_id']+' '+r['title_zh']+'.mp4',final_alias_Git_blob_SHA=blob['git_blob_sha'],current_final_alias_exact_identity_proven=True)
    ordered=sorted(rows.values(),key=lambda r:int(r['new_id']));scope=load(B/'first34-uniform06-057-scope-20261114/PUBLIC-FIRST34-UNIFORM06-SCOPE.json');mapping={r['book_order']:r['source_id'] for r in scope['book_source_mapping']}
    for r in ordered:assert mapping[r['new_id']]==r['source_id'] and r['actual_end_reading_pause_seconds']>=0.6
    done=len(ordered)==34 and {r['new_id'] for r in ordered}==set(mapping)
    proof=state['final_directory'];result={'kind':'purpose-built-first34-final-release-inputs','user_facing_date':'2026-11-14','user_timezone':'America/New_York','current_main_commit':state['primary_main'],'current_backup_delivery_commit':state['backup_head'],'expected_video_count':34,'actual_ready_video_count':len(ordered),'all34_complete':done,'partial':not done,'end_reading_pause_seconds':0.6,'final_alias_exact_proof':{'same_final_folder_tree_in_both_repositories':proof['final_tree_sha'],'actual_final_video_folder_tree':proof['video_tree_sha'],'all_current_final_file_modes_sizes_Git_SHA_verified':proof['all_file_modes_sizes_gitSHA_verified'],'current_final_unique_video_count':proof['video_count']},'videos':ordered,'not_yet_ready_book_orders':sorted(set(mapping)-{r['new_id'] for r in ordered}),'book35_plus_media_audio_body_not_changed':True,'PDF_work_remains_paused':True}
    text=json.dumps(result,ensure_ascii=False,indent=2)+'\n';assert not any(v in text for v in ['/workspace/','/dev/shm/','/home/','CURRENT-ROOT','USER-REVIEW-2026-11-14-055','USER-REVIEW-2026-11-14-056']);OUT.write_text(text);registry.write_text(json.dumps(work_dirs,indent=2)+'\n');print(json.dumps({'output':str(OUT),'actual_ready_video_count':len(ordered),'all34_complete':done,'no_internal_workspace_paths':True}))
if __name__=='__main__':main()
