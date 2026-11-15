"""Concrete ROOT5b366-bound original cachedwhole caller. Author never dispatches it."""
from pathlib import Path
import argparse,hashlib,importlib.util,json,os,re,subprocess,sys,traceback
sys.dont_write_bytecode=True
ROOT_SHA='5b3662be03af72ff6fa203d7a7d68318145871edc81b7c11517cba638922e068'
HELPER_SHA='4c60c628a61bab60a207df54795694c8cfa43c5b0d870c53a0967c916ed6de6f'
PROFILE_SHA='3a5e4fce5e7d8a58a328ce60c48ccf82e4f7ced8033b9e22165aa0af9fe8b1e5'
SOURCE_SHA='e122c817946c4ed6e7cd1394749879276ef2afe9d01ad691b4142c6bbd9ec9b4'
OLD_KEY='Linux-native68-exact-S2-first-spoken-comma-43702410293';OLD_VERSION='1876e5e5b689945a432f2564472935c78443d40f5d021a2378395bf71140c1d5'
NEW_KEY='Linux-native68-exact-S2-strong-and-pronCTX-43758184941';NEW_VERSION='05484165225efbe7bf9fb42b2c84f15a71a73eadff73a3006983d7c3e03b22e6'
MATH_KEY='Linux-native68-only-target-whole-original-math-43722945326';MATH_VERSION='00b4c677297a43021c5f8c943aa224d49fb32065f82bcda32a2d8ddeb68c0931'
S6_KEY='Linux-native68-only-S6-local-original-math-43766261084';S6_VERSION='96ca98f696bc62493e6aa62f5c23f5bc12a1f1722fc6bce97ce9d18d947ccd59'
PARENT_KIND='ROOT-DELEGATED-independent-source68-S2strong-S6boost-combined-whole-oneS2math-execution-adoption'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def require(x,msg):
 if not x:raise AssertionError(msg)
def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def cache_api_row(path,key,version):
 d=json.loads(Path(path).read_text());require(d['total_count']==len(d['actions_caches'])==1,'Unique actual cache API row required');r=d['actions_caches'][0]
 require(r['key']==key and r['version']==version and r['ref']=='refs/heads/codex/finish-05-and-summaries-20261112','Wrong actual key/version/ref; never normalize historical68 label');return r
def validate_root(path,literal,N):
 path,N=map(Path,(path,N));require(literal==ROOT_SHA and path.is_file() and not path.is_symlink() and sha(path)==ROOT_SHA and path.read_bytes()==(N/'root-combined-whole-execution-scope.json').read_bytes(),'Actual ROOT5b366 file/literal before setup or HTTP')
 r=json.loads(path.read_text());require(r['source_id']=='68' and r['book_order']==53 and r['actual_scope_targets']==['S2','S6'] and r['actual_current_whole_reference']['report']['sha256']==P_REFERENCE_SHA(N),'Exact combined ROOT targets/reference');return r

def P_REFERENCE_SHA(N):return json.loads((Path(N)/'profile.json').read_text())['inputs']['reference_whole']['sha256']
def validate_parent(path,literal,N):
 p=Path(path);N=Path(N);require(re.fullmatch('[0-9a-f]{64}',literal or '') and p.is_file() and not p.is_symlink() and sha(p)==literal,'Actual independent parent record fullSHA required')
 require(p.read_bytes()==(N/'actual-parent-combined-whole-review.json').read_bytes() and (N/'actual-parent-combined-whole-review.sha256').read_text().strip()==literal,'Parent copy/literal differs')
 v=json.loads(p.read_text());require(v['kind']==PARENT_KIND and v['root_scope']['sha256']==ROOT_SHA and v['program_SHA256']==HELPER_SHA and v['profile_SHA256']==PROFILE_SHA,'Actual parent must bind new exact ROOT/helper/profile')
 require(v['source_id']=='68' and v['target_sentence']=='S2' and v['actual_scope_targets']==['S2','S6'] and v['sentence_count']==19 and v['independent_review_passed'] is True and v['allow_only_S2_one_original_math_if_missing'] is True and v['S6_saved_math_strict_readonly_no_recalculation'] is True and v['new_TTS_GT_ASR_or_native_finalization_authorized'] is False,'Parent scope incomplete');return v
