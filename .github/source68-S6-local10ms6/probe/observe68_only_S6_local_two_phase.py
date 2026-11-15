"""Original cached local two-phase S6 measurement; never whole, TTS, GT or ASR."""
from pathlib import Path
import argparse,copy,gc,hashlib,importlib.util,inspect,io,json,os,re,shutil,sys,traceback
sys.dont_write_bytecode=True
ROOT_SHA='185b3e1502aeb77d1af7bac4c7f05af298924c49e2f0b9448db6313b127a6da2'
PROFILE_SHA='a161336f87e1965c80a0bbcbd57c653290439386e42a48cff75c82ae9e1bb9c9'
TAIL_SHAPE_SHA='ff59708ea754b5d3817448f20e023b6283603a99168ba35c4cd894df63d0d326'
BASELINE_HELPER_SHA='d53aebdd61c992473b6f3f455c23a852b979cd3fe8dce11f3fad35c576851ea4'
BASELINE_PROFILE_SHA='6ac2d576251651ef5d3ffdfd70f399c351b4af268df03d7259425027db128c7a'
OLD_SOURCE_SHA='e122c817946c4ed6e7cd1394749879276ef2afe9d01ad691b4142c6bbd9ec9b4'
NEW_SOURCE_SHA='875ed85c326ef888183591646ab4727cc9b5f286377cac0ae3614dc23d5501d8'
OLD_BOOST={'句末':[9.025,9.085,3.5]};NEW_BOOST={'句末':[9.025,9.035,6.0]}
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def require(x,msg):
 if not x:raise AssertionError(msg)
def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m
def restore_task_owned_modules(snapshot,roots):
 # Extension modules retain their actual loaded lifetime. Only new modules
 # physically owned by this exact task are removed; all preexisting object
 # identities are restored. New external libraries are explicitly reported.
 roots=tuple(Path(p).resolve() for p in roots);removed=[]
 for name in set(sys.modules)-set(snapshot):
  module=sys.modules.get(name);filename=getattr(module,'__file__',None)
  owned=False
  if filename:
   path=Path(filename).resolve()
   owned=any(path.is_relative_to(root) for root in roots)
  if owned:sys.modules.pop(name,None);removed.append(name)
 for name,module in snapshot.items():sys.modules[name]=module
 retained=sorted(set(sys.modules)-set(snapshot))
 require(all(sys.modules.get(k) is v for k,v in snapshot.items()),'Preexisting module object identity was not restored')
 for name in retained:
  filename=getattr(sys.modules.get(name),'__file__',None)
  require(not filename or not any(Path(filename).resolve().is_relative_to(root) for root in roots),'Task-owned module leaked after restoration')
 return {'preexisting_module_object_identities_restored':True,'new_task_owned_modules_removed':sorted(removed),'new_non_task_library_modules_retained':retained,'namespace_key_set_exact':set(sys.modules)==set(snapshot),'third_party_extensions_unloaded':False}
def inventory(path):
 return {p.name:digest(p) for p in Path(path).iterdir() if p.is_file()}
def exact_delta(old,new):
 require(old['除阻加强']['S6']==OLD_BOOST and new['除阻加强']['S6']==NEW_BOOST,'Exact one original boost data leaf required')
 undo=copy.deepcopy(new);undo['除阻加强']['S6']=copy.deepcopy(OLD_BOOST)
 require(undo==old,'Any source/English/CF/non-target change is forbidden')
 require(len(new['sentences'])==19 and str(new['no'])=='68','Wrong source schema')
def cache_scope(before,after,new_math):
 return (all(after.get(k)==v for k,v in before.items()) and not(set(before)-set(after)) and set(after)-set(before)==set(new_math) and len(new_math)<=1 and all(after.get(k)==v['sha256'] for k,v in new_math.items()))
def selected_shape_contract(adoption,evidence,baseline):
 require(adoption['source_id']=='68' and adoption['target_sentence']=='S6' and adoption['prior_scope_185b_and2efa_continue'] is True,'Wrong actual ROOT A20 selected scope')
 actual=evidence['actual_candidate_boost_and_premath_prefix']['actual_original_candidate_before_math_guard'];specific=adoption['specific_selected_pre_math']
 require(actual==specific,'Actual candidate scalar must exactly equal ROOT-selected original A20 evidence')
 require(baseline['clip_samples']==adoption['old_expected_baseline_shape']==[45240,9120,159960] and baseline['original_tmap']==specific['unchanged_expected_tmap'] and baseline['gaps']==specific['unchanged_expected_gaps'],'Original baseline geometry must remain old214320/8.93 exact')
 require(specific['clip_samples']==[45240,9120,159840] and sum(specific['clip_samples'])==adoption['specific_selected_total_samples']==214200 and specific['actual_tmap']==[[0,27,0.,1.885],[28,135,2.265,8.925]] and specific['actual_gaps']==[.4],'Only actual selected original A20 5ms shape permitted')
 expected=copy.deepcopy(baseline);expected.update(clip_samples=specific['clip_samples'],original_tmap=specific['actual_tmap'],gaps=specific['actual_gaps'],selected_actual_guard=copy.deepcopy(specific));return expected

