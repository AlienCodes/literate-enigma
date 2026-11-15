"""Original cached whole measurement for actual CMU2 mothers; no new model/TTS/GT/ASR."""
from pathlib import Path
import argparse,ast,collections,contextlib,copy,gc,hashlib,importlib.util,json,os,re,shutil,sys,traceback
sys.dont_write_bytecode=True
ROOT_SHA='a430159b2c827fcabcdf242f8407b33d546f1d5cfac336558b4537c90577efa4'
PROFILE_SHA='04d11bb2099f0bd2ef2ddc9810fcccc332489f0379ad266c8c5e6cbac908682a'
OBSERVER_SHA='7013809ab08a9706ecc6e9a5e573637b51fb5aef23dc412d49ea296f9ed66752'
SUPPORT_SHA='44afe8fcb5bc9b723dc7291876ece463c0c72013390e7ed3b2777d9a58e6f222'
OLD_SOURCE='dc3fec8cb898d8a7279739b6c4c62d38caf509580e26511acd95d07f1bbc18ef'
SELECTED_SOURCE='74b57d0fff73ae89d7b1d0c5492c72cd94a758bc5cc20871322fb7f335656b10'
OLD_CTX='4d8905dc1a87f97b707270f03f41ea0fdf2b207ca218ed74608cdb134e3dc8e3'
NEW_CTX='db04a700c9778e45db7c934ce0f4cf8f44349ff3a924599d4194aa90a363440f'
DISPLAY='The compromise, struck without Wallace, may have kept rivalry over precedence at bay.'
PROJECTED='The compromise struck without Wallace, may have kept rivalry over precedence at bay.'
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def require(x,message):
 if not x:raise AssertionError(message)
def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m
def inventory(path):return {p.name:digest(p) for p in Path(path).iterdir() if p.is_file()}
def typed(x):
 if isinstance(x,dict):return {k:typed(v) for k,v in x.items()}
 if isinstance(x,list):return [typed(v) for v in x]
 return (type(x).__name__,x)
def validate_bundle(profile,inp,root):
 require(profile['source_id']=='56' and profile['target_sentence']=='S11' and profile['sentence_count']==17 and profile['allow_selected_target_G36_math'] is True,'Exact original source56/S11/count/math role required')
 require(root['finite_target_scope']['source']=='56' and root['finite_target_scope']['target']=='S11' and root['finite_target_scope']['new_phone_input_SHA256']=='7ab4087b2c5293e715b5a63769102df98c294a405f7d0e5368c328f51388492a','Wrong actual ROOT CMU2 scope')
 require(digest(inp['source'])==OLD_SOURCE and digest(inp['selected_source'])==SELECTED_SOURCE and digest(inp['old_context'])==OLD_CTX and digest(inp['new_context'])==NEW_CTX,'Wrong actual current source/context roles')
 old,new=json.loads(inp['source'].read_text()),json.loads(inp['selected_source'].read_text());undo=copy.deepcopy(new)
 require(old['区间声音指纹'].get('S11')=='5e39565cea68' and 'S11' not in new['区间声音指纹'],'Only actual old S11 VFP retirement allowed')
 undo['区间声音指纹']['S11']=old['区间声音指纹']['S11'];require(typed(undo)==typed(old),'Source change beyond one retired S11 VFP')
 require(old['结尾句']['S17']==new['结尾句']['S17']=={'整句语速':.95},'Current transparent S17 .95 must stay exact in both phases')
 oc,nc=json.loads(inp['old_context'].read_text()),json.loads(inp['new_context'].read_text())
 require(set(nc)-set(oc)=={PROJECTED} and {k:v for k,v in nc.items() if k!=PROJECTED}==oc and nc[PROJECTED]['词']=='Wallace' and nc[PROJECTED]['读音']=='wˈɔːlɪs','Only exact full PROJECTED CMU2 context entry allowed')
 m=json.loads(inp['actual_new_mother_H'].read_text());require(m['actual_completed'] and m['actual_old_full_pair_preinfer_witness']['old_complete_phones_equal_actual_internal_and_contract'] and m['actual_target_context_during_method_calls']==NEW_CTX and m['actual_title_plus16_nontarget_postpron_tuple_keys_exact'],'Actual new-mother/private old-fulltimed provenance incomplete')
 require(profile['new_processed_S11_clean_tail_VFP'] is None and profile['new_full_raw_array_MD5_first12']=='8c48a0220dc7','Do not equate raw mother MD5 with unknown clean-tail VFP')
 pre=json.loads(inp['current_precheck'].read_text());b=profile['baseline_target_expected_observed'];clock=profile['baseline_target_expected_clock']
 require(pre['physical_metadata_precheck_ready'] is True and pre['errors']==[] and b==pre['phases']['selected']['observed_sentences']['S11'] and clock==pre['phases']['selected']['actual_sample_clock']['S11'],'Wrong current true native precheck')
 require(b['pre_master_PCM_sha256']=='1497bbffd71c24b0ca05a4ca45767980a3af3a223745a0ba3c0783539d64110a' and clock['observed_post_master_float_PCM_sha256']=='54beedaf1230cc8e317310b2446baf04a5bc7a10f5b6db4fd19e2e6496d9830b','Current native floating roles must not revert to old whole f900')
 require(profile['baseline_audio']['WAV_sha256']=='b485a8871177099720963f694d887d39de05ec30af7ca4ccf4aac270689a2444' and profile['baseline_audio']['WAV_md5']=='a92bc6737128e7c27c38f7c7a89805aa' and profile['baseline_audio']['packet_count']==7310,'Actual complete current baseline identity differs')
 return old,new
