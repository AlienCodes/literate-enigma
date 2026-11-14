"""Read-only source provenance: original functions, G72 mothers, stored level JSON.

No inference or parameter changes. Private reconstructed audio is deleted. This is
diagnosis only; an AAC mismatch never establishes an accepted source binding.
"""
import pathlib,json,importlib.util,hashlib,re,sys,tempfile,subprocess,os,traceback
import numpy as np,soundfile as sf,imageio_ffmpeg
from kokoro_onnx.tokenizer import Tokenizer

B=pathlib.Path(__file__).parent
spec=importlib.util.spec_from_file_location('original_cache_funcs',B.parent/'audio-a21-15-17-18-30-readonly/reproduce_a21_cache_only.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
sys.path.insert(0,str(m.T))
pron=json.loads((m.T/'发音词典/读音改正.json').read_text())
ctx=json.loads((m.T/'发音词典/按语境读音.json').read_text())
tk=Tokenizer();AF=m.git('视频/工具/配音/AF.txt').decode().strip();FF=imageio_ffmpeg.get_ffmpeg_exe()
os.environ['STRICT_CACHE']='1'
level_rows={}

def sha(x):return hashlib.sha256(x).hexdigest()

def scope(d,si,cache):
 ns,text=m.scope_for(d,si)
 ns['KT'].tokenizer=tk
 ns['PRON_WORDS']={k:v['读音'] for k,v in pron.items()}
 ns['PRON_EXTRA']={k:v['语境错读'] for k,v in pron.items() if v.get('语境错读')}
 ns['PRON_CTX']=ctx;ns['PRON_FIX']={}
 ns['_wf']=lambda w:0 if any(c.isupper() for c in w[1:]) else re.I
 ns['_SP_CACHE']={};ns['k'].create=ns['_pron'](ns['k'].create)
 ns['KT'].create_timed=ns['_pron'](ns['KT'].create_timed)
 if d.get('结尾句',{}).get('S'+str(si)):ns['ENDING']={text:d['结尾句']['S'+str(si)]}
 ns['_短下']=4.5;ns['_短上']=6.;ns['_短长']=1.5
 ns['_CACHE']=str(cache);ns['_REPO_CACHE']=str(cache/'nonexistent-public')
 original_level=ns['_auto_level']
 def exact_level(clips,tmap,gaps,no='',rounds=2):
  import 响度一致性核对 as LQ
  if not any(g>=LQ.IN_GAP for g in gaps):
   return original_level(clips,tmap,gaps,no,rounds)
  key=hashlib.sha1(b''.join(np.ascontiguousarray(c,np.float32).tobytes() for c in clips)+repr((str(no),list(gaps),[(round(t[2],4),round(t[3],4)) for t in tmap])+(('K134等效',) if ns['_短起'](no) else ())).encode()).hexdigest()
  name='调平_'+key+'.json';p=cache/name
  if not p.exists():
   raw=m.git('视频/配音缓存/'+name);value=json.loads(raw)
   assert isinstance(value,dict) and all(str(k).isdigit() and isinstance(v,(float,int)) for k,v in value.items())
   p.write_bytes(raw);level_rows[name]={'key':name,'stored_json_full_SHA256':sha(raw),'stored_value':value,'repository_commit':m.PIN,'existing_public_cache_copied_to_private_temp_only':True}
  return original_level(clips,tmap,gaps,no,rounds)
 ns['_auto_level']=exact_level
 return ns,text

def build(d,cache):
 ns,_=scope(d,1,cache);title=d['title_en']
 for control,key in [('NONVOICE','非人声区间'),('GRAFT','词尾除阻'),('BOOST','除阻加强')]:
  if '标题' in d.get(key,{}):ns[control]['标题::'+title]=d[key]['标题']
 ta=ns['title_audio'](title);audio=[ns['sil'](.4),ta,ns['sil'](.6)];prev=None
 parts=[{'sentence':'title','start_s':.4,'end_s':.4+len(ta)/24000,'sample_count':len(ta),'pre_normalized_array_SHA256':sha(ta.tobytes())}]
 for si,s in enumerate(d['sentences'],1):
  n,t=scope(d,si,cache);pieces=[];gaps=[];p0=0;listed=n['list_commas'](t)
  for mt in re.finditer(r'[,;:](?=\s)',t):pieces.append((p0,mt.end()));p0=mt.end()+1;gaps.append(.2 if mt.start() in listed else .4)
  pieces.append((p0,len(t)))
  clips,tmap=n['sentence_audio'](t,pieces,gaps)
  clips,a,agn,pgn=n['句增益'](d,d['no'],si-1,t,pieces,gaps,clips,tmap,np.concatenate(clips))
  lead=.4 if si==1 else .3+(.2 if prev is not None and s['para']!=prev else 0.);prev=s['para'];start=(sum(len(x) for x in audio)/24000)+lead
  parts.append({'sentence':'S'+str(si),'spoken_English':t,'start_s':start,'end_s':start+len(a)/24000,'sample_count':len(a),'pre_normalized_array_SHA256':sha(a.tobytes()),'automatic_level':agn,'manual_segment_level':pgn,'actual_raw_processed_fp':n['SENT_FP'].get(t),'actual_control_invalidated':t in n['VOIDED'],'LAST_scalar_timing':{k:n['LAST'].get(k) for k in ['head','segs','total','cuts','grafts','gaps','hs']}})
  audio.extend([n['sil'](lead),a,n['sil'](.7)])
  print(d['no'],'S'+str(si),'ok',flush=True)
 audio.append(ns['sil'](1.3));a=np.concatenate(audio)
 return a/np.abs(a).max()*.89,parts

def main(no):
 folder=B/no;expected=json.loads((folder/f'{no}-failed-draft-proof.json').read_text());st=json.loads((folder/f'{no}-status.json').read_text())
 warm=B.parent/f'warm-source-readonly-43545131120/{no}-restored-cache-source-candidate.json'
 actual=folder/f'{no}-failed-working-source.json';request=pathlib.Path('/workspace/work/video-revision-batch-ci/.github/video-revision-batch/request')/no/'视频/脚本'/f'{no}.json'
 report={'kind':f'{no}-original-G72-cache-source-AAC-provenance','quality_acceptance':False,'original_maker_SHA256':sha(m.source.encode()),'original_clean_SHA256':sha(m.clean.encode()),'pronunciation_dictionary_SHA256':sha((m.T/'发音词典/读音改正.json').read_bytes()),'AF_full_SHA256':sha(AF.encode()),'FF_version':subprocess.check_output([FF,'-version'],text=True).splitlines()[0],'accepted_anchor':st['accepted_source'],'actual_failed_expected_proof':{k:expected[k]for k in ['internal_pcm_sha256','video_sha256','aac_adts_sha256','source_sha256']},'modes':[]}
 try:
  with tempfile.TemporaryDirectory(prefix=f'private-{no}-exact-source-diagnostic-',dir='/dev/shm') as td:
   td=pathlib.Path(td);cache=td/'cache';cache.mkdir()
   for label,p in [('warm_candidate',warm),('actual_failed_source',actual),('current_request',request)]:
    d=json.loads(p.read_text());x,parts=build(d,cache);wav=td/(label+'.wav');out=td/(label+'.m4a');sf.write(wav,x,24000)
    subprocess.run([FF,'-y','-loglevel','error','-i',str(wav),'-af',AF,'-c:a','aac','-b:a','256k','-movflags','+faststart',str(out)],check=True)
    aa=sha(subprocess.check_output(['ffmpeg','-v','error','-nostdin','-i',str(out),'-map','0:a:0','-c:a','copy','-f','adts','-']));ws=sha(wav.read_bytes())
    row={'source_kind':label,'source_file_SHA256':sha(p.read_bytes()),'private_WAV_full_SHA256':ws,'private_AAC_ADTS_SHA256':aa,'matches_actual_failed_native_PCM':ws==expected['internal_pcm_sha256'],'matches_actual_failed_AAC':aa==expected['aac_adts_sha256'],'matches_real_accepted_AAC':aa==st['accepted_source']['aac_adts_sha256'],'sample_count_24k':len(x),'parts':parts};report['modes'].append(row)
    print(no,label,aa,'old?',row['matches_real_accepted_AAC'],'native?',row['matches_actual_failed_native_PCM'],flush=True)
 except BaseException as e:
  report['error']={'type':type(e).__name__,'detail':str(e),'traceback':traceback.format_exc()};print(traceback.format_exc(),flush=True)
 report['no_TTS_or_source_core_existing_cache_mutation']=True;report['private_generated_audio_removed']=True
 report['G72_mother_cache_scalar_provenance']=list(m.cache_rows.values());report['stored_level_cache_scalar_provenance']=list(level_rows.values())
 (folder/f'{no}-original-source-exact-AAC-replay.json').write_text(json.dumps(report,ensure_ascii=False,indent=2,default=lambda x:float(x))+'\n')

if __name__=='__main__':
 for no in sys.argv[1:]or['65','69']:main(no)
