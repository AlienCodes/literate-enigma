"""Concrete ROOTa430-bound original cachedwhole caller. Author never dispatches it."""
from pathlib import Path
import argparse,hashlib,importlib.util,json,os,re,subprocess,sys,traceback
sys.dont_write_bytecode=True
ROOT_SHA='a430159b2c827fcabcdf242f8407b33d546f1d5cfac336558b4537c90577efa4'
HELPER_SHA='c6e18e9f8a0d69f41e4f82c454b0fa2c927392941b80bec2e45d881a74696456'
PROFILE_SHA='04d11bb2099f0bd2ef2ddc9810fcccc332489f0379ad266c8c5e6cbac908682a'
SOURCE_SHA='dc3fec8cb898d8a7279739b6c4c62d38caf509580e26511acd95d07f1bbc18ef'
OLD_KEY='Linux-native56-exact-S11-first-spoken-comma-43721094194';OLD_VERSION='7368862e74747836adc191d99e433a5c870b2d184e3f9e387280fecd8c07432c'
NEW_KEY='Linux-native56-exact-S11-CMU2-Wallace-pronCTX-43759374449';NEW_VERSION='b7a003ff3df1f4b269f8c12708946abaaa05cb7df7047df9ea58b673f802f325'
MATH_KEY='Linux-native56-only-target-whole-original-math-43729197848';MATH_VERSION='e64dc6e131ead6fee8e56c8b20ae45b4234f00b5f4a12a556d02eaa69af30a6c'
PARENT_KIND='ROOT-DELEGATED-independent-source56-CMU2-onlyS11-original-cachedwhole-one-math-execution-adoption'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def require(x,msg):
 if not x:raise AssertionError(msg)
def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def cache_api_row(path,key,version):
 d=json.loads(Path(path).read_text());require(d['total_count']==len(d['actions_caches'])==1,'Unique actual cache API row required');r=d['actions_caches'][0]
 require(r['key']==key and r['version']==version and r['ref']=='refs/heads/codex/finish-05-and-summaries-20261112','Wrong actual key/version/ref; never normalize historical68 label');return r
def validate_root(path,literal,N):
 path=Path(path);N=Path(N);require(literal==ROOT_SHA and path.is_file() and not path.is_symlink() and sha(path)==ROOT_SHA and path.read_bytes()==(N/'root-CMU2-whole-execution-scope.json').read_bytes(),'Mandatory actual ROOTa430 SHA/copy before setup or HTTP')
 r=json.loads(path.read_text());require(r['finite_target_scope']['source']=='56' and r['finite_target_scope']['target']=='S11' and r['finite_target_scope']['new_context_SHA256']=='db04a700c9778e45db7c934ce0f4cf8f44349ff3a924599d4194aa90a363440f','Wrong actual ROOT source/context scope');return r
def validate_parent(path,literal,N):
 p=Path(path);N=Path(N);require(re.fullmatch('[0-9a-f]{64}',literal or '') and p.is_file() and not p.is_symlink() and sha(p)==literal,'Actual independent parent record fullSHA required')
 require(p.read_bytes()==(N/'actual-parent-CMU2-whole-review.json').read_bytes() and (N/'actual-parent-CMU2-whole-review.sha256').read_text().strip()==literal,'Parent copy/literal differs')
 v=json.loads(p.read_text());require(v['kind']==PARENT_KIND and v['root_scope']['sha256']==ROOT_SHA and v['program_SHA256']==HELPER_SHA and v['profile_SHA256']==PROFILE_SHA,'Actual parent must bind new exact ROOT/helper/profile')
 require(v['source_id']=='56' and v['target_sentence']=='S11' and v['sentence_count']==17 and v['independent_review_passed'] is True and v['allow_only_S11_one_original_math_if_missing'] is True and v['new_TTS_GT_ASR_or_native_finalization_authorized'] is False,'Parent scope incomplete');return v
