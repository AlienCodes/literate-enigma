"""Mature exact source45/book70 revision after real separate user publication consent."""
from pathlib import Path
import base64,hashlib,json,subprocess,sys,os,shutil,urllib.parse,urllib.request
B=Path(__file__).parent;C=Path('/dev/shm/archive-writer-main061')
def load(p):return json.loads(Path(p).read_bytes())
def save(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def spec(p):
 p=Path(p);b=p.read_bytes();return {'path':str(p),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
def main():
 state=load(C/'CURRENT-ARCHIVE-STATE.json');prior=Path(state['actual_inventory']);before=load(prior)
 assert before['archived_passed_count']==65
 old=next(x for x in before['articles'] if x['source_id']=='45')
 assert old['new_id']=='70' and old['sha256']=='96af2c088e534c311ae4d67088835598d9d4a2f795c84fa4ac06759d49bf2b66'
 token=subprocess.check_output(['gh','auth','token'],text=True).strip()
 def api(repo,path):
  q=urllib.request.Request('https://api.github.com/repos/'+repo+'/'+urllib.parse.quote(path,safe='/?=&%'),headers={'Authorization':'Bearer '+token,'Accept':'application/vnd.github+json','User-Agent':'source45-mature-current-readback'})
  with urllib.request.urlopen(q,timeout=60) as r:return json.loads(r.read())
 repos=[('primary','alienalgorithm/postgraduate-vocabulary','main','primary_main'),('backup','AlienCodes/literate-enigma','codex/all-deliverables-20261113','backup_head')]
 old_alias_trees={}
 for role,repo,branch,key in repos:
  assert api(repo,'git/ref/heads/'+branch)['object']['sha']==state[key]
  old_alias_trees[role]={x['path']:x for x in api(repo,'git/trees/'+state['final_directory']['video_tree_sha'])['tree']}
  assert len(old_alias_trees[role])==62
 baseline=load(C/'latest_requests.json');priority=baseline['video_work_priority_policy']
 e=next(x for x in baseline['articles'] if x['source_id']=='45')
 assert e['latest_requested_revision_complete'] is False and not e.get('latest_finalization_authority')
 assert baseline['latest_requested_revision_completed_count']==52
 loc=load(C/'active-source45-book70-existing-normal18-staging-location.json');HOST=Path(loc['root']);W=Path(loc['work_dir'])
 m=load(W/'prepared-archive.json');row=m['articles'][0];ready=load(HOST/'ready-book70-source45-existing-normal18.json')
 assert ready['asset_commit']==load(W/'assets-primary.json')['asset_commit']==load(W/'assets-backup.json')['asset_commit']
 assert row['bytes']==15768989 and row['sha256']=='c72753547d18ca0f9e9041ef41de9502d25d31e39295a2488c2886cec6bccef8'
 assert row['postprocessing_full_V3_handoff_sha256']=='9755327747b30b8e83878836f26f4cf682ebadb851b0fd0c66e72d7e01b0564c'
 assert row['approved_audio_repair_applied'] is False and row['new_native_Actions_run_claimed'] is False and row['inherited_full_native_archive_commit']==old['asset_commit']
 assert load(W/'actual-dual-asset-blob-verification.json')['actual_dual_blob_rows']==2*loc['files']==380
 assert load(W/'remote-video-byte-verification.json')['passed'] is True
 user=Path('/workspace/work/book70-source45-final-source-and-normal18-data-only-preparation-20261115/USER-BOOK68-SOURCE25-APOLLO13-FINALIZATION-20261115.json');us=spec(user)
 consent=Path('/workspace/work/all-project-deliverables-and-final70-release-authorities-20261115/USER-ALL-PROJECT-GENERATED-DELIVERABLES-GITHUB-ARCHIVE-AUTHORITY.json');cs=spec(consent)
 assert us['sha256']=='591135ed41aa8fa6fea7b97c838214571d7be7342ef59255fca6a3fe1dbe7f8a'
 assert cs['sha256']=='b00a133cc88ed37496e225a181898863ce52e9a774e6b5c2991a310691fd4312'
 assert any(x['sha256']==cs['sha256'] for x in m['material_source_bindings'])
 import archive_revision_policy as revisions
 auth={'kind':'explicit-completed-user-review-video-revision-archive-authorization','requirements':{
  'old_asset_blobs_and_history_preserved':True,'unique_article_count_increased_by_revisions':False,
  'all_other_article_rows_unchanged':True,'published_review40_release_unchanged':True,
  'real_actual_full_V3_handoff_and_full_dual_byte_verification_still_required':True},
  'actual_original_native_source_run_preserved_for_local_tail_derivative':True,'new_native_or_TTS_run_not_invented':True,'additional_global_transition_authority':spec(B.parent/'first50-review-release/USER-REVIEW-2026-11-14-051.json'),
  'authorized_revisions':[{'source_id':'45','new_id':'70','previous_row':old,'previous_row_sha256':revisions.identity(old),'review_record':us,'actual_hold18_handoff':spec(Path(loc['handoff']))}]}
 ap=HOST/'actual-book70-source45-current-final-revision-authorization.json';save(ap,auth);revisions.authorization(ap)
 op=HOST/'operations-book70-source45-full-current-final';assert not op.exists()
 for n in ['archive_batch.py','prepare_operation.py']:shutil.copyfile(B/n,HOST/n)
 integrator=C/'integrate_verified_batch-book48-isolated-single-delta-transport.py'
 assert spec(integrator)['sha256']=='e44686bf2d238e96c1aad08f522b927de8c29955e196d61277a6e28a5fed9400'
 env={**os.environ,'PYTHONPATH':str(B),'PYTHONDONTWRITEBYTECODE':'1','TMPDIR':str(HOST)}
 cmd=[sys.executable,HOST/'prepare_operation.py','--work-dir',op,'--batch','2026-11-15-书70原45实际正常18帧新定稿及真实源文档公开许可',
  '--asset-branch','codex/book70-source45-full-current-final-records-v1','--previous-inventory',prior,'--revision-authorization',ap,'--article-work-dir',W]
 for p in [B/'latest_final_directory_policy.py',B/'latest_request_tracking.py',B/'integrate_verified_batch.py',integrator,B/'video_order_authorization.py',
  B/'video_title_authorization.py',B/'exact_existing_tail_authorities.py',B/'prepare_actual_source45_book70_existing_normal18_assets.py',B/'transport_source45_book70_existing_normal18_assets.py',
  HOST/'ACTUAL-BOOK68-UNIQUE-GIT-TRANSPORT-BUDGET.json',consent,Path(__file__)]:cmd+=['--attach',p]
 subprocess.run(list(map(str,cmd)),check=True,env=env)
 for _,repo,_,_ in repos:
  subprocess.run([sys.executable,str(HOST/'archive_batch.py'),'push','--work-dir',str(op),'--repo',repo],check=True,timeout=180,env=env)
 # Exact small-operation raw readback, in addition to the mature Git identity gates.
 operation_readbacks=[]
 for role,repo,_,_ in repos:
  asset=load(op/('assets-'+role+'.json'))
  assert api(repo,'git/ref/heads/'+asset['asset_branch'])['object']['sha']==asset['asset_commit']
  for f in asset['files_index']:
   raw=base64.b64decode(api(repo,'git/blobs/'+f['git_blob_sha'])['content'])
   assert len(raw)==f['bytes'] and hashlib.sha256(raw).hexdigest()==f['sha256']
  operation_readbacks.append({'repository':repo,'commit':asset['asset_commit'],'files':len(asset['files_index']),'all_raw_SHA256_exact':True})
 save(op/'actual-dual-small-operation-full-raw-readback.json',operation_readbacks)
 plan={'writer_window_granted_by_root':True,'expected_heads':{'primary':state['primary_main'],'backup':state['backup_head']},
  'previous_inventory':str(prior),'operation_work_dir':str(op),'article_work_dirs':[str(W)],'revision_authorization':str(ap),'exact_existing_tail_finalization_authorities':{'45':us},
  'result_count':65,'source_run':m['source_run'],'latest_requests_local_path':str(C/'latest_requests.json'),
  'message':'书70原45实际完整源与4K定稿双仓保存，按真实新许可公开源文档，保旧版并同步唯一最新目录 [skip ci]'}
 pp=C/'integration-plan-book70-source45-full-final.json';save(pp,plan)
 subprocess.run([sys.executable,str(integrator),'--plan',str(pp),'--execute'],check=True,env=env)
 after=load(C/'CURRENT-ARCHIVE-STATE.json');inv=load(after['actual_inventory']);now={x['source_id']:x for x in inv['articles']}
 assert len(now)==65 and all(now[x['source_id']]==x for x in before['articles'] if x['source_id']!='45')
 assert now['45']['previous_versions'][-1]==old and now['45']['sha256']==row['sha256']
 assert inv['latest_final_directory_policy']==before['latest_final_directory_policy'] and inv['video_order_overlay']==before['video_order_overlay']
 reg=load(C/'latest_requests.json');en=next(x for x in reg['articles'] if x['source_id']=='45')
 assert en['latest_requested_revision_complete'] is True and en['latest_revision_final']['sha256']==row['sha256']
 assert reg['latest_requested_revision_completed_count']==53 and after['final_directory']['video_count']==62
 assert reg['video_work_priority_policy']==priority and all(x==y for x,y in zip(baseline['articles'],reg['articles']) if x['source_id']!='45')
 alias='70 写给外星人的一张唱片.mp4';canonical_streams=[]
 for role,repo,branch,key in repos:
  head=after[key];assert api(repo,'git/ref/heads/'+branch)['object']['sha']==head
  tree={x['path']:x for x in api(repo,'git/trees/'+after['final_directory']['video_tree_sha'])['tree']}
  assert set(tree)==set(old_alias_trees[role]) and alias in tree
  assert tree[alias]['sha']!=old_alias_trees[role][alias]['sha']
  assert all(tree[n]==v for n,v in old_alias_trees[role].items() if n!=alias)
  path='视频修订定稿/最终定稿/视频/'+alias
  url='https://raw.githubusercontent.com/'+repo+'/'+head+'/'+urllib.parse.quote(path,safe='/')
  hasher=hashlib.sha256();n=0
  with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'source45-current-latest-alias-full-byte-readback'}),timeout=120) as response:
   assert response.status==200
   for b in iter(lambda:response.read(1024*1024),b''):n+=len(b);hasher.update(b)
  assert n==row['bytes'] and hasher.hexdigest()==row['sha256']
  canonical_streams.append({'repository':repo,'commit':head,'alias_path':path,'bytes':n,'sha256':hasher.hexdigest(),'http_status':200,'immutable_URL':url})
 out={'kind':'actual-book70-source45-full-current-final-after-real-user-source-publication-consent',
  'primary_main':after['primary_main'],'backup_delivery':after['backup_head'],'archived_passed_count':65,
  'actual_latest_directory_count':62,'latest_user_request_completed_count':53,'source_id':'45','book_order':'70',
  'final_bytes':row['bytes'],'final_sha256':row['sha256'],'actual_handoff_sha256':loc['handoff_sha256'],
  'source_publication_consent_sha256':cs['sha256'],'quality_H_unchanged_and_actualb00_publication_consent_bound':True,
  'only_source45_row_revised_other64_exact':True,'old_accepted_whole_row_and_history_preserved_in_previous_versions':True,
  'only_source45_latest_request_complete_other69_rows_equal':True,'other61_MP4_alias_nodes_exact_one_replaced70_alias':True,
  'other_pending_final_sources_not_promoted_without_qualified_H':True,
  'all_other_final_targets_remain_according_to_actual_registry_not_assumed_done':True,
  'originalb00_consent_and_full_H_source_GEN_MD_QA_actually_dual_archived':True,
  'no_private_RAW_GT_cache_models_tokens_signedURL_ROOTSTATE_PDF_or_unrelated_source_uploaded':True,
  '090_146_153_history_and_PDF_master_other_roots_preserved':True,'no_new_Release':True,
  'full_READY':str(HOST/'ready-book70-source45-existing-normal18.json'),
  'actual_asset_blob_rows':380,'actual_asset_MP4_streams':2,'actual_canonical_alias_streams':canonical_streams,
  'operation_full_raw_readbacks':operation_readbacks,'archive_receipt':after['last_completed_receipt']}
 cp=C/'actual-book70-source45-full-current-final-closure.json';save(cp,out)
 print(json.dumps({'closure':str(cp),'closure_SHA256':spec(cp)['sha256'],'primary':after['primary_main'],
  'backup':after['backup_head'],'archive':65,'latest':62,'complete':53},ensure_ascii=False),flush=True)
if __name__=='__main__':main()
