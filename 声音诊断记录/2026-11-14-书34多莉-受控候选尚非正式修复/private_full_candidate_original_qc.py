"""Root-authorized private whole-cache candidate, exact original functions/gates.

Only source control leaf S15/2/0 differs in memory. No TTS, accepted source,
program or released media writes. Private PCM/AAC are deleted on exit.
"""
from pathlib import Path
import json,hashlib,tempfile,copy,subprocess,importlib.util,re,sys,traceback
import numpy as np,soundfile as sf
OUT=Path('/workspace/work/dolly62-audio-user-review-20261114')
defs=OUT/'inspect_actual_junction.py'
exec(compile(defs.read_text().split('\nwith tempfile.TemporaryDirectory')[0],str(defs)+'#definitions-only','exec'))
T=Path('/workspace/work/audit-repo/视频/工具');sys.path.insert(0,str(T))
spec=importlib.util.spec_from_file_location('original62_candidate_health',T/'音频体检.py');Q=importlib.util.module_from_spec(spec);spec.loader.exec_module(Q);R=Q.R
texts=[d['title_en']]+[' '.join(re.sub(r'\{\{.*?\}\}|\*\*','',c['en'])for c in s['chunks'])for s in d['sentences']]
Q.文本=lambda no:texts
baseline_thresholds=json.loads((T/'音频体检基准.json').read_text())
mp=Path('/workspace/work/video-audit70-20261113/next-passed-native/43543967031/62/62-4K-正文后插图2秒-简述2秒.mp4')
sha=lambda x:hashlib.sha256(x).hexdigest()
def run(cmd,**kw):return subprocess.run(cmd,capture_output=True,check=True,**kw)
def decode(path,sr=48000):return np.frombuffer(run([r.FF,'-v','error','-nostdin','-i',str(path),'-vn','-ac','1','-ar',str(sr),'-f','f32le','-']).stdout,np.float32)
def adts(path):return run(['ffmpeg','-v','error','-nostdin','-i',str(path),'-map','0:a:0','-c:a','copy','-f','adts','-']).stdout
def packets(raw):
 out=[];i=0
 while i<len(raw):
  assert raw[i]==255 and raw[i+1]&240==240
  n=((raw[i+3]&3)<<11)|(raw[i+4]<<3)|(raw[i+5]>>5);assert n>7 and i+n<=len(raw)
  out.append(raw[i:i+n]);i+=n
 assert i==len(raw)
 return out
def stream(path):
 return json.loads(run(['ffprobe','-v','error','-select_streams','a:0','-show_entries','stream=codec_name,sample_rate,channels,channel_layout,start_time,duration,nb_frames,bit_rate','-of','json',str(path)],text=True).stdout)['streams'][0]
def health(path):
 a=Q.读(str(path));notes=[];met=Q.指标(a,'62');bad=Q.超限(met,baseline_thresholds,d.get('核对确认',{}).get('句首突起',{}),notes)
 I,segs,lev,rbad,summ=R.check(str(path),a)
 tm=R.momentary(str(path));groups={f'S{i}':[{'时刻':[st/R.SR,en/R.SR]}]for i,(st,en)in enumerate(Q.句段(a)[1:],1)}
 # Original function wants a JSON path; this private scalar-only file also leaves /dev/shm.
 gp=Path(path).parent/'private-original-gate-segments.json';gp.write_text(json.dumps(groups,ensure_ascii=False))
 ins=R.句内(str(path),a,tm,str(gp));ib=R.句内报(ins)
 return {'eight_original_metrics':met,'eight_original_failures':bad,'confirmation_notes':notes,'original_R_integrated_lufs':I,'original_R_sentence_spans':segs,'original_R_sentence_lufs':lev,'original_R_whole_sentence_failures':rbad,'original_R_summary':summ,'original_within_sentence_comparisons':ins,'original_within_sentence_failures':ib,'title_plus_sentence_count':len(Q.句段(a)),'clipped_sample_count':int(np.sum(np.abs(a)>=1))}
