"""Read-only original historical G36 functions on unchanged actual source.

The two historical source functions are read directly from an actual git commit.
No new math, inference, parameter change, cache writes, or acceptance assertion.
"""
from pathlib import Path
import ast,json,hashlib,importlib.util,tempfile,subprocess
import numpy as np,soundfile as sf
B=Path(__file__).parent
spec=importlib.util.spec_from_file_location('original_replay',B/'replay_original_sources.py');r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
REV='e6327aff';code=subprocess.check_output(['git','cat-file','blob',REV+':视频/工具/make_video.py'],cwd=r.m.RPO).decode();tree=ast.parse(code);funcs=[x for x in tree.body if isinstance(x,ast.FunctionDef)and x.name in ['_auto_level','句增益']];assert len(funcs)==2
original_scope=r.scope;levelrows={}
def scope(d,si,cache):
 ns,text=original_scope(d,si,cache)
 exec(compile(ast.Module(body=funcs,type_ignores=[]),'actual-historical-'+REV+'-G36-original-functions','exec'),ns)
 fn=ns['_auto_level']
 def read_level(clips,tmap,gaps,no='',rounds=2):
  import 响度一致性核对 as LQ
  if not any(g>=LQ.IN_GAP for g in gaps):return fn(clips,tmap,gaps,no,rounds)
  key=hashlib.sha1(b''.join(np.ascontiguousarray(c,np.float32).tobytes()for c in clips)+repr((str(no),list(gaps),[(round(t[2],4),round(t[3],4))for t in tmap])).encode()).hexdigest();name='调平_'+key+'.json';p=cache/name
  if not p.exists():
   raw=r.m.git('视频/配音缓存/'+name);p.write_bytes(raw);levelrows[name]={'stored_file_full_SHA256':r.sha(raw),'stored_value':json.loads(raw),'original_repository_pin':r.m.PIN}
  return fn(clips,tmap,gaps,no,rounds)
 ns['_auto_level']=read_level
 return ns,text
r.scope=scope
for no in ['69','65']:
 p=B/no/f'{no}-failed-working-source.json';d=json.loads(p.read_text());st=json.loads((B/no/f'{no}-status.json').read_text());report={'kind':f'{no}-two-real-historical-G36-functions-on-unchanged-current-source','quality_acceptance':False,'historical_commit_prefix':REV,'historical_make_file_full_SHA256':r.sha(code.encode()),'historical_function_AST_SHA256':r.sha(ast.dump(ast.Module(body=funcs,type_ignores=[]),include_attributes=False).encode()),'unchanged_actual_source_full_SHA256':r.sha(p.read_bytes()),'original_current_maker_full_SHA256':r.sha(r.m.source.encode()),'only_namespace_functions_from_exact_historical_code':['_auto_level','句增益'],'no_source_controls_or_thresholds_or_production_programs_modified':True,'no_TTS_or_level_math_recalculation':True}
 try:
  with tempfile.TemporaryDirectory(prefix='private-historical-G36-'+no+'-',dir='/dev/shm')as td:
   td=Path(td);cache=td/'cache';cache.mkdir();x,parts=r.build(d,cache);wav=td/'a.wav';mp4=td/'voice.m4a';sf.write(wav,x,24000)
   subprocess.run([r.FF,'-y','-loglevel','error','-i',str(wav),'-af',r.AF,'-c:a','aac','-b:a','256k','-movflags','+faststart',str(mp4)],check=True);aa=r.sha(subprocess.check_output(['ffmpeg','-v','error','-i',str(mp4),'-map','0:a:0','-c:a','copy','-f','adts','-']))
   report.update({'private_original_functions_WAV_SHA256':r.sha(wav.read_bytes()),'private_original_functions_AAC_ADTS_SHA256':aa,'real_accepted_AAC_ADTS_SHA256':st['accepted_source']['aac_adts_sha256'],'matches_real_accepted_AAC':aa==st['accepted_source']['aac_adts_sha256'],'parts':parts})
 except BaseException as e:
  report['error']={'type':type(e).__name__,'detail':str(e)}
 report['stored_original_level_cache_scalar_provenance']=levelrows.copy();report['all_G72_original_mother_scalar_provenance']=list(r.m.cache_rows.values());report['private_audio_deleted']=True
 out=B/no/f'{no}-historical-G36-exact-AAC-probe.json';out.write_text(json.dumps(report,ensure_ascii=False,indent=2,default=lambda x:float(x))+'\n');print(no,'oldacceptedAAC?',report.get('matches_real_accepted_AAC'),'error',report.get('error'),flush=True)
