"""Read-only actual published audio measurements for user092; no repair or TTS."""
import hashlib,json,subprocess,zipfile
from pathlib import Path
import numpy as np
import soundfile as sf
H=Path(__file__).resolve().parent;B=Path('/workspace/work/video-audit70-20261113');A=H/'audio092-readonly';A.mkdir(exist_ok=True)
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
OLD_VIDEO_SHA='6bad7b012ccbad87a60ced23ada2c3162c7a561b4e72ad52362004ee3313ea8c';OLD_AAC_SHA='66f8c5cfdd6c5551f20779115574f896d849763cf5adf8042c503664bf7ab94f'
rootzip=Path('/dev/shm/37-70-4K-REVIEW.zip');name='37 末日种子库的第一次取种.mp4';mp4=A/'actual-published-legacy-book37-source65.mp4'
with zipfile.ZipFile(rootzip)as z:data=z.read(name)
assert len(data)==12530393 and hashlib.sha256(data).hexdigest()==OLD_VIDEO_SHA
if mp4.exists():assert mp4.read_bytes()==data
else:mp4.write_bytes(data)
adts=subprocess.check_output(['ffmpeg','-v','error','-nostdin','-i',str(mp4),'-map','0:a:0','-c:a','copy','-f','adts','-']);assert hashlib.sha256(adts).hexdigest()==OLD_AAC_SHA
wav=A/'actual-public-AAC-decoded-48k.wav';subprocess.run(['ffmpeg','-v','error','-nostdin','-y','-i',str(mp4),'-map','0:a:0','-ac','1','-ar','48000','-c:a','pcm_s16le',str(wav)],check=True)
x,sr=sf.read(wav,dtype='int16');assert sr==48000 and x.ndim==1;v=x.astype(np.float64)/32768
def db(n):return float(20*np.log10(max(float(n),1e-15)))
def metrics(start,end):
 z=v[round(start*sr):round(end*sr)];e=z*z;n=len(z);frame=round(.02*sr);step=round(.005*sr)
 frame_starts=np.arange(0,max(n-frame+1,1),step);frame_rms=np.array([np.sqrt(np.mean(e[p:min(p+frame,n)]))for p in frame_starts]);active=frame_rms>10**(-42/20)
 mask=np.zeros(n,dtype=bool)
 for p,a in zip(frame_starts,active):
  if a:mask[p:min(p+frame,n)]=True
 window=min(round(.4*sr),n);sums=np.cumsum(np.r_[0,e]);ms=(sums[window:]-sums[:-window])/window;best=int(np.argmax(ms))
 return {'span_seconds':[start,end],'sample_count':n,'RMS_including_silence_dBFS':db(np.sqrt(np.mean(e))),'peak_dBFS':db(np.max(np.abs(z))),'speech_active_20ms_frame_gate_dBFS':-42,'speech_active_sample_ratio':float(np.mean(mask)),'speech_active_RMS_dBFS':db(np.sqrt(np.mean(e[mask])))if mask.any()else None,'loudest_400ms_RMS_dBFS':db(np.sqrt(ms[best])),'loudest_400ms_span_seconds':[start+best/sr,start+(best+window)/sr]}
probe=B/'audio65-69-source-readonly/65/65-real-historical-source-G36-AAC-probe.json';p=json.loads(probe.read_text());parts=p['parts'];rows=[]
for part in parts:
 rows.append({'sentence':part['sentence'],'whole_utterance':metrics(part['start_s'],part['end_s'])})
targets={'S2_At_its_end_first_phrase_approximate':[12.12,12.91],'S2_first_300ms_approximate':[12.12,12.42],'S2_later_speech_context':[13.05,17.63],'S1_initial_location_context':[3.275,4.72]}
targetmetrics={label:metrics(*span)for label,span in targets.items()}
for label,span in [('S2-At-its-end-context-11.8-13.5s',[11.8,13.5]),('S2-complete-12.12-20.98s',[12.12,20.98]),('neighbor-S1-S2-S3-3.1-35.8s',[3.1,35.8])]:sf.write(A/(label+'.wav'),x[round(span[0]*sr):round(span[1]*sr)],sr,subtype='PCM_16')
report={'kind':'source65_actual_published_legacy_audio_readonly_objective_baseline','user_record':'092','quality_acceptance_or_listening_claimed':False,'audio_repaired_or_TTS_or_normalization_performed':False,'source_MP4':{'path':str(mp4),'bytes':mp4.stat().st_size,'sha256':sha(mp4)},'actual_AAC_adts_sha256':hashlib.sha256(adts).hexdigest(),'decoded_actual_public_WAV':{'path':str(wav),'bytes':wav.stat().st_size,'sha256':sha(wav),'sample_rate':sr,'samples':len(x)},'timing_provenance':{'path':str(probe),'sha256':sha(probe),'old_historical_source_sha256':p['historical_source_full_SHA256'],'old_original_G36_function_revision':p['historical_original_G36_function_revision'],'whole_AAC_matches_actual_accepted':p['whole_AAC_matches_actual_accepted']},'target_phrase_boundaries_are_approximate_from_retained_FIRST_LAST_segment_not_new_word_forced_alignment':True,'target_metrics':targetmetrics,'whole_utterance_metrics':rows,'existing_historical_S2_automatic_first_segment_gain_dB':-4.0,'later_failed_native_S2_automatic_first_segment_gain_dB':-2.0,'later_failed_native_has_different_whole_AAC_and_is_not_this_baseline':True,'mean_only_normality_inference_not_used':True,'local_derived_public_audio_clips_not_final_deliverables':True}
out=A/'actual-old65-speechactive-and-400ms-report.json';out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'report':str(out),'sha256':sha(out),'target_metrics':targetmetrics},ensure_ascii=False))
