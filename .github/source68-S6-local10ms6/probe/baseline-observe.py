"""CODE-ONLY: two actual source68 cached sentences; no quality verdict, inference or whole build."""
from pathlib import Path
import argparse,ast,copy,gc,hashlib,importlib.util,io,json,math,os,re,sys,traceback
sys.dont_write_bytecode=True
PROFILE_SHA256='6ac2d576251651ef5d3ffdfd70f399c351b4af268df03d7259425027db128c7a'
SOURCE_NO='68';TARGETS=('S6','S2')
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

def validate_data(profile,source,whole,failed,actual):
 require(profile['source_id']=='68' and profile['book_order']==53 and profile['target_sentences']==['S6','S2'] and str(source['no'])=='68' and len(source['sentences'])==19,'Wrong bounded source/target role')
 require(whole['diagnostic_completed'] and whole['exact_scope_proved'] and not whole['errors'] and whole['actual_global_master_scale_ratio_selected_over_baseline']==1.0,'Actual completed whole reference required; this observer never builds it')
 require(actual['physical_metadata_precheck_ready'] is True and actual['errors']==[],'Actual native selected metadata prerequisite differs')
 for phase in [whole['phases']['selected'],actual['phases']['selected']]:
  require(phase['actual_complete_WAV']['file_sha256']==failed['internal_pcm_sha256']==profile['actual_selected_WAV_SHA256'],'Wrong actual selected whole WAV identity')
  require(phase['actual_complete_AAC']['AAC_ADTS_sha256']==failed['aac_adts_sha256']==profile['actual_selected_AAC_SHA256'],'Wrong actual selected AAC identity')
  for sid in TARGETS:
   expected=profile['expected'][sid]
   observed=copy.deepcopy(phase['observed_sentences'][sid]);wanted=copy.deepcopy(expected['observed'])
   if sid=='S2' and phase is whole['phases']['selected']:
    require(observed['effective_source_DSP']['区间声音指纹'] is None and wanted['effective_source_DSP']['区间声音指纹']==observed['actual_raw_w_fingerprint']=='7590b17b3cb1','Only actual A45 mother-identity field was added after measured whole')
    observed['effective_source_DSP']['区间声音指纹']=wanted['effective_source_DSP']['区间声音指纹']
   require(observed==wanted and phase['actual_sample_clock'][sid]==expected['clock'],'Wrong actual sentence identity '+sid)
   require(next(x for x in phase['original_G36_calls'] if x['sentence']==sid)==expected['original_G36'],'Wrong actual original math role '+sid)
 require(profile['S6_actual_displayed_window']=={'kind':'孤立杂音','key':'44.66–44.72s','duration_ms':60,'metrics':{'最响dB':-31.0,'重心Hz':3567,'周期':0.15,'低频dB':-12.6}},'Unknown PV observation scope')
 require(source['除阻加强']['S6']=={'句末':[9.025,9.085,3.5]} and source['区间声音指纹']['S6']=='3f9afd2d248b','Wrong original S6 boost/mother role')
 require(source['朗读删逗号']['S2']=={'篇号':68,'原文':'Its amenities included a lounge and, that year, a grand piano.','逗号序号':[1]},'Wrong S2 spoken input role')
 for sid in TARGETS:
  require(set(profile['cache_entries'][sid])=={'create','create_timed'},'Both authentic original mother entries required')
  for meth,row in profile['cache_entries'][sid].items():
   require(row['method']==meth and re.fullmatch('[0-9a-f]{40}\\.pkl',row['name']) and re.fullmatch('[0-9a-f]{64}',row['sha256']) and re.fullmatch('[0-9a-f]{64}',row['single_thread_marker_sha256']) and row['single_thread_marker_value']==row['sha256'][:16],'Wrong finite original cache identity')
 for sid in TARGETS:
  DSP=profile['expected'][sid]['observed']['effective_source_DSP']
  for key,value in DSP.items():require(source.get(key,{}).get(sid)==value,'Unknown source target DSP '+sid+'/'+key)

