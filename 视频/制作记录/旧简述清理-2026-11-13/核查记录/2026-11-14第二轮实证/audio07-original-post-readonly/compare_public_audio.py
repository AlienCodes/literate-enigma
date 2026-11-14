import json,subprocess,pathlib,hashlib,re
import numpy as np
from scipy import signal
B=pathlib.Path(__file__).parent;SR=48000
D=lambda p:np.frombuffer(subprocess.check_output(['ffmpeg','-v','error','-nostdin','-i',str(p),'-map','0:a:0','-vn','-ac','1','-ar',str(SR),'-f','f32le','-']),np.float32)
A=D(B/'07-accepted-public.mp4');C=D(B/'files/07-failed-draft.mp4')
oldsrc=json.loads((B/'07-old-public-source.json').read_text());source=json.loads((B/'files/07-failed-working-source.json').read_text());status=json.loads((B/'files/07-status.json').read_text())
def fit(a,b):
 a=a.astype(float);b=b.astype(float); g=float(a@b/(a@a+1e-30));d=b-g*a
 return {'gain_db':float(20*np.log10(max(g,1e-30))),'NCC':float(a@b/(np.linalg.norm(a)*np.linalg.norm(b)+1e-30)),'residual_SNR_dB':float(10*np.log10((np.mean((g*a)**2)+1e-30)/(np.mean(d*d)+1e-30)))}
def span(start,end):
 a=A[round(start*SR):round(end*SR)];b=C[round(start*SR):round(end*SR)]
 return {'start_s':start,'end_s':end,'sample_count':len(a),'bit_identical':bool(np.array_equal(a,b)),'different_samples':int(np.count_nonzero(a!=b)),'max_abs_difference':float(np.max(abs(a-b))),'accepted_float32_sha256':hashlib.sha256(a.tobytes()).hexdigest(),'actual_float32_sha256':hashlib.sha256(b.tobytes()).hexdigest(),**fit(a,b)}
lines=status['failure_details']['public_checker_diagnostics']['做_07/出片后.log'];rows=[]
for l in lines:
 m=re.search('BAD (.*?) ([\\d.]+)–([\\d.]+)s',l)
 if not m:continue
 a,b=map(float,m.group(2,3));key=f'{m.group(2)}–{m.group(3)}s';conf=oldsrc['核对确认']['非人声'].get(key)
 rows.append({'alarm':l,'exact_existing_confirmation_key':key if conf else None,'existing_confirmation':conf,'actual_source_confirmation':source['核对确认']['非人声'].get(key),'exact_alarm_span':span(a,b),'context_span':span(a-.15,b+.15)})
blocks=[]
for k in range(1,int(min(len(A),len(C))/SR)-1):
 a=A[k*SR:(k+1)*SR]
 if np.sqrt(np.mean(a.astype(float)**2))<.001:continue
 blocks.append({'start_s':k,**span(k,k+1)})
r={'kind':'actual-public-07-audio-continuity-diagnostic','acceptance':False,'accepted_MP4_sha256':hashlib.sha256((B/'07-accepted-public.mp4').read_bytes()).hexdigest(),'actual_failed_MP4_sha256':hashlib.sha256((B/'files/07-failed-draft.mp4').read_bytes()).hexdigest(),'accepted_sample_count':len(A),'actual_sample_count':len(C),'duration_delta_s':(len(C)-len(A))/SR,'actual14alarms':rows,'active_1s_blocks':blocks,'private_GT_PCM_cache_read_or_exported':False}
(B/'07-public-audio-continuity.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'durations':[len(A)/SR,len(C)/SR],'alarm_rows':[{ 'key':x['exact_existing_confirmation_key'],'bit_equal':x['context_span']['bit_identical'],'gain':x['context_span']['gain_db'],'NCC':x['context_span']['NCC'],'SNR':x['context_span']['residual_SNR_dB']} for x in rows],'block_nonidentical':len([x for x in blocks if not x['bit_identical']]),'totalblocks':len(blocks)},ensure_ascii=False))