@contextlib.contextmanager
def selected_context_namespace(T,W,old_bytes,new_bytes,scratch,restoration):
 paths=[Path(T)/'发音词典/按语境读音.json',Path(W)/'按语境读音.json'];saved=[]
 restoration['selected_context_payload_exact_at_exit']=False
 require(hashlib.sha256(old_bytes).hexdigest()==OLD_CTX and hashlib.sha256(new_bytes).hexdigest()==NEW_CTX,'Wrong phase context payload')
 require(len({str(p.resolve()) for p in paths})==2 and all(p.is_file() and not p.is_symlink() and p.read_bytes()==old_bytes for p in paths),'Both original regular context paths must be actual old4d890')
 try:
  for i,p in enumerate(paths):
   backup=Path(scratch)/('original-context-inode-'+str(i));require(not backup.exists(),'Context backup collision');inode=p.stat().st_ino;os.replace(p,backup);saved.append((p,backup,inode));p.write_bytes(new_bytes)
  require(all(digest(p)==NEW_CTX for p in paths),'Both contexts must precede selected source-first import');yield
 finally:
  allnew=True
  for i,(p,backup,inode) in enumerate(saved):
   allnew=allnew and p.is_file() and digest(p)==NEW_CTX
   if p.exists():os.replace(p,Path(scratch)/('observed-selected-context-'+str(i)))
   os.replace(backup,p);require(p.stat().st_ino==inode and p.read_bytes()==old_bytes,'Original context inode/bytes failed restore')
  restoration['both_T_W_original_context_inode_and_bytes_restored']=all(p.read_bytes()==old_bytes for p in paths)
  restoration['selected_context_payload_exact_at_exit']=allnew
  require(allnew,'Selected context was modified during original phase')
@contextlib.contextmanager
def phase_source_namespace(support,W,payload,restoration):
 restoration['normal_scripts_namespace_restored']=False
 with support.source_namespace(W,payload,restoration):yield
def tracked_native_blocker(original,label,receipts):
 receipts[label]=False
 def block(m,support,events):
  restore=original(m,support,events)
  def actual_restore():
   receipts[label]=False;restore();receipts[label]=True
  return actual_restore
 return block