report={'kind':'root-authorized-private-full62-original-cache-candidate-original-QC','root_authorized_one_leaf':{'path':'停顿插入点.S15.2[0]','from':3.580083,'to':3.584083},'new_TTS':False,'formal_source_or_GEN_DSP_programs_or_accepted_media_modified':False,'candidate_native_acceptance_or_human_listening_not_claimed':True}
try:
 with tempfile.TemporaryDirectory(prefix='private62-full-candidate-',dir='/dev/shm')as td:
  td=Path(td);cache=td/'cache';cache.mkdir()
  original,original_parts=r.build(d,cache)
  baselinewav=td/'baseline.wav';sf.write(baselinewav,original,24000)
  assert sha(baselinewav.read_bytes())==bind['reconstructed_pcm_sha256']
  candidate_source=copy.deepcopy(d);candidate_source['停顿插入点']['S15']['2'][0]=3.584083
  restored=copy.deepcopy(candidate_source);restored['停顿插入点']['S15']['2'][0]=3.580083;assert restored==d
  candidate,candidate_parts=r.build(candidate_source,cache)
  wav=td/'62.wav';aac=td/'62.m4a';sf.write(wav,candidate,24000)
  original16=sf.read(baselinewav,dtype='int16')[0];candidate16=sf.read(wav,dtype='int16')[0]
  assert len(candidate)==len(original) and len(candidate16)==len(original16)
  dif=np.flatnonzero(original!=candidate);dif16=np.flatnonzero(original16!=candidate16)
  support=[int(dif[0]),int(dif[-1])+1];s15=next(x for x in candidate_parts if x['sentence']=='S15');old15=next(x for x in original_parts if x['sentence']=='S15')
  other=[{'sentence':a['sentence'],'array_SHA_unchanged':a['pre_normalized_array_SHA256']==b['pre_normalized_array_SHA256'],'start_s_unchanged':a['start_s']==b['start_s'],'end_s_unchanged':a['end_s']==b['end_s']}for a,b in zip(original_parts,candidate_parts) if a['sentence']!='S15'];assert all(all(v for k,v in row.items()if k!='sentence')for row in other)
  lo=round((old15['start_s']+old15['LAST_scalar_timing']['segs'][1][2]+(old15['LAST_scalar_timing']['cuts'][1][0]-old15['LAST_scalar_timing']['segs'][1][0])/fs-.04)*fs)
  hi=round((old15['start_s']+old15['LAST_scalar_timing']['segs'][2][2]+.04)*fs)
  outside=np.array_equal(original[:lo],candidate[:lo])and np.array_equal(original[hi:],candidate[hi:]);assert outside
  run([r.FF,'-y','-v','error','-nostdin','-i',str(wav),'-af',r.AF,'-c:a','aac','-b:a','256k','-movflags','+faststart',str(aac)])
  oa=adts(mp);ca=adts(aac);assert sha(oa)==bind['reconstructed_AAC_sha256'];op=packets(oa);cp=packets(ca);assert len(op)==len(cp)
  changed_packets=[i for i,(a,b)in enumerate(zip(op,cp))if a!=b]
  pts=json.loads(run(['ffprobe','-v','error','-select_streams','a:0','-show_entries','packet=pts_time,duration_time','-of','json',str(mp)],text=True).stdout)['packets'];assert len(pts)==len(op)
  actual=decode(mp);encoded=decode(aac);assert len(actual)==len(encoded)
  ed=np.flatnonzero(actual!=encoded);same_before_after=(np.array_equal(actual[:round(112.9*48000)],encoded[:round(112.9*48000)])and np.array_equal(actual[round(114.3*48000):],encoded[round(114.3*48000):]))
  # Native codec/AF may spread a local input edit across nearby transform frames.
  # Record actual difference support instead of assuming an arbitrary bound.
  encoded_support=[float(ed[0]/48000),float((ed[-1]+1)/48000)] if len(ed) else None
  h=health(aac)
  eb=run([r.FF,'-v','info','-nostats','-i',str(aac),'-vn','-af','ebur128=peak=true','-f','null','-'],text=True).stderr;eb=eb[eb.rfind('Summary:'):].strip()
  f_lo=round(113.8575*48000);f_hi=round(113.8675*48000)
  local_features={'f_estimated_10ms_public_clock_s':[113.8575,113.8675],'baseline_rms_dbfs':rmsdb(actual[f_lo:f_hi]),'candidate_rms_dbfs':rmsdb(encoded[f_lo:f_hi]),'delta_db':rmsdb(encoded[f_lo:f_hi])-rmsdb(actual[f_lo:f_hi])}
  f0={}
  try:
   import parselmouth
   aa=actual[round(113.9*48000):round(115.05*48000)];cc=encoded[round(113.9*48000):round(115.05*48000)]
   pa=parselmouth.Sound(aa,48000).to_pitch_ac(time_step=.01,pitch_floor=60,pitch_ceiling=450).selected_array['frequency'];pc=parselmouth.Sound(cc,48000).to_pitch_ac(time_step=.01,pitch_floor=60,pitch_ceiling=450).selected_array['frequency'];both=(pa>0)&(pc>0)
   f0={'public_clock_s':[113.9,115.05],'estimator':'Praat/parselmouth original-sample autocorrelation','same_voicing_frame_mask':np.array_equal(pa>0,pc>0),'joint_voiced_frames':int(both.sum()),'median_baseline_Hz':float(np.median(pa[both])),'median_candidate_Hz':float(np.median(pc[both])),'max_abs_F0_difference_Hz':float(np.max(np.abs(pc[both]-pa[both])))}
  except Exception as exc:f0={'not_available':str(exc)}
  report.update({'actual_baseline_identity':{'video_sha256':sha(mp.read_bytes()),'source_sha256':bind['source_sha256'],'WAV_sha256':sha(baselinewav.read_bytes()),'AAC_sha256':sha(oa),'source_maker_sha256':bind['original_maker_sha256']},'candidate_identity':{'in_memory_source_canonical_JSON_sha256':sha(json.dumps(candidate_source,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()),'WAV_sha256':sha(wav.read_bytes()),'WAV_bytes':wav.stat().st_size,'WAV_subtype':'PCM_16','sample_rate':24000,'AAC_ADTS_sha256':sha(ca),'AAC_ADTS_bytes':len(ca),'M4A_sha256':sha(aac.read_bytes()),'M4A_bytes':aac.stat().st_size,'candidate_raw_S15_array_SHA256':s15['pre_normalized_array_SHA256']},'one_source_leaf_only_proved_by_restore_equality':True,'source_change_is_insertion_boundary_not_deletion':{'original_cut_samples':[85922,85922],'candidate_cut_samples':[86018,86018],'samples_deleted_at_this_cut':0,'pause_samples':9600,'original_pause_s':.4,'candidate_pause_s':.4,'original_public_boundaries_s':[113.45008333333334,113.85008333333333],'candidate_public_boundaries_s':[113.45408333333334,113.85408333333333],'mother_samples_between_old_and_new_cut_reassigned_to_before_pause':96,'A42_original_cosine_fades_ms':8},'PCM_preservation':{'total_samples':len(original),'total_duration_s':len(original)/24000,'total_duration_and_samples_unchanged':True,'changed_float_samples_count':len(dif),'changed_float_sample_span':support,'changed_float_time_span_s':[x/24000 for x in support],'changed_PCM16_samples_count':len(dif16),'source_PCM_outside_local_window_sample_for_sample_exact':outside,'window_s':[lo/24000,hi/24000],'all_other_sentences':other,'S15_start_end_sample_count_unchanged':all(s15[k]==old15[k]for k in ['start_s','end_s','sample_count']),'S15_original_automatic_gain':old15['automatic_level'],'S15_candidate_automatic_gain':s15['automatic_level'],'S15_automatic_gain_unchanged':s15['automatic_level']==old15['automatic_level']},'codec_preservation':{'baseline_stream':stream(mp),'candidate_stream':stream(aac),'AAC_packet_count':len(op),'changed_packet_indices_0_based':changed_packets,'first_changed_packet':pts[changed_packets[0]],'last_changed_packet':pts[changed_packets[-1]],'public_decoded_samples_total':len(actual),'public_decoded_sample_count_unchanged':len(actual)==len(encoded),'public_decoded_changed_samples_count':len(ed),'public_decoded_change_support_s':encoded_support,'public_decoded_outside112_9to114_3_sample_for_sample_exact':same_before_after},'fresh_candidate_original_audio_health_and_levels':h,'candidate_ffmpeg_ebur128_summary':eb,'actual_public_estimated_f_start_comparison':local_features,'voiced_four_phrase_F0':f0,'ASR_status':{'fresh_local_candidate_ASR_run':False,'reason':'Original local ASR model files are unavailable; no model download or new native job was launched. Unchanged words/outside support are proved by exact original PCM, but this is not fresh ASR acceptance.','actual_baseline_native_original_ASR_and_other_original_audio_gates_passed_previously':True,'native_production_owner_must_run_unchanged_original_candidate_ASR_and_audio_gates':True},'private_WAV_AAC_mother_cache_removed_after_context':True,'candidate_formal_acceptance':False})
except BaseException as exc:
 report['diagnostic_execution_error']={'type':type(exc).__name__,'message':str(exc),'traceback':traceback.format_exc()}
(OUT/'private-full-candidate-original-QC.json').write_text(json.dumps(report,ensure_ascii=False,indent=2,default=lambda v:float(v)if isinstance(v,np.floating)else int(v)if isinstance(v,np.integer)else str(v))+'\n')
print(json.dumps({k:v for k,v in report.items()if k not in ['fresh_candidate_original_audio_health_and_levels']},ensure_ascii=False))
