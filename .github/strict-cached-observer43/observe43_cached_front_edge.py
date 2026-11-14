#!/usr/bin/env python3
"""Only the missing cached43S16 w0.98–1.35 word-tail front-edge observation.
No TTS inference, alternative cut search, source/CF/core writing, or acceptance.
"""
import argparse,ast,copy,hashlib,importlib.util,json,os,re,shutil,subprocess,sys,tempfile
from pathlib import Path
import numpy as np

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def arrsha(a):return hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()
def safe(x):
 if isinstance(x,dict):return {str(k):safe(v)for k,v in x.items()}
 if isinstance(x,(list,tuple)):return[safe(v)for v in x]
 if isinstance(x,np.integer):return int(x)
 if isinstance(x,(float,np.floating)):return float(x)if np.isfinite(x)else None
 if isinstance(x,np.bool_):return bool(x)
 return x

def original_functions(path,names,namespace):
 tree=ast.parse(Path(path).read_text());nodes=[x for x in tree.body if isinstance(x,ast.FunctionDef)and x.name in names];assert{n.name for n in nodes}==set(names);exec(compile(ast.Module(body=nodes,type_ignores=[]),str(path)+'#original-functions-only','exec'),namespace)
 return {n.name:hashlib.sha256(ast.dump(n,include_attributes=False).encode()).hexdigest()for n in nodes}