def verify_transport(N):
 N=Path(N);rows=json.loads((N/'transport-file-pins.json').read_text());require(rows and len({r['relative'] for r in rows})==len(rows),'Finite unique transport pins required')
 for r in rows:
  rel=Path(r['relative']);require(not rel.is_absolute() and '..' not in rel.parts,'Transport path escaped');p=N/rel;require(p.is_file() and not p.is_symlink() and p.stat().st_size==r['bytes'] and sha(p)==r['sha256'],'Frozen program/input differs '+str(rel))
 require(sha(N/'observe56_CMU2_current_baseline_and_selected_whole.py')==HELPER_SHA and sha(N/'profile.json')==PROFILE_SHA,'Wrong whole helper/profile');return rows
def helper_argv(N,M,T,O):
 N,M,T,O=map(Path,(N,M,T,O));return [sys.executable,str(N/'observe56_CMU2_current_baseline_and_selected_whole.py'),'--tools',str(T),'--video-root',str(M),'--inputs',str(N),'--profile',str(N/'profile.json'),'--execution-adoption',str(N/'root-CMU2-whole-execution-scope.json'),'--execution-adoption-sha256',ROOT_SHA,'--output',str(O/'56-CMU2-baseline-and-selected-whole-scalar.json'),'--cache-path-output',str(O/'56-onlyS11-CMU2-private-math-step-output.txt')]
def verify_G27(N,T,W,profile):
 N,T,W=map(Path,(N,T,W));require(sha(T/'出片指纹.py')=='ef589d2ad0bc9e1806a37161c81e727b7f900d4de490d05d4c74755b392b91a9','Original actual G27 differs');g=load('_CMU2_caller_original_G27',T/'出片指纹.py');paths=g.清单([str(T)]);require(len(paths)==8 and set(paths)==set(profile['original_G27_expected']) and g.核对工作目录(str(W),str(T))==[],'Original eight work imports differ');rows={}
 for name,p in paths.items():
  q=g._找(name,g.工作目录搜(str(W)));require(q is not None and sha(q)==sha(p)==profile['original_G27_expected'][name],'Actual original module path/fullSHA differs '+name);rows[name]={'tools_path':str(Path(p).resolve()),'work_path':str(Path(q).resolve()),'sha256':sha(q)}
 return rows
