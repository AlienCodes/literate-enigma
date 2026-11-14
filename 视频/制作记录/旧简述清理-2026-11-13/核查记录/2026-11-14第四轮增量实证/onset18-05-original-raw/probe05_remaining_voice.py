"""Read-only actual original PCM/mother phoneme continuity for two PV alarms."""
from pathlib import Path
import ast,io,json,hashlib,importlib.util,tempfile,re
import numpy as np,soundfile as sf
B=Path(__file__).parent;A=B.parent
spec=importlib.util.spec_from_file_location('original_replay',A/'audio65-69-source-readonly/replay_original_sources.py');r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
p=A/'payload/视频/脚本/05.json';d=json.loads(p.read_text());pure=r.m.T/'纯人声核对.py';source=pure.read_text();pv={'np':np,'SR':24000,'F':120}
exec(compile(ast.Module(body=[n for n in ast.parse(source).body if isinstance(n,ast.FunctionDef)and n.name in ['per','spec','segments','scan','贴词尾擦音','像吸气','实测']],type_ignores=[]),str(pure)+'#unchanged-numeric','exec'),pv)
def sha(x):return hashlib.sha256(x).hexdigest()
with tempfile.TemporaryDirectory(prefix='private05-remaining-',dir='/dev/shm')as td:
 c=Path(td)/'cache';c.mkdir();a,parts=r.build(d,c);buf=io.BytesIO();sf.write(buf,a,24000,format='WAV');wav=buf.getvalue();x,sr=sf.read(io.BytesIO(wav));x=np.asarray(x,float);assert sha(wav)=='4c20eb528b935e7a315e3f41b3f4168fe82cd5e26e0b33d16ea4bfce2609cb64'
 rows=[]
 for si,alarm in[(7,[60.51,60.775]),(15,[116.30,116.395])]:
  n,t=r.scope(d,si,c);pieces=[];gaps=[];pos=0;lst=n['list_commas'](t)
  for z in re.finditer(r'[,;:](?=\s)',t):pieces.append((pos,z.end()));pos=z.end()+1;gaps.append(.2 if z.start()in lst else .4)
  pieces.append((pos,len(t)));clips,tm=n['sentence_audio'](t,pieces,gaps);last=dict(n['LAST']);part=next(v for v in parts if v['sentence']=='S'+str(si));origin=part['start_s'];raw,_=n['k'].create(n['spoken'](t),voice=n['V'],speed=n['SPEED'],lang='en-us')
  def mp(z):
   v=round(z*last['scale']*sr)-last['head']
   for aa,bb,t0,rm in last['segs']:
    if v<aa:return origin+t0
    if v<bb:
     q=v-aa;q-=sum(min(q,y)-xx for xx,y in rm if xx<q);return origin+t0+q/sr
   return origin+last['total']
  def inverse(native):
   rel=native-origin
   for j,(aa,bb,t0,rm)in enumerate(last['segs']):
    en=t0+(bb-aa-sum(y-xx for xx,y in rm))/sr
    if t0<=rel<=en:
     q0=round((rel-t0)*sr);q=q0;removed=0
     for xx,y in rm:
      if q0>=xx-removed:q+=y-xx
      removed+=y-xx
     return round(aa+q+last['head'])
   return None
  tokens=[{'phoneme':v.phoneme,'model_raw_start_s':v.start*last['scale'],'model_raw_end_s':v.end*last['scale'],'mapped_actual_native_start_s':mp(v.start),'mapped_actual_native_end_s':mp(v.end)}for v in last['toks']if alarm[0]-.6<=mp(v.start)<=alarm[1]+.25]
  sn=x[round(part['start_s']*sr):round(part['end_s']*sr)];F=120;ref=float(np.sqrt(np.mean(sn[:len(sn)//F*F].reshape(-1,F)**2,axis=1)).max());frames=[]
  for at in np.arange(alarm[0]-.2,alarm[1]+.08,.005):
   q=round(at*sr);y=x[q:q+F];specv=pv['spec'](x[q:q+480]);period=pv['per'](x[max(0,q-180):q+300]);rp=inverse(float(at));rr=raw[rp:rp+480].astype(float)if rp is not None else None
   frames.append({'actual_native_t_s':round(float(at),6),'RMS_dBFS_5ms':float(20*np.log10(np.sqrt(np.mean(y*y))+1e-15)),'relative_sentence_peak_RMS_dB_5ms':float(20*np.log10(np.sqrt(np.mean(y*y))/(ref+1e-15)+1e-15)),'official_spec_centroid_20ms_hz':float(specv[0]),'official_spec_low150_dB':float(specv[1]),'official_per_20ms':float(period),'inverse_original_raw_sample_index':rp,'raw_mother_20ms_RMS_dBFS':None if rr is None or not len(rr)else float(20*np.log10(np.sqrt(np.mean(rr*rr))+1e-15)),'raw_mother_20ms_official_spec':None if rr is None or not len(rr)else[list(map(float,pv['spec'](rr)))][0]})
  rec={'sentence':'S'+str(si),'actual_alarm_native_s':alarm,'original_sentence_English':t,'actual_spoken_English':n['spoken'](t),'actual_sentence_native_timing':part,'model_phoneme_scalar_mapping':tokens,'native_and_unprocessed_mother_continuity_5ms_rows':frames,'original_actual_edit_map':{k:last[k]for k in['head','scale','segs','total','cuts','grafts','gaps','fades','hs']},'original_nonvoice_controls':d.get('非人声区间',{}).get('S'+str(si)),'original_K139_tail_fricative_continuity_pass':bool(pv['贴词尾擦音'](x,('收尾过长'if si==7 else'呼吸声',alarm[0],alarm[1],-30.379 if si==7 else -37.343,0.265 if si==7 else 3353,0. if si==7 else .19,0. if si==7 else -4.1)))}
  if si==15:
   rawlo,rawhi=5.95,6.1612;rs=raw[round(rawlo*sr):round(rawhi*sr)].astype(float);rec['S15_raw_deletion_diagnostic']={'original_raw_seconds':[rawlo,rawhi],'original_raw_RMS_dBFS':float(20*np.log10(np.sqrt(np.mean(rs*rs))+1e-15)),'original_raw_official_spec':list(map(float,pv['spec'](rs))),'overlapping_model_tokens':[{'phoneme':z.phoneme,'start_raw_s':z.start*last['scale'],'end_raw_s':z.end*last['scale']}for z in last['toks']if z.end*last['scale']>rawlo-.1 and z.start*last['scale']<rawhi+.1],'basis_not_created':True}
  sn_native=x[round(part['start_s']*sr):round(part['end_s']*sr)]
  rec['original_scan_on_actual_sentence_only']=[{'label':f[0],'native_start_s':float(f[1]+origin),'native_end_s':float(f[2]+origin),'original_numeric_tuple_fields_after_times':list(map(float,f[3:]))}for f in pv['scan'](sn_native)]
  if si==15:
   rawref=float(np.sqrt(np.mean(raw[:len(raw)//120*120].reshape(-1,120)**2,axis=1)).max());rf=[]
   for at in np.arange(5.80,6.321,.005):
    q=raw[round(at*sr):round((at+.005)*sr)].astype(float);zz=raw[round(at*sr):round((at+.02)*sr)].astype(float);rf.append({'original_raw_t_s':round(float(at),6),'RMS_dBFS':float(20*np.log10(np.sqrt(np.mean(q*q))+1e-15)),'relative_raw_sentence_peak_RMS_dB':float(20*np.log10(np.sqrt(np.mean(q*q))/(rawref+1e-15)+1e-15)),'original_spec_centroid_Hz':float(pv['spec'](zz)[0]),'original_spec_low150_dB':float(pv['spec'](zz)[1]),'original_per_20ms':float(pv['per'](zz))})
   rec['S15_raw_deletion_diagnostic']['raw_5ms_boundary_frames']=rf
  rows.append(rec)
 result={'kind':'05-two-current-PV-alarms-and-S15-original-word-phoneme-evidence','quality_acceptance':False,'actual_source_file':str(p),'actual_source_full_SHA256':sha(p.read_bytes()),'exact_actual_native_WAV_full_SHA256':sha(wav),'exact_actual_native_WAV_MD5_first12':hashlib.md5(wav).hexdigest()[:12],'original_purevoice_full_SHA256':sha(source.encode()),'same_old_audio_not_used_as_sole_pronunciation_basis':True,'alarms':rows,'G72_original_mother_scalar_manifest':list(r.m.cache_rows.values()),'source_controls_CF_core_thresholds_cache_modified':False,'no_TTS_inference_or_raw_mother_PCM_GT_export':True}
 out=B/'05'/'05-two-PV-word-phoneme-continuity-next-unreviewed.json';out.write_text(json.dumps(result,ensure_ascii=False,indent=2,default=lambda x:float(x))+'\n');print('wrote',str(out),sha(out.read_bytes()),flush=True)
