#!/usr/bin/env python3
"""Original certified17 AUDIO_ONLY builder; strictly cached models, exact identity.

Only the two new-mother G36 keys may be derived by the unchanged original
ffmpeg-math function. This is diagnosis, never an audio gate or 4K acceptance.
"""
import argparse,ast,copy,gc,hashlib,importlib.util,json,os,shutil,subprocess,sys,tempfile
from pathlib import Path
import numpy as np
p=argparse.ArgumentParser();p.add_argument('--tools',type=Path,required=True);p.add_argument('--video-root',type=Path,required=True);p.add_argument('--request43',type=Path,required=True);p.add_argument('--request52',type=Path,required=True);p.add_argument('--cache-contract',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--reference',type=Path,default=Path(__file__).with_name('spoken-whole-track-reference.json'));a=p.parse_args()
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();arrsha=lambda x:hashlib.sha256(np.ascontiguousarray(x).tobytes()).hexdigest();canon=lambda x:json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False)
ref=json.loads(a.reference.read_text());contract=json.loads(a.cache_contract.read_text());T=a.tools.resolve();M=a.video_root.resolve();O=a.output.resolve();PR=M/'spoken-whole-track-diagnostic';W=PR/'video';W.mkdir(parents=True,exist_ok=True);(W/'scripts').mkdir(exist_ok=True)
assert sha(a.cache_contract)==ref['cache_contract_sha256'];assert sha(T/'make_video.py')==ref['maker_sha256'];assert os.environ.get('XG_NOPUSH')=='1';os.environ['STRICT_CACHE']='1';os.environ['AUDIO_ONLY']='1';os.environ.pop('OLD_IV_VOID',None)
assert not os.environ.get('VOICE')and not os.environ.get('AFFILE')
if not (PR/'tts').exists():(PR/'tts').symlink_to(M/'tts',target_is_directory=True)
assert (PR/'tts').resolve()==(M/'tts').resolve();cache=M/'tts/cache_tts';assert cache.is_dir()and not cache.is_symlink()
private_save=M/'tts/spoken-comma-whole-reference-cache';private_save.mkdir(exist_ok=True);normal_six=M/'tts/spoken-comma-reference-cache';assert normal_six.is_dir()
requests={43:a.request43.resolve(),52:a.request52.resolve()};candidates={};bases={};source_files={};inputs=[]
for no,root in requests.items():
 src=root/'视频/脚本'/f'{no}.json';gen=root/'视频/工具/初稿生成'/f'gen{no}.py';base=Path(__file__).parent/'baselines'/f'{no}.json'
 assert sha(src)==ref['candidates'][str(no)]['source_sha256']and sha(gen)==ref['candidates'][str(no)]['GEN_sha256'];assert sha(base)==ref['baselines'][str(no)]['source_sha256']
 candidates[no]=json.loads(src.read_text());bases[no]=json.loads(base.read_text());source_files[no]=src;inputs += [src,gen,base]
source_hashes={str(x):sha(x)for x in inputs};models_before={n:sha(M/'tts'/n)for n in contract['models']};assert models_before==contract['models']
assert sha(M/'tts/voice_mb.npy')=='1f97658bb5a4280cc3f6c01dc644dff471bf57c970fc8b99f3049d6991c4f6c8'
def bare(data):return [data['title_en']]+[' '.join(__import__('re').sub(r'\*\*','',__import__('re').sub(r'\{\{.*?\}\}','',c['en'])).strip()for c in s['chunks'])for s in data['sentences']]
for no in (43,52):assert bare(bases[no])==bare(candidates[no])
assert not candidates[52].get('结尾句',{}).get('S18'),'S18 no-comma explicit ENDING0; do not infer ending reconstruction.'
for no in (43,52):
 for sid,value in ref['candidates'][str(no)]['root_manual_gain_leaves'].items():assert candidates[no].get('分段增益dB',{}).get(sid)==value
