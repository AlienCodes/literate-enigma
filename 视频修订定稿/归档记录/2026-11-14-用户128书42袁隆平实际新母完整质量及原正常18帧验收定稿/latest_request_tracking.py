"""Update serving metadata from the very H/media already verified by the installer."""
from copy import deepcopy
from pathlib import Path
import hashlib,json

def read(spec):
 p=Path(spec['path']);raw=p.read_bytes();assert len(raw)==spec['bytes']and hashlib.sha256(raw).hexdigest()==spec['sha256'];return raw
def public_spec(spec):return {k:spec[k]for k in ['bytes','sha256','origin','derived_from_json_sha256']if k in spec}
def complete(previous,incoming,asset_inputs,authorization,plan):
 result=deepcopy(previous);byid={r['source_id']:r for r in result['articles']};old=deepcopy(byid)
 permits={r['source_id']:r for r in authorization['document']['authorized_revisions']}if authorization else {}
 for row in incoming:
  sid=row['source_id'];entry=byid[sid];expected=row['postprocessing_full_V3_handoff_sha256']
  material=[b for m,asset,w in asset_inputs if any(x['source_id']==sid for x in m['articles'])for b in m.get('material_source_bindings',[])if b['sha256']==expected]
  assert material,'Exact already-passed final handoff must be included in the dual-archived payload'
  specs=[{'path':b['original_path'],'bytes':b['bytes'],'sha256':b['sha256']}for b in material];h=json.loads(read(specs[0]))
  assert h['status']=='passed_actual_normal18_post_only_for_permanent_archive'and h['production_delivery_eligible']is True and h['preview_only']is False
  if h['kind']not in {'authorized-normal18-local-tail-derivative','actual-new-native-source-QA-then-authorized-normal18-local-tail'}:
   import existing_final_tail_handoff_compat as exact_kind
   exact_kind.check(h,expected)
  assert len(h['articles'])==1;a=h['articles'][0];assert a['source_id']==sid and a['new_id']==row['new_id']and a['passed_per_article']is True
  assert all(a['final_mp4'][k]==row[k]for k in ['bytes','sha256'])and row['post_reading_pause_seconds']==0.6
  if not entry['latest_requested_revision_complete']:
   assert entry.get('final_4K_generation_authorized')is True,'A draft or unbound historical file cannot become final merely by copying'
   authority=entry['latest_finalization_authority'];spec=permits[sid]['review_record']if sid in permits else plan['latest_request_authorities'][sid]
   raw=read(spec);assert hashlib.sha256(raw).hexdigest()==entry['user_request_SHA256'][authority]
   user=json.loads(raw);assert user['author']=='user'and user['source_id']==sid
  pair=a['section']['final_source'];entry.update(status='latest_qualified_cloud_final',latest_requested_revision_complete=True,actual_complete_validation_passed=True,actual_dual_permanent_archive_passed=True,title_zh=row['title_zh'],latest_revision_final={k:row[k]for k in ['asset_commit','video_repo_path','bytes','sha256']},validation_handoff_sha256=expected,post_reading_pause_seconds=0.6,illustration_seconds=2,summary_card_seconds=2,source_and_GEN_MD={k:public_spec(v)for k,v in pair.items()},source_roles_preserved=True)
  entry['previously_accepted_cloud_final']={k:row[k]for k in ['asset_commit','video_repo_path','bytes','sha256']}
 assert all(byid[sid]==r for sid,r in old.items()if sid not in {r['source_id']for r in incoming})
 result['latest_requested_revision_completed_count']=sum(r['latest_requested_revision_complete']for r in result['articles']);result['all70_latest_complete']=all(r['latest_requested_revision_complete']for r in result['articles'])
 return result
