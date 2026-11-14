"""Private exact original-function source A/B replay; export scalar hashes only."""
import pathlib,json,importlib.util,hashlib,copy,re,sys,types,tempfile,subprocess,io,contextlib
import numpy as np,soundfile as sf,imageio_ffmpeg
from kokoro_onnx.tokenizer import Tokenizer
B=pathlib.Path(__file__).parent;A=pathlib.Path('/workspace/work/video-audit70-20261113/ready41-monitor/02-artifact');req=pathlib.Path('/workspace/work/video-revision-batch-ci/.github/video-revision-batch/request/02/视频/脚本/02.json');old=json.loads(req.read_text());cur=json.loads((A/'02-failed-working-source.json').read_text());spec=importlib.util.spec_from_file_location('original_cache_funcs',B.parent/'audio-a21-15-17-18-30-readonly/reproduce_a21_cache_only.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);pron=json.loads((m.T/'发音词典/读音改正.json').read_text());ctx=json.loads((m.T/'发音词典/按语境读音.json').read_text());tk=Tokenizer()
def scope(d,si):
 ns,text=m.scope_for(d,si);ns['KT'].tokenizer=tk;ns['PRON_WORDS']={k:v['读音'] for k,v in pron.items()};ns['PRON_EXTRA']={k:v['语境错读'] for k,v in pron.items() if v.get('语境错读')};ns['PRON_CTX']=ctx;ns['PRON_FIX']={};ns['_wf']=lambda w:0 if any(c.isupper() for c in w[1:]) else re.I;ns['_SP_CACHE']={};ns['k'].create=ns['_pron'](ns['k'].create);ns['KT'].create_timed=ns['_pron'](ns['KT'].create_timed)
 if d.get('结尾句',{}).get('S'+str(si)):ns['ENDING']={text:d['结尾句']['S'+str(si)]}
 ns['_短下']=4.5;ns['_短上']=6.;ns['_短长']=1.5
 return ns,text
def build(d):
 ns,_=scope(d,1);title=d['title_en']
 for control,key in [('NONVOICE','非人声区间'),('GRAFT','词尾除阻'),('BOOST','除阻加强')]:
  if '标题' in d.get(key,{}):ns[control]['标题::'+title]=d[key]['标题']
 audio=[ns['sil'](.4),ns['title_audio'](title),ns['sil'](.6)];prev=None;parts=[]
 for si,s in enumerate(d['sentences'],1):
  n,t=scope(d,si);pieces=[];gaps=[];p0=0;listed=n['list_commas'](t)
  for mt in re.finditer(r'[,;:](?=\s)',t):pieces.append((p0,mt.end()));p0=mt.end()+1;gaps.append(.2 if mt.start() in listed else .4)
  pieces.append((p0,len(t)));clips,tmap=n['sentence_audio'](t,pieces,gaps);clips,a,agn,pgn=n['句增益'](d,'02',si-1,t,pieces,gaps,clips,tmap,np.concatenate(clips));lead=.4 if si==1 else .3+(.2 if prev is not None and s['para']!=prev else 0.);prev=s['para'];start=(sum(len(x) for x in audio)/24000)+lead;parts.append({'sentence':'S'+str(si),'start_s':start,'end_s':start+len(a)/24000,'sample_count':len(a),'pre_normalized_array_SHA256':hashlib.sha256(a.tobytes()).hexdigest()});audio.extend([n['sil'](lead),a,n['sil'](.7)])
 audio.append(ns['sil'](1.3));a=np.concatenate(audio);return a/np.abs(a).max()*.89,parts
current,cp=build(cur);previous,op=build(old);expected=json.loads((A/'02-failed-draft-proof.json').read_text());AF=m.git('视频/工具/配音/AF.txt').decode().strip();FF=imageio_ffmpeg.get_ffmpeg_exe();rows=[]
with tempfile.TemporaryDirectory(prefix='02-native-exact-counterfactual-',dir='/workspace/work/video-private-reference-analysis') as td:
 for label,x,parts in [('current_source_only',current,cp),('request_without_added_NV',previous,op)]:
  wav=pathlib.Path(td)/(label+'.wav');mp4=pathlib.Path(td)/(label+'.m4a');sf.write(wav,x,24000)
  wavsha=hashlib.sha256(wav.read_bytes()).hexdigest();subprocess.run([FF,'-y','-loglevel','error','-i',str(wav),'-af',AF,'-c:a','aac','-b:a','256k','-movflags','+faststart',str(mp4)],check=True);adts=subprocess.check_output(['ffmpeg','-v','error','-nostdin','-i',str(mp4),'-map','0:a:0','-c:a','copy','-f','adts','-']);aa=hashlib.sha256(adts).hexdigest();rows.append({'mode':label,'private_reconstructed_WAV_SHA256':wavsha,'private_reconstructed_AAC_ADTS_SHA256':aa,'sample_count_24k':len(x),'parts':parts,'matches_current_native_full_PCM_SHA256':wavsha==expected['internal_pcm_sha256'],'matches_current_public_AAC':aa==expected['aac_adts_sha256'],'matches_actual_accepted_AAC':aa=='c026dfff1f9591a3e11539cc40e87e3da0ed247cec3bf883d265011126e094d3'})
r={'kind':'02-exact-original-function-whole-source-counterfactual','quality_acceptance':False,'no_TTS_inference_or_source_core_cache_mutation':True,'private_all_generated_audio_removed':True,'original_maker_SHA256':hashlib.sha256(m.source.encode()).hexdigest(),'original_AF_SHA256':hashlib.sha256(AF.encode()).hexdigest(),'actual_used_ffmpeg_version':subprocess.check_output([FF,'-version'],text=True).splitlines()[0],'G72_mother_cache_scalar_provenance':list(m.cache_rows.values()),'current_expected_native_PCM_SHA256':expected['internal_pcm_sha256'],'current_expected_native_AAC_SHA256':expected['aac_adts_sha256'],'modes':rows};(B/'02-whole-original-source-counterfactual-proof.json').write_text(json.dumps(r,ensure_ascii=False,indent=2,default=lambda x:float(x))+'\n');print(json.dumps({'modes':[{k:v for k,v in x.items() if k!='parts'} for x in rows],'private_audio_removed':True},ensure_ascii=False))
