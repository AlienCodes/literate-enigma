"""Original cached whole measurement for actual COMBINED mothers; no new model/TTS/GT/ASR."""
from pathlib import Path
import argparse,ast,collections,contextlib,copy,gc,hashlib,importlib.util,json,os,re,shutil,sys,traceback
sys.dont_write_bytecode=True
ROOT_SHA='5b3662be03af72ff6fa203d7a7d68318145871edc81b7c11517cba638922e068'
PROFILE_SHA='3a5e4fce5e7d8a58a328ce60c48ccf82e4f7ced8033b9e22165aa0af9fe8b1e5'
OBSERVER_SHA='128de00687a82daa6c784e0c7884e4c9fc48d0d4c9ef7f32ed80558f2388aede'
SUPPORT_SHA='29fb324a58d2b40c236317bd8b627cca953f0f2fda91ed8adf45b62b54e8b358'
OLD_SOURCE='e122c817946c4ed6e7cd1394749879276ef2afe9d01ad691b4142c6bbd9ec9b4'
SELECTED_SOURCE='5e83d47b15e2bb605fa9f613867189f69ef488ced8da4c51919b9b1e824ac449'
OLD_CTX='ef53a5cc5795929b5477b40550cab61ee709156112a0f2bc7a2deb071845552c'
NEW_CTX='142686fb2a4764dba90834ecf3ed5cfced2723872a6a84500229e4f2061e6ec6'
DISPLAY='Its amenities included a lounge and, that year, a grand piano.'
PROJECTED='Its amenities included a lounge and that year, a grand piano.'
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
 require((profile['source_id'],profile['book_order'],profile['target_sentence'],profile['actual_scope_targets'],profile['sentence_count'])==('68',53,'S2',['S2','S6'],19) and profile['allow_selected_target_G36_math'] is True,'Exact source68 S2/S6 combined scope required')
 require(root['source_id']=='68' and root['actual_scope_targets']==['S2','S6'] and root['actual_current_whole_reference']['report']['sha256']==profile['inputs']['reference_whole']['sha256'],'Wrong actual ROOT5b366 scope/reference')
 require(digest(inp['source'])==OLD_SOURCE and digest(inp['selected_source'])==SELECTED_SOURCE and digest(inp['old_context'])==OLD_CTX and digest(inp['new_context'])==NEW_CTX,'Wrong current/combined source or phase context')
 old,new=json.loads(inp['source'].read_text()),json.loads(inp['selected_source'].read_text());undo=copy.deepcopy(new)
 require(old['区间声音指纹'].get('S2')=='7590b17b3cb1' and 'S2' not in new['区间声音指纹'] and old['除阻加强']['S6']=={'句末':[9.025,9.085,3.5]} and new['除阻加强']['S6']=={'句末':[9.025,9.035,6.]},'Only exact two authorized data leaves')
 undo['区间声音指纹']['S2']=old['区间声音指纹']['S2'];undo['除阻加强']['S6']=old['除阻加强']['S6'];require(typed(undo)==typed(old),'Other source/body/CF/control changed')
 require(old['词尾除阻']==new['词尾除阻']=={'S8':{'1':[3.205,'t']}} and 'S13' not in old['词尾除阻'],'Preserve original S8 graft; S13 has no graft')
 prior=json.loads(inp['reference_phase_source'].read_text());aligned=copy.deepcopy(old);require(aligned['区间声音指纹'].pop('S2')=='7590b17b3cb1','Current S2 VFP metadata alignment')
 require(sha_bytes(inp['reference_phase_source'].read_bytes())=='f5c533a9411f0f6e746363039092311b02951807d126791e11cff87d51b98145','Never relabel whole reference source as e122')
 group=aligned['核对确认'];previous=prior['核对确认'];changed=0
 for kind,rows in group.items():
  for label,row in rows.items():
   if isinstance(row,dict) and '配音指纹' in row and row['配音指纹']!=previous[kind][label].get('配音指纹'):
    require(row['配音指纹']=='8469bb07c8da' and previous[kind][label]['配音指纹']=='a4f76dab45bd' and kind in {'删除段','机器复听'},'Unexpected confirmation alignment')
    row['配音指纹']=previous[kind][label]['配音指纹'];changed+=1
 require(changed==6 and typed(aligned)==typed(prior),'Only S2 VFP plus six metadata fingerprint alignments allowed')
 oc,nc=json.loads(inp['old_context'].read_text()),json.loads(inp['new_context'].read_text())
 require(set(nc)-set(oc)=={PROJECTED} and {k:v for k,v in nc.items() if k!=PROJECTED}==oc and nc[PROJECTED]['词']=='and' and nc[PROJECTED]['读音']=='ˈænd','Only strong-and full projected S2 CTX; retain S13')
 mother=json.loads(inp['new_mother_H'].read_text());s6=json.loads(inp['S6_H'].read_text())
 require(mother['actual_completed'] is True and mother['actual_shared_context_during_target']==NEW_CTX and mother['title_plus18_nontarget_postpron_tuple_keys_exact'] is True and s6['measurement_completed'] is True and s6['CF_not_mutated_or_accepted'] is True,'Actual strong mother/S6 evidence incomplete')
 require(profile['new_processed_S2_clean_tail_VFP'] is None and profile['new_full_raw_array_MD5_first12']=='49e6ccc03908','Raw mother49e6 must not prefill clean FP')
 ref=json.loads(inp['reference_whole'].read_text());require(ref['phases']['selected']['source_sha256']==profile['baseline_reference_source_SHA256'] and ref['phases']['selected']['actual_complete_WAV']['file_sha256']==profile['baseline_audio']['WAV_sha256']=='c5e6dd2618e476e1a8179c77233797f5101e5e4a22a2b47fa3f2e28ea5c2ca84','Use actual current selected c5e6, not old baseline e7b')
 require(profile['baseline_audio']['WAV_md5']=='8469bb07c8da04e0922209b845b72b80' and profile['baseline_audio']['packet_count']==6660,'Wrong current whole identity')
 return old,new

