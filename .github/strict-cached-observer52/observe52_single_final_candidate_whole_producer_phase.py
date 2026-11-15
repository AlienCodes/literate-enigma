#!/usr/bin/env python3
"""One exact source52 private final-candidate build. Never builds a baseline.
Disabled until sole owner binds and approves the observed S18 first-zero report.
No model inference, G36 calculation, confirmation renewal or formal acceptance.
"""
import argparse,ast,copy,gc,hashlib,importlib.util,json,os,re,subprocess,sys,tempfile,wave
from pathlib import Path
import numpy as np
import soundfile as sf
HERE=Path(__file__).resolve().parent
MAKER='23d886be9cf999eabc682159e1ab2fc2cf6c4ccb0597f32d60d5e90a34606c0e'
REQUEST='c00eb5707f1b269d2ce88fed455f592962d674d46e3bf172ba00cfe6597245f3'
BASE='55594624daca4a4601146e4cb1822e813782e14e1cdc0a5e65774e8602045822'
CONTRACT='9d133939b08a08b78cb6810028708618b92a2f2449cf56a67bd9b82506887b79'
MATHNAME='调平_5d2d6bab45b9b765994454b448b0cfc3c61dde90.json'
MATHSHA='44136fa355b3678a1146ad16f7e8649e94fb4fc21fe77e8310c060f61caaff8a'
PINNED_FP={'S4':'f2954ac315f1','S18':'88dadf11eead'}
PRODUCER_PHASE='5c4a2e62624ade5d119086c9525a8d90588efc7507fdbdd04678219dd8f4a156'
CALLER_PROOF='fca5492b070d5f6cd62503ec8d84464b428501dadd08f442647b6899c0f4ac16'
LOCAL_PROOF='696f92b6d9fa74e461c5b6defec09b5616e9e972e7ef2aa75e8ac4ded2f380f2'
def producer_phase_records(first,baseline,caller,local):
 assert first['passed']is True and first['models_still_exact']is True and first['existing_normal_cache_files_stat_unchanged']is True and first['original_source_GEN_baseline_files_still_exact']is True
 assert REQUEST in [v for k,v in first['source_input_sha256'].items()if k.endswith('/52.json')]
 row=next(z for z in first['cases']if z['source_id']==52)['candidate']
 assert row['raw_WAV_sha256']=='ad119eca768315a636608cf88a4220ed717c5866a9e46aa0ba20b0806dc360c5'and row['AAC_ADTS_sha256']=='2491cfa8ab9262bd313fc224e48f1816e65cd562cb2c91fb01f5e48bc25ac29d'
 last=baseline['cases'][-1];current=baseline['cases'][0]
 assert current['whole_WAV_sha256']==row['raw_WAV_sha256']and current['whole_AAC_ADTS_sha256']==row['AAC_ADTS_sha256']
 assert caller['observation_completed']is True and caller['whole_build_count']==0 and caller['intentional_stop_at_S3_original_gain_return']is True
 assert caller['all_private_cache_stats_and_keys_unchanged']and caller['all_models_byte_exact_after']and caller['all_input_and_tools_byte_exact_after']
 assert local['observation_completed']is True and local['hard_comparisons']['post_native_bytes_matches_actual555']is True and local['original_master_quantization_S3_only']['exact_actual555_quantized_S3']is True
 original=row['sentence_pre_master_records'];expected={};proof={};different=[]
 for sid in ['title']+[f'S{k}'for k in range(1,18)]:
  old=last['sentence_records'][sid]
  if sid=='S4':
   expected[sid]={'samples':old['samples'],'post_float32_SHA256':old['pre_master_float32_sha256'],'role':'actual555 newS4 NV mother, unchanged by conservativeS18'};continue
  q=original[sid];assert q['samples']==old['samples']
  if sid!='title':
   assert q['before_gain_float32_SHA256']==old['before_gain_float32_sha256']and same([{'samples':c['samples'],'sha256':c['SHA256']}for c in q['before_gain_clips']],old['before_gain_clips'])
   for left,right in [('tmap','tmap'),('gaps','gaps'),('cuts','cuts'),('raw_fingerprint','raw_fingerprint'),('automatic_level','automatic_level'),('manual_segment_level','manual_segment_level')]:assert same(q[left],old[right]),sid+' historical control or mother mismatch'
  expected[sid]={'samples':q['samples'],'post_float32_SHA256':q['pre_master_float32_SHA256'],'role':'actual5c4 original build c00 producer-context phase; source control and mother exact to555'}
  proof[sid]={'actual5c4_post':q['pre_master_float32_SHA256'],'actual555_post':old['pre_master_float32_sha256'],'actual555_original_float_lineage_retained':True,'historical_full_current_WAV_AAC_double_identity':True}
  if q['pre_master_float32_SHA256']!=old['pre_master_float32_sha256']:different.append(sid)
 assert different==['S3','S5','S6'],'Unrecognized phase difference; no arbitrary alternate hashes'
 c=caller['actual_S3_caller_before_gain'];a=caller['actual_S3_caller_after_gain'];l=local['S3_after_gain']
 assert c['no']=='52'and c['si']==2 and c['array']['SHA256']==last['sentence_records']['S3']['before_gain_float32_sha256']and c['S3_source_controls']=={}
 assert a['array']['SHA256']==a['concatenated_returned_clips']['SHA256']==expected['S3']['post_float32_SHA256']
 ct=a['actual_original_tail'][0];lt=l['original_tail_operations'][0]
 assert ct['input']['SHA256']==lt['input']['native_bytes_SHA256']=='8d3214f0c52f137ec64745435c03d2429dc67ec8a3477585bd0ce7bc69ed4c21'and ct['changed_sample_count']==lt['changed_sample_count']==1199
 assert a['normalized_PCM16_float64']['SHA256']==local['original_master_quantization_S3_only']['decoded_float64_SHA256']==last['old_to_current_actual_sentence_PCM_identity']['S3']['new_quantized_float64_sha256']=='325a4b3b8fcf0e46aaae895867c19ef57804ee0f016b0ed9aba28ad3cb7ec805'
 return expected,proof,different

