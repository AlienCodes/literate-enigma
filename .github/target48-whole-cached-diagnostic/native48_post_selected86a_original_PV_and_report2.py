"""Read only the successful86a same-native actual WAV; no rebuild/inference/math generation.
Original PV scan and original GT/labels/audit are observational, never acceptance.
"""
from pathlib import Path
import argparse,copy,hashlib,importlib.util,json,os,sys,traceback
sys.dont_write_bytecode=True
P=argparse.ArgumentParser()
for k in ('tools','video-root','request','whole-observation','cache-identity','adapter','main-code-adoption','output-dir'):
 P.add_argument('--'+k,type=Path,required=True)
a=P.parse_args();T=a.tools.resolve();M=a.video_root.resolve();W=M/'video';C=M/'tts/cache_tts';O=a.output_dir.resolve()
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb')as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
def inventory():return{p.name:sha(p)for p in C.iterdir()if p.is_file()}
SOURCE='73ac6fe3fdc0d203eaa1d8a4de6399381f15a14140aaf2dbe6bc4fde30b16610';MAKER='4c85e1fbdd2e82c5646d5f58df63c85eca60af4ef521f1d36f765575a568d6f3'
assert sha(a.request)==SOURCE
assert sha(a.adapter)=='8244b099265e3979c6cd90383a2bf500e392467d78ba2ae494c9ef6c7cf624e8'
assert sha(a.main_code_adoption)=='eeabccad3ef759bae8418e18a5c61aefbd903b46d827292b15ea4c1c7f1a143f'
assert sha(a.cache_identity)=='29f7d58ebd14d3ee50c1a779eb7dc95ecb60fd10f9812bff788bdfcf5af8ebe1'
main=json.loads(a.whole_observation.read_text());assert main['helper_sha256']=='86a36966f42d6567c09bffe826a6b7e70c1e40d3151071f02bfb4b0536e36028'
assert main['source_request_sha256']==SOURCE and main['exact_scope_proved']and not main['errors']
assert main['all_protected_title_and13_pre_and_post_master_exact295']and main['all_four_final_restored_values_exact_raw_and_normalized']
assert main['S9_only_missing_original_math_result_empty']and main['no_baseline_rebuild_or_other_new_math']
assert set(main['phases'])=={'selected_four_protection'};phase=main['phases']['selected_four_protection']
assert len(phase['observed_sentences'])==17
assert all(x['final_pre_master_values_equal_original_raw']and x['final_mastered_selected_values_equal_raw_under_original_normalization']and x['original_sf_write_read_PCM16_quantization_equal_per_sample']for x in phase['four_final_restored_sample_values_independent_vs_raw'].values())
for flag in ('STRICT_CACHE','AUDIO_ONLY','XG_NOPUSH','XG_KEEP_REVIEWED_GAIN','XG_KEEP_REVIEWED_CUTS','XG_KEEP_REVIEWED_ENDING'):assert os.environ.get(flag)=='1'
assert not os.environ.get('OLD_IV_VOID')and not os.environ.get('VOICE')and not os.environ.get('AFFILE')
assert Path('/home/user/postgraduate-vocabulary').resolve()==T.parent.parent.resolve()
assert sha(T/'make_video.py')==sha(W/'make_video.py')==MAKER
for rel,digest in main['actual_original_fivecore_seven_runtime_files'].items():assert sha(T/rel)==digest
assert sha(T/'发音词典/读音改正.json')=='5f558c61f8ffb99009a89989afcc07a9ce168b2b70a6c9377289040d14ec402b'
assert sha(T/'发音词典/按语境读音.json')=='4d8905dc1a87f97b707270f03f41ea0fdf2b207ca218ed74608cdb134e3dc8e3'
identity=json.loads(a.cache_identity.read_text())
for name,digest in identity['all_five_restored_files_require_actual_fullSHA_readback'].items():assert sha(C/name)==digest
for name,digest in identity['original_models_fullSHA'].items():assert sha(M/'tts'/name)==digest
assert sha(M/'tts/voice_mb.npy')==identity['original_voice_sha256']
for e in main['actual_used_source48_private_cache_entries_scalar_only']:
 assert sha(C/e['name'])==e['sha256']
 if e.get('single_thread_marker_sha256'):assert sha(C/(e['name']+'.单线程'))==e['single_thread_marker_sha256']
