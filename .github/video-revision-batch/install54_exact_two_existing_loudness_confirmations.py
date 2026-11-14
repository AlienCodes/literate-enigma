#!/usr/bin/env python3
"""Apply only two root-approved runtime source54 loudness fingerprints.

Run AFTER original canonical-draft has produced W/work_54/a.wav and W/54.mp4,
BEFORE original canonical-final4K. The request source and GEN are read-only.
This is identity/metadata continuity, not an audio QA verdict or gate bypass.
"""
import argparse,copy,hashlib,importlib.util,json,os,subprocess,sys,wave
from pathlib import Path
import numpy as np,imageio_ffmpeg
HERE=Path(__file__).resolve().parent
KEYS=('95.6–96.0s','118.3–118.8s')
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb')as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def canonical(x):return hashlib.sha256(json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def aac_sha(p):return hashlib.sha256(subprocess.check_output(['ffmpeg','-v','error','-nostdin','-i',str(p),'-map','0:a:0','-c:a','copy','-f','adts','-'])).hexdigest()
def clock(p):
 d=json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','a:0','-show_streams','-show_packets','-of','json',str(p)]))
 stream=d['streams'][0]
 return {'stream':{k:stream.get(k)for k in ['codec_name','sample_rate','channels','channel_layout','time_base','start_pts','extradata_size']},'packets':[{k:r.get(k)for k in ['pts','dts','duration','side_data_list']}for r in d['packets']]}
def actual_loudness_context(p,ref):
 decoder=imageio_ffmpeg.get_ffmpeg_exe();assert sha(decoder)==ref['original_audioQC_imageio_decoder_sha256']
 raw=subprocess.check_output([decoder,'-v','error','-nostdin','-i',str(p),'-map','0:a:0','-vn','-ac','1','-ar','48000','-c:a','pcm_s16le','-f','s16le','-'])
 pcm=np.frombuffer(raw,dtype='<i2');crops=[]
 for row in ref['exact_public_whole_sentence_crops']:
  lo,hi=[int(t*48000)for t in row['span_s']];a=pcm[lo:hi]
  assert len(a)==row['samples']and hashlib.sha256(a.tobytes()).hexdigest()==row['PCM16_sha256'],'Original complete sentence crop identity differs: '+row['scope']
  crops.append({'scope':row['scope'],'samples':len(a),'PCM16_sha256':hashlib.sha256(a.tobytes()).hexdigest(),'original_full_sentence_bound':True})
 # Exact original audio_qc segmentation/baseline, not an alternative threshold.
 a=pcm.astype(np.float64)/32768;h=480;rms=np.array([np.sqrt(np.mean(a[i:i+h]**2))for i in range(0,len(a)-h,h)])
 q=20*np.log10(rms/(rms.max()+1e-9)+1e-9)<-45;runs=[];st=None
 for i,v in enumerate(q):
  if v and st is None:st=i
  if not v and st is not None:runs.append((st/100,(i-st)/100));st=None
 segs=[];prev=0
 for t,d in runs:
  if t-prev>.4:segs.append((prev,t))
  prev=t+d
 lv=[float(20*np.log10(np.sqrt(np.mean(a[int(x*48000):int(y*48000)]**2))+1e-9))for x,y in segs];med=float(np.median(lv))
 assert len(segs)==ref['original_current_global_context']['segment_count']
 assert abs(med-ref['original_current_global_context']['median_dBFS'])<1e-12,'Original whole-piece comparison baseline changed.'
 found=[]
 for key in KEYS:
  i=next(i for i,(x,y)in enumerate(segs)if f'{x:.1f}–{y:.1f}s'==key);expected=ref['original_current_global_context']['targets'][key]
  assert list(segs[i])==expected['span_s']and abs(lv[i]-expected['RMS_dBFS'])<1e-12
  dip=float(f'{med-lv[i]:.1f}');assert dip==expected['reported_dB']and dip<=expected['existing_low']+.3
  found.append({'key':key,'RMS_dBFS':lv[i],'reported_dB':dip,'original_confirmed_low':expected['existing_low'],'original_plus0_3_predicate':True})
 return {'original_current_context_exact':True,'median_dBFS':med,'segment_count':len(segs),'whole_sentence_crops':crops,'existing_two_original_policy_dips':found}