def target_model_guard(m,np,cache,method,model,original,sent,sid,entries,used):
 def guarded(text,voice,speed=1.0,lang='en-us',**kw):
  require(os.environ.get('STRICT_CACHE')=='1' and text==m.spoken(sent) and speed==.95 and lang=='en-us' and np.array_equal(voice,m.V),'Only exact active S6/S2 cached tuple authorized')
  require((method=='create' and kw=={}) or (method=='create_timed' and kw=={'clause_pause':0,'sentence_pause':0}),'Wrong original target cache kwargs')
  seen=[]
  def capture(actual_text,voice,speed=1.0,lang='en-us',**actualkw):
   mid=m._portable_mid(str(cache.parent/model));vh=hashlib.sha1(np.ascontiguousarray(voice).tobytes()).hexdigest()
   key=hashlib.sha1(repr((method,mid,actual_text,vh,float(speed),lang,sorted(actualkw.items()))).encode()).hexdigest()+'.pkl';row=entries[method]
   require(key==row['name'] and (cache/key).is_file() and not (cache/key).is_symlink() and (cache/(key+'.单线程')).is_file() and not (cache/(key+'.单线程')).is_symlink(),'Unknown, linked or missing raw/timed mother; no fallback')
   require(digest(cache/key)==row['sha256'] and digest(cache/(key+'.单线程'))==row['single_thread_marker_sha256'] and (cache/(key+'.单线程')).read_text().strip()==row['single_thread_marker_value'],'Actual original PKL or marker differs')
   require(hashlib.sha256(actual_text.encode()).hexdigest()==row['actual_model_input_sha256'],'Actual post-pron input differs')
   m._条目核对(str(cache/key))
   seen.append({'sentence':sid,'method':method,'name':key,'PKL_SHA256':digest(cache/key),'marker_SHA256':digest(cache/(key+'.单线程')),'actual_post_pron_input':actual_text,'actual_post_pron_input_SHA256':hashlib.sha256(actual_text.encode()).hexdigest(),'kwargs':actualkw})
  m._pron(capture)(text,voice=voice,speed=speed,lang=lang,**kw)
  require(len(seen)==1,'Original pronunciation wrapper ABI changed');used.append(seen[0])
  return original(text,voice=voice,speed=speed,lang=lang,**kw)
 return guarded

def original_existing_math_guard(m,observer,original,cache,sid,expected,used):
 def strict_read(clips,tmap,gaps,no='',rounds=2):
  require(str(no)=='68' and rounds==2 and os.environ.get('STRICT_CACHE')=='1','Original math scope must remain strict')
  current=m._auto_level;m._auto_level=original
  try:key=observer.auto_key(m,clips,tmap,gaps,no)
  finally:m._auto_level=current
  require(key==expected['original_key'] and key is not None,'Unmeasured original G36 key or group role')
  name='调平_'+key+'.json';p=cache/name
  require(p.is_file() and not p.is_symlink() and name==expected['file'] and digest(p)==expected['sha256'] and json.loads(p.read_text())==expected['value'],'Only exact saved existing regular G36 JSON permitted; no calculation')
  array_sha=lambda x:hashlib.sha256(m.np.ascontiguousarray(x).tobytes()).hexdigest()
  require([array_sha(x) for x in clips]==expected['clip_SHA256'] and [len(x) for x in clips]==expected['clip_samples'] and list(gaps)==expected['gaps'] and [list(x) for x in tmap]==expected['original_tmap'],'Actual original G36 inputs differ')
  before=digest(p);value=original(clips,tmap,gaps,no,rounds)
  require(value=={int(k):float(v) for k,v in expected['value'].items()} and digest(p)==before and os.environ.get('STRICT_CACHE')=='1','Original existing math changed')
  used.append({'sentence':sid,'file':name,'sha256':before,'value':value,'strict_before_and_after':True,'new_math':False})
  return value
 return strict_read

def original_dossier_functions(path,np,SR):
 names={'to_w','words','per','spec'};nodes=[n for n in ast.parse(path.read_text()).body if isinstance(n,ast.FunctionDef) and n.name in names]
 require(len(nodes)==4,'Original dossier AST shape differs');ns={'np':np,'SR':SR}
 exec(compile(ast.Module(body=nodes,type_ignores=[]),str(path),'exec'),ns);return ns

