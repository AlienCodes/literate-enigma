"""Original source-bound S4 first-word diagnostic; no source or waveform changes."""
from pathlib import Path
import json,hashlib,re,subprocess
import numpy as np
from scipy import signal
BASE=Path('/workspace/work/video-audit70-20261113');OUT=Path('/workspace/work/tetris34-audio-user-review-20261114')
probe=BASE/'audio-a21-actual-first-4K-20261114/probe_minimal_encoded_boost.py'
ns={'__name__':'readonly34_wordhead_definitions','__file__':str(probe)};exec(compile(probe.read_text().split('\nfor no in sys.argv')[0],str(probe)+'#definitions-only','exec'),ns);r=ns['r']
bind=json.loads((OUT/'strict-original-cache-source-binding.json').read_text());assert bind['matches_actual_native_PCM'] and bind['matches_actual_accepted_AAC']
d=json.loads(Path(bind['source_file']).read_text());baseline=next(p for p in bind['parts'] if p['sentence']=='S4')
import tempfile
with tempfile.TemporaryDirectory(prefix='private34-wordhead-',dir='/dev/shm') as td:
 cache=Path(td)/'cache';cache.mkdir();scope,text=r.scope(d,4,cache)
 import ast
 for node in ast.parse(r.m.source).body:
  if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='_NOSOUND' for t in node.targets):exec(compile(ast.Module(body=[node],type_ignores=[]),'unchanged-original-NOSOUND-definition','exec'),scope)
 pieces=[];gaps=[];p0=0;listed=scope['list_commas'](text)
 for mt in re.finditer(r'[,;:](?=\s)',text):pieces.append((p0,mt.end()));p0=mt.end()+1;gaps.append(.2 if mt.start() in listed else .4)
 pieces.append((p0,len(text)));clips,tmap=scope['sentence_audio'](text,pieces,gaps);clips,a,agn,pgn=scope['句增益'](d,d['no'],3,text,pieces,gaps,clips,tmap,np.concatenate(clips))
 assert hashlib.sha256(a.tobytes()).hexdigest()==baseline['pre_normalized_array_SHA256']
 wordends=[]
 for prefix in ['He','He called','He called it']:
  rest=text[len(prefix):].strip();wordends.append(scope['chunk_times']([prefix,rest])[0])
 wordends.append(tmap[0][3]);wordrows=[{'word':w,'start_s_in_producer_sentence':st,'end_s_in_producer_sentence':en}for w,st,en in zip(['He','called','it','Tetris,'],[0.0]+wordends[:-1],wordends)]
 toks=[{'phoneme':x.phoneme,'start':float(x.start),'end':float(x.end)}for x in scope['LAST']['toks']]
 # Public MP4 decoded waveform, no private producer data exported.
 p=BASE/'next-passed-native/43533004625/34/34-4K-正文后插图2秒-简述2秒.mp4'
 raw=subprocess.check_output([r.FF,'-v','error','-nostdin','-i',str(p),'-vn','-ac','1','-ar','24000','-f','f32le','-']);pub=np.frombuffer(raw,dtype=np.float32)
 st=baseline['start_s'];expected=int(round(st*24000));margin=2400
 target=pub[expected-margin:expected+len(a)+margin]
 c=signal.correlate(target.astype(float),a.astype(float),mode='valid',method='fft');lag=int(np.argmax(c))-margin
 def metrics(x):
  return {'rms_dbfs':float(20*np.log10(np.sqrt(np.mean(np.asarray(x,float)**2))+1e-20)),'peak_dbfs':float(20*np.log10(np.max(np.abs(x))+1e-20)),'samples':len(x)}
 m=[]
 for w in wordrows[:4]:
  s=st+w['start_s_in_producer_sentence']+lag/24000;e=st+w['end_s_in_producer_sentence']+lag/24000;x=pub[int(round(s*24000)):int(round(e*24000))]
  m.append(dict(w,public_window_s=[s,e],public_measurement=metrics(x)))
 rawmother,_=scope['k'].create(scope['spoken'](text),voice=scope['V'],speed=scope['SPEED'],lang='en-us')
 h=scope['LAST']['head']+scope['LAST']['hs'];first_removed=rawmother[:h]
 out={'kind':'source-bound-actual-public-S4-word-head-diagnostic','source_PCM_and_AAC_exact_binding':True,'S4_sentence':baseline,'word_boundaries_basis':'unchanged original native chunk_times on unique initial text prefixes plus unchanged remainder; source phoneme timings, not independent human listening','first_four_words':m,'raw_timed_phonemes_prefix':toks[:20],'raw_to_public_waveform_alignment_lag_samples_24k':lag,'raw_to_public_waveform_alignment_lag_s':lag/24000,'original_AF':r.AF,'native_head_trim_samples':h,'native_head_trim_ms':h/24,'trimmed_head_scalar_metrics':metrics(first_removed) if len(first_removed) else None,'clean_tail_original_head_fade_ms':10,'first_He_full_source_bound_word_peak_and_RMS_measured':True,'private_cache_audio_exported':False,'any_source_or_audio_changed':False}
 (OUT/'source-bound-S4-word-head-diagnostic.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k not in ['S4_sentence','raw_timed_phonemes_prefix']},ensure_ascii=False))