report={'kind':'strict-original-certified17-private-AUDIO_ONLY-whole-track-diagnostic','diagnostic_only':True,'formal_audio_or_video_accepted':False,'original_Q8_R_two_ASR_cut_highlight_and_final_fullV3_still_required':True,'maker_sha256':sha(T/'make_video.py'),'source_input_sha256':source_hashes,'six_mother_contract_sha256':sha(a.cache_contract),'new_model_inference':False,'cases':[],'pure_math_derived_G36':[],'passed':False}
six=[]
for case in contract['case_evidence']:
 for item in case['model_inputs']:
  for name,h in [(item['cache_key'],item['cache_PKL_SHA256']),(item['cache_key']+'.单线程',item['single_thread_marker_SHA256'])]:
   src=normal_six/name;assert src.is_file()and sha(src)==h
   for dest in (cache/name,private_save/name):
    if dest.exists():assert sha(dest)==h
    else:shutil.copyfile(src,dest)
   six.append({'name':name,'SHA256':h})
report['actual_six_original_format_cache_files_verified']=six
original_cache_stat={x.name:(x.stat().st_size,x.stat().st_mtime_ns)for x in cache.iterdir()if x.is_file()};new_derived_names=set();negative_tests=[]
def signature(m,clips,tmap,gaps,no):
 tree=ast.parse((T/'make_video.py').read_text());func=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='_auto_level');value=next(n.value for n in func.body if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='_k'for t in n.targets))
 key=eval(compile(ast.Expression(body=value),str(T/'make_video.py')+'#actual-_auto_level-key-expression','eval'),m.__dict__,dict(clips=clips,tmap=tmap,gaps=gaps,no=no))
 return {'key':key,'clip_SHA256':[arrsha(x)for x in clips],'clip_samples':[len(x)for x in clips],'gaps':list(gaps),'tmap':copy.deepcopy(tmap),'no':str(no)}
def validate_pin(actual,expected,stage,sid):
 if stage!='candidate'or sid not in expected:raise AssertionError('Only the exact two new-mother candidate G36 inputs may enter math preparation')
 if canon(actual)!=canon(expected[sid]):raise AssertionError('New-mother G36 clips/source/tmap/gaps differ from actual certified-mother preflight')
