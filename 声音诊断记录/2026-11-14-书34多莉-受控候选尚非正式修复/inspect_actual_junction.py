"""Exact-source clones/four junction scalar diagnosis; no formal source/audio mutation."""
from pathlib import Path
import json,hashlib,tempfile,re,ast,copy,subprocess
import numpy as np
from scipy import signal
BASE=Path('/workspace/work/video-audit70-20261113');OUT=Path('/workspace/work/dolly62-audio-user-review-20261114')
probe=BASE/'audio-a21-actual-first-4K-20261114/probe_minimal_encoded_boost.py';ns={'__name__':'readonly62_junction','__file__':str(probe)};exec(compile(probe.read_text().split('\nfor no in sys.argv')[0],str(probe)+'#definitions-only','exec'),ns);r=ns['r'];bind=json.loads((OUT/'strict-original-cache-source-binding.json').read_text());assert bind['matches_actual_native_PCM'] and bind['matches_actual_accepted_AAC']
d=json.loads(Path(bind['source_file']).read_text());part=next(p for p in bind['parts']if p['sentence']=='S15');fs=24000

def rmsdb(x):return float(20*np.log10(np.sqrt(np.mean(np.asarray(x,float)**2))+1e-20))
def features(x):
 x=np.asarray(x,float);Y=np.abs(np.fft.rfft(x*np.hanning(len(x))))**2;f=np.fft.rfftfreq(len(x),1/fs);total=Y.sum()+1e-30
 return {'rms_dbfs':rmsdb(x),'peak_dbfs':float(20*np.log10(np.max(np.abs(x))+1e-20)),'centroid_hz':float((np.sqrt(Y)*f).sum()/(np.sqrt(Y).sum()+1e-30)),'energy_below800_ratio':float(Y[f<800].sum()/total),'energy_above4000_ratio':float(Y[f>4000].sum()/total)}
def build_one(data,cache):
 sc,txt=r.scope(data,15,cache);pieces=[];gaps=[];p0=0;listed=sc['list_commas'](txt)
 for mt in re.finditer(r'[,;:](?=\s)',txt):pieces.append((p0,mt.end()));p0=mt.end()+1;gaps.append(.2 if mt.start() in listed else .4)
 pieces.append((p0,len(txt)));clips,tm=sc['sentence_audio'](txt,pieces,gaps);clips,a,agn,pgn=sc['句增益'](data,data['no'],14,txt,pieces,gaps,clips,tm,np.concatenate(clips));return sc,txt,a,tm,agn
