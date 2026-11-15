"""Cold tests only: real public JSON + synthetic tiny files; no actual models/caches/audio."""
from pathlib import Path
import ast,copy,hashlib,importlib.util,json,os,sys,tempfile,types
import numpy as np
sys.dont_write_bytecode=True
D=Path(__file__).parent
spec=importlib.util.spec_from_file_location('_cold68',D/'observe68_only_S6_S2_actual_cached_scalars.py');h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
P=json.loads((D/'profile.json').read_text());I=h.bind_inputs(D,P);src=json.loads(I['source'].read_text());whole=json.loads(I['whole_report'].read_text());failed=json.loads(I['failed_proof'].read_text());actual=json.loads(I['actual_precheck'].read_text())
rows=[]
def check(name,fn,bad=False):
 try:fn()
 except (AssertionError,FileNotFoundError,KeyError) as e:
  if not bad:raise
  rows.append(dict(name=name,passed=True,expected_rejection=True,error=str(e)));return
 if bad:raise AssertionError('BAD fixture escaped '+name)
 rows.append(dict(name=name,passed=True,expected_rejection=False))
def validate(p=P,s=src,w=whole,f=failed,a=actual):return h.validate_data(p,s,w,f,a)
check('real_public_inputs_and_exact_actual_source_scope',validate)
check('actual_profile_SHA',lambda:h.require(sha(D/'profile.json')==h.PROFILE_SHA256,'profile SHA'))
def bad_data(name,obj,path,value):
 x=copy.deepcopy(obj);t=x
 for k in path[:-1]:t=t[k]
 t[path[-1]]=value
 key={'profile':'p','source':'s','whole':'w','failed':'f','actual':'a'}[name]
 check('reject_'+name+'_'+str(path),lambda:validate(**{key:x}),True)
