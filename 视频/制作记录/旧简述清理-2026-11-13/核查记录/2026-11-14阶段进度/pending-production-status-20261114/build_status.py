#!/usr/bin/env python3
"""Read current source/evidence only. Writes this local status index, never source or GitHub."""
from pathlib import Path
import csv,datetime,hashlib,json
R=Path('/workspace/work/video-audit70-20261113');PAY=R/'payload';B=Path('/workspace/work/video-revision-delivery');CI=Path('/workspace/work/video-revision-batch-ci');OUT=Path(__file__).resolve().parent
H=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
L=lambda p:json.loads(Path(p).read_text())
def spec(p):
 p=Path(p);assert p.is_file(),p
 return {'path':str(p),'sha256':H(p),'bytes':p.stat().st_size}
base=L(R/'current70-final-preflight.json');baseline={r['id']:r for r in base['articles']};order=L(R/'publication-order-manifest-readonly.json');mapping={r['source_id']:r for r in order['articles']}
book=L('/workspace/work/punk-print-20261113-v3/book-illustrations70.json');assert {r['source_id']:r['new_id']for r in book['illustrations']}=={n:r['new_id']for n,r in mapping.items()}
assert len(mapping)==70 and {x['new_id']for x in mapping.values()}=={f'{i:02}'for i in range(1,71)}
reserved=set('10 11 12 25 26 27 29 31 34 35 38 39 40 42 43 45 47 50 51 52 53 56 58 64'.split());hold_a21=set('15 17 18 30'.split());hold=hold_a21|{'07'}
ready=sorted(set(mapping)-reserved-hold);pending=sorted(set(mapping)-reserved);assert len(reserved)==24 and len(ready)==41 and len(pending)==46
handoffs={}
for directory in (B/'actual53-64-validation',B/'next-passed-validated',B/'recovered-canonical-validated'):
 for p in directory.rglob('archive-handoff.json'):
  d=L(p)
  for a in d.get('articles',[]):
   if a.get('passed_per_article'):
    assert a['source_id']in reserved and a['new_id']==mapping[a['source_id']]['new_id']
    handoffs[a['source_id']]={'handoff':spec(p),'source_run':d.get('source_run'),'actual_final':a['final_mp4'],'record':a['validated_record'],'outer_job_failure_preserved':d.get('original_outer_job_preserved_as_failed',False)}
delta={}
for fn in ('A21-specific-repair-text-preflight/report.json','44-raw-clock-text-preflight/report.json','pending-production-status-20261114/article03-current-MD-gate/report.json'):
 p=R/fn;d=L(p);assert d['status']=='passed'
 for a in d['articles']:delta[a['article']]=(p,a)
roots=[PAY,Path('/workspace/work/github-publication/target'),Path('/workspace/work/audit-repo')]
def manuscript(n):
 own=sorted((PAY/'新版定稿').glob(n+'-*.md'))
 if own:assert len(own)==1;return own[0]
 expected=baseline[n]['current_manuscript_sha256']
 for root in roots[1:]:
  for p in sorted((root/'新版定稿').glob(n+'-*.md')):
   if H(p)==expected:return p
 for p in R.glob('*/mirror/新版定稿/'+n+'-*.md'):
  if H(p)==expected:return p
 raise ValueError('No immutable current manuscript found '+n)
