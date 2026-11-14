"""Actual native PCM reconstruction + unchanged G45 function, no confirmations."""
from pathlib import Path
import ast,io,json,hashlib,importlib.util,tempfile,re,sys
import numpy as np,soundfile as sf
B=Path(__file__).parent;A=B.parent
spec=importlib.util.spec_from_file_location('original_replay',A/'audio65-69-source-readonly/replay_original_sources.py');r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
tool=r.m.T/'高亮同步核对.py';src=tool.read_text();tree=ast.parse(src);func={n.name:n for n in tree.body if isinstance(n,ast.FunctionDef)}
def sha(b):return hashlib.sha256(b).hexdigest()
def main(no):
 f=B/no;f.mkdir(exist_ok=True)
 if no=='18':p=f/'18-failed-working-source.json';si=8;ci=2;display=73.98;known=[73.81,73.98,74.,74.07];expected=json.loads((f/'18-failed-draft-proof.json').read_text())['internal_pcm_sha256']
 else:p=A/'payload/视频/脚本/05.json';si=5;ci=4;display=43.9;known=[43.72,43.9,43.92];expected='4c20eb528b935e7a315e3f41b3f4168fe82cd5e26e0b33d16ea4bfce2609cb64'
 d=json.loads(p.read_text())
 with tempfile.TemporaryDirectory(prefix=f'private-{no}-onset-',dir='/dev/shm')as td:
  cache=Path(td)/'cache';cache.mkdir();a,parts=r.build(d,cache);buf=io.BytesIO();sf.write(buf,a,24000,format='WAV');wav=buf.getvalue();x,sr=sf.read(io.BytesIO(wav));x=np.asarray(x,float)
  assert sha(wav)==expected,('not_actual_PCM',sha(wav),expected)
  n,t=r.scope(d,si,cache);exec(r.m.source[r.m.source.index('_NOSOUND=set'):r.m.source.index('def chunk_token_starts')],n)
  ps=[];gaps=[];st=0;listed=n['list_commas'](t)
  for mt in re.finditer(r'[,;:](?=\s)',t):ps.append((st,mt.end()));st=mt.end()+1;gaps.append(.2 if mt.start()in listed else .4)
  ps.append((st,len(t)));clips,tmap=n['sentence_audio'](t,ps,gaps);last=dict(n['LAST']);part=next(q for q in parts if q['sentence']=='S'+str(si));origin=part['start_s'];texts=[re.sub(r'\*\*','',re.sub(r'\{\{.*?\}\}','',c['en'])).strip()for c in d['sentences'][si-1]['chunks']]
  exec(compile(ast.Module(body=[func['是开口'],func['确认可收']],type_ignores=[]),str(tool)+'#original-onset-functions','exec'),n)
  def measure(at):
   F=int(.005*sr);i=round(at*sr);w=x[max(0,i-2*sr):i+2*sr];ln=len(w)//(2*F);ref=np.sqrt(np.mean(w[:ln*2*F].reshape(ln,2*F)**2,axis=1)).max()+1e-12
   lv=lambda q:float(20*np.log10(np.sqrt(np.mean(x[q:q+F]**2))/ref+1e-12));pre=[lv(q)for q in range(i-6*F,i,F)];post=[lv(q)for q in range(i,i+8*F,F)]
   return {'raw_native_t_s':round(float(at),6),'pre_30ms_max_dB':max(pre),'post_40ms_max_dB':max(post),'pre_5ms_dB':pre,'post_5ms_dB':post,'original_is_onset':bool(n['是开口'](x,sr,at)),'original_confirmation_receivable':bool(n['确认可收'](no,x,sr,at))}
  lo=min(known)-.05;hi=max(known)+.08;grid=[measure(float(z))for z in np.arange(round(lo,3),round(hi,3)+.0005,.001)];exact=[measure(z)for z in known]
  spectral=[]
  for at in np.arange(lo,hi,.005):
   q=x[round(at*sr):round((at+.005)*sr)];pow=abs(np.fft.rfft(q*np.hanning(len(q))))**2;freq=np.fft.rfftfreq(len(q),1/sr);spectral.append({'raw_t_s':round(float(at),6),'RMS_dBFS':float(20*np.log10(np.sqrt(np.mean(q*q))+1e-15)),'centroid_hz':float((pow*freq).sum()/(pow.sum()+1e-30))})
  def tokenmap(z):
   pos=round(z*last['scale']*sr)-last['head']
   for aa,bb,t0,rm in last['segs']:
    if pos<aa:return origin+t0
    if pos<bb:
     q=pos-aa;q-=sum(min(q,yy)-xx for xx,yy in rm if xx<q);return origin+t0+q/sr
   return origin+last['total']
  toks=[{'phoneme':z.phoneme,'original_model_start_s':z.start,'original_model_end_s':z.end,'mapped_raw_native_start_s':tokenmap(z.start),'mapped_raw_native_end_s':tokenmap(z.end)}for z in last['toks']if lo-.25<=tokenmap(z.start)<=hi+.25]
  rec={'kind':f'{no}-original-native-raw-onset-specific-proof','quality_acceptance':False,'source_file':str(p),'source_file_full_SHA256':sha(p.read_bytes()),'native_reconstructed_WAV_full_SHA256':sha(wav),'native_reconstructed_WAV_MD5_first12':hashlib.md5(wav).hexdigest()[:12],'matches_actual_known_native_PCM_full_SHA256':True,'original_checker_full_SHA256':sha(src.encode()),'sentence':'S'+str(si),'chunk':ci,'displayed_highlight_observed_s':display,'actual_original_source_sentence':d['sentences'][si-1],'actual_original_native_sentence_timing':part,'source_existing_highlight_confirmation':d.get('核对确认',{}).get('高亮',{}).get('S'+str(si)+' 第'+str(ci)+'块'),'known_candidate_raw_G45_metrics':exact,'raw_G45_one_ms_grid':grid,'original_raw_5ms_level_spectrum':spectral,'original_phoneme_scalar_mapping':toks,'original_chunk_times_relative_to_sentence_s':n['chunk_times'](texts),'original_sentence_edit_map':{k:last[k]for k in['head','scale','segs','total','cuts','grafts','gaps','fades','hs']},'all_G72_mother_scalar_provenance':list(r.m.cache_rows.values()),'no_TTS_inference_source_or_program_change_private_waveform_export':True,'proposed_confirmation':None}
  o=f/f'{no}-specific-original-raw-onset-proof.json';o.write_text(json.dumps(rec,ensure_ascii=False,indent=2,default=lambda z:float(z))+'\n')
  print(no,'nativeexact',sha(wav),'candidates',[{k:z[k]for k in ['raw_native_t_s','pre_30ms_max_dB','post_40ms_max_dB','original_is_onset']}for z in exact],flush=True)
for no in sys.argv[1:]or['18','05']:main(no)