bad_data('profile',P,['source_id'],'35')
bad_data('profile',P,['target_sentences'],['S6','S2','S13'])
bad_data('profile',P,['cache_entries','S6','create','name'],'../wrong.pkl')
bad_data('profile',P,['cache_entries','S2','create_timed','single_thread_marker_value'],'0'*16)
bad_data('source',src,['除阻加强','S6','句末'],[9.025,9.085,4.])
bad_data('source',src,['朗读删逗号','S2','逗号序号'],[2])
bad_data('source',src,['分段增益dB','S2'],{'1':-2.})
bad_data('whole',whole,['actual_global_master_scale_ratio_selected_over_baseline'],.999)
bad_data('failed',failed,['internal_pcm_sha256'],'0'*64)
bad_data('failed',failed,['aac_adts_sha256'],'0'*64)
bad_data('actual',actual,['physical_metadata_precheck_ready'],False)
bad_data('actual',actual,['phases','selected','observed_sentences','S2','pre_master_PCM_sha256'],'0'*64)
bad_data('actual',actual,['phases','selected','original_G36_calls',1,'original_key'],'0'*40)
os.environ['STRICT_CACHE']='1'  # This cold test subprocess only; no actual model/cache.
with tempfile.TemporaryDirectory(prefix='cold68-') as tmp:
 C=Path(tmp);text='fixture active sentence';voice=np.array([1.,.5],dtype=np.float32);used=[];called=[]
 m=types.SimpleNamespace(np=np,V=voice,spoken=lambda s:s,_portable_mid=lambda _: 'fixture-model:1',_条目核对=lambda p:None,_pron=lambda f:f)
 method='create';vh=hashlib.sha1(voice.tobytes()).hexdigest();key=hashlib.sha1(repr((method,'fixture-model:1',text,vh,.95,'en-us',[])).encode()).hexdigest()+'.pkl'
 p=C/key;p.write_bytes(b'SYNTHETIC FILE, not pickle or audio');mark=C/(key+'.单线程');mark.write_text(sha(p)[:16]);row=dict(name=key,sha256=sha(p),single_thread_marker_sha256=sha(mark),single_thread_marker_value=sha(p)[:16],actual_model_input_sha256=hashlib.sha256(text.encode()).hexdigest())
 original=lambda *a,**kw:called.append('fixture cached reader') or ('fixture result',24000)
 def call(row_=row,txt=text,**kw):
  fn=h.target_model_guard(m,np,C,'create','fixture.onnx',original,text,'S6',{'create':row_},used)
  return fn(txt,voice=voice,**dict(speed=.95,lang='en-us',**kw))
 check('synthetic_authenticated_key_calls_only_stub_cache_reader',call)
 require_count=len(called)
 check('reject_unknown_text_before_stub_reader',lambda:call(txt='different'),True)
 check('reject_unapproved_method_kwargs_before_stub_reader',lambda:call(is_phonemes=True),True)
 bad=copy.deepcopy(row);bad['sha256']='0'*64;check('reject_wrong_PKL_SHA_before_stub_reader',lambda:call(bad),True)
 bad=copy.deepcopy(row);bad['single_thread_marker_sha256']='0'*64;check('reject_wrong_marker_SHA_before_stub_reader',lambda:call(bad),True)
 bad=copy.deepcopy(row);bad['actual_model_input_sha256']='0'*64;check('reject_wrong_post_pron_input_SHA_before_stub_reader',lambda:call(bad),True)
 original_bytes=p.read_bytes();p.unlink();check('reject_missing_PKL_before_stub_reader',call,True)
 target=C/'synthetic-pkl-target';target.write_bytes(original_bytes);p.symlink_to(target);check('reject_linked_PKL_even_with_matching_hash',call,True);p.unlink()
 check('all_bad_cache_guards_prevent_original_stub_read',lambda:h.require(len(called)==require_count,'reader entered on BAD'))
 p=C/'调平_fixture.json';p.write_text('{"1": -1.5, "2": 1.5}');clips=[np.ones(3,dtype=np.float32),np.zeros(2,dtype=np.float32)];tmap=[(0,3,0.,.1),(4,7,.5,.6)];gaps=[.4]
 expected=dict(original_key='fixture',file=p.name,sha256=sha(p),value={'1':-1.5,'2':1.5},clip_SHA256=[hashlib.sha256(x.tobytes()).hexdigest() for x in clips],clip_samples=[3,2],gaps=gaps,original_tmap=[list(x) for x in tmap])
 auto_called=[];old=os.environ.get('STRICT_CACHE');os.environ['STRICT_CACHE']='1';original=lambda *args:auto_called.append('fixture original strict read') or {int(k):float(v) for k,v in json.loads(p.read_text()).items()};observer=types.SimpleNamespace(auto_key=lambda *args:'fixture');m._auto_level=original
 def call_math(expect=expected,ob=observer):return h.original_existing_math_guard(m,ob,original,C,'S2',expect,[])(clips,tmap,gaps,'68',2)
 check('synthetic_existing_math_exact_tuple_and_strict_read',call_math);n=len(auto_called)
 check('reject_unknown_math_key_before_original_stub',lambda:call_math(ob=types.SimpleNamespace(auto_key=lambda *args:'unknown')),True)
 bad=copy.deepcopy(expected);bad['clip_samples']=[3,3];check('reject_wrong_math_clip_tuple_before_original_stub',lambda:call_math(bad),True)
 bad=copy.deepcopy(expected);bad['sha256']='0'*64;check('reject_wrong_math_SHA_before_original_stub',lambda:call_math(bad),True)
 os.environ['STRICT_CACHE']='0';check('reject_nonstrict_math_before_original_stub',call_math,True);os.environ['STRICT_CACHE']='1';original_bytes=p.read_bytes();p.unlink();check('reject_missing_math_no_recalculation',call_math,True)
 target=C/'synthetic-math-target';target.write_bytes(original_bytes);p.symlink_to(target);check('reject_linked_math_even_with_matching_hash',call_math,True);p.unlink()
 check('all_bad_math_guards_prevent_original_calculation',lambda:h.require(len(auto_called)==n,'math called on BAD'))
 # Real unmodified original _auto_level existing-cache branch on tiny synthetic
 # arrays/files. Missing file is rejected by our guard before original math.
 actual_observer=h.load_module('_cold68_actual_observer',I['observer'])
 maker=Path('/workspace/work/source68-book53-actual-MD5-six-FP-source-and-canonical-native-preparation-20261115/actual-final-F-context-preflight/mirror/视频/工具/make_video.py');tree=ast.parse(maker.read_text())
 nodes=[x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name in ['_auto_level','_短起']]
 lq=types.ModuleType('响度一致性核对');lq.IN_GAP=.3;lq.momentary=lambda *a:(_ for _ in ()).throw(AssertionError('No level computation allowed in fixture'))
 old_lq=sys.modules.get('响度一致性核对');sys.modules['响度一致性核对']=lq
 ns=dict(np=np,os=os,json=json,_hl=hashlib,_CACHE=str(C),_REPO_CACHE=str(C/'nonexistent-public'),_to_repo=lambda p:None)
 exec(compile(ast.Module(body=nodes,type_ignores=[]),str(maker),'exec'),ns);original=ns['_auto_level'];m=types.SimpleNamespace(np=np,_hl=hashlib,_短起=ns['_短起'],_auto_level=original)
 key=actual_observer.auto_key(m,clips,tmap,gaps,'68');file=C/('调平_'+key+'.json');file.write_text('{"1": -1.5, "2": 1.5}')
 exact=dict(original_key=key,file=file.name,sha256=sha(file),value={'1':-1.5,'2':1.5},clip_SHA256=[hashlib.sha256(x.tobytes()).hexdigest() for x in clips],clip_samples=[3,2],gaps=gaps,original_tmap=[list(x) for x in tmap])
 fn=h.original_existing_math_guard(m,actual_observer,original,C,'S2',exact,[])
 check('real_original_auto_level_existing_cache_returns_int_keys_no_measurement',lambda:h.require(fn(clips,tmap,gaps,'68',2)=={1:-1.5,2:1.5},'Original G36 ABI int keys'))
 file.unlink();check('real_original_auto_level_guard_missing_cannot_calculate',lambda:fn(clips,tmap,gaps,'68',2),True)
 if old_lq is None:sys.modules.pop('响度一致性核对',None)
 else:sys.modules['响度一致性核对']=old_lq
 if old is None:os.environ.pop('STRICT_CACHE',None)
 else:os.environ['STRICT_CACHE']=old
 # Test real inherited contexts on actual tiny directory inodes, including exceptions.
 support=h.load_module('_cold_actual68_support',I['support']);work=C/'work';work.mkdir();scripts=work/'scripts';scripts.mkdir();(scripts/'68.json').write_bytes(b'ORIGINAL SCRIPT');(scripts/'01.json').write_bytes(b'OTHER SCRIPT');inode=scripts.stat().st_ino
 # Exercise unchanged native closure disabler with synthetic function closures,
 # never actual inference. It must block both primary and opposite methods.
 def wrap(fn):
  def g(*a,**kw):return fn(*a,**kw)
  return g
 native_events=[]
 def native(*a,**kw):native_events.append('synthetic native entered')
 mm=types.SimpleNamespace(k=types.SimpleNamespace(create=wrap(wrap(native)),create_timed=native),KT=types.SimpleNamespace(create_timed=wrap(wrap(native)),create=native));events=[]
 restore=actual_observer.block_native(mm,support,events)
 for obj,method in [(mm.k,'create'),(mm.KT,'create_timed'),(mm.k,'create_timed'),(mm.KT,'create')]:check('unchanged_block_native_rejects_'+method+'_'+('k' if obj is mm.k else 'KT'),lambda:getattr(obj,method)(),True)
 check('blocked_native_never_entered_synthetic_native',lambda:h.require(not native_events and len(events)==4,'Native endpoint escaped'))
 restore();mm.k.create();mm.KT.create_timed();check('unchanged_native_closure_restore',lambda:h.require(len(native_events)==2,'Native closure restore failed'))
 for initial in [None,'0','1']:
  for failure in [False,True]:
   old=os.environ.get('AUDIO_ONLY')
   if initial is None:os.environ.pop('AUDIO_ONLY',None)
   else:os.environ['AUDIO_ONLY']=initial
   environ=dict(os.environ);cwd=Path.cwd();path=list(sys.path);r={}
   try:
    with support.environment_and_cwd(work,r):
     with support.source_namespace(work,b'PRIVATE FIXTURE ONLY',r):
      assert os.environ['AUDIO_ONLY']=='1' and os.environ['STRICT_CACHE']=='1';assert (work/'scripts/68.json').read_bytes()==b'PRIVATE FIXTURE ONLY'
      if failure:raise RuntimeError('fixture intentional')
   except RuntimeError:assert failure
   assert dict(os.environ)==environ and Path.cwd()==cwd and sys.path==path and scripts.stat().st_ino==inode and (scripts/'68.json').read_bytes()==b'ORIGINAL SCRIPT' and (scripts/'01.json').read_bytes()==b'OTHER SCRIPT'
   rows.append(dict(name=f'actual_inherited_context_restores_initial_AUDIO_ONLY_{initial}_exception_{failure}',passed=True))
   if old is None:os.environ.pop('AUDIO_ONLY',None)
   else:os.environ['AUDIO_ONLY']=old
 # Module restoration exact identity with additions and replacement.
 snapshot=dict(sys.modules);prior=sys.modules['json'];sys.modules['_cold_added68']=types.ModuleType('_cold_added68');sys.modules['json']=types.ModuleType('_cold_wrong_json');h.restore_modules(snapshot)
 check('actual_module_restore_added_and_replaced_identities',lambda:h.require(sys.modules['json'] is prior and '_cold_added68' not in sys.modules,'module restore'))
 # Input hashes reject before original programs can be loaded.
 q=C/'fixture.txt';q.write_text('known');mini={'inputs':{'a':{'file':'fixture.txt','bytes':5,'sha256':sha(q)}}};check('finite_input_positive',lambda:h.bind_inputs(C,mini));q.write_text('BAD!!');check('finite_input_rejects_wrong_bytes_before_execution',lambda:h.bind_inputs(C,mini),True)
 mini['inputs']['a']['file']='../fixture.txt';check('finite_input_rejects_namespace_escape',lambda:h.bind_inputs(C,mini),True)
