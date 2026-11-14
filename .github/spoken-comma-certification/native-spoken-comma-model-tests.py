#!/usr/bin/env python3
"""Six explicitly authorized actual model inputs, original cache and timing guards.

Run only in the dedicated preparatory subprocess. Public output is scalar;
private original-format PKLs remain in the internal cache, never the artifact.
This certifies interface and real timing, not final article sound acceptance.
"""
import argparse, copy, hashlib, importlib.util, json, os, shutil, sys
from pathlib import Path
import numpy as np

p=argparse.ArgumentParser()
p.add_argument('--tools',type=Path,required=True)
p.add_argument('--video-root',type=Path,required=True)
p.add_argument('--fixtures',type=Path,required=True)
p.add_argument('--output',type=Path,required=True)
a=p.parse_args();a.tools=a.tools.resolve();a.fixtures=a.fixtures.resolve();a.output=a.output.resolve()
root=a.video_root.resolve();W=root/'video';tts=root/'tts';cache=tts/'cache_tts'
assert os.environ.get('XG_NOPUSH')=='1'
assert not os.environ.get('STRICT_CACHE'),'Only this dedicated six-input prep subprocess is non-strict.'
assert cache.is_dir()and not cache.is_symlink()
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
arrsha=lambda x:hashlib.sha256(np.ascontiguousarray(x).tobytes()).hexdigest()
assert sha(a.tools/'make_video.py')=='23d886be9cf999eabc682159e1ab2fc2cf6c4ccb0597f32d60d5e90a34606c0e'
expected_models={'kokoro-v1.0.onnx':'7d5df8ecf7d4b1878015a32686053fd0eebe2bc377234608764cc0ef3636a6c5','kokoro-v1.0-timed.onnx':'beb0d1848dee9a49da392cc3df26958d46cfa35d321edf434f52949153f0df3a','voices-v1.0.bin':'bca610b8308e8d99f32e6fe4197e7ec01679264efed0cac9140fe9c29f1fbf7d'}
assert {n:sha(tts/n)for n in expected_models}==expected_models
voice_sha=sha(tts/'voice_mb.npy');assert voice_sha=='1f97658bb5a4280cc3f6c01dc644dff471bf57c970fc8b99f3049d6991c4f6c8'
assert (W/'make_video.py').resolve()==(a.tools/'make_video.py').resolve() or sha(W/'make_video.py')==sha(a.tools/'make_video.py')
private=root/'tts/spoken-comma-reference-cache';private.mkdir(exist_ok=True)
public_cache=a.tools.parent/'配音缓存'
def inventory(path):
 return {str(x.relative_to(path)):(x.stat().st_size,x.stat().st_mtime_ns)for x in path.rglob('*')if x.is_file()}if path.exists()else{}
