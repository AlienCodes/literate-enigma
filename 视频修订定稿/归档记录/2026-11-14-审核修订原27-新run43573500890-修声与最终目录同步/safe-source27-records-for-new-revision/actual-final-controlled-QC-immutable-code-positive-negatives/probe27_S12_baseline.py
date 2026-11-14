"""Exact unchanged accepted S12 supplement finding; no source or audio edits."""
from pathlib import Path
import hashlib,importlib.util,json,subprocess,tempfile,sys
import numpy as np
import soundfile as sf
H=Path(__file__).parent;B=H.parent;CI=Path('/workspace/work/video-revision-batch-ci/.github/video-revision-batch')
def mod(name,p):
 s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();U=mod('S12_original_U',CI/'audio-qc.py')
helper=B/'audio-a21-actual-first-4K-20261114/probe_minimal_encoded_boost.py';ns={'__file__':str(helper),'__name__':'S12_original_source_context'};exec(compile(helper.read_text().split('for no in sys.argv')[0],str(helper)+'#definitions-only','exec'),ns);o=ns['r'];T=o.m.T
R=mod('响度一致性核对',T/'响度一致性核对.py');R.FF='ffmpeg';Q=mod('S12_original_health',T/'音频体检.py')
source=B/'payload/视频/脚本/27.json';assert sha(source)=='e1214d8e9314a1cb54da82e2532889198bec555d6be9189fbfb43b5fdedcd728';oldpath=H/'27-original-accepted-public.mp4';assert sha(oldpath)=='4ab9da92fd3f57c226bd064c4c076d3f3b5428545542410d83ddc7cd90d9075e'
first=H/'controlled-QC-real-verification/27-actual-diagnostic-positive.json';old=U.decode(oldpath)
with tempfile.TemporaryDirectory(prefix='private27_S12_baseline_',dir='/dev/shm')as td:
 td=Path(td);cache=td/'cache';cache.mkdir();a,parts=o.build(json.loads(source.read_text()),cache);wav=td/'new.wav';sf.write(wav,a,24000);assert sha(wav)=='def5cf361fc57229ff8e14bf8db379fa60ca876b4ecde7eae6689444d4416ea7';aac=td/'new.m4a';subprocess.run([o.FF,'-y','-v','error','-i',str(wav),'-af',o.AF,'-c:a','aac','-b:a','256k','-movflags','+faststart',str(aac)],check=True)
 ash=hashlib.sha256(subprocess.check_output(['ffmpeg','-v','error','-i',str(aac),'-map','0:a:0','-c:a','copy','-f','adts','-'])).hexdigest();assert ash=='d619f0175ab2c57c6a5b77b9c6f0d62cd5b9fc2c548ec3900a45b3c44919b6f9';new=U.decode(aac)
 pre_SF=hashlib.sha256(np.ascontiguousarray(a[:2454600]).tobytes()).hexdigest();assert pre_SF=='6d4e5f189a4c6c6b139fb881f82bcf08e48f0126929e5c19e898590ce7d5cb2f'
 raw,sr=sf.read(wav,dtype='float32');prefix=hashlib.sha256(np.ascontiguousarray(raw[:2454600]).tobytes()).hexdigest()
 baseline=json.loads((H/'candidate-payload/视频/脚本/27.json').read_text());old_a,_=o.build(baseline,cache);oldwav=td/'old.wav';sf.write(oldwav,old_a,24000);assert sha(oldwav)=='e15a2d05428e3219216ac8d10780669007f903071b0fcfc3c6bf377c517b8d7f';oldraw,_=sf.read(oldwav,dtype='float32');oldprefix=hashlib.sha256(np.ascontiguousarray(oldraw[:2454600]).tobytes()).hexdigest();assert oldprefix==prefix
 assert hashlib.sha256(np.ascontiguousarray(old_a[:2454600]).tobytes()).hexdigest()==pre_SF
 findings={}
 for label,path in [('old',oldpath),('new',aac)]:
  samples=R.pcm(str(path));tm=R.momentary(str(path));spans=Q.句段(samples);assert len(spans)==17
  seg=td/'work_27/分段.json';seg.parent.mkdir(exist_ok=True);seg.write_text(json.dumps({f'S{i}':[{'时刻':[x/R.SR,y/R.SR]}]for i,(x,y)in enumerate(spans[1:],1)}));findings[label]=json.loads(json.dumps(R.压小(str(path),samples,tm,str(seg))))
 target=[99.2,101.4];context=[92.8,101.6];proof=[]
 for label,span in [('exact_original_flag_window',target),('entire_sentence_plus_context',context)]:
  lo,hi=[round(x*48000)for x in span];oa=np.ascontiguousarray(old[lo:hi],dtype=np.float32);na=np.ascontiguousarray(new[lo:hi],dtype=np.float32);proof.append({'label':label,'span_s':span,'sample_count':len(oa),'float32_bitexact':bool(np.array_equal(oa,na)),'old_sha256':hashlib.sha256(oa.tobytes()).hexdigest(),'new_sha256':hashlib.sha256(na.tobytes()).hexdigest()})
 result={'article':'27','kind':'exact_existing_accepted_S12_original_supplement_finding','new_production_quality_passed':False,'actual_old_accepted_MP4_sha256':sha(oldpath),'actual_old_AAC_ADTS_sha256':'14bc91c62e66921fb55a215a42ce2db6a5544316600687b535a468770ae28252','actual_old_WAV_sha256':sha(oldwav),'actual_new_WAV_sha256':sha(wav),'actual_new_AAC_ADTS_sha256':ash,'original_R_program_sha256':sha(T/'响度一致性核对.py'),'old_original_raw_suppression_findings':findings['old'],'new_original_raw_suppression_findings':findings['new'],'original_R_findings_exact_equal':findings['old']==findings['new'],'raw_original_R_failure_lists_retained':True,'public_exact_sample_proof':proof,'native_prefix_24k_float32':{'sample_range':[0,2454600],'seconds':[0,102.275],'pre_SF_original_build_float32_old_and_new_sha256':pre_SF,'WAV_PCM16_roundtrip_float32_actual_new_sha256':prefix,'WAV_PCM16_roundtrip_float32_actual_old_sha256':oldprefix,'equal_in_both_representations':True},'only_existing_S12_2_finding':len(findings['new'])==1 and findings['new'][0][:2]==['S12',2],'source_DSP_checker_threshold_or_existing_cache_changed':False,'private_audio_deleted_after_probe':True,'first_actual_helper_failed_report_sha256':sha(first),'program_sha256':sha(__file__)}
 result['root_conditions_satisfied']=result['original_R_findings_exact_equal']and result['only_existing_S12_2_finding']and all(x['float32_bitexact']for x in proof)
p=H/'controlled-QC-real-verification/S12-existing-accepted-exact-sample-evidence.json';p.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'conditions_satisfied':result['root_conditions_satisfied'],'original_old_findings':findings['old'],'all_public_context_samples_identical':all(x['float32_bitexact']for x in proof),'report_sha256':sha(p)},ensure_ascii=False))