def validate_selected_pre_math(actual,expected):
 e=expected['selected_actual_guard']
 fields=['clip_samples','clip_dtypes','clip_SHA256','clip_absolute_peaks','actual_tmap','actual_gaps','actual_original_LAST','actual_timed_last10_phonemes']
 require(all(json.loads(json.dumps(actual[k]))==e[k] for k in fields),'Candidate selected A20 geometry/SHA/LAST/timed-tail differs from actual ROOT bound scalar')
 require(sum(actual['clip_samples'])==214200,'Candidate selected total differs')

def validate_selected_post_math(m,sent,clips,tmap,gaps,pcm,expected):
 e=expected['selected_actual_guard'];last={k:m.LAST[k] for k in ['head','hs','scale','segs','total','cuts','gaps','fades','grafts']}
 require(m.SENT_FP[sent]=='3f9afd2d248b' and len(pcm)==214200 and [len(x) for x in clips]==expected['clip_samples'] and [list(x) for x in tmap]==expected['original_tmap'] and list(gaps)==expected['gaps'] and json.loads(json.dumps(last))==e['actual_original_LAST'],'Candidate raw mother/selected original A20 duration/tmap/LAST changed')

def guarded_original_math(m,observer,original,cache,expected,boost_capture,source_path,reads,new_math):
 calls=[]
 def strict(clips,tmap,gaps,no='',rounds=2):
  require(str(no)=='68' and rounds==2 and os.environ.get('STRICT_CACHE')=='1','Math must enter original strict source68/rounds2')
  require(digest(source_path)==NEW_SOURCE_SHA and boost_capture.get('original_candidate_guard_passed') is True,'Candidate source/original boost must genuinely pass before math')
  require(not calls,'Only one selected S6 G36 invocation permitted');calls.append(True)
  last=m.LAST;SR=m.SR;head=last['head'];scale=last['scale']
  boost_capture['actual_original_candidate_before_math_guard']={'clip_samples':[len(x) for x in clips],'clip_dtypes':[str(x.dtype) for x in clips],'clip_SHA256':[hashlib.sha256(m.np.ascontiguousarray(x).tobytes()).hexdigest() for x in clips],'clip_absolute_peaks':[float(m.np.abs(x).max()) if len(x) else 0. for x in clips],'actual_tmap':[list(x) for x in tmap],'actual_gaps':list(gaps),'unchanged_expected_clip_samples':expected['clip_samples'],'unchanged_expected_tmap':expected['original_tmap'],'unchanged_expected_gaps':expected['gaps'],'shape_equal': [len(x) for x in clips]==expected['clip_samples'],'tmap_equal':[list(x) for x in tmap]==expected['original_tmap'],'gaps_equal':list(gaps)==expected['gaps'],'actual_original_LAST':{k:last[k] for k in ['head','hs','scale','segs','total','cuts','gaps','fades','grafts']},'actual_timed_last10_phonemes':[{'phoneme':t.phoneme,'timed_start_s':t.start,'timed_end_s':t.end,'raw_w_start_sample':round(t.start*scale*SR)-head,'raw_w_end_sample':round(t.end*scale*SR)-head} for t in list(last['toks'])[-10:]],'timed_annotation_not_ASR_or_safety_acceptance':True,'original_math_or_new_key_not_yet_executed':True}
  validate_selected_pre_math(boost_capture['actual_original_candidate_before_math_guard'],expected)
  require([len(x) for x in clips]==expected['clip_samples'] and list(gaps)==expected['gaps'] and [list(x) for x in tmap]==expected['original_tmap'],'Candidate original duration/tmap/gaps changed')
  cur=m._auto_level;m._auto_level=original
  try:key=observer.auto_key(m,clips,tmap,gaps,no)
  finally:m._auto_level=cur
  require(re.fullmatch('[0-9a-f]{40}',key or '') and key!=expected['original_key'],'Candidate must derive its true different original key, not old bb23')
  name='调平_'+key+'.json';p=cache/name;existed=p.exists()
  require(not p.is_symlink() and (not existed or p.is_file()),'Math key is not a regular actual entry')
  row={'sentence':'S6','phase':'candidate-local','original_key':key,'file':name,'existing':existed,'clip_SHA256':[hashlib.sha256(m.np.ascontiguousarray(x).tobytes()).hexdigest() for x in clips],'clip_samples':[len(x) for x in clips],'gaps':list(gaps),'tmap':copy.deepcopy(tmap),'actual_math_created':False}
  if existed:
   before=digest(p);saved=json.loads(p.read_text());value=original(clips,tmap,gaps,no,rounds)
   require(digest(p)==before,'Existing original math bytes changed')
   row['sha256']=before;row['original_saved_value']=saved
  else:
   require(not new_math,'At most one actual new S6 math file allowed')
   os.environ.pop('STRICT_CACHE')
   try:value=original(clips,tmap,gaps,no,rounds)
   finally:os.environ['STRICT_CACHE']='1'
   require(p.is_file() and not p.is_symlink(),'Original S6 math did not create its normal actual key')
   new_math[name]={'sha256':digest(p),'value':json.loads(p.read_text()),'source_id':'68','target_sentence':'S6','strict_readback_exact':False}
   row['actual_math_created']=True
  require(os.environ.get('STRICT_CACHE')=='1','STRICT_CACHE failed to restore')
  before=digest(p);readback=original(clips,tmap,gaps,no,rounds)
  require(value==readback and digest(p)==before,'Original strict key readback/value differs')
  if name in new_math:new_math[name]['strict_readback_exact']=True
  row.update(value=value,sha256=digest(p),strict_readback_exact=True);reads.append(row);return value
 return strict