def sha_bytes(raw):return hashlib.sha256(raw).hexdigest()
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
     require(text==m.spoken(DISPLAY),'Original outer S2 ABI must remain display text before _pron projection')
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
    if label=='selected' and method=='create':require(hashlib.md5(np.ascontiguousarray(a).tobytes()).hexdigest()[:12]=='49e6ccc03908','New full raw array MD5 differs; this is not a processed VFP')
   result.setdefault('actual_postpron_cache_tuples',[]).append(row);return value
  return read
 return factory
def math_factory(lib,original_factory,label,profile):
 def factory(m,original,phase,state,p,result,new_math):
  observed=original_factory(m,original,phase,state,p,result,new_math)
  def guarded(clips,tmap,gaps,no='',rounds=2):
   require(phase==label and str(no)=='68' and rounds==2 and os.environ.get('STRICT_CACHE')=='1','Original math phase/source/rounds strict')
   source_path=Path(m.__file__).resolve().parent/'scripts/68.json';role='source' if label=='baseline' else 'selected_source';require(source_path.is_file() and not source_path.is_symlink() and digest(source_path)==profile['inputs'][role]['sha256'],'Actual phase source at math differs')
   ctx=OLD_CTX if label=='baseline' else NEW_CTX;contexts=[Path(m.__file__).resolve().parent/'按语境读音.json',Path(lib.COMBINED_DECLARED_TOOLS)/'发音词典/按语境读音.json'];require(all(q.is_file() and not q.is_symlink() and digest(q)==ctx for q in contexts),'Actual phase T/W context at math differs')
   current=m._auto_level;m._auto_level=original
   try:key=lib.auto_key(m,clips,tmap,gaps,no)
   finally:m._auto_level=current
   path=lib.CACHE/('调平_'+key+'.json') if key else None
   if path is not None:require(not path.is_symlink(),'Linked math entry forbidden')
   sh=lambda x:hashlib.sha256(m.np.ascontiguousarray(x).tobytes()).hexdigest();sid=state.get('sid')
   if label=='baseline' and sid=='S2':
    e=profile['baseline_S2_original_G36'];require(key==e['original_key'] and path.is_file() and digest(path)==e['sha256'] and [sh(x) for x in clips]==e['clip_SHA256'] and [len(x) for x in clips]==e['clip_samples'] and typed(tmap)==typed(e['original_tmap']) and list(gaps)==e['gaps'],'Baseline S2 actual e55a inputs/readback differ')
   if label=='baseline' and sid=='S6':
    e=profile['baseline_S6_original_G36'];require(key==e['original_key'] and path.is_file() and digest(path)==e['sha256'] and json.loads(path.read_text())=={} and [sh(x) for x in clips]==e['clip_SHA256'] and [len(x) for x in clips]==e['clip_samples'] and typed(tmap)==typed(e['original_tmap']) and list(gaps)==e['gaps'],'Baseline S6 original bb23/44136 actual shape must strict hit; no manufacture')
   if label=='selected' and sid=='S6':
    e=profile['existing_selected_S6_original_G36'];g=profile['S6_expected_original_geometry'];last={k:m.LAST[k] for k in ['head','hs','scale','segs','total','cuts','gaps','fades','grafts']}
    require(key==Path(e['file']).stem.removeprefix('调平_') and path.is_file() and digest(path)==e['sha256'] and json.loads(path.read_text())==e['value']=={} and [sh(x) for x in clips]==g['clip_SHA256'] and [len(x) for x in clips]==g['clip_samples'] and [list(x) for x in tmap]==g['actual_tmap'] and list(gaps)==g['actual_gaps'] and typed(json.loads(json.dumps(last)))==typed(g['actual_original_LAST']),'S6 must strictly read real saved9f744 on exact actual original A20 geometry')
   if label=='selected' and sid=='S2':require(key is not None and key!=profile['baseline_S2_original_G36']['original_key'],'New strong S2 must derive true different math key')
   value=observed(clips,tmap,gaps,no,rounds)
   if label=='selected' and sid=='S2':
    before=digest(path);again=original(clips,tmap,gaps,no,rounds);require(os.environ.get('STRICT_CACHE')=='1' and typed(value)==typed(again) and digest(path)==before,'Actual selected S2 strict math readback failed')
    result['original_G36_calls'][-1]['strict_readback_exact']=True
   return value
  return guarded
 return factory