def install(args):
 output=Path(args.output);output.parent.mkdir(parents=True,exist_ok=True)
 report={'article':'54','kind':'specific-two-existing-loudness-confirmation-runtime-fingerprint-continuity','passed':False,'quality_acceptance':False,'runtime_confirmation_transfer_applied':False,'no_TTS_audio_cache_or_threshold_mutation':True,'original_full_native_gates_ASR_and_finalV3_still_required':True,'request_and_GEN_readonly':True,'legacy_reference_not_relabelled_accepted_current':True,'program_sha256':sha(__file__)}
 try:
  rp=Path(args.reference or HERE/'install54_exact_two_existing_loudness_confirmations_reference.json');ref=json.loads(rp.read_text());report['reference_sha256']=sha(rp)
  assert ref['article']=='54'and tuple(ref['keys'])==KEYS
  assert ref['root_decision_sha256']=='e04a52c1a6e3027d0fd515a017593c31ed60315c4f37281d7e0d2eed4595aed6'
  profile=ref['profile'];assert canonical(profile)==ref['profile_canonical_sha256']
  assert ref['profile_file_sha256']=='70469afeec6fe37b8997575d87ae36493426ef11ad0fb2e8828d9edba03882fa'
  assert hashlib.sha256((json.dumps(profile,ensure_ascii=False,indent=2)+'\n').encode()).hexdigest()==ref['profile_file_sha256']
  assert ref['identity_only_verifier_sha256']=='cf946dd36c42d4fcbe8661869cf2adcb81b1ac302da143e3d9a67f5dbaffce7d'
  vp=HERE/'verify54_exact_current_reference.py';assert sha(vp)==ref['identity_only_verifier_sha256'];s=importlib.util.spec_from_file_location('specific54_identity',vp);v=importlib.util.module_from_spec(s);s.loader.exec_module(v)
  W=Path(args.work).resolve();request=Path(args.request).resolve();source=W/'scripts/54.json';q=request/'视频/脚本/54.json';g=request/'视频/工具/初稿生成/gen54.py';wav=W/'work_54/a.wav';audio=Path(args.actual_audio).resolve()if args.actual_audio else W/'54.mp4'
  assert source.resolve()!=q.resolve(),'Runtime and request must be separate files.'
  assert sha(q)==profile['request_source_sha256']and sha(g)==profile['request_GEN_sha256']
  assert sha(wav)==profile['current_reference_WAV_sha256']and hashlib.md5(wav.read_bytes()).hexdigest()[:12]==profile['current_reference_WAV_file_MD5_first12']
  with wave.open(str(wav),'rb')as f:shape={'rate':f.getframerate(),'channels':f.getnchannels(),'width':f.getsampwidth(),'samples':f.getnframes()}
  assert shape==ref['WAV_shape']
  actualaac=aac_sha(audio);assert actualaac==profile['current_reference_AAC_adts_sha256']
  actualclock=clock(audio);assert canonical(actualclock)==ref['actual_current_absolute_packet_projection_sha256'],'Public AAC absolute clock changed.'
  context=actual_loudness_context(audio,ref)
  requested=json.loads(q.read_text());actual=json.loads(source.read_text());current=actual['核对确认']['响度骤降'];before=copy.deepcopy(actual);changed=copy.deepcopy(actual);states=[]
  for row in profile['exact_two_existing_confirmation_fingerprint_changes']:
   key=row['exact_review_path'][2];assert requested['核对确认']['响度骤降'][key]==row['existing_entry_verbatim'];assert current[key]in [row['existing_entry_verbatim'],row['proposed_entry']]
   changed['核对确认']['响度骤降'][key]=copy.deepcopy(row['proposed_entry']);states.append(current[key]==row['proposed_entry'])
  assert all(states)or not any(states),'Partial fingerprint installation is not an expected state.'
  identity=v.validate(profile,requested,changed,sha(q),sha(g),sha(wav),actualaac,profile['legacy_accepted_AAC_adts_sha256'],profile['actual_public_wholeS11_S13_and_comparison_context']['sha256'])
  assert identity['identity_binding_passed'],'Fullsource changed outside the two approved fingerprints and exact G35.'
  assert {k:x for k,x in before.items()if k!='核对确认'}=={k:x for k,x in changed.items()if k!='核对确认'}
  report.update(actual_WAV_sha256=sha(wav),actual_AAC_sha256=actualaac,actual_absolute_packet_projection_sha256=canonical(actualclock),actual_public_original_context=context,identity_only_binding=identity,source_sha256_before=sha(source),only_two_existing_fingerprints_changed=True,existing_basis_low_sentence_and_userquote_fields_preserved=True,already_exactly_installed=all(states))
  if not args.diagnostic:
   assert args.write_runtime,'Explicit runtime-write mode is required.'
   temporary=source.with_name(source.name+'.specific54-loudness-tmp');temporary.write_text(json.dumps(changed,ensure_ascii=False,indent=2)+'\n');os.replace(temporary,source);assert json.loads(source.read_text())==changed;report['runtime_confirmation_transfer_applied']=True
  report['source_sha256_after']=sha(source);assert sha(q)==profile['request_source_sha256']and sha(g)==profile['request_GEN_sha256']and sha(wav)==profile['current_reference_WAV_sha256'];report['passed']=True
 except BaseException as e:report['error']={'type':type(e).__name__,'detail':str(e)}
 output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');return 0 if report['passed']else 1
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__)
 for name in ['work','request','output']:p.add_argument('--'+name,required=True)
 p.add_argument('--actual-audio');p.add_argument('--reference');p.add_argument('--write-runtime',action='store_true');p.add_argument('--diagnostic',action='store_true');sys.exit(install(p.parse_args()))