def raw_scalar_profile(np,SR,functions,it,arrays,span,coordinate='raw_w'):
 a,b=span;out={}
 for label,w in arrays.items():
  n=len(w)//120;ref=float(np.sqrt(np.mean(w[:n*120].reshape(n,120)**2,axis=1)).max());rows=[]
  lv=lambda x:20*math.log10(float(np.sqrt(np.mean(x*x)))/(ref+1e-12)+1e-9) if len(x) else -99.
  for i in range(max(0,a),min(len(w),b),60):
   x=w[i:i+60];c,lo=functions['spec'](w[max(0,i-90):min(len(w),i+150)]);period=functions['per'](w[max(0,i-210):min(len(w),i+270)])
   rows.append({'sample':i,'time_s':i/SR,'dB_2p5ms':lv(x),'preceding5ms_dB':lv(w[max(0,i-120):i]),'following5ms_dB':lv(w[i:i+120]),'periodicity20ms':period,'centroid_Hz_10ms':c,'low150Hz_dB_10ms':lo})
  out[label]={'coordinate':coordinate,'samples':len(w),'dtype':str(w.dtype),'array_SHA256':hashlib.sha256(np.ascontiguousarray(w).tobytes()).hexdigest(),'reference_peak5ms_RMS':ref,'profile':rows}
 return out

def original_segment_raw_to_sentence_sample(it,w_sample,SR):
 """Inverse of original dossier.to_w on the already-observed LAST segments."""
 for a,b,t0,removed in it['segs']:
  if a<=w_sample<b:
   relative=w_sample-a
   if any(x<=relative<y for x,y in removed):return None
   return round(t0*SR)+relative-sum(y-x for x,y in removed if y<=relative)
 return None

def original_burst_details(pv,a,f):
 np,SR,F=pv.np,pv.SR,pv.F;i0,i1=round(f[1]*SR),round(f[2]*SR);h=F//2
 result={'original_爆破起_result':pv.爆破起(a,f),'window_integer_samples':[i0,i1]}
 for s0,s1 in pv.segments(a):
  if s0<=i0<s1:
   seg=a[s0:s1];n=len(seg)//F;ref=float(np.sqrt(np.mean(seg[:n*F].reshape(n,F)**2,axis=1)).max())+1e-12
   lv=lambda x:20*math.log10(float(np.sqrt(np.mean(a[x:x+h]**2)))/ref+1e-12) if x>=0 and len(a[x:x+h])==h else -99.
   xs=list(range(max(0,i0-2*F),i1,h));on=next((x for x in xs if lv(x)>=-50),None)
   result.update({'original_segment_samples':[s0,s1],'reference_peak5ms_RMS':ref,'onset_sample':on,'profile2p5ms':[{'sample':x,'s':x/SR,'dB':lv(x)} for x in xs]})
   if on is not None:result.update({'before_onset_dB':lv(on-h),'peak_dB':max(lv(x) for x in xs if x>=on),'first5ms_peak_dB':max(lv(x) for x in range(on,on+F+1,h))})
   break
 return result

def original_PCM16_and_S6_scan(m,T,normalized,whole,profile,source):
 np,SR=m.np,m.SR;require(m.sf.default_subtype('WAV')=='PCM_16','Original WAV subtype changed')
 b=io.BytesIO();m.sf.write(b,normalized,SR,format='WAV',subtype='PCM_16');b.seek(0);pcm,rate=m.sf.read(b)
 require(rate==SR and len(pcm)==len(normalized),'Original PCM16 conversion shape differs')
 pv=load_module('_source68_bounded_original_PV',T/'纯人声核对.py');rows=[]
 for phase,label,key in [(whole['phases']['baseline'],'old_baseline','45.19–45.24s'),(whole['phases']['selected'],'actual_selected','44.66–44.72s')]:
  clock=phase['actual_sample_clock']['S6'];context=np.zeros(phase['actual_complete_WAV']['samples'],float);offset=clock['start_sample'];context[offset:offset+len(pcm)]=pcm
  fs=pv.scan(context);require(len(fs)==1 and fs[0][0]=='孤立杂音' and pv.key(fs[0])==key,'Original bounded S6 scan does not reproduce actual single flag')
  f=fs[0];require(pv.实测(f)==profile['S6_actual_displayed_window']['metrics'] and round((f[2]-f[1])*1000)==60,'Original local PV metrics differ from actual native')
  cf=copy.deepcopy(source['核对确认']['非人声']['45.19–45.24s']);candidate=copy.deepcopy(cf);candidate['词尾']='t'
  rows.append({'phase':label,'original_complete_f':list(f),'key':pv.key(f),'integer_samples':[round(f[1]*SR),round(f[2]*SR)],'duration_float':f[2]-f[1],'original_像吸气':pv.像吸气(f),'original_确认可收_unchanged_CF':pv.确认可收('68',f,cf,context),'original_确认可收_candidate_structured_t_in_memory_only':pv.确认可收('68',f,candidate,context),'original_burst_details':original_burst_details(pv,context,f),'local_span_s':[(round(f[1]*SR)-offset)/SR,(round(f[2]*SR)-offset)/SR]})
 return rows,{'original_PCM16_decoded_float_SHA256':hashlib.sha256(np.ascontiguousarray(pcm).tobytes()).hexdigest(),'samples':len(pcm),'bit_identity_basis':'Hard-matched actual native post-master float + unchanged original PCM16 writer; native per-sentence PCM16 hash was not separately exported. No independent native per-sentence hash invented.','sparse_context_only_this_sentence_and_zeros_not_a_rebuilt_whole':True,'waveform_exported':False}