def cached_factory(lib,original_factory,label,profile):
 def factory(m,np,cache,method,model,outer,used,result):
  guarded=original_factory(m,np,cache,method,model,outer,used,result)
  def read(text,voice,speed=1.,lang='en-us',**kw):
   require(os.environ.get('STRICT_CACHE')=='1','Every mother/cache access must stay strict, including during G36 mathematics')
   captured=[]
   def capture(actual_text,voice,speed=1.,lang='en-us',**actualkw):
    mid=m._portable_mid(str(cache.parent/model));vh=hashlib.sha1(np.ascontiguousarray(voice).tobytes()).hexdigest();key=hashlib.sha1(repr((method,mid,actual_text,vh,float(speed),lang,sorted(actualkw.items()))).encode()).hexdigest()+'.pkl';p=cache/key
    require(p.is_file() and not p.is_symlink(),'Missing/linked cached key before any original native endpoint: '+key)
    input_sha=hashlib.sha256(actual_text.encode()).hexdigest();target=text==m.spoken(DISPLAY) or input_sha in {e[method]['input_SHA256'] for e in profile['target_entries'].values()};row={'method':method,'name':key,'input_SHA256':input_sha,'kwargs':actualkw,'speed':float(speed),'lang':lang,'target':target}
    if target:
     require(text==m.spoken(DISPLAY),'Original outer S11 ABI must remain display text before _pron projection')
     e=profile['target_entries'][label][method];marker=cache/e['marker_name']
     require(key==e['name'] and row['input_SHA256']==e['input_SHA256'] and digest(p)==e['sha256'] and marker.is_file() and not marker.is_symlink() and digest(marker)==e['marker_sha256'] and marker.read_text().strip()==e['marker_value'],'Wrong actual phase raw/timed key/fullSHA/marker/input')
     expectedkw={} if method=='create' else {'clause_pause':0,'sentence_pause':0}
     if label=='selected':expectedkw={'is_phonemes':True,**expectedkw}
     require(actualkw==expectedkw and speed==.95 and lang=='en-us' and np.array_equal(voice,m.V),'Target exact original tuple differs')
    captured.append(row)
   m._pron(capture)(text,voice=voice,speed=speed,lang=lang,**kw);require(len(captured)==1,'Original cached/pron capture ABI changed')
   value=guarded(text,voice=voice,speed=speed,lang=lang,**kw)
   row=captured[0]
   if row['target']:
    e=profile['target_entries'][label][method];a=value[0]
    require(len(a)==e['samples'] and value[1]==e['sample_rate'] and str(a.dtype)=='float32' and hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()==e['array_SHA256'],'Actual cached mother array identity differs')
    if label=='selected' and method=='create':require(hashlib.md5(np.ascontiguousarray(a).tobytes()).hexdigest()[:12]=='8c48a0220dc7','New full raw array MD5 differs; this is not a processed VFP')
   result.setdefault('actual_postpron_cache_tuples',[]).append(row);return value
  return read
 return factory
def math_factory(lib,original_factory,label,profile):
 def factory(m,original,phase,state,p,result,new_math):
  observed=original_factory(m,original,phase,state,p,result,new_math)
  def guarded(clips,tmap,gaps,no='',rounds=2):
   require(phase==label and str(no)=='56' and rounds==2 and os.environ.get('STRICT_CACHE')=='1','Original whole math phase/source/rounds must stay strict')
   source_path=Path(m.__file__).resolve().parent/'scripts/56.json';role='source' if label=='baseline' else 'selected_source';require(source_path.is_file() and digest(source_path)==profile['inputs'][role]['sha256'],'Actual phase source must remain exact at original mathematics call')
   ctx=OLD_CTX if label=='baseline' else NEW_CTX
   context_paths=[Path(m.__file__).resolve().parent/'按语境读音.json',Path(lib.CMU2_DECLARED_TOOLS)/'发音词典/按语境读音.json']
   require(all(p.is_file() and not p.is_symlink() and digest(p)==ctx for p in context_paths),'Actual phase T/W contexts must remain exact at original mathematics call')
   current=m._auto_level;m._auto_level=original
   try:key=lib.auto_key(m,clips,tmap,gaps,no)
   finally:m._auto_level=current
   if key is not None:
    path=lib.CACHE/('调平_'+key+'.json');require(not path.is_symlink(),'Linked original math path forbidden')
   if label=='baseline' and state.get('sid')=='S11':
    e=profile['baseline_S11_original_G36'];require(key==e['original_key'] and path.is_file() and digest(path)==e['sha256'],'Baseline original228420/98c2 must strictly hit')
    sh=lambda x:hashlib.sha256(m.np.ascontiguousarray(x).tobytes()).hexdigest()
    require([sh(x) for x in clips]==e['clip_SHA256'] and [len(x) for x in clips]==e['clip_samples'] and list(gaps)==e['gaps'] and [list(x) for x in tmap]==e['original_tmap'],'Actual baseline original G36 inputs differ')
   return observed(clips,tmap,gaps,no,rounds)
  return guarded
 return factory
