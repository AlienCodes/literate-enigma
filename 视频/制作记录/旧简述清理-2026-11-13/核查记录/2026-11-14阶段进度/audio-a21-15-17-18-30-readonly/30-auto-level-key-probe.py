"""Only derive original G36 key from original cache-verified pre-level clips. No cache writes."""
import sys,types,importlib.util,pathlib,json,hashlib,subprocess,numpy as np,re
pkg=types.ModuleType('kokoro_onnx');sliding=types.ModuleType('kokoro_onnx.sliding');Timing=type('Timing',(),{});Timing.__module__='kokoro_onnx.sliding';sliding.Timing=Timing;pkg.sliding=sliding;sys.modules['kokoro_onnx']=pkg;sys.modules['kokoro_onnx.sliding']=sliding
B=pathlib.Path(__file__).parent
spec=importlib.util.spec_from_file_location('original_cached_functions',B/'reproduce_a21_cache_only.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
new=json.loads(pathlib.Path('/workspace/work/video-audit70-20261113/payload/视频/脚本/30.json').read_text());old=json.loads((B/'30/files/30-failed-working-source.json').read_text());rows=[]
for kind,d in [('old-current-native-failed-source',old),('root-approved-new-source',new)]:
 ns,sent=m.scope_for(d,9);pieces=[];gaps=[];p0=0;lst=ns['list_commas'](sent)
 for p in re.finditer(r'[,;:](?=\s)',sent):pieces.append((p0,p.end()));p0=p.end()+1;gaps.append(.2 if p.start() in lst else .4)
 pieces.append((p0,len(sent)));clips,tmap=ns['sentence_audio'](sent,pieces,gaps)
 key=hashlib.sha1(b''.join(np.ascontiguousarray(c,np.float32).tobytes() for c in clips)+repr(('30',list(gaps),[(round(t[2],4),round(t[3],4)) for t in tmap])).encode()).hexdigest();filename='调平_'+key+'.json'
 try:raw=m.git('视频/配音缓存/'+filename);existing=True;data=json.loads(raw);sha=hashlib.sha256(raw).hexdigest()
 except subprocess.CalledProcessError:existing=False;data=None;sha=None
 rows.append({'kind':kind,'article':'30','sentence':'S9','original_G36_auto_level_called':True,'reason':'NO30>=26, multiple punctuation pieces; PGRAFT skip only NO>=36, and approved repair removes PGRAFT anyway.','source_sha256':hashlib.sha256(json.dumps(d,ensure_ascii=False).encode()).hexdigest(),'source_file_sha256':hashlib.sha256((pathlib.Path('/workspace/work/video-audit70-20261113/payload/视频/脚本/30.json') if kind=='root-approved-new-source' else B/'30/files/30-failed-working-source.json').read_bytes()).hexdigest(),'spoken_English':sent,'number_of_pieces':len(pieces),'gaps':gaps,'tmap_public_scalar':[[x0,x1,round(a,4),round(b,4)] for x0,x1,a,b in tmap],'pre_level_clip_lengths':[len(x) for x in clips],'pre_level_clip_float32_SHA256':[hashlib.sha256(np.ascontiguousarray(x,np.float32).tobytes()).hexdigest() for x in clips],'derived_cache_filename':filename,'pinned_public_cache_entry_exists':existing,'existing_entry_sha256':sha,'existing_entry_gain_values':data,'raw_clips_or_private_cache_exported':False})
r={'kind':'read-only-original-G36-exact-key-probe','original_maker_sha256':hashlib.sha256(m.source.encode()).hexdigest(),'original_cache_pin':m.PIN,'original_model_voice_input_keys_G72_verified':True,'actual_native_new_production_not_yet_observed':True,'no_TTS_or_level_recomputation_or_cache_write':True,'rows':rows}
(B/'30-auto-level-exact-key-probe.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print(json.dumps(r,ensure_ascii=False))