def restore_modules(snapshot):
 for name in set(sys.modules)-set(snapshot):sys.modules.pop(name,None)
 for name,module in snapshot.items():sys.modules[name]=module
 require(set(sys.modules)==set(snapshot) and all(sys.modules[k] is v for k,v in snapshot.items()),'Module namespace did not restore')

def main():
 parser=argparse.ArgumentParser()
 for key in ['tools','video-root','inputs','profile','output']:parser.add_argument('--'+key,type=Path,required=True)
 a=parser.parse_args();T,M=a.tools.resolve(),a.video_root.resolve();W=M/'video';C=M/'tts/cache_tts'
 report={'kind':'source68_only_S6_S2_actual_cached_scalar_no_quality_verdict','source_id':'68','book_order':53,'diagnostic_completed':False,'quality_acceptance':False,'production_delivery_eligible':False,'new_CF_or_source_write':False,'whole_build_GT_ASR_render_TTS_new_math_authorized':False,'targets':{},'errors':[],'restoration':{},'forbidden_model_events':[]}
 snapshot=dict(sys.modules);before=public=inp=profile=support=observer=m=restore=methods=None;old_auto=old_boost=old_build=None;normal=None;normal_files=None
 try:
  require(digest(a.profile)==PROFILE_SHA256,'Wrong bounded exact profile');profile=json.loads(a.profile.read_text());inp=bind_inputs(a.inputs,profile)
  source=json.loads(inp['source'].read_text());whole=json.loads(inp['whole_report'].read_text());failed=json.loads(inp['failed_proof'].read_text());actual=json.loads(inp['actual_precheck'].read_text());validate_data(profile,source,whole,failed,actual)
  require(all(os.environ.get(k)=='1' for k in ['STRICT_CACHE','XG_NOPUSH','AUDIO_ONLY','XG_KEEP_REVIEWED_GAIN','XG_KEEP_REVIEWED_ENDING','XG_KEEP_REVIEWED_CUTS']) and not any(os.environ.get(k) for k in ['VOICE','AFFILE','OLD_IV_VOID']),'Exact original strict modes required')
  require(Path('/home/user/postgraduate-vocabulary').resolve()==T.parent.parent.resolve(),'Canonical ROOT alias differs')
  require(C.is_dir() and digest(T/'make_video.py')==digest(W/'make_video.py')==profile['maker_SHA256'],'Actual20 maker/cache role differs')
  support=load_module('_source68_bounded_mother_support',inp['support']);observer=load_module('_source68_bounded_whole_guard_support',inp['observer']);support.validate_certificate(T,json.loads(inp['overlay'].read_text()),json.loads(inp['certificate'].read_text()))
  for rel,key in [('疑点清单.py','dossier_SHA256'),('纯人声核对.py','PV_SHA256'),('发音词典/读音改正.json','dictionary_SHA256'),('发音词典/按语境读音.json','context_SHA256'),('新管/快测通过.json','stamp_SHA256')]:require(digest(T/rel)==profile[key],'Original tool/context differs '+rel)
  require({k:digest(M/'tts'/k) for k in profile['models_SHA256']}==profile['models_SHA256'] and digest(M/'tts/voice_mb.npy')==profile['voice_SHA256'],'Actual original models/voice identity differs')
  for entries in profile['cache_entries'].values():
   for row in entries.values():require(digest(C/row['name'])==row['sha256'] and digest(C/(row['name']+'.单线程'))==row['single_thread_marker_sha256'],'Required original finite PKL/marker missing or wrong')
  for sid in TARGETS:
   row=profile['expected'][sid]['original_G36'];require((C/row['file']).is_file() and not (C/row['file']).is_symlink() and digest(C/row['file'])==row['sha256'],'Required existing saved regular math missing; no generation')
  before=inventory(C);public=inventory(T.parent/'配音缓存');normal=(W/'work_68').stat().st_ino if (W/'work_68').exists() else None
  normal_files={str(p.relative_to(W/'work_68')):digest(p) for p in (W/'work_68').rglob('*') if p.is_file()}
  with support.environment_and_cwd(W,report['restoration']):
   with support.source_namespace(W,inp['source'].read_bytes(),report['restoration']):
    for name in ['render','title2','clean','出片指纹']:sys.modules.pop(name,None)
    m=load_module('_source68_only_two_actual_cached',W/'make_video.py');m._SPOKEN_SOURCE_NO='68';m._REPO_CACHE=str(M/'forbid-source68-bounded-public-export');require(not Path(m._REPO_CACHE).exists(),'Private sentinel unexpectedly exists')
    require(m._OLDF and digest(m._OLDF)==profile['old_registry_SHA256'] and digest(m._cand)==profile['dictionary_SHA256'] and digest(m._CTX_PATH)==profile['context_SHA256'],'Fresh actual ROOT dictionary/registry/context role differs')
    np,SR=m.np,m.SR;restore=observer.block_native(m,support,report['forbidden_model_events']);methods=(m.k.create,m.KT.create_timed);old_auto,old_boost,old_build=m._auto_level,m._boost,m.build
    def no_build(*args,**kw):raise AssertionError('No main/build/whole/render authorized')
    m.build=no_build
    functions=original_dossier_functions(T/'疑点清单.py',np,SR);used=[];math_reads=[]
    for sid in TARGETS:
     si=int(sid[1:])-1;sent=' '.join(m.re.sub(r'\*\*','',m.R.strip_gloss(c['en'])).strip() for c in source['sentences'][si]['chunks']);require(m.SENT_NO[sent]=='68','Source must precede fresh maker import')
     require(observer.dsp(source,sid)==profile['expected'][sid]['observed']['effective_source_DSP'],'Unknown target DSP')
     for meth,obj,model,original in [('create',m.k,'kokoro-v1.0.onnx',methods[0]),('create_timed',m.KT,'kokoro-v1.0-timed.onnx',methods[1])]:setattr(obj,meth,target_model_guard(m,np,C,meth,model,original,sent,sid,profile['cache_entries'][sid],used))
     m._auto_level=original_existing_math_guard(m,observer,old_auto,C,sid,profile['expected'][sid]['original_G36'],math_reads);capture={}
     def observe_boost(w,items,label,off=0):
      require(sid=='S6' and label==sent and items=={'句末':[9.025,9.085,3.5]} and off==0 and not capture,'Unknown target boost call')
      pre=w.copy();value=old_boost(w,items,label,off=off);require(np.array_equal(w,pre),'Original boost mutated input');capture.update(before=pre,after=value.copy());return value
     m._boost=observe_boost
     raw,rate=m.k.create(m.spoken(sent),voice=m.V,speed=m.SPEED,lang='en-us');require(rate==SR,'Raw sample rate changed');w0=m.clean_tail(raw)
     pieces=[];gaps=[];p0=0;listing=m.list_commas(sent)
     for mark in m._speech_marks(sent):pieces.append((p0,mark.end()));p0=mark.end()+1;gaps.append(m.P_LIST if mark.start() in listing else m.P_COMMA)
     pieces.append((p0,len(sent)));clips,tmap=m.sentence_audio(sent,pieces,gaps);clips,pcm,auto,manual=m.句增益(source,'68',si,sent,pieces,gaps,clips,tmap,np.concatenate(clips))
     expected=profile['expected'][sid];sha_array=lambda x:hashlib.sha256(np.ascontiguousarray(x).tobytes()).hexdigest()
     require(sha_array(pcm)==expected['observed']['pre_master_PCM_sha256'] and len(pcm)==expected['observed']['samples'],'Actual pre-master identity differs '+sid)
     require(m.SENT_FP[sent]==expected['observed']['actual_raw_w_fingerprint'] and [list(x) for x in m.LAST['cuts']]==expected['observed']['actual_raw_cuts'] and auto=={int(k):float(v) for k,v in expected['observed']['automatic_gain_dB'].items()} and manual==expected['observed']['manual_gain_dB'],'Actual original raw/cuts/gain differs '+sid)
     require([sha_array(x) for x in clips]==expected['observed']['piece_clips_sha256'],'Actual post-gain piece buffers differ '+sid)
     normalized=pcm/np.float32(whole['phases']['selected']['actual_original_mastering']['pre_master_absolute_peak'])*.89
     require(sha_array(normalized)==expected['clock']['observed_post_master_float_PCM_sha256'],'Original ordered master normalization differs '+sid)
     it={'segs':[tuple(x[:3])+(list(x[3]),) for x in m.LAST['segs']],'toks':[(x.phoneme,x.start,x.end) for x in m.LAST['toks']],'scale':m.LAST['scale'],'head':m.LAST['head']}
     words=functions['words'](it);phones=[{'phoneme':ph,'w_start_s':(st*it['scale']*SR-it['head'])/SR,'w_end_s':(en*it['scale']*SR-it['head'])/SR} for ph,st,en in it['toks']]
     item={'plain_display':sent,'actual_post_pron_cached_reads':[x for x in used if x['sentence']==sid],'pre_master_SHA256':sha_array(pcm),'post_master_float_SHA256':sha_array(normalized),'samples':len(pcm),'raw_FP':m.SENT_FP[sent],'raw_cuts':m.LAST['cuts'],'scale':it['scale'],'head_samples':it['head'],'original_tmap':tmap,'timed_phonemes':phones,'original_word_groups':words,'labels_are_annotation_not_ASR_or_quality_verdict':True};report['targets'][sid]=item
     if sid=='S6':
      require(capture,'Original S6 boost not observed');rows,quant=original_PCM16_and_S6_scan(m,T,normalized,whole,profile,source);item.update(original_scan_both_absolute_clocks=rows,PCM16_identity=quant)
      lo,hi=rows[1]['local_span_s'];p0=functions['to_w'](it,lo);p1=functions['to_w'](it,hi-1/SR);require(p0 is not None and p1 is not None,'Actual S6 PV maps into inserted gap')
      item['PV_raw_samples_halfopen']=[p0,p1+1];item['raw_scalar_profiles']=raw_scalar_profile(np,SR,functions,it,{'original_clean_tail_raw':w0,'actual_boost_input':capture['before'],'actual_boost_return':capture['after']},[max(0,p0-1920),min(max(len(w0),len(capture['after'])),p1+1+1920)])
     else:
      require(not capture,'No S2 boost authorized');actual_text=next(x['actual_post_pron_input'] for x in used if x['sentence']=='S2' and x['method']=='create');textwords=re.findall(r"[A-Za-z]+(?:['’][A-Za-z]+)?",actual_text)
      item['orthographic_word_alignment_only_if_exact_group_count']=dict(words=textwords,orthographic_count=len(textwords),timed_group_count=len(words),unambiguous=(len(textwords)==len(words) and textwords.count('and')==1))
      require(len(textwords)==len(words) and textwords.count('and')==1,'S2 original timed word groups cannot be assigned unambiguously; no guessed and label')
      k=textwords.index('and');near=words[max(0,k-1):min(len(words),k+2)];item['and_and_neighbors']=[{'orthography':textwords[j],'original_timed_phoneme_word':words[j][0],'w_start_s':words[j][1],'w_end_s':words[j][2]} for j in range(max(0,k-1),min(len(words),k+2))]
      a0=max(0,round(near[0][1]*SR)-120);a1=min(len(w0),round(near[-1][2]*SR)+120);item['and_neighbor_raw_samples_halfopen']=[a0,a1];item['raw_scalar_profiles']=raw_scalar_profile(np,SR,functions,it,{'original_clean_tail_raw':w0},[a0,a1])
      l0=original_segment_raw_to_sentence_sample(it,a0,SR);l1=original_segment_raw_to_sentence_sample(it,a1-1,SR)
      require(l0 is not None and l1 is not None and 0<=l0<=l1<len(normalized),'Actual and-neighbor raw range falls in a removed interval; no guessed mapping')
      require(functions['to_w'](it,l0/SR)==a0 and functions['to_w'](it,l1/SR)==a1-1,'Original raw-to-local-to-raw mapping did not roundtrip exactly')
      b=io.BytesIO();m.sf.write(b,normalized,SR,format='WAV',subtype='PCM_16');b.seek(0);pcm16,rate=m.sf.read(b);require(rate==SR and len(pcm16)==len(normalized),'Original S2 PCM16 conversion differs')
      item['and_neighbor_actual_sentence_samples_halfopen']=[l0,l1+1];item['and_neighbor_actual_global_samples_halfopen']=[expected['clock']['start_sample']+l0,expected['clock']['start_sample']+l1+1]
      item['actual_processed_acoustic_profiles']=raw_scalar_profile(np,SR,functions,it,{'actual_post_master_float':normalized,'original_PCM16_writer_decoded':pcm16},[l0,l1+1],coordinate='actual_sentence_local')
      item['original_segments_raw_to_sentence_mapping']=it['segs'];item['ASR_not_run_or_classified']=True
     m._boost=old_boost;m._auto_level=old_auto;m.k.create,m.KT.create_timed=methods
    report['actual_cache_reads']=used;report['actual_existing_G36_reads']=math_reads;report['actual_original_master_absolute_peak']=whole['phases']['selected']['actual_original_mastering']['pre_master_absolute_peak']
    m.build=old_build;restore();restore=None
  current_inode=(W/'work_68').stat().st_ino if (W/'work_68').exists() else None
  require(current_inode==normal and {str(p.relative_to(W/'work_68')):digest(p) for p in (W/'work_68').rglob('*') if p.is_file()}==normal_files,'Original normal work inode/files changed')
  report['normal_work_inode_and_files_unchanged']=True;report['diagnostic_completed']=True
 except BaseException as error:report['errors'].append({'type':type(error).__name__,'detail':str(error)});traceback.print_exc()
 finally:
  try:
   if m is not None:
    if old_auto is not None:m._auto_level=old_auto
    if old_boost is not None:m._boost=old_boost
    if old_build is not None:m.build=old_build
    if methods is not None:m.k.create,m.KT.create_timed=methods
   if restore is not None:restore()
   if before is not None:
    if normal_files is not None:
     report['normal_work_inode_and_files_unchanged']=((W/'work_68').stat().st_ino if (W/'work_68').exists() else None)==normal and {str(p.relative_to(W/'work_68')):digest(p) for p in (W/'work_68').rglob('*') if p.is_file()}==normal_files
    report['all_private_cache_bytes_unchanged']=inventory(C)==before;report['all_public_cache_bytes_unchanged']=inventory(T.parent/'配音缓存')==public;report['all_frozen_inputs_unchanged']=all(digest(p)==profile['inputs'][k]['sha256'] for k,p in inp.items())
    require(all(report.get(k) is True for k in ['all_private_cache_bytes_unchanged','all_public_cache_bytes_unchanged','all_frozen_inputs_unchanged','normal_work_inode_and_files_unchanged']) and all(report['restoration'].get(k) is True for k in ['normal_scripts_namespace_restored','environment_cwd_sys_path_restored']) and not report['forbidden_model_events'],'Original cached observer restoration/forbidden-entry guard failed')
  except BaseException as error:report['diagnostic_completed']=False;report['errors'].append({'type':type(error).__name__,'detail':str(error),'during':'restore'})
  restore_modules(snapshot);report['all_original_module_identities_restored']=True;gc.collect()
  a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,ensure_ascii=False,indent=2,default=lambda x:x.item())+'\n');print(json.dumps({'diagnostic_completed':report['diagnostic_completed'],'output_SHA256':digest(a.output),'errors':report['errors']},ensure_ascii=False))
 return 0 if report['diagnostic_completed'] else 1
if __name__=='__main__':sys.exit(main())