def runtime_bindings(T,M,W,lib,profile,inp):
 live={T/'发音词典/读音改正.json':lib.DICT_SHA256,T/'发音词典/按语境读音.json':OLD_CTX,W/'读音改正.json':lib.DICT_SHA256,W/'按语境读音.json':OLD_CTX,T/'新管/快测通过.json':lib.STAMP_SHA256,M/'tts/voice_mb.npy':profile['voice_SHA256'],M/'tts/AF.txt':profile['AF_SHA256']}
 live.update({M/'tts'/k:v for k,v in profile['models_SHA256'].items()})
 for r in json.loads(inp['overlay'].read_text())['files']:live[T/Path(r['path']).relative_to('视频/工具')]=r['patch_SHA256']
 g=load('_CMU2_whole_actual_G27',T/'出片指纹.py');paths=g.清单([str(T)])
 require(len(paths)==8 and set(paths)==set(profile['original_G27_expected']) and g.核对工作目录(str(W),str(T))==[],'Original eight actual G27 routes differ')
 for name,p in paths.items():
  q=g._找(name,g.工作目录搜(str(W)));require(q is not None,'Original G27 import path missing '+name);live[Path(p)]=profile['original_G27_expected'][name];live[Path(q)]=profile['original_G27_expected'][name]
 require(all(p.is_file() and digest(p)==h for p,h in live.items()),'Original runtime/model/voice/filter/dictionary/context/stamp differs');return live
def cache_scope(before,after,new_math):return all(after.get(k)==v for k,v in before.items()) and not(set(before)-set(after)) and set(after)-set(before)==set(new_math) and len(new_math)<=1 and all(after.get(k)==v['sha256'] for k,v in new_math.items())
def restore_original_local_modules(snapshot,roots=()):
 local={'make_video','render','title2','title_anim','clean','出片指纹','响度一致性核对','对正量'}
 local.update(k for k in set(snapshot)|set(sys.modules) if k.startswith('_CMU2_') or k.startswith('_original_56_strict_whole_'))
 roots=[Path(p).resolve() for p in roots];path_aliases=[]
 for k,v in list(sys.modules.items()):
  f=getattr(v,'__file__',None)
  if not isinstance(f,(str,bytes)):continue
  try:
   p=Path(f).resolve()
   if p.is_file() and any(p.is_relative_to(r) for r in roots):local.add(k);path_aliases.append(k)
  except (OSError,TypeError,ValueError):continue
 added_third_party={k:v for k,v in sys.modules.items() if k not in snapshot and k not in local}
 for k in local:
  if k in snapshot:sys.modules[k]=snapshot[k]
  else:sys.modules.pop(k,None)
 return {'all_original_local_module_objects_restored':all((sys.modules.get(k) is snapshot[k]) if k in snapshot else k not in sys.modules for k in local),'all_preexisting_module_objects_preserved':all(sys.modules.get(k) is v for k,v in snapshot.items()),'all_added_third_party_module_objects_retained':all(sys.modules.get(k) is v for k,v in added_third_party.items()),'retained_added_third_party_module_count':len(added_third_party),'actual_T_W_inputs_path_aliases_restored':sorted(path_aliases),'third_party_C_extensions_never_purged':True}
def math_scope_prerequisites(report,new_math,profile,restored):
 rows=[r for r in report.get('phases',{}).get('selected',{}).get('original_G36_calls',[]) if r.get('sentence')=='S11' and r.get('actual_math_created') is True]
 calls=report.get('phases',{}).get('selected',{}).get('actual_postpron_cache_tuples',[]);expected={r['name'] for r in profile['target_entries']['selected'].values()};seen={r['name'] for r in calls if r.get('target') is True}
 one=len(new_math)==1;item=next(iter(new_math.values())) if one else {};name=next(iter(new_math)) if one else ''
 return {'all_inner_runtime_source_context_work_module_cache_restores':restored is True,'baseline_and_selected_native_endpoints_restored':all(report.get('native_closure_restore_receipts',{}).get(k) is True for k in ['baseline','selected']),'declared_source_context_and_actual_mother_inputs_checked':report.get('declared_source_context_and_mother_inputs_checked') is True,'both_actual_new_target_mothers_witnessed_before_math':expected<=seen,'one_original_S11_math_creator_and_strict_readback':one and len(rows)==1 and rows[0].get('file')==name and rows[0].get('sha256')==item.get('sha256') and rows[0].get('source_no')=='56' and rows[0].get('original_rounds')==2 and item.get('source_id')=='56' and item.get('target_sentence')=='S11' and item.get('strict_readback_exact') is True,'no_forbidden_model_endpoint_events':report.get('forbidden_model_events')==[]}