rows=[];binding_errors=[]
for n in sorted(mapping):
 m=mapping[n];source=PAY/f'视频/脚本/{n}.json';gen=PAY/f'视频/工具/初稿生成/gen{n}.py';md=manuscript(n);src=spec(source);gs=spec(gen);ms=spec(md);before=baseline[n]
 bgen=src['sha256']==before['current_source_sha256']and gs['sha256']==before['current_actual_generator_sha256']and ms['sha256']==before['current_manuscript_sha256']
 ev={'baseline_all70_report':spec(R/'current70-final-preflight.json'),'baseline_original_text_gate_report':spec(R/before['full_original_text_gate_report']),'baseline_current_source_sha256':before['current_source_sha256'],'baseline_current_generator_sha256':before['current_actual_generator_sha256'],'baseline_current_manuscript_sha256':before['current_manuscript_sha256']}
 if n in delta:
  p,a=delta[n];exact=(src['sha256']==a['source_sha256']and gs['sha256']==a['new_generator_sha256']and ms['sha256']==a['manuscript_sha256']and a['generator_roundtrip_exact']is True and a['text_gate_exit_code']==0 and not a['text_hard_errors']and not a['text_pending_confirmations'])
  ev.update(current_evidence=spec(p),current_original_text_gate_log=spec(a['text_gate_log']),current_generator_whole_JSON_exact=a['generator_roundtrip_exact'],current_original_text_gate_exit=a['text_gate_exit_code'],bound_to_current_all_three_source_files=exact,method='actual current delta GEN/fullJSON and original text gate')
 elif bgen:
  exact=before['actual_existing_generator_whole_JSON_exact']is True and before['text_gate_exit']==0 and not before['hard_errors']and not before['pending_confirmations']
  ev.update(bound_to_current_all_three_source_files=exact,current_generator_whole_JSON_exact=before['actual_existing_generator_whole_JSON_exact'],current_original_text_gate_exit=before['text_gate_exit'],method='all three current file hashes exactly equal actual all70 gate snapshot; no redundant rerun')
 else:
  exact=False;ev.update(bound_to_current_all_three_source_files=False,method='already accepted source lineage changed by separately reviewed canonical backflow or prior audio source delta; excluded from production list',source_backflow_plan=spec(R/'canonical-final-source-backflow-plan-20261114/backflow-plan.json'))
 if n not in reserved and not exact:binding_errors.append(n)
 if n in handoffs:state='actual_V3_passed_exclude_from_new_production'
 elif n in reserved:state='genuine_upstream_quality_passed_local_missing_art_recovery_reserved_do_not_rerender'
 elif n=='07':state='pending_program_repair_preserve_reviewed_ending_points'
 elif n in hold_a21:state='pending_A21_audio_QA_integration_do_not_launch_yet'
 else:state='ready_for_formal_production_not_final_quality_acceptance'
 flags=[]
 if n=='44':flags.append('latest exact raw-clock specific confirmation source87f531...; dedicated acoustic QC still required on actual new output')
 if n in {'06','54','57','67'}:flags.append('same-job reviewed scalar preparation must run; no claim of new actual sound acceptance')
 if n in {'46','49','55'}:flags.append('actual two-route new transcription needed; preserve same AAC, do not fabricate old confirmations')
 if n in {'32','33','37','41','60','62'}:flags.append('previous safe20 original post-QC selftest failed; requires actual fresh fixed-core whole quality pass, never reuse failed candidate')
 if n in {'65','69'}:flags.append('prior old-run AAC drift diagnostic; actual new original sound comparison remains strict')
 if n=='68':flags.append('prior old-run source fingerprint gap; new actual collector and immutable source fingerprints required')
 rows.append({'source_id':n,'book_new_id':m['new_id'],'title_zh':m['title_zh'],'title_en':m['title_en'],'book_order_video_path':'顺序重排版/'+m['video'],'state':state,'exclude_from_new_production':n in reserved,'formal_production_ready':n in ready,'source_json':src,'generator':gs,'manuscript':ms,'source_gate_evidence':ev,'actual_accepted_handoff':handoffs.get(n),'production_notes':flags})
assert not binding_errors,binding_errors
context=CI/'.github/video-revision-batch/context/manifest.json';ctx=L(context);context_diffs=[]
for rel,old in ctx['files_sha256'].items():
 p=PAY/rel
 if p.is_file()and H(p)!=old:context_diffs.append({'path':rel,'old_context_sha256':old,'current_PAY_sha256':H(p)})
cert=CI/'.github/video-revision-batch/certified-core';cm=L(cert/'manifest.json');core=[]
for r in cm['core_files']:
 p=cert/r['file'];assert H(p)==r['patched_sha256'];core.append({'target':r['target'],**spec(p),'original_sha256':r['original_sha256'],'certified_patched_sha256':r['patched_sha256']})
