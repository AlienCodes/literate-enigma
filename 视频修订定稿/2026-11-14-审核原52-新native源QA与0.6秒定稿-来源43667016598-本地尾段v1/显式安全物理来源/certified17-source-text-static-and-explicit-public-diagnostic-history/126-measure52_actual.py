from pathlib import Path
import hashlib,importlib.util,json,os,re,datetime
import numpy as np,pyloudnorm as pyln
from scipy import signal
O=Path(__file__).parent;os.environ['TMPDIR']=str(O);T=Path('/workspace/work/audit-repo/视频/工具');N=Path('/workspace/work/video-audit70-20261113/next-passed-native/43533004625/52');A=N/'files';V=N/'52-4K-正文后插图2秒-简述2秒.mp4';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();bind=json.load(open(O/'52-original-actual-source-full-AAC-binding-and-requested-timing-PRIVATE.json'));x=np.load(O/'source-normalized.npy');y=np.load(O/'actual-public-decoded.npy');sr=24000;meter=pyln.Meter(sr);lags=[]
for a,b in [(5,8),(10,14),(26,30),(100,104)]:
 st,en=round(a*sr),round(b*sr);u=x[st:en].astype(float);v=y[st-1500:en+1500].astype(float);cor=signal.correlate(v,u,'valid',method='fft');j=int(np.argmax(cor));lag=j-1500;lags.append({'source_window_s':[a,b],'best_lag_samples_24k':lag,'normalized_cross_correlation':float(np.corrcoef(u,v[j:j+len(u)])[0,1])});assert lag==600
lag=600/sr
def db(v):return float(20*np.log10(max(float(v),1e-30)))
def met(a,b):
 z=y[round(a*sr):round(b*sr)].astype(float);n=len(z)//240;fr=z[:n*240].reshape(-1,240);lev=10*np.log10((fr*fr).mean(1)+1e-30);active=fr[lev>-45].reshape(-1);L=meter.integrated_loudness(z)if len(z)>=9600 else None;LM=[meter.integrated_loudness(z[k:k+9600])for k in range(0,max(1,len(z)-9600+1),240)]if len(z)>=9600 else[]
 return {'public_start_s':a,'public_end_s':b,'duration_s':b-a,'LUFS':float(L)if L is not None and np.isfinite(L)else None,'max400ms_LUFS':float(max(LM))if LM else None,'active10ms_RMS_dBFS':db(np.sqrt(np.mean(active*active)))if len(active)else None,'active_fraction':float(np.mean(lev>-45))if len(lev)else 0,'RMS_dBFS':db(np.sqrt(np.mean(z*z))),'sample_peak_dBFS':db(np.max(np.abs(z)))}
rows=[]
for p in bind['parts']:
 if p['sentence']=='title':continue
 texts=re.split(r'(?<=[,;:])\s+',p['spoken_English']);segs=p['LAST_scalar_timing']['segs'];assert len(texts)==len(segs);pieces=[]
 for j,(t,z)in enumerate(zip(texts,segs),1):
  a=p['start_s']+max(0,z[2])+lag;b=p['start_s']+z[2]+(z[1]-z[0]-sum(e-s for s,e in z[3]))/sr+lag
  if j==len(segs):b=p['end_s']+lag
  pieces.append({'piece':j,'text':t,**met(a,b)})
 rows.append({'sentence':p['sentence'],'text':p['spoken_English'],'public_start_s':p['start_s']+lag,'public_end_s':p['end_s']+lag,'automatic_level':p['automatic_level'],'manual_level':p['manual_segment_level'],'pieces':pieces})
def load(n,p):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
H=load('source52_original_health',T/'音频体检.py');R=H.R;priv=O/'original-whole-health-private';(priv/'scripts').mkdir(parents=True,exist_ok=True);(priv/'scripts/52.json').write_bytes((A/'52-source.json').read_bytes());os.chdir(priv);pcm=R.pcm(str(V));tm=R.momentary(str(V));I,segments,levels,bad,summ=R.check(str(V),pcm);span=priv/'52-calibrated-native-spans.json';span.write_text(json.dumps({p['sentence']:[{'时刻':[p['start_s']+lag,p['end_s']+lag]}]for p in bind['parts']if p['sentence']!='title'}));inside=R.句内(str(V),pcm,tm,str(span));insidebad=R.句内报(inside);metrics=H.指标(pcm,'52');notes=[];hbad=H.超限(metrics,json.load(open(T/'音频体检基准.json')),H.确认('52'),notes)
rep={'kind':'source52-user117119-current-original-bound-full18-audio-measurement','source_id':'52','frozen_book_order':'41','full_AAC_exact':True,'original_WAV_sha256':bind['whole_original_source_WAV_sha256'],'actual_AAC_sha256':bind['actual_AAC_sha256'],'actual_MP4_sha256':sha(V),'actual_source_sha256':bind['actual_original_source_sha256'],'original_maker_sha256':bind['original_maker_sha256'],'original_clean_sha256':bind['original_clean_sha256'],'actual_AF_delay_samples24k':600,'four_source_to_public_crosscorrelations':lags,'all18_actual_punctuation_piece_metrics':rows,'original_R_whole_summary':summ,'original_R_whole_flags':bad,'original_R_inside_all_rows':inside,'original_R_inside_flags':insidebad,'original_8_health_metrics':metrics,'original_8_health_flags':hbad,'original_8_health_notes':notes,'no_new_CF_or_source_control_or_program_or_PDF_written':True,'no_TTS_or_candidate_applied':True,'human_listening_not_claimed':True,'private_raw_waveforms_GT_and_cache_not_exported':True,'utc':datetime.datetime.now(datetime.timezone.utc).isoformat()};p=O/'52-original-bound-full18-and-cold-though-ThatSmoke-measurement.json';p.write_text(json.dumps(rep,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'path':str(p),'sha256':sha(p),'healthbad':hbad,'Rbad':bad,'insidebad':insidebad,'requested':[r for r in rows if r['sentence']in['S1','S4','S5']]},ensure_ascii=False))