orig=Path('/workspace/work/source35-S15-two-actual-PV-windows-original-cached-scalar-preparation-20261115/observe35_only_S15_two_actual_PV_windows.py')
def funcs(p):
 s=p.read_text();return {x.name:ast.get_source_segment(s,x) for x in ast.parse(s).body if isinstance(x,ast.FunctionDef)}
a,b=funcs(orig),funcs(D/'observe68_only_S6_S2_actual_cached_scalars.py')
check('five_mature_ABI_functions_entire_bytes_unchanged',lambda:h.require(all(a[k]==b[k] for k in ['digest','require','inventory','load_module','bind_inputs']),'mature ABI changed'))
# New coordinate observer must roundtrip the original dossier function exactly;
# this is a numeric tiny-fixture test, not actual source68 timing evidence.
dp=Path('/workspace/work/source68-book53-actual-MD5-six-FP-source-and-canonical-native-preparation-20261115/actual-final-F-context-preflight/mirror/视频/工具/疑点清单.py');ds=dp.read_text();node=next(x for x in ast.parse(ds).body if isinstance(x,ast.FunctionDef) and x.name=='to_w');ns={'SR':24000};exec(compile(ast.Module(body=[node],type_ignores=[]),str(dp),'exec'),ns)
it={'segs':[(10,300,-.0025,[(20,40),(80,120)]),(500,1000,.4,[(100,150)])]}
for idx,(start,end,t0,rm) in enumerate(it['segs']):
 def roundtrip(start=start,end=end,t0=t0,rm=rm):
  for pos in range(start,end):
   local=h.original_segment_raw_to_sentence_sample(it,pos,24000)
   if any(x<=pos-start<y for x,y in rm):assert local is None
   else:assert local is not None and ns['to_w'](it,local/24000)==pos
 check('coordinate_inverse_original_to_w_exact_with_deleted_intervals_'+str(idx),roundtrip)
check('coordinate_inverse_refuses_inserted_gap_or_outside_raw_segment',lambda:h.require(h.original_segment_raw_to_sentence_sample(it,400,24000) is None,'gap mapped'))
r=dict(kind='CODE-ONLY cold tests; actual public inputs and synthetic tiny files, no original cache/audio/model execution',passed=all(x['passed'] for x in rows),tests=rows,tests_count=len(rows),helper_sha256=sha(D/'observe68_only_S6_S2_actual_cached_scalars.py'),profile_sha256=sha(D/'profile.json'),actual_audio_or_model_inference_or_cloud_or_ASR_executed=False)
out=D/'COLD-GUARDS-AND-ACTUAL-CONTEXT-RESTORATION-TESTS.json';out.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print(out,len(rows),r['passed'],sha(out))
