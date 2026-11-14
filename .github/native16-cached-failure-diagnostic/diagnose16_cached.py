#!/usr/bin/env python3
"""Exact cached diagnosis only. No acceptance, inference, source/CF/core changes."""
import argparse, ast, hashlib, importlib.util, json, os, re, shutil, subprocess, sys, tempfile, traceback
from pathlib import Path
import numpy as np
import soundfile as sf
SR=24000
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def js(p):return json.loads(Path(p).read_text())
def dump(p,d):Path(p).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def call(cmd,cwd,env,log):
 q=subprocess.run(list(map(str,cmd)),cwd=cwd,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
 Path(log).write_text(q.stdout)
 if q.returncode:raise RuntimeError('Original command failed: '+Path(str(cmd[1])).name+'; exit='+str(q.returncode)+'; see '+Path(log).name)
 return q.stdout

def worker(work,output):
 os.chdir(work);sys.path.insert(0,str(work));sys.argv=[str(work/'make_video.py'),'scripts/16.json','unused.m4a']
 sp=importlib.util.spec_from_file_location('exact_original_maker16',work/'make_video.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)
 d=js(work/'scripts/16.json');s=d['sentences'][14];texts=[re.sub(r'\*\*','',m.R.strip_gloss(c['en'])).strip()for c in s['chunks']];sent=' '.join(texts)
 ps=[];gaps=[];p0=0;lst=m.list_commas(sent)
 for mt in re.finditer(r'[,;:](?=\s)',sent):ps.append((p0,mt.end()));p0=mt.end()+1;gaps.append(.2 if mt.start()in lst else .4)
 ps.append((p0,len(sent)));clips,tmap=m.sentence_audio(sent,ps,gaps);L=m.LAST.copy();raw,_=m.k.create(m.spoken(sent),voice=m.V,speed=m.SPEED,lang='en-us');tb,_,toks=m.KT.create_timed(m.spoken(sent),voice=m.V,speed=m.SPEED,lang='en-us',clause_pause=0,sentence_pause=0)
 A,sr=sf.read(work/'work_16/a.wav');assert sr==SR
 seg=js(work/'work_16/分段.json')['S15'];start=seg[0]['时刻'][0]
 def mp(t):
  p=int(round(float(t)*L['scale']*SR))-L['head']
  for a,b,t0,rm in L['segs']:
   if p<a:return start+t0
   if p<b:
    q=p-a;q-=sum(min(q,y)-x for x,y in rm if x<q);return start+t0+q/SR
  return start+L['total']
 rows=[]
 for t in toks:
  a,b=mp(t.start),mp(t.end)
  if b>=111.85 and a<=112.9:rows.append({'phoneme':t.phoneme,'timed_start_s':float(t.start),'timed_end_s':float(t.end),'mapped_actual_start_s':a,'mapped_actual_end_s':b})
 src=(Path(os.environ['XG_TOOLS'])/'纯人声核对.py').read_text();ns={'np':np,'SR':SR,'F':120};tr=ast.parse(src);names={'per','spec','segments','scan','实测','像吸气','贴词头','爆破起','贴词尾擦音','确认可收'};exec(compile(ast.Module(body=[n for n in tr.body if isinstance(n,ast.FunctionDef)and n.name in names],type_ignores=[]),'original_PV_pure_functions','exec'),ns)
 findings=ns['scan'](A);target=[f for f in findings if 112.50<=f[1]<=112.60];assert len(target)==1
 f=target[0];samples=[]
 for t in np.arange(111.94,112.901,.0025):
  i=round(float(t)*SR);x=np.asarray(A[i:i+60],float);c,lf=ns['spec'](x)
  samples.append({'start_s':round(float(t),6),'rms_dBFS':float(20*np.log10(np.sqrt(np.mean(x*x))+1e-15)),'centroid_Hz':c,'LF150_dB':lf,'periodicity':ns['per'](A[max(0,i-210):i+270])})
 hl=(Path(os.environ['XG_TOOLS'])/'高亮同步核对.py').read_text();hn={'np':np};ht=ast.parse(hl);exec(compile(ast.Module(body=[n for n in ht.body if isinstance(n,ast.FunctionDef)and n.name in {'是开口','确认可收'}],type_ignores=[]),'original_HL_onset_functions','exec'),hn)
 onset=[{'time_s':round(float(t),6),'original_raw_onset_predicate':bool(hn['是开口'](A,SR,float(t)))}for t in np.arange(111.93,112.051,.001)]
 dump(output,{'kind':'actual-current-S15-original-cached-token-wave-scalar-only','quality_acceptance':False,'maker_sha256':sha(work/'make_video.py'),'wav_sha256':sha(work/'work_16/a.wav'),'source_sha256':sha(work/'scripts/16.json'),'sentence':sent,'original_LAST_scalar':{k:L[k]for k in ['scale','head','segs','total','cuts','gaps','hs']},'actual_producer_segments':seg,'actual_original_PV_target':list(f),'actual_original_PV_measured':ns['实测'](f),'actual_original_PV_looks_like_breath':ns['像吸气'](f),'token_mapped_times_are_timed_model_diagnostic_not_human_hearing':True,'timed_model_neighbor_phonemes':rows,'actual_PCM_2p5ms_spectrum_rows':samples,'original_5ms_onset_predicate':onset,'actual_whole_finite':bool(np.isfinite(A).all()),'actual_whole_peak':float(np.abs(A).max()),'private_arrays_exported':False})

def main(a):
 repo=a.repo.resolve();T=repo/'视频/工具';W=a.video_root.resolve()/'video';task=a.task.resolve();P=js(a.profile);O=a.output.resolve();O.mkdir(parents=True,exist_ok=True)
 report={'kind':'source16-exact-original-cached-scalar-diagnostic','quality_acceptance':False,'production_delivery_eligible':False,'source_GEN_CF_core_or_original_cache_mutated':False,'TTS_inference':False,'private_raw_GT_cache_or_model_exported':False,'program_sha256':sha(__file__),'profile_sha256':sha(a.profile)}
 try:
  assert os.environ.get('STRICT_CACHE')=='1';assert sha(W/'make_video.py')==P['maker_sha256'];assert sha(T/'独立复核/synth.py')==P['synth_sha256']
  assert sha(a.current_source)==P['current_source_sha256'];oldsrc=task/'accepted-pcm-source-reference/16.json';assert sha(oldsrc)==P['old_source_sha256']
  oldproof=js(task/'accepted-pcm-source-reference/16-proof.json');assert oldproof['internal_pcm_sha256']==P['old_pcm_sha256']
  states={name:{'present':(W/name).is_file(),'sha256':sha(W/name)if(W/name).is_file()else None}for name in oldproof['pronunciation_inputs']}
  report['actual_restored_W_dictionary_states']=states
  report['old177_assertion_reproduction']=[{'name':name,'historical_source_SHA_valid':sha(task/'accepted-pcm-source-reference'/it['file'])==it['sha256'],'original_target_is_file':states[name]['present'],'original_assertion_would_pass':states[name]['present']and sha(task/'accepted-pcm-source-reference'/it['file'])==it['sha256']}for name,it in oldproof['pronunciation_inputs'].items()]
  contract=js(task/'native16-Origin-cache-contract.json');privatecache=a.video_root.resolve()/'tts/cache_tts';pinrows=contract['origin_mother_cache']['exact_four_file_restore_verification'];cpins={Path(x['path_below_runner_temp']).name:x['expected_file_SHA256']for x in pinrows};assert{n:sha(privatecache/n)for n in cpins}==cpins
  cache_before={x.name:(x.stat().st_size,x.stat().st_mtime_ns)for x in privatecache.iterdir()if x.is_file()};roles={}
  with tempfile.TemporaryDirectory(prefix='private16-diagnosis-',dir=a.video_root.resolve().parent)as td:
   base=Path(td)
   for role,src in [('old',oldsrc),('current',a.current_source)]:
    rb=base/role;vw=rb/'video';vw.mkdir(parents=True);(rb/'tts').symlink_to(a.video_root.resolve()/'tts',target_is_directory=True)
    call([sys.executable,T/'出片指纹.py','--拷',vw],repo,os.environ,O/(role+'-original-module-copy.log'))
    assert sha(vw/'make_video.py')==P['maker_sha256'];(vw/'scripts').mkdir();shutil.copyfile(src,vw/'scripts/16.json')
    if(W/'fonts').exists():(vw/'fonts').symlink_to((W/'fonts').resolve(),target_is_directory=True)
    for name,item in oldproof['pronunciation_inputs'].items():
     if role=='old':
      q=task/'accepted-pcm-source-reference'/item['file'];assert sha(q)==item['sha256'];shutil.copyfile(q,vw/name)
     elif(W/name).is_file():shutil.copyfile(W/name,vw/name)
    env={**os.environ,'STRICT_CACHE':'1','AUDIO_ONLY':'1','VIDEO_ROOT':str(rb),'XG_WORK':str(vw),'XG_TOOLS':str(T),'XG_P':str(repo),'QC_DIR':str(rb/'qc_independent')};env.pop('OLD_IV_VOID',None)
    call([sys.executable,vw/'make_video.py',vw/'scripts/16.json',vw/'voice.m4a'],vw,env,O/(role+'-original-cached-maker.log'))
    wav=vw/'work_16/a.wav';wh=sha(wav);fp=hashlib.md5(wav.read_bytes()).hexdigest()[:12];expected=P[role+'_pcm_sha256'];assert wh==expected,(role,'whole PCM mismatch',wh)
    aa=hashlib.sha256(subprocess.check_output(['ffmpeg','-v','error','-nostdin','-i',str(vw/'voice.m4a'),'-map','0:a:0','-c:a','copy','-f','adts','-'])).hexdigest();assert aa==P[role+'_aac_sha256'],(role,'whole AAC mismatch',aa)
    call([sys.executable,T/'独立复核/synth.py','16'],vw,env,O/(role+'-original-cached-GT.log'))
    meta=js(rb/'qc_independent/gt/16_meta.json');gts={int(x['idx']):Path(x['file'])for x in meta}
    roles[role]={'root':rb,'work':vw,'wav':wav,'gts':gts};report[role+'_whole_identity']={'PCM_SHA256':wh,'PCM_MD5_first12':fp,'AAC_SHA256':aa,'source_SHA256':sha(src),'all_expected_exact':True}
    if role=='current':
     assert {str(i):sha(p)for i,p in gts.items()}==P['current_native_GT_SHA256_by_index']
     call([sys.executable,Path(__file__).resolve(),'--worker',vw,'--worker-output',O/'16-current-S15-scalar.json'],vw,env,O/'current-S15-scalar.log')
     # The genuine failed native checker already measured both DTW methods.
     # Preserve that actual result; this probe performs no new chunk inference.
     report['actual_failed_native_S15_HL']=P['actual_failed_native_S15_HL']
   old,new=roles['old'],roles['current'];oa,sr=sf.read(old['wav'],dtype='int16');na,_=sf.read(new['wav'],dtype='int16');assert sr==SR
   osgs=js(old['work']/'work_16/分段.json');nsgs=js(new['work']/'work_16/分段.json');rows=[]
   for v in P['seven_existing_typed_edits']:
    s=v['sentence'];idx=int(s[1:])-1;u=np.load(old['gts'][idx]);v2=np.load(new['gts'][idx]);a0,b0=v['raw_seconds'];lo=round((a0-.015)*SR);hi=round((b0+.015)*SR);same=np.array_equal(u[lo:hi],v2[lo:hi]);assert same
    ost,oend=osgs[s][0]['时刻'][0],osgs[s][-1]['时刻'][1];nst,nend=nsgs[s][0]['时刻'][0],nsgs[s][-1]['时刻'][1];op=oa[round(ost*SR):round(oend*SR)];np_=na[round(nst*SR):round(nend*SR)];whole=np.array_equal(op,np_);assert whole
    rows.append({**v,'expanded_raw_GT_context_s':[lo/SR,hi/SR],'old_GT_SHA256':sha(old['gts'][idx]),'current_GT_SHA256':sha(new['gts'][idx]),'expanded_transformed_GT_float32_exact':same,'context_float32_SHA256':hashlib.sha256(u[lo:hi].tobytes()).hexdigest(),'whole_corresponding_sentence_PCM16_exact':whole,'whole_sentence_PCM16_SHA256':hashlib.sha256(op.tobytes()).hexdigest(),'old_sentence_s':[ost,oend],'new_sentence_s':[nst,nend],'basis_not_modified':True})
   report['seven_existing_typed_local_continuity']=rows
  assert{n:sha(privatecache/n)for n in cpins}==cpins
  cache_after={x.name:(x.stat().st_size,x.stat().st_mtime_ns)for x in privatecache.iterdir()if x.is_file()};report['cache_added_names']=sorted(set(cache_after)-set(cache_before));report['cache_removed_names']=sorted(set(cache_before)-set(cache_after));report['cache_changed_stat_names']=[n for n in cache_before.keys()&cache_after.keys()if cache_before[n]!=cache_after[n]];assert cache_before==cache_after
  assert {name:{'present':(W/name).is_file(),'sha256':sha(W/name)if(W/name).is_file()else None}for name in states}==states
  assert sha(a.current_source)==P['current_source_sha256'];report['diagnostic_completed']=True
 except BaseException as e:
  report['diagnostic_completed']=False;report['error']={'type':type(e).__name__,'message':str(e),'traceback':traceback.format_exc()}
 finally:
  report['temporary_raw_audio_and_GT_removed']=True;dump(O/'16-exact-cached-diagnostic.json',report)
 if not report['diagnostic_completed']:raise SystemExit(1)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--worker',type=Path);p.add_argument('--worker-output',type=Path)
 for n in ['video-root','repo','task','current-source','profile','output']:p.add_argument('--'+n,type=Path)
 a=p.parse_args();worker(a.worker,a.worker_output)if a.worker else main(a)
