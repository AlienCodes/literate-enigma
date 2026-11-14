"""Four meaningful metadata scenarios; no media generation or repeated QA."""
from pathlib import Path
from copy import deepcopy
import importlib.util,hashlib,json,sys
B=Path('/workspace/work/video-archive-batches-20261114');R=Path(__file__).parent;sys.path.insert(0,str(B))
import build_final_alias_plan as aliases
import final_alias_git as trees
import latest_final_directory_policy as policy
import archive_revision_policy as revisions
def load(p):return json.loads(Path(p).read_text())
state=load(R/'CURRENT-ARCHIVE-STATE.json');inv=load(state['actual_inventory']);observed=load(R/'actual-canonical-video-tree-before146.local.json');assert observed['sha']==state['video_subtree'];actual={x['path']:x for x in observed['tree']};catalog=load(state['final_alias_catalog']['path']);registry=load(R/'user146-planned-latest_requests.json')
spec=importlib.util.spec_from_file_location('old_before146_aliases',B/'build_final_alias_plan-before-user146-latest-only.py');legacy=importlib.util.module_from_spec(spec);spec.loader.exec_module(legacy)
oldplan=legacy.build(inv,actual,catalog);assert aliases.build(inv,actual,catalog)==oldplan;trees.assert_existing_final_matches(inv,actual,catalog)
original=deepcopy(inv);live=deepcopy(inv);live[policy.KEY]=deepcopy(policy.POLICY);plan=aliases.build(live,actual,catalog,latest_requests=registry);selected={x['source_id']:x for x in plan['manifest']['videos']}
assert '19'not in selected and len(plan['video_entries'])==plan['manifest']['current_count']==plan['manifest']['latest_deliverable_count']
assert plan['manifest']['archived_passed_count']==60 and len(selected)<60
assert {x['source_id']for x in plan['manifest']['excluded_older_accepted']}==set(x['source_id']for x in inv['articles'])-set(selected)
try:aliases.build(live,actual,catalog)
except AssertionError:pass
else:raise AssertionError('146 missing registry fell back to old accepted aliases')
# The real actual39 final restores a pending39 entry using its real new SHA.
pending=deepcopy(registry);p=next(x for x in pending['articles']if x['source_id']=='29');p['latest_requested_revision_complete']=False;p['actual_complete_validation_passed']=False;p['actual_dual_permanent_archive_passed']=False;p.pop('latest_revision_final',None)
before_restore=aliases.build(live,actual,catalog,latest_requests=pending);assert '29'not in {r['source_id']for r in before_restore['manifest']['videos']};assert selected['29']['sha256']=='b26c43e7dfef10cd17a068d36a0cdd24e58d522a15d75e6595b73b14f914e244'
wrong=deepcopy(registry);next(x for x in wrong['articles']if x['source_id']=='29')['latest_revision_final']['sha256']='0'*64
try:aliases.build(live,actual,catalog,latest_requests=wrong)
except AssertionError:pass
else:raise AssertionError('wrong completed SHA restored a stale alias')
# The real077 rename has one current basename; 090 keeps source07 at video01/book03.
names=[e['path']for e in plan['video_entries']];assert names.count('36 爱因斯坦的诺奖之路.mp4')==1 and '36 改变世界的科学巨匠.mp4'not in names
assert len(names)==len(set(names))and len(selected)==len(plan['manifest']['videos']);assert selected['07']['current_video_order']=='01'and selected['07']['original_book_order']=='03';assert plan['manifest']['video_order_overlay']==inv['video_order_overlay']
# Future merge uses the real old/new29 rows and immutable110 H, preserving all others.
row=next(x for x in inv['articles']if x['source_id']=='29');fixture=deepcopy(live);idx=next(i for i,x in enumerate(fixture['articles'])if x['source_id']=='29');fixture['articles'][idx]=deepcopy(row['previous_versions'][-1]);fixture['batches']=[b for b in fixture['batches']if b['prefix']!=row['archive_prefix']]
loc=load(R/'active-source29-puretail-staging-location.json');w=Path(loc['work_dir']);m=load(w/'prepared-archive.json');asset=load(w/'assets-primary.json');incoming=[{**m['articles'][0],'asset_commit':asset['asset_commit'],'archive_prefix':m['prefix']}];auth=revisions.authorization(R/'user110-134-existing-tail-final-authorizations.json');batch={'prefix':row['archive_prefix'],'asset_commit':row['asset_commit'],'source_ids':['29']};merged=revisions.merge_inventory(fixture,incoming,batch,auth);revisions.validate_transition(fixture,merged,incoming,auth)
assert merged[policy.KEY]==policy.POLICY and merged['video_order_overlay']==fixture['video_order_overlay'];assert all(r==next(x for x in merged['articles']if x['source_id']==r['source_id'])for r in fixture['articles']if r['source_id']!='29');assert inv==original
summary={'kind':'actual-metadata-user146-four-latest-directory-plan-scenarios','legacy_no_flag_plan_entire_object_and_text_bytes_unchanged':True,'pending_old_accepted_alias_excluded_and_missing_registry_refused':True,'actual_new39_final_restores_and_wrong_SHA_refused':True,'actual077_new_title_single_alias_and_090_order_preserved':True,'future_real110_merge_preserves_146_flag_other_rows_and_all_history':True,'archived_count':60,'actual_planned_latest_directory_count':len(selected),'actual_excluded_old_accepted_sources':[r['source_id']for r in plan['manifest']['excluded_older_accepted']],'only_metadata_tests_no_new_media_QA':True}
(R/'user146-actual-metadata-plan-checks.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n');(R/'user146-planned-cumulative-inventory.json').write_text(json.dumps(live,ensure_ascii=False,indent=2)+'\n');(R/'user146-planned-final-alias-plan.local.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n');print(json.dumps(summary,ensure_ascii=False),flush=True)