def runtime_bindings(T,M,W,lib,profile,inp):
 live={T/'发音词典/读音改正.json':lib.DICT_SHA256,T/'发音词典/按语境读音.json':OLD_CTX,W/'读音改正.json':lib.DICT_SHA256,W/'按语境读音.json':OLD_CTX,T/'新管/快测通过.json':lib.STAMP_SHA256,M/'tts/voice_mb.npy':profile['voice_SHA256'],M/'tts/AF.txt':profile['AF_SHA256']}
 live.update({M/'tts'/k:v for k,v in profile['models_SHA256'].items()});oldp=json.loads(inp['old_profile'].read_text());live[T/'纯人声核对.py']=oldp['PV_SHA256'];live[T/'疑点清单.py']=oldp['dossier_SHA256']
 for r in json.loads(inp['overlay'].read_text())['files']:live[T/Path(r['path']).relative_to('视频/工具')]=r['patch_SHA256']
 g=load('_COMBINED_whole_actual_G27',T/'出片指纹.py');paths=g.清单([str(T)])
 require(len(paths)==8 and set(paths)==set(profile['original_G27_expected']) and g.核对工作目录(str(W),str(T))==[],'Original eight actual G27 routes differ')
 for name,p in paths.items():
  q=g._找(name,g.工作目录搜(str(W)));require(q is not None,'Original G27 import path missing '+name);live[Path(p)]=profile['original_G27_expected'][name];live[Path(q)]=profile['original_G27_expected'][name]
 require(all(p.is_file() and digest(p)==h for p,h in live.items()),'Original runtime/model/voice/filter/dictionary/context/stamp differs');return live