def verify_transport(N):
 N=Path(N);rows=json.loads((N/'transport-file-pins.json').read_text());require(rows and len({r['relative'] for r in rows})==len(rows),'Finite unique transport pins required')
 for r in rows:
  rel=Path(r['relative']);require(not rel.is_absolute() and '..' not in rel.parts,'Transport path escaped');p=N/rel;require(p.is_file() and not p.is_symlink() and p.stat().st_size==r['bytes'] and sha(p)==r['sha256'],'Frozen program/input differs '+str(rel))
 require(sha(N/'observe68_S2strong_S6boost_combined_whole.py')==HELPER_SHA and sha(N/'profile.json')==PROFILE_SHA,'Wrong whole helper/profile');return rows
def helper_argv(N,M,T,O):
 N,M,T,O=map(Path,(N,M,T,O));return [sys.executable,str(N/'observe68_S2strong_S6boost_combined_whole.py'),'--tools',str(T),'--video-root',str(M),'--inputs',str(N),'--profile',str(N/'profile.json'),'--execution-adoption',str(N/'root-combined-whole-execution-scope.json'),'--execution-adoption-sha256',ROOT_SHA,'--output',str(O/'68-combined-baseline-and-selected-whole-scalar.json'),'--cache-path-output',str(O/'68-combined-private-math-step-output.txt')]
def verify_G27(N,T,W,profile):
 N,T,W=map(Path,(N,T,W));require(sha(T/'出片指纹.py')=='ef589d2ad0bc9e1806a37161c81e727b7f900d4de490d05d4c74755b392b91a9','Original actual G27 differs');g=load('_combined_caller_original_G27',T/'出片指纹.py');paths=g.清单([str(T)]);require(len(paths)==8 and set(paths)==set(profile['original_G27_expected']) and g.核对工作目录(str(W),str(T))==[],'Original eight work imports differ');rows={}
 for name,p in paths.items():
  q=g._找(name,g.工作目录搜(str(W)));require(q is not None and sha(q)==sha(p)==profile['original_G27_expected'][name],'Actual original module path/fullSHA differs '+name);rows[name]={'tools_path':str(Path(p).resolve()),'work_path':str(Path(q).resolve()),'sha256':sha(q)}
 return rows
def publish_verified_math_outputs(s,private,M,real,outer_restored):
 require(outer_restored is True and s.get('math_scope_integrity_proved') is True and s.get('forbidden_model_events')==[],'No SAVE without independent actual math scope and all outer restores')
 required={'all_inner_runtime_source_context_work_module_cache_restores','baseline_and_selected_native_endpoints_restored','declared_source_context_and_actual_mother_inputs_checked','both_actual_new_target_mothers_witnessed_before_math','one_original_S2_math_creator_and_strict_readback','no_forbidden_model_endpoint_events'}
 require(set(s.get('actual_math_scope_prerequisites',{}))==required and all(v is True for v in s['actual_math_scope_prerequisites'].values()),'Unknown or failed source/method/mother/math scope')
 guards=['all_original_local_modules_preexisting_objects_env_cwd_path_trace_restored','all_existing_private_cache_exact_only_one_actual_S2_math_added','public_cache_exact_after','all_runtime_model_voice_AF_G27_dict_context_stamp_bytes_exact_after','all_frozen_inputs_exact_after']
 require(all(s.get(k) is True for k in guards) and all(s.get('restoration',{}).get(k) is True for k in ['normal_scripts_namespace_restored','environment_cwd_sys_path_restored','normal_work_inode_and_PCM_restored','both_T_W_original_context_inode_and_bytes_restored','selected_context_payload_exact_at_exit']) and all(s.get('native_closure_restore_receipts',{}).get(k) is True for k in ['baseline','selected']),'Helper restoration failed; never expose SAVE')
 entries=s.get('actual_new_S2_original_math',{});private=Path(private)
 if not entries:require(not private.exists() or private.read_text()=='','Unexpected private output without actual new math');return False
 require(len(entries)==1 and s.get('math_save_integrity_proved') is True,'One actual verified S2 math only');name,item=next(iter(entries.items()));match=re.fullmatch(r'调平_([0-9a-f]{40})\.json',name)
 require(match is not None and item.get('source_id')=='68' and item.get('target_sentence')=='S2' and item.get('strict_readback_exact') is True and re.fullmatch('[0-9a-f]{64}',item.get('sha256','')),'Wrong actual single-S2 identity')
 rows=[r for r in s['phases']['selected']['original_G36_calls'] if r['sentence']=='S2'];require(len(rows)==1 and rows[0]['file']==name and rows[0]['original_key']==match.group(1) and rows[0]['actual_math_created'] is True and rows[0]['sha256']==item['sha256'],'Selected actual math role differs')
 M=Path(M).resolve();folder=M/'tts/source68-only-S2-combined-whole-original-math-cache';copy_path=folder/name;original=M/'tts/cache_tts'/name
 require(not folder.is_symlink() and all(p.is_file() and not p.is_symlink() for p in [copy_path,original]) and sha(copy_path)==sha(original)==item['sha256'] and json.loads(copy_path.read_text())==json.loads(original.read_text())==item['value'],'Actual math copy/cache regular bytes/value differ')
 runid=os.environ.get('GITHUB_RUN_ID','');require(runid.isdigit(),'Actual run ID required');key='Linux-native68-only-S2-combined-whole-original-math-'+runid;save=s.get('private_original_math_save',{})
 require(save.get('cache_key')==key and save.get('exact_paths')==[str(copy_path)] and save.get('files')==entries and save.get('save_success_not_claimed') is True,'Unknown private declaration')
 expected='cache_key='+key+'\ncache_paths<<ONLY_S2_COMBINED_MATH_PATHS\n'+str(copy_path)+'\nONLY_S2_COMBINED_MATH_PATHS\n';require(private.is_file() and not private.is_symlink() and private.read_text()==expected,'Private fields are not the exact known one math output');real=Path(real);require(real.resolve()!=private.resolve() and not real.resolve().is_relative_to(M),'Real step output must be isolated from private/cached machine')
 with real.open('a') as f:f.write(expected)
 return True
