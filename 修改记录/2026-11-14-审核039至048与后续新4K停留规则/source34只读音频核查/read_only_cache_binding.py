"""Read-only original cache reconstitution; no TTS inference or production changes."""
from pathlib import Path
import hashlib,json,subprocess,tempfile,io,contextlib,ast
import numpy as np,soundfile as sf
BASE=Path('/workspace/work/video-audit70-20261113')
OUT=Path('/workspace/work/tetris34-audio-user-review-20261114')
probe=BASE/'audio-a21-actual-first-4K-20261114/probe_minimal_encoded_boost.py'
ns={'__name__':'tetris34_readonly_definitions','__file__':str(probe)}
exec(compile(probe.read_text().split('\nfor no in sys.argv')[0],str(probe)+'#definitions-only','exec'),ns)
r=ns['r']
sp=Path('/workspace/work/video-revision-delivery/next-passed-validated/43533004625/34/final-source/视频/脚本/34.json')
data=json.loads(sp.read_text());assert data['no']=='34'
expected_pcm='460d6113f34677d349884ddb0e80b68ff4bd6f16efce5feb0e998e7eab9659d4'
expected_aac='5649e6746d919510ba830daa5509ab68814dc1afe4d3578cf9c246dfb2c4a0e6'
sha=lambda b:hashlib.sha256(b).hexdigest()
report={'kind':'strict-original-cache-only-producer-binding-for-readonly-audio-diagnosis','source_file':str(sp),'source_sha256':sha(sp.read_bytes()),'expected_accepted_PCM_sha256':expected_pcm,'expected_accepted_AAC_sha256':expected_aac,'new_TTS_inference':False,'source_or_approved_media_modified':False,'private_pcm_or_cache_exported':False}
try:
 assert sha(r.m.source.encode())=='4c85e1fbdd2e82c5646d5f58df63c85eca60af4ef521f1d36f765575a568d6f3'
 with tempfile.TemporaryDirectory(prefix='private34-readonly-binding-',dir='/dev/shm') as td:
  td=Path(td);cache=td/'cache';cache.mkdir()
  x,parts=r.build(data,cache)
  wav=td/'original.wav';enc=td/'original.m4a';sf.write(wav,x,24000)
  subprocess.run([r.FF,'-y','-loglevel','error','-i',str(wav),'-af',r.AF,'-c:a','aac','-b:a','256k','-movflags','+faststart',str(enc)],check=True)
  pcm=sha(wav.read_bytes());aac=sha(subprocess.check_output(['ffmpeg','-v','error','-nostdin','-i',str(enc),'-map','0:a:0','-c:a','copy','-f','adts','-']))
  report.update({'original_maker_sha256':sha(r.m.source.encode()),'reconstructed_pcm_sha256':pcm,'reconstructed_AAC_sha256':aac,'matches_actual_native_PCM':pcm==expected_pcm,'matches_actual_accepted_AAC':aac==expected_aac,'parts':parts})
  assert pcm==expected_pcm and aac==expected_aac,'Original producer not bound to accepted native audio; do not claim exact timings.'
  s4=next(p for p in parts if p['sentence']=='S4')
  # Same unmodified sentence method, again from the same strictly read-only cache.
  scope,text=r.scope(data,4,cache);pieces=[];gaps=[];p0=0;listed=scope['list_commas'](text)
  import re
  for mt in re.finditer(r'[,;:](?=\s)',text):pieces.append((p0,mt.end()));p0=mt.end()+1;gaps.append(.2 if mt.start() in listed else .4)
  pieces.append((p0,len(text)))
  clips,tmap=scope['sentence_audio'](text,pieces,gaps)
  clips,a,agn,pgn=scope['句增益'](data,data['no'],3,text,pieces,gaps,clips,tmap,np.concatenate(clips))
  report['S4_word_tmap_raw_scalars']=tmap
  report['S4_LAST_timing']={k:scope['LAST'].get(k) for k in ['head','segs','total','cuts','gaps','hs']}
  report['S4_native_source_bound']=True
  report['temporary_private_audio_removed_after_context']=True
except BaseException as e:
 import traceback
 report['diagnostic_error']={'type':type(e).__name__,'message':str(e),'traceback':traceback.format_exc()}
report['G72_original_mother_scalar_provenance']=list(r.m.cache_rows.values())
report['stored_original_level_scalar_provenance']=list(r.level_rows.values())
report['temporary_derived_level_scalar_provenance']=list(ns['derived'])
(OUT/'strict-original-cache-source-binding.json').write_text(json.dumps(report,ensure_ascii=False,indent=2,default=lambda v:float(v) if isinstance(v,np.floating) else int(v))+'\n')
print(json.dumps({k:v for k,v in report.items() if k not in ['parts','G72_original_mother_scalar_provenance','stored_original_level_scalar_provenance','temporary_derived_level_scalar_provenance']},ensure_ascii=False),flush=True)