def cache_scope(before,after,new_math):return all(after.get(k)==v for k,v in before.items()) and not(set(before)-set(after)) and set(after)-set(before)==set(new_math) and len(new_math)<=1 and all(after.get(k)==v['sha256'] for k,v in new_math.items())
def restore_original_local_modules(snapshot,roots=()):
 local={'make_video','render','title2','title_anim','clean','出片指纹','响度一致性核对','对正量'}
 local.update(k for k in set(snapshot)|set(sys.modules) if k.startswith('_COMBINED_') or k.startswith('_original_68_strict_whole_'))
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
 rows=[r for r in report.get('phases',{}).get('selected',{}).get('original_G36_calls',[]) if r.get('sentence')=='S2' and r.get('actual_math_created') is True]
 calls=report.get('phases',{}).get('selected',{}).get('actual_postpron_cache_tuples',[]);expected={r['name'] for r in profile['target_entries']['selected'].values()};seen={r['name'] for r in calls if r.get('target') is True}
 one=len(new_math)==1;item=next(iter(new_math.values())) if one else {};name=next(iter(new_math)) if one else ''
 return {'all_inner_runtime_source_context_work_module_cache_restores':restored is True,'baseline_and_selected_native_endpoints_restored':all(report.get('native_closure_restore_receipts',{}).get(k) is True for k in ['baseline','selected']),'declared_source_context_and_actual_mother_inputs_checked':report.get('declared_source_context_and_mother_inputs_checked') is True,'both_actual_new_target_mothers_witnessed_before_math':expected<=seen,'one_original_S2_math_creator_and_strict_readback':one and len(rows)==1 and rows[0].get('file')==name and rows[0].get('sha256')==item.get('sha256') and rows[0].get('source_no')=='68' and rows[0].get('original_rounds')==2 and item.get('source_id')=='68' and item.get('target_sentence')=='S2' and item.get('strict_readback_exact') is True,'no_forbidden_model_endpoint_events':report.get('forbidden_model_events')==[]}
def compare_combined(lib,profile,report):
 # Reuse exact original comparison body, changing only the non-target set to
 # exclude the two explicit physical targets. Original function remains intact.
 import inspect
 body=inspect.getsource(lib.compare_phases)
 old="if 'S'+str(i)!=TARGET";new="if 'S'+str(i) not in {'S2','S6'}"
 require(body.count(old)==1,'Original comparison ABI differs');body=body.replace('def compare_phases(','def compare_combined_original_body(',1).replace(old,new)
 namespace=dict(lib.__dict__);exec(compile(body,'<original compare with exact two-target set>','exec'),namespace);namespace['compare_combined_original_body'](profile,report)
 old_phase,new_phase=report['phases']['baseline'],report['phases']['selected']
 for sid in ['S'+str(i) for i in range(1,20) if i not in (2,6)]:require(typed(old_phase['observed_sentences'][sid])==typed(new_phase['observed_sentences'][sid]),'Non-target raw/mother/cuts/gains/full local metadata changed: '+sid)
 math_rows=lambda phase:collections.Counter(json.dumps({k:v for k,v in r.items() if k!='phase'},sort_keys=True) for r in phase['original_G36_calls'] if r['sentence'] not in {'S2','S6'})
 require(math_rows(old_phase)==math_rows(new_phase),'Non-target original math key/clip/gaps/tmap/value/strict identity changed');report['all_18_nontarget_raw_mother_cut_and_original_math_identity_exact']=True
 rows=report['all_non_target_title_and_sentence_identity'];require(len(rows)==18 and {r['segment'] for r in rows}=={'title'}|{'S'+str(i) for i in range(1,20) if i not in (2,6)},'Exact title+17 combined non-target comparison required')

