"""Mature exact source70/book50 first accepted installation after real separate user publication consent."""
from pathlib import Path
import base64,hashlib,json,subprocess,sys,os,shutil,urllib.parse,urllib.request
B=Path(__file__).parent;C=Path('/dev/shm/archive-writer-main061')
def load(p):return json.loads(Path(p).read_bytes())
def save(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def spec(p):
 p=Path(p);b=p.read_bytes();return {'path':str(p),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
def main():
 state=load(C/'CURRENT-ARCHIVE-STATE.json');prior=Path(state['actual_inventory']);before=load(prior)
 assert before['archived_passed_count']==67
 assert not any(x['source_id']=='70'for x in before['articles'])
 token=subprocess.check_output(['gh','auth','token'],text=True).strip()
 def api(repo,path):
  q=urllib.request.Request('https://api.github.com/repos/'+repo+'/'+urllib.parse.quote(path,safe='/?=&%'),headers={'Authorization':'Bearer '+token,'Accept':'application/vnd.github+json','User-Agent':'source70-mature-current-readback'})
  with urllib.request.urlopen(q,timeout=60) as r:return json.loads(r.read())
 repos=[('primary','alienalgorithm/postgraduate-vocabulary','main','primary_main'),('backup','AlienCodes/literate-enigma','codex/all-deliverables-20261113','backup_head')]
 old_alias_trees={}
 for role,repo,branch,key in repos:
  assert api(repo,'git/ref/heads/'+branch)['object']['sha']==state[key]
  old_alias_trees[role]={x['path']:x for x in api(repo,'git/trees/'+state['final_directory']['video_tree_sha'])['tree']}
  assert len(old_alias_trees[role])==62
 baseline=load(C/'latest_requests.json');priority=baseline['video_work_priority_policy']
 e=next(x for x in baseline['articles'] if x['source_id']=='70')
 assert e['latest_finalization_authority']=='assistant-derived-record-key-final-book50-source70-f4a049d869e0' and e['final_4K_generation_authorized'] is True
 assert baseline['latest_requested_revision_completed_count']==62
 loc=load(C/'active-source70-book50-full-asset-staging-location.json');HOST=Path(loc['root']);W=Path(loc['work_dir'])
 m=load(W/'prepared-archive.json');row=m['articles'][0];ready=load(HOST/'ready-book50-source70-full.json')
 assert ready['asset_commit']==load(W/'assets-primary.json')['asset_commit']==load(W/'assets-backup.json')['asset_commit']
 assert row['bytes']==14874227 and row['sha256']=='b4f8f6123e100ebbc1252de834f8d18f1e85db4719de89415d596b81614c0f79'
 assert row['postprocessing_full_V3_handoff_sha256']=='9b7de7262eaa8dcb8f91abfb323cab92829d10a603df42eaf6c2b5fc7cf36758'
 assert row['source_native_audio_repair_applied'] is False and row['local_tail_postprocessing_audio_repair_applied'] is False
 assert load(W/'actual-dual-asset-blob-verification.json')['actual_dual_blob_rows']==2*loc['files']
 assert load(W/'remote-video-byte-verification.json')['passed'] is True
 user=Path('/workspace/work/book50-source70-layout-and-illustration-final-preparation-20261115/actual-user-message-raw-and-three-roles.json');us=spec(user)
 consent=Path('/workspace/work/all-project-deliverables-and-final70-release-authorities-20261115/USER-ALL-PROJECT-GENERATED-DELIVERABLES-GITHUB-ARCHIVE-AUTHORITY.json');cs=spec(consent)
 assert us['sha256']=='f4a049d869e00fb089395bf8e4dfb1eee0d892406f707fbf18cf39091f5cbfd5'
 assert cs['sha256']=='b00a133cc88ed37496e225a181898863ce52e9a774e6b5c2991a310691fd4312'
 assert any(x['sha256']==cs['sha256'] for x in m['material_source_bindings'])
 op=HOST/'operations-book50-source70-full-current-final';assert not op.exists()
 for n in ['archive_batch.py','prepare_operation.py']:shutil.copyfile(B/n,HOST/n)
 integrator=C/'integrate_verified_batch-book61-isolated-single-delta-transport.py'
 assert spec(integrator)['sha256']=='e44686bf2d238e96c1aad08f522b927de8c29955e196d61277a6e28a5fed9400'
 env={**os.environ,'PYTHONPATH':str(B),'PYTHONDONTWRITEBYTECODE':'1','TMPDIR':str(HOST)}
 cmd=[sys.executable,HOST/'prepare_operation.py','--work-dir',op,'--batch','2026-11-15-书50原70实际正常18帧新定稿及真实源文档公开许可',
  '--asset-branch','codex/book50-source70-full-current-final-records-v1','--previous-inventory',prior,'--article-work-dir',W]
 for p in [B/'latest_final_directory_policy.py',B/'latest_request_tracking.py',B/'integrate_verified_batch.py',integrator,B/'video_order_authorization.py',
  B/'video_title_authorization.py',B/'exact_known_final_authorities17.py',B/'EXACT17-READONLY-AUTHORITY-PINS.json',user,consent,
  B/'prepare_actual_source70_book50_host_assets.py',
  B/'book50-source70-full-current-intake-20261115/ACTUAL-SOLE-WRITER-BOOK56-ALL-SPEC-AND-FIVE-CURRENT-FRAME-ADOPTION.json',
  Path('/workspace/work/source70-book50-standalone-public-master-collector-IO-CODE-ONLY-20261115/INDEPENDENT-SOLE-WRITER-EXACT70-MASTER-COLLECTOR-IO-ADOPTION.json'),
  Path(__file__),*[Path(x)for x in loc['transport_source_records']]]:cmd+=['--attach',p]
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
  'previous_inventory':str(prior),'operation_work_dir':str(op),'article_work_dirs':[str(W)],'latest_request_authorities':{'70':us},
  'result_count':68,'source_run':m['source_run'],'latest_requests_local_path':str(C/'latest_requests.json'),
  'message':'书50原70实际完整源与4K定稿双仓保存，按真实新许可公开源文档，首次正式合格入库并同步唯一最新目录 [skip ci]'}
 pp=C/'integration-plan-book50-source70-full-final.json';save(pp,plan)
 subprocess.run([sys.executable,str(integrator),'--plan',str(pp),'--execute'],check=True,env=env)
 after=load(C/'CURRENT-ARCHIVE-STATE.json');inv=load(after['actual_inventory']);now={x['source_id']:x for x in inv['articles']}
 assert len(now)==68 and all(now[x['source_id']]==x for x in before['articles'])
 assert 'previous_versions'not in now['70'] and now['70']['sha256']==row['sha256']
 assert inv['latest_final_directory_policy']==before['latest_final_directory_policy'] and inv['video_order_overlay']==before['video_order_overlay']
 reg=load(C/'latest_requests.json');en=next(x for x in reg['articles'] if x['source_id']=='70')
 assert en['latest_requested_revision_complete'] is True and en['latest_revision_final']['sha256']==row['sha256']
 assert reg['latest_requested_revision_completed_count']==63 and after['final_directory']['video_count']==63
 assert reg['video_work_priority_policy']==priority and all(x==y for x,y in zip(baseline['articles'],reg['articles']) if x['source_id']!='70')
 alias='50 一枚邮票改变通信.mp4';canonical_streams=[]
 for role,repo,branch,key in repos:
  head=after[key];assert api(repo,'git/ref/heads/'+branch)['object']['sha']==head
  tree={x['path']:x for x in api(repo,'git/trees/'+after['final_directory']['video_tree_sha'])['tree']}
  assert set(tree)-set(old_alias_trees[role])=={alias} and set(old_alias_trees[role])<=set(tree)
  assert all(tree[n]==v for n,v in old_alias_trees[role].items())
  path='视频修订定稿/最终定稿/视频/'+alias
  url='https://raw.githubusercontent.com/'+repo+'/'+head+'/'+urllib.parse.quote(path,safe='/')
  hasher=hashlib.sha256();n=0
  with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'source70-current-latest-alias-full-byte-readback'}),timeout=120) as response:
   assert response.status==200
   for b in iter(lambda:response.read(1024*1024),b''):n+=len(b);hasher.update(b)
  assert n==row['bytes'] and hasher.hexdigest()==row['sha256']
  canonical_streams.append({'repository':repo,'commit':head,'alias_path':path,'bytes':n,'sha256':hasher.hexdigest(),'http_status':200,'immutable_URL':url})
 out={'kind':'actual-book50-source70-full-current-final-after-real-user-source-publication-consent',
  'primary_main':after['primary_main'],'backup_delivery':after['backup_head'],'archived_passed_count':68,
  'actual_latest_directory_count':63,'latest_user_request_completed_count':63,'source_id':'70','book_order':'50',
  'final_bytes':row['bytes'],'final_sha256':row['sha256'],'actual_handoff_sha256':loc['handoff_sha256'],
  'source_publication_consent_sha256':cs['sha256'],'quality_H_unchanged_and_actual_b00_publication_consent_bound':True,
  'only_source70_first_accepted_row_added_other67_exact':True,'no_fabricated_old_accepted_row_or_previous_versions':True,
  'only_source70_latest_request_complete_other69_rows_equal':True,'other62_MP4_alias_nodes_exact_one_new50_alias':True,
  'all_other7_pending_articles_not_promoted':True,
  'all_other_pending_targets_remain_according_to_actual_registry_not_assumed_done':True,
  'actual_b00_authority_and_full_H_source_GEN_MD_QA_actually_dual_archived':True,
  'no_private_RAW_GT_cache_models_tokens_signedURL_ROOTSTATE_PDF_or_unrelated_source_uploaded':True,
  '090_146_153_history_and_PDF_master_other_roots_preserved':True,'no_new_Release':True,
  'full_READY':str(HOST/'ready-book50-source70-full.json'),
  'actual_asset_blob_rows':2*loc['files'],'actual_asset_MP4_streams':2,'actual_canonical_alias_streams':canonical_streams,
  'operation_full_raw_readbacks':operation_readbacks,'archive_receipt':after['last_completed_receipt']}
 cp=C/'actual-book50-source70-full-current-final-closure.json';save(cp,out)
 print(json.dumps({'closure':str(cp),'closure_SHA256':spec(cp)['sha256'],'primary':after['primary_main'],
  'backup':after['backup_head'],'archive':68,'latest':63,'complete':63},ensure_ascii=False),flush=True)
if __name__=='__main__':main()
