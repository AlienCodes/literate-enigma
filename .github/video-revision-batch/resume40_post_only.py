#!/usr/bin/env python3
"""Execute only actual failed40's remaining original outer checks in a NEW native job.

No original draft/final/TTS/body generator is invoked. This produces a private
quality-completed original outer result; sole CI still must run authorized144
hold18 and independent full V3 before an actual final delivery is accepted.
"""
import argparse,ast,copy,json,os,shutil,sys,time
from pathlib import Path
from resume40_contract import *

def complete(a):
 require(os.environ.get('GITHUB_ACTIONS')=='true'and os.environ.get('GITHUB_RUN_ID','').isdigit()and int(os.environ['GITHUB_RUN_ID'])!=43640848824,'Post-only completion must have its own genuine new native run')
 require(digest(a.reference)==REFERENCE_SHA256,'Exact frozen source40 reference file required')
 ref=load(a.reference);root=Path(a.repository).resolve();request=Path(a.request).resolve();cap=Path(a.capsule).resolve();program=Path(a.original_program).resolve();decision=Path(a.decision).resolve();task=root/'.github/video-revision-batch';m=Path(a.work).resolve();w=m/'video';out=Path(a.output).resolve();log=m/'article40-local-logs'
 require(not out.exists()or not any(out.iterdir()),'New completion output must be empty, never overwrite old failed output');out.mkdir(parents=True,exist_ok=True);w.mkdir(parents=True,exist_ok=True);log.mkdir(parents=True,exist_ok=True)
 old=load(cap/'files/40-status.json');reference=old['accepted_source'];accepted=root/reference['path'];verified=verify_inputs(cap,request,program,decision,ref,accepted_video=accepted,inspect_media=True);checked(task/'certified-core/manifest.json',ref['original_core_manifest'])
 # Preserve old false verdict and all public failed provenance byte-for-byte.
 for name in ['40-status.json','40-failed-draft-proof.json','40-failed-draft-fingerprint.json','40-failed-working-source.json']:
  shutil.copyfile(cap/'files'/name,out/('inherited-original-'+name))
 for rel in ref['request_files']:
  dest=root/rel;dest.parent.mkdir(parents=True,exist_ok=True)
  if dest.exists()and digest(dest)!=ref['request_files'][rel]:shutil.copyfile(dest,log/('pre-completion-workspace-'+dest.name))
  shutil.copyfile(request/rel,dest)
 (w/'scripts').mkdir(exist_ok=True);shutil.copyfile(cap/'files/40-failed-working-source.json',w/'scripts/40.json');shutil.copyfile(cap/'files/40-failed-draft.mp4',w/'40.mp4');shutil.copyfile(cap/'files/40-failed-draft-fingerprint.json',w/'40.mp4.指纹.json');shutil.copyfile(cap/'files/40-user-authorization.json',out/'40-user-authorization.json')
 status={k:copy.deepcopy(v)for k,v in old.items()if k not in {'passed','error','failed_current_video','check_summaries','reference_gain_failure_diagnostic','stage'}}
 status.update(article='40',passed=False,stage='post-only-completion-inputs-verified',postprocessing_only=True,new_TTS_or_original_body_render=False,new_native_full_original_pipeline_rerun=False,actual_new_native_post_only_completion=True,completion_native_run=int(os.environ['GITHUB_RUN_ID']),original_failed_native_run=43640848824,original_failed_native_HEAD=ref['source_native_HEAD'],original_failed_status_SHA256=ref['input_files']['40-status.json']['sha256'],original_run_and_false_status_preserved=True,inherited_original_check_summaries=old['check_summaries'],check_summaries={},inherited_original_voice_text_ASR_4K_gates_exit0=True,inherited_original_gate_control_flow_binding=verified,final_wav_sha256_origin='inherited actual original PCM proof + official fingerprint; not a newly materialized or measured WAV',original_current_PCM_recomputed=False,remaining_hold18_and_independent_fullV3_required=True,production_delivery_eligible=False,completion_entrypoint='resume40_post_only.py')
 env={**os.environ,'XG_P':str(root),'XG_TOOLS':str(root/'视频/工具'),'XG_WORK':str(w),'VIDEO_ROOT':str(m),'XG_NOPUSH':'1','STRICT_CACHE':'1'}
 ns=dict(ROOT=root,TASK=task,NO='40',M=m,W=w,T=root/'视频/工具',OUT=out,LOG=log,ENV=env,status=status,PRODUCTION_STARTED_NS=None,BASELINE_AUDIO_FILES=None)
 tree=ast.parse(program.read_text());imports=[n for n in tree.body if isinstance(n,(ast.Import,ast.ImportFrom))];defs=[n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))];constants=[n for n in tree.body if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id in {'ALLOWED','A21_AUDIO_REPAIRS','CONTROLLED_AUDIO_REPAIRS','APPROVED_AUDIO_REPAIRS'}for t in n.targets)]
 exec(compile(ast.Module(body=imports+constants+defs,type_ignores=[]),str(program)+'#unchanged-functions','exec'),ns)
 def no_original_pipeline(*args,**kwargs):raise RuntimeError('Original synthesis/draft/final rendering prohibited in post-only completion')
 ns['official']=no_original_pipeline
 original_predicate=ns['same_summary_content']
 def narrow_summary(expected,actual):
  return original_predicate(expected,actual)or exact_summary_pair('40',digest(request/'视频/脚本/40.json'),digest(request/'视频/工具/初稿生成/gen40.py'),digest(w/'scripts/40.json'),expected,actual,ref)
 ns['same_summary_content']=narrow_summary
 def inherited_pcm_sha():
  require(digest(w/'40.mp4')==ref['canonical_video_sha256']and digest(w/'40.mp4.指纹.json')==ref['official_fingerprint_sha256'],'Inherited PCM belongs to another canonical/fingerprint')
  return ref['expected_RAW_PCM_sha256']
 ns['inherited_pcm_sha']=inherited_pcm_sha
 ns.update(request=request,requested=load(request/'视频/脚本/40.json'),requested_summary=ref['request_summary'],source_video=accepted,reference=reference,accepted_aac=ref['expected_current_AAC_ADTS_sha256'],start_wav=None)
 try:
  # Original verifier executes now against the exact same certified tools; no
  # current source/audio gates are forged or represented as rerun.
  ns['install_certified_core_repairs']();env['XG_KEEP_REVIEWED_ENDING']='0';status['reviewed_existing_ending_preservation_mode']=False
  # Execute the exact original font/alias setup statements, without its cache,
  # waveform, draft, final-render or input-reset paths.
  original_body=next(n.body for n in tree.body if isinstance(n,ast.Try));font_start=next(i for i,n in enumerate(original_body)if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='fonts'for t in n.targets));font_end=next(i for i,n in enumerate(original_body[font_start:],font_start)if isinstance(n,ast.Expr)and isinstance(n.value,ast.Call)and isinstance(n.value.func,ast.Name)and n.value.func.id=='checked')
  exec(compile(ast.Module(body=original_body[font_start:font_end],type_ignores=[]),str(program)+'#unchanged-outer-font-alias-setup','exec'),ns)
  ns['checked'](['python3',ns['T']/'新管/印章.py'],'resume-original-stamp-before-outer.log',w)
  tail,bridge=prepare_tail(program.read_text());write(out/'40-original-outer-resume-AST-bridge.json',bridge);exec(compile(tail,str(program)+'#actual-post-only-suffix','exec'),ns)
  status.update(actual_new_native_remaining_original_outer_checks_passed=True,inherited_original_gates_not_rerun=True,private_intermediate_only=True,production_delivery_eligible=False,remaining_hold18_and_independent_fullV3_required=True);ns['save']()
  write(out/'40-post-only-native-completion-ready.json',dict(source_id='40',quality_book_order='46',actual_new_native_run=int(os.environ['GITHUB_RUN_ID']),original_failed_run=43640848824,original_remaining_outer_completed=True,original_gate_provenance_inherited_not_rerun=True,canonical_video_sha256=status['canonical_video_sha256'],current_AAC_SHA256=status['canonical_aac_adts_sha256'],new_private_source_QA_candidate_only=True,production_delivery_eligible=False,final_user_acceptance=False,remaining_hold18_and_fullV3_required=True))
 except Exception as e:
  status.update(passed=False,production_delivery_eligible=False,stage='post-only-completion-failed',error=str(e));ns['save']();raise

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('mode',choices=['verify-inputs','complete']);
 for key in ['reference','capsule','request','original-program','decision']:p.add_argument('--'+key,required=True)
 for key in ['repository','work','output','accepted-video']:p.add_argument('--'+key)
 a=p.parse_args()
 if a.mode=='verify-inputs':print(json.dumps(verify_inputs(a.capsule,a.request,a.original_program,a.decision,load(a.reference),accepted_video=a.accepted_video),ensure_ascii=False))
 else:
  require(all(getattr(a,k)for k in ['repository','work','output']),'Actual new native completion paths required');complete(a)