newgain=phase['actual_new_S9_G51'];assert sha(C/newgain['name'])==newgain['sha256']and json.loads((C/newgain['name']).read_text())=={}
S=M/'_source48_post_selected86a_original_PV_report2';private_work=M/'_source48_selected_four_protection_one_whole_diagnostic/selected_four_protection-private-original-work48'
canonical=M/'_source48_selected_four_protection_one_whole_diagnostic/selected_four_protection-actual-original-canonical.m4a'
assert not S.exists()and private_work.is_dir()and canonical.is_file()
assert sha(private_work/'a.wav')==phase['actual_complete_WAV']['file_sha256']
assert sha(T/'纯人声核对.py')=='1050d1df51eb21ed0dbd19e9a97a8325c4dbfa1f58e9834760f8e5e5ba0b414f'
assert not O.exists(),'Use a new scalar output namespace; no evidence overwrite.'
source=W/'scripts/48.json';scripts=source.parent;work=W/'work_48';assert scripts.is_dir()
prior_source=source.read_bytes()if source.exists()else None;scripts_link=scripts.is_symlink();source_isolated=False;work_isolated=False
other_before={str(p):sha(p)for p in scripts.glob('*.json')if p.name!='48.json'}
prior_work_wav=sha(work/'a.wav')if(work/'a.wav').is_file()else None
prior_script_entry=S/'prior-script48';prior_scripts_entry=S/'prior-scripts-link';prior_work=S/'prior-work48'
envdir=W/'环境';env_created=False
assert sha(T/'环境/模型校验码.json')=='dfde6c065a3558b74923ce82865a3b01dae1f839af4456b74de55dc3ff492312'
if envdir.exists():assert sha(envdir/'模型校验码.json')=='dfde6c065a3558b74923ce82865a3b01dae1f839af4456b74de55dc3ff492312'
before_cache=inventory();S.mkdir();O.mkdir(parents=True)
report={'kind':'source48_same_native_success86a_only_readonly_original_PV_fulltuple_and_fresh_GT18_report2_POST','main_observer_success_preserved':True,'main_observer_report_sha256':sha(a.whole_observation),'source_sha256':SOURCE,'adapter_sha256':sha(a.adapter),'helper_sha256':sha(__file__),'no_audio_rebuild_model_inference_G36_or_render':True,'production_source_CF_voice_or_threshold_written':False,'formal_acceptance':False,'errors':[]}
try:
 if not envdir.exists():envdir.symlink_to(T/'环境',target_is_directory=True);env_created=True
 if scripts_link:
  others={p.name:p.read_bytes()for p in scripts.glob('*.json')if p.name!='48.json'};scripts.rename(prior_scripts_entry);scripts.mkdir();source_isolated=True
  for name,b in others.items():(scripts/name).write_bytes(b)
 else:
  if source.exists()or source.is_symlink():source.rename(prior_script_entry)
  source_isolated=True
 source.write_bytes(a.request.read_bytes());assert sha(source)==SOURCE
 if work.exists()or work.is_symlink():work.rename(prior_work)
 work.symlink_to(private_work,target_is_directory=True);work_isolated=True
 os.chdir(W);sys.path.insert(0,str(W))
 for name in ('render','title2','clean','出片指纹'):sys.modules.pop(name,None)
 spec=importlib.util.spec_from_file_location('source48_only_POST_no_build',W/'make_video.py');m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m)
 assert m.PRON_WORDS['Yuan']=='juːˈɑːn'and sha(m._OLDF)=='91ccecd61ade5284de72f27235c82df3fdff6350576abfac02d2e0db0f346a9a'
 assert sha(m._CTX_PATH)=='4d8905dc1a87f97b707270f03f41ea0fdf2b207ca218ed74608cdb134e3dc8e3'
 m._REPO_CACHE=str(M/'forbid-public-private-cache-export');assert not Path(m._REPO_CACHE).exists()
 own=[' '.join(m.re.sub(r'\*\*','',m.R.strip_gloss(c['en'])).strip()for c in x['chunks'])for x in json.loads(source.read_text())['sentences']]
 assert all(m.SENT_NO[s]=='48'for s in own)
 # Original full PV detector consumes the actual full quantized WAV. Export all
 # original unrounded tuples and displayed metrics, with no confirmation writes.
 sp=importlib.util.spec_from_file_location('source48_POST_original_fullPV',T/'纯人声核对.py');pv=importlib.util.module_from_spec(sp);sp.loader.exec_module(pv)
 wav=work/'a.wav';pcm,sr=m.sf.read(wav);assert sr==24000 and len(pcm)==phase['actual_complete_WAV']['samples']
 fp=hashlib.md5(wav.read_bytes()).hexdigest()[:12];assert fp==phase['actual_full_WAV_original_PV_fingerprint_md5_12']
 flags=pv.scan(pcm);current=json.loads(source.read_text());pvrows=[]
 for f in flags:
  clock=[{'sentence':sid,**row}for sid,row in phase['actual_sample_clock'].items()if row['start_s']<=f[1]<row['end_s']]
  pvrows.append({'kind':f[0],'key':pv.key(f),'full_original_unrounded_tuple':list(f),'display_metrics':pv.实测(f),'actual_span_s':[f[1],f[2]],'current_actual_sentence_clock':clock,'existing_source_CF_not_accepted_or_renewed':current.get('核对确认',{}).get('非人声',{}).get(pv.key(f))})
 pvout={'kind':'source48_actual_new_selected86a_whole_original_PV_FULL_TUPLES_no_CF_write','source_sha256':SOURCE,'actual_WAV_sha256':sha(wav),'actual_whole_PV_fingerprint':fp,'original_PV_program_sha256':sha(T/'纯人声核对.py'),'actual_full_WAV_decoded_dtype':str(pcm.dtype),'original_scan_all_flag_count':len(pvrows),'all_original_flags':pvrows,'formal_acceptance':False,'source_CF_not_modified':True}
 (O/'48-actual-new-whole-original-PV-full-tuples.json').write_text(json.dumps(pvout,ensure_ascii=False,indent=2,default=lambda x:x.item())+'\n')
 report['actual_original_PV_full_tuple_report_sha256']=sha(O/'48-actual-new-whole-original-PV-full-tuples.json');report['actual_full_PV_flag_count']=len(pvrows)
 sp=importlib.util.spec_from_file_location('source48_POST_original_report2_adapter',a.adapter);mod=importlib.util.module_from_spec(sp);sp.loader.exec_module(mod)
 observed=mod.observe(m,M,T,a.request,a.whole_observation,canonical,S/'private-GT18-report2',O/'original-report2-safe-scalars',root_has_adopted_cached_labels_IO=True)
 assert observed['report2_observation_completed']and observed['all_private_TTS_cache_existing_exact']and observed['source_exact_after']and observed['replay_RAW_exact_after']
 report['actual_original_report2_observation_sha256']=sha(O/'original-report2-safe-scalars/48-original-reference-report2-observation.json')
 report['actual_original_report2_JSON_sha256']=sha(O/'original-report2-safe-scalars/report2_48.json')
 report['actual_original_report2_TXT_sha256']=sha(O/'original-report2-safe-scalars/report2_48.txt')
 report['original_default_audit_g']=observed['original_audit_default_g'];report['actual_A10_edge_count']=len(observed['actual_A10_edge_rows']);report['actual_generic_tail_or_onset_positive_count']=len(observed['actual_tail_or_onset_positive_rows'])
 report['post_observation_completed']=True