def run_stage(no,stage,data,baseline_arrays=None):
 for n in (43,52):(W/'scripts'/f'{n}.json').write_text(json.dumps((bases if stage=='baseline'else candidates)[n],ensure_ascii=False,indent=2)+'\n')
 os.chdir(W);sys.path.insert(0,str(T));sys.path.insert(0,str(W));os.environ['TMPDIR']=str(PR/'tmp');Path(os.environ['TMPDIR']).mkdir(exist_ok=True);tempfile.tempdir=None
 name=f'actual_spoken_whole_diagnostic_{no}_{stage}';spec=importlib.util.spec_from_file_location(name,T/'make_video.py');m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m)
 state={'sid':None,'counter':0};records={};arrays={};prelevel_pins={};orig_sentence=m.sentence_audio;orig_gain=m.句增益;orig_title=m.title_audio;orig_level=m._auto_level;orig_repo=m._REPO_CACHE;orig_cache=m._CACHE
 # Models remain hard cache-only even during the explicitly separate pure G36
 # math call. A model attempt with STRICT off is rejected before original fn.
 for obj,method in [(m.k,'create'),(m.KT,'create_timed')]:
  actual=getattr(obj,method)
  def strict_only(*args,_actual=actual,**kw):
   if os.environ.get('STRICT_CACHE')!='1':raise AssertionError('Model calls must stay STRICT_CACHE=1; this helper never infers')
   return _actual(*args,**kw)
  setattr(obj,method,strict_only)
 try:
  if stage=='candidate':
   m._SPOKEN_SOURCE_NO=str(no)
   for case in contract['case_evidence']:
    if case['source_id']!=no:continue
    sid=case['sentence'];sent=bare(data)[int(sid[1:])]
    if sid not in ref['candidates'][str(no)]['new_G36_only']:
     assert no==52 and sid=='S18'and sent not in m.ENDING and m._speech_marks(sent)==[]
     continue  # No redundant mother/cut/L14 retest; whole build reads this cached sentence once.
    marks=m._speech_marks(sent);pieces=[];gaps=[];p0=0;listed=m.list_commas(sent)
    for mark in marks:pieces.append((p0,mark.end()));p0=mark.end()+1;gaps.append(m.P_LIST if mark.start()in listed else m.P_COMMA)
    pieces.append((p0,len(sent)));clips,tmap=orig_sentence(sent,pieces,gaps)
    assert m.SENT_FP[sent]==case['actual_raw_fingerprint']and canon(tmap)==canon(case['actual_processed_tmap'])and canon(m.LAST['cuts'])==canon(case['actual_processed_cuts'])
    if sid in ref['candidates'][str(no)]['new_G36_only']:
     prelevel_pins[sid]=signature(m,clips,tmap,gaps,no)
     mutated=copy.deepcopy(prelevel_pins[sid]);mutated['clip_SHA256'][0]='0'*64
     for label,actual_pin,test_stage,test_sid in [('one-sample-or-wrong-clip-hash',mutated,stage,sid),('wrong-source',{**prelevel_pins[sid],'no':'999'},stage,sid),('wrong-sentence',prelevel_pins[sid],stage,'S999'),('baseline-cannot-derive',prelevel_pins[sid],'baseline',sid)]:
      try:validate_pin(actual_pin,prelevel_pins,test_stage,test_sid)
      except AssertionError:negative_tests.append({'source':no,'sentence':sid,'case':label,'rejected':True})
      else:raise AssertionError('G36 preparation negative failed '+label)
    elif no==52 and sid=='S18':assert len(pieces)==1 and gaps==[]
  def controlled_level(clips,tmap,gaps,no='',rounds=2):
   sid=state['sid'];expected=prelevel_pins.get(sid)
   if expected is None:return orig_level(clips,tmap,gaps,no,rounds)
   assert rounds==2;actual=signature(m,clips,tmap,gaps,no);validate_pin(actual,prelevel_pins,stage,sid)
   key=actual['key'];filename='调平_'+key+'.json';math_dir=PR/f'derived-original-math-{no}-{sid}';math_dir.mkdir(exist_ok=True);math_file=math_dir/filename
   assert not math_file.exists(),'Fresh private original-math directory required for the initial diagnostic'
   m._CACHE=str(math_dir);m._REPO_CACHE=str(PR/'nonexistent-no-public-export');assert not Path(m._REPO_CACHE).exists();os.environ.pop('STRICT_CACHE',None)
   try:value=orig_level(clips,tmap,gaps,no,rounds)
   finally:os.environ['STRICT_CACHE']='1';m._CACHE=orig_cache;m._REPO_CACHE=orig_repo
   assert math_file.is_file();stored=json.loads(math_file.read_text());assert {int(k):float(v)for k,v in stored.items()}==value
   dest=cache/filename
   if dest.exists():assert json.loads(dest.read_text())==stored,'Existing derived cache disagrees with actual original math'
   else:shutil.copyfile(math_file,dest);new_derived_names.add(filename)
   saved=private_save/filename
   if saved.exists():assert sha(saved)==sha(dest)
   else:shutil.copyfile(dest,saved)
   again=orig_level(clips,tmap,gaps,no,rounds);assert again==value
   report['pure_math_derived_G36'].append({'source_id':int(no),'sentence':sid,'actual_prelevel_pin':actual,'key':filename,'JSON_sha256':sha(dest),'JSON_bytes':dest.stat().st_size,'value':stored,'original_auto_level_algorithm_only':True,'strict_cached_readback_same':True,'new_TTS_or_model_call':False})
   prelevel_pins.pop(sid)
   return value
  m._auto_level=controlled_level
  def title_capture(text):
   out=orig_title(text);arrays['title']=out.copy();records['title']={'samples':len(out),'pre_master_float32_SHA256':arrsha(out)};return out
  def sentence_capture(sent,pieces,gaps):
   state['counter']+=1;sid='S'+str(state['counter']);state['sid']=sid;assert sent==bare(data)[state['counter']]
   clips,tmap=orig_sentence(sent,pieces,gaps);records[sid]={'samples_before_gain':sum(len(x)for x in clips),'before_gain_float32_SHA256':arrsha(np.concatenate(clips)),'before_gain_clips':[{'samples':len(x),'SHA256':arrsha(x)}for x in clips],'tmap':copy.deepcopy(tmap),'gaps':list(gaps),'raw_fingerprint':m.SENT_FP[sent],'cuts':copy.deepcopy(m.LAST['cuts'])};return clips,tmap
  def gain_capture(d,number,si,sent,pieces,gaps,clips,tmap,arr):
   assert state['sid']=='S'+str(si+1);result=orig_gain(d,number,si,sent,pieces,gaps,clips,tmap,arr);aout=result[1];arrays[state['sid']]=aout.copy();records[state['sid']].update(samples=len(aout),pre_master_float32_SHA256=arrsha(aout),automatic_level=result[2],manual_segment_level=result[3]);return result
  m.title_audio=title_capture;m.sentence_audio=sentence_capture;m.句增益=gain_capture
  out=PR/f'{no}-{stage}.m4a';source=W/'scripts'/f'{no}.json';m.build(str(source),str(out));wav=W/f'work_{no}/a.wav';assert len(records)==len(data['sentences'])+1 and not prelevel_pins
  peak=max(float(np.abs(v).max())for v in arrays.values());aac=hashlib.sha256(subprocess.check_output(['ffmpeg','-v','error','-nostdin','-i',str(out),'-map','0:a:0','-c:a','copy','-f','adts','-'])).hexdigest();probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_entries','stream=codec_name,codec_type,sample_rate,channels:format=duration','-of','json',str(out)]));row={'stage':stage,'source_id':no,'raw_WAV_sha256':sha(wav),'AAC_ADTS_sha256':aac,'raw_WAV_bytes':wav.stat().st_size,'master_pre_peak':peak,'master_ideal_multiplier':.89/peak,'master_exact_original_operation':'A / np.abs(A).max() * 0.89 (original NumPy dtype/arithmetic)','codec_probe':probe,'sentence_pre_master_records':records,'actual_segment_record':json.loads((W/f'work_{no}/分段.json').read_text())}
  if stage=='baseline':
   assert row['raw_WAV_sha256']==ref['baselines'][str(no)]['raw_WAV_sha256']and aac==ref['baselines'][str(no)]['AAC_ADTS_sha256'],'Actual old current whole WAV/AAC must both bind before identity comparison'
   row['actual_current_native_WAV_AAC_double_bound']=True
  else:
   allowed=set(ref['candidates'][str(no)]['voice_changed_sentences']);outside={};inside={}
   for sid,arr in arrays.items():
    old=baseline_arrays[sid];record={'same_samples':len(old)==len(arr),'array_equal':bool(np.array_equal(old,arr)),'old_SHA256':arrsha(old),'new_SHA256':arrsha(arr)}
    if sid not in allowed:assert record['array_equal'];outside[sid]=record
    else:inside[sid]=record
   row['all_title_and_non_target_pre_master_PCM_exact']=outside;row['only_authorized_changed_sentence_pre_master_PCM']=inside;row['new_whole_track_identity_actual_not_guessed']=True
  wav.unlink();out.unlink();return row,arrays
 finally:
  sys.modules.pop(name,None);del m;gc.collect()