def main():
 parser=argparse.ArgumentParser()
 for k in ['tools','video-root','inputs','profile','execution-adoption','output','cache-path-output']:parser.add_argument('--'+k,type=Path,required=True)
 parser.add_argument('--execution-adoption-sha256',required=True);a=parser.parse_args()
 report={'kind':'source56-CMU2-currentdc3-baseline-vs-onlyS11-selected-original-cachedwhole-scalar','source_id':'56','book_order':65,'target_sentence':'S11','measurement_completed':False,'exact_scope_proved':False,'quality_acceptance':False,'formal_acceptance':False,'production_delivery_eligible':False,'new_TTS_GT_ASR_or_native_executed':False,'phases':{},'restoration':{},'forbidden_model_events':[],'errors':[]}
 modules=dict(sys.modules);env=dict(os.environ);cwd=Path.cwd();path=list(sys.path);trace=sys.gettrace();inp=profile=before=public=live=lib=None;new_math={};used={};oldfunctions=None;T=a.tools.resolve();M=a.video_root.resolve();W=M/'video';C=M/'tts/cache_tts'
 try:
  require(a.execution_adoption_sha256==ROOT_SHA and digest(a.execution_adoption)==ROOT_SHA,'Actual ROOTa430 literal CLI record required')
  require(digest(a.profile)==PROFILE_SHA,'Wrong current CMU2 whole profile');profile=json.loads(a.profile.read_text());inp={}
  for role,r in profile['inputs'].items():
   rel=Path(r['file']);require(not rel.is_absolute() and '..' not in rel.parts,'Frozen input escaped');p=a.inputs/rel;require(p.stat().st_size==r['bytes'] and digest(p)==r['sha256'],'Wrong frozen input '+role);inp[role]=p
  require(digest(inp['observer'])==OBSERVER_SHA and digest(inp['support'])==SUPPORT_SHA,'Original whole library/support bytes differ')
  old,new=validate_bundle(profile,inp,json.loads(a.execution_adoption.read_text()))
  require(not a.output.resolve().is_relative_to(M) and not a.cache_path_output.resolve().is_relative_to(M) and not a.output.exists(),'Fresh scalar/private-step paths outside cached machine required')
  require(all(os.environ.get(k)=='1' for k in ['AUDIO_ONLY','STRICT_CACHE','XG_NOPUSH','XG_KEEP_REVIEWED_GAIN','XG_KEEP_REVIEWED_ENDING','XG_KEEP_REVIEWED_CUTS']) and not any(os.environ.get(k) for k in ['VOICE','AFFILE','OLD_IV_VOID','ONLY','BREATH_FRAC','CACHE_LOG']),'Exact reviewed strict environment required')
  require(Path('/home/user/postgraduate-vocabulary').resolve()==T.parent.parent,'Original ROOT alias differs')
  lib=load('_CMU2_original56_whole_library',inp['observer']);support=load('_CMU2_original56_mother_scope',inp['support']);require(lib.SOURCE_NO==support.SOURCE_NO=='56' and lib.TARGET==support.TARGET=='S11' and lib.COUNT==17,'Do not retarget another source/mother helper')
  support.validate_certificate(T,json.loads(inp['overlay'].read_text()),json.loads(inp['certificate'].read_text()))
  lib.CACHE=C;lib.CMU2_DECLARED_TOOLS=T;lib.phase_arrays.clear();lib.phase_post_arrays.clear();lib.phase_int16_arrays.clear();oldfunctions=(lib.strict_cached_guard,lib.math_guard,lib.block_native);live=runtime_bindings(T,M,W,lib,profile,inp);report['native_closure_restore_receipts']={'baseline':False,'selected':False}
  for phase,entries in profile['target_entries'].items():
   for e in entries.values():
    for name,h in [(e['name'],e['sha256']),(e['marker_name'],e['marker_sha256'])]:p=C/name;require(p.is_file() and not p.is_symlink() and digest(p)==h,'Actual phase mother/marker missing/wrong; no fallback')
  e=profile['baseline_S11_original_G36'];require((C/e['file']).is_file() and not (C/e['file']).is_symlink() and digest(C/e['file'])==e['sha256'],'Actual baseline228420 original G36 JSON missing/wrong')
  report['declared_source_context_and_mother_inputs_checked']=True
  before=inventory(C);public=inventory(T.parent/'配音缓存');scratch=M/'_source56_CMU2_original_cachedwhole';require(not scratch.exists(),'Fresh whole scratch namespace required');scratch.mkdir();paths={'T':T,'M':M,'W':W,'scratch':scratch}
  with support.environment_and_cwd(W,report['restoration']):
   with lib.work_namespace(W/'work_56',scratch,report['restoration']):
    for label,role in [('baseline','source'),('selected','selected_source')]:
     ctx=OLD_CTX if label=='baseline' else NEW_CTX
     manager=contextlib.nullcontext() if label=='baseline' else selected_context_namespace(T,W,inp['old_context'].read_bytes(),inp['new_context'].read_bytes(),scratch,report['restoration'])
     with manager:
      lib.CTX_SHA256=ctx;require(digest(T/'发音词典/按语境读音.json')==digest(W/'按语境读音.json')==ctx,'T/W declared context must precede source/maker import')
      lib.strict_cached_guard=cached_factory(lib,oldfunctions[0],label,profile);lib.math_guard=math_factory(lib,oldfunctions[1],label,profile)
      lib.block_native=tracked_native_blocker(oldfunctions[2],label,report['native_closure_restore_receipts'])
      with phase_source_namespace(support,W,inp[role].read_bytes(),report['restoration']):lib.run_phase(label,inp[role].read_bytes(),profile['inputs'][role]['sha256'],paths,support,profile,report,used,new_math)
     if label=='baseline':
      b=report['phases']['baseline'];expected=profile['baseline_target_expected_observed'];actual=b['observed_sentences']['S11'];require(typed(actual)==typed(expected),'Current native S11 baseline1497 DSP/float identity differs')
      require(b['actual_sample_clock']['S11']==profile['baseline_target_expected_clock'],'Current native S11 baseline54beed clock/float differs')
      require(b['actual_complete_WAV']['file_md5']==profile['baseline_audio']['WAV_md5'],'Current complete baseline MD5 differs')
  lib.CTX_SHA256=OLD_CTX
  report['measurement_completed']=True;lib.compare_phases(profile,report)
  require(report['actual_global_master_scale_ratio_selected_over_baseline']==1.0,'Actual original global master scale must remain exactly1')
  def nontarget(phase):return collections.Counter(json.dumps({k:v for k,v in r.items() if k!='target'},sort_keys=True,ensure_ascii=False) for r in phase['actual_postpron_cache_tuples'] if not r['target'])
  require(nontarget(report['phases']['baseline'])==nontarget(report['phases']['selected']),'A title/non-target/helper post-pron tuple/key changed')
  report['all_title16_nontarget_and_helper_postpron_key_multisets_exact']=True
  report['actual_new_processed_S11_VFP']=report['phases']['selected']['observed_sentences']['S11']['actual_raw_w_fingerprint'];report['new_clean_VFP_not_assumed_equal_full_raw8c48']=True
  report['actual_S11_duration_delta_samples']=report['phases']['selected']['observed_sentences']['S11']['samples']-report['phases']['baseline']['observed_sentences']['S11']['samples']
  report['actual_absolute_clock_deltas']={sid:{'start_sample_delta':report['phases']['selected']['actual_sample_clock'][sid]['start_sample']-v['start_sample'],'end_sample_delta':report['phases']['selected']['actual_sample_clock'][sid]['end_sample_exclusive']-v['end_sample_exclusive']} for sid,v in report['phases']['baseline']['actual_sample_clock'].items()}
  report['exact_scope_proved']=True
 except BaseException as e:report['errors'].append({'type':type(e).__name__,'detail':str(e)});traceback.print_exc()
 finally:
  try:
   if lib is not None:
    lib.CTX_SHA256=OLD_CTX
    if oldfunctions is not None:lib.strict_cached_guard,lib.math_guard,lib.block_native=oldfunctions
   if before is not None:report['all_existing_private_cache_exact_only_one_actual_S11_math_added']=cache_scope(before,inventory(C),new_math);report['public_cache_exact_after']=inventory(T.parent/'配音缓存')==public
   if live is not None:report['all_runtime_model_voice_AF_G27_dict_context_stamp_bytes_exact_after']=all(p.is_file() and digest(p)==h for p,h in live.items())
   if inp is not None:report['all_frozen_inputs_exact_after']=all(digest(p)==profile['inputs'][r]['sha256'] for r,p in inp.items())
  except BaseException as e:report['errors'].append({'type':type(e).__name__,'detail':str(e),'during':'restore-input-scope'})
  os.environ.clear();os.environ.update(env);os.chdir(cwd);sys.path[:]=path;sys.settrace(trace)
  report['actual_local_module_restoration']=restore_original_local_modules(modules,[T,W,a.inputs.resolve()])
  report['all_original_local_modules_preexisting_objects_env_cwd_path_trace_restored']=all(v is True for v in report['actual_local_module_restoration'].values() if type(v) is bool) and dict(os.environ)==env and Path.cwd()==cwd and sys.path==path and sys.gettrace() is trace
  guards=['all_original_local_modules_preexisting_objects_env_cwd_path_trace_restored','all_existing_private_cache_exact_only_one_actual_S11_math_added','public_cache_exact_after','all_runtime_model_voice_AF_G27_dict_context_stamp_bytes_exact_after','all_frozen_inputs_exact_after']
  restored=all(report.get(k) is True for k in guards) and all(report['restoration'].get(k) is True for k in ['normal_scripts_namespace_restored','environment_cwd_sys_path_restored','normal_work_inode_and_PCM_restored','both_T_W_original_context_inode_and_bytes_restored','selected_context_payload_exact_at_exit'])
  report['measurement_completed']=bool(report['measurement_completed'] and restored and not report['errors'] and not report['forbidden_model_events']);report['exact_scope_proved']=bool(report['exact_scope_proved'] and report['measurement_completed']);report['actual_new_S11_original_math']=new_math;report['math_save_integrity_proved']=False
  report['actual_math_scope_prerequisites']=math_scope_prerequisites(report,new_math,profile,restored) if profile is not None else {}
  report['math_scope_integrity_proved']=bool(report['actual_math_scope_prerequisites'] and all(v is True for v in report['actual_math_scope_prerequisites'].values()))
  report['proven_original_math_scope_is_independent_of_whole_or_quality_verdict']=True
  try:
   if report['math_scope_integrity_proved']:
    folder=M/'tts/source56-only-S11-CMU2-whole-original-math-cache';require(not folder.exists(),'Fresh single-S11 SAVE namespace required');folder.mkdir();saved=[]
    for name,row in new_math.items():p=folder/name;shutil.copyfile(C/name,p);require(digest(p)==row['sha256'],'Actual new math SAVE copy differs');saved.append(str(p))
    runid=os.environ.get('GITHUB_RUN_ID','');require(runid.isdigit(),'Actual Actions run ID required');key='Linux-native56-only-S11-CMU2-whole-original-math-'+runid
    report['private_original_math_save']={'cache_key':key,'exact_paths':saved,'files':new_math,'save_success_not_claimed':True};report['math_save_integrity_proved']=True
    a.cache_path_output.parent.mkdir(parents=True,exist_ok=True)
    with a.cache_path_output.open('a') as f:f.write('cache_key='+key+'\ncache_paths<<ONLY_S11_CMU2_MATH_PATHS\n'+'\n'.join(saved)+'\nONLY_S11_CMU2_MATH_PATHS\n')
  except BaseException as e:report['measurement_completed']=report['exact_scope_proved']=report['math_scope_integrity_proved']=False;report['errors'].append({'type':type(e).__name__,'detail':str(e),'during':'private-math-staging-only'})
  a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,ensure_ascii=False,indent=2,default=lambda x:x.item())+'\n');print(json.dumps({'measurement_completed':report['measurement_completed'],'exact_scope_proved':report['exact_scope_proved'],'quality_acceptance':False,'output_SHA256':digest(a.output),'errors':report['errors']},ensure_ascii=False))
 return 0 if report['measurement_completed'] and report['exact_scope_proved'] else 1
if __name__=='__main__':sys.exit(main())
