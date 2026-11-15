#!/usr/bin/env python3
"""Observe original a473 caller through S3 gain, then stop before whole/media."""
import argparse,hashlib,io,json,sys
from pathlib import Path
import numpy as np
import soundfile as sf
BASE='a473452dba8cd83e9792119f265ef06e457d1f4e076c6902a9ca0a455ac2eced'
ACTUAL='696f92b6d9fa74e461c5b6defec09b5616e9e972e7ef2aa75e8ac4ded2f380f2'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def sig(z):return {'samples':len(z),'dtype':str(z.dtype),'SHA256':hashlib.sha256(np.ascontiguousarray(z).tobytes()).hexdigest()}
def pcm16_quant(z,peak):
 b=io.BytesIO();sf.write(b,z/np.float32(peak)*0.89,24000,format='WAV',subtype='PCM_16');b.seek(0);x,_=sf.read(b,dtype='float64');return sig(x)
class PrefixComplete(BaseException):pass
def instrument(text):
 # Exact byte anchors and the immutable base SHA keep all original setup,
 # cache guards and source construction intact. Only scalar capture and stop.
 replacements=[
 ("envkeys=['AUDIO_ONLY','TMPDIR']", "envkeys=['AUDIO_ONLY','TMPDIR','CACHE_LOG']"),
 ("   os.chdir(W);sys.path[:0]=[str(T),str(W)]", "   os.environ['CACHE_LOG']=str(PR/'S3-prefix-cache-keys.txt')\n   os.chdir(W);sys.path[:0]=[str(T),str(W)]"),
 ("   title0=ns['title_audio'];sentence0=ns['sentence_audio'];gain0=ns['句增益']", """   prefix_tail=[];tail0=ns['_收句尾']
   def tail_trace(z):
    before=_prefix_sig(z);answer=tail0(z)
    if state['sid']=='S3':prefix_tail.append({'input':before,'output':_prefix_sig(answer),'changed_sample_count':int(np.count_nonzero(z!=answer))})
    return answer
   ns['_收句尾']=tail_trace
   title0=ns['title_audio'];sentence0=ns['sentence_audio'];gain0=ns['句增益']"""),
 ("    clips,tmap=sentence0(sent,pieces,gaps);records[sid]=", """    if sid=='S3':report['S3_prefix_cache_start']=len(Path(os.environ['CACHE_LOG']).read_text().splitlines())if Path(os.environ['CACHE_LOG']).exists()else 0
    clips,tmap=sentence0(sent,pieces,gaps);records[sid]="""),
 ("""   def gain(d,no,si,sent,pieces,gaps,clips,tmap,z):
    answer=gain0(d,no,si,sent,pieces,gaps,clips,tmap,z);sid=state['sid'];arrays[sid]=answer[1].copy();records[sid].update(samples=len(answer[1]),pre_master_float32_SHA256=arrsha(answer[1]),automatic_gain=answer[2],manual_gain=answer[3]);return answer""", """   def gain(d,no,si,sent,pieces,gaps,clips,tmap,z):
    sid=state['sid']
    if sid=='S3':
     report['actual_S3_caller_before_gain']={'no':no,'no_python_type':type(no).__name__,'si':si,'si_python_type':type(si).__name__,'sentence':sent,'state':copy.deepcopy(state),'pieces':copy.deepcopy(pieces),'gaps':list(gaps),'array':_prefix_sig(z),'clips':[_prefix_sig(q)for q in clips],'raw_fingerprint':ns['SENT_FP'][sent],'tmap':copy.deepcopy(tmap),'cuts':copy.deepcopy(ns['LAST']['cuts']),'S3_source_controls':{k:v['S3']for k,v in d.items()if isinstance(v,dict)and'S3'in v}}
    answer=gain0(d,no,si,sent,pieces,gaps,clips,tmap,z);sid=state['sid'];arrays[sid]=answer[1].copy();records[sid].update(samples=len(answer[1]),pre_master_float32_SHA256=arrsha(answer[1]),automatic_gain=answer[2],manual_gain=answer[3])
    if sid=='S3':
     names=Path(os.environ['CACHE_LOG']).read_text().splitlines()[report['S3_prefix_cache_start']:]
     assert all((cache/n).is_file()for n in names)
     modules={k:{'basename':Path(sys.modules[k].__file__).name,'SHA256':sha(sys.modules[k].__file__)}for k in ['clean','render','title2','kokoro_onnx']if k in sys.modules and getattr(sys.modules[k],'__file__',None)}
     report['actual_S3_caller_after_gain']={'array':_prefix_sig(answer[1]),'concatenated_returned_clips':_prefix_sig(np.concatenate(answer[0])),'automatic_gain':answer[2],'manual_gain':answer[3],'actual_original_tail':prefix_tail,'actual_S3_stored_G36':[v for v in levels if v['sentence']=='S3'],'actual_S3_cache_reads':[{'filename':n,'SHA256':sha(cache/n),'marker_SHA256':sha(cache/(n+'.单线程'))if(cache/(n+'.单线程')).is_file()else None}for n in names],'actual_imported_module_files':modules,'SR':ns['SR'],'AUD_DB':ns['AUD_DB'],'short_start':ns['_短起'](no),'SENT_NO':ns['SENT_NO'].get(sent),'spoken_source_no':ns['_SPOKEN_SOURCE_NO'],'source_file_SHA256':sha(source),'normalized_PCM16_float64':_prefix_pcm16(answer[1],last['master_pre_peak'])}
     report['records_captured_before_original_hard_assertions']=copy.deepcopy(records);report['actual_G36_captured_before_original_hard_assertions']=copy.deepcopy(levels)
     report['actual_standalone_S3_report_SHA256']=_prefix_actual_sha
     report['historical_expected_postgain555']=last['sentence_records']['S3']['pre_master_float32_sha256']
     report['historical_expected_quantized555']=last['old_to_current_actual_sentence_PCM_identity']['S3']['new_quantized_float64_sha256']
     report['intentional_stop_at_S3_original_gain_return']=True
     raise _PrefixComplete('Intentional S3-only original caller prefix stop; no S4 or whole WAV/AAC')
    return answer""")]
 for old,new in replacements:
  assert text.count(old)==1,'Exact immutable a473 instrumentation anchor changed: '+old[:80]
  text=text.replace(old,new,1)
 return text,replacements
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base-helper',type=Path,required=True);p.add_argument('--actual-S3-report',type=Path,required=True);args,rest=p.parse_known_args()
 assert sha(args.base_helper)==BASE and sha(args.actual_S3_report)==ACTUAL
 actual=json.loads(args.actual_S3_report.read_text());assert actual['observation_completed']is True and actual['hard_comparisons']['post_native_bytes_matches_actual555']is True and actual['original_master_quantization_S3_only']['exact_actual555_quantized_S3']is True
 assert rest.count('--output')==1;output=Path(rest[rest.index('--output')+1]);text,replacements=instrument(args.base_helper.read_text())
 ns={'__name__':'source52_original_a473_prefix_observer','__file__':str(args.base_helper),'_prefix_sig':sig,'_prefix_pcm16':pcm16_quant,'_PrefixComplete':PrefixComplete,'_prefix_actual_sha':ACTUAL}
 exec(compile(text,str(args.base_helper)+'#read-only-S3-prefix-instrumentation','exec'),ns)
 oldargv=list(sys.argv);stopped=False
 try:
  sys.argv=[str(args.base_helper),*rest]
  try:ns['main']()
  except PrefixComplete:stopped=True
 finally:sys.argv[:]=oldargv
 assert stopped,'Original build must stop immediately after S3 gain, never proceed to S4 or whole'
 report=json.loads(output.read_text());assert report['intentional_stop_at_S3_original_gain_return']is True
 assert report['all_private_cache_stats_and_keys_unchanged']and report['all_models_byte_exact_after']and report['all_input_and_tools_byte_exact_after']
 report['original_observer_build_attempt_counter']=report.pop('whole_build_count');assert report['original_observer_build_attempt_counter']==1
 report.update(kind='source52-original-a473-builder-prefix-through-S3-only-observation',whole_build_count=0,whole_WAV_or_AAC_or_video_encoded=False,completed=False,observation_completed=True,original_expected_Stop_exception=report.pop('error'),base_helper_SHA256=BASE,program_SHA256=sha(__file__),instrumentation_exact_anchor_count=len(replacements),fulltrack_or_formal_acceptance=False)
 before=report['actual_S3_caller_before_gain'];after=report['actual_S3_caller_after_gain']
 report['strict_comparisons']={'before_gain_same_as_standalone_and555':before['array']['SHA256']==actual['S3_before_gain']['array']['native_bytes_SHA256'],'post_gain_same_as_standalone_and555':after['array']['SHA256']==actual['S3_after_gain']['array']['native_bytes_SHA256']==report['historical_expected_postgain555'],'quantized_same_as_standalone_and555':after['normalized_PCM16_float64']['SHA256']==actual['original_master_quantization_S3_only']['decoded_float64_SHA256']==report['historical_expected_quantized555'],'no_previous_expected_hash_replaced':True}
 output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 assert all(report['strict_comparisons'].values()),'Actual original caller S3 differs; scalar partial saved; original hard hashes remain unmodified'
 return 0
if __name__=='__main__':raise SystemExit(main())
