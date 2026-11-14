"""Independent comparison of the actual public MP4 audio, safe scalar output."""
from pathlib import Path
import hashlib,json,subprocess
import numpy as np
from scipy import signal
B=Path(__file__).parent;SR=48000
def sha(b):return hashlib.sha256(b).hexdigest()
def decode(p):return np.frombuffer(subprocess.check_output(['ffmpeg','-v','error','-nostdin','-i',str(p),'-vn','-ac','1','-ar',str(SR),'-f','f32le','-']),np.float32)
def fit(x,y):
 a=x.astype(float);b=y.astype(float);g=float(a@b/(a@a+1e-30));e=b-g*a
 return {'gain_dB':float(20*np.log10(max(g,1e-30))),'NCC':float(a@b/(np.linalg.norm(a)*np.linalg.norm(b)+1e-30)),'residual_SNR_dB':float(10*np.log10((np.mean((g*a)**2)+1e-30)/(np.mean(e*e)+1e-30))),'array_equal':bool(np.array_equal(x,y)),'different_samples':int(np.count_nonzero(x!=y)),'old_array_SHA256':sha(x.tobytes()),'actual_array_SHA256':sha(y.tobytes())}
for no in ['65','69']:
 f=B/no;op=f/f'{no}-accepted-public.mp4';cp=f/f'{no}-failed-draft.mp4';a=decode(op);b=decode(cp);n=min(len(a),len(b));diff=np.flatnonzero(a[:n]!=b[:n]);rows=[]
 for st in np.arange(1,min(len(a),len(b))/SR-1,2.):
  lo=round(st*SR);hi=lo+SR;x=a[lo:hi]
  rms=float(np.sqrt(np.mean(x.astype(float)**2)))
  if rms<10**(-45/20):continue
  marg=round(.6*SR);left=max(0,lo-marg);s=b[left:min(len(b),hi+marg)];corr=signal.correlate(s,x,'valid',method='fft');idx=int(np.argmax(corr));start=left+idx;y=s[idx:idx+len(x)]
  rows.append({'accepted_public_span_s':[float(st),float(st+1)],'actual_independently_correlated_span_s':[start/SR,(start+len(x))/SR],'lag_samples':start-lo,'lag_s':(start-lo)/SR,'old_RMS_dBFS':float(20*np.log10(rms)),**fit(x,y)})
 adts=lambda p:sha(subprocess.check_output(['ffmpeg','-v','error','-nostdin','-i',str(p),'-map','0:a:0','-c:a','copy','-f','adts','-']))
 r={'kind':f'{no}-independent-actual-public-audio-comparison','quality_acceptance':False,'old_MP4_SHA256':sha(op.read_bytes()),'actual_MP4_SHA256':sha(cp.read_bytes()),'old_AAC_ADTS_SHA256':adts(op),'actual_AAC_ADTS_SHA256':adts(cp),'decoded_float32_sample_counts':[len(a),len(b)],'whole_AAC_equal':adts(op)==adts(cp),'whole_decoded_array_equal':bool(np.array_equal(a,b)),'first_different_sample_s':None if not len(diff)else int(diff[0])/SR,'last_different_sample_s':None if not len(diff)else int(diff[-1])/SR,'direct_clock_different_sample_count':len(diff),'independent_active_one_second_template_rows':rows,'no_private_raw_mother_or_GT_audio_exported':True}
 (f/f'{no}-actual-public-audio-comparison.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n')
 print(no,'duration_delta',(len(b)-len(a))/SR,'firstdiff',r['first_different_sample_s'],'lastdiff',r['last_different_sample_s'],'lags',sorted(set(x['lag_samples']for x in rows)),flush=True)
