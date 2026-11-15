"""Only current S15 cached sentence and two existing PV windows; no whole or inference."""
from pathlib import Path
import argparse,ast,copy,gc,hashlib,importlib.util,io,json,math,os,sys,traceback
sys.dont_write_bytecode=True
PROFILE_SHA256='64b1abf5a8a0efbf93e7de6bdc0b651de9eb410c116b35f067d575766d53eab3'
SOURCE_NO='35';TARGET='S15'
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def require(x,msg):
 if not x:raise AssertionError(msg)
def inventory(p):return {x.name:digest(x)for x in Path(p).iterdir()if x.is_file()}
def load_module(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m
def bind_inputs(folder,profile):
 result={}
 for role,row in profile['inputs'].items():
  rel=Path(row['file']);require(not rel.is_absolute()and'..'not in rel.parts,'Input escaped frozen namespace');p=Path(folder)/rel
  require(p.is_file()and p.stat().st_size==row['bytes']and digest(p)==row['sha256'],'Wrong frozen input '+role);result[role]=p
 return result
def validate_data(profile,source,whole,failed):
 require(profile['source_id']=='35'and profile['target_sentence']=='S15'and str(source['no'])=='35'and len(source['sentences'])==21,'Wrong target scope')
 require(whole['diagnostic_completed']and whole['exact_scope_proved']and whole['errors']==[]and whole['actual_global_master_scale_ratio_selected_over_baseline']==1.0,'Real completed selected whole required')
 require(failed['internal_pcm_sha256']==whole['phases']['selected']['actual_complete_WAV']['file_sha256']==profile['actual_selected_WAV_SHA256'],'Wrong actual selected WAV role')
 require(failed['aac_adts_sha256']==whole['phases']['selected']['actual_complete_AAC']['AAC_ADTS_sha256']==profile['actual_selected_AAC_SHA256'],'Wrong actual selected AAC role')
 require(source.get('除阻加强',{}).get('S15')=={'句末':[3.235,3.295,4.0]}and source.get('区间声音指纹',{}).get('S15')=='6a4205ab64e1','Exact actual target BOOST and mother FP required')
 for key,value in profile['target_effective_DSP'].items():require(source.get(key,{}).get('S15')==value,'Unexpected target DSP '+key)
 require(profile['windows']==[{'id':12,'kind':'呼吸声','global_span_s':[100.72,100.83],'local_span_s':[1.27,1.38],'actual_displayed_metrics':{'duration_ms':100,'max_dB':-36.1,'centroid_Hz':2406,'periodicity':0.21,'low_frequency_dB':-5.7}}, {'id':13,'kind':'孤立杂音','global_span_s':[102.67,102.72],'local_span_s':[3.22,3.27],'actual_displayed_metrics':{'duration_ms':55,'max_dB':-30.8,'centroid_Hz':3197,'periodicity':0.18,'low_frequency_dB':-12.0}}],'Only two actual displayed native windows permitted')
def target_model_guard(m,np,cache,method,model,original,sent,entries,used):
 def guarded(text,voice,speed=1.0,lang='en-us',**kw):
  require(os.environ.get('STRICT_CACHE')=='1'and text==m.spoken(sent)and speed==.95 and lang=='en-us'and np.array_equal(voice,m.V),'Only actual S15 model tuple may read existing cache')
  require((method=='create'and kw=={})or(method=='create_timed'and kw=={'clause_pause':0,'sentence_pause':0}),'Wrong original target model kwargs')
  seen=[]
  def capture(actual_text,voice,speed=1.0,lang='en-us',**actualkw):
   mid=m._portable_mid(str(cache.parent/model));vh=hashlib.sha1(np.ascontiguousarray(voice).tobytes()).hexdigest();key=hashlib.sha1(repr((method,mid,actual_text,vh,float(speed),lang,sorted(actualkw.items()))).encode()).hexdigest()+'.pkl';row=entries[method]
   require(key==row['name']and digest(cache/key)==row['pkl_SHA256']and digest(cache/(key+'.单线程'))==row['marker_SHA256'],'Only exact existing raw/timed S15 mother authorized')
   m._条目核对(str(cache/key));seen.append({'method':method,'name':key,'PKL_SHA256':digest(cache/key),'post_pron_input_SHA256':hashlib.sha256(actual_text.encode()).hexdigest(),'kwargs':actualkw})
  m._pron(capture)(text,voice=voice,speed=speed,lang=lang,**kw);require(len(seen)==1,'Actual pronunciation capture ABI changed');used.append(seen[0]);return original(text,voice=voice,speed=speed,lang=lang,**kw)
 return guarded
def scalar_profiles(np,SR,original_dossier,it,w0,boost_before,boost_after,windows):
 names={'to_w','words','per','spec'};nodes=[n for n in ast.parse(original_dossier.read_text()).body if isinstance(n,ast.FunctionDef)and n.name in names];require(len(nodes)==4,'Original dossier AST changed')
 ns={'np':np,'SR':SR};exec(compile(ast.Module(body=nodes,type_ignores=[]),str(original_dossier),'exec'),ns);to_w,words,per,spec=(ns[n]for n in ['to_w','words','per','spec']);F5=int(.005*SR)
 rows=[]
 for window in windows:
  lo,hi=window['local_span_s'];p0=to_w(it,lo);p1=to_w(it,hi-1/SR);require(p0 is not None and p1 is not None,'Reported PV window maps to inserted gap')
  require(0<=p0<=p1<len(boost_after),'Actual mapped raw-w interval invalid')
  a,b=max(0,p0-int(.08*SR)),min(len(boost_after),p1+1+int(.08*SR));profiles={}
  for label,w in [('original_dossier_clean_tail_raw',w0),('actual_original_boost_input_w',boost_before),('actual_original_plus4_boost_return_w',boost_after)]:
   n=len(w)//F5;ref=float(np.sqrt(np.mean(w[:n*F5].reshape(n,F5)**2,axis=1)).max());lv=lambda x:20*math.log10(float(np.sqrt(np.mean(x*x)))/(ref+1e-12)+1e-9)if len(x)else-99.
   values=[]
   for i in range(a,min(b,len(w)),60):
    x=w[i:i+60];cent,low=spec(w[max(0,i-90):min(len(w),i+150)]);period=per(w[max(0,i-210):min(len(w),i+270)]);zero=[(i+j)/SR for j in range(1,len(x))if x[j-1]*x[j]<=0]
    values.append({'w_s':i/SR,'dB_2p5ms':lv(x),'preceding5ms_dB':lv(w[max(0,i-120):i]),'following5ms_dB':lv(w[i:i+120]),'periodicity20ms':period,'low150Hz_dB_10ms':low,'centroid_Hz_10ms':cent,'first4_zero_crossing_w_s':zero[:4]})
   profiles[label]={'dtype':str(w.dtype),'samples':len(w),'array_SHA256':hashlib.sha256(np.ascontiguousarray(w).tobytes()).hexdigest(),'reference_peak5ms_RMS':ref,'profile':values}
  phones=[{'phoneme':ph,'w_start_s':(st*it['scale']*SR-it['head'])/SR,'w_end_s':(en*it['scale']*SR-it['head'])/SR}for ph,st,en in it['toks']if ph.strip()and(en*it['scale']*SR-it['head'])/SR>p0/SR-.2 and(st*it['scale']*SR-it['head'])/SR<(p1+1)/SR+.2]
  ws=[{'phoneme_word':ph,'w_start_s':st,'w_end_s':en}for ph,st,en in words(it)if en>p0/SR-.35 and st<(p1+1)/SR+.35]
  rows.append({**window,'actual_original_to_w_samples_halfopen':[p0,p1+1],'actual_original_to_w_seconds':[p0/SR,(p1+1)/SR],'observed_window_raw_w_samples_halfopen':[a,b],'nearby_original_timed_phonemes':phones,'nearby_original_timed_word_groups':ws,'raw_and_actual_processed_scalar_profiles':profiles,'phoneme_labels_are_annotations_not_noise_or_confirmation_verdict':True})
 return rows
def recover_original_two_PV_tuples(m,T,normalized,whole,profile):
 """Original PCM16 quantization and original local scan on explicit sparse context."""
 np,SR=m.np,m.SR;require(m.sf.default_subtype('WAV')=='PCM_16','Original WAV default subtype differs')
 buffer=io.BytesIO();m.sf.write(buffer,normalized,SR,format='WAV',subtype='PCM_16');buffer.seek(0);pcm16,rate=m.sf.read(buffer)
 require(rate==SR and len(pcm16)==len(normalized),'Original private in-memory PCM16 container differs')
 selected=whole['phases']['selected'];clock=selected['actual_sample_clock']['S15'];context=np.zeros(selected['actual_complete_WAV']['samples'],float);offset=clock['start_sample'];context[offset:offset+len(pcm16)]=pcm16
 pv=load_module('_source35_original_local_PV',T/'纯人声核对.py');actual=pv.scan(context);expected={('呼吸声','100.72–100.83s'),('孤立杂音','102.67–102.72s')}
 require({(f[0],pv.key(f))for f in actual}==expected,'Original local scan did not reproduce exactly the two actual S15 flags')
 output=[]
 for row in profile['windows']:
  key=f"{row['global_span_s'][0]:.2f}–{row['global_span_s'][1]:.2f}s";f=next(f for f in actual if f[0]==row['kind']and pv.key(f)==key);given=row['actual_displayed_metrics'];measured=pv.实测(f)
  require(measured=={'最响dB':given['max_dB'],'重心Hz':given['centroid_Hz'],'周期':given['periodicity'],'低频dB':given['low_frequency_dB']}and round((f[2]-f[1])*1000)==given['duration_ms'],'Original local PV displayed complete metrics differ')
  output.append({**row,'native_displayed_span_s':row['global_span_s'],'global_span_s':[f[1],f[2]],'local_span_s':[(round(f[1]*SR)-offset)/SR,(round(f[2]*SR)-offset)/SR],'exact_reproduced_original_PV_tuple':list(f),'actual_reproduced_original_PV_metrics':measured,'raw_float_tuple_is_new_local_readonly_observation_not_previously_exported_native_precision':True})
 return output,{'source':'same exact S15 float argument, original WAV PCM16 writer in BytesIO, no filter or rescale','PCM16_quantized_samples':len(pcm16),'quantized_float_SHA256':hashlib.sha256(np.ascontiguousarray(pcm16).tobytes()).hexdigest(),'only_zeros_and_this_S15_sparse_clock_context_not_rebuilt_whole_or_whole_fingerprint':True,'container_or_audio_array_exported':False}
def main():
 p=argparse.ArgumentParser()
 for k in ['tools','video-root','inputs','profile','output']:p.add_argument('--'+k,type=Path,required=True)
 a=p.parse_args();T,M=a.tools.resolve(),a.video_root.resolve();W=M/'video';C=M/'tts/cache_tts';report={'kind':'source35_only_S15_two_actual_native_PV_windows_cached_original_scalar_no_quality_verdict','source_id':'35','target_sentence':'S15','diagnostic_completed':False,'quality_acceptance':False,'new_CF_or_source_write':False,'model_inference_authorized':False,'whole_build_or_GT_or_math_authorized':False,'errors':[],'restoration':{},'forbidden_model_events':[]};before=None;public=None;inp=None;wholemod=None;support=None;m=None;restore=None;old_boost=None;old_auto=None
 try:
  require(digest(a.profile)==PROFILE_SHA256,'Wrong target-only profile');profile=json.loads(a.profile.read_text());inp=bind_inputs(a.inputs,profile);source=json.loads(inp['source'].read_text());whole=json.loads(inp['whole_report'].read_text());failed=json.loads(inp['failed_proof'].read_text());validate_data(profile,source,whole,failed)
  require(all(os.environ.get(k)=='1'for k in ['STRICT_CACHE','XG_NOPUSH','AUDIO_ONLY','XG_KEEP_REVIEWED_GAIN','XG_KEEP_REVIEWED_ENDING','XG_KEEP_REVIEWED_CUTS']),'Original strict modes required');require(not any(os.environ.get(k)for k in ['VOICE','AFFILE','OLD_IV_VOID']),'Unapproved override')
  require(Path('/home/user/postgraduate-vocabulary').resolve()==T.parent.parent.resolve(),'Canonical ROOT alias differs');require(digest(T/'make_video.py')==digest(W/'make_video.py')==profile['maker_SHA256'],'Actual spoken20 maker differs')
  support=load_module('_source35_original_mother_support',inp['mother_helper']);wholemod=load_module('_source35_original_whole_guard_support',inp['whole_helper']);support.validate_certificate(T,json.loads(inp['overlay'].read_text()),json.loads(inp['certificate'].read_text()))
  require(digest(T/'疑点清单.py')==profile['dossier_SHA256']and digest(T/'纯人声核对.py')==profile['PV_SHA256']and digest(T/'发音词典/读音改正.json')==profile['dictionary_SHA256']and digest(T/'发音词典/按语境读音.json')==profile['context_SHA256'],'Original diagnostic/dictionary context differs')
  identity=json.loads(inp['identity'].read_text());require(all(digest(C/k)==v for k,v in identity['actual_four_private_files'].items()),'Actual four target cache files differ');require({k:digest(M/'tts'/k)for k in identity['models_SHA256']}==identity['models_SHA256']and digest(M/'tts/voice_mb.npy')==identity['voice_SHA256'],'Actual model/voice SHA differs')
  before=inventory(C);public=inventory(T.parent/'配音缓存');old_pcm=digest(W/'work_35/a.wav')if(W/'work_35/a.wav').is_file()else None
  with support.environment_and_cwd(W,report['restoration']):
   with support.source_namespace(W,inp['source'].read_bytes(),report['restoration']):
    for name in ['render','title2','clean','出片指纹']:sys.modules.pop(name,None)
    m=load_module('_source35_only_S15_actual_cached',W/'make_video.py');m._SPOKEN_SOURCE_NO='35';m._REPO_CACHE=str(M/'forbid-source35-S15-probe-public-export');require(not Path(m._REPO_CACHE).exists(),'Private sentinel already exists')
    require(m._OLDF and digest(m._OLDF)==profile['old_registry_SHA256']and digest(m._cand)==profile['dictionary_SHA256']and digest(m._CTX_PATH)==profile['context_SHA256'],'Fresh maker alias/registry context differs')
    np,SR=m.np,m.SR;sent=' '.join(m.re.sub(r'\*\*','',m.R.strip_gloss(c['en'])).strip()for c in source['sentences'][14]['chunks']);require(m.SENT_NO[sent]=='35','Source was not installed before fresh maker import')
    restore=wholemod.block_native(m,support,report['forbidden_model_events']);entries={r['method']:r for r in identity['cache_entries']};used=[]
    for meth,obj,model in [('create',m.k,'kokoro-v1.0.onnx'),('create_timed',m.KT,'kokoro-v1.0-timed.onnx')]:setattr(obj,meth,target_model_guard(m,np,C,meth,model,getattr(obj,meth),sent,entries,used))
    old_auto=m._auto_level
    def forbidden_math(*args,**kw):raise AssertionError('No target or other G36/G51 mathematics is authorized')
    m._auto_level=forbidden_math;capture={};old_boost=m._boost
    def observe_boost(w,items,label,off=0):
     require(label==sent and items=={'句末':[3.235,3.295,4.0]}and off==0 and not capture,'Only one actual S15 boost return may be observed')
     before_w=w.copy();value=old_boost(w,items,label,off=off);require(np.array_equal(w,before_w),'Original BOOST unexpectedly mutated input');capture.update({'before':before_w,'after':value.copy()});return value
    m._boost=observe_boost
    raw,_=m.k.create(m.spoken(sent),voice=m.V,speed=m.SPEED,lang='en-us');w0=m.clean_tail(raw)
    pieces=[];gaps=[];p0=0;listing=m.list_commas(sent)
    for mark in m._speech_marks(sent):pieces.append((p0,mark.end()));p0=mark.end()+1;gaps.append(m.P_LIST if mark.start()in listing else m.P_COMMA)
    pieces.append((p0,len(sent)));require(len(pieces)==1 and gaps==[],'Actual approved spoken S15 must have one piece')
    clips,tmap=m.sentence_audio(sent,pieces,gaps);clips,pcm,auto,manual=m.句增益(source,'35',14,sent,pieces,gaps,clips,tmap,np.concatenate(clips))
    target=whole['phases']['selected']['observed_sentences']['S15'];clock=whole['phases']['selected']['actual_sample_clock']['S15'];array_sha=lambda x:hashlib.sha256(np.ascontiguousarray(x).tobytes()).hexdigest()
    require(array_sha(pcm)==target['pre_master_PCM_sha256']==profile['pre_master_SHA256']and len(pcm)==78480,'Actual pre-master S15 buffer differs')
    require(m.SENT_FP[sent]=='6a4205ab64e1'and m.LAST['cuts']==[]and auto=={}and manual is None,'Actual target raw/control identity differs')
    normalized=pcm/np.float32(whole['phases']['selected']['actual_original_mastering']['pre_master_absolute_peak'])*.89
    require(array_sha(normalized)==clock['observed_post_master_float_PCM_sha256']==profile['post_master_SHA256'],'Original ordered normalization differs')
    it={'segs':[tuple(x[:3])+(list(x[3]),)for x in m.LAST['segs']],'toks':[(x.phoneme,x.start,x.end)for x in m.LAST['toks']],'scale':m.LAST['scale'],'head':m.LAST['head']}
    require(capture and len(it['toks'])>0,'Original boost or cached timed evidence not observed')
    actual_windows,quantization=recover_original_two_PV_tuples(m,T,normalized,whole,profile)
    report.update({'actual_cached_reads':used,'actual_source_first_SENT_NO':m.SENT_NO[sent],'actual_S15_plain_display':sent,'actual_S15_spoken_model_text':m.spoken(sent),'actual_target_pre_master_SHA256':array_sha(pcm),'actual_target_post_master_SHA256':array_sha(normalized),'actual_samples':len(pcm),'actual_master_normalization_order':'pcm / np.float32(actual whole absolute peak) * .89','actual_whole_absolute_peak':whole['phases']['selected']['actual_original_mastering']['pre_master_absolute_peak'],'actual_raw_fingerprint':m.SENT_FP[sent],'actual_raw_cuts':[],'actual_original_timed_scale':it['scale'],'actual_original_raw_head_samples':it['head'],'original_tmap':tmap,'original_source_control':source['除阻加强']['S15'],'two_actual_windows':scalar_profiles(np,SR,T/'疑点清单.py',it,w0,capture['before'],capture['after'],actual_windows),'original_PCM16_quantization_and_sparse_local_PV_diagnostic':quantization,'no_new_model_G36_GT_whole_producer_ASR_render_or_voice_export':True,'ROOT_semantic_classification_pending_no_CF_authored':True})
    m._boost=old_boost;m._auto_level=old_auto;restore();restore=None
  require((digest(W/'work_35/a.wav')if(W/'work_35/a.wav').is_file()else None)==old_pcm,'Normal private complete WAV changed');report['normal_existing_WAV_not_touched']=True;report['diagnostic_completed']=True
 except BaseException as e:report['errors'].append({'type':type(e).__name__,'detail':str(e)});traceback.print_exc()
 finally:
  try:
   if m is not None:
    if old_boost is not None:m._boost=old_boost
    if old_auto is not None:m._auto_level=old_auto
   if restore is not None:restore()
   if before is not None:
    report['all_existing_private_cache_bytes_unchanged']=inventory(C)==before;report['all_public_cache_bytes_unchanged']=inventory(T.parent/'配音缓存')==public;report['all_frozen_inputs_unchanged']=all(digest(p)==profile['inputs'][k]['sha256']for k,p in inp.items())
    require(all(report.get(k)is True for k in ['all_existing_private_cache_bytes_unchanged','all_public_cache_bytes_unchanged','all_frozen_inputs_unchanged','normal_existing_WAV_not_touched'])and all(report['restoration'].get(k)is True for k in ['normal_scripts_namespace_restored','environment_cwd_sys_path_restored'])and not report['forbidden_model_events'],'Original namespaces/cache/input/model guards did not restore')
  except BaseException as e:report['diagnostic_completed']=False;report['errors'].append({'type':type(e).__name__,'detail':str(e),'during':'restore'})
  for name in ['_source35_only_S15_actual_cached','_source35_original_mother_support','_source35_original_whole_guard_support','_source35_original_local_PV']:sys.modules.pop(name,None)
  gc.collect();a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,ensure_ascii=False,indent=2,default=lambda x:x.item())+'\n');print(json.dumps({'diagnostic_completed':report['diagnostic_completed'],'output_SHA256':digest(a.output),'errors':report['errors']},ensure_ascii=False))
 return 0 if report['diagnostic_completed']else 1
if __name__=='__main__':sys.exit(main())
