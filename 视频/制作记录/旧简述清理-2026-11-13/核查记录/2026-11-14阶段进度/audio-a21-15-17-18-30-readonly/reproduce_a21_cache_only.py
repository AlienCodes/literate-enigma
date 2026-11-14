"""Diagnostic only: original functions + G72-verified unprocessed cached material.
No TTS inference; no source changes; no waveform/pickle/GT written or exported.
"""
from pathlib import Path
import ast,hashlib,json,os,pickle,re,subprocess,types
import numpy as np
import scipy.signal as ss

B=Path('/workspace/work/video-audit70-20261113');O=B/'audio-a21-15-17-18-30-readonly';T=Path('/workspace/work/audit-repo/视频/工具');RPO=Path('/workspace/work/github-publication/target');PIN='64621068034f8b6e09836a6d97210a0e9b2f1ed6'
def sha(data):return hashlib.sha256(data).hexdigest()
def git(path):return subprocess.check_output(['git','cat-file','blob',PIN+':'+path],cwd=RPO,stderr=subprocess.PIPE)
voice_raw=git('视频/工具/配音/voice_mb.npy')
import io
V=np.load(io.BytesIO(voice_raw));VH=hashlib.sha1(np.ascontiguousarray(V).tobytes()).hexdigest();models=json.loads((T/'环境/模型校验码.json').read_text());old=json.loads(git('视频/配音缓存/老条目指纹.json'))['条目'];cache={};cache_rows={}
class StrictReadOnlyCache:
 def __init__(self,method):self.method=method
 def create(self,text,voice,speed=1.,lang='en-us',**kw):return self._read(text,voice,speed,lang,kw)
 def create_timed(self,text,voice,speed=1.,lang='en-us',**kw):return self._read(text,voice,speed,lang,kw)
 def _read(self,text,voice,speed,lang,kw):
  model='kokoro-v1.0.onnx' if self.method=='create' else 'kokoro-v1.0-timed.onnx';mid=models[model];vh=hashlib.sha1(np.ascontiguousarray(voice).tobytes()).hexdigest()
  key=hashlib.sha1(repr((self.method,mid,text,vh,float(speed),lang,sorted(kw.items()))).encode()).hexdigest()+'.pkl'
  if key not in cache:
   blob=git('视频/配音缓存/'+key);h=sha(blob)
   try:mark=git('视频/配音缓存/'+key+'.单线程').decode().strip();assert mark==h[:16];basis='native-single-thread-marker'
   except subprocess.CalledProcessError:mark=None;assert old.get(key)==h[:16];basis='original-old-entry-manifest'
   value=pickle.loads(blob);assert type(value) is tuple and len(value)==(2 if self.method=='create' else 3);assert value[1]==24000
   cache[key]=value;cache_rows[key]={'key':key,'method':self.method,'model_identifier':mid,'input_sha256':sha(text.encode()),'voice_array_sha1':vh,'speed':speed,'lang':lang,'kw':kw,'pkl_full_sha256':h,'G72_basis':basis,'marker':mark,'schema':{'tuple_length':len(value),'dtype':str(value[0].dtype),'shape':list(value[0].shape),'sample_rate':24000},'raw_array_bytes_exported':False}
  value=cache[key];return (value[0].copy(),*value[1:])

source=(T/'make_video.py').read_text();tree=ast.parse(source);clean=(T/'clean.py').read_text();clean_tree=ast.parse(clean);a21=(T/'词尾辅音核对.py').read_text();atree=ast.parse(a21)

def scope_for(d,si):
 ns={'np':np,'os':os,'re':re,'json':json,'subprocess':subprocess,'_hl':hashlib,'SR':24000,'WIN':240,'SPEED':.95,'SIL_DB':-55,'PAUSE_DB':-40,'AUD_DB':-55,'INNER_MAX':.22,'INNER_TO':.18,'GRAFT_DB':-27,'P_COMMA':.4,'P_LIST':.2,'V':V,'k':StrictReadOnlyCache('create'),'KT':StrictReadOnlyCache('create_timed'),'R':types.SimpleNamespace(strip_gloss=lambda t:re.sub(r'\{\{.*?\}\}','',t)),'DONOR':{'t':('Bring a pipe, and then they left.','ac4047d887b8'),'k':('Their brains began alike.','b6329f1b0c07')},'_DON':{},'LAST':{},'SENT_FP':{},'SENT_KEYS':{},'VOIDED':[],'ENDING':{},'SYNTH_PUNCT':{},'TITLE_GRAFT':[],'_EJ':{}}
 clean_ns={'np':np,'SR':24000,'WIN':240}
 exec(compile(ast.Module(body=[n for n in clean_tree.body if isinstance(n,ast.FunctionDef)],type_ignores=[]),str(T/'clean.py'),'exec'),clean_ns)
 ns['clean_tail']=clean_ns['clean_tail']
 exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef)],type_ignores=[]),str(T/'make_video.py')+'#original-functions-only','exec'),ns)
 exec(source[source.index('# 朗读用的数字读法'):source.index('def say(t):')],ns)
 sent=' '.join(re.sub(r'\{\{.*?\}\}','',c['en']).replace('**','').strip() for c in d['sentences'][si-1]['chunks'])
 lab='S'+str(si)
 for name,key in [('INSERT_AT','停顿插入点'),('DEL_AT','停顿删除区间')]:ns[name]={sent:{int(k):v for k,v in d.get(key,{}).get(lab,{}).items()}}
 for name,key in [('NONVOICE','非人声区间'),('GRAFT','词尾除阻'),('PGRAFT','停顿处除阻'),('BOOST','除阻加强')]:ns[name]={sent:d[key][lab]} if lab in d.get(key,{}) else {}
 ns['VFP']={sent:d['区间声音指纹'][lab]} if lab in d.get('区间声音指纹',{}) else {}
 ns['SENT_NO']={sent:d['no']};ns['LIST_AT']={}
 if lab in d.get('列举逗号',{}):
  marks=[m.start() for m in re.finditer(r'[,;:](?=\s)',sent)];ns['LIST_AT'][sent]={marks[i-1] for i in d['列举逗号'][lab]}
 ns.update({'F5':120,'HP':ss.butter(6,2000,'highpass',fs=24000,output='sos'),'LP8':ss.butter(6,800,'lowpass',fs=24000,output='sos'),'ss':ss,'TH_HF':-36.,'TH_P':-33.,'CEN_MIN':1000,'DUR_MAX':110,'LF_MAX':-20.,'PER_MAX':.6})
 names={'frames_back','release','centroid','lf_peak','periodicity','双爆破','judge','finals'}
 exec(compile(ast.Module(body=[n for n in atree.body if isinstance(n,ast.FunctionDef) and n.name in names],type_ignores=[]),str(T/'词尾辅音核对.py')+'#original-pure-functions','exec'),ns)
 return ns,sent

