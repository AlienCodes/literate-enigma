"""Read-only actual failed/approved public media comparison; no QC waiver."""
from pathlib import Path
import datetime,hashlib,json,re,subprocess,numpy as np

HERE=Path(__file__).resolve().parent
BASE=Path('/workspace/work/video-audit70-20261113/ci63-final-43523430839/public-evidence')
SR=48000;targets={'46':6,'49':8,'55':11};reports=[]
def sha(b):return hashlib.sha256(b).hexdigest()
def run(args):return subprocess.run(args,capture_output=True,check=True).stdout
def adts(p):return run(['ffmpeg','-v','error','-i',str(p),'-map','0:a:0','-c:a','copy','-f','adts','pipe:1'])
def pcm(p):return run(['ffmpeg','-v','error','-i',str(p),'-map','0:a:0','-c:a','pcm_f32le','-f','f32le','pipe:1'])
def packets(p):
 d=json.loads(run(['ffprobe','-v','error','-select_streams','a:0','-show_packets','-show_streams','-show_data_hash','sha256','-of','json',str(p)]))
 projection=[{k:x.get(k) for k in ['pts','dts','duration','size','data_hash']} for x in d['packets']]
 info={k:d['streams'][0].get(k) for k in ['codec_name','profile','sample_rate','channels','channel_layout','time_base','start_pts','start_time','extradata_size','extradata_hash']}
 return info,projection
def spans(a):
 # Unmodified scalar logic of official 音频体检.句段; this is only a public
 # clip locator, never an extra acceptance test or a private alignment export.
 z=np.concatenate([[0],(np.abs(a)<1e-6).astype(np.int8),[0]]);d=np.diff(z)
 sil=[(s,e) for s,e in zip(np.where(d==1)[0],np.where(d==-1)[0]) if e-s>=0.7*SR]
 out=[];prev=0
 for s,e in sil:
  if s>prev:out.append((prev,s))
  prev=e
 return [(int(s),int(e)) for s,e in out if e-s>0.3*SR]

for n,si in targets.items():
 root=HERE/'public-media'/n;retrieval=json.loads((root/'public-media-retrieval.json').read_text())
 files={k:Path(retrieval[k]['path']) for k in ['accepted','failed']}
 for k,p in files.items():assert sha(p.read_bytes())==retrieval[k]['sha256']
 encoded={k:adts(p) for k,p in files.items()};decoded={k:pcm(p) for k,p in files.items()}
 a=np.frombuffer(decoded['accepted'],dtype='<f4');b=np.frombuffer(decoded['failed'],dtype='<f4')
 infoA,packA=packets(files['accepted']);infoB,packB=packets(files['failed'])
 status=json.loads((BASE/n/f'{n}-status.json').read_text());proof=json.loads((BASE/n/f'{n}-failed-draft-proof.json').read_text());source=json.loads((BASE/n/f'{n}-failed-working-source.json').read_text())
 expected=status['accepted_source']['aac_adts_sha256']
 assert sha(encoded['accepted'])==expected and sha(encoded['failed'])==proof['aac_adts_sha256']
 equality=decoded['accepted']==decoded['failed'];seg=spans(b)
 row={'article':n,'sentence':f'S{si}','checked_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
      'human_listening_performed':False,'audio_controls_sources_thresholds_or_confirmations_modified':False,
      'media_retrieval':retrieval,'actual_adts':{k:{'bytes':len(v),'sha256':sha(v)} for k,v in encoded.items()},
      'ADTS_payload_and_headers_byte_identical':encoded['accepted']==encoded['failed'],
      'audio_codec_parameters_equal':infoA==infoB,'codec_parameters':{'accepted':infoA,'failed':infoB},
      'packet_counts':{'accepted':len(packA),'failed':len(packB)},'AAC_payload_absolute_pts_dts_duration_sizes_equal':packA==packB,
      'packet_projection_sha256':{'accepted':sha(json.dumps(packA,sort_keys=True,separators=(',',':')).encode()),'failed':sha(json.dumps(packB,sort_keys=True,separators=(',',':')).encode())},
      'decoded_public_PCM':{'format':'native ffmpeg float32le, original audio channel count/sample rate; no gain, filtering, resampling or alignment fit',
         'sample_rate':infoA['sample_rate'],'channels':infoA['channels'],'accepted_bytes':len(decoded['accepted']),'failed_bytes':len(decoded['failed']),
         'accepted_sha256':sha(decoded['accepted']),'failed_sha256':sha(decoded['failed']),'entire_decoded_track_byte_identical':equality,
         'samples_each':len(a),'max_abs_sample_difference':float(np.max(np.abs(a-b))) if len(a)==len(b) else None},
      'sentence_script':' '.join(re.sub(r'\{\{.*?\}\}|\*\*','',c['en']) for c in source['sentences'][si-1]['chunks']),
      'existing_machine_confirmation_for_target':source.get('核对确认',{}).get('机器复听',{}).get(f'S{si}'),
      'existing_machine_confirmation_sentence_keys':list(source.get('核对确认',{}).get('机器复听',{})),
      'public_silence_span_count':len(seg),'expected_title_plus_sentence_count':len(source['sentences'])+1,
      'public_clip_locator_logic':'official 音频体检.句段: consecutive abs(sample)<1e-6 for>=0.7seconds; keep spans>0.3seconds'}
 if len(seg)==len(source['sentences'])+1:
  start,end=seg[si];clip=root/f'{n}-S{si}-actual-failed-public-sentence.wav'
  subprocess.run(['ffmpeg','-v','error','-y','-i',str(files['failed']),'-map','0:a:0','-af',f'atrim=start_sample={start}:end_sample={end},asetpts=PTS-STARTPTS','-c:a','pcm_f32le',str(clip)],check=True)
  row['actual_public_sentence_clip']={'path':str(clip),'bytes':clip.stat().st_size,'sha256':sha(clip.read_bytes()),'sample_start':start,'sample_end':end,'seconds_start':start/SR,'seconds_end':end/SR,'derived_only_from_public_MP4':True,'entire_target_interval_matches_approved_samples':equality}
 else:row['sentence_clip_not_exported']='Public silence span count differs from title+script sentences; no unproven sentence label assigned.'
 (root/'audio-comparison.json').write_text(json.dumps(row,ensure_ascii=False,indent=2)+'\n');reports.append(row)
 print(json.dumps({'article':n,'ADTS_equal':row['ADTS_payload_and_headers_byte_identical'],'AAC_absolute_times_equal':row['AAC_payload_absolute_pts_dts_duration_sizes_equal'],'PCM_entire_track_equal':equality,'samples':len(a),'spans':len(seg),'expected':len(source['sentences'])+1,'target_clip':row.get('actual_public_sentence_clip',{})},ensure_ascii=False),flush=True)
(HERE/'actual-public-audio-comparison.json').write_text(json.dumps({'scope':'readonly actual public media; no human listening and no new acceptance or waiver','articles':reports},ensure_ascii=False,indent=2)+'\n')