def observe_whole_PV_and_t(a,lib,inp,profile,report):
 # Original detector, actual complete selected PCM16 decoded from the already
 # measured private WAV. This emits scalar evidence and never writes CF.
 import soundfile as sf
 base=load('_COMBINED_original68_burst_observer',inp['original_burst_helper']);pv=load('_COMBINED_original68_PV',a.tools/'纯人声核对.py')
 selected=report['phases']['selected'];pcm,rate=sf.read(Path(selected['private_work_preserved_path'])/'a.wav');require(rate==24000 and len(pcm)==selected['actual_complete_WAV']['samples'],'Actual whole decoded PCM clock differs')
 prior=json.loads(inp['S6_scalar'].read_text());oldrow=prior['candidate']['original_local_PV_and_burst']['all_original_candidate_scan_flags'][0];oldclock=json.loads(inp['reference_whole'].read_text())['phases']['selected']['actual_sample_clock']['S6'];clock=selected['actual_sample_clock']['S6'];delta=(clock['start_sample']-oldclock['start_sample'])/rate
 target_window=[oldrow['original_complete_f'][1]+delta,oldrow['original_complete_f'][2]+delta];rows=[];source=json.loads(inp['selected_source'].read_text());require(len(prior['candidate']['original_local_PV_and_burst']['all_original_candidate_scan_flags'])==1,'Prior exact S6 scalar must contain one actual reference flag')
 for f in pv.scan(pcm):
  key=pv.key(f);cf=source.get('核对确认',{}).get('非人声',{}).get(key,{});ok,reason=pv.确认可收('68',f,cf,pcm)
  rows.append({'original_complete_f':list(f),'current_key':key,'current_original_metrics':pv.实测(f),'original_像吸气':pv.像吸气(f),'original_爆破起':pv.爆破起(pcm,f),'current_unchanged_source_CF_check':[ok,reason],'unchanged_CF_metrics_comparison_is_not_current_fullwave_fingerprint_acceptance':True,'original_burst_details':base.original_burst_details(pv,pcm,f),'matches_actual_S6_window_by_sample_clock':all(abs(f[i+1]-target_window[i])<1e-8 for i in (0,1))})
 targets=[r for r in rows if r['matches_actual_S6_window_by_sample_clock']];other=[r for r in rows if not r['matches_actual_S6_window_by_sample_clock'] and not r['current_unchanged_source_CF_check'][0]]
 report['actual_selected_whole_original_PV_and_exact_S6_t']={'scope':'actual current whole PCM16 and absolute clock; no CF write or quality acceptance','selected_WAV_MD5':selected['actual_complete_WAV']['file_md5'],'selected_WAV_FP_first12':selected['actual_complete_WAV']['file_md5_first12'],'selected_S6_clock':clock,'old_local_reference_clock_not_reused_as_current':oldclock,'actual_S6_flag_window_derived_from_true_clock':target_window,'all_original_flags':rows,'exact_S6_target_rows':targets,'unconfirmed_other_flags':other,'conditional_exact_t_CF_evidence_ready':len(targets)==1 and targets[0]['original_爆破起'] is True and targets[0]['original_像吸气'] is False and not other,'CF_written':False,'quality_acceptance':False,'human_listening_or_user_confirmation_performed':False}
 report['conditional_exact_S6_CF_evidence_ready']=report['actual_selected_whole_original_PV_and_exact_S6_t']['conditional_exact_t_CF_evidence_ready']

