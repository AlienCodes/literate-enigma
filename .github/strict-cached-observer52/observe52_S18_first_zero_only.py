#!/usr/bin/env python3
"""Source52 S18 only: one first real zero after a disputed short peak.
No whole reconstruction, new model inference, G36, CF, or production edit.
"""
from pathlib import Path
import argparse,ast,copy,hashlib,importlib.util,json,os,re,sys,tempfile,gc
import numpy as np
import soundfile as sf

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def arrsha(x):return hashlib.sha256(np.ascontiguousarray(x).tobytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def functions(path,names,ns):
 nodes=[n for n in ast.parse(Path(path).read_text()).body if isinstance(n,ast.FunctionDef)and n.name in names];assert{n.name for n in nodes}==set(names);exec(compile(ast.Module(body=nodes,type_ignores=[]),str(path)+'#unchanged-original-functions','exec'),ns)
def safe(x):
 if isinstance(x,dict):return{str(k):safe(v)for k,v in x.items()}
 if isinstance(x,(tuple,list)):return[safe(v)for v in x]
 if isinstance(x,np.integer):return int(x)
 if isinstance(x,np.bool_):return bool(x)
 if isinstance(x,(float,np.floating)):return float(x)if np.isfinite(x)else None
 return x
def bare(d):return[' '.join(re.sub(r'\*\*','',re.sub(r'\{\{.*?\}\}','',c['en'])).strip()for c in s['chunks'])for s in d['sentences']]

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for n in ('tools','video-root','request-source','old-private-candidate','mother-contract','actual-observation','output'):p.add_argument('--'+n,type=Path,required=True)
 a=p.parse_args();T=a.tools.resolve();M=a.video_root.resolve();O=a.output.resolve()
 assert os.environ.get('XG_NOPUSH')=='1'and os.environ.get('STRICT_CACHE')=='1'and not os.environ.get('VOICE')and not os.environ.get('AFFILE')and not os.environ.get('OLD_IV_VOID')
 assert sha(T/'make_video.py')=='23d886be9cf999eabc682159e1ab2fc2cf6c4ccb0597f32d60d5e90a34606c0e'
 assert sha(a.request_source)=='c00eb5707f1b269d2ce88fed455f592962d674d46e3bf172ba00cfe6597245f3'
 assert sha(a.mother_contract)=='9d133939b08a08b78cb6810028708618b92a2f2449cf56a67bd9b82506887b79'
 assert sha(a.actual_observation)=='55594624daca4a4601146e4cb1822e813782e14e1cdc0a5e65774e8602045822'
 request=read(a.request_source);old=read(a.old_private_candidate);contract=read(a.mother_contract);prior=read(a.actual_observation);current=prior['cases'][1]
 assert current['stage']=='candidate_twoNV'and current['whole_WAV_sha256']=='e75598471ff617384aff07e4ec29eed3a389bd75aae3bb2d4bd9668dafd4debf'
 assert old['非人声区间']['S4']==[[4.985,5.2185,'紧贴词头']]and old['非人声区间']['S18']==[[2.71,3.015]]
 assert old['区间声音指纹']['S4']=='f2954ac315f1'and old['区间声音指纹']['S18']=='88dadf11eead'
 z=copy.deepcopy(old)
 for sid in('S4','S18'):del z['非人声区间'][sid];del z['区间声音指纹'][sid]
 assert z==request and str(old['no'])=='52'and len(old['sentences'])==18
 sent=bare(old)[17];assert sent=='The cosy hearth, beloved of British families, had, all along, been among the chief offenders.'
 for k in('词尾除阻','除阻加强','停顿插入点','停顿删除区间','停顿处除阻','分段增益dB','段内渐变dB','句子增益dB','分段包络dB','结尾句'):assert not old.get(k,{}).get('S18')
 case=next(c for c in contract['case_evidence']if c['source_id']==52 and c['sentence']=='S18');assert case['actual_raw_fingerprint']=='88dadf11eead'
 cache=M/'tts/cache_tts';before={p.name:(p.stat().st_size,p.stat().st_mtime_ns)for p in cache.iterdir()if p.is_file()}
 for r in case['model_inputs']:
  assert sha(cache/r['cache_key'])==r['cache_PKL_SHA256']and sha(cache/(r['cache_key']+'.单线程'))==r['single_thread_marker_SHA256']
 inputs={str(p):sha(p)for p in(a.request_source,a.old_private_candidate,a.mother_contract,a.actual_observation)}
 private=M/'source52-S18-first-real-zero-only-local';assert not private.exists();W=private/'video';(W/'scripts').mkdir(parents=True);(private/'tts').symlink_to(M/'tts',target_is_directory=True)
 os.environ['AUDIO_ONLY']='1';os.environ['TMPDIR']=str(private/'tmp');Path(os.environ['TMPDIR']).mkdir();tempfile.tempdir=None
 pvsp=importlib.util.spec_from_file_location('original52_S18_only_PV',T/'纯人声核对.py');PV=importlib.util.module_from_spec(pvsp);pvsp.loader.exec_module(PV)
 assert sha(T/'纯人声核对.py')=='1050d1df51eb21ed0dbd19e9a97a8325c4dbfa1f58e9834760f8e5e5ba0b414f'
 report={'kind':'source52-S18-only-first-real-zero-after-disputed-2p5ms-peak-private-local-observation','diagnostic_only':True,'audio_or_video_accepted':False,'completed':False,'whole_audio_reconstructed':False,'new_model_inference':False,'new_G36_math_or_cache':False,'parameter_sweep_performed':False,'source_or_CF_or_production_controls_modified':False,'actual_prior555946_report_sha256':sha(a.actual_observation),'cases':[]}
 oldcwd=Path.cwd();oldpath=list(sys.path);pristine_base=None;selected_sample=None
 def run(data,stage):
  nonlocal pristine_base,selected_sample
  source=W/'scripts/52.json';source.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n');os.chdir(W);sys.path[:0]=[str(T),str(W)]
  text=(T/'make_video.py').read_text().split('if __name__')[0]
  hooks=[('    w=clean_tail(raw)\n','    w=clean_tail(raw)\n    _RAW.append(np.asarray(raw,np.float32).copy())\n'),('    if sent in NONVOICE: w=_nonvoice(w,NONVOICE[sent],sent)','    _PRISTINE.append(w.copy())\n    if sent in NONVOICE: w=_nonvoice(w,NONVOICE[sent],sent)'),('    clips=[];tmap=[];t=0.0;prev=0;segs=[];pgts=[]\n','    _POST.append(w.copy())\n    clips=[];tmap=[];t=0.0;prev=0;segs=[];pgts=[]\n')]
  for h,v in hooks:assert text.count(h)==1;text=text.replace(h,v,1)
  ns={'__name__':'source52_S18_only_'+stage,'__file__':str(T/'make_video.py'),'_RAW':[],'_PRISTINE':[],'_POST':[]};exec(compile(text,str(T/'make_video.py')+'#record-hooks-only','exec'),ns);ns['_SPOKEN_SOURCE_NO']='52';assert ns['SENT_NO'][sent]=='52'
  for obj,method in((ns['k'],'create'),(ns['KT'],'create_timed')):
   original=getattr(obj,method);record=next(r for r in case['model_inputs']if r['method']==method)
   def strict(text,voice,speed=1.,lang='en-us',_fn=original,_method=method,_record=record,**kw):
    assert os.environ.get('STRICT_CACHE')=='1'and text==ns['spoken'](sent)and speed==ns['SPEED']and lang=='en-us'and np.array_equal(voice,ns['V'])
    captured=[]
    def capture(actual,voice,speed=1.,lang='en-us',**actual_kw):
     mid=ns['_portable_mid'](str(M/'tts'/('kokoro-v1.0.onnx'if _method=='create'else'kokoro-v1.0-timed.onnx')));vh=hashlib.sha1(np.ascontiguousarray(voice).tobytes()).hexdigest();key=hashlib.sha1(repr((_method,mid,actual,vh,float(speed),lang,sorted(actual_kw.items()))).encode()).hexdigest()+'.pkl'
     assert key==_record['cache_key']and hashlib.sha256(actual.encode()).hexdigest()==_record['actual_input_text_SHA256'];assert sha(cache/key)==_record['cache_PKL_SHA256']and sha(cache/(key+'.单线程'))==_record['single_thread_marker_SHA256'];captured.append(key)
    ns['_pron'](capture)(text,voice=voice,speed=speed,lang=lang,**kw);assert len(captured)==1
    return _fn(text,voice=voice,speed=speed,lang=lang,**kw)
   setattr(obj,method,strict)
  def no_math(*x,**kw):raise AssertionError('S18 one piece has no G36; no math authorized')
  ns['_auto_level']=no_math;assert ns['_speech_marks'](sent)==[]
  clips,tm=ns['sentence_audio'](sent,[(0,len(sent))],[]);raw=ns['_RAW'][0];pristine=ns['_PRISTINE'][0];post=ns['_POST'][0];out=np.concatenate(clips);last=copy.deepcopy(ns['LAST'])
  assert ns['SENT_FP'][sent]=='88dadf11eead'and last['cuts']==[]and len(tm)==1
  assert arrsha(pristine)==current['new_mother_observations']['S18']['pristine_w_float32_sha256']
  if stage=='old2p710':
   assert arrsha(out)==current['sentence_records']['S18']['pre_master_float32_sha256'];pristine_base=pristine.copy()
   lower,upper=65100,65160;zeros=[i for i in range(lower,upper+1)if pristine[i-1]*pristine[i]<0 or(pristine[i]==0 and pristine[i-1]!=0)]
   assert zeros,'No real zero crossing within root-limited [2.7125,2.715]; stop without alternative search'
   selected_sample=zeros[0]
   report['single_selected_first_zero']={'allowed_sample_interval_inclusive':[lower,upper],'allowed_w_seconds':[2.7125,2.715],'first_real_zero_sample':selected_sample,'first_real_zero_w_seconds':selected_sample/24000,'prior_sample_sign':int(np.sign(pristine[selected_sample-1])),'next_sample_sign':int(np.sign(pristine[selected_sample])),'original_end_sample':72360,'one_candidate_only_not_parameter_sweep':True}
  else:assert np.array_equal(pristine_base,pristine)and data['非人声区间']['S18']==[[selected_sample/24000,3.015,'紧贴词尾']]
  F=120;ref=float(np.sqrt(np.mean(pristine[:len(pristine)//F*F].reshape(-1,F)**2,axis=1)).max());lv=lambda x:float(20*np.log10(np.sqrt(np.mean(x*x))/(ref+1e-12)+1e-12))
  iv=data['非人声区间']['S18'][0];i,j=round(iv[0]*24000),round(iv[1]*24000);changed=ns['_nonvoice'](pristine,[iv],sent);mask=np.zeros(len(pristine),bool);mask[i:j]=True;assert np.array_equal(pristine[~mask],changed[~mask])
  def out_at(wsample):
   for a0,b0,t0,rm in last['segs']:
    if a0<=wsample<b0:
     q=wsample-a0
     if any(x<=q<y for x,y in rm):return None
     return round(t0*24000)+q-sum(min(q,y)-x for x,y in rm if x<q)
   return None
  peak=range(65040,65100);oi=[out_at(k)for k in peak];actual_peak=np.asarray([out[k]if k is not None and 0<=k<len(out)else np.nan for k in oi]);expected_peak=pristine[65040:65100]
  peak_exact=bool(np.array_equal(actual_peak,expected_peak))
  if stage=='conservative_first_zero':assert peak_exact,'Disputed original2.710–2.7125 peak was not bit-exact in final processed sentence; stop'
  functions(T/'可闻声保全核对.py',{'lost_frames','check_sentence'},ns);ns['F5']=120;allowed=[(i,j)]
  preserved=ns['check_sentence']('S18',raw,out,last['head'],last['segs'],allowed,last['toks'],last['scale'],round(-last['segs'][0][2]*24000))
  bad=out.copy();loud=int(np.argmax(np.sqrt(np.mean(out[:len(out)//120*120].reshape(-1,120)**2,axis=1))))*120;bad[loud:loud+120]=0;negative=ns['check_sentence']('S18-negative',raw,bad,last['head'],last['segs'],allowed,last['toks'],last['scale'],round(-last['segs'][0][2]*24000));assert negative
  table=[]
  for k in range(round(2.68*24000),round(2.75*24000)+1,60):
   x=pristine[k:k+120];c,l=PV.spec(x);q=out_at(k);q2=out_at(k+119);processed=out[q:q2+1]if q is not None and q2 is not None and q2-q==119 else np.zeros(120)
   table.append({'w_seconds':k/24000,'pristine_2p5ms_dB':lv(pristine[k:k+60]),'pristine_5ms_dB':lv(x),'original_NV_only_5ms_dB':lv(changed[k:k+120]),'processed_mapped_5ms_dB':lv(processed),'centroid_Hz_5ms':c,'below150Hz_energy_dB_5ms':l,'periodicity20ms':PV.per(pristine[k-180:k+300])})
  peaknorm=current['master_pre_peak'];normalized=out/np.float32(peaknorm)*.89;wav=private/(stage+'-private-sentence-only.wav');sf.write(wav,normalized,24000);quant,sr=sf.read(wav);assert sr==24000;wav.unlink();start=round(current['actual_segment_clock']['S18'][0]['时刻'][0]*24000);sparse=np.zeros(start+len(quant)+48000,float);sparse[start:start+len(quant)]=quant;events=[{'tuple':f,'key':PV.key(f),'actual_measurement':PV.实测(f),'original_looks_like_breath':bool(PV.像吸气(f))}for f in PV.scan(sparse)]
  row={'stage':stage,'private_phase_source_sha256':sha(source),'S18_NV_only':iv,'new_mother_data_binding':'88dadf11eead','pristine_w_sha256':arrsha(pristine),'processed_float32_sha256':arrsha(out),'processed_samples':len(out),'duration_seconds':len(out)/24000,'original_NV_guard_passed':True,'original_NV_endpoint':{'samples':[i,j],'left5ms_dB':lv(pristine[i-120:i]),'right5ms_dB':lv(pristine[j:j+120]),'interval_max5ms_dB':float(ns['_env5'](pristine)[i//120:j//120].max()),'real_left_zero_crossing':bool(pristine[i-1]*pristine[i]<0 or(pristine[i]==0 and pristine[i-1]!=0))},'all_samples_outside_NV_directly_exact':True,'disputed_2p710_to2p7125_original_peak_final_processed_samples_exact':peak_exact,'peak_pristine_sha256':arrsha(expected_peak),'peak_processed_sha256':arrsha(actual_peak),'peak_mapping_all_samples_present':all(q is not None for q in oi),'original_audible_preservation_failures':preserved,'original_audible_preservation_loud5ms_zero_negative_rows':negative,'local2p5ms_spectrum_and_actual_original_NV_comparison':table,'S18_only_original_PV_events_using_correct_prior555_global_start_clock':events,'global_whole_fp_not_computed_or_claimed':True,'new_whole_AAC_not_computed_or_claimed':True,'no_automatic_CF_created':True}
  report['cases'].append(row);del ns;gc.collect()
 try:
  run(old,'old2p710');conservative=copy.deepcopy(old);conservative['非人声区间']['S18']=[[selected_sample/24000,3.015,'紧贴词尾']];run(conservative,'conservative_first_zero');report['completed']=True
 except BaseException as ex:report['error']={'type':type(ex).__name__,'detail':str(ex)};raise
 finally:
  os.chdir(oldcwd);sys.path[:]=oldpath;after={p.name:(p.stat().st_size,p.stat().st_mtime_ns)for p in cache.iterdir()if p.is_file()};report['all_private_cache_file_stats_unchanged']=before==after;report['input_files_byte_exact_after']=all(sha(Path(k))==v for k,v in inputs.items());assert report['all_private_cache_file_stats_unchanged']and report['input_files_byte_exact_after'];O.parent.mkdir(parents=True,exist_ok=True);O.write_text(json.dumps(safe(report),ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({'completed':report['completed'],'output':str(O),'sha256':sha(O),'not_audio_acceptance':True}))
if __name__=='__main__':main()