def publish_verified_math_outputs(s,private,M,real,outer_restored):
 require(outer_restored is True and s.get('math_scope_integrity_proved') is True and s.get('forbidden_model_events')==[],'No SAVE without independent actual math scope and all outer restores')
 required={'all_inner_runtime_source_context_work_module_cache_restores','baseline_and_selected_native_endpoints_restored','declared_source_context_and_actual_mother_inputs_checked','both_actual_new_target_mothers_witnessed_before_math','one_original_S11_math_creator_and_strict_readback','no_forbidden_model_endpoint_events'}
 require(set(s.get('actual_math_scope_prerequisites',{}))==required and all(v is True for v in s['actual_math_scope_prerequisites'].values()),'Unknown or failed source/method/mother/math scope')
 guards=['all_original_local_modules_preexisting_objects_env_cwd_path_trace_restored','all_existing_private_cache_exact_only_one_actual_S11_math_added','public_cache_exact_after','all_runtime_model_voice_AF_G27_dict_context_stamp_bytes_exact_after','all_frozen_inputs_exact_after']
 require(all(s.get(k) is True for k in guards) and all(s.get('restoration',{}).get(k) is True for k in ['normal_scripts_namespace_restored','environment_cwd_sys_path_restored','normal_work_inode_and_PCM_restored','both_T_W_original_context_inode_and_bytes_restored','selected_context_payload_exact_at_exit']) and all(s.get('native_closure_restore_receipts',{}).get(k) is True for k in ['baseline','selected']),'Helper restoration failed; never expose SAVE')
 entries=s.get('actual_new_S11_original_math',{});private=Path(private)
 if not entries:require(not private.exists() or private.read_text()=='','Unexpected private output without actual new math');return False
 require(len(entries)==1 and s.get('math_save_integrity_proved') is True,'One actual verified S11 math only');name,item=next(iter(entries.items()));match=re.fullmatch(r'调平_([0-9a-f]{40})\.json',name)
 require(match is not None and item.get('source_id')=='56' and item.get('target_sentence')=='S11' and item.get('strict_readback_exact') is True and re.fullmatch('[0-9a-f]{64}',item.get('sha256','')),'Wrong actual single-S11 identity')
 rows=[r for r in s['phases']['selected']['original_G36_calls'] if r['sentence']=='S11'];require(len(rows)==1 and rows[0]['file']==name and rows[0]['original_key']==match.group(1) and rows[0]['actual_math_created'] is True and rows[0]['sha256']==item['sha256'],'Selected actual math role differs')
 M=Path(M).resolve();folder=M/'tts/source56-only-S11-CMU2-whole-original-math-cache';copy_path=folder/name;original=M/'tts/cache_tts'/name
 require(not folder.is_symlink() and all(p.is_file() and not p.is_symlink() for p in [copy_path,original]) and sha(copy_path)==sha(original)==item['sha256'] and json.loads(copy_path.read_text())==json.loads(original.read_text())==item['value'],'Actual math copy/cache regular bytes/value differ')
 runid=os.environ.get('GITHUB_RUN_ID','');require(runid.isdigit(),'Actual run ID required');key='Linux-native56-only-S11-CMU2-whole-original-math-'+runid;save=s.get('private_original_math_save',{})
 require(save.get('cache_key')==key and save.get('exact_paths')==[str(copy_path)] and save.get('files')==entries and save.get('save_success_not_claimed') is True,'Unknown private declaration')
 expected='cache_key='+key+'\ncache_paths<<ONLY_S11_CMU2_MATH_PATHS\n'+str(copy_path)+'\nONLY_S11_CMU2_MATH_PATHS\n';require(private.is_file() and not private.is_symlink() and private.read_text()==expected,'Private fields are not the exact known one math output');real=Path(real);require(real.resolve()!=private.resolve() and not real.resolve().is_relative_to(M),'Real step output must be isolated from private/cached machine')
 with real.open('a') as f:f.write(expected)
 return True