def sha(path):
 h=hashlib.sha256()
 with Path(path).open('rb')as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
def arrsha(a):return hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def same(a,b):return json.dumps(a,ensure_ascii=False,sort_keys=True)==json.dumps(b,ensure_ascii=False,sort_keys=True)
def safe(x):
 if isinstance(x,dict):return {str(k):safe(v)for k,v in x.items()}
 if isinstance(x,(tuple,list)):return [safe(v)for v in x]
 if isinstance(x,np.bool_):return bool(x)
 if isinstance(x,np.integer):return int(x)
 if isinstance(x,(float,np.floating)):return float(x)if np.isfinite(x)else None
 return x
def bare(d):return [d['title_en']]+[' '.join(re.sub(r'\*\*|\{\{.*?\}\}','',c['en']).strip()for c in s['chunks'])for s in d['sentences']]
def load(name,path):
 sp=importlib.util.spec_from_file_location(name,path);v=importlib.util.module_from_spec(sp);sys.modules[name]=v;sp.loader.exec_module(v);return v

def edge_binding_valid(e,r):
 if not(e.get('diagnostic_only')is True and e.get('completed')is True and e.get('audio_or_video_accepted')is False and e.get('actual_prior555946_report_sha256')==BASE):return False
 for k in ['whole_audio_reconstructed','new_model_inference','new_G36_math_or_cache','parameter_sweep_performed','source_or_CF_or_production_controls_modified']:
  if e.get(k)is not False:return False
 z=e.get('single_selected_first_zero',{});i=z.get('first_real_zero_sample')
 if not(isinstance(i,int)and not isinstance(i,bool)and 65100<=i<=65160 and z.get('allowed_sample_interval_inclusive')==[65100,65160]and z.get('original_end_sample')==72360 and z.get('one_candidate_only_not_parameter_sweep')is True and z.get('first_real_zero_w_seconds')==i/24000):return False
 rows=[x for x in e.get('cases',[])if x.get('stage')=='conservative_first_zero']
 if len(rows)!=1:return False
 q=rows[0]
 return (q.get('S18_NV_only')==[i/24000,3.015,'紧贴词尾']and q.get('new_mother_data_binding')==PINNED_FP['S18']and q.get('processed_float32_sha256')==r.get('expected_S18_processed_float32_SHA256')and q.get('processed_samples')==r.get('expected_S18_processed_samples')and q.get('pristine_w_sha256')==r.get('expected_S18_pristine_w_SHA256')and q.get('original_NV_guard_passed')is True and q.get('original_NV_endpoint',{}).get('real_left_zero_crossing')is True and q.get('original_NV_endpoint',{}).get('samples')==[i,72360]and q.get('all_samples_outside_NV_directly_exact')is True and q.get('disputed_2p710_to2p7125_original_peak_final_processed_samples_exact')is True and q.get('peak_mapping_all_samples_present')is True and q.get('peak_pristine_sha256')==q.get('peak_processed_sha256')==r.get('expected_preserved_peak_SHA256')and q.get('original_audible_preservation_failures')==[]and bool(q.get('original_audible_preservation_loud5ms_zero_negative_rows'))and e.get('all_private_cache_file_stats_unchanged')is True and e.get('input_files_byte_exact_after')is True)

