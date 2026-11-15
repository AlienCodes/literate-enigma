#!/usr/bin/env python3
"""Exact source48 certified-original-fivecore new-S15 plus four measured word-preservation controls supplement.

Runs only after the unchanged actual full native pipeline. No inference, repair,
source writing, CF renewal, numeric-threshold changes, or human-listening claim.
The independent native whole-track identity evidence is kept as diagnosis;
production requires the new real canonical WAV/AAC plus original full gates.
"""
import argparse,contextlib,copy,datetime,hashlib,importlib.util,json,os,re,subprocess,sys,tempfile,wave
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parent;SR=48000

def sha(path):
 h=hashlib.sha256()
 with Path(path).open('rb')as f:
  for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
 return h.hexdigest()
def canonical(value):return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def safe(v):
 if isinstance(v,dict):return {str(k):safe(x)for k,x in v.items()}
 if isinstance(v,(list,tuple)):return [safe(x)for x in v]
 if isinstance(v,np.integer):return int(v)
 if isinstance(v,(float,np.floating)):return float(v)if np.isfinite(v)else None
 if isinstance(v,np.bool_):return bool(v)
 return v
def module(name,path):
 spec=importlib.util.spec_from_file_location(name,path);value=importlib.util.module_from_spec(spec);sys.modules[name]=value;spec.loader.exec_module(value);return value
def capture(cmd):return subprocess.check_output([str(x)for x in cmd])
def aac(path):return capture(['ffmpeg','-v','error','-nostdin','-i',path,'-map','0:a:0','-c:a','copy','-f','adts','-'])
def spoken(data):return [data['title_en']]+[' '.join(re.sub(r'\{\{.*?\}\}|\*\*','',c['en'])for c in s['chunks'])for s in data['sentences']]
def control_valid(data,p):return str(data.get('no'))==p['article']and {k:data.get(k)for k in p['approved_audio_controls']}==p['approved_audio_controls']
def nonclipped(a):return bool(len(a)>0 and np.isfinite(a).all()and np.max(np.abs(a))<1.)
def fingerprints_valid(measured,p):return all(measured.get(k)==v for k,v in p['fingerprints'].items())
def at(data,path):
 for k in path:data=data[k]
 return data
def put(data,path,value):
 for k in path[:-1]:data=data[k]
 data[path[-1]]=value

def actual_nonreview_binding(actual,requested,p):
 current=copy.deepcopy(actual);keys=('换行变更已获同意','换行变更记录');moved=any(requested.get(k)!=actual.get(k)for k in keys)
 if moved:
  consent=requested.get(keys[0]);before=requested.get(keys[1],[]);after=actual.get(keys[1],[])
  if not(isinstance(consent,dict)and consent and keys[0]not in actual and isinstance(before,list)and isinstance(after,list)and len(after)==len(before)+1 and after[:-1]==before and isinstance(after[-1],dict)):return False,{'exact_original_pending_history_move':False}
  last=after[-1];day=last.get('日期','')
  if not(isinstance(day,str)and re.fullmatch(r'\d{4}-\d{2}-\d{2}',day)and{k:v for k,v in last.items()if k!='日期'}==consent):return False,{'exact_original_pending_history_move':False}
  try:datetime.date.fromisoformat(day)
  except ValueError:return False,{'exact_original_pending_history_move':False}
  current[keys[0]]=copy.deepcopy(consent)
  if keys[1]in requested:current[keys[1]]=copy.deepcopy(before)
  else:current.pop(keys[1],None)
 normalized=[]
 for variant in p.get('exact_observed_original_G35_note_variants',[]):
  path=variant['path']
  if at(current,path)==variant['observed_original_variant']and at(requested,path)==variant['requested']:
   put(current,path,variant['requested']);normalized.append(path)
 core={k:v for k,v in current.items()if k not in p['review_only_top_level_keys']};valid=canonical(core)==p['approved_nonreview_document_sha256']
 return valid,{'original_pending_consent_consumed':moved,'exact_original_pending_history_move':bool(moved),'exact_observed_G35_note_paths_normalized':normalized,'all_other_nonreview_data_exact':valid}