def feature_rows(pristine,processed,center,ref,per,spec,sr=24000,window_start=.98,window_end=1.35):
 rows=[];step=round(.0025*sr)
 for sample in range(max(0,round(window_start*sr)),min(len(pristine)-120,round(window_end*sr))+1,step):
  x=pristine[sample:sample+120];y=processed[sample:sample+120];wide=pristine[max(0,sample-180):sample+300];centroid,low=spec(x)
  X=abs(np.fft.rfft(x*np.hanning(len(x)),n=4096))**2;f=np.fft.rfftfreq(4096,1/sr)
  rows.append({'w_start_s':sample/sr,'raw_original_frame_rms_relative_dB':20*np.log10(np.sqrt(np.mean(x*x))/(ref+1e-12)+1e-12),'post_original_fade_frame_rms_relative_dB':20*np.log10(np.sqrt(np.mean(y*y))/(ref+1e-12)+1e-12),'changed_energy_relative_dB':20*np.log10(np.sqrt(np.mean((x-y)**2))/(ref+1e-12)+1e-12),'centroid_Hz':centroid,'below150Hz_energy_dB':low,'above4kHz_energy_fraction':float(X[f>4000].sum()/(X.sum()+1e-30)),'original_periodicity_20ms':per(wide)})
 return rows

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--tools',type=Path,required=True);p.add_argument('--video-root',type=Path,required=True);p.add_argument('--source','--request',dest='source',type=Path,required=True);p.add_argument('--failure-status',type=Path,required=True);p.add_argument('--reference-preparation',type=Path,required=True);p.add_argument('--cache-contract',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--window-start',type=float,default=.98);p.add_argument('--window-end',type=float,default=1.35);a=p.parse_args()
 T=a.tools.resolve();M=a.video_root.resolve();out=a.output.resolve();source=a.source.resolve();status=json.loads(a.failure_status.read_text());data=json.loads(source.read_text());contract=json.loads(a.cache_contract.read_text());prep=json.loads(a.reference_preparation.read_text());assert a.window_start==.98 and a.window_end==1.35;assert os.environ.get('XG_NOPUSH')=='1';os.environ['STRICT_CACHE']='1';os.environ['AUDIO_ONLY']='1';os.environ.pop('OLD_IV_VOID',None)
 assert sha(a.failure_status)=='344d52007e32b8ac060d7de4178e8294ff76f788ce30ecca68b366163aa2430f'and sha(a.reference_preparation)=='b34e1de12fdd0b49e97226ed1b3502937b59c7a9af395722d15aadd1318d9e5c';assert sha(source)=='bacc7abafe824031e0d85349f80327b66947839472008a18bd679cf6cdc3b53e';assert sha(a.cache_contract)=='9d133939b08a08b78cb6810028708618b92a2f2449cf56a67bd9b82506887b79';assert sha(T/'make_video.py')=='23d886be9cf999eabc682159e1ab2fc2cf6c4ccb0597f32d60d5e90a34606c0e';assert str(data['no'])=='43'
 sent=' '.join(re.sub(r'\{\{.*?\}\}|\*\*','',c['en']).strip()for c in data['sentences'][15]['chunks']);assert sent=='Apple, he later said, had been weeks from ruin.';assert data['朗读删逗号']['S16']=={'篇号':43,'原文':sent,'逗号序号':[1]}
 for key in ('非人声区间','词尾除阻','除阻加强','停顿插入点','停顿删除区间','停顿处除阻','分段增益dB','段内渐变dB','句子增益dB','分段包络dB','结尾句'):assert not data.get(key,{}).get('S16')
 lines=[line for group in status.get('failure_details',{}).get('public_checker_diagnostics',{}).values()for line in group if '43 S16 BAD' in line and 'said,'in line];assert len(lines)==1;line=lines[0];ratios=re.search(r'段长比 前 ([\d.]+) 后 ([\d.]+)',line);assert ratios;prior_ratios=list(map(float,ratios.groups()));assert'停顿 1.295–1.295s'in line
 case=next(c for c in contract['case_evidence']if c['source_id']==43 and c['sentence']=='S16');cache=M/'tts/cache_tts';assert cache.is_dir();input_paths=[source,a.failure_status.resolve(),a.reference_preparation.resolve(),a.cache_contract.resolve()];input_before={str(x):sha(x)for x in input_paths};tool_before={x:sha(T/x)for x in ['make_video.py','clean.py','停顿位置精确核对.py','可闻声保全核对.py','纯人声核对.py','标点停顿核对.py']};cache_stats={x.name:(x.stat().st_size,x.stat().st_mtime_ns)for x in cache.iterdir()if x.is_file()}
 report={'kind':'actual-strict-cached43S16-missing-front-edge-window-supplement','diagnostic_only':True,'completed':False,'audio_or_video_accepted':False,'subjective_listening_claimed':False,'new_TTS_inference':False,'alternative_cut_search_performed':False,'source_or_CF_or_core_mutated':False,'actual_prior_failure_line':line,'actual_source_SHA256':sha(source),'actual_failed_native_run':43649061154,'tool_SHA256':tool_before,'selected_cached_mothers':[],'supplemental_window_w_s':[.98,1.35],'original_observer_report_SHA256':'2670fa48498f01dc4010edbb751d21ad14ea53ee45f1eb3794ebd30a9033e786','whole_replay_or_4K_performed':False}
 private=M/'source43-current-boundary-observer';W=private/'video';W.mkdir(parents=True,exist_ok=True);(W/'scripts').mkdir(exist_ok=True)
 if not(private/'tts').exists():(private/'tts').symlink_to(M/'tts',target_is_directory=True)
 assert(private/'tts').resolve()==(M/'tts').resolve()
 if not(W/'fonts').exists():(W/'fonts').symlink_to(T/'fonts',target_is_directory=True)
 subprocess.run([sys.executable,str(T/'出片指纹.py'),'--拷',str(W)],check=True,capture_output=True,text=True)
 for name in ('读音改正.json','按语境读音.json'):
  actual=M/'video'/name;assert actual.is_file();shutil.copyfile(actual,W/name)
 shutil.copyfile(source,W/'scripts/43.json');os.chdir(W);os.environ['TMPDIR']=str(private/'tmp');Path(os.environ['TMPDIR']).mkdir(exist_ok=True);tempfile.tempdir=None;sys.path.insert(0,str(W));sys.path.insert(0,str(T))
 spec=importlib.util.spec_from_file_location('actual_cached43_boundary_maker',W/'make_video.py');m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m);m._SPOKEN_SOURCE_NO='43';m._REPO_CACHE=str(private/'no-public-export');assert not Path(m._REPO_CACHE).exists()
 for item in case['model_inputs']:
  q=cache/item['cache_key'];mark=Path(str(q)+'.单线程');assert q.is_file()and mark.is_file()and sha(q)==item['cache_PKL_SHA256']and sha(mark)==item['single_thread_marker_SHA256'];m._条目核对(str(q));report['selected_cached_mothers'].append({'key':q.name,'PKL_SHA256':sha(q),'marker_SHA256':sha(mark)})
 for obj,method in ((m.k,'create'),(m.KT,'create_timed')):
  actual=getattr(obj,method)
  def strict_only(*args,_actual=actual,**kw):
   assert os.environ.get('STRICT_CACHE')=='1','Observer cannot call a model outside strict cache';return _actual(*args,**kw)
  setattr(obj,method,strict_only)
 try:
  # These are the exact two recording hooks used by the original checker;
  # numerical producer code and source files are unchanged.
  maker=(W/'make_video.py').read_text().split('if __name__')[0];hook="    XF_OUT=float(os.environ.get('XF_OUT','0.06'))";hook2='    clips=[];tmap=[];t=0.0;prev=0;segs=[];pgts=[]\n';assert maker.count(hook)==maker.count(hook2)==1;instrumented=maker.replace(hook,"    _LOG.extend([(c_[0],c_[1]) for c_ in cuts])\n"+hook).replace(hook2,'    _W.append(w)\n'+hook2,1);node=next(n for n in ast.parse(instrumented).body if isinstance(n,ast.FunctionDef)and n.name=='sentence_audio');m._LOG=[];m._W=[];exec(compile(ast.Module(body=[node],type_ignores=[]),str(T/'make_video.py')+'#original-pause-checker-record-hooks','exec'),m.__dict__)
  marks=m._speech_marks(sent);assert len(marks)==1;pieces=[(0,marks[0].end()),(marks[0].end()+1,len(sent))];clips,tm=m.sentence_audio(sent,pieces,[.4]);post=m._W[0];last=copy.deepcopy(m.LAST);raw,sr=m.k.create(m.spoken(sent),voice=m.V,speed=m.SPEED,lang='en-us');tb,_,sp=m.KT.create_timed(m.spoken(sent),voice=m.V,speed=m.SPEED,lang='en-us',clause_pause=0,sentence_pause=0);tokens=list(sp);assert sr==24000
  pristine=m.clean_tail(raw);pristine=m._keep_tail(raw,pristine,m._head_offset(raw,pristine));assert m.SENT_FP[sent]==case['actual_raw_fingerprint']and [list(x)for x in tm]==case['actual_processed_tmap']and last['cuts']==[tuple(x)for x in case['actual_processed_cuts']]
  output=np.concatenate(clips);pv={'np':np,'SR':m.SR,'F5':int(.005*m.SR),'AUD_DB':m.AUD_DB};pv_ast=original_functions(T/'可闻声保全核对.py',{'lost_frames','check_sentence'},pv);pvbad=pv['check_sentence']('S16',raw,output,last['head'],last['segs'],(),last['toks'],last['scale'],int(round(-last['segs'][0][2]*m.SR)))
  P={'np':np};position_ast=original_functions(T/'停顿位置精确核对.py',{'logmel','dtw_map','确认可收'},P);mp,cost=P['dtw_map'](P['logmel'](np.asarray(tb,float)),P['logmel'](np.asarray(post,float)));tow=lambda t:float(np.interp(t*100,np.arange(len(mp)),mp))/100;idx=[i for i,x in enumerate(tokens)if x.phoneme in',;:'];assert len(idx)==1;i=idx[0];nonsound=set(',;:.!?"\'“”‘’()[]—–-…');prv=next(x for x in reversed(tokens[:i])if x.phoneme.strip()and x.phoneme not in nonsound);nxt=next(x for x in tokens[i+1:]if x.phoneme.strip()and x.phoneme not in nonsound);pe,ns=tow(prv.start),tow(nxt.start);ca,cb=m._LOG[0];a0,b0=ca/m.SR,cb/m.SR;assert a0==b0==1.295
  # Only reference entries physically present and SHA-bound to the actual
  # successful prep may be reread. Missing refs cause no model invocation.
  refs=[r for r in prep['reference_calls']if r['sentence']=='S16'and r['reference_kind']=='pause-punctuation-slice'];manifest={r['exact_native_cache_key']:r for r in prep['raw_mother_cache_scalar_manifest']};ready=all((cache/r['exact_native_cache_key']).is_file()and sha(cache/r['exact_native_cache_key'])==manifest[r['exact_native_cache_key']]['pkl_sha256']for r in refs);ratio_evidence={'prior_actual_checker_rounded_values':prior_ratios,'fresh_ratio_recomputed':False,'missing_reference_is_not_audio_failure':True}
  if ready:
   ratios=[(t1-t0)/(len(m.say(m._speech_piece(sent,x0,x1)))/m.SR)for x0,x1,t0,t1 in tm];ratio_evidence.update(fresh_ratio_recomputed=True,actual_values=ratios)
  else:ratios=prior_ratios;ratio_evidence['unavailable_reference_keys']=[r['exact_native_cache_key']for r in refs if not(cache/r['exact_native_cache_key']).is_file()]
  constants={};checker_tree=ast.parse((T/'停顿位置精确核对.py').read_text());need={'TOL','RLO','RHI'}
  for node0 in checker_tree.body:
   if isinstance(node0,ast.Assign)and any(isinstance(q,ast.Name)and q.id in need or isinstance(q,ast.Tuple)and any(isinstance(z,ast.Name)and z.id in need for z in q.elts)for q in node0.targets):exec(compile(ast.Module(body=[node0],type_ignores=[]),'original-position-thresholds','exec'),{'os':os},constants)
  TOL,RLO,RHI=constants['TOL'],constants['RLO'],constants['RHI'];numeric_ok=a0>=pe-TOL and b0<=ns+TOL and all(RLO<r<RHI for r in ratios);g40=P['确认可收']('43',1000*(ns-b0),False,False);cf=data.get('核对确认',{}).get('停顿位置',{}).get('S16 said, / had @1.295')
  F=int(.005*m.SR);ref=float(np.sqrt(np.mean(pristine[:len(pristine)//F*F].reshape(-1,F)**2,axis=1)).max());e=m._env5(pristine);f=ca//F;lo=f;hi=f
  while lo>0 and e[lo-1]<m.AUD_DB:lo-=1
  while hi<len(e)and e[hi]<m.AUD_DB:hi+=1
  spectral={'np':np,'SR':m.SR};spectral_ast=original_functions(T/'纯人声核对.py',{'per','spec'},spectral);rows=feature_rows(pristine,post,a0,ref,spectral['per'],spectral['spec'],window_start=a.window_start,window_end=a.window_end)
  pv_mut=output.copy();loud=int(np.argmax(np.sqrt(np.mean(output[:len(output)//F*F].reshape(-1,F)**2,axis=1))))*F;pv_mut[loud:loud+F]=0;mutbad=pv['check_sentence']('S16-mutated-test',raw,pv_mut,last['head'],last['segs'],(),last['toks'],last['scale'],int(round(-last['segs'][0][2]*m.SR)))
  report['S16']={'raw_array_SHA256':arrsha(raw),'pristine_cleaned_w_SHA256':arrsha(pristine),'original_processed_sentence_SHA256':arrsha(output),'raw_fingerprint':m.SENT_FP[sent],'head_samples_original_raw_to_w':last['head'],'current_cut_w_samples':[ca,cb],'current_cut_w_s':[a0,b0],'current_cut_original_model_raw_s':[(last['head']+ca)/m.SR,(last['head']+cb)/m.SR],'actual_tmap':tm,'original_fade_sample_ranges_in_raw':last['fades'],'original_cuts':last['cuts'],'actual_prior_checker_line':line,'actual_numeric_position':{'previous_phoneme':prv.phoneme,'previous_phoneme_start_w_s':pe,'next_phoneme':nxt.phoneme,'next_phoneme_start_w_s':ns,'position_numeric_pass':a0>=pe-TOL and b0<=ns+TOL,'original_TOL':TOL,'original_ratio_range':[RLO,RHI],'numeric_initial_filter_pass':numeric_ok,'DTW_cost':cost,'G40_accepts_this_positive_distance':g40},'ratio_evidence':ratio_evidence,'mandatory_new_insertion_record_currently_present':bool(cf),'original_kind_insertion_requires_independent_boundary_record':True,'original_pause_checker_final_pass_not_claimed':True,'original_PV_bad_rows':pvbad,'original_PV_loud_5ms_zero_negative_detected':bool(mutbad),'negative_mutation_bad_rows':mutbad,'threshold':{'original_AUD_DB':m.AUD_DB,'cut_frame_relative_dB':float(e[f]),'frame_before_cut_relative_dB':float(e[f-1]),'frame_after_cut_relative_dB':float(e[f+1]),'contiguous_quiet_interval_touching_cut_w_s':[lo*.005,hi*.005]},'actual_timed_tokens_near_boundary':[{'phoneme':x.phoneme,'timed_start_s':x.start,'timed_end_s':x.end,'DTW_start_w_s':tow(x.start),'DTW_end_w_s':tow(x.end)}for x in tokens if abs(tow(x.start)-a0)<.25 or abs(tow(x.end)-a0)<.25],'actual_2p5ms_spectrum_envelope_rows':rows,'original_function_AST_SHA256':{**pv_ast,**position_ast,**spectral_ast},'alternative_cut_or_CF_proposed_or_applied':False}
  report['completed']=True
 except BaseException as exc:report['error']={'type':type(exc).__name__,'detail':str(exc)};raise
 finally:
  report['source_status_and_reference_files_still_exact']=all(sha(Path(k))==v for k,v in input_before.items());report['original_tool_files_still_exact']=all(sha(T/k)==v for k,v in tool_before.items());after={x.name:(x.stat().st_size,x.stat().st_mtime_ns)for x in cache.iterdir()if x.is_file()};report['normal_cache_entries_unchanged']=after==cache_stats;assert report['source_status_and_reference_files_still_exact']and report['original_tool_files_still_exact']and report['normal_cache_entries_unchanged'];out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(safe(report),ensure_ascii=False,indent=2)+'\n');print(json.dumps({'completed':report['completed'],'output':str(out),'formal_audio_acceptance':False},ensure_ascii=False))
if __name__=='__main__':main()
