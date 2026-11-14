"""Join actual final GitHub metadata and all63 public native statuses; no acceptance inference."""
from collections import Counter
import csv
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import re

HERE=Path(__file__).resolve().parent
BASE=HERE.parent
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
load=lambda p:json.loads(Path(p).read_text())
jobs=load(HERE/'jobs-final.json');artifacts=load(HERE/'artifacts-final.json')
job_by_id={re.fullmatch(r'produce \((\d{2})\)',r['name']).group(1):r for r in jobs['jobs'] if re.fullmatch(r'produce \((\d{2})\)',r['name'])}
artifact_by_id={re.fullmatch(r'article(\d{2})-revised-canonical-4K-final',r['name']).group(1):r for r in artifacts['artifacts']}
initial=load(HERE/'initial25-classification.json');new=load(HERE/'new36-classification.json')
failures=initial['articles']+new['articles']
assert len(failures)==61 and len({r['article'] for r in failures})==61
assert len(job_by_id)==len(artifact_by_id)==63
assert set(job_by_id)==set(artifact_by_id)
assert Counter(r['conclusion'] for r in job_by_id.values())=={'failure':61,'success':2}
assert all(r['status']=='completed' for r in job_by_id.values())

labels={
 'wrapper_summary_decoration':'仅▹包装器比较误报，可固定包装器后重新正式出片',
 'missing_reference_cache':'缺精确reference/cache；另有声音/自检等次因待解',
 'text_table_parser_data':'速查表/词性释义解析数据',
 'cross_article_context':'跨篇词汇上下文快照不一致',
 'audio_interval_data_invalid':'非人声区间数据非法',
 'reported_audio_quality_gates':'原生声音质量门未过，需实际复核',
 'independent_cut_review':'独立切边/删除复核未过',
 'audio_double_release':'原生双爆破门未过',
 'checker_selftest_failure':'检查器自检漏检；后续坏点计数不可当作可信实测',
 'machine_relisten_unresolved':'机器复听差异未解，需实际听音确认',
 'checker_runtime_failure':'检查器IndexError运行异常；无CPU归因证据',
 'highlight_timing_unresolved':'高亮实际同步/独立方法差异未解',
 'wrapper_summary_decoration_and_candidate_AAC_drift':'▹包装器问题且候选AAC漂移，禁止当作仅包装器安全重试',
 'post_finalize_source_fingerprint_evidence_gap':'4K后脚本指纹不匹配且缺实际候选proof/source',
 'passed_original_pipeline':'原生正式job通过；53/64后续真实插图定稿已另验',
}

for row in failures:
 no=row['article'];assert sha(row['native_status_path'])==row['native_status_sha256']
 status=load(row['native_status_path']);assert status['passed'] is False and job_by_id[no]['conclusion']=='failure'
 row['final_job']={k:job_by_id[no][k] for k in ('id','status','conclusion','name','html_url','started_at','completed_at')}
 row['final_artifact']={k:artifact_by_id[no][k] for k in ('id','name','size_in_bytes','digest')}
 row['primary_explanation_zh']=labels[row['primary_class']]
 row['evidence_retrieval_basis']='reused prior25 verified public native-status snapshot' if no in {r['article'] for r in initial['articles']} else 'this-pass connector ZIP download, exact GitHub digest and byte-count verified, JSON-only extraction, ZIP removed'

success_rows=[]
for no in ('53','64'):
 art=artifact_by_id[no]
 folder=BASE/'actual-passed-43523430839'/no
 archive=folder/f'article{no}-passed-output.zip'
 assert sha(archive)==art['digest'].removeprefix('sha256:') and archive.stat().st_size==art['size_in_bytes']
 status_path=folder/'files'/f'{no}-status.json';status=load(status_path)
 assert status['passed'] is True and status['stage']=='final4K-passed' and job_by_id[no]['conclusion']=='success'
 tail_path=folder/f'{no}-illustrated-tail-verification.json';tail=load(tail_path)
 assert tail['passed'] is True and tail['production_delivery_eligible'] is True
 success_rows.append({'article':no,'native_status_path':str(status_path),'native_status_sha256':sha(status_path),
   'native_status_passed':True,'stage':status['stage'],'primary_class':'passed_original_pipeline',
   'primary_explanation_zh':labels['passed_original_pipeline'],'secondary_classes':[],
   'diagnostics':[{'category':'passed_original_pipeline','native_diagnostic':'Actual native successful job/status and canonical AAC=accepted AAC verified; real art60+summary60 derivative also independently passed.'}],
   'wrapper_only_immediate_retry_after_fixed_strict_wrapper':False,'acceptance':True,
   'final_job':{k:job_by_id[no][k] for k in ('id','status','conclusion','name','html_url','started_at','completed_at')},
   'final_artifact':{k:art[k] for k in ('id','name','size_in_bytes','digest')},
   'existing_success_ZIP_SHA_reverified_now':True,'existing_success_evidence_preserved':True,
   'actual_native_final_video_sha256':status['video_sha256'],'illustrated_tail_report':str(tail_path),
   'illustrated_tail_report_sha256':sha(tail_path),'actual_illustrated_final_video_sha256':tail['video_sha256']})