try:
 for no in (43,52):
  baseline,arrays=run_stage(no,'baseline',bases[no]);entry={'source_id':no,'baseline':baseline};report['cases'].append(entry)
  candidate,_=run_stage(no,'candidate',candidates[no],arrays);entry.update(candidate=candidate,master_ideal_multiplier_ratio_new_over_old=candidate['master_ideal_multiplier']/baseline['master_ideal_multiplier'],post_master_same_audio_not_claimed_if_coefficient_changes=True);del arrays;gc.collect()
 assert len(report['pure_math_derived_G36'])==2;report['passed']=True
except BaseException as exc:report['error']={'type':type(exc).__name__,'detail':str(exc)};raise
finally:
 report['actual_pure_math_scope_negative_tests']=negative_tests;report['original_source_GEN_baseline_files_still_exact']=all(sha(Path(k))==v for k,v in source_hashes.items());report['models_still_exact']={n:sha(M/'tts'/n)for n in contract['models']}==models_before
 actual_stat={x.name:(x.stat().st_size,x.stat().st_mtime_ns)for x in cache.iterdir()if x.is_file()};report['existing_normal_cache_files_stat_unchanged']=all(actual_stat.get(k)==v for k,v in original_cache_stat.items());report['only_new_normal_cache_files_are_two_derived_JSON']=set(actual_stat)-set(original_cache_stat)==new_derived_names;report['private_cache_save_folder']=str(private_save);report['private_media_or_PCM_in_public_output']=False
 assert report['original_source_GEN_baseline_files_still_exact']and report['models_still_exact']and report['existing_normal_cache_files_stat_unchanged']and report['only_new_normal_cache_files_are_two_derived_JSON']
 O.parent.mkdir(parents=True,exist_ok=True);O.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'passed':report['passed'],'output':str(O),'new_derived':sorted(new_derived_names)},ensure_ascii=False))