def write_guard(m,original_auto,original_write,events):
 def guarded(path,*args,**kwargs):
  if isinstance(path,io.BytesIO):return original_write(path,*args,**kwargs)
  frame=inspect.currentframe().f_back
  if frame.f_code is original_auto.__code__ and str(path)==os.path.join(frame.f_locals.get('td',''),'s.wav'):
   require(os.environ.get('STRICT_CACHE') is None,'Only actual original missing-key math may write its internal temporary WAV')
   return original_write(path,*args,**kwargs)
  events.append('forbidden_non_math_physical_audio_write');raise AssertionError('No physical audio export or whole write allowed')
 return guarded
def local_gate_decision(burst,rows):
 # Old CF comparisons are historical counterfactual diagnostics, never an
 # actual current key+whole-fingerprint confirmation. Any flag remains pending.
 return bool(burst and not rows)
def actual_local_PV(base,m,T,normalized,whole,source,prior):
 b=io.BytesIO();m.sf.write(b,normalized,m.SR,format='WAV',subtype='PCM_16');b.seek(0);pcm,rate=m.sf.read(b)
 require(rate==m.SR and len(pcm)==len(normalized),'Original PCM16 memory conversion ABI changed')
 pv=load('_onlyS6_original_PV_candidate',T/'纯人声核对.py');phase=whole['phases']['selected'];clock=phase['actual_sample_clock']['S6'];context=m.np.zeros(phase['actual_complete_WAV']['samples'],float)
 offset=clock['start_sample'];context[offset:offset+len(pcm)]=pcm
 cf=source['核对确认']['非人声']['45.19–45.24s'];rows=[]
 for f in pv.scan(context):
  ok,reason=pv.确认可收('68',f,cf,context)
  rows.append({'original_complete_f':list(f),'key':pv.key(f),'original_metrics':pv.实测(f),'original_像吸气':pv.像吸气(f),'original_爆破起':pv.爆破起(context,f),'historical_CF_counterfactual_comparison_only':[ok,reason],'historical_CF_not_current_key_or_new_whole_fingerprint_acceptance':True,'unchanged_CF_source_path':'/核对确认/非人声/45.19–45.24s','original_burst_details':base.original_burst_details(pv,context,f)})
 fixed=prior['targets']['S6']['original_scan_both_absolute_clocks'][1]['original_complete_f']
 burst=base.original_burst_details(pv,context,fixed)
 # This uses only the prior window times to locate the acoustic onset. Fixed f
 # spectral fields remain historical and are never reused as new PV metrics.
 result={'coordinate':'baseline-current S6 start clock; actual selected A20 tail5ms shorter; later whole clocks unmeasured','mastering_role':'conditional normalization using original baseline whole peak only; no new whole/master1 claim','all_original_candidate_scan_flags':rows,'original_burst_at_fixed_old_window':burst,'fixed_window_tuple_role':'Only times locate current measured onset; historical spectral metrics not asserted current','candidate_original_PCM16_decoded_SHA256':hashlib.sha256(m.np.ascontiguousarray(pcm).tobytes()).hexdigest(),'waveform_or_container_exported':False,'CF_mutated':False}
 passed=local_gate_decision(burst['original_爆破起_result'],rows)
 return result,passed
