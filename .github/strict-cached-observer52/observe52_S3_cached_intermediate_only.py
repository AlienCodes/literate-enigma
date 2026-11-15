#!/usr/bin/env python3
"""One original cached source52 S3 only; scalar evidence, no whole or acceptance."""
import argparse, ast, copy, hashlib, importlib.metadata, io, json, os, platform, re, sys, tempfile
from pathlib import Path
import numpy as np
import soundfile as sf

MAKER='23d886be9cf999eabc682159e1ab2fc2cf6c4ccb0597f32d60d5e90a34606c0e'
SOURCE='2e494dd76be71f2661f5935b26911b1b94f677627b4b990a3c0376a865030686'
BASE='55594624daca4a4601146e4cb1822e813782e14e1cdc0a5e65774e8602045822'
FIRST='5c4a2e62624ade5d119086c9525a8d90588efc7507fdbdd04678219dd8f4a156'
CONTRACT='9d133939b08a08b78cb6810028708618b92a2f2449cf56a67bd9b82506887b79'
SENT='Londoners were accustomed to murky, dreary winters.'
BEFORE='7596f3cb080ddb1ad7bc7f4b4e6b88b11bb524eb8620669dbac12ee229a21394'
H555='4871c0a4b3920e82a0d7d6bc7eaa5386349088319251ada49bbd6b0f012a0269'
H5C4='8e56f34c5476c294526d989caa0e7901a36dcfb409de7a22adf36e6981e227c1'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb')as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
def ah(x):return hashlib.sha256(np.ascontiguousarray(x).tobytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def sig(x):return {'samples':len(x),'dtype':str(x.dtype),'native_bytes_SHA256':ah(x),'as_float32_SHA256':ah(np.asarray(x,np.float32)),'as_float64_SHA256':ah(np.asarray(x,np.float64)),'finite':bool(np.isfinite(x).all())}
def safe(x):
 if isinstance(x,dict):return {str(k):safe(v)for k,v in x.items()}
 if isinstance(x,(list,tuple)):return [safe(v)for v in x]
 if isinstance(x,np.generic):return x.item()
 return x
def bare(d):return [d['title_en']]+[' '.join(re.sub(r'\*\*|\{\{.*?\}\}','',c['en']).strip()for c in s['chunks'])for s in d['sentences']]
def dump(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(safe(d),ensure_ascii=False,indent=2)+'\n')
def exact_key(ns,clips,tmap,gaps,no):
 tree=ast.parse(Path(ns['__file__']).read_text());fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='_auto_level')
 expr=next(n.value for n in fn.body if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='_k'for t in n.targets))
 return eval(compile(ast.Expression(expr),'original-G36-key-expression-only','eval'),ns,dict(clips=clips,tmap=tmap,gaps=gaps,no=no))
