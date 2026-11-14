"""Original cached mother/functions in memory only; compare two real source controls."""
import pathlib,json,importlib.util,hashlib,re,numpy as np,sys,types
from scipy import signal
B=pathlib.Path(__file__).parent;A=pathlib.Path('/workspace/work/video-audit70-20261113/ready41-monitor/02-artifact');req=pathlib.Path('/workspace/work/video-revision-batch-ci/.github/video-revision-batch/request/02/视频/脚本/02.json');old=json.loads(req.read_text());current=json.loads((A/'02-failed-working-source.json').read_text());spec=importlib.util.spec_from_file_location('strict_original_readonly',B.parent/'audio-a21-15-17-18-30-readonly/reproduce_a21_cache_only.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
assert hashlib.sha256(m.source.encode()).hexdigest()=='4c85e1fbdd2e82c5646d5f58df63c85eca60af4ef521f1d36f765575a568d6f3'
def build(d):
 ns,text=m.scope_for(d,14);raw,sr=ns['k'].create(ns['spoken'](text),voice=ns['V'],speed=ns['SPEED'],lang='en-us');w=ns['clean_tail'](raw);w=ns['_keep_tail'](raw,w,ns['_head_offset'](raw,w));out,starts,tmap,last=m.sentence(ns,text)
 return ns,text,raw,w,out,last,tmap
n0,text,raw,w,a,lastold,told=build(old);n1,_,raw2,w2,b,lastnew,tnew=build(current);assert np.array_equal(raw,raw2) and np.array_equal(w,w2)
for doc in (old,current):
 if doc.get('区间声音指纹',{}).get('S14'):assert hashlib.md5(w.tobytes()).hexdigest()[:12]==doc['区间声音指纹']['S14']
start=round(4.183958*24000);end=round(4.275*24000);F=120;ref=np.sqrt(np.mean(w[:len(w)//F*F].astype(float).reshape(-1,F)**2,axis=1)).max();frames=[]
for q in np.arange(4.10,4.29,.005):
 p=round(q*24000);x=w[p:p+F].astype(float)
 if len(x)<F:break
 window=x*np.hanning(len(x));freq=np.fft.rfftfreq(len(x),1/24000);power=np.abs(np.fft.rfft(window))**2
 long=w[max(0,p-180):p+300].astype(float);longwin=long*np.hanning(len(long));fl=np.fft.rfftfreq(len(long),1/24000);po=np.abs(np.fft.rfft(longwin))**2
 autoc=signal.correlate(long,long,'full',method='fft')[len(long)-1:];lo=round(24000/350);hi=min(len(autoc),round(24000/60));idx=lo+int(np.argmax(autoc[lo:hi]))
 band=lambda lo,hi:float(10*np.log10((po[(fl>=lo)&(fl<hi)].sum()+1e-30)/(po.sum()+1e-30)))
 frames.append({'w_time_s':round(float(q),4),'relative_RMS5_dB':float(20*np.log10(np.sqrt(np.mean(x*x))/(ref+1e-30)+1e-30)),'centroid_5ms_Hz':float((freq*power).sum()/(power.sum()+1e-30)),'periodicity_20ms':float(autoc[idx]/(autoc[0]+1e-30)),'best_period_F0_Hz':float(24000/idx),'under150Hz_fraction_dB':band(0,150),'3000to12000Hz_fraction_dB':band(3000,12000)})
# Pure source A/B differ only in this extra NV interval for S14.
first=np.flatnonzero(a[:min(len(a),len(b))]!=b[:min(len(a),len(b))]);prefix=int(first[0]) if len(first) else min(len(a),len(b));meta=json.loads((A/'02-reference-gain-diagnostic.json').read_text())['public_producer_timing_metadata'];native=meta['segments']['S14'];nativeStart=native[0]['时刻'][0];head=lastold['head'];assert head==lastnew['head'];segmap=[]
for label,last in [('old',lastold),('new',lastnew)]:
 for ws,we,t0,rm in last['segs']:
  if ws<=start<we:
   q=start-ws;q-=sum(min(q,y)-x for x,y in rm if x<q);sec=t0+q/24000;segmap.append({'mode':label,'w_extra_NV_start':start/24000,'producer_start_s':nativeStart+sec,'sentence_offset_s':sec,'original_raw_sample_interval_s':[(start+head)/24000,(end+head)/24000]})
# Compare old/current only in memory and serialize scalar hashes/timing.
proof={'kind':'02-S14-original-raw-mother-and-source-only-ablation','quality_acceptance':False,'original_maker_SHA256':hashlib.sha256(m.source.encode()).hexdigest(),'original_clean_SHA256':hashlib.sha256(m.clean.encode()).hexdigest(),'raw_mother_manifest':list(m.cache_rows.values()),'original_raw_mother_same_between_both_source_modes':True,'original_timed_phonemes_near_last_word':[{'phoneme':x.phoneme,'raw_start_s':x.start*lastold['scale'],'raw_end_s':x.end*lastold['scale'],'clean_w_start_s':x.start*lastold['scale']-lastold['head']/24000,'clean_w_end_s':x.end*lastold['scale']-lastold['head']/24000} for x in lastold['toks'] if x.start*lastold['scale']>3.5],'pre_interval_processed_w_same':True,'pre_interval_w_fp':hashlib.md5(w.tobytes()).hexdigest()[:12],'old_current_NV':{'old':old['非人声区间']['S14'],'current':current['非人声区间']['S14']},'w_candidate_removed_start_end_sample':[start,end],'w_candidate_removed_samples':end-start,'w_candidate_removed_duration_s':(end-start)/24000,'w_candidate_removed_fullSHA256':hashlib.sha256(w[start:end].tobytes()).hexdigest(),'w_candidate_removed_rms_relative_dB':float(20*np.log10(np.sqrt(np.mean(w[start:end].astype(float)**2))/(ref+1e-30)+1e-30)),'original_clean_head_samples':head,'original_sentence_only_sample_counts':[len(a),len(b)],'original_sentence_only_duration_delta_s':(len(b)-len(a))/24000,'old_S14_output_SHA256':hashlib.sha256(a.tobytes()).hexdigest(),'current_S14_output_SHA256':hashlib.sha256(b.tobytes()).hexdigest(),'complete_unchanged_sentence_prefix_samples':prefix,'complete_unchanged_sentence_prefix_seconds':prefix/24000,'old_LAST_public_scalar':{k:lastold[k] for k in ['head','segs','total','cuts','grafts','gaps','hs']},'current_LAST_public_scalar':{k:lastnew[k] for k in ['head','segs','total','cuts','grafts','gaps','hs']},'native_actual_S14_segment_timings':native,'w_to_current_producer_scalar_map':segmap,'5ms_raw_mother_frames_w4p10_to4p29':frames,'existing_original_confirmations':{k:v for k,v in old['核对确认']['非人声'].items() if 'S14' in v.get('依据','')},'native_actual_raw_mother_hashes':[],'private_waveforms_GT_pickle_or_model_bytes_exported':False}
prep=json.loads((A/'02-checker-reference-preparation.json').read_text());
for x in prep['raw_mother_cache_scalar_manifest']:
 if any(z['sentence']=='S14' and z['reference_kind']=='whole-default-raw' for z in x['input_proofs']):
  matching=next(y for y in m.cache_rows.values() if y['key']==x['exact_native_cache_key']);assert x['pkl_sha256']==matching['pkl_full_sha256'];proof['native_actual_raw_mother_hashes'].append({'key':x['exact_native_cache_key'],'native_pkl_SHA256':x['pkl_sha256'],'pinned_original_pkl_SHA256':matching['pkl_full_sha256'],'match':True})
(B/'02-S14-original-cache-ablation-proof.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2,default=lambda x:float(x) if isinstance(x,np.floating) else int(x))+'\n')
print(json.dumps({'old_new_sentence_seconds':[len(a)/24000,len(b)/24000],'delta':proof['original_sentence_only_duration_delta_s'],'first_diff_sentence_s':prefix/24000,'head':head,'removed_interval_s':proof['w_to_current_producer_scalar_map'],'rawfp':proof['pre_interval_w_fp'],'native_mother_same':proof['native_actual_raw_mother_hashes']},ensure_ascii=False))
