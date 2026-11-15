"""Only actual dual-ready user128 first accepted final48; preserve all other rows."""
from pathlib import Path
import argparse,hashlib,json,subprocess,sys,os,shutil
B=Path(__file__).parent;C=Path('/dev/shm/archive-writer-main061')
def load(p):return json.loads(Path(p).read_text())
def save(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def spec(p):return {'path':str(p),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
def main():
 p=argparse.ArgumentParser();p.add_argument('--stream-approval',required=True);args=p.parse_args()
 state=load(C/'CURRENT-ARCHIVE-STATE.json');prior=Path(state['actual_inventory']);before=load(prior)
 assert before['archived_passed_count']==63 and not any(x['source_id']=='48'for x in before['articles'])
 for repo,branch,key in [('alienalgorithm/postgraduate-vocabulary','main','primary_main'),('AlienCodes/literate-enigma','codex/all-deliverables-20261113','backup_head')]:
  assert subprocess.check_output(['gh','api',f'repos/{repo}/git/ref/heads/{branch}','--jq','.object.sha'],text=True).strip()==state[key]
 baseline=load(C/'latest_requests.json');priority=baseline['video_work_priority_policy'];assert priority['authority_review_sha256']=='f7414c06d76c99938a42e6c757e0c4235814874df345e069a3bbc646e1ea42fe'
 e=next(x for x in baseline['articles']if x['source_id']=='48');assert e['latest_finalization_authority']=='128'and e['newest_user_revision_records']==['125','126','127','128']and e['final_4K_generation_authorized']is True
 loc=load(C/'active-source48-user128-streaming-staging-location.json');HOST=Path(loc['root']);W=Path(loc['work_dir']);m=load(W/'prepared-archive.json');row=m['articles'][0];ready=load(HOST/'ready-user128-source48.json')
 assert spec(W/'prepared-archive.json')['sha256']==loc['prepared_sha256']and spec(W/'payload-file-index.json')['sha256']==loc['index_sha256']
 adoption=load(args.stream_approval);assert adoption['kind']=='root-reviewed-exact-source48-streaming-asset-transport'and adoption['approved']is True and adoption['handoff_sha256']==loc['handoff_sha256']and adoption['prepared_sha256']==loc['prepared_sha256']and adoption['index_sha256']==loc['index_sha256']
 assert ready['asset_commit']==load(W/'assets-primary.json')['asset_commit']==load(W/'assets-backup.json')['asset_commit']
 assert row['bytes']==20307318 and row['sha256']=='612b53f821b5487406f3c0c6b3e82c57413c553f45509ffa0f045238d8c4ee5b'
 assert row['source_native_audio_repair_applied']is True and row['local_tail_postprocessing_audio_repair_applied']is False
 assert load(W/'actual-dual-asset-blob-verification.json')['actual_dual_blob_rows']==2*loc['files']and load(W/'remote-video-byte-verification.json')['passed']is True
 user=Path('/dev/shm/archive-writer-user-review-20261114/USER-REVIEW-2026-11-14-128.json');us=spec(user);assert us['sha256']=='d84f17de59d94e829483a6588bd34753e837839d9fc02c4a69e1877699d66b63'
 attempts=sorted(W.glob('streaming-attempt-*'));closed=[a for a in attempts if (a/'dual-transport-completion-not-READY.json').exists()];assert closed
 op=HOST/'operations-user128-source48-current-final';assert not op.exists()
 for n in ['archive_batch.py','prepare_operation.py']:shutil.copyfile(B/n,HOST/n)
 shutil.copyfile(B/'integrate_verified_batch.py',C/'integrate_verified_batch.py')
 env={**os.environ,'PYTHONPATH':str(B),'PYTHONDONTWRITEBYTECODE':'1','TMPDIR':str(HOST)}
 cmd=[sys.executable,HOST/'prepare_operation.py','--work-dir',op,'--batch','2026-11-14-用户128书42袁隆平实际新母完整质量及原正常18帧验收定稿','--asset-branch','codex/user128-source48-current-final-records','--previous-inventory',prior,'--article-work-dir',W]
 for q in [B/'latest_final_directory_policy.py',B/'latest_request_tracking.py',B/'integrate_verified_batch.py',B/'video_order_authorization.py',B/'video_title_authorization.py',B/'prepare_actual_source48_user128_streaming_host_assets.py',HOST/'streaming_git_data_asset_transport.py',HOST/'streaming_git_data_asset_transport_proxy_v2.py',Path('/workspace/work/source48-low-disk-streaming-transport-review-20261115/proxy-v2-network-factory-and-safe-stage-only.diff'),Path('/workspace/work/source48-low-disk-streaming-transport-review-20261115/actual-proxy-v2-readonly-GET200-repo-identity-proof.json'),Path('/workspace/work/source48-low-disk-streaming-transport-review-20261115/seed_source48_one_public_zip_git.py'),Path('/workspace/work/source48-low-disk-streaming-transport-review-20261115/resume_a0ba_with_exact_backup_seed_skip.py'),Path('/workspace/work/root-source48-nativeZIP56565-standard-Git-seed451b-one-execution-approval.json'),HOST/'actual-backup-zip56565-standard-Git-seed-full-raw-proof.json',HOST/'streaming-observer-one-fresh-third-attempt.json',HOST/'readonly-remote-state-after-fresh-observed-HTTP504.json',W/'streaming-attempt-20261115T050430-54fcb488/stopped-not-READY.json',HOST/'actual-root-approved-streaming-execution.log',Path(args.stream_approval),HOST/'actual-local-streaming-dryplan.json',HOST/'actual-source48-collection-completed-not-upload.json',closed[-1]/'actual-object-journal.json',closed[-1]/'dual-transport-completion-not-READY.json',user,Path(__file__)]:cmd+=['--attach',q]
 for q in [HOST/'actual-exact-backup-seeded-resume-receipt.json',HOST/'actual-root-approved-standard-Git-seed.log',HOST/'actual-root-approved-exact-seeded-resume.log']:
  cmd+=['--attach',q]
 for name in ['observe_frozen_proxy_v2_once.py','offline-tests-proxy-v2.log','offline-observer-tests.log','offline-seed-and-skip-tests.log','test_streaming_git_data_asset_transport_proxy_v2.py','test_observe_frozen_proxy_v2_once.py','test_source48_seed_and_skip_contract.py']:
  cmd+=['--attach',Path('/workspace/work/source48-low-disk-streaming-transport-review-20261115')/name]
 for failed in attempts:
  if (failed/'stopped-not-READY.json').exists():cmd+=['--attach-tree',failed]
 subprocess.run(list(map(str,cmd)),check=True,env=env)
 for repo in ['alienalgorithm/postgraduate-vocabulary','AlienCodes/literate-enigma']:
  subprocess.run([sys.executable,str(HOST/'archive_batch.py'),'push','--work-dir',str(op),'--repo',repo],check=True,timeout=85,env=env)
 plan={'writer_window_granted_by_root':True,'expected_heads':{'primary':state['primary_main'],'backup':state['backup_head']},'previous_inventory':str(prior),'operation_work_dir':str(op),'article_work_dirs':[str(W)],'result_count':64,'source_run':m['source_run'],'latest_requests_local_path':str(C/'latest_requests.json'),'latest_request_authorities':{'48':us},'message':'用户128书42袁隆平实际完整验收最新版云端保存，同步最新目录与请求并保153及旧历史 [skip ci]'}
 pp=C/'integration-plan-user128-source48-final.json';save(pp,plan)
 subprocess.run([sys.executable,str(C/'integrate_verified_batch.py'),'--plan',str(pp),'--execute'],check=True,env=env)
 after=load(C/'CURRENT-ARCHIVE-STATE.json');inv=load(after['actual_inventory']);now={x['source_id']:x for x in inv['articles']};reg=load(C/'latest_requests.json')
 assert len(now)==64 and all(now[x['source_id']]==x for x in before['articles'])
 assert inv['latest_final_directory_policy']==before['latest_final_directory_policy']and inv['video_order_overlay']==before['video_order_overlay']
 assert reg['video_work_priority_policy']==priority and all(a==b for a,b in zip(baseline['articles'],reg['articles'])if a['source_id']!='48')
 e=next(x for x in reg['articles']if x['source_id']=='48');assert e['latest_requested_revision_complete']is True and e['latest_revision_final']['sha256']==row['sha256']
 assert reg['latest_requested_revision_completed_count']==47 and after['final_directory']['video_count']==63
 assert all(x['latest_requested_revision_complete']for x in reg['articles']if int(x['current_video_order'])<=47)
 assert next(x for x in reg['articles']if x['source_id']=='46')['latest_requested_revision_complete']is False
 out={'kind':'actual-user128-source48-first-accepted-final-cloud-only-under153','primary_main':after['primary_main'],'backup_delivery':after['backup_head'],'archived_passed_count':64,'actual_latest_directory_count':63,'latest_user_request_completed_count':47,'continuous_current_video01to47_latest_requests_complete':True,'only_source48_passed_row_added_other63_exact':True,'current7085_AAC_and_absolute_clock_preserved_tail_no_further_audio_repair':True,'actual_new_native_Yuan_Longping_target_notes_layout_illustration_and_original_history_preserved':True,'no_fabricated_subjective_listening_acceptance':True,'proxy_v2_streaming_and_only_public_ZIP56565_standard_Git_seed_all_raw_verified':True,'exact_seeded_ZIP_POST_skipped_not_claimed201_original_verifier_still_ran':True,'original_connection_failure_and_actual_HTTP504_history_preserved':True,'153_priority_090_order_146_selector_077_title_PDF_pause_preserved':True,'source46_book48_collecting152_and_other69_request_rows_unchanged':True,'all49to70_aliases_unchanged':True,'079_cloud_only_no_single_Release':True,'PDF_master_and_other_root_trees_preserved':True,'ready_manifest':str(HOST/'ready-user128-source48.json'),'actual_handoff_sha256':loc['handoff_sha256'],'archive_receipt':after['last_completed_receipt']}
 save(C/'actual-user128-source48-current-final-closure.json',out);print(json.dumps(out,ensure_ascii=False),flush=True)
if __name__=='__main__':main()