old_cache=inventory(cache);public_before=inventory(public_cache)
scripts=W/'scripts';scripts.mkdir(exist_ok=True)
source_before={str(x):x.read_bytes()for x in scripts.glob('*.json')}
report={'kind':'actual-native-three-sentence-spoken-comma-model-and-display-timing-certification','diagnostic_only':True,'final_article_audio_accepted':False,'all_original_article_quality_gates_still_required':True,'source_ids_are_stable_source_numbers':[43,52],'six_model_input_scope_only':True,'models_SHA256':expected_models,'voice_SHA256':voice_sha,'cases':[],'passed':False}
allowed={};all_events=[];m=None
try:
 for no in (43,52):shutil.copyfile(a.fixtures/f'{no}.json',scripts/f'{no}.json')
 fixture_bytes={str(no):(a.fixtures/f'{no}.json').read_bytes()for no in (43,52)}
 assert {k:hashlib.sha256(v).hexdigest()for k,v in fixture_bytes.items()}=={'43':'62d2439a0e50ef62b713c003cb208c1c93e4914a590595999276f2c1504c65d7','52':'7ecc6cec4d6129253f1b255a8fc0090ef87dd365e41a824b2b93cdd17e0a18c2'}
 os.chdir(W);sys.path.insert(0,str(W));sys.path.insert(0,str(a.tools))
 spec=importlib.util.spec_from_file_location('real_native_spoken_comma_maker',a.tools/'make_video.py');m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m)
 m._REPO_CACHE=str(root/'do-not-export-spoken-comma-cache');assert not Path(m._REPO_CACHE).exists()
 sessions=[]
 for obj in (m.k,m.KT):
  found=[v for v in vars(obj).values()if hasattr(v,'get_session_options')];assert found
  for s in found:
   opts=s.get_session_options();assert opts.intra_op_num_threads==opts.inter_op_num_threads==1;sessions.append({'intra_op_num_threads':1,'inter_op_num_threads':1})
 report['actual_single_thread_sessions']=sessions
 voice_id=hashlib.sha1(np.ascontiguousarray(m.V).tobytes()).hexdigest()
 objects={'create':m.k,'create_timed':m.KT};cache_fns={}
 for method,obj in objects.items():
  outer=getattr(obj,method);closure=dict(zip(outer.__code__.co_freevars,(c.cell_contents for c in outer.__closure__)))
  assert 'fn'in closure and callable(closure['fn']);cache_fns[method]=closure['fn']
 # Plan all six real inner inputs with the actual native tokenizer; capture does
 # not synthesize. Inference can only occur later through guarded original fn.
 planned=[]
 for no,si in ((43,16),(52,4),(52,18)):
  data=json.loads(fixture_bytes[str(no)]);sid=f'S{si}';m._SPOKEN_SOURCE_NO=str(no)
  sent=' '.join(m.R.strip_gloss(c['en']).replace('**','').strip()for c in data['sentences'][si-1]['chunks'])
  rule=m._speech_comma_spec(data,sid);assert rule and m._speech_rule(sent)==rule
  assert rule['needs_mother_binding']is False and not data.get('区间声音指纹',{}).get(sid)
  assert [w.lower()for w in __import__('re').findall(r"[A-Za-z]+(?:['’][A-Za-z]+)?",sent)]==[w.lower()for w in __import__('re').findall(r"[A-Za-z]+(?:['’][A-Za-z]+)?",rule['projected'])]
  row={'source_id':no,'sentence':sid,'source_fixture_SHA256':hashlib.sha256(fixture_bytes[str(no)]).hexdigest(),'display_EN':sent,'actual_spoken_projection':rule['projected'],'removed_comma_ordinals':data['朗读删逗号'][sid]['逗号序号'],'model_inputs':[]}
  for method,kwargs in (('create',{}),('create_timed',{'clause_pause':0,'sentence_pause':0})):
   captured=[]
   def capture(text,voice,speed=1.,lang='en-us',**kw):captured.append((text,speed,lang,kw,hashlib.sha1(np.ascontiguousarray(voice).tobytes()).hexdigest()))
   m._pron(capture)(m.spoken(sent),voice=m.V,speed=m.SPEED,lang='en-us',**kwargs);assert len(captured)==1
   text,speed,lang,kw,vh=captured[0];assert vh==voice_id and lang=='en-us'and speed==m.SPEED
   mid=m._portable_mid(str(tts/('kokoro-v1.0.onnx'if method=='create'else'kokoro-v1.0-timed.onnx')))
   key=hashlib.sha1(repr((method,mid,text,vh,float(speed),lang,sorted(kw.items()))).encode()).hexdigest()+'.pkl'
   ident=(method,text,float(speed),lang,repr(sorted(kw.items())),vh);assert ident not in allowed;allowed[ident]=key
   row['model_inputs'].append({'method':method,'actual_input_text_SHA256':hashlib.sha256(text.encode()).hexdigest(),'actual_input_is_phonemes':bool(kw.get('is_phonemes')),'actual_kwargs':kw,'cache_key':key,'actual_mid':mid})
  assert row['model_inputs'][0]['actual_input_text_SHA256']==row['model_inputs'][1]['actual_input_text_SHA256']
  planned.append((data,si,sent,row))
 assert len(allowed)==6
 negatives=[]
 for data,si,sent,row in planned:
  sid=f'S{si}'
  mutations={'wrongword':lambda d:d['朗读删逗号'][sid].__setitem__('原文',sent.replace('he ','she ',1)if'he 'in sent else sent+' word'),'wrongsource':lambda d:d['朗读删逗号'][sid].__setitem__('篇号',40),'wrongcomma':lambda d:d['朗读删逗号'][sid].__setitem__('逗号序号',[999]),'extra_spoken_freeform':lambda d:d['朗读删逗号'][sid].__setitem__('spoken','arbitrary replacement')}
  for label,mutate in mutations.items():
   bad=copy.deepcopy(data);mutate(bad)
   try:m._speech_comma_spec(bad,sid)
   except SystemExit:negatives.append({'source_id':data['no'],'sentence':sid,'case':label,'rejected':True})
   else:raise AssertionError('Source schema negative control accepted '+label)
 report['actual_namespace_schema_negative_controls']=negatives
 # Guard before the real original _cached function: wrong text/voice/speed/
 # method/kwargs is rejected, even though this subprocess is non-strict.
 def guarded(method,fn):
  def call(text,voice,speed=1.,lang='en-us',**kw):
   vh=hashlib.sha1(np.ascontiguousarray(voice).tobytes()).hexdigest();ident=(method,text,float(speed),lang,repr(sorted(kw.items())),vh)
   if ident not in allowed:raise AssertionError('Unauthorized model input outside the exact six-input scope')
   all_events.append({'method':method,'cache_key':allowed[ident]})
   return fn(text,voice,speed=speed,lang=lang,**kw)
  return call
 for method,obj in objects.items():setattr(obj,method,m._pron(guarded(method,cache_fns[method])))
 bad_scope=[]
 for method in objects:
  try:guarded(method,cache_fns[method])('not an authorized source input',m.V,speed=m.SPEED)
  except AssertionError:bad_scope.append(method)
  else:raise AssertionError('The model-input negative control did not reject')
 report['wrong_model_input_negative_controls_rejected']=bad_scope
 # Actual raw/timed mothers are obtained now, not fabricated or copied under a
 # different header. Then strict-cache repeat proves exact cache reuse.
 prepared=[]
 for data,si,sent,row in planned:
  m._SPOKEN_SOURCE_NO=str(data['no']);row['phase']='actual_models';report['cases'].append(row)
  raw,raw_sr=m.k.create(m.spoken(sent),voice=m.V,speed=m.SPEED,lang='en-us')
  tb,timed_sr,toks=m.KT.create_timed(m.spoken(sent),voice=m.V,speed=m.SPEED,lang='en-us',clause_pause=0,sentence_pause=0);toks=list(toks)
  assert raw_sr==timed_sr==m.SR
  actual_ph=''.join(t.phoneme for t in toks)
  expected_ph=m.phonemes_of(m._synth_punct(m.spoken(sent)))
  assert actual_ph==expected_ph,'Actual timed tokens must equal actual projected source phonemes (L14)'
  marks=m._speech_marks(sent);pieces=[];gaps=[];p0=0;listed=m.list_commas(sent)
  for mark in marks:pieces.append((p0,mark.end()));p0=mark.end()+1;gaps.append(.2 if mark.start()in listed else .4)
  pieces.append((p0,len(sent)))
  assert sum(t.phoneme in ',;:'for t in toks)==len(marks)==len(pieces)-1
  assert len(marks)=={(43,16):1,(52,4):2,(52,18):0}[(int(data['no']),si)]
  row.update(raw_samples=len(raw),raw_float32_SHA256=arrsha(raw),timed_samples=len(tb),timed_array_SHA256=arrsha(tb),timed_tokens=len(toks),actual_phonemes_SHA256=hashlib.sha256(actual_ph.encode()).hexdigest(),L14_full_phonemes_exact=True,retained_display_char_pieces=pieces,gaps=gaps,actual_timed_punctuation_count=len(marks))
  # Preserve even a real original cutter failure as evidence; no old source
  # insert points or intervals can bypass it.
  for item in row['model_inputs']:
   path=cache/item['cache_key'];marker=Path(str(path)+'.单线程');assert path.is_file()and marker.is_file()
   m._条目核对(str(path));h=sha(path);assert marker.read_text().strip()==h[:16]
   item.update(cache_PKL_SHA256=h,cache_PKL_bytes=path.stat().st_size,single_thread_marker_SHA256=sha(marker),single_thread_marker_value=marker.read_text().strip(),existing_cache_hit_before_test=item['cache_key']in old_cache)
   for src in (path,marker):
    dst=private/src.name
    if dst.exists():assert sha(dst)==sha(src)
    else:shutil.copyfile(src,dst)
  row['phase']='actual_models_prepared';prepared.append((data,si,sent,row,raw,tb,toks,actual_ph,pieces,gaps,raw_sr))
 # All six mothers are safely prepared before any real cutter runs. A real
 # failed cut is retained per case and still fails certification; it cannot
 # prevent diagnosing the remaining two authorized sentences.
 for data,si,sent,row,raw,tb,toks,actual_ph,pieces,gaps,raw_sr in prepared:
  try:
   m._SPOKEN_SOURCE_NO=str(data['no']);row['phase']='actual_original_sentence_audio'
   os.environ['STRICT_CACHE']='1'
   clips,tmap=m.sentence_audio(sent,pieces,gaps);w=np.concatenate(clips)
   display_texts=[m.R.strip_gloss(c['en']).replace('**','').strip()for c in data['sentences'][si-1]['chunks']]
   chunk_ts=m.chunk_times(display_texts)
   assert len(chunk_ts)==len(display_texts)-1 and all(np.isfinite(chunk_ts))
   assert all(0<=x<=len(w)/m.SR for x in chunk_ts)and chunk_ts==sorted(chunk_ts)
   assert len(tmap)==len(pieces)and[(x[0],x[1])for x in tmap]==pieces
   assert len(m.LAST['cuts'])==len(marks)and m.LAST['gaps']==gaps
   assert m.LAST['total']==len(w)/m.SR
   raw_again,sr_again=m.k.create(m.spoken(sent),voice=m.V,speed=m.SPEED,lang='en-us');assert np.array_equal(raw,raw_again)and sr_again==raw_sr
   tb_again,_,tok_again=m.KT.create_timed(m.spoken(sent),voice=m.V,speed=m.SPEED,lang='en-us',clause_pause=0,sentence_pause=0);assert np.array_equal(tb,tb_again)and ''.join(t.phoneme for t in tok_again)==actual_ph
   row.update(phase='passed_actual_sentence_audio_and_display_chunk_mapping',processed_samples=len(w),processed_float32_SHA256=arrsha(w),actual_new_raw_fingerprint=m.SENT_FP[sent],actual_tmap=tmap,actual_chunk_times=chunk_ts,actual_cuts=m.LAST['cuts'],actual_fades=m.LAST['fades'],actual_timed_to_raw_scale=m.LAST['scale'],new_model_strict_cache_repeat_exact=True,display_chunk_EN_exact=True,no_inserted_pause_for_deleted_commas=True)
   os.environ.pop('STRICT_CACHE',None)
  except BaseException as case_exc:
   row['original_sentence_audio_error']={'type':type(case_exc).__name__,'detail':str(case_exc)}
   row['phase']='failed_actual_original_sentence_audio_or_display_mapping'
  finally:os.environ.pop('STRICT_CACHE',None)
 assert len(report['cases'])==3
 if any('original_sentence_audio_error'in r for r in report['cases']):raise AssertionError('At least one actual original sentence cutter/display-mapping check failed; see exact per-case errors. No quality gate bypassed.')
 report['passed']=True