def prior_evidence_valid(e,p):
 if p.get('whole_profile_bound')is not True:return False
 if not(e.get('diagnostic_only')is True and e.get('production_delivery_eligible')is False and e.get('quality_acceptance')is False and e.get('diagnostic_completed')is True and e.get('exact_scope_proved')is True and e.get('old_and_new_model_inference_forbidden')is True):return False
 if not(e.get('article')=='48'and e.get('source_request_sha256')==p['fingerprints']['request_source_sha256']and e.get('baseline_current_request_sha256')==p['current_diagnostic_baseline']['request_source_sha256']and e.get('baseline_is_historical_legacy_f7d')is False):return False
 if not(e.get('same_original_maker_sha256')==p['original_tool_sha256']['make_video.py']and e.get('required_original_fivecore_contract_sha256')==p['certified_original_fivecore_contract_sha256']and e.get('actual_correct_context_gain_reselection_decision_sha256')==p['root_gain_selection_sha256']):return False
 if not(e.get('original_dictionary_sha256')==p['original_tool_sha256']['发音词典/读音改正.json']and e.get('context_dictionary_sha256')==p['original_tool_sha256']['发音词典/按语境读音.json']and e.get('original_old_cache_registry_sha256')==p['actual_old_registry_sha256']):return False
 b,c=(e['phases'][key]for key in ['baseline_current4f','selected_new0193'])
 if not(b['actual_complete_WAV']['file_sha256']==p['current_diagnostic_baseline']['raw_WAV_sha256']and b['actual_complete_AAC']['AAC_ADTS_sha256']==p['current_diagnostic_baseline']['AAC_ADTS_sha256']and c['actual_complete_WAV']['file_sha256']==p['fingerprints']['actual_raw_WAV_sha256']and c['actual_complete_AAC']['AAC_ADTS_sha256']==p['fingerprints']['canonical_AAC_ADTS_sha256']):return False
 if not(b['actual_original_mastering']==p['actual_baseline_mastering']and c['actual_original_mastering']==p['actual_selected_mastering']and b['actual_original_mastering']['original_ordered_formula_exact_to_sf_write_argument']is True and c['actual_original_mastering']['original_ordered_formula_exact_to_sf_write_argument']is True):return False
 rows=e['non_target_title_and16_sentence_pre_master_identity'];outside={r['segment']:r for r in rows};want={'title'}|{f'S{i}'for i in range(1,18)if i!=15}
 if set(outside)!=want or outside!=p['non_target_pre_master_identity']:return False
 if not all(r['actual_pre_master_samples_exact']is True and r['old_samples']==r['new_samples']and r['old_dtype']==r['new_dtype']and r['old_actual_PCM_sha256']==r['new_actual_PCM_sha256']for r in rows):return False
 target=c['observed_sentences']['S15']
 if not(target['automatic_gain_dB']==p['actual_selected_S15_automatic_gain_dB']and target['manual_gain_dB']=={'1':1.0}and target['actual_raw_w_fingerprint']==p['actual_selected_S15_raw_fingerprint']and e['target_S15_changed_as_explicitly_authorized']is True):return False
 if not(e['all_existing_private_cache_files_exact_before_after']is True and e['normal_W_scripts48_exact_restored']is True and e['all_other_W_source_scripts_exact']is True and e['original_maker_file_exact_after']is True and e['all_original_seven_runtime_core_files_exact_after']is True and e['original_request_and_baseline_files_exact_after']is True):return False
 return canonical(c['actual_original_piece_time_table'])==p['approved_producer_segments_sha256']