def restore_saved_S6(M,C,profile,hit):
 e=profile['existing_selected_S6_original_G36'];source=Path(M)/'tts/source68-only-S6-local-original-math-cache'/e['file'];dest=Path(C)/e['file'];require(hit=='true' and source.is_file() and not source.is_symlink() and sha(source)==e['sha256'] and json.loads(source.read_text())=={},'Real S6 saved9f744 cache must strictly hit')
 existed=dest.exists();require(not dest.is_symlink() and (not existed or dest.is_file() and sha(dest)==e['sha256']),'Do not overwrite any different existing S6 math')
 if not existed:dest.write_bytes(source.read_bytes())
 require(sha(dest)==sha(source)==e['sha256'] and json.loads(dest.read_text())=={},'Actual S6 strict readback differs');return {'file':e['file'],'sha256':sha(dest),'value':{},'destination_preexisted':existed,'original_math_recomputed':False}

def main():
 p=argparse.ArgumentParser()
 for k in ['actual-root-execution-adoption','actual-parent-review-adoption']:p.add_argument('--'+k,type=Path,required=True);p.add_argument('--'+k+'-sha256',required=True)
 a=p.parse_args();N=Path(__file__).resolve().parent;validate_root(a.actual_root_execution_adoption,a.actual_root_execution_adoption_sha256,N);validate_parent(a.actual_parent_review_adoption,a.actual_parent_review_adoption_sha256,N);pins=verify_transport(N)
 ROOT=Path(os.environ['GITHUB_WORKSPACE']);M=Path(os.environ['RUNNER_TEMP'])/'completion-machine';W=M/'video';T=ROOT/'official-main/视频/工具';O=ROOT/'source68-combined-whole-public';require(not O.exists(),'Fresh scalar output directory required')
 require(all(os.environ.get(k)=='1' for k in ['AUDIO_ONLY','STRICT_CACHE','XG_NOPUSH','XG_KEEP_REVIEWED_GAIN','XG_KEEP_REVIEWED_ENDING','XG_KEEP_REVIEWED_CUTS']) and not any(os.environ.get(k) for k in ['VOICE','AFFILE','OLD_IV_VOID','ONLY','BREATH_FRAC','CACHE_LOG']),'No acoustic/voice override permitted')
 require(all(os.environ.get(k)=='true' for k in ['OLD_S2_MOTHER_CACHE_HIT','NEW_S2_STRONG_MOTHER_CACHE_HIT','OLD_S2_G36_CACHE_HIT','EXISTING_S6_G36_CACHE_HIT']),'All exact existing private caches must hit')
 api={'old_mothers':cache_api_row(N/'actual-mother-cache-API.json',OLD_KEY,OLD_VERSION),'new_mothers':cache_api_row(N/'actual-new-S2-mother-cache-API.json',NEW_KEY,NEW_VERSION),'old_G36':cache_api_row(N/'actual-G36-cache-API.json',MATH_KEY,MATH_VERSION),'S6_G36':cache_api_row(N/'actual-existing-S6-math-cache-API.json',S6_KEY,S6_VERSION)}
 profile=json.loads((N/'profile.json').read_text());C=M/'tts/cache_tts'
 for entries in profile['target_entries'].values():
  for e in entries.values():
   for name,h in [(e['name'],e['sha256']),(e['marker_name'],e['marker_sha256'])]:q=C/name;require(q.is_file() and not q.is_symlink() and sha(q)==h,'Actual old/new mother missing/wrong '+name)
 e=profile['baseline_S6_original_G36'];require((C/e['file']).is_file() and not (C/e['file']).is_symlink() and sha(C/e['file'])==e['sha256'] and json.loads((C/e['file']).read_text())=={},'Base machine must contain genuine existing baseline S6 bb23; missing cannot be manufactured or computed')
 runid=os.environ.get('GITHUB_RUN_ID','');require(runid.isdigit(),'Actual run ID required');scratch=M/('_combined_whole_setup_'+runid);require(not scratch.exists(),'Fresh isolated setup required');scratch.mkdir();O.mkdir()
 report={'kind':'actual-ROOT5b366-and-independent-parent-bound-combined-cachedwhole-setup','root_SHA256':ROOT_SHA,'actual_parent_review_SHA256':a.actual_parent_review_adoption_sha256,'helper_SHA256':HELPER_SHA,'profile_SHA256':PROFILE_SHA,'quality_acceptance':False,'restoration':{},'errors':[],'cache_API':api,'runtime_program_pin_count':len(pins)};status=1
 try:
  lib=load('_combined_setup_original_work_namespace',N/'inputs/observer.py')
  with lib.work_namespace(W,scratch,report['restoration']):
   W.mkdir();subprocess.run([sys.executable,str(N/'install_actual_certified20_context.py')],check=True);sd=W/'scripts';sd.mkdir();source=sd/'68.json';source.write_bytes((N/'inputs/source.json').read_bytes());require(sha(source)==SOURCE_SHA,'Private same-byte source initialization differs')
   context=load('_combined_existing_S13_context',N/'apply_exact_existing_S13_context_data.py');report['actual_shared_S13_context']=context.apply(T,W,N/'source68-S13-context.json',N/'root-source68-S13-context-adoption.json',O/'68-actual-shared-S13-context.json')
   restore=load('_combined_existing_baseline_math_restore',N/'restore_exact_existing_S2_G36_JSON.py');report['actual_baseline_math_readback']=restore.restore_existing_original_math(M/'tts/source68-only-target-whole-original-math-cache'/restore.NAME,C/restore.NAME,os.environ['OLD_S2_G36_CACHE_HIT'])
   report['actual_existing_S6_math_readback']=restore_saved_S6(M,C,profile,os.environ['EXISTING_S6_G36_CACHE_HIT'])
   report['G27_before_helper']=verify_G27(N,T,W,profile);status=subprocess.run(helper_argv(N,M,T,O)).returncode;report['helper_exit']=status;report['G27_after_helper']=verify_G27(N,T,W,profile)
   s=json.loads((O/'68-combined-baseline-and-selected-whole-scalar.json').read_text());report['helper_measurement_completed']=s['measurement_completed'];report['helper_exact_scope_proved']=s['exact_scope_proved'];report['helper_math_scope_integrity_proved']=s.get('math_scope_integrity_proved') is True;report['helper_reported_whole_or_quality_errors']=s['errors']
   if not (s['measurement_completed'] is True and s['exact_scope_proved'] is True and s['errors']==[]):status=1
 except BaseException as e:report['errors'].append({'type':type(e).__name__,'detail':str(e)});traceback.print_exc();status=1
 finally:
  report['outer_original_video_inode_and_PCM_restored']=report['restoration'].get('normal_work_inode_and_PCM_restored') is True;report['caller_measurement_completed']=report.get('helper_measurement_completed') is True and report.get('helper_exact_scope_proved') is True and not report['errors'] and report['outer_original_video_inode_and_PCM_restored'];report['math_outputs_published_after_all_restores']=False
  try:
   if report['outer_original_video_inode_and_PCM_restored'] and not report['errors'] and report.get('helper_math_scope_integrity_proved') is True:
    s=json.loads((O/'68-combined-baseline-and-selected-whole-scalar.json').read_text());report['math_outputs_published_after_all_restores']=publish_verified_math_outputs(s,O/'68-combined-private-math-step-output.txt',M,Path(os.environ['GITHUB_OUTPUT']),report['outer_original_video_inode_and_PCM_restored'])
  except BaseException as e:report['errors'].append({'type':type(e).__name__,'detail':str(e),'during':'verified-math-publication-after-all-restores'});status=1;report['caller_measurement_completed']=False
  if not report['caller_measurement_completed']:status=1
  (O/'68-combined-whole-actual-ROOT5b366-binding-and-setup.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 return status
if __name__=='__main__':sys.exit(main())
