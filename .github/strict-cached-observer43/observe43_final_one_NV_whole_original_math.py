#!/usr/bin/env python3
"""One candidate-only43 AUDIO_ONLY build; original math and strictly existing models.
No old whole replay, no source/GEN/CF modification, no acceptance or new TTS.
"""
import argparse,ast,copy,gc,hashlib,importlib.util,json,os,re,shutil,subprocess,sys,tempfile
from pathlib import Path
import numpy as np
import soundfile as sf

PIN={'source':'e000223b06902520aa354e496be9292c9ce91aa6e1e5886bfff7366f815d4cea','GEN':'32b33f5d74f871fa6e2b0b264722000dc0c207047715d5e2a6b1da156862e6c8','before_source':'bacc7abafe824031e0d85349f80327b66947839472008a18bd679cf6cdc3b53e','whole_reference':'5c4a2e62624ade5d119086c9525a8d90588efc7507fdbdd04678219dd8f4a156','mother_contract':'9d133939b08a08b78cb6810028708618b92a2f2449cf56a67bd9b82506887b79','candidate_proof':'c000662913d08b2082681dac9ecbc128a346c73976524ca82fc9335a10aae759','root_decision':'2f14e9bea5a6703148b43ae7a5f84c9838b7851dac9b294be419b5ccad1b8b17'}
MAKER='23d886be9cf999eabc682159e1ab2fc2cf6c4ccb0597f32d60d5e90a34606c0e'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
arrsha=lambda a:hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()
read=lambda p:json.loads(Path(p).read_text())
canon=lambda v:json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':'))
def safe(v):
 if isinstance(v,dict):return {str(k):safe(x)for k,x in v.items()}
 if isinstance(v,(list,tuple)):return[safe(x)for x in v]
 if isinstance(v,np.integer):return int(v)
 if isinstance(v,np.bool_):return bool(v)
 if isinstance(v,(float,np.floating)):return float(v)if np.isfinite(v)else None
 return v

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for name in ('tools','video-root','source','GEN','before-source','whole-reference','mother-contract','candidate-proof','root-decision','output'):p.add_argument('--'+name,type=Path,required=True)
 a=p.parse_args();T=a.tools.resolve();M=a.video_root.resolve();O=a.output.resolve()
 assert os.environ.get('XG_NOPUSH')=='1'and os.environ.get('STRICT_CACHE')=='1';assert not any(os.environ.get(k)for k in ('VOICE','AFFILE','OLD_IV_VOID'));assert sha(T/'make_video.py')==MAKER
 inputs={k:getattr(a,k).resolve()for k in PIN};assert all(sha(q)==PIN[k]for k,q in inputs.items())
 d=read(a.source);old=read(a.before_source);proof=read(a.candidate_proof);c=proof['candidate'];assert str(d['no'])=='43'and len(d['sentences'])==21
 assert c['candidate_data_leaf_delta']=={'非人声区间.S16':[[1.0950416666666667,1.295,'紧贴词尾']],'区间声音指纹.S16':'4c97c3273743'}
 assert d['非人声区间']['S16']==c['candidate_data_leaf_delta']['非人声区间.S16']and d['区间声音指纹']['S16']=='4c97c3273743'
 reduced=copy.deepcopy(d);del reduced['非人声区间']['S16'];del reduced['区间声音指纹']['S16'];assert reduced==old
 assert d['分段增益dB']['S13']=={'1':1.0}and not d.get('结尾句',{}).get('S21');assert c['processed_sentence_SHA256']=='987aeb8c06d57c53e6078ab8259a27c3696f06d10b9832d17f556b812168d3b7'
 baseline=next(x for x in read(a.whole_reference)['cases']if x['source_id']==43)['candidate'];assert baseline['raw_WAV_sha256']=='7e20f3e642d31bdd31baa0ac480098af8fdc0f0ba2936f93ce47aa431e533ea2'and baseline['AAC_ADTS_sha256']=='d28d0504397cf1e9520b1e84599ff2dd9406df1519632b70d94b8961ce1c71bf'
 contract=read(a.mother_contract);case=next(x for x in contract['case_evidence']if x['source_id']==43 and x['sentence']=='S16');cache=M/'tts/cache_tts';assert cache.is_dir();cache_before={q.name:(q.stat().st_size,q.stat().st_mtime_ns)for q in cache.iterdir()if q.is_file()};models_before={k:sha(M/'tts'/k)for k in contract['models']};assert models_before==contract['models']
 for z in case['model_inputs']:
  assert sha(cache/z['cache_key'])==z['cache_PKL_SHA256']and sha(cache/(z['cache_key']+'.单线程'))==z['single_thread_marker_SHA256']
 PR=M/'source43-final-one-NV-original-math-whole';assert not PR.exists();W=PR/'video';(W/'scripts').mkdir(parents=True);(PR/'tts').symlink_to(M/'tts',target_is_directory=True)
 for name in ('读音改正.json','按语境读音.json'):
  assert(M/'video'/name).is_file();shutil.copyfile(M/'video'/name,W/name)
 source=W/'scripts/43.json';shutil.copyfile(a.source,source);os.environ['AUDIO_ONLY']='1';os.environ['TMPDIR']=str(PR/'tmp');Path(os.environ['TMPDIR']).mkdir();tempfile.tempdir=None;os.chdir(W);sys.path[:0]=[str(T),str(W)]
 spec=importlib.util.spec_from_file_location('actual_final43_one_NV_whole',T/'make_video.py');m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m);m._SPOKEN_SOURCE_NO='43';m._REPO_CACHE=str(PR/'no-public-export');assert not Path(m._REPO_CACHE).exists()
 report={'kind':'source43-root-selected-one-NV-candidate-only-original-math-whole-diagnostic','diagnostic_only':True,'formal_audio_or_video_accepted':False,'source_GEN_CF_or_core_modified':False,'new_model_inference':False,'old_or_baseline_whole_replay_performed':False,'candidate_whole_build_count':0,'input_SHA256':PIN,'maker_SHA256':MAKER,'original_8_R_PV_cut_position_two_ASR_and_final4K_still_required':True,'original_math_records':[],'passed':False};state={'counter':0,'sid':None};records={};arrays={};new_names=set();neg=[]
 orig_s=m.sentence_audio;orig_g=m.句增益;orig_t=m.title_audio;orig_level=m._auto_level;orig_cache=m._CACHE;orig_repo=m._REPO_CACHE
 for obj,name in ((m.k,'create'),(m.KT,'create_timed')):
  fn=getattr(obj,name)
  def guarded(*ar,_fn=fn,**kw):
   assert os.environ.get('STRICT_CACHE')=='1','No model call outside STRICT; original math only';return _fn(*ar,**kw)
  setattr(obj,name,guarded)
 tree=ast.parse((T/'make_video.py').read_text());fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='_auto_level');keyexpr=next(n.value for n in fn.body if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='_k'for t in n.targets));level_ast=hashlib.sha256(ast.dump(fn,include_attributes=False).encode()).hexdigest()
 def actual_pin(clips,tm,gaps,no):
  key=eval(compile(ast.Expression(body=keyexpr),str(T/'make_video.py')+'#original-key-expression','eval'),m.__dict__,dict(clips=clips,tmap=tm,gaps=gaps,no=no))
  return {'key':key,'no':str(no),'sentence':state['sid'],'clip_SHA256':[arrsha(x)for x in clips],'clip_samples':[len(x)for x in clips],'tmap':copy.deepcopy(tm),'gaps':list(gaps)}
 def validate_tuple(v,expected):assert canon(v)==canon(expected),'Exact newS16 source/clip/tmap/gaps tuple differs'
 def candidate_level(clips,tm,gaps,no='',rounds=2):
  if state['sid']!='S16':return orig_level(clips,tm,gaps,no,rounds)
  assert str(no)=='43'and rounds==2 and os.environ.get('STRICT_CACHE')=='1';assert m.SENT_FP[sent16]=='4c97c3273743'and m.VFP[sent16]=='4c97c3273743';assert arrsha(np.concatenate(clips))==c['processed_sentence_SHA256']and canon(tm)==canon(c['actual_tmap'])and canon(m.LAST['cuts'])==canon(c['actual_original_cuts'])and list(gaps)==[.4]
  pin=actual_pin(clips,tm,gaps,no);expected=copy.deepcopy(pin)
  altered=[x.copy()for x in clips];altered[0][0]=np.nextafter(altered[0][0],np.float32(np.inf),dtype=altered[0].dtype)
  for label,bad in [('one_sample_changed',actual_pin(altered,tm,gaps,no)),('wrong_source',{**pin,'no':'999'}),('wrong_sentence',{**pin,'sentence':'S999'})]:
   try:validate_tuple(bad,expected)
   except AssertionError:neg.append({'case':label,'rejected':True})
   else:raise AssertionError('Actual math input negative not rejected')
  validate_tuple(actual_pin(clips,tm,gaps,no),expected);filename='调平_'+pin['key']+'.json';private=PR/'only-original-S16-auto-level-math';private.mkdir();m._CACHE=str(private);m._REPO_CACHE=str(PR/'no-math-export');assert not Path(m._REPO_CACHE).exists();os.environ.pop('STRICT_CACHE')
  try:value=orig_level(clips,tm,gaps,no,rounds)
  finally:os.environ['STRICT_CACHE']='1';m._CACHE=orig_cache;m._REPO_CACHE=orig_repo
  q=private/filename;assert q.is_file();stored=read(q);assert {int(k):float(v)for k,v in stored.items()}==value
  target=cache/filename
  if target.exists():assert sha(target)==sha(q),'Original-math new tuple disagrees with existing cache'
  else:shutil.copyfile(q,target);new_names.add(filename)
  save=M/'tts/source43-one-NV-candidate-reference-cache';save.mkdir(exist_ok=True);saved=save/filename
  if saved.exists():assert sha(saved)==sha(q)
  else:shutil.copyfile(q,saved)
  assert orig_level(clips,tm,gaps,no,rounds)==value
  report['original_math_records'].append({'source_id':43,'sentence':'S16','actual_prelevel_tuple':pin,'original_auto_level_AST_SHA256':level_ast,'original_math_algorithm_unchanged':True,'file':filename,'JSON_SHA256':sha(q),'JSON_bytes':q.stat().st_size,'value':stored,'strict_cache_readback_exact':True,'private_save_directory':str(save),'new_model_inference':False});return value
 m._auto_level=candidate_level
 bare=lambda s:' '.join(re.sub(r'\*\*','',re.sub(r'\{\{.*?\}\}','',x['en'])).strip()for x in s['chunks']);sent16=bare(d['sentences'][15])
 def title(text):
  z=orig_t(text);arrays['title']=z.copy();records['title']={'samples':len(z),'pre_master_float32_SHA256':arrsha(z)};return z
 def sentence(sent,pieces,gaps):
  state['counter']+=1;sid='S'+str(state['counter']);state['sid']=sid;assert sent==bare(d['sentences'][state['counter']-1]);clips,tm=orig_s(sent,pieces,gaps);records[sid]={'samples_before_gain':sum(len(x)for x in clips),'before_gain_float32_SHA256':arrsha(np.concatenate(clips)),'before_gain_clips':[{'samples':len(x),'SHA256':arrsha(x)}for x in clips],'tmap':copy.deepcopy(tm),'gaps':list(gaps),'raw_fingerprint':m.SENT_FP[sent],'cuts':copy.deepcopy(m.LAST['cuts'])};return clips,tm
 def gain(data,no,si,sent,pieces,gaps,clips,tm,arr):
  assert state['sid']=='S'+str(si+1);result=orig_g(data,no,si,sent,pieces,gaps,clips,tm,arr);z=result[1];arrays[state['sid']]=z.copy();records[state['sid']].update(samples=len(z),pre_master_float32_SHA256=arrsha(z),automatic_level=result[2],manual_segment_level=result[3]);return result
 m.title_audio=title;m.sentence_audio=sentence;m.句增益=gain
 try:
  output=PR/'source43-final-one-NV.m4a';m.build(str(source),str(output));report['candidate_whole_build_count']=1;wav=W/'work_43/a.wav';assert len(records)==22 and len(report['original_math_records'])==1
  peak=max(float(np.abs(x).max())for x in arrays.values());assert peak==baseline['master_pre_peak'],'New global master differs; cannot claim other quantized samples unchanged'
  comparisons={}
  for sid,r in records.items():
   b=baseline['sentence_pre_master_records'][sid];equal=r['samples']==b['samples']and r['pre_master_float32_SHA256']==b['pre_master_float32_SHA256'];z={'old_pre_master_SHA256':b['pre_master_float32_SHA256'],'new_pre_master_SHA256':r['pre_master_float32_SHA256'],'same_samples':r['samples']==b['samples'],'pre_master_SHA256_identity':equal}
   if sid!='S16':assert equal;z['quantized_identity_proof']='Actual same pre-master byte SHA/sample length and unchanged original full-track normalization+PCM16 encoding implies identical original per-sample quantization; oldwhole not replayed.'
   comparisons[sid]=z
  newraw=sha(wav);newaac=hashlib.sha256(subprocess.check_output(['ffmpeg','-v','error','-nostdin','-i',str(output),'-map','0:a:0','-c:a','copy','-f','adts','-'])).hexdigest();assert newraw!=baseline['raw_WAV_sha256']and newaac!=baseline['AAC_ADTS_sha256']
  full,sr=sf.read(wav,dtype='float64');assert sr==24000;segs=read(W/'work_43/分段.json');quantized={}
  for sid,rng in segs.items():
   lo=round(rng[0]['时刻'][0]*sr);hi=round(rng[-1]['时刻'][1]*sr);quantized[sid]={'actual_new_WAV_frame_range':[lo,hi],'actual_decoded_PCM16_float64_SHA256':arrsha(full[lo:hi])}
  sp=importlib.util.spec_from_file_location('original43_purevoice_whole',T/'纯人声核对.py');pv=importlib.util.module_from_spec(sp);sp.loader.exec_module(pv);flags=[]
  for f in pv.scan(full):
   sid=next((k for k,rng in segs.items()if rng[0]['时刻'][0]-.06<=f[1]<=rng[-1]['时刻'][1]+.06),None);flags.append({'actual_tuple':list(f),'key':pv.key(f),'sentence':sid,'actual_measurement':pv.实测(f),'new_S16_no_legacyCF_allowed':sid=='S16'})
  report.update(actual_new_whole_RAW_WAV_SHA256=newraw,actual_new_whole_AAC_ADTS_SHA256=newaac,actual_new_whole_WAV_MD5_first12=hashlib.md5(wav.read_bytes()).hexdigest()[:12],actual_new_raw_WAV_bytes=wav.stat().st_size,master_pre_peak=peak,master_ideal_multiplier=.89/peak,master_exact_to_5c4a=True,old_baseline_role='Actual43643745207 approved-spoken input before selectedpost-dNV; sourcebacc, WAV7e20/AACd28d; no replay.',sentence_pre_master_records=records,sentence_pre_master_identity_to_actual5c4a=comparisons,non_target_count_including_title_and_S13=sum(k!='S16'for k in comparisons),actual_new_quantized_sentence_evidence=quantized,actual_segment_clock=segs,purevoice_actual_raw_events=flags,new_S16_raw_noise_events=[x for x in flags if x['sentence']=='S16'],actual_original_display_chunk_timetable=(W/'work_43/list.txt').read_text(),codec_probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_entries','stream=codec_name,codec_type,sample_rate,channels:format=duration','-of','json',str(output)])),passed=True)
  wav.unlink();output.unlink()
 except BaseException as exc:report['error']={'type':type(exc).__name__,'detail':str(exc)};raise
 finally:
  after={q.name:(q.stat().st_size,q.stat().st_mtime_ns)for q in cache.iterdir()if q.is_file()};report['existing_normal_cache_stats_unchanged']=all(after.get(k)==v for k,v in cache_before.items());report['new_normal_cache_files']=sorted(set(after)-set(cache_before));report['only_new_cache_files_original_math_JSON']=set(after)-set(cache_before)==new_names;report['models_byte_exact']={k:sha(M/'tts'/k)for k in contract['models']}==models_before;report['input_files_byte_exact']=all(sha(q)==PIN[k]for k,q in inputs.items());report['actual_original_math_scope_negatives']=neg;report['private_audio_or_models_exported']=False;assert report['existing_normal_cache_stats_unchanged']and report['only_new_cache_files_original_math_JSON']and report['models_byte_exact']and report['input_files_byte_exact'];O.parent.mkdir(parents=True,exist_ok=True);O.write_text(json.dumps(safe(report),ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({'diagnostic_only':True,'passed':report['passed'],'output':str(O),'SHA256':sha(O)},ensure_ascii=False))
if __name__=='__main__':main()