def main():
 ap=argparse.ArgumentParser(description=__doc__)
 ap.add_argument('--reference',type=Path,default=HERE/'disabled-reference-PENDING.json')
 for key in ['tools','video-root','request-source','baseline-report','mother-contract','edge-report','producer-phase-reference','caller-phase-proof','local-phase-proof','output']:ap.add_argument('--'+key,type=Path,required=True)
 a=ap.parse_args();r=read(a.reference);out=a.output.resolve();report={'kind':'source52-single-final-private-candidate-whole-original-cache-observer','diagnostic_only':True,'formal_audio_or_video_accepted':False,'production_delivery_eligible':False,'whole_build_count':0,'baseline_rebuilt':False,'new_model_inference':False,'new_G36_math_or_cache':False,'production_source_or_CF_written':False,'completed':False,'program_SHA256':sha(__file__),'reference_SHA256':sha(a.reference)}
 # This refusal is deliberately before model imports, source/cache access or owned W creation.
 if r.get('enabled')is not True or not r.get('edge_report_SHA256'):
  report['refused']='Profile disabled or actual edge report not bound; no audio/model/source/cache operation performed.'
  out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');return 2
 T=a.tools.resolve();M=a.video_root.resolve();inputs=[a.reference,a.request_source,a.baseline_report,a.mother_contract,a.edge_report,a.producer_phase_reference,a.caller_phase_proof,a.local_phase_proof]
 assert r.get('article')=='52'and r.get('expected_request_SHA256')==REQUEST and r.get('expected_baseline_report_SHA256')==BASE and r.get('expected_mother_contract_SHA256')==CONTRACT
 for p,h in [(T/'make_video.py',MAKER),(a.request_source,REQUEST),(a.baseline_report,BASE),(a.mother_contract,CONTRACT),(a.edge_report,r['edge_report_SHA256']),(a.producer_phase_reference,PRODUCER_PHASE),(a.caller_phase_proof,CALLER_PROOF),(a.local_phase_proof,LOCAL_PROOF)]:assert sha(p)==h
 assert r['producer_phase_reference_SHA256']==PRODUCER_PHASE and r['caller_phase_proof_SHA256']==CALLER_PROOF and r['local_phase_proof_SHA256']==LOCAL_PROOF
 edge=read(a.edge_report);assert edge_binding_valid(edge,r),'Exact approved first-zero evidence or preserved-peak binding failed'
 i=edge['single_selected_first_zero']['first_real_zero_sample'];s18row=next(x for x in edge['cases']if x['stage']=='conservative_first_zero')
 baseline=read(a.baseline_report);assert baseline['observation_completed']is True and baseline['diagnostic_only']is True and baseline['audio_or_video_accepted']is False
 last=baseline['cases'][-1];assert last['stage']=='candidate_twoNV'and last['whole_WAV_sha256']=='e75598471ff617384aff07e4ec29eed3a389bd75aae3bb2d4bd9668dafd4debf'
 assert last['master_pre_peak']==r['expected_master_pre_peak']==0.8474143147468567
 expected_phase,phase_proof,known_float_differences=producer_phase_records(read(a.producer_phase_reference),baseline,read(a.caller_phase_proof),read(a.local_phase_proof))
 data=read(a.request_source);assert str(data['no'])=='52'and len(data['sentences'])==18 and not data.get('结尾句',{}).get('S18')
 candidate=copy.deepcopy(data);nv={'S4':[[4.985,5.2185,'紧贴词头']],'S18':[[i/24000,3.015,'紧贴词尾']]}
 for sid,ivs in nv.items():
  assert sid not in candidate.get('非人声区间',{})and sid not in candidate.get('区间声音指纹',{})
  candidate.setdefault('非人声区间',{})[sid]=ivs;candidate.setdefault('区间声音指纹',{})[sid]=PINNED_FP[sid]
 reduced=copy.deepcopy(candidate)
 for sid in nv:del reduced['非人声区间'][sid];del reduced['区间声音指纹'][sid]
 assert same(reduced,data)and bare(candidate)==bare(data)and candidate['核对确认']==data['核对确认']
 assert os.environ.get('STRICT_CACHE')=='1'and os.environ.get('XG_NOPUSH')=='1'
 assert not any(os.environ.get(k)for k in ['VOICE','AFFILE','OLD_IV_VOID'])
 contract=read(a.mother_contract);cache=M/'tts/cache_tts';assert cache.is_dir()
 models_before={n:sha(M/'tts'/n)for n in contract['models']};assert models_before==contract['models']
 cache_before={p.name:(p.stat().st_size,p.stat().st_mtime_ns)for p in cache.iterdir()if p.is_file()};input_before={str(p):sha(p)for p in inputs}
 assert sha(cache/MATHNAME)==r['required_S4_G36_JSON_SHA256']==MATHSHA and read(cache/MATHNAME)=={}
 # Actual selected raw/timed mothers retain their original SHA and single-thread marker checks.
 for case in contract['case_evidence']:
  if case['source_id']==52:
   for item in case['model_inputs']:
    assert sha(cache/item['cache_key'])==item['cache_PKL_SHA256']and sha(cache/(item['cache_key']+'.单线程'))==item['single_thread_marker_SHA256']
 oldcwd=Path.cwd();oldpath=list(sys.path);envkeys=['AUDIO_ONLY','TMPDIR'];oldenv={k:os.environ.get(k)for k in envkeys};ns=None;arrays={};records={};rawaudio=None
 toolfiles={str(T/n):sha(T/n)for n in ['make_video.py','纯人声核对.py','响度一致性核对.py','音频体检.py','音频体检基准.json']}
 # All unique media/W live in owned temporary storage; shared production W is never opened for writing.
 with tempfile.TemporaryDirectory(prefix='source52-single-final-private-',dir=M)as td:
  PR=Path(td);W=PR/'video';(W/'scripts').mkdir(parents=True);(PR/'tts').symlink_to(M/'tts',target_is_directory=True);assert (PR/'tts').resolve()==(M/'tts').resolve()
  source=W/'scripts/52.json';source.write_text(json.dumps(candidate,ensure_ascii=False,indent=2)+'\n')
  assert sha(source)==r['expected_candidate_source_SHA256'],'Private candidate bytes differ from sole source-writer frozen JSON'
  os.environ['AUDIO_ONLY']='1';os.environ['TMPDIR']=str(PR/'tmp');Path(os.environ['TMPDIR']).mkdir();tempfile.tempdir=None
  try:
   os.chdir(W);sys.path[:0]=[str(T),str(W)]
   ns={'__name__':'source52_single_final_private','__file__':str(T/'make_video.py')}
   exec(compile((T/'make_video.py').read_text().split('if __name__')[0],str(T/'make_video.py')+'#unchanged-private-single-candidate','exec'),ns)
   ns['_SPOKEN_SOURCE_NO']='52';assert ns['SENT_NO'].get(bare(candidate)[4])=='52'
   for obj,name in [(ns['k'],'create'),(ns['KT'],'create_timed')]:
    original=getattr(obj,name)
    def model_guard(*ar,_fn=original,**kw):
     assert os.environ.get('STRICT_CACHE')=='1','No model call outside original STRICT'
     return _fn(*ar,**kw)
    setattr(obj,name,model_guard)
   original_level=ns['_auto_level'];tree=ast.parse((T/'make_video.py').read_text());fn=next(x for x in tree.body if isinstance(x,ast.FunctionDef)and x.name=='_auto_level');expr=next(x.value for x in fn.body if isinstance(x,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='_k'for t in x.targets));state={'sid':None,'n':0};levels=[]
   def level_guard(clips,tmap,gaps,no='',rounds=2):
    assert os.environ.get('STRICT_CACHE')=='1'and str(no)=='52'and rounds==2
    key=eval(compile(ast.Expression(body=expr),'original-G36-cache-key-only','eval'),ns,dict(clips=clips,tmap=tmap,gaps=gaps,no=no));name='调平_'+key+'.json'
    assert (cache/name).is_file(),'Missing stored original G36; no derivation is permitted'
    if state['sid']=='S4':assert name==MATHNAME and sha(cache/name)==MATHSHA and read(cache/name)=={}
    assert state['sid']!='S18','One-piece S18 must not call G36'
    result=original_level(clips,tmap,gaps,no,rounds);levels.append({'sentence':state['sid'],'name':name,'JSON_SHA256':sha(cache/name),'actual_gain':result,'no_new_math':True});return result
   ns['_auto_level']=level_guard
   title0=ns['title_audio'];sentence0=ns['sentence_audio'];gain0=ns['句增益']
   def title(text):
    z=title0(text);arrays['title']=z.copy();records['title']={'samples':len(z),'pre_master_float32_SHA256':arrsha(z)};return z
   def sentence(sent,pieces,gaps):
    state['n']+=1;sid='S'+str(state['n']);state['sid']=sid;assert sent==bare(candidate)[state['n']]
    clips,tmap=sentence0(sent,pieces,gaps);records[sid]={'before_gain_samples':sum(len(z)for z in clips),'before_gain_float32_SHA256':arrsha(np.concatenate(clips)),'before_gain_clips':[{'samples':len(z),'sha256':arrsha(z),'dtype':str(z.dtype)}for z in clips],'actual_gaps':list(gaps),'raw_w_fingerprint':ns['SENT_FP'][sent],'actual_tmap':copy.deepcopy(tmap),'actual_cuts':copy.deepcopy(ns['LAST']['cuts'])}
    if sid in PINNED_FP:assert ns['SENT_FP'][sent]==PINNED_FP[sid]
    return clips,tmap
   def gain(d,no,si,sent,pieces,gaps,clips,tmap,z):
    answer=gain0(d,no,si,sent,pieces,gaps,clips,tmap,z);sid=state['sid'];arrays[sid]=answer[1].copy();records[sid].update(samples=len(answer[1]),pre_master_float32_SHA256=arrsha(answer[1]),automatic_gain=answer[2],manual_gain=answer[3]);return answer
   ns['title_audio']=title;ns['sentence_audio']=sentence;ns['句增益']=gain
   media=PR/'single-final-private-candidate.m4a';report['whole_build_count']+=1;ns['build'](str(source),str(media));assert report['whole_build_count']==1 and state['n']==18
   assert set(arrays)=={'title'}|{f'S{i}'for i in range(1,19)}
   report.update(sentence_records_before_hard_assertions=records,actual_G36_before_hard_assertions=levels,explicit_single_producer_phase_expected=expected_phase,historical_phase_proof=phase_proof,known_historical_float_differences=known_float_differences,producer_phase_reference_SHA256=PRODUCER_PHASE,caller_phase_proof_SHA256=CALLER_PROOF,local_phase_proof_SHA256=LOCAL_PROOF)
   out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(safe(report),ensure_ascii=False,indent=2)+'\n')
   for sid in ['title']+[f'S{k}'for k in range(1,18)]:
    assert records[sid]['samples']==expected_phase[sid]['samples']and records[sid]['pre_master_float32_SHA256']==expected_phase[sid]['post_float32_SHA256'],sid+' original-producer phase pre-master changed unexpectedly'
    assert arrays[sid].dtype==np.float32,sid+' unexpected producer dtype'
    if sid!='title':
     old=last['sentence_records'][sid];now=records[sid]
     assert now['before_gain_float32_SHA256']==old['before_gain_float32_sha256']and same([{'samples':z['samples'],'sha256':z['sha256']}for z in now['before_gain_clips']],old['before_gain_clips']),sid+' before-gain mother or clip changed'
     for left,right in [('actual_tmap','tmap'),('actual_gaps','gaps'),('actual_cuts','cuts'),('raw_w_fingerprint','raw_fingerprint'),('automatic_gain','automatic_level'),('manual_gain','manual_segment_level')]:assert same(now[left],old[right]),sid+' effective producer inputs or gains changed'

   assert records['S18']['pre_master_float32_SHA256']==r['expected_S18_processed_float32_SHA256']and records['S18']['samples']==r['expected_S18_processed_samples']and records['S18']['automatic_gain']=={}and records['S18']['manual_gain']is None
   peak=max(float(np.max(np.abs(z)))for z in arrays.values());assert peak==r['expected_master_pre_peak']
   assert same(read(source),candidate),'Original private source or CF unexpectedly changed'
   rawpath=W/'work_52/a.wav';audio,sr=sf.read(rawpath,dtype='float64');assert sr==24000;groups=read(W/'work_52/分段.json');grafts=read(W/'work_52/词尾除阻.json');quantized={}
   for sid in [f'S{k}'for k in range(1,18)]:
    lo,hi=groups[sid][0]['时刻'][0],groups[sid][-1]['时刻'][1];z=audio[round(lo*sr):round(hi*sr)];h=arrsha(z);expected=last['old_to_current_actual_sentence_PCM_identity'][sid]['new_quantized_float64_sha256'];assert h==expected,sid+' quantized whole sentence changed unexpectedly';quantized[sid]={'start_s':lo,'end_s':hi,'samples':len(z),'quantized_float64_SHA256':h,'equals_actual555_final_case':True}
   # No baseline title quantized file was exported. Exact pre-master+same original M is the explicit title-preservation proof.
   report['title_preservation']={'pre_master_SHA256':records['title']['pre_master_float32_SHA256'],'equals_555_title_pre_master':True,'master_pre_peak_same':True,'quantized_identity_basis':'same actual original ordered normalization and identical title array; no fabricated direct old title crop hash'}
   PV=load('source52_single_final_original_PV',T/'纯人声核对.py');fp=hashlib.md5(rawpath.read_bytes()).hexdigest()[:12];pvrows=[]
   for f in PV.scan(audio):
    key=PV.key(f);cf=candidate.get('核对确认',{}).get('非人声',{}).get(key);match=isinstance(cf,dict)and cf.get('配音指纹')==fp;accepted,why=PV.确认可收('52',f,cf,audio)if match else(False,'original CF missing or full current fingerprint differs; no CF updated');graft=next((q for q in grafts if f[0]in('孤立杂音','噗声','呼吸声')and q['开始']-.005<=f[1]and f[2]<=q['结束']+.005),None)
    if graft:accepted=True;why='actual original A21 graft interval'
    pvrows.append({'tuple':list(f),'key':key,'actual_measurement':PV.实测(f),'original_CF_verbatim':cf,'fingerprint_matches':match,'original_confirmation_accepted':bool(accepted),'original_reason':why,'original_looks_like_breath':bool(PV.像吸气(f)),'original_graft_exemption':graft})
   adts=subprocess.check_output(['ffmpeg','-v','error','-nostdin','-i',str(media),'-map','0:a:0','-c:a','copy','-f','adts','-']);probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','a:0','-show_packets','-show_streams','-of','json',str(media)]));packets=probe['packets']
   with wave.open(str(rawpath),'rb')as wf:shape={'sample_rate':wf.getframerate(),'channels':wf.getnchannels(),'width':wf.getsampwidth(),'samples':wf.getnframes()}
   report.update(actual_private_candidate_source_SHA256=sha(source),actual_candidate_NV=nv,exact_control_scope_only_two_NV_plus_two_measured_mother_pins=True,source_confirmation_tree_exact_original_c00=True,sentence_records=records,actual_master_pre_peak=peak,actual_G36_stored_cache_reads=levels,whole_RAW={'SHA256':sha(rawpath),'bytes':rawpath.stat().st_size,'md5_first12':fp,**shape},whole_AAC={'ADTS_SHA256':hashlib.sha256(adts).hexdigest(),'ADTS_bytes':len(adts),'packet_count':len(packets),'actual_packet_clock_metadata_SHA256':hashlib.sha256(json.dumps(packets,sort_keys=True,separators=(',',':')).encode()).hexdigest(),'first_packet':packets[0]if packets else None,'last_packet':packets[-1]if packets else None,'audio_streams':probe['streams']},actual_segment_clock=groups,actual_display_chunk_timetable=(W/'work_52/list.txt').read_text(),title_and_S1_S17_pre_master_exact_to_explicit_original_producer_phase=True,all_S1_S17_before_gain_clip_tmap_rawfp_and_effective_gains_exact_to_555=True,S1_S17_actual_quantized_sentence_proof=quantized,actual_PV_all_tuples=pvrows,actual_PV_total_scan_count=len(pvrows),actual_PV_unconfirmed_count=sum(not z['original_confirmation_accepted']for z in pvrows))
   report['inherited_original_preservation_evidence_not_rerun']={'micro_report_SHA256':r['edge_report_SHA256'],'S18_micro_original_A21_failures':s18row['original_audible_preservation_failures'],'S18_micro_negative_rows':s18row['original_audible_preservation_loud5ms_zero_negative_rows'],'555_report_SHA256':BASE,'S4_original_preservation_rows':last['new_mother_observations']['S4']['original_audible_preservation_failures'],'S5_original_preservation_rows':last['new_mother_observations']['S5']['original_audible_preservation_failures'],'role':'Inherited actual original local/555 observations, not a claimed new full A21 run.'}
   try:
    RR=load('source52_single_final_R',T/'响度一致性核对.py');RR.FF='ffmpeg';Q=load('source52_single_final_Q8',T/'音频体检.py');pcm=RR.pcm(str(media));mom=RR.momentary(str(media));metrics=Q.指标(pcm,'52');notes=[];qbad=Q.超限(metrics,read(T/'音频体检基准.json'),Q.确认('52'),notes)
    alias=PR/'52.mp4';alias.symlink_to(media);I,sg,levelsR,rbad,summary=RR.check(str(alias),pcm);inside=RR.句内(str(media),pcm,mom,str(W/'work_52/分段.json'));ibad=RR.句内报(inside)
    report['original_Q8_R_withinR']={'completed':True,'Q8_metrics':metrics,'Q8_failures':qbad,'original_confirmation_notes':notes,'integrated_LUFS':I,'R_sentence_levels':levelsR,'R_failures':rbad,'R_summary':summary,'within_R_comparisons':inside,'within_R_failures':ibad,'all_passed':not qbad and not rbad and not ibad,'original_rules_unchanged':True,'official_two_ASR_not_run_here':True}
   except BaseException as ex:report['original_Q8_R_withinR']={'completed':False,'error':{'type':type(ex).__name__,'detail':str(ex)},'no_quality_acceptance':True}
   report['completed']=True
  except BaseException as ex:
   report['error']={'type':type(ex).__name__,'detail':str(ex)};raise
  finally:
   os.chdir(oldcwd);sys.path[:]=oldpath
   for k,v in oldenv.items():
    if v is None:os.environ.pop(k,None)
    else:os.environ[k]=v
   tempfile.tempdir=None
   after={p.name:(p.stat().st_size,p.stat().st_mtime_ns)for p in cache.iterdir()if p.is_file()};report['all_private_cache_stats_and_keys_unchanged']=cache_before==after;report['all_models_byte_exact_after']={n:sha(M/'tts'/n)for n in contract['models']}==models_before;report['all_input_and_tools_byte_exact_after']=all(sha(Path(p))==h for p,h in {**input_before,**toolfiles}.items());report['original_full_2ASR_gates_and_final_V3_still_required']=True
   report['private_PCM_PKL_GT_or_media_exported']=False
   out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(safe(report),ensure_ascii=False,indent=2)+'\n')
   assert report['all_private_cache_stats_and_keys_unchanged']and report['all_models_byte_exact_after']and report['all_input_and_tools_byte_exact_after']
 return 0 if report['completed']else 1
if __name__=='__main__':sys.exit(main())
