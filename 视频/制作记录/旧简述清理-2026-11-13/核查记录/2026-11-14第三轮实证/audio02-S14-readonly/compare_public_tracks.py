import pathlib,json,hashlib,subprocess,numpy as np
from scipy import signal
B=pathlib.Path(__file__).parent;SR=48000
D=lambda p:np.frombuffer(subprocess.check_output(['ffmpeg','-v','error','-nostdin','-i',str(p),'-map','0:a:0','-vn','-ac','1','-ar',str(SR),'-f','f32le','-']),np.float32)
a=D(B/'02-accepted-public.mp4');b=D(B/'02-current-failed-public.mp4')
def fit(x,y):
 x=x.astype(float);y=y.astype(float);g=float(x@y/(x@x+1e-30));e=y-g*x
 return {'gain_dB':float(20*np.log10(max(g,1e-30))),'NCC':float(x@y/(np.linalg.norm(x)*np.linalg.norm(y)+1e-30)),'gain_compensated_residual_SNR_dB':float(10*np.log10((np.mean((g*x)**2)+1e-30)/(np.mean(e*e)+1e-30))),'np_array_equal':bool(np.array_equal(x,y)),'different_samples':int(np.count_nonzero(x!=y)),'max_abs_difference':float(np.max(abs(x-y))),'old_SHA256':hashlib.sha256(np.asarray(x,np.float32).tobytes()).hexdigest(),'current_SHA256':hashlib.sha256(np.asarray(y,np.float32).tobytes()).hexdigest(),'samples':len(x)}
rows=[]
for st,en in [(1,2),(10,11),(40,41),(90,91),(114.8,115.5),(117,117.6),(118.1,118.6),(119.9,120.4),(121,122),(125,126),(130,131),(134,135),(138.5,139.5)]:
 lo=round(st*SR);hi=round(en*SR);m=round(.3*SR);t=a[lo:hi];search=b[lo-m:min(len(b),hi+m)];c=signal.correlate(search,t,'valid',method='fft');index=int(np.argmax(c));lag=index-m;segment=search[index:index+len(t)];rows.append({'accepted_span_s':[st,en],'independent_template_lag_samples':lag,'independent_template_lag_s':lag/SR,**fit(t,segment)})
prelags=[x['independent_template_lag_samples'] for x in rows if x['accepted_span_s'][1]<118.8];postlags=[x['independent_template_lag_samples'] for x in rows if x['accepted_span_s'][0]>120]
pre=int(np.median(prelags));post=int(np.median(postlags));same=np.flatnonzero(a[:min(len(a),len(b))]!=b[:min(len(a),len(b))]);first=int(same[0]);prefix=a[:first];context=[]
for st,en in [(114.6,118.7),(118.7,119.2),(118.85,119.12),(119.12,119.4)]:
 lo=round(st*SR);hi=round(en*SR);context.append({'public_same_clock_span_s':[st,en],**fit(a[lo:hi],b[lo:hi])})
AAC=[]
for p in (B/'02-accepted-public.mp4',B/'02-current-failed-public.mp4'):
 raw=subprocess.check_output(['ffmpeg','-v','error','-nostdin','-i',str(p),'-map','0:a:0','-c:a','copy','-f','adts','-']);AAC.append(hashlib.sha256(raw).hexdigest())
report={'kind':'02-actual-old-current-public-waveform-comparison','acceptance':False,'old_MP4_SHA256':hashlib.sha256((B/'02-accepted-public.mp4').read_bytes()).hexdigest(),'current_failed_MP4_SHA256':hashlib.sha256((B/'02-current-failed-public.mp4').read_bytes()).hexdigest(),'AAC_ADTS_SHA256':{'old':AAC[0],'current':AAC[1]},'whole_AAC_equal':AAC[0]==AAC[1],'old_current_decoded_sample_counts':[len(a),len(b)],'duration_delta_s':(len(b)-len(a))/SR,'first_actual_difference_at_s':first/SR,'entire_exact_equal_prefix':{'samples':first,'SHA256':hashlib.sha256(prefix.tobytes()).hexdigest(),'np_array_equal':bool(np.array_equal(prefix,b[:first]))},'independent_public_template_alignments':rows,'before_and_after_actual_public_clock_lag_samples':{'before':pre,'after':post,'step_samples':post-pre},'S14_and_tail_public_window_comparisons_same_clock':context,'private_PCM_GT_or_cache_used_for_public_comparison':False}
(B/'02-actual-public-waveform-proof.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'duration_delta_s':report['duration_delta_s'],'first_difference_s':first/SR,'wholeAACequal':report['whole_AAC_equal'],'prepostlags':report['before_and_after_actual_public_clock_lag_samples'],'templates':[{'s':x['accepted_span_s'],'lag':x['independent_template_lag_s'],'NCC':x['NCC'],'bit_equal':x['np_array_equal']} for x in rows]},ensure_ascii=False))