except BaseException as e:
 report['post_observation_completed']=False;report['errors'].append({'type':type(e).__name__,'detail':str(e)});traceback.print_exc()
finally:
 if work_isolated:
  assert work.is_symlink()and work.resolve()==private_work.resolve();work.unlink()
 if prior_work.exists()or prior_work.is_symlink():prior_work.rename(work)
 if scripts_link:
  if prior_scripts_entry.exists()or prior_scripts_entry.is_symlink():
   if scripts.exists():
    assert not scripts.is_symlink()
    for p in scripts.iterdir():assert p.is_file()and p.suffix=='.json';p.unlink()
    scripts.rmdir()
   prior_scripts_entry.rename(scripts)
 elif source_isolated:
  source.unlink(missing_ok=True)
  if prior_script_entry.exists()or prior_script_entry.is_symlink():prior_script_entry.rename(source)
 if env_created:envdir.unlink()
 report['all_existing_TTS_cache_exact_before_after']=before_cache==inventory()
 report['normal_source48_exact_restored']=source.read_bytes()==prior_source if prior_source is not None else not source.exists()
 report['normal_preexisting_work48_exact_restored']=sha(work/'a.wav')==prior_work_wav if prior_work_wav is not None else True
 report['other69_source_scripts_unchanged']=all(Path(p).is_file()and sha(p)==v for p,v in other_before.items())
 report['actual_new_private_WAV_unchanged']=sha(private_work/'a.wav')==phase['actual_complete_WAV']['file_sha256']
 report['frozen_input_source_and_adapter_unchanged']=sha(a.request)==SOURCE and sha(a.adapter)=='8244b099265e3979c6cd90383a2bf500e392467d78ba2ae494c9ef6c7cf624e8'
 report['original_runtime_core_unchanged']=sha(T/'make_video.py')==sha(W/'make_video.py')==MAKER and all(sha(T/p)==v for p,v in main['actual_original_fivecore_seven_runtime_files'].items())
 report['exact_scope_proved']=bool(report.get('post_observation_completed')and report['all_existing_TTS_cache_exact_before_after']and report['normal_source48_exact_restored']and report['normal_preexisting_work48_exact_restored']and report['other69_source_scripts_unchanged']and report['actual_new_private_WAV_unchanged']and report['frozen_input_source_and_adapter_unchanged']and report['original_runtime_core_unchanged'])
 (O/'48-same-native-post-original-PV-and-report2-scope.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'main_observer_success_preserved':True,'post_observation_completed':report.get('post_observation_completed'),'exact_scope_proved':report['exact_scope_proved'],'errors':report['errors']},ensure_ascii=False))
sys.exit(0 if report['exact_scope_proved']else 1)