def evidence_valid(e,p):
 # Original295's independently captured proper-context new-name scope stays bound;
 # current513d adds only four measured physical protections and specific metadata.
 prior=p['proper295_physical_reference'];ep=HERE/prior['evidence_file'];pp=HERE/prior['profile_file']
 if not(sha(ep)==prior['evidence_sha256']and sha(pp)==prior['profile_sha256']and prior_evidence_valid(json.loads(ep.read_text()),json.loads(pp.read_text()))):return False
 if not(p.get('whole_profile_bound')is True and e.get('article')=='48'and e.get('diagnostic_only')is True and e.get('production_delivery_eligible')is False and e.get('quality_acceptance')is False and e.get('diagnostic_completed')is True and e.get('exact_scope_proved')is True and e.get('errors')==[]):return False
 if not(e['old_and_new_model_inference_forbidden']is True and e['no_baseline_rebuild_or_other_new_math']is True and e['source_request_sha256']==p['physical_source_sha256']and e['baseline_current_request_sha256']==prior['request_source_sha256']and e['baseline_is_historical_legacy_f7d']is False and e['prior0193_whole_reference_only_not_rebuilt']is True):return False
 if not(e['same_original_maker_sha256']==p['original_tool_sha256']['make_video.py']and e['required_original_fivecore_contract_sha256']==p['certified_original_fivecore_contract_sha256']and e['actual_correct_context_gain_reselection_decision_sha256']==p['root_gain_selection_sha256']):return False
 if not(e['original_dictionary_sha256']==p['original_tool_sha256']['发音词典/读音改正.json']and e['context_dictionary_sha256']==p['original_tool_sha256']['发音词典/按语境读音.json']and e['original_old_cache_registry_sha256']==p['actual_old_registry_sha256']):return False
 if not(e['root_four_physical_selection_sha256']==p['root_four_physical_selection_sha256']and e['source_and_GEN_only_four_NV_freeze_sha256']==p['source_and_GEN_only_four_NV_freeze_sha256']):return False
 physical=HERE/p['physical_source_file'];final=HERE/p['final_request_source_file'];decision=HERE/p['root_current_specific_metadata_decision_file']
 if not(sha(physical)==p['physical_source_sha256']and sha(final)==p['fingerprints']['request_source_sha256']and sha(decision)==p['root_current_specific_metadata_decision_sha256']):return False
 old=json.loads(physical.read_text());requested=json.loads(final.read_text());restored=copy.deepcopy(requested)
 for key in p['metadata_only_since_actual57_allowed_CF_sections']:restored['核对确认'][key]=copy.deepcopy(old['核对确认'][key])
 for key,value in p['metadata_only_since_actual57_allowed_display_HL'].items():
  if requested['高亮开始'].get(key)!=value:return False
  if key in old.get('高亮开始',{}):restored['高亮开始'][key]=old['高亮开始'][key]
  else:restored['高亮开始'].pop(key,None)
 # Exact root-selected S10 leaf only; never reset the entire machine-ASR section.
 case_file=HERE/p['root_selected_S10_machine_case_file']
 if sha(case_file)!=p['root_selected_S10_machine_case_sha256']:return False
 case=json.loads(case_file.read_text());selected=case['selected_specific_machine_confirmation']
 if not(case['source_id']=='48'and case['selected_record_canonical_JSON_sha256']==p['approved_S10_machine_case_canonical_SHA256']and canonical(selected)==p['approved_S10_machine_case_canonical_SHA256']):return False
 actual_machine=requested['核对确认'].get('机器复听',{});original_machine=old['核对确认'].get('机器复听',{})
 if not('S10'in original_machine and actual_machine.get('S10')==selected and {k:v for k,v in actual_machine.items()if k!='S10'}=={k:v for k,v in original_machine.items()if k!='S10'}):return False
 restored['核对确认']['机器复听']['S10']=copy.deepcopy(original_machine['S10'])
 if restored!=old or not control_valid(requested,p):return False
 c=e['phases']['selected_four_protection']
 if not(c['source_sha256']==p['physical_source_sha256']and c['actual_complete_WAV']['file_sha256']==p['fingerprints']['actual_raw_WAV_sha256']and c['actual_complete_AAC']['AAC_ADTS_sha256']==p['fingerprints']['canonical_AAC_ADTS_sha256']and c['actual_complete_AAC']['packet_count']==p['approved_canonical_audio_packet_provenance']['packet_count']and c['actual_full_WAV_original_PV_fingerprint_md5_12']==p['actual_current_whole_PV_fingerprint']):return False
 if not(c['actual_original_mastering']==p['actual_selected_mastering']and c['actual_original_mastering']['original_ordered_formula_exact_to_sf_write_argument']is True and e['actual_global_scale_ratio_new_over_prior295']==1.0 and c['actual_sample_clock']==p['actual_current_sample_clock']):return False
 identity=e['protected_title_and13_sentence_physical_identity'];want={'title'}|{f'S{i}'for i in range(1,18)if i not in(9,10,12,13)}
 if not({r['segment']for r in identity}==want and identity==p['protected_title_and13_physical_identity']and all(r['pre_master_exact_to_actual295']is True and r['post_master_float_exact_to_actual295']is True for r in identity)and e['all_protected_title_and13_pre_and_post_master_exact295']is True):return False
 four=c['four_final_restored_sample_values_independent_vs_raw']
 if not(four==p['actual_four_final_restored_ranges']and set(four)=={'S9','S10','S12','S13'}and e['all_four_final_restored_values_exact_raw_and_normalized']is True):return False
 for row in four.values():
  if not(row['selected_raw_samples']==row['actual_final_mapped_samples']and row['final_pre_master_values_equal_original_raw']is True and row['final_pre_master_mismatched_samples']==0 and row['final_mastered_selected_values_equal_raw_under_original_normalization']is True and row['final_mastered_mismatched_samples']==0 and row['original_sf_write_read_PCM16_quantization_equal_per_sample']is True and row['PCM16_quantized_mismatched_samples']==0):return False
 target=c['observed_sentences']['S15']
 if not(target['automatic_gain_dB']==p['actual_selected_S15_automatic_gain_dB']and target['manual_gain_dB']=={'1':1.0}and target['actual_raw_w_fingerprint']==p['actual_selected_S15_raw_fingerprint']):return False
 gain=c['actual_new_S9_G51']
 if not(gain==p['actual_original_S9_only_gain_cache']and gain['actual_original_gains']=={}and gain['sha256']=='44136fa355b3678a1146ad16f7e8649e94fb4fc21fe77e8310c060f61caaff8a'and e['S9_only_missing_original_math_result_empty']is True and e['only_allowed_new_S9_G51_cache_written']is True):return False
 if not all(e[k]is True for k in ['all_existing_private_cache_files_exact_before_after','normal_W_scripts48_exact_restored','normal_W_preexisting_work48_PCM_exact_restored','all_other_W_source_scripts_exact','original_maker_file_exact_after','all_original_seven_runtime_core_files_exact_after','original_request_and_baseline_files_exact_after']):return False
 return canonical(c['actual_original_piece_time_table'])==p['approved_producer_segments_sha256']