def main():
 parser=argparse.ArgumentParser()
 for k in ['tools','video-root','inputs','profile','execution-adoption','output','cache-path-output']:parser.add_argument('--'+k,type=Path,required=True)
 parser.add_argument('--execution-adoption-sha256',required=True);a=parser.parse_args()
 report={'kind':'source68-COMBINED-currente122-baseline-vs-combinedS2S6-selected-original-cachedwhole-scalar','source_id':'68','book_order':53,'target_sentence':'S2','measurement_completed':False,'exact_scope_proved':False,'quality_acceptance':False,'formal_acceptance':False,'production_delivery_eligible':False,'new_TTS_GT_ASR_or_native_executed':False,'phases':{},'restoration':{},'forbidden_model_events':[],'errors':[]}
 modules=dict(sys.modules);env=dict(os.environ);cwd=Path.cwd();path=list(sys.path);trace=sys.gettrace();inp=profile=before=public=live=lib=None;new_math={};used={};oldfunctions=None;T=a.tools.resolve();M=a.video_root.resolve();W=M/'video';C=M/'tts/cache_tts'
 try:
  require(a.execution_adoption_sha256==ROOT_SHA and digest(a.execution_adoption)==ROOT_SHA,'Actual ROOT5b366 literal CLI record required')
  require(digest(a.profile)==PROFILE_SHA,'Wrong current COMBINED whole profile');profile=json.loads(a.profile.read_text());inp={}
  for role,r in profile['inputs'].items():
   rel=Path(r['file']);require(not rel.is_absolute() and '..' not in rel.parts,'Frozen input escaped');p=a.inputs/rel;require(p.stat().st_size==r['bytes'] and digest(p)==r['sha256'],'Wrong frozen input '+role);inp[role]=p
  require(digest(inp['observer'])==OBSERVER_SHA and digest(inp['support'])==SUPPORT_SHA,'Original whole library/support bytes differ')
  old,new=validate_bundle(profile,inp,json.loads(a.execution_adoption.read_text()))
  require(not a.output.resolve().is_relative_to(M) and not a.cache_path_output.resolve().is_relative_to(M) and not a.output.exists(),'Fresh scalar/private-step paths outside cached machine required')
  require(all(os.environ.get(k)=='1' for k in ['AUDIO_ONLY','STRICT_CACHE','XG_NOPUSH','XG_KEEP_REVIEWED_GAIN','XG_KEEP_REVIEWED_ENDING','XG_KEEP_REVIEWED_CUTS']) and not any(os.environ.get(k) for k in ['VOICE','AFFILE','OLD_IV_VOID','ONLY','BREATH_FRAC','CACHE_LOG']),'Exact reviewed strict environment required')
  require(Path('/home/user/postgraduate-vocabulary').resolve()==T.parent.parent,'Original ROOT alias differs')
  lib=load('_COMBINED_original68_whole_library',inp['observer']);support=load('_COMBINED_original68_mother_scope',inp['support']);require(lib.SOURCE_NO==support.SOURCE_NO=='68' and lib.TARGET==support.TARGET=='S2' and lib.COUNT==19,'Do not retarget another source/mother helper')
  support.validate_certificate(T,json.loads(inp['overlay'].read_text()),json.loads(inp['certificate'].read_text()))
  lib.CACHE=C;lib.COMBINED_DECLARED_TOOLS=T;lib.phase_arrays.clear();lib.phase_post_arrays.clear();lib.phase_int16_arrays.clear();oldfunctions=(lib.strict_cached_guard,lib.math_guard,lib.block_native);live=runtime_bindings(T,M,W,lib,profile,inp);report['native_closure_restore_receipts']={'baseline':False,'selected':False}
  for name,h in profile['all_required_actual_mother_and_marker_fullSHAs'].items():p=C/name;require(p.is_file() and not p.is_symlink() and digest(p)==h,'Actual phase S2/S6 mother/marker missing or wrong')
  e=profile['baseline_S2_original_G36'];require((C/e['file']).is_file() and not (C/e['file']).is_symlink() and digest(C/e['file'])==e['sha256'],'Actual baseline e55a missing/wrong')
  e=profile['baseline_S6_original_G36'];require((C/e['file']).is_file() and not (C/e['file']).is_symlink() and digest(C/e['file'])==e['sha256'] and json.loads((C/e['file']).read_text())=={},'Existing baseline S6 bb23 absent/wrong; must stop before any mathematics')
  e=profile['existing_selected_S6_original_G36'];require((C/e['file']).is_file() and not (C/e['file']).is_symlink() and digest(C/e['file'])==e['sha256'] and json.loads((C/e['file']).read_text())=={},'Actual selected S6 saved9f744 missing/wrong')
  report['declared_source_context_and_mother_inputs_checked']=True;report['actual_input_SHA256']={k:digest(v) for k,v in inp.items()};report['actual_execution_scope_SHA256']=ROOT_SHA;report['actual_profile_SHA256']=PROFILE_SHA;report['actual_runtime_contract_before']={str(q):digest(q) for q in live}
  before=inventory(C);public=inventory(T.parent/'配音缓存');scratch=M/'_source68_COMBINED_original_cachedwhole';require(not scratch.exists(),'Fresh whole scratch namespace required');scratch.mkdir();paths={'T':T,'M':M,'W':W,'scratch':scratch}
  with support.environment_and_cwd(W,report['restoration']):
   with lib.work_namespace(W/'work_68',scratch,report['restoration']):
    for label,role in [('baseline','source'),('selected','selected_source')]:
     ctx=OLD_CTX if label=='baseline' else NEW_CTX
     manager=contextlib.nullcontext() if label=='baseline' else selected_context_namespace(T,W,inp['old_context'].read_bytes(),inp['new_context'].read_bytes(),scratch,report['restoration'])
     with manager:
      lib.CTX_SHA256=ctx;require(digest(T/'发音词典/按语境读音.json')==digest(W/'按语境读音.json')==ctx,'T/W declared context must precede source/maker import')
      lib.strict_cached_guard=cached_factory(lib,oldfunctions[0],label,profile);lib.math_guard=math_factory(lib,oldfunctions[1],label,profile)
      lib.block_native=tracked_native_blocker(oldfunctions[2],label,report['native_closure_restore_receipts'])
      with phase_source_namespace(support,W,inp[role].read_bytes(),report['restoration']):lib.run_phase(label,inp[role].read_bytes(),profile['inputs'][role]['sha256'],paths,support,profile,report,used,new_math)
     if label=='baseline':
      b=report['phases']['baseline'];expected=profile['baseline_target_expected_observed'];actual=b['observed_sentences']['S2'];require(typed(actual)==typed(expected),'Actual current whole S2 physical/DSP baseline differs from reference after explicit metadata alignment')
      require(b['actual_sample_clock']['S2']==profile['baseline_target_expected_clock'],'Actual current whole baseline S2 clock/float differs')
      require(b['actual_complete_WAV']['file_md5']==profile['baseline_audio']['WAV_md5'],'Current complete baseline MD5 differs')
  lib.CTX_SHA256=OLD_CTX
  report['measurement_completed']=True;compare_combined(lib,profile,report)
  require(report['actual_global_master_scale_ratio_selected_over_baseline']==1.0,'Actual original global master scale must remain exactly1')
  def nontarget(phase):return collections.Counter(json.dumps({k:v for k,v in r.items() if k!='target'},sort_keys=True,ensure_ascii=False) for r in phase['actual_postpron_cache_tuples'] if not r['target'])
  require(nontarget(report['phases']['baseline'])==nontarget(report['phases']['selected']),'A title/non-target/helper post-pron tuple/key changed')
  report['all_title17_nontarget_and_helper_postpron_key_multisets_exact']=True
  report['actual_new_processed_S2_VFP']=report['phases']['selected']['observed_sentences']['S2']['actual_raw_w_fingerprint'];report['new_clean_VFP_not_assumed_equal_full_raw49e6']=True
  report['actual_S2_duration_delta_samples']=report['phases']['selected']['observed_sentences']['S2']['samples']-report['phases']['baseline']['observed_sentences']['S2']['samples']
  report['actual_absolute_clock_deltas']={sid:{'start_sample_delta':report['phases']['selected']['actual_sample_clock'][sid]['start_sample']-v['start_sample'],'end_sample_delta':report['phases']['selected']['actual_sample_clock'][sid]['end_sample_exclusive']-v['end_sample_exclusive']} for sid,v in report['phases']['baseline']['actual_sample_clock'].items()}
  report['actual_S6_selected_pre_master_exact']=report['phases']['selected']['observed_sentences']['S6']['pre_master_PCM_sha256']==profile['S6_expected_pre_master_SHA256'];require(report['actual_S6_selected_pre_master_exact'] and report['phases']['selected']['observed_sentences']['S6']['samples']==214200,'Selected whole S6 must equal actually measured original boost9f744 PCM')
  selected_rows=[r for r in report['phases']['selected']['original_G36_calls'] if r['sentence']=='S6'];e=profile['existing_selected_S6_original_G36'];require(len(selected_rows)==1 and selected_rows[0]['file']==e['file'] and selected_rows[0]['sha256']==e['sha256'] and selected_rows[0]['value']=={} and selected_rows[0]['actual_math_created'] is False and selected_rows[0]['strict_after'] is True,'Selected S6 existing9f744 original read must be witnessed exactly once')
  report['exact_scope_proved']=True
  observe_whole_PV_and_t(a,lib,inp,profile,report)
 except BaseException as e:report['errors'].append({'type':type(e).__name__,'detail':str(e)});traceback.print_exc()
 finally:
  try:
   if lib is not None:
    lib.CTX_SHA256=OLD_CTX
    if oldfunctions is not None:lib.strict_cached_guard,lib.math_guard,lib.block_native=oldfunctions
   if before is not None:report['all_existing_private_cache_exact_only_one_actual_S2_math_added']=cache_scope(before,inventory(C),new_math);report['public_cache_exact_after']=inventory(T.parent/'配音缓存')==public
   if live is not None:report['all_runtime_model_voice_AF_G27_dict_context_stamp_bytes_exact_after']=all(p.is_file() and digest(p)==h for p,h in live.items())
   if inp is not None:report['all_frozen_inputs_exact_after']=all(digest(p)==profile['inputs'][r]['sha256'] for r,p in inp.items())
  except BaseException as e:report['errors'].append({'type':type(e).__name__,'detail':str(e),'during':'restore-input-scope'})
  os.environ.clear();os.environ.update(env);os.chdir(cwd);sys.path[:]=path;sys.settrace(trace)
  report['actual_local_module_restoration']=restore_original_local_modules(modules,[T,W,a.inputs.resolve()])
  report['all_original_local_modules_preexisting_objects_env_cwd_path_trace_restored']=all(v is True for v in report['actual_local_module_restoration'].values() if type(v) is bool) and dict(os.environ)==env and Path.cwd()==cwd and sys.path==path and sys.gettrace() is trace
  guards=['all_original_local_modules_preexisting_objects_env_cwd_path_trace_restored','all_existing_private_cache_exact_only_one_actual_S2_math_added','public_cache_exact_after','all_runtime_model_voice_AF_G27_dict_context_stamp_bytes_exact_after','all_frozen_inputs_exact_after']
  restored=all(report.get(k) is True for k in guards) and all(report['restoration'].get(k) is True for k in ['normal_scripts_namespace_restored','environment_cwd_sys_path_restored','normal_work_inode_and_PCM_restored','both_T_W_original_context_inode_and_bytes_restored','selected_context_payload_exact_at_exit'])
  report['measurement_completed']=bool(report['measurement_completed'] and restored and not report['errors'] and not report['forbidden_model_events']);report['exact_scope_proved']=bool(report['exact_scope_proved'] and report['measurement_completed']);report['actual_new_S2_original_math']=new_math;report['math_save_integrity_proved']=False
  report['actual_math_scope_prerequisites']=math_scope_prerequisites(report,new_math,profile,restored) if profile is not None else {}
  report['math_scope_integrity_proved']=bool(report['actual_math_scope_prerequisites'] and all(v is True for v in report['actual_math_scope_prerequisites'].values()))
  report['proven_original_math_scope_is_independent_of_whole_or_quality_verdict']=True
  try:
   if report['math_scope_integrity_proved']:
    folder=M/'tts/source68-only-S2-combined-whole-original-math-cache';require(not folder.exists(),'Fresh single-S2 SAVE namespace required');folder.mkdir();saved=[]
    for name,row in new_math.items():p=folder/name;shutil.copyfile(C/name,p);require(digest(p)==row['sha256'],'Actual new math SAVE copy differs');saved.append(str(p))
    runid=os.environ.get('GITHUB_RUN_ID','');require(runid.isdigit(),'Actual Actions run ID required');key='Linux-native68-only-S2-combined-whole-original-math-'+runid
    report['private_original_math_save']={'cache_key':key,'exact_paths':saved,'files':new_math,'save_success_not_claimed':True};report['math_save_integrity_proved']=True
    a.cache_path_output.parent.mkdir(parents=True,exist_ok=True)
    with a.cache_path_output.open('a') as f:f.write('cache_key='+key+'\ncache_paths<<ONLY_S2_COMBINED_MATH_PATHS\n'+'\n'.join(saved)+'\nONLY_S2_COMBINED_MATH_PATHS\n')
  except BaseException as e:report['measurement_completed']=report['exact_scope_proved']=report['math_scope_integrity_proved']=False;report['errors'].append({'type':type(e).__name__,'detail':str(e),'during':'private-math-staging-only'})
  a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,ensure_ascii=False,indent=2,default=lambda x:x.item())+'\n');print(json.dumps({'measurement_completed':report['measurement_completed'],'exact_scope_proved':report['exact_scope_proved'],'quality_acceptance':False,'output_SHA256':digest(a.output),'errors':report['errors']},ensure_ascii=False))
 return 0 if report['measurement_completed'] and report['exact_scope_proved'] else 1
if __name__=='__main__':sys.exit(main())
