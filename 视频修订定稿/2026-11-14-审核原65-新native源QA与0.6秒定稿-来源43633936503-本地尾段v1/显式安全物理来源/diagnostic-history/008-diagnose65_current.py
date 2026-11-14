"""Read-only actual-source / original-cache audio diagnosis; no TTS, formal writes or PDF."""
from pathlib import Path
import ast,hashlib,importlib.util,json,os,re,subprocess,sys,time
import numpy as np,soundfile as sf
import urllib.request,urllib.parse
os.environ['GIT_NO_LAZY_FETCH']='1'
B=Path('/workspace/work/video-audit70-20261113'); O=Path(__file__).parent
A=B/'audio65-69-source-readonly/65';source=A/'65-failed-working-source.json';video=Path('/dev/shm/source65-audio092-private/65-current-latest-native.mp4')
P=Path('/dev/shm/source65-audio092-private');P.mkdir(exist_ok=True);cache=P/'cache';cache.mkdir(exist_ok=True)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def module(name,p):
 sp=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m
r=module('strict60_original_replay',B/'audio65-69-source-readonly/replay_original_sources.py')
original_git=r.m.git;restored=P/'restored-native-exact-cache';restored.mkdir(exist_ok=True);restored_rows=[]
def exact_original_git(path):
 candidate=restored/Path(path).name
 if path.startswith('视频/配音缓存/')and candidate.exists():
  raw=candidate.read_bytes()
 else:
  try:return original_git(path)
  except subprocess.CalledProcessError as missing:
   assert path.startswith('视频/配音缓存/'),'Only immutable audio-cache objects may be privately restored.'
   listing=subprocess.check_output(['git','ls-tree','-z',r.m.PIN,'--',path],cwd=r.m.RPO)
   if not listing:raise missing
   assert listing.split(b'\t',1)[1].rstrip(b'\0').decode()==path
   blob=listing.split()[2].decode();url='https://raw.githubusercontent.com/alienalgorithm/postgraduate-vocabulary/'+r.m.PIN+'/'+urllib.parse.quote(path)
   raw=urllib.request.urlopen(url,timeout=25).read();assert len(raw)<8000000
   assert hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==blob
   candidate.write_bytes(raw);restored_rows.append({'key':Path(path).name,'git_blob_sha1':blob,'SHA256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)})
 return raw
r.m.git=exact_original_git
d=json.loads(source.read_text());assert sha(source)=='10cce8b5be1949c746369bb091829dbca9bcdd59f65b5d8b24b4a2a0ffcd4327'
rep={'kind':'source65-book37-readonly-current-native-before-user092-diagnostic','not_quality_acceptance':True,'source_sha256':sha(source),'video_sha256':sha(video),'video_bytes':video.stat().st_size,'original_maker_sha256':hashlib.sha256(r.m.source.encode()).hexdigest(),'new_TTS_or_formal_source_mutation':False,'human_listening_claimed':False}
x,parts=r.build(d,cache);wav=P/'current-source.wav';sf.write(wav,x,24000);assert sha(wav)=='c655cba20b97c97ca431a6e5eb43e8c250a67d6fc6ea92e695ff58139aa3ed41'
enc=P/'current-source.m4a';subprocess.run([r.FF,'-y','-loglevel','error','-i',str(wav),'-af',r.AF,'-c:a','aac','-b:a','256k','-movflags','+faststart',str(enc)],check=True)
def aac_sha(p):return hashlib.sha256(subprocess.check_output(['ffmpeg','-v','error','-nostdin','-i',str(p),'-map','0:a:0','-c:a','copy','-f','adts','-'])).hexdigest()
oldAAC=aac_sha(video);newAAC=aac_sha(enc);assert newAAC==oldAAC=='e561c8319355ca7f96047b52c3a758cb89e92196553949e4532d06a2893a4125'
rep['current_native_binding']={'WAV_sha256':sha(wav),'WAV_md5_first12':hashlib.md5(wav.read_bytes()).hexdigest()[:12],'reconstructed_AAC_sha256':newAAC,'actual_current_native_AAC_sha256':oldAAC,'whole_AAC_exact':True,'samples':len(x),'rate':24000}
rep['legacy_role']={'video_sha256':'6bad7b012ccbad87a60ced23ada2c3162c7a561b4e72ad52362004ee3313ea8c','AAC_sha256':'66f8c5cfdd6c5551f20779115574f896d849763cf5adf8042c503664bf7ab94f','role':'only-the-older-review-user-heard-not-current-repair-baseline','not_AAC_identical_to_current':oldAAC!='66f8c5cfdd6c5551f20779115574f896d849763cf5adf8042c503664bf7ab94f'}
raw=subprocess.check_output(['ffmpeg','-v','error','-nostdin','-i',str(video),'-map','0:a:0','-f','f32le','-ac','1','-ar','24000','-']);dc=np.frombuffer(raw,np.float32).copy();np.save(P/'current-decoded.npy',dc);np.save(P/'current-source-normalized.npy',x)
rep['parts']=parts;rep['restored_original_immutable_cache_scalar_provenance']=restored_rows;rep['stored_level_cache_scalar_provenance']=list(r.level_rows.values())
ns,txt=r.scope(d,2,cache);nsound=next(z for z in ast.parse(r.m.source).body if isinstance(z,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='_NOSOUND'for t in z.targets));exec(compile(ast.Module(body=[nsound],type_ignores=[]),'original-NOSOUND','exec'),ns)
pieces=[];gaps=[];p0=0;listed=ns['list_commas'](txt)
for mt in re.finditer(r'[,;:](?=\s)',txt):pieces.append((p0,mt.end()));p0=mt.end()+1;gaps.append(.2 if mt.start()in listed else .4)
pieces.append((p0,len(txt)));clips,tmap=ns['sentence_audio'](txt,pieces,gaps);clips,vo,agn,pgn=ns['句增益'](d,d['no'],1,txt,pieces,gaps,clips,tmap,np.concatenate(clips))
rep['S2_current_producer']={'text':txt,'pieces':pieces,'piece_texts':[txt[a:b]for a,b in pieces],'gaps':gaps,'tmap':tmap,'automatic_level':agn,'manual_segment_level':pgn,'LAST':{k:ns['LAST'].get(k)for k in ['head','segs','total','cuts','grafts','gaps','hs']}}
rep['human_listening_claimed']=False;rep['current_latest_native_is_repair_baseline']=True;rep['source_PAY_GEN_text_PDF_or_existing_controls_mutated']=False
(P/'65-current-native-original-cache-binding-and-timing.json').write_text(json.dumps(rep,ensure_ascii=False,indent=2,default=lambda z:float(z))+'\n');print(json.dumps({'binding':rep['current_native_binding'],'S2':rep['S2_current_producer']},ensure_ascii=False),flush=True)