except BaseException as exc:
 report['error']={'type':type(exc).__name__,'detail':str(exc)}
 raise
finally:
 os.environ.pop('STRICT_CACHE',None)
 for x in scripts.glob('*.json'):
  if str(x)not in source_before:x.unlink()
 for name,raw in source_before.items():Path(name).write_bytes(raw)
 assert {str(x):x.read_bytes()for x in scripts.glob('*.json')}==source_before
 after=inventory(cache);changed_existing=[k for k,v in old_cache.items()if after.get(k)!=v]
 new_keys=sorted(set(after)-set(old_cache));allowed_names=set(allowed.values())|{x+'.单线程'for x in allowed.values()}
 report.update(actual_model_calls=all_events,model_input_distinct_keys=sorted(set(e['cache_key']for e in all_events)),new_cache_files=new_keys,existing_cache_entries_stat_unchanged=not changed_existing,unrelated_new_cache_files=sorted(set(new_keys)-allowed_names),public_repository_cache_stat_unchanged=inventory(public_cache)==public_before,working_source_bytes_restored=True,private_cache_folder=str(private),private_PCM_exported=False)
 assert not changed_existing and not report['unrelated_new_cache_files']and report['public_repository_cache_stat_unchanged']
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({'passed':report['passed'],'case_phases':[(x['source_id'],x['sentence'],x['phase'])for x in report['cases']],'new_cache_files':len(new_keys),'output':str(a.output)},ensure_ascii=False))
