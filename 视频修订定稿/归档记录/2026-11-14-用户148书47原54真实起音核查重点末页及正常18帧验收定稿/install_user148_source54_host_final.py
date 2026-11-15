"""Admit first accepted final54 under148; retain prior102 review as honest history."""
from pathlib import Path
import hashlib,json,subprocess,sys,os,shutil
B=Path(__file__).parent; C=Path('/dev/shm/archive-writer-main061')
def load(p): return json.loads(Path(p).read_text())
def save(p,x): Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def spec(p): return {'path':str(p),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
def main():
 state=load(C/'CURRENT-ARCHIVE-STATE.json'); prior=Path(state['actual_inventory']); before=load(prior)
 assert before['archived_passed_count']==62 and not any(x['source_id']=='54'for x in before['articles'])
 for repo,branch,key in [('alienalgorithm/postgraduate-vocabulary','main','primary_main'),('AlienCodes/literate-enigma','codex/all-deliverables-20261113','backup_head')]:
  actual=subprocess.check_output(['gh','api',f'repos/{repo}/git/ref/heads/{branch}','--jq','.object.sha'],text=True).strip(); assert actual==state[key]
 baseline=load(C/'latest_requests.json'); priority=baseline['video_work_priority_policy']
 assert priority['authority_review_sha256']=='f7414c06d76c99938a42e6c757e0c4235814874df345e069a3bbc646e1ea42fe' and priority['finalization_priority_video_order_max']==47
 entry=next(x for x in baseline['articles']if x['source_id']=='54'); assert entry['latest_finalization_authority']=='148' and entry['newest_user_revision_records']==['147','148'] and entry['final_4K_generation_authorized']is True
 loc=load(C/'active-source54-user148-asset-staging-location.json'); HOST=Path(loc['root']); W=Path(loc['work_dir']); m=load(W/'prepared-archive.json'); row=m['articles'][0]; ready=load(HOST/'ready-user148-source54.json')
 assert ready['asset_commit']==load(W/'assets-primary.json')['asset_commit']
 assert row['bytes']==22100097 and row['sha256']=='dffa42ac5cc04d93a52a414a371d278037568f0485a3814f2f09cba86edf2fe2'
 assert row['source_native_audio_repair_applied']is False and row['local_tail_postprocessing_audio_repair_applied']is False
 assert row['previous_qualified_review_versions'][0]['sha256']=='6223bf386aa819bf66117705fffc9afa07bf83909a8a3dd14758b3be5ba7e19c'
 assert load(W/'actual-dual-asset-blob-verification.json')['actual_dual_blob_rows']==2*loc['files'] and load(W/'remote-video-byte-verification.json')['passed']is True
 user=Path('/dev/shm/archive-writer-user-review-20261114/USER-REVIEW-2026-11-14-148.json'); us=spec(user)
 assert us['sha256']=='b1686faffc1516df0fde3dbb0fc4d0c61f0dfa74c6c76f3d40a9257f3299930d'
 op=HOST/'operations-user148-source54-current-final'; assert not op.exists()
 for n in ['archive_batch.py','prepare_operation.py']: shutil.copyfile(B/n,HOST/n)
 shutil.copyfile(B/'integrate_verified_batch.py',C/'integrate_verified_batch.py')
 env={**os.environ,'PYTHONPATH':str(B),'PYTHONDONTWRITEBYTECODE':'1','TMPDIR':str(HOST)}
 cmd=[sys.executable,HOST/'prepare_operation.py','--work-dir',op,'--batch','2026-11-14-用户148书47原54真实起音核查重点末页及正常18帧验收定稿','--asset-branch','codex/user148-source54-current-final-records','--previous-inventory',prior,'--article-work-dir',W]
 for p in [B/'latest_final_directory_policy.py',B/'latest_request_tracking.py',B/'integrate_verified_batch.py',B/'video_order_authorization.py',B/'video_title_authorization.py',B/'prepare_actual_source54_user148_host_assets.py',B/'transport_source54_user148_host_assets.py',HOST/'actual-source54-unique-Git-disk-budget-before-transport.json',user,Path(__file__)]: cmd+=['--attach',p]
 subprocess.run(list(map(str,cmd)),check=True,env=env)
 for repo in ['alienalgorithm/postgraduate-vocabulary','AlienCodes/literate-enigma']:
  subprocess.run([sys.executable,str(HOST/'archive_batch.py'),'push','--work-dir',str(op),'--repo',repo],check=True,timeout=85,env=env)
 plan={'writer_window_granted_by_root':True,'expected_heads':{'primary':state['primary_main'],'backup':state['backup_head']},'previous_inventory':str(prior),'operation_work_dir':str(op),'article_work_dirs':[str(W)],'result_count':63,'source_run':m['source_run'],'latest_requests_local_path':str(C/'latest_requests.json'),'latest_request_authorities':{'54':us},'message':'用户148书47真实全门验收新定稿双云保存，保旧审核历史并原子同步最新目录及请求，保153暂停范围 [skip ci]'}
 pp=C/'integration-plan-user148-source54-final.json'; save(pp,plan)
 subprocess.run([sys.executable,str(C/'integrate_verified_batch.py'),'--plan',str(pp),'--execute'],check=True,env=env)
 after=load(C/'CURRENT-ARCHIVE-STATE.json'); inv=load(after['actual_inventory']); now={x['source_id']:x for x in inv['articles']}; reg=load(C/'latest_requests.json')
 assert len(now)==63 and all(now[x['source_id']]==x for x in before['articles'])
 assert inv['latest_final_directory_policy']==before['latest_final_directory_policy'] and inv['video_order_overlay']==before['video_order_overlay']
 assert reg['video_work_priority_policy']==priority and all(a==b for a,b in zip(baseline['articles'],reg['articles'])if a['source_id']!='54')
 e=next(x for x in reg['articles']if x['source_id']=='54'); assert e['latest_requested_revision_complete']is True and e['latest_revision_final']['sha256']==row['sha256']
 assert reg['latest_requested_revision_completed_count']==46 and after['final_directory']['video_count']==62
 assert next(x for x in reg['articles']if x['source_id']=='46')['latest_requested_revision_complete']is False
 out={'kind':'actual-user148-source54-first-accepted-final-cloud-only-under153','primary_main':after['primary_main'],'backup_delivery':after['backup_head'],'archived_passed_count':63,'actual_latest_directory_count':62,'latest_user_request_completed_count':46,'only_source54_passed_row_added_other62_exact':True,'old6223_review_kept_honestly_as_previous_qualified_review_not_old_accepted_final':True,'current7546_AAC_and_absolute_clock_preserved_exactly_tail_no_audio_repair':True,'original_ENOSPC_failure_and_actual_c366_execution_history_preserved':True,'true_source_GEN_MD_focus_and_actual_S6_inplaces_lastpage_art_summary_frames_inherited':True,'153_priority_090_order_146_selector_077_title_PDF_pause_preserved':True,'source48_book42_pending_and_source46_book48_collecting152_unchanged':True,'other69_request_rows_and_all49to70_aliases_unchanged':True,'079_cloud_only_no_single_Release_created_or_triggered':True,'PDF_master_and_other_root_trees_preserved':True,'ready_manifest':str(HOST/'ready-user148-source54.json'),'actual_handoff_sha256':loc['handoff_sha256'],'archive_receipt':after['last_completed_receipt']}
 save(C/'actual-user148-source54-current-final-closure.json',out); print(json.dumps(out,ensure_ascii=False),flush=True)
if __name__=='__main__': main()