def run_candidate(a,profile,inp,base,baseline,report,new_math):
 T,M=a.tools.resolve(),a.video_root.resolve();W=M/'video';C=M/'tts/cache_tts';source=Path(inp['selected_source']);oldprofile=json.loads(inp['baseline_profile'].read_text());oldsource=json.loads(inp['source'].read_text());candidate=json.loads(source.read_text());exact_delta(oldsource,candidate)
 require(digest(W/'scripts/68.json')==OLD_SOURCE_SHA,'Fresh private setup must still contain exact current baseline source')
 require(all(os.environ.get(k)=='1' for k in ['STRICT_CACHE','AUDIO_ONLY','XG_NOPUSH','XG_KEEP_REVIEWED_GAIN','XG_KEEP_REVIEWED_ENDING','XG_KEEP_REVIEWED_CUTS']) and not any(os.environ.get(k) for k in ['VOICE','AFFILE','OLD_IV_VOID','ONLY','BREATH_FRAC','CACHE_LOG']),'No override or relaxed acoustic threshold permitted')
 support=load('_onlyS6_original_support',inp['support']);observer=load('_onlyS6_original_whole_primitives',inp['observer'])
 require(support.SOURCE_NO=='68' and support.TARGET=='S2','Original mother provenance TARGET must remain S2')
 public_path=T.parent/'配音缓存';before=inventory(C);public=inventory(public_path);normal=(W/'work_68').stat().st_ino if (W/'work_68').exists() else None;normalfiles={str(p.relative_to(W/'work_68')):digest(p) for p in (W/'work_68').rglob('*') if p.is_file()}
 live={T/'发音词典/读音改正.json':oldprofile['dictionary_SHA256'],T/'发音词典/按语境读音.json':oldprofile['context_SHA256'],T/'新管/快测通过.json':oldprofile['stamp_SHA256'],T/'纯人声核对.py':oldprofile['PV_SHA256'],T/'疑点清单.py':oldprofile['dossier_SHA256'],M/'tts/voice_mb.npy':oldprofile['voice_SHA256'],M/'tts/AF.txt':json.loads(inp['whole_report'].read_text())['phases']['selected']['AF_sha256']}
 live.update({M/'tts'/k:v for k,v in oldprofile['models_SHA256'].items()})
 g27=load('_onlyS6_actual_original_G27_paths',T/'出片指纹.py');actual_modules=g27.清单([str(T)])
 require(len(actual_modules)==8 and set(actual_modules)==set(profile['original_G27_expected']),'Original actual eight-module map differs')
 require(g27.核对工作目录(str(W),str(T))==[],'Original G27 work paths differ')
 for name,p in actual_modules.items():
  q=g27._找(name,g27.工作目录搜(str(W)));require(q is not None,'Original G27 resolved import missing '+name)
  live[Path(p)]=profile['original_G27_expected'][name];live[Path(q)]=profile['original_G27_expected'][name]
 require(all(digest(p)==h for p,h in live.items()),'Actual model/voice/filter/dictionary/context/tool input differs before candidate')
 m=restore=methods=old_auto=old_boost=old_write=old_build=old_title=None;used=[];reads=[];capture={};sentinel=M/'forbid-onlyS6-local-public-cache-export';require(not sentinel.exists(),'Private public-cache sentinel already exists')
 try:
  with support.environment_and_cwd(W,report['restoration']):
   with support.source_namespace(W,source.read_bytes(),report['restoration']):
    for name in ['render','title2','clean','出片指纹']:sys.modules.pop(name,None)
    m=load('_onlyS6_selected_fresh_source_first_maker',W/'make_video.py');m._SPOKEN_SOURCE_NO='68';m._REPO_CACHE=str(sentinel)
    require(m._OLDF and digest(m._OLDF)==oldprofile['old_registry_SHA256'] and digest(m._cand)==oldprofile['dictionary_SHA256'] and digest(m._CTX_PATH)==oldprofile['context_SHA256'],'Original source-first registry/dictionary/context differs')
    require(digest(T/'make_video.py')==digest(W/'make_video.py')==oldprofile['maker_SHA256'],'Original maker bytes changed')
    np,SR=m.np,m.SR;restore=observer.block_native(m,support,report['forbidden_model_events']);methods=(m.k.create,m.KT.create_timed);old_auto,old_boost,old_write,old_build,old_title=m._auto_level,m._boost,m.sf.write,m.build,m.title_audio
    def forbid(*args,**kwargs):report['forbidden_model_events'].append('forbidden_whole_or_title');raise AssertionError('No whole/build/title execution allowed')
    m.build=m.title_audio=forbid;m.sf.write=write_guard(m,old_auto,old_write,report['forbidden_model_events'])
    sent=' '.join(m.re.sub(r'\*\*','',m.R.strip_gloss(c['en'])).strip() for c in candidate['sentences'][5]['chunks']);require(m.SENT_NO[sent]=='68','Source must precede maker import')
    expected=copy.deepcopy(oldprofile['expected']['S6']);expected['original_G36']=selected_shape_contract(json.loads(inp['actual_tail_shape_scope'].read_text()),json.loads(inp['actual_tail_shape_evidence'].read_text()),oldprofile['expected']['S6']['original_G36']);prior=json.loads(inp['actual_bounded'].read_text());target_prior=prior['targets']['S6'];sha=lambda x:hashlib.sha256(np.ascontiguousarray(x).tobytes()).hexdigest()
    def guarded_boost(w,items,label,off=0):
     require(items==NEW_BOOST and label==sent and off==0 and not capture,'Only one exact new S6 original boost allowed')
     before_w=w.copy();require(sha(before_w)==target_prior['raw_scalar_profiles']['actual_boost_input']['array_SHA256'],'Actual unchanged unboosted S6 input differs')
     old_result=old_boost(w,OLD_BOOST,label,off=off);require(sha(old_result)==target_prior['raw_scalar_profiles']['actual_boost_return']['array_SHA256'],'Old original boost on same unchanged input differs')
     value=old_boost(w,items,label,off=off);p,q=round(9.025*SR),round(9.035*SR)
     require(np.array_equal(w,before_w) and value.dtype==before_w.dtype and value.shape==before_w.shape and np.array_equal(value[:p],before_w[:p]) and np.array_equal(value[q:],before_w[q:]),'Original boost mutated input or changed samples outside exact interval')
     require(not np.array_equal(value,old_result),'Candidate actual original boost unchanged')
     capture.update(original_candidate_guard_passed=True,original_input_SHA256=sha(before_w),old_boost_return_SHA256=sha(old_result),new_boost_return_SHA256=sha(value),outside_exact_interval_unchanged=True,interval_samples_halfopen=[p,q],input=before_w,output=value.copy());return value
    m._boost=guarded_boost
    for meth,obj,model,original in [('create',m.k,'kokoro-v1.0.onnx',methods[0]),('create_timed',m.KT,'kokoro-v1.0-timed.onnx',methods[1])]:setattr(obj,meth,base.target_model_guard(m,np,C,meth,model,original,sent,'S6',oldprofile['cache_entries']['S6'],used))
    m._auto_level=guarded_original_math(m,observer,old_auto,C,expected['original_G36'],capture,W/'scripts/68.json',reads,new_math)
    pieces=[];gaps=[];p0=0;listing=m.list_commas(sent)
    for mark in m._speech_marks(sent):pieces.append((p0,mark.end()));p0=mark.end()+1;gaps.append(m.P_LIST if mark.start() in listing else m.P_COMMA)
    pieces.append((p0,len(sent)));clips,tmap=m.sentence_audio(sent,pieces,gaps);clips,pcm,auto,manual=m.句增益(candidate,'68',5,sent,pieces,gaps,clips,tmap,np.concatenate(clips))
    require(capture.get('original_candidate_guard_passed') and len(reads)==1,'Actual original candidate boost/math not observed')
    validate_selected_post_math(m,sent,clips,tmap,gaps,pcm,expected['original_G36'])
    peak=np.float32(baseline['actual_original_master_absolute_peak']);normalized=pcm/peak*.89
    pv,passed=actual_local_PV(base,m,T,normalized,json.loads(inp['whole_report'].read_text()),oldsource,prior)
    functions=base.original_dossier_functions(T/'疑点清单.py',np,SR)
    profiles=base.raw_scalar_profile(np,SR,functions,{}, {'same_original_boost_input':capture['input'],'new_original_boost_return':capture['output']},[round(8.95*SR),round(9.12*SR)])
    report['candidate']={'actual_source_SHA256':NEW_SOURCE_SHA,'baseline_source_SHA256':OLD_SOURCE_SHA,'plain_English':sent,'raw_FP':m.SENT_FP[sent],'samples':len(pcm),'pre_master_SHA256':sha(pcm),'conditional_post_master_float_SHA256':sha(normalized),'conditional_master_peak_from_actual_baseline':float(peak),'candidate_own_absolute_peak':float(np.abs(pcm).max()),'new_whole_master_scale_or_identity_claimed':False,'automatic_gain_dB':auto,'manual_gain_dB':manual,'clips_SHA256':[sha(x) for x in clips],'original_tmap':tmap,'original_gaps':gaps,'original_raw_cuts':m.LAST['cuts'],'original_boost':{k:v for k,v in capture.items() if k not in ['input','output']},'actual_raw_profiles':profiles,'original_local_PV_and_burst':pv}
    peak_compatible=bool(np.abs(pcm).max()<=peak)
    report['candidate']['baseline_global_peak_not_exceeded_prerequisite_only']=peak_compatible
    report['actual_candidate_cache_reads']=used;report['actual_candidate_G36']=reads;report['candidate_local_original_gates_passed']=bool(passed and peak_compatible)
 finally:
  report['actual_candidate_boost_and_premath_prefix']={k:v for k,v in capture.items() if k not in ['input','output']}
  report['actual_candidate_cache_reads_before_any_guard_stop']=used
  report['actual_candidate_original_math_reads_before_any_guard_stop']=reads
  if m is not None:
   if old_auto is not None:m._auto_level=old_auto
   if old_boost is not None:m._boost=old_boost
   if old_write is not None:m.sf.write=old_write
   if old_build is not None:m.build=old_build
   if old_title is not None:m.title_audio=old_title
   if methods is not None:m.k.create,m.KT.create_timed=methods
  if restore is not None:restore()
  report['all_preexisting_private_cache_files_unchanged_only_one_actual_S6_math_added']=cache_scope(before,inventory(C),new_math)
  report['public_cache_bytes_unchanged']=inventory(public_path)==public and not sentinel.exists()
  report['normal_work_inode_and_files_unchanged']=((W/'work_68').stat().st_ino if (W/'work_68').exists() else None)==normal and {str(p.relative_to(W/'work_68')):digest(p) for p in (W/'work_68').rglob('*') if p.is_file()}==normalfiles
  report['original_private_initial_source_restored']=digest(W/'scripts/68.json')==OLD_SOURCE_SHA
  report['actual_model_voice_AF_dictionary_context_stamp_PV_dossier_inputs_exact_after']=all(digest(p)==h for p,h in live.items())
  require(all(report.get(k) is True for k in ['all_preexisting_private_cache_files_unchanged_only_one_actual_S6_math_added','public_cache_bytes_unchanged','normal_work_inode_and_files_unchanged','original_private_initial_source_restored','actual_model_voice_AF_dictionary_context_stamp_PV_dossier_inputs_exact_after']),'Candidate cache/work/source/runtime input restoration failed')