runner_files=['.github/video-revision-batch/run.py','.github/video-revision-batch/approved_illustration_resource.py','.github/video-revision-batch/approved-illustration-source70.json','.github/workflows/produce-revision-batch4K.yml']
runner={name:spec(CI/name)for name in runner_files}
result={'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'Read-only all70 current state and exact next formal production candidates; no workflow dispatch, no remote/source mutation','status':'pending_production_index_ready','required_articles':70,'excluded_from_new_production_count':24,'excluded_original_ids':sorted(reserved),'actually_completed_V3_handoff_count_at_this_snapshot':len(handoffs),'actually_completed_V3_source_ids_at_this_snapshot':sorted(handoffs),'genuine_passed_upstream_reserved_recovery_without_completed_handoff_at_snapshot':sorted(reserved-set(handoffs)),'remaining_formal_production_count':46,'pending_source_ids':pending,'ready_to_launch_count':41,'ready_to_launch_source_ids':ready,'ready_source_ids_in_book_order':[r['source_id']for r in sorted(rows,key=lambda r:int(r['book_new_id']))if r['formal_production_ready']],'held_source_ids':sorted(hold),'held_program_repair':['07'],'held_A21_audio_QA':sorted(hold_a21),'all_pending46_current_JSON_GEN_MD_files_bound_to_existing_actual_original_text_pass':True,'new_output_quality_pass_claimed':False,'frozen_book_order_manifest':spec(R/'publication-order-manifest-readonly.json'),'book_illustration_mapping_matches_exact_source_to_new_id':True,'production_owner_coordination':{'agent':'/root/resume_audio_ci','latest_local_candidate':str(CI),'launch_commit_not_yet_frozen_at_index_creation':True,'certified_core_handoff':spec(cert/'actual-native-handoff.json'),'actual_original_full_core_fastcheck_passed':L(cert/'actual-native-handoff.json')['passed_program_full_quickcheck'],'article_quality_acceptance_not_implied_by_program_certification':True,'core_files':core,'current_runner_working_files_observed':runner,'approved_image_resource_actual_validation':spec(R/'first3core7-failure-triage/image-resource-fix-validation.json'),'current_context_manifest':spec(context),'current_context_diff_from_latest_PAY':context_diffs,'context_refresh_policy':'audio_ci confirmed start.py rebuilds entire latest70 JSON+MD context/manifest140 from PAY priority and immutable unchanged MD fallbacks at each launch; current old context is not a launch freeze','ASR_route46_49_55':'audio_ci will freeze actual two-route transcription collector before launch; no automatic reused confirmation','scalar06_54_57_67':'same-job safe original scalar preparation already hooked; final actual quality still required','A21_four':'specific source/GEN/text passed, audio-a21-QA helper/reference exists but formal hook/raw clocks and30 original-level cache integration pending; excluded','07':'reviewed ending point preservation program repair pending; excluded'},'articles':rows,'workflow_dispatched':False,'remote_written':False,'PAY_source_or_generator_written':False}
(OUT/'pending70-status.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
(OUT/'ready41-source-ids.txt').write_text(','.join(ready)+'\n')
(OUT/'pending46-source-ids.txt').write_text(','.join(pending)+'\n')
with(OUT/'pending70-status.csv').open('w',newline='')as f:
 w=csv.DictWriter(f,fieldnames=['source_id','book_new_id','title_zh','state','formal_production_ready','exclude_from_new_production','source_json_sha256','generator_sha256','manuscript_sha256','text_gate_evidence']);w.writeheader()
 for r in sorted(rows,key=lambda r:int(r['book_new_id'])):w.writerow({**{k:r[k]for k in('source_id','book_new_id','title_zh','state','formal_production_ready','exclude_from_new_production')},'source_json_sha256':r['source_json']['sha256'],'generator_sha256':r['generator']['sha256'],'manuscript_sha256':r['manuscript']['sha256'],'text_gate_evidence':r['source_gate_evidence'].get('current_evidence',r['source_gate_evidence']['baseline_all70_report'])['path']})
print(json.dumps({'path':str(OUT/'pending70-status.json'),'sha256':H(OUT/'pending70-status.json'),'counts':{'excluded_no_rerender':24,'true_V3_handoffs':len(handoffs),'pending':46,'ready':41,'held':5},'ready41':ready,'current_pending_source_gate_binding_errors':binding_errors},ensure_ascii=False))