rows=sorted(failures+success_rows,key=lambda r:r['article'])
assert len(rows)==63 and {r['article'] for r in rows}==set(job_by_id)
receipts=[load(p) for p in sorted((HERE/'public-evidence').glob('*/artifact-retrieval-receipt.json'))]
assert len(receipts)==36
assert all(r['zip_digest_verified'] and r['zip_removed_after_public_extraction'] for r in receipts)
assert all(not r['private_audio_GT_cache_or_media_extracted'] and not r['removed_private_fields'] for r in receipts)
assert not list((HERE/'temporary-downloads').iterdir())
retry=sorted(initial['fixed_wrapper_only_retry_ids']+new['fixed_wrapper_only_retry_ids'])
assert len(retry)==len(set(retry))==23
assert all(next(r for r in rows if r['article']==no)['wrapper_only_immediate_retry_after_fixed_strict_wrapper'] for no in retry)
assert not {'65','68','69'}&set(retry)
counts=Counter(r['primary_class'] for r in rows)
groups=[]
for key,count in counts.items():
 groups.append({'class':key,'explanation_zh':labels[key],'count':count,'articles':[r['article'] for r in rows if r['primary_class']==key]})
secondary=Counter(k for r in rows for k in r.get('secondary_classes',[]))
report={'kind':'all63-actual-final-native-failure-classification-not-new-quality-acceptance',
 'generated_utc':datetime.now(timezone.utc).isoformat(),'repository':'AlienCodes/literate-enigma',
 'producer_run_id':43523430839,'producer_source_commit':'1ec776c9c214ef668cab4c27b43780bc12c38c19',
 'all_final_metadata_fetched_now':True,'metadata':{'jobs':{'path':str(HERE/'jobs-final.json'),'sha256':sha(HERE/'jobs-final.json')},'artifacts':{'path':str(HERE/'artifacts-final.json'),'sha256':sha(HERE/'artifacts-final.json')}},
 'selected_article_count':63,'article_job_final_counts':{'failure':61,'success':2},
 'non_article_prepare_job_excluded':{'count':1,'conclusion':'success'},'unavailable_or_in_progress_article_count':0,
 'evidence_reuse':{'prior_verified_statuses':25,'new_failure_ZIPs_downloaded_and_GitHub_digest_verified':36,
  'successful_existing_ZIPs_rehashed_and_preserved':2,'all_new_temporary_ZIPs_removed':True,
  'new_failure_archive_bytes_streamed':sum(r['actual_zip_bytes'] for r in receipts),
  'new_public_JSON_bytes_retained':sum(f['bytes'] for r in receipts for f in r['public_files']),
  'raw_media_PCM_GT_cache_payload_retained':False,'only_public_status_proof_source_scalar_JSON_saved':True},
 'primary_counts':dict(counts),'primary_groups':groups,'secondary_counts':dict(secondary),
 'fixed_wrapper_only_retry_ids':retry,'new_wrapper_only_retry_ids_beyond_initial25':new['fixed_wrapper_only_retry_ids'],
 'wrapper_candidates_blocked_by_actual_candidate_AAC_drift':['65','69'],
 'post_finalize_source_fingerprint_evidence_gap_ids':['68'],
 'reference_CPU_or_timeout_failure_evidence_count':0,
 'no_CPU_root_cause_inferred_from_long_runtime_or_selftest_counts':True,
 'reproduction_rules':[
  'Retry means fresh unchanged original official 做+定稿 with the fixed strict wrapper; failed candidate MP4s are never deliverables.',
  'The23 wrapper-only rows prove original checks returned passed and candidate4K AAC matched accepted AAC; source/body/five summary points differ only by line-leading continuation decoration/whitespace.',
  '65/69 require independent actual AAC-drift resolution plus wrapper repair; neither is approved for wrapper-only batch.',
  'Do not interpret28/36/59/63/66/70 selftest-missed counts as trustworthy real audio defects;54/57/67 also have explicit IndexError.',
  'Missing references can coexist with unresolved audio/highlight/selftest findings; reference preparation alone does not prove quality.',
  'No source, official program, threshold or private PCM/GT/cache was modified or published in this audit.'
 ],'source_or_official_checks_modified':False,'failed_statuses_never_upgraded_to_passed':True,
 'detail_sources':[{'path':str(HERE/name),'sha256':sha(HERE/name)} for name in ('initial25-classification.json','new36-classification.json')],
 'articles':rows}
(HERE/'final63-classification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')

with (HERE/'final63-classification.csv').open('w',encoding='utf-8-sig',newline='') as stream:
 writer=csv.writer(stream);writer.writerow(['原篇号','原生job结果','主因','次因','原生失败阶段','可仅修包装器后正式重试','最短原诊断','status_SHA256','artifact_ID','GitHub_ZIP_SHA256'])
 for row in rows:
  diagnosis=(row.get('diagnostics') or [{}])[0].get('native_diagnostic','')
  writer.writerow([row['article'],row['final_job']['conclusion'],row['primary_explanation_zh'],';'.join(row.get('secondary_classes',[])),row.get('failure_step') or row.get('stage',''),row['wrapper_only_immediate_retry_after_fixed_strict_wrapper'],diagnosis,row['native_status_sha256'],row['final_artifact']['id'],row['final_artifact']['digest']])

retry_report={'run_id':43523430839,'quality_acceptance':False,'fresh_official_run_required':True,
 'fixed_wrapper_only_retry_ids':retry,'new20_beyond_already_reported26_27_29':new['fixed_wrapper_only_retry_ids'],
 'do_not_duplicate_current26_27_29_runs_without_root_coordination':True,
 'excluded_candidate_AAC_drift':['65','69'],'excluded_source_fingerprint_gap':['68'],
 'basis_report_sha256':sha(HERE/'final63-classification.json')}
(HERE/'fixed-wrapper-only-retry23.json').write_text(json.dumps(retry_report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'all63_final':True,'failed':61,'passed_native':2,'unavailable':0,'primary_counts':dict(counts),'fixed_wrapper_only_retry23':retry},ensure_ascii=False))