def sentence(ns,sent):
 spans=[];p0=0;gaps=[];lst=ns['list_commas'](sent)
 for m in re.finditer(r'[,;:](?=\s)',sent):spans.append((p0,m.end()));p0=m.end()+1;gaps.append(.2 if m.start() in lst else .4)
 spans.append((p0,len(sent)))
 clips,tmap=ns['sentence_audio'](sent,spans,gaps);out=np.concatenate(clips);lengths=[len(c) for c in clips]
 starts=[sum(lengths[:2*g+1]) for g in range(len(ns['LAST']['cuts']))]+[len(out)]
 return out,starts,tmap,dict(ns['LAST'])
def measure(ns,out,P):
 F=120;n=len(out)//F;ref=float(np.sqrt(np.mean(np.asarray(out[:n*F],float).reshape(n,F)**2,axis=1)).max());hp=ss.sosfiltfilt(ns['HP'],out.astype(float));z=ns['release'](out,hp,P,ref);db=ns['双爆破'](out,hp,z,ref)
 return {'P_samples':P,'P_seconds_in_sentence':P/24000,'release':z,'release_original_A21_pass':bool(ns['judge'](out,z,ns['test_ph'])),'double_release':db,'reference_rms_5ms':ref,'first_release_metrics':None if z is None else {'centroid_hz':ns['centroid'](out,*z[3]),'periodicity':ns['periodicity'](out,*z[3]),'low_800hz_peak_db':ns['lf_peak'](out,*z[3])}}

def main():
 results=[]
 for no,si,gi,ph in [('15',8,0,'t'),('17',1,-1,'k'),('18',6,1,'t'),('30',9,0,'t')]:
  folder=O/no;d=json.loads((folder/'files'/f'{no}-failed-working-source.json').read_text());ns,sent=scope_for(d,si);ns['test_ph']=ph
  out,starts,tmap,last=sentence(ns,sent);g=gi if gi>=0 else len(starts)-1;P=starts[g];native=measure(ns,out,P)
  phases=[]
  for ds in [-120,-60,0,60,120]:
   if 0<P+ds<=len(out):phases.append({'endpoint_offset_ms':ds/24,**measure(ns,out,P+ds)})
  # Original checker nograft algorithm, isolated memory only, never a source edit.
  keep=ns['GRAFT'];pg=ns['PGRAFT'];ns['GRAFT']={};ns['PGRAFT']={}
  plain,pstarts,_,_=sentence(ns,sent);plain_result=measure(ns,plain,pstarts[g]);ns['GRAFT']=keep;ns['PGRAFT']=pg
  rec={'article':no,'sentence':'S'+str(si),'spoken_English':sent,'word':ns['finals'](last['toks'])[g],'target_punctuation_index':g+1 if gi>=0 else 'sentence-end','current_source_sha256':sha((folder/'files'/f'{no}-failed-working-source.json').read_bytes()),'cache_only_source_functions':{'maker_sha256':sha(source.encode()),'clean_sha256':sha(clean.encode()),'original_A21_sha256':sha(a21.encode())},'diagnostic_reconstruction_not_actual_new_MP4':True,'current_native_precheck_reproduction':native,'endpoint_phase_results':phases,'original_nograft_diagnostic':plain_result,'sentence_length_seconds':len(out)/24000,'starts_seconds':[p/24000 for p in starts],'original_LAST_scalar_timing':{key:last[key] for key in ['head','segs','total','cuts','grafts','gaps','hs']},'private_cache_waveform_exported':False}
  (folder/'cache-only-A21-reproduction.json').write_text(json.dumps(rec,ensure_ascii=False,indent=2,default=lambda v:float(v) if isinstance(v,np.floating) else int(v))+'\n');print(no,json.dumps(native),flush=True)
  results.append(rec)
 (O/'original-native-cache-scalar-provenance.json').write_text(json.dumps({'repository_commit':PIN,'cache_entries':list(cache_rows.values()),'no_raw_arrays_or_cache_bytes_exported':True},ensure_ascii=False,indent=2)+'\n')
 (O/'cache-only-A21-reproduction-summary.json').write_text(json.dumps({'purpose':'Reproduce exact original native prechecks from verified original unprocessed cache; no new MP4 or acceptance claim','quality_acceptance':False,'articles':results},ensure_ascii=False,indent=2,default=lambda v:float(v) if isinstance(v,np.floating) else int(v))+'\n')
if __name__=='__main__':main()