with tempfile.TemporaryDirectory(prefix='private62-junction-',dir='/dev/shm')as td:
 cache=Path(td)/'cache';cache.mkdir();sc,txt,a,tm,agn=build_one(d,cache);assert hashlib.sha256(a.tobytes()).hexdigest()==part['pre_normalized_array_SHA256']
 raw,_=sc['k'].create(sc['spoken'](txt),voice=sc['V'],speed=sc['SPEED'],lang='en-us');w=sc['clean_tail'](raw);assert hashlib.md5(np.ascontiguousarray(w).tobytes()).hexdigest()[:12]=='d0af91d053ec'
 mp=BASE/'next-passed-native/43543967031/62/62-4K-正文后插图2秒-简述2秒.mp4';b=subprocess.check_output([r.FF,'-v','error','-nostdin','-i',str(mp),'-vn','-ac','1','-ar',str(fs),'-f','f32le','-']);pub=np.frombuffer(b,np.float32)
 expected=round(part['start_s']*fs);margin=2400;target=pub[expected-margin:expected+len(a)+margin];cc=signal.correlate(target.astype(float),a.astype(float),mode='valid',method='fft');lag=int(np.argmax(cc))-margin
 toks=sc['LAST']['toks'];commas=[i for i,t in enumerate(toks)if t.phoneme==','];around=toks[max(0,commas[1]-10):commas[1]+10];tok=[{'phoneme':t.phoneme,'start_s':float(t.start),'end_s':float(t.end),'clean_mother_start_s':float(t.start*sc['LAST']['scale']-sc['LAST']['head']/fs),'clean_mother_end_s':float(t.end*sc['LAST']['scale']-sc['LAST']['head']/fs)}for t in around]
 frames=[]
 for t in np.arange(3.535,3.6276,.0025):
  x=w[round(t*fs):round((t+.005)*fs)];frames.append({'clean_mother_window_s':[round(float(t),6),round(float(t+.005),6)],**features(x)})
 # Existing source cut and exact clocks of the public AAC.
 cut=tm[1][3];nxt=tm[2][2];pubend=part['start_s']+lag/fs+cut;pubnext=part['start_s']+lag/fs+nxt
 actual=[]
 for label,start,stop in [('clones_tail',pubend-.04,pubend),('four_start',pubnext,pubnext+.04)]:
  for t in np.arange(start,stop-.004,.0025):actual.append({'region':label,'public_window_s':[float(t),float(t+.005)],**features(pub[round(t*fs):round((t+.005)*fs)])})
 candidates=[]
 for pos in [3.580083,3.5825,3.584083,3.585,3.587667]:
  dd=copy.deepcopy(d);dd['停顿插入点']['S15']['2']=[pos,'交界'];ss,tt,ca,ct,ag=build_one(dd,cache)
  changed=np.flatnonzero(a!=ca)if len(a)==len(ca)else np.array([],dtype=int)
  row={'proposed_cut_clean_mother_s':pos,'source_control_only_delta':'/停顿插入点/S15/2/0','sample_count_same':len(a)==len(ca),'automatic_level_original':agn,'automatic_level_candidate':ag,'automatic_gains_unchanged':agn==ag,'changed_processed_sentence_sample_span':None if not len(changed)else[int(changed[0]),int(changed[-1]+1)],'changed_processed_sentence_span_s':None if not len(changed)else[float(changed[0]/fs),float((changed[-1]+1)/fs)],'clones_to_four_standard_pause_s':ct[2][2]-ct[1][3],'first_postpause_10ms':features(ca[round(ct[2][2]*fs):round((ct[2][2]+.01)*fs)]),'last_prepause_10ms':features(ca[round((ct[1][3]-.01)*fs):round(ct[1][3]*fs)]),'private_candidate_array_sha256':hashlib.sha256(ca.tobytes()).hexdigest(),'private_audio_exported':False}
  # Compare native unchanged samples outside a 0.50s target junction window.
  lo=round((cut-.04)*fs);hi=round((nxt+.04)*fs)
  row['all_samples_outside_local_junction_unchanged']=len(a)==len(ca)and np.array_equal(a[:lo],ca[:lo])and np.array_equal(a[hi:],ca[hi:])
  candidates.append(row)
 report={'kind':'bound-actual62-S15-clones-four-junction-diagnostic-and-private-original-function-cutpoint-candidates','video_sha256':hashlib.sha256(mp.read_bytes()).hexdigest(),'source_sha256':bind['source_sha256'],'actual_original_PCM_and_AAC_binding_passed':True,'sentence':part,'actual_native_tmap':tm,'actual_native_automatic_gain':agn,'actual_public_alignment_lag_samples_24k':lag,'actual_public_alignment_lag_s':lag/fs,'actual_public_clones_end_s':pubend,'actual_public_four_start_s':pubnext,'actual_public_gap_s':pubnext-pubend,'existing_cut_clean_mother_s':d['停顿插入点']['S15']['2'][0],'source_timed_phonemes_around_second_comma':tok,'mother_fricative_junction_5ms_frames_stride2_5ms':frames,'actual_public_junction_5ms_frames_stride2_5ms':actual,'private_minimal_cutpoint_candidates':candidates,'original_A42_fades_ms':8,'source_or_approved_audio_modified':False,'new_TTS_inference':False,'candidate_new_audio_not_accepted_or_delivered':True,'private_waveforms_cache_GT_not_exported':True}
 (OUT/'S15-clones-four-junction-diagnostic.json').write_text(json.dumps(report,ensure_ascii=False,indent=2,default=lambda v:float(v)if isinstance(v,np.floating)else int(v))+'\n')
 print(json.dumps({k:v for k,v in report.items()if k in ['actual_public_clones_end_s','actual_public_four_start_s','actual_public_gap_s','existing_cut_clean_mother_s','actual_native_automatic_gain','actual_public_alignment_lag_s','private_minimal_cutpoint_candidates','source_timed_phonemes_around_second_comma']},ensure_ascii=False))
