"""User146 latest-only aliases; original accepted rows/history never change."""
from copy import deepcopy
from pathlib import Path
import hashlib,json

USER_SHA='e759548c0f1889fed996d8fd627e69eae26fe3c4ce0013a911a9f61ac61dd772'
KEY='latest_final_directory_policy'
POLICY={'kind':'explicit-user146-unique-latest-final-video-directory','authority_review_sha256':USER_SHA,'managed_video_directory':'视频修订定稿/最终定稿/视频/','source_specific_pending_request_excludes_older_alias':True,'completed_latest_must_match_current_row_asset_path_bytes_SHA':True,'no_source_specific_pending_requires_explicit_passed_current_row':True,'old_archive_rows_blobs_and_history_preserved':True,'new_current_and_raw_pending_updates_sync_directory_same_commit':True,'video_order090_and_frozen_quality_book_order_preserved':True}

def activation(spec):
 raw=Path(spec['path']).read_bytes();assert len(raw)==spec['bytes']and hashlib.sha256(raw).hexdigest()==spec['sha256']==USER_SHA
 d=json.loads(raw);assert d['author']=='user'and d['scope']=='global'and d['kind']=='global_unique_latest_final_video_directory_and_no_stale_alias_policy'
 return deepcopy(POLICY)

def select(inventory,registry):
 assert inventory.get(KEY)==POLICY,'The latest-only policy requires the exact user146 authority'
 assert isinstance(registry,dict)and registry['kind']=='public-purpose-built-latest-user-video-request-registry','An explicit frozen latest registry is required; no old accepted fallback'
 rr=registry['articles'];byid={r['source_id']:r for r in rr};assert len(rr)==len(byid)==70
 assert set(byid)=={f'{n:02d}'for n in range(1,71)}
 order={x['source_id']:x['video_order']for x in inventory['video_order_overlay']['video_order']}
 selected=set();excluded=[]
 for row in inventory['articles']:
  sid=row['source_id'];e=byid[sid];assert row['passed_per_article']is True
  assert e['frozen_book_order']==row['new_id']and e['current_video_order']==order[sid]
  if e.get('latest_requested_revision_complete')is True:
   assert e['actual_complete_validation_passed']is True and e['actual_dual_permanent_archive_passed']is True
   current={k:row[k]for k in ['asset_commit','video_repo_path','bytes','sha256']}
   assert e['latest_revision_final']==current,'Claimed complete revision must equal the exact current article; never restore a different SHA'
   selected.add(sid)
  elif e.get('newest_user_revision_records')or e.get('newer_actual_media_known_not_current')is True:
   excluded.append({'source_id':sid,'current_video_order':order[sid],'original_book_order':row['new_id'],'title_zh':row['title_zh'],'latest_user_records':deepcopy(e.get('newest_user_revision_records',[])),'status':e['status'],'reason':'newer_article_revision_pending_old_accepted_is_history_only'})
  else:
   # A truly passed current row with no newer source-specific request is usable.
   if 'previously_accepted_cloud_final'in e:assert e['previously_accepted_cloud_final']=={k:row[k]for k in ['asset_commit','video_repo_path','bytes','sha256']}
   selected.add(sid)
 pending=[{'source_id':e['source_id'],'current_video_order':e['current_video_order'],'original_book_order':e['frozen_book_order'],'title_zh':e['title_zh'],'status':e['status'],'latest_user_records':deepcopy(e.get('newest_user_revision_records',[]))}for e in rr if e.get('newest_user_revision_records')and not e.get('latest_requested_revision_complete')]
 return selected,{'policy':deepcopy(POLICY),'latest_requests_canonical_json_sha256':hashlib.sha256((json.dumps(registry,ensure_ascii=False,indent=2)+'\n').encode()).hexdigest(),'archived_passed_count':len(inventory['articles']),'latest_deliverable_count':len(selected),'excluded_older_accepted':sorted(excluded,key=lambda x:int(x['current_video_order'])),'pending_latest_user_requests':sorted(pending,key=lambda x:int(x['current_video_order']))}