def runtime_mutation_tests(actual,p,fp,raw_bytes,decoded):
 wrong=copy.deepcopy(actual);sid='S15';piece='1';wrong['分段增益dB'][sid][piece]=0.
 badbytes=bytearray(raw_bytes);badbytes[44+2*min(100,(len(raw_bytes)-44)//2-1)]^=1;badfp={**fp,'actual_raw_WAV_sha256':hashlib.sha256(badbytes).hexdigest()}
 clipped=decoded.copy();clipped[min(len(clipped)-1,SR)]=1.
 return {'actual_new_source_and_full_raw_AAC_identity_positive':control_valid(actual,p)and fingerprints_valid(fp,p)and nonclipped(decoded),'wrong_gain_or_source_control_rejected':not control_valid(wrong,p),'actual_one_PCM16_sample_byte_mutation_rejected':not fingerprints_valid(badfp,p),'actual_decoded_clipping_mutation_rejected':not nonclipped(clipped),'mutated_audio_written':False,'ASR_simulated':False}
@contextlib.contextmanager
def directory(path):
 before=Path.cwd();os.chdir(path)
 try:yield
 finally:os.chdir(before)

def audit(args):
 output=Path(args.output);output.parent.mkdir(parents=True,exist_ok=True);no=args.article;checks=[]
 report={'article':no,'kind':'controlled_audio_repair','passed':False,'repair_applied':False,'diagnostic_only':bool(args.diagnostic),'production_delivery_eligible':False,'official_full_gates_are_separate_required_precondition':True,'official_gates_replaced_or_thresholds_modified':False,'subjective_listening_claimed':False,'private_caches_GT_or_PCM_exported':False,'program_sha256':sha(__file__)}
 def add(name,passed,**kw):checks.append(dict(name=name,passed=bool(passed),**safe(kw)))
 try:
  profile_path=Path(args.reference or HERE/f'audio{no}-controlled-qc-reference.json');p=json.loads(profile_path.read_text());report['reference_file_sha256']=sha(profile_path);assert no==p['article']=='48'and p['enabled']is True and p['whole_profile_bound']is True
  assert p['review_only_top_level_keys']==['核对确认','区间声音指纹'];utility=Path(args.numeric_utilities or HERE/'audio-qc.py');assert sha(utility)==p['numeric_utilities_sha256'];U=module('spoken_unchanged_numeric_utilities_'+no,utility)
  ep=HERE/p['whole_track_evidence_file'];add('actual-native-whole-track-proof-bytes-and-precise-voice-scope',sha(ep)==p['whole_track_evidence_sha256']and evidence_valid(json.loads(ep.read_text()),p),actual_native_diagnostic_run=p['actual_whole_native_diagnostic_run'],proof_is_diagnostic_and_not_substituted_for_formal_gates=True)
  request=Path(args.request).resolve();work=Path(args.work).resolve();reqpath=request/f'视频/脚本/{no}.json';genpath=request/f'视频/工具/初稿生成/gen{no}.py';actualpath=Path(args.actual_source or work/f'scripts/{no}.json');rawpath=Path(args.raw_pcm or work/f'work_{no}/a.wav');requested=json.loads(reqpath.read_text());actual=json.loads(actualpath.read_text());oldaac=aac(args.accepted_source);newaac=aac(args.canonical_video)
  fp={'request_source_sha256':sha(reqpath),'request_generator_sha256':sha(genpath),'actual_full_source_sha256':sha(actualpath),'actual_raw_WAV_sha256':sha(rawpath),'accepted_video_sha256':sha(args.accepted_source),'canonical_video_sha256':sha(args.canonical_video),'accepted_AAC_ADTS_sha256':hashlib.sha256(oldaac).hexdigest(),'canonical_AAC_ADTS_sha256':hashlib.sha256(newaac).hexdigest()}
  report.update(fingerprints=fp,source_current_sha256=fp['actual_full_source_sha256'],accepted_sha256=fp['accepted_video_sha256'],canonical_sha256=fp['canonical_video_sha256'],source_authorization_ids=p['source_authorization_ids'])
  for key,want in p['fingerprints'].items():add('exact-approved-fingerprint:'+key,fp[key]==want,actual=fp[key],expected=want)
  for label,data in [('requested',requested),('actual',actual)]:
   if label=='actual':valid,meta=actual_nonreview_binding(actual,requested,p);add(label+'-entire-source-except-original-review-and-exact-mechanical-metadata',valid,**meta)
   else:add(label+'-entire-nonreview-source',canonical({k:v for k,v in data.items()if k not in p['review_only_top_level_keys']})==p['approved_nonreview_document_sha256'])
   add(label+'-only-exact-approved-spoken-and-gain-controls',control_valid(data,p));add(label+'-all-display-spoken-English-words-preserved',canonical(spoken(data))==p['spoken_title_and_sentences_sha256'])
  if not all(x['passed']for x in checks):raise ValueError('Exact new-source/raw/AAC or actual voice-scope identity failed.')
  if not args.diagnostic:
   statuspath=Path(args.official_status or output.parent/f'{no}-status.json');status=json.loads(statuspath.read_text());passed=status.get('canonical_pipeline_passed')is True and status.get('canonical_video_sha256')==fp['canonical_video_sha256']and status.get('canonical_aac_adts_sha256')==fp['canonical_AAC_ADTS_sha256']and status.get('final_wav_sha256')==fp['actual_raw_WAV_sha256'];add('unchanged-full-native-pipeline-all-gates-already-really-passed',passed,status_file_sha256=sha(statuspath),original_two_ASR_and_full_gates_not_replaced=True)
   if not passed:raise ValueError('Actual original native canonical pipeline/status must pass and bind first.')
  raw_bytes=rawpath.read_bytes()
  with wave.open(str(rawpath),'rb')as wav:shape={'rate':wav.getframerate(),'channels':wav.getnchannels(),'width':wav.getsampwidth(),'samples':wav.getnframes()}
  add('actual-raw-PCM16-shape-bytes-and-duration',shape==p['raw_WAV_shape']and len(raw_bytes)==p['raw_WAV_bytes'],actual=shape,actual_bytes=len(raw_bytes))
  groups=json.loads((work/f'work_{no}/分段.json').read_text());add('all-actual-producer-gain-groups-times-and-cuts-metadata-bound',canonical(groups)==p['approved_producer_segments_sha256'],actual_sha256=canonical(groups))
  cache=work.parent/'tts/cache_tts';cache_records=[]
  for row in p['private_original_cache_identity_files']:
   path=cache/row['name'];measured=sha(path)if path.is_file()else None;cache_records.append({'name':row['name'],'actual_SHA256':measured});add('exact-original-private-cache-input:'+row['name'],measured==row['SHA256'])
  report['private_cache_identity_scalars']=cache_records
  info=json.loads(capture(['ffprobe','-v','error','-show_streams','-of','json',args.canonical_video]));audio=[s for s in info['streams']if s['codec_type']=='audio'];video=[s for s in info['streams']if s['codec_type']=='video'];add('original-public-AAC-mono-48k-clock',len(audio)==1 and audio[0]['codec_name']=='aac'and int(audio[0]['sample_rate'])==SR and int(audio[0]['channels'])==1)
  if not args.diagnostic:add('actual-canonical-4K-video-present',len(video)==1 and(video[0]['width'],video[0]['height'])==(3840,2160))
  decoded=U.decode(args.canonical_video);add('actual-no-clipping-or-nonfinite-samples',nonclipped(decoded),sample_peak_dbfs=float(20*np.log10(np.max(abs(decoded))+1e-30)))
  _,old_global,oldlog=U.r128(args.accepted_source);moments,new_global,newlog=U.r128(args.canonical_video);(output.parent/f'{no}-controlled-current-r128.log').write_text(newlog);(output.parent/f'{no}-controlled-prior-r128.log').write_text(oldlog);report.update(accepted_global=old_global,actual_global=new_global);add('actual-true-peak-below-zero',new_global['true_peak_dbtp']<0,actual_dbtp=new_global['true_peak_dbtp']);add('original-controlled-whole-track-level-difference-limit',abs(new_global['integrated_lufs']-old_global['integrated_lufs'])<=p['original_thresholds']['whole_track_delta_LU'],delta_lu=new_global['integrated_lufs']-old_global['integrated_lufs'])
  tools=Path(args.tools or HERE.parents[1]/'视频/工具').resolve()
  for name,want in p['original_tool_sha256'].items():assert sha(tools/name)==want,'Pinned original tool differs: '+name
  sys.path.insert(0,str(tools));R=module('响度一致性核对',tools/'响度一致性核对.py');R.FF='ffmpeg';Q=module('controlled_spoken_original_health_'+no,tools/'音频体检.py')
  with directory(work):
   samples=R.pcm(str(Path(args.canonical_video).resolve()));TM=R.momentary(str(Path(args.canonical_video).resolve()));metrics=Q.指标(samples,no);base=json.loads((tools/'音频体检基准.json').read_text());notes=[];bad=Q.超限(metrics,base,Q.确认(no),notes)
   with tempfile.TemporaryDirectory(prefix='controlled-spoken-original-R-')as td:
    alias=Path(td)/f'{no}.mp4';alias.symlink_to(Path(args.canonical_video).resolve());I,segs,levels,rbad,summary=R.check(str(alias),samples)
   inside=R.句内(str(Path(args.canonical_video).resolve()),samples,TM,str(work/f'work_{no}/分段.json'));ibad=R.句内报(inside)
  add('all-eight-unchanged-original-health-rules',not bad,metrics=metrics,failures=bad,original_confirmation_notes=notes);add('unchanged-original-whole-sentence-R-rule',not rbad,failures=rbad,summary=summary);add('unchanged-original-within-sentence-R-rule',not ibad,comparisons=inside,failures=ibad)
  report['original_full_track_supplement']={'metrics':metrics,'global_lufs':I,'sentence_lufs':levels,'summary':summary,'suppressed_segment_rule_not_added':True,'official_original_ASR_gates_separate':True}
  mutations=runtime_mutation_tests(actual,p,fp,raw_bytes,decoded);add('actual-runtime-positive-and-one-byte-control-clipping-negatives',all(v for k,v in mutations.items()if k not in('mutated_audio_written','ASR_simulated')),**mutations)
  report['approved_audio_repair_scope']={'source_id':no,'approved_new_S15_mother_sentences':p['approved_new_mother_sentences'],'approved_gain_only_sentences':p['approved_gain_only_sentences'],'only_voice_changed_sentences':p['approved_voice_changed_sentences'],'non_target_title_and_body_pre_master_identity_count':len(p['non_target_pre_master_identity']),'non_target_pre_master_identity_basis':'current57 actual four restored ranges and title+13 exact proper295 arrays, with independently validated prior proper295/old4f diagnostic provenance, plus runtime entire current513d RAW/AAC identity','master_multiplier_before':p['actual_master_multiplier_before'],'master_multiplier_after':p['actual_master_multiplier_after'],'ASR_confirmations_not_renewed_by_this_helper':True,'old_new_whole_duration_AAC_packets_or_new_mother_pitch_not_claimed_equal':True}
  report['comparison_before_is_formally_accepted_whole']=False;report['comparison_before_role']='current513d scalar proof and proper295 physical-reference chain; older4f remains diagnostic, not formalaccepted legacy';report['legacy_accepted_source_role']='exact wrapper accepted-videos48 input and measured whole-level reference only';report['legacy_accepted_file_not_falsely_used_for_16sentence_premaster_identity']=True;report['accepted_AAC_is_intentionally_different_after_approved_new_mothers']=True;report['passed']=bool(checks)and all(x['passed']for x in checks);report['repair_applied']=report['passed'];report['production_delivery_eligible']=report['passed']and not args.diagnostic
 except BaseException as exc:report['error']={'type':type(exc).__name__,'detail':str(exc)}
 report['checks']=checks;output.write_text(json.dumps(safe(report),ensure_ascii=False,indent=2)+'\n');return 0 if report['passed']else 1

if __name__=='__main__':
 default='48';parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--article',default=default)
 for name in ['accepted-source','canonical-video','work','request','output']:parser.add_argument('--'+name,required=True)
 for name in ['actual-source','raw-pcm','tools','reference','numeric-utilities','official-status']:parser.add_argument('--'+name)
 parser.add_argument('--diagnostic',action='store_true');sys.exit(audit(parser.parse_args()))