def main():
 p=argparse.ArgumentParser()
 for k in ['actual-root-execution-adoption','actual-parent-review-adoption']:p.add_argument('--'+k,type=Path,required=True);p.add_argument('--'+k+'-sha256',required=True)
 a=p.parse_args();N=Path(__file__).resolve().parent;validate_root(a.actual_root_execution_adoption,a.actual_root_execution_adoption_sha256,N);validate_parent(a.actual_parent_review_adoption,a.actual_parent_review_adoption_sha256,N);pins=verify_transport(N)
 ROOT=Path(os.environ['GITHUB_WORKSPACE']);M=Path(os.environ['RUNNER_TEMP'])/'completion-machine';W=M/'video';T=ROOT/'official-main/视频/工具';O=ROOT/'source56-CMU2-whole-public';require(not O.exists(),'Fresh scalar output directory required')
 require(all(os.environ.get(k)=='1' for k in ['AUDIO_ONLY','STRICT_CACHE','XG_NOPUSH','XG_KEEP_REVIEWED_GAIN','XG_KEEP_REVIEWED_ENDING','XG_KEEP_REVIEWED_CUTS']) and not any(os.environ.get(k) for k in ['VOICE','AFFILE','OLD_IV_VOID','ONLY','BREATH_FRAC','CACHE_LOG']),'No acoustic/voice override permitted')
 require(all(os.environ.get(k)=='true' for k in ['OLD_S11_MOTHER_CACHE_HIT','NEW_S11_CMU2_MOTHER_CACHE_HIT','OLD_S11_G36_CACHE_HIT']),'All exact existing private caches must hit')
 api={'old_mothers':cache_api_row(N/'actual-old-mother-cache-API.json',OLD_KEY,OLD_VERSION),'new_mothers':cache_api_row(N/'actual-new-mother-cache-API.json',NEW_KEY,NEW_VERSION),'old_G36':cache_api_row(N/'actual-existing-S11-G36-cache-API.json',MATH_KEY,MATH_VERSION)}
 profile=json.loads((N/'profile.json').read_text());C=M/'tts/cache_tts'
 for entries in profile['target_entries'].values():
  for e in entries.values():
   for name,h in [(e['name'],e['sha256']),(e['marker_name'],e['marker_sha256'])]:q=C/name;require(q.is_file() and not q.is_symlink() and sha(q)==h,'Actual old/new mother missing/wrong '+name)
 runid=os.environ.get('GITHUB_RUN_ID','');require(runid.isdigit(),'Actual run ID required');scratch=M/('_CMU2_whole_setup_'+runid);require(not scratch.exists(),'Fresh isolated setup required');scratch.mkdir();O.mkdir()
 report={'kind':'actual-ROOTa430-and-independent-parent-bound-CMU2-cachedwhole-setup','root_SHA256':ROOT_SHA,'actual_parent_review_SHA256':a.actual_parent_review_adoption_sha256,'helper_SHA256':HELPER_SHA,'profile_SHA256':PROFILE_SHA,'quality_acceptance':False,'restoration':{},'errors':[],'cache_API':api,'runtime_program_pin_count':len(pins)};status=1
 try:
  lib=load('_CMU2_setup_original_work_namespace',N/'inputs/original_whole_observer.py')
  with lib.work_namespace(W,scratch,report['restoration']):
   W.mkdir();subprocess.run([sys.executable,str(N/'install_actual_certified22_context.py')],check=True);sd=W/'scripts';sd.mkdir();source=sd/'56.json';source.write_bytes((N/'inputs/current_source.json').read_bytes());require(sha(source)==SOURCE_SHA,'Private same-byte source initialization differs')
   restore=load('_CMU2_existing_baseline_math_restore',N/'restore_exact_existing_S11_G36.py');report['actual_baseline_math_readback']=restore.restore_existing_original_math(M/'tts/source56-only-target-whole-original-math-cache'/restore.NAME,C/restore.NAME,os.environ['OLD_S11_G36_CACHE_HIT'])
   report['G27_before_helper']=verify_G27(N,T,W,profile);status=subprocess.run(helper_argv(N,M,T,O)).returncode;report['helper_exit']=status;report['G27_after_helper']=verify_G27(N,T,W,profile)
   s=json.loads((O/'56-CMU2-baseline-and-selected-whole-scalar.json').read_text());report['helper_measurement_completed']=s['measurement_completed'];report['helper_exact_scope_proved']=s['exact_scope_proved'];report['helper_math_scope_integrity_proved']=s.get('math_scope_integrity_proved') is True;report['helper_reported_whole_or_quality_errors']=s['errors']
   if not (s['measurement_completed'] is True and s['exact_scope_proved'] is True and s['errors']==[]):status=1
 except BaseException as e:report['errors'].append({'type':type(e).__name__,'detail':str(e)});traceback.print_exc();status=1
 finally:
  report['outer_original_video_inode_and_PCM_restored']=report['restoration'].get('normal_work_inode_and_PCM_restored') is True;report['caller_measurement_completed']=report.get('helper_measurement_completed') is True and report.get('helper_exact_scope_proved') is True and not report['errors'] and report['outer_original_video_inode_and_PCM_restored'];report['math_outputs_published_after_all_restores']=False
  try:
   if report['outer_original_video_inode_and_PCM_restored'] and not report['errors'] and report.get('helper_math_scope_integrity_proved') is True:
    s=json.loads((O/'56-CMU2-baseline-and-selected-whole-scalar.json').read_text());report['math_outputs_published_after_all_restores']=publish_verified_math_outputs(s,O/'56-onlyS11-CMU2-private-math-step-output.txt',M,Path(os.environ['GITHUB_OUTPUT']),report['outer_original_video_inode_and_PCM_restored'])
  except BaseException as e:report['errors'].append({'type':type(e).__name__,'detail':str(e),'during':'verified-math-publication-after-all-restores'});status=1;report['caller_measurement_completed']=False
  if not report['caller_measurement_completed']:status=1
  (O/'56-CMU2-whole-actual-ROOTa430-binding-and-setup.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 return status
if __name__=='__main__':sys.exit(main())