def main():
 ap=argparse.ArgumentParser(description=__doc__)
 for k in ['tools','video-root','source','baseline-report','first-whole-report','mother-contract','output']:ap.add_argument('--'+k,type=Path,required=True)
 a=ap.parse_args();T=a.tools.resolve();M=a.video_root.resolve();O=a.output.resolve()
 report={'kind':'source52-S3-only-original-cache-intermediate-hard-refusal-diagnostic','diagnostic_only':True,'formal_audio_or_video_accepted':False,'production_delivery_eligible':False,'whole_build_count':0,'new_model_inference':False,'new_math_or_cache':False,'source_or_CF_or_controls_written':False,'observation_completed':False,'program_SHA256':sha(__file__),'historical_hard_hashes_not_replaced':{'actual555':H555,'actual5c4a':H5C4},'private_PCM_PKL_GT_or_media_exported':False}
 inputs={T/'make_video.py':MAKER,a.source:SOURCE,a.baseline_report:BASE,a.first_whole_report:FIRST,a.mother_contract:CONTRACT}
 for p,h in inputs.items():assert sha(p)==h, str(p)+' immutable pin mismatch'
 d=read(a.source);base=read(a.baseline_report);first=read(a.first_whole_report);contract=read(a.mother_contract)
 assert str(d['no'])=='52'and len(d['sentences'])==18 and bare(d)[3]==SENT
 expect=base['cases'][-1]['sentence_records']['S3'];firstrow=next(c for c in first['cases']if c['source_id']==52)['candidate']['sentence_pre_master_records']['S3']
 assert expect['before_gain_float32_sha256']==firstrow['before_gain_float32_SHA256']==BEFORE
 assert expect['pre_master_float32_sha256']==H555 and firstrow['pre_master_float32_SHA256']==H5C4
 assert os.environ.get('STRICT_CACHE')=='1'and os.environ.get('XG_NOPUSH')=='1'
 assert not any(os.environ.get(k)for k in ['VOICE','AFFILE','OLD_IV_VOID'])
 cache=M/'tts/cache_tts';assert cache.is_dir();before={p.name:(p.stat().st_size,p.stat().st_mtime_ns)for p in cache.iterdir()if p.is_file()}
 models={k:sha(M/'tts'/k)for k in contract['models']};assert models==contract['models']
 report['input_pins']={str(p):h for p,h in inputs.items()};report['actual_runtime']={'python':sys.version,'platform':platform.platform(),'numpy':np.__version__,'soundfile':sf.__version__,'environment':{k:os.environ.get(k)for k in ['STRICT_CACHE','XG_NOPUSH','GAIN','ENDING','CUTS','XF_OUT','XF_IN','SPEED','OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NPY_DISABLE_CPU_FEATURES']}}
 for pkg in ['onnxruntime','kokoro-onnx','scipy']:
  try:report['actual_runtime'][pkg]=importlib.metadata.version(pkg)
  except importlib.metadata.PackageNotFoundError:report['actual_runtime'][pkg]=None
 oldcwd=Path.cwd();oldpath=list(sys.path);keys=['AUDIO_ONLY','TMPDIR','CACHE_LOG'];oldenv={k:os.environ.get(k)for k in keys};ns=None;failure=None
 try:
  with tempfile.TemporaryDirectory(prefix='source52-S3-local-',dir=M)as td:
   PR=Path(td);W=PR/'video';(W/'scripts').mkdir(parents=True);(PR/'tts').symlink_to(M/'tts',target_is_directory=True)
   src=W/'scripts/52.json';src.write_bytes(a.source.read_bytes());assert sha(src)==SOURCE
   os.environ['AUDIO_ONLY']='1';os.environ['TMPDIR']=str(PR/'tmp');Path(os.environ['TMPDIR']).mkdir();tempfile.tempdir=None
   log=PR/'cache-keys.txt';os.environ['CACHE_LOG']=str(log)
   try:
    os.chdir(W);sys.path[:0]=[str(T),str(W)]
    text=(T/'make_video.py').read_text().split('if __name__')[0]
    h1='    w=clean_tail(raw)\n';h2="    XF_OUT=float(os.environ.get('XF_OUT','0.06'))"
    assert text.count(h1)==text.count(h2)==1
    text=text.replace(h1,h1+'    _READONLY_RAW.append(raw.copy())\n    _READONLY_PRISTINE.append(w.copy())\n',1).replace(h2,'    _READONLY_PRE_FADE.append(w.copy())\n'+h2,1)
    ns={'__name__':'source52_single_final_private','__file__':str(T/'make_video.py'),'_READONLY_RAW':[],'_READONLY_PRISTINE':[],'_READONLY_PRE_FADE':[]}
    exec(compile(text,str(T/'make_video.py')+'#readonly-S3-copy-hooks','exec'),ns)
    ns['_SPOKEN_SOURCE_NO']='52';assert ns['SENT_NO'].get(SENT)=='52'
    report['original_context']={'source_no':ns['SENT_NO'].get(SENT),'spoken_source_no':ns['_SPOKEN_SOURCE_NO'],'short_start':ns['_短起']('52'),'SR':ns['SR'],'AUD_DB':ns['AUD_DB'],'SPEED':ns['SPEED'],'raw_fingerprint_before':ns.get('SENT_FP',{}).get(SENT),'source_installed_before_import_SHA256':sha(src),'dictionary_files':{k:{'basename':Path(ns[k]).name,'SHA256':sha(ns[k])}for k in ['_PRON_PATH','_CTX_PATH','_OLDF']if ns.get(k)and Path(ns[k]).is_file()},'PRON_WORDS_canonical_SHA256':hashlib.sha256(json.dumps(ns['PRON_WORDS'],sort_keys=True,ensure_ascii=False).encode()).hexdigest()}
    report['original_context']['actual_imported_module_files']={k:{'basename':Path(sys.modules[k].__file__).name,'SHA256':sha(sys.modules[k].__file__)}for k in ['clean','render','title2','kokoro_onnx']if k in sys.modules and getattr(sys.modules[k],'__file__',None)}
    calls=[]
    for obj,name in [(ns['k'],'create'),(ns['KT'],'create_timed')]:
     original=getattr(obj,name)
     def guarded(*ar,_fn=original,_name=name,**kw):
      assert os.environ.get('STRICT_CACHE')=='1';n=len(log.read_text().splitlines())if log.exists()else 0
      value=_fn(*ar,**kw);names=log.read_text().splitlines()[n:]
      assert names and all((cache/q).is_file()for q in names)
      calls.append({'method':_name,'input_text_SHA256':hashlib.sha256(ar[0].encode()).hexdigest(),'speed':kw.get('speed'),'cache_files':[{'filename':q,'full_SHA256':sha(cache/q),'marker_SHA256':sha(cache/(q+'.单线程'))if(cache/(q+'.单线程')).exists()else None}for q in names]})
      return value
     setattr(obj,name,guarded)
    orig_level=ns['_auto_level'];levels=[]
    def level(clips,tmap,gaps,no='',rounds=2):
     assert str(no)=='52'and rounds==2 and os.environ.get('STRICT_CACHE')=='1'
     name='调平_'+exact_key(ns,clips,tmap,gaps,no)+'.json';p=cache/name;assert p.is_file(),'Original S3 stored G36 missing; math forbidden'
     result=orig_level(clips,tmap,gaps,no,rounds);levels.append({'filename':name,'full_SHA256':sha(p),'stored_value':read(p),'original_return':result,'clips':[sig(z)for z in clips],'tmap':copy.deepcopy(tmap),'gaps':list(gaps)})
     return result
    ns['_auto_level']=level;tail0=ns['_收句尾'];tail=[]
    def trace_tail(z):
     before_sig=sig(z);out=tail0(z);tail.append({'input':before_sig,'output':sig(out),'changed_sample_count':int(np.count_nonzero(z!=out))});return out
    ns['_收句尾']=trace_tail
    pieces=[];gaps=[];p0=0;listed=ns['list_commas'](SENT)
    for mark in ns['_speech_marks'](SENT):pieces.append((p0,mark.end()));p0=mark.end()+1;gaps.append(ns['P_LIST']if mark.start()in listed else ns['P_COMMA'])
    pieces.append((p0,len(SENT)))
    clips,tmap=ns['sentence_audio'](SENT,pieces,gaps);pre=np.concatenate(clips)
    report['S3_before_gain']={'array':sig(pre),'clips':[sig(z)for z in clips],'tmap':copy.deepcopy(tmap),'cuts':copy.deepcopy(ns['LAST']['cuts']),'gaps':gaps,'pieces':pieces,'raw_fingerprint':ns['SENT_FP'][SENT],'raw':sig(ns['_READONLY_RAW'][0]),'pristine':sig(ns['_READONLY_PRISTINE'][0]),'pre_fade':sig(ns['_READONLY_PRE_FADE'][0])}
    report['actual_model_calls']=calls;dump(O,report)
    assert ah(pre)==BEFORE and len(pre)==79080 and ns['SENT_FP'][SENT]=='fbb395bf4698','S3 original before-gain changed; no gain comparison allowed'
    assert [ah(z)for z in clips]==[z['sha256']for z in expect['before_gain_clips']]
    ans=ns['句增益'](d,'52',2,SENT,pieces,gaps,clips,tmap,pre);post=ans[1]
    report['S3_after_gain']={'array':sig(post),'automatic_level':ans[2],'manual_level':ans[3],'clips':[sig(z)for z in ans[0]],'actual_G36':levels,'original_tail_operations':tail,'automatic_float32_factors':{str(k):{'dB':float(v),'factor':float(np.float32(10**(v/20))),'factor_float32_bytes_SHA256':ah(np.asarray([np.float32(10**(v/20))]))}for k,v in ans[2].items()}}
    normalized=post/np.float32(base['cases'][-1]['master_pre_peak'])*0.89
    buf=io.BytesIO();sf.write(buf,normalized,24000,format='WAV',subtype='PCM_16');buf.seek(0);decoded,_=sf.read(buf,dtype='float64')
    qexp=base['cases'][-1]['old_to_current_actual_sentence_PCM_identity']['S3']['new_quantized_float64_sha256']
    report['original_master_quantization_S3_only']={'operation':'post / np.float32(actual_master_pre_peak) * 0.89; soundfile WAV PCM16; float64 decode','decoded_float64_SHA256':ah(decoded),'expected_actual555_quantized_float64_SHA256':qexp,'exact_actual555_quantized_S3':ah(decoded)==qexp,'no_whole_file_or_AAC_generated':True}
    report['hard_comparisons']={'before_gain_exact':ah(pre)==BEFORE,'samples_exact':len(post)==expect['samples']==79080,'post_native_bytes_matches_actual555':ah(post)==H555,'post_native_bytes_matches_actual5c4a':ah(post)==H5C4,'no_hash_expectation_replaced':True}
    report['observation_completed']=True;dump(O,report)
    assert report['hard_comparisons']['post_native_bytes_matches_actual555'],'S3 actual555 hard hash still differs; actual metadata saved, no whole retry authorized'
   finally:
    os.chdir(oldcwd);sys.path[:]=oldpath
    for k,v in oldenv.items():
     if v is None:os.environ.pop(k,None)
     else:os.environ[k]=v
    tempfile.tempdir=None
 except BaseException as e:failure=e;report['error']={'type':type(e).__name__,'detail':str(e)}
 finally:
  report['all_existing_private_cache_stats_and_keys_unchanged']={p.name:(p.stat().st_size,p.stat().st_mtime_ns)for p in cache.iterdir()if p.is_file()}==before
  report['all_models_byte_exact_after']={k:sha(M/'tts'/k)for k in models}==models
  report['all_input_pins_byte_exact_after']=all(sha(p)==h for p,h in inputs.items());dump(O,report)
  assert report['all_existing_private_cache_stats_and_keys_unchanged']and report['all_models_byte_exact_after']and report['all_input_pins_byte_exact_after']
 if failure:raise failure
 return 0
if __name__=='__main__':raise SystemExit(main())
