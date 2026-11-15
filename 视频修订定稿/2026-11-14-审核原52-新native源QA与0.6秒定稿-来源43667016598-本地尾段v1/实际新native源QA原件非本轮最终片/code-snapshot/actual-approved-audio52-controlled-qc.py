#!/usr/bin/env python3
"""Exact source43/52 certified17 spoken-comma + approved gain supplement.

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

def legacy_evidence_valid(e,p):
 if not(e.get('passed')is True and e.get('diagnostic_only')is True and e.get('formal_audio_or_video_accepted')is False and e.get('new_model_inference')is False):return False
 case=next((x for x in e['cases']if str(x['source_id'])==p['article']),None)
 if not case:return False
 b,c=case['baseline'],case['candidate'];outside=c['all_title_and_non_target_pre_master_PCM_exact'];allowed=set(p['approved_voice_changed_sentences']);want=({'title'}|{f'S{i}'for i in range(1,p['body_sentence_count']+1)})-allowed
 if not(b.get('actual_current_native_WAV_AAC_double_bound')is True and b['AAC_ADTS_sha256']==p['fingerprints']['accepted_AAC_ADTS_sha256']and c['raw_WAV_sha256']==p['fingerprints']['actual_raw_WAV_sha256']and c['AAC_ADTS_sha256']==p['fingerprints']['canonical_AAC_ADTS_sha256']):return False
 if not(b['master_ideal_multiplier']==c['master_ideal_multiplier']==p['actual_master_multiplier_after']==p['actual_master_multiplier_before']and set(outside)==want and outside==p['non_target_pre_master_identity']):return False
 if not all(x['same_samples']and x['array_equal']and x['old_SHA256']==x['new_SHA256']for x in outside.values()):return False
 if set(c['only_authorized_changed_sentence_pre_master_PCM'])!=allowed:return False
 for sid in p['approved_gain_only_sentences']:
  if not(b['sentence_pre_master_records'][sid]['before_gain_float32_SHA256']==c['sentence_pre_master_records'][sid]['before_gain_float32_SHA256']==p['gain_only_pre_gain_identity'][sid]):return False
 return canonical(c['actual_segment_record'])==p['approved_producer_segments_sha256']

def evidence_valid(e,p):
 if p['article']!='52' or 'bridge_selected_whole_file'not in p:return legacy_evidence_valid(e,p)
 def pinned(file_key,hash_key):
  path=HERE/p[file_key]
  if sha(path)!=p[hash_key]:raise ValueError('Exact52 stage evidence bytes changed: '+file_key)
  return json.loads(path.read_text())
 old=pinned('bridge_stage0_original_profile_file','bridge_stage0_original_profile_SHA256')
 if not legacy_evidence_valid(e,old):return False
 n=pinned('bridge_selected_whole_file','bridge_selected_whole_SHA256');v=pinned('bridge_two_NV_reference_file','bridge_two_NV_reference_SHA256');edge=pinned('bridge_selected_edge_file','bridge_selected_edge_SHA256')
 physical=pinned('bridge_physical_source_file','bridge_physical_source_SHA256');stage0=pinned('bridge_stage0_request_file','bridge_stage0_request_SHA256')
 if not(n.get('completed')is True and n.get('diagnostic_only')is True and n.get('formal_audio_or_video_accepted')is False and n.get('production_delivery_eligible')is False and n.get('whole_build_count')==1 and n.get('baseline_rebuilt')is False and n.get('new_model_inference')is False and n.get('new_G36_math_or_cache')is False and n.get('production_source_or_CF_written')is False):return False
 if not(n['program_SHA256']=='ab05e41a86a0fe191a4efb26c9aab85fbc0db732bf0da8ee627f63437dd0cd0a'and n['reference_SHA256']=='294572fb87cb35e6de21c2603059bf68f9b004a9bdb2f3101cee9e725dbfdc65'and n['actual_private_candidate_source_SHA256']==p['bridge_physical_source_SHA256']):return False
 if not(n['all_private_cache_stats_and_keys_unchanged']and n['all_models_byte_exact_after']and n['all_input_and_tools_byte_exact_after']and n['original_Q8_R_withinR']['completed']and n['original_Q8_R_withinR']['all_passed']):return False
 if not(n['actual_PV_total_scan_count']==n['actual_PV_unconfirmed_count']==19 and n['known_historical_float_differences']==['S3','S5','S6']):return False
 if not(n['whole_RAW']['SHA256']==p['fingerprints']['actual_raw_WAV_sha256']and n['whole_AAC']['ADTS_SHA256']==p['fingerprints']['canonical_AAC_ADTS_sha256']and n['whole_RAW']['md5_first12']==p['exact_selected_final_whole_fp']and n['whole_AAC']['packet_count']==p['exact_selected_final_AAC_packet_count']):return False
 if not(n['actual_master_pre_peak']==.8474143147468567 and p['actual_master_multiplier_before']==p['actual_master_multiplier_after']==old['actual_master_multiplier_after']):return False
 if canonical(n['actual_segment_clock'])!=p['approved_producer_segments_sha256']:return False
 if not(n['title_and_S1_S17_pre_master_exact_to_explicit_original_producer_phase']and n['all_S1_S17_before_gain_clip_tmap_rawfp_and_effective_gains_exact_to_555']and len(n['S1_S17_actual_quantized_sentence_proof'])==17):return False
 last=v['cases'][-1]
 for sid in [f'S{k}'for k in range(1,18)]:
  x=n['S1_S17_actual_quantized_sentence_proof'][sid]
  if not(x['equals_actual555_final_case']and x['quantized_float64_SHA256']==last['old_to_current_actual_sentence_PCM_identity'][sid]['new_quantized_float64_sha256']and n['actual_segment_clock'][sid]==last['actual_segment_clock'][sid]):return False
 selected=next(x for x in edge['cases']if x['stage']=='conservative_first_zero')
 if not(n['sentence_records']['S18']['pre_master_float32_SHA256']==n['sentence_records']['S18']['before_gain_float32_SHA256']==selected['processed_float32_sha256']=='01047eb79caeac42caa17a23d1c03d0c38c37bfc26711fa370760f3de8ff20ab'and n['sentence_records']['S18']['samples']==selected['processed_samples']==129240 and selected['disputed_2p710_to2p7125_original_peak_final_processed_samples_exact']):return False
 nv={'S4':[[4.985,5.2185,'紧贴词头']],'S18':[[2.7125,3.015,'紧贴词尾']]};want=copy.deepcopy(stage0)
 for sid in nv:want.setdefault('非人声区间',{})[sid]=nv[sid];want.setdefault('区间声音指纹',{})[sid]=p['selected_newmother_NV_pins'][sid]
 if physical!=want or n['actual_candidate_NV']!=nv:return False
 if p['approved_audio_controls']!={k:physical.get(k)for k in old['approved_audio_controls']}:return False
 if canonical({k:v for k,v in physical.items()if k not in p['review_only_top_level_keys']})!=p['approved_nonreview_document_sha256']:return False
 if not(p['fingerprints']['accepted_video_sha256']==old['fingerprints']['accepted_video_sha256']and p['fingerprints']['accepted_AAC_ADTS_sha256']==old['fingerprints']['accepted_AAC_ADTS_sha256']):return False
 return True

def runtime_mutation_tests(actual,p,fp,raw_bytes,decoded):
 wrong=copy.deepcopy(actual);sid=p['approved_gain_only_sentences'][0];piece=next(iter(wrong['分段增益dB'][sid]));wrong['分段增益dB'][sid][piece]=0.
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
  profile_path=Path(args.reference or HERE/f'audio{no}-controlled-qc-reference.json');p=json.loads(profile_path.read_text());report['reference_file_sha256']=sha(profile_path);assert no==p['article']and no in('43','52')and p['enabled']is True
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
   if no=='52':add(label+'-new-S18-no-ENDING-and-only-selected-measured-NV',not data.get('结尾句',{}).get('S18')and not data.get('停顿插入点',{}).get('S18')and data.get('非人声区间',{}).get('S18')==[[2.7125,3.015,'紧贴词尾']]and{sid:data.get('区间声音指纹',{}).get(sid)for sid in ['S4','S18']}==p['selected_newmother_NV_pins'])
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
  report['approved_audio_repair_scope']={'source_id':no,'spoken_comma_new_mother_sentences':p['approved_new_mother_sentences'],'approved_gain_only_sentences':p['approved_gain_only_sentences'],'only_voice_changed_sentences':p['approved_voice_changed_sentences'],'non_target_title_and_body_pre_master_identity_count':len(p['non_target_pre_master_identity']),'non_target_pre_master_identity_basis':'actual-native-whole-track-diagnostic exact arrays plus this runtime entire new RAW/AAC cryptographic identity','master_multiplier_before':p['actual_master_multiplier_before'],'master_multiplier_after':p['actual_master_multiplier_after'],'ASR_confirmations_not_renewed_by_this_helper':True,'old_new_whole_duration_AAC_packets_or_new_mother_pitch_not_claimed_equal':True}
  report['comparison_before_is_formally_accepted_whole']=True;report['accepted_AAC_is_intentionally_different_after_approved_new_mothers']=True;report['passed']=bool(checks)and all(x['passed']for x in checks);report['repair_applied']=report['passed'];report['production_delivery_eligible']=report['passed']and not args.diagnostic
 except BaseException as exc:report['error']={'type':type(exc).__name__,'detail':str(exc)}
 report['checks']=checks;output.write_text(json.dumps(safe(report),ensure_ascii=False,indent=2)+'\n');return 0 if report['passed']else 1

if __name__=='__main__':
 default=(re.search(r'audio(43|52)-controlled-qc',Path(__file__).name).group(1)if re.search(r'audio(43|52)-controlled-qc',Path(__file__).name)else'43');parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--article',default=default)
 for name in ['accepted-source','canonical-video','work','request','output']:parser.add_argument('--'+name,required=True)
 for name in ['actual-source','raw-pcm','tools','reference','numeric-utilities','official-status']:parser.add_argument('--'+name)
 parser.add_argument('--diagnostic',action='store_true');sys.exit(audit(parser.parse_args()))
