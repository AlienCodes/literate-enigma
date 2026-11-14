"""Readonly diagnostic: original-maker cache-only source37 to actual accepted AAC binding."""
from pathlib import Path
import ast,hashlib,importlib.util,json,os,re,subprocess,sys,urllib.parse,urllib.request
import numpy as np,soundfile as sf
os.environ['GIT_NO_LAZY_FETCH']='1';os.environ['TMPDIR']=str(Path(__file__).parent)
B=Path('/workspace/work/video-audit70-20261113');O=Path(__file__).parent;A=B/'next-passed-native/43543967031/37/artifact-files';src=A/'37-actual-working-source.json';video=A.parent/'37-4K-正文后插图2秒-简述2秒.mp4';cache=O/'cache';cache.mkdir(exist_ok=True);restored=O/'restored-native-exact-cache';restored.mkdir(exist_ok=True)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(name,p):
 sp=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m
r=load('readonly19_original_replay',B/'audio65-69-source-readonly/replay_original_sources.py');assert hashlib.sha256(r.m.source.encode()).hexdigest()=='4c85e1fbdd2e82c5646d5f58df63c85eca60af4ef521f1d36f765575a568d6f3';assert hashlib.sha256(r.m.clean.encode()).hexdigest()=='86b3872cbca83437e24da2c7ada5fffd916f06cacdd2b32fee2a78c9b134178d';ogit=r.m.git;restore_rows=[]
def exactgit(path):
 q=restored/Path(path).name
 if path.startswith('视频/配音缓存/')and q.exists():return q.read_bytes()
 try:return ogit(path)
 except subprocess.CalledProcessError as exc:
  assert path.startswith('视频/配音缓存/'),'No non-cache Git object or source restoration permitted.'
  out=subprocess.check_output(['git','ls-tree','-z',r.m.PIN,'--',path],cwd=r.m.RPO)
  if not out:raise exc
  assert out.split(b'\t',1)[1].rstrip(b'\0').decode()==path;blob=out.split()[2].decode();url='https://raw.githubusercontent.com/alienalgorithm/postgraduate-vocabulary/'+r.m.PIN+'/'+urllib.parse.quote(path);raw=urllib.request.urlopen(url,timeout=30).read();assert len(raw)<9000000;assert hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==blob;q.write_bytes(raw);restore_rows.append({'key':q.name,'immutable_PIN':r.m.PIN,'git_blob_sha1':blob,'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw),'RAM_private_only':True});return raw
# Load the actual original G57 table from every canonical current article, not only this source.
_full_SP={};_full_SP_rows=[]
for _p in sorted((B/'payload/视频/脚本').glob('[0-9][0-9].json')):
 _j=json.loads(_p.read_text())
 for _sn,_pairs in _j.get('合成标点',{}).items():
  _disp=' '.join(re.sub(r'\{\{.*?\}\}','',c['en']).replace('**','').strip()for c in _j['sentences'][int(_sn[1:])-1]['chunks']);_full_SP[(str(_p),_sn)]=(_disp,[tuple(z)for z in _pairs]);_full_SP_rows.append({'source_id':_j['no'],'sentence':_sn,'source_sha256':sha(_p),'display_English':_disp,'pairs':_pairs})
_original_scope=r.scope
def _scope_with_all_SP(d_,si_,cache_):
 ns_,t_=_original_scope(d_,si_,cache_);ns_['SYNTH_PUNCT']=_full_SP;ns_['_SP_CACHE']={};return ns_,t_
r.scope=_scope_with_all_SP
r.m.git=exactgit;assert sha(src)=='cf4d7618f46155f222d9ce016c5411fbd3904aa6296834048c486c286ed2e40d';assert sha(video)=='decc63c0423eee0526315aa78e5a3c867300b335296006cf108891ccf1d5f174';d=json.loads(src.read_text());x,parts=r.build(d,cache);wav=O/'original-actual-source.wav';sf.write(wav,x,24000);enc=O/'original-actual-source.m4a';subprocess.run([r.FF,'-y','-loglevel','error','-i',str(wav),'-af',r.AF,'-c:a','aac','-b:a','256k','-movflags','+faststart',str(enc)],check=True)
def aac(p):return hashlib.sha256(subprocess.check_output(['ffmpeg','-v','error','-nostdin','-i',str(p),'-map','0:a:0','-c:a','copy','-f','adts','-'])).hexdigest()
a,b=aac(video),aac(enc);assert a==b=='60f3893386a8fc86d9f72b08b0b7eada024dcb350a7bb9bad9a37588b771d572';raw=subprocess.check_output(['ffmpeg','-v','error','-nostdin','-i',str(video),'-map','0:a:0','-f','f32le','-ac','1','-ar','24000','-']);decoded=np.frombuffer(raw,np.float32).copy();np.save(O/'actual-public-decoded.npy',decoded);np.save(O/'source-normalized.npy',x)
requested=[]
for si in [10,13]:
 ns,t=r.scope(d,si,cache);pieces=[];gaps=[];p0=0;listed=ns['list_commas'](t)
 for mt in re.finditer(r'[,;:](?=\s)',t):pieces.append((p0,mt.end()));p0=mt.end()+1;gaps.append(.2 if mt.start()in listed else .4)
 pieces.append((p0,len(t)));clips,tmap=ns['sentence_audio'](t,pieces,gaps);clips,vo,agn,pgn=ns['句增益'](d,d['no'],si-1,t,pieces,gaps,clips,tmap,np.concatenate(clips));rawmother=ns['k'].create(ns['spoken'](t),voice=ns['V'],speed=.95,lang='en-us')[0];timed,_,tokens=ns['KT'].create_timed(ns['spoken'](t),voice=ns['V'],speed=.95,lang='en-us',clause_pause=0,sentence_pause=0);np.save(O/f'S{si}-raw-mother.npy',rawmother);np.save(O/f'S{si}-processed.npy',vo)
 requested.append({'sentence':'S'+str(si),'English':t,'piece_texts':[t[s:e]for s,e in pieces],'pieces':pieces,'gaps':gaps,'tmap':tmap,'automatic_level':agn,'manual_segment_level':pgn,'LAST':{k:ns['LAST'].get(k)for k in['head','segs','total','cuts','grafts','gaps','hs']},'source_voice_controls':{k:d.get(k,{}).get('S'+str(si))for k in['非人声区间','停顿删除区间','停顿插入点','词尾除阻','停顿处除阻','除阻加强','分段增益dB','段内渐变dB','句子增益dB','结尾句']},'raw_mother_samples':len(rawmother),'timed_mother_samples':len(timed),'private_raw_tokens':[{'phoneme':z.phoneme,'start_s':z.start,'end_s':z.end}for z in tokens]})
rep={'kind':'readonly-actual-source37-full-original-cache-AAC-binding-and-requested-sentence-timing','source_id':'37','book_order':'43','diagnostic_not_formal_native_acceptance':True,'new_TTS_or_source_core_cache_mutation':False,'actual_original_source_sha256':sha(src),'actual_latest_accepted_MP4_sha256':sha(video),'original_maker_sha256':hashlib.sha256(r.m.source.encode()).hexdigest(),'original_clean_sha256':hashlib.sha256(r.m.clean.encode()).hexdigest(),'original_AF_sha256':hashlib.sha256(r.AF.encode()).hexdigest(),'whole_original_source_WAV_sha256':sha(wav),'whole_original_source_WAV_md5_first12':hashlib.md5(wav.read_bytes()).hexdigest()[:12],'whole_reconstructed_AAC_sha256':b,'actual_AAC_sha256':a,'full_AAC_exact_binding':True,'sample_count_24k':len(x),'parts':parts,'requested_original_producer':requested,'private_restored_immutable_cache_scalar_provenance':restore_rows,'private_G72_mother_scalar_provenance':list(r.m.cache_rows.values()),'stored_original_automatic_level_scalar_provenance':r.level_rows,'loaded_all_original_synth_punctuation_table':_full_SP_rows,'synth_punctuation_hits_for_this_source':[z for z in _full_SP_rows if str(z['source_id'])=='37'],'human_listening_not_claimed':True,'private_raw_timed_token_report_NOT_FOR_PUBLIC_ALLOWLIST':True};p=O/'37-original-actual-source-full-AAC-binding-and-requested-timing-PRIVATE.json';p.write_text(json.dumps(rep,ensure_ascii=False,indent=2,default=lambda z:float(z))+'\n');print(json.dumps({'report':str(p),'sha256':sha(p),'WAV_sha256':sha(wav),'AAC_sha256':b,'requested':[dict(z,private_raw_tokens='PRIVATE OMITTED')for z in requested]},ensure_ascii=False))