def main():
 p=argparse.ArgumentParser()
 for k in ['tools','video-root','inputs','profile','execution-adoption','output','cache-path-output']:p.add_argument('--'+k,type=Path,required=True)
 p.add_argument('--execution-adoption-sha256',required=True);p.add_argument('--actual-tail-shape-adoption',type=Path,required=True);p.add_argument('--actual-tail-shape-adoption-sha256',required=True);a=p.parse_args()
 report={'kind':'source68-onlyS6-exact10ms6-original-cached-local-two-phase-conditional-one-math-measurement','source_id':'68','book_order':53,'changed_sentence':'S6','original_mother_provenance_target':'S2','measurement_completed':False,'diagnostic_passed':False,'quality_acceptance':False,'whole_master1_proved':False,'new_TTS_GT_ASR_whole_or_native_authorized':False,'CF_or_production_source_written':False,'candidate_local_original_gates_passed':False,'restoration':{},'forbidden_model_events':[],'errors':[]}
 modules=dict(sys.modules);env=dict(os.environ);cwd=Path.cwd();path=list(sys.path);trace=sys.gettrace();profile=inp=None;new_math={};base=None
 try:
  require(a.execution_adoption_sha256==ROOT_SHA and digest(a.execution_adoption)==ROOT_SHA,'Actual ROOT185b mandatory exact CLI binding')
  root=json.loads(a.execution_adoption.read_text());require(root['candidate_only']=={'source':'68','sentence':'S6','old_boost':[9.025,9.085,3.5],'new_boost':[9.025,9.035,6.0]},'Wrong ROOT onlyS6 data scope')
  require(digest(a.profile)==PROFILE_SHA,'Wrong frozen extension profile');profile=json.loads(a.profile.read_text());inp={}
  require(not a.output.resolve().is_relative_to(a.video_root.resolve()) and not a.cache_path_output.resolve().is_relative_to(a.video_root.resolve()),'Only scalar/step-output paths outside cached machine authorized')
  require(not a.output.exists() and not a.output.with_name('68-existing-S6-S2-baseline-scalars.json').exists(),'Fresh scalar evidence output required')
  for k,row in profile['inputs'].items():
   rel=Path(row['file']);require(not rel.is_absolute() and '..' not in rel.parts,'Input path escaped');q=a.inputs/rel;require(q.stat().st_size==row['bytes'] and digest(q)==row['sha256'],'Frozen input differs '+k);inp[k]=q
  require(a.actual_tail_shape_adoption_sha256==TAIL_SHAPE_SHA and digest(a.actual_tail_shape_adoption)==TAIL_SHAPE_SHA and a.actual_tail_shape_adoption.read_bytes()==inp['actual_tail_shape_scope'].read_bytes(),'Mandatory actual ROOTff597 fullSHA tail-shape binding')
  tail=json.loads(inp['actual_tail_shape_scope'].read_text());require(digest(inp['actual_tail_shape_evidence'])==tail['actual_evidence']['sha256']=='b0c905dcf2819fcc456fd8d498e4018cb6c388ce78389060a356276b4340686b','Actual original candidate scalar evidence differs')
  selected_shape_contract(tail,json.loads(inp['actual_tail_shape_evidence'].read_text()),json.loads(inp['baseline_profile'].read_text())['expected']['S6']['original_G36'])
  report['actual_ROOT_A20_tail_shape_scope_SHA256']=TAIL_SHAPE_SHA;report['actual_original_A20_tail_shape_evidence_SHA256']=digest(inp['actual_tail_shape_evidence']);report['actual_original_A20_tail_shape_and_timed_tail']=tail['specific_selected_pre_math'];report['bound_prior_original_A20_quiet_tail_reason_not_a_new_measurement']=tail['A20_reason_not_an_extra_manual_cut'];report['A20_shape_binding_is_not_speech_quality_or_burst_acceptance']=True
  require(digest(inp['baseline_helper'])==BASELINE_HELPER_SHA and digest(inp['baseline_profile'])==BASELINE_PROFILE_SHA,'Original55 helper/profile must remain byteexact')
  require(digest(inp['source'])==OLD_SOURCE_SHA and digest(inp['selected_source'])==NEW_SOURCE_SHA,'Exact baseline and one-leaf candidate required');exact_delta(json.loads(inp['source'].read_text()),json.loads(inp['selected_source'].read_text()))
  require(digest(inp['root_scope'])==ROOT_SHA and digest(inp['data_H'])==root['actual_H']['sha256'],'Root data-role provenance differs')
  base=load('_onlyS6_original55_baseline_helper',inp['baseline_helper']);baseline_output=a.output.with_name('68-existing-S6-S2-baseline-scalars.json');argv=list(sys.argv)
  require(digest(inp['actual_onlyS6_baseline_observation_scope'])=='2efaf635e7924c1bf38ed62a1d4b661cf63b3373f87aca1511bf517021af8231','Actual ROOT2efa exact onlyS6 observation scope required before baseline')
  original_baseline_targets=base.TARGETS
  require(original_baseline_targets==('S6','S2'),'Expected original observation list before exact S6 subset')
  try:
   base.TARGETS=('S6',)
   sys.argv=[str(inp['baseline_helper']),'--tools',str(a.tools),'--video-root',str(a.video_root),'--inputs',str(a.inputs),'--profile',str(inp['baseline_profile']),'--output',str(baseline_output)]
   original_baseline_module_restore=base.restore_modules
   def baseline_task_module_restore(snapshot):
    report['baseline_module_lifecycle']=restore_task_owned_modules(snapshot,[a.tools,a.video_root,a.inputs])
   base.restore_modules=baseline_task_module_restore
   try:status=base.main()
   finally:base.restore_modules=original_baseline_module_restore
  finally:
   base.TARGETS=original_baseline_targets
   sys.argv=argv
  require(base.TARGETS==original_baseline_targets,'Original observer observation-list data was not restored')
  report['explicit_baseline_observation_scope']={'original_program_bytes_unchanged':True,'observed':['S6'],'extra_oldS2_not_replayed':True,'oldS2_run43759678069_pre_master_failure_not_resolved_or_waived':True,'original_TARGETS_restored':True,'originalS6_model_cache_math_PCM_PV_guards_unchanged':True,'no_formal_audio_quality_verdict':True}
  baseline=json.loads(baseline_output.read_text());require(status==0 and baseline['diagnostic_completed'] and not baseline['errors'],'Original baseline must complete before any candidate')
  require(baseline['targets']['S6']['pre_master_SHA256']=='66ca4d94cd7ea8775f9702a4c9afc77c772853a19345ffcecbb56225d277379a' and baseline['targets']['S6']['post_master_float_SHA256']=='4b85804895a6d5865b81c3ba106518e78f0e5220a095d6e83e45bcea4102c480','Actual native baseline66ca/4b858 mismatch')
  report['baseline']={'scalar_SHA256':digest(baseline_output),'pre_master_SHA256':baseline['targets']['S6']['pre_master_SHA256'],'post_master_SHA256':baseline['targets']['S6']['post_master_float_SHA256'],'actual_saved_math_reads':baseline['actual_existing_G36_reads'],'all_restores_exact':all(baseline.get(k) is True for k in ['normal_work_inode_and_files_unchanged','all_private_cache_bytes_unchanged','all_public_cache_bytes_unchanged','all_frozen_inputs_unchanged','all_original_module_identities_restored'])}
  require(report['baseline']['all_restores_exact'],'Baseline original restoration prerequisite failed')
  run_candidate(a,profile,inp,base,baseline,report,new_math)
  report['measurement_completed']=True
 except BaseException as e:report['errors'].append({'type':type(e).__name__,'detail':str(e)});traceback.print_exc()
 finally:
  try:
   if inp is not None:report['all_frozen_inputs_unchanged']=all(digest(q)==profile['inputs'][k]['sha256'] for k,q in inp.items())
   report['actual_new_S6_original_math']=new_math
   report['math_save_integrity_independent_of_PV_verdict']=bool(new_math and all(x.get('strict_readback_exact') is True for x in new_math.values()) and report.get('all_preexisting_private_cache_files_unchanged_only_one_actual_S6_math_added') is True and report.get('public_cache_bytes_unchanged') is True and report.get('normal_work_inode_and_files_unchanged') is True and report.get('original_private_initial_source_restored') is True and report.get('actual_model_voice_AF_dictionary_context_stamp_PV_dossier_inputs_exact_after') is True and report.get('all_frozen_inputs_unchanged') is True and not report['forbidden_model_events'])
   if report['math_save_integrity_independent_of_PV_verdict']:
    M=a.video_root.resolve();directory=M/'tts/source68-only-S6-local-original-math-cache';require(not directory.exists(),'Fresh S6 math SAVE directory required');directory.mkdir();saved=[]
    for name,row in new_math.items():
     p=directory/name;shutil.copyfile(M/'tts/cache_tts'/name,p);require(digest(p)==row['sha256'],'Actual math SAVE copy differs');saved.append(str(p))
    runid=os.environ.get('GITHUB_RUN_ID','');require(runid.isdigit(),'Real Actions run ID needed to expose exact math SAVE paths')
    key='Linux-native68-only-S6-local-original-math-'+runid
    with a.cache_path_output.open('a') as f:f.write('cache_key='+key+'\ncache_paths<<ONLY_S6_ORIGINAL_MATH_PATHS\n'+'\n'.join(saved)+'\nONLY_S6_ORIGINAL_MATH_PATHS\n')
    report['private_original_math_save']={'cache_key':key,'exact_paths':saved,'files':new_math,'save_success_not_claimed':True}
  except BaseException as e:report['measurement_completed']=False;report['errors'].append({'type':type(e).__name__,'detail':str(e),'during':'restoration-or-math-save'})
  os.environ.clear();os.environ.update(env);os.chdir(cwd);sys.path[:]=path;sys.settrace(trace)
  report['final_module_lifecycle']=restore_task_owned_modules(modules,[a.tools,a.video_root,a.inputs])
  report['all_original_modules_trace_env_cwd_path_restored']=all(sys.modules[k] is v for k,v in modules.items()) and dict(os.environ)==env and Path.cwd()==cwd and sys.path==path and sys.gettrace() is trace
  report['module_restoration_role']='All preexisting module objects plus task-owned modules restored; new non-task library modules deliberately retained; namespace-set equality is separately reported, never assumed'
  restored=report['all_original_modules_trace_env_cwd_path_restored'] and report.get('all_frozen_inputs_unchanged') is True and all(report['restoration'].get(k) is True for k in ['normal_scripts_namespace_restored','environment_cwd_sys_path_restored'])
  report['measurement_completed']=bool(report['measurement_completed'] and restored and not report['errors'] and not report['forbidden_model_events'])
  report['diagnostic_passed']=bool(report['measurement_completed'] and report['candidate_local_original_gates_passed'])
  a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,ensure_ascii=False,indent=2,default=lambda x:x.item())+'\n')
  print(json.dumps({'measurement_completed':report['measurement_completed'],'diagnostic_passed':report['diagnostic_passed'],'output_SHA256':digest(a.output),'errors':report['errors'],'quality_acceptance':False},ensure_ascii=False))
 return 0 if report['diagnostic_passed'] else 1
if __name__=='__main__':sys.exit(main())
