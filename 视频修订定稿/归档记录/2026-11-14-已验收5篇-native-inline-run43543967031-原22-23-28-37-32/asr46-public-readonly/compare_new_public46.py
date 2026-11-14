from pathlib import Path
import zipfile,json,hashlib,subprocess,datetime,numpy as np

HERE=Path(__file__).resolve().parent
ZIP=Path('/workspace/work/video-audit70-20261113/native-inline41-second20-43543967031/failed46/article46-native-output.zip')
OLD=Path('/workspace/work/video-audit70-20261113/asr46-49-55-readonly-20261114/public-media/46')
def sha(b):return hashlib.sha256(b).hexdigest()
def run(a):return subprocess.run(a,capture_output=True,check=True).stdout
assert sha(ZIP.read_bytes())=='329565110f5d635c3e8a57db2aafb1ca79d923ce7e14f1dec52e1620e943e658'
with zipfile.ZipFile(ZIP) as z:
 names=z.namelist();en=next(n for n in names if n.endswith('46-original-ASR-target-evidence.json'));raw=z.read(en);ev=json.loads(raw)
 assert ev['diagnostic_only'] and not ev['acceptance'] and not ev['automatic_confirmation'] and not ev['private_raw_PCM_GT_models_or_caches_exported']
 (HERE/'46-original-ASR-target-evidence.json').write_bytes(raw)
 candidates=[n for n in names if n.endswith('.mp4')]
 assert len(candidates)==1
 data=z.read(candidates[0]);assert sha(data)==ev['public_video_sha256'];new=HERE/'46-current-failed-public.mp4';new.write_bytes(data)
 context=ev['public_MP4_context'];cn=next(n for n in names if n.endswith(context['file']));data=z.read(cn);assert sha(data)==context['sha256'];(HERE/context['file']).write_bytes(data)
retrieval=json.loads((OLD/'public-media-retrieval.json').read_text());accepted=Path(retrieval['accepted']['path']);assert sha(accepted.read_bytes())==retrieval['accepted']['sha256']
def audio(p,encoded):return run(['ffmpeg','-v','error','-i',str(p),'-map','0:a:0']+(['-c:a','copy','-f','adts'] if encoded else ['-c:a','pcm_f32le','-f','f32le'])+['pipe:1'])
def packets(p):
 d=json.loads(run(['ffprobe','-v','error','-select_streams','a:0','-show_packets','-show_streams','-show_data_hash','sha256','-of','json',str(p)]))
 return ({k:d['streams'][0].get(k) for k in ('codec_name','profile','sample_rate','channels','channel_layout','time_base','start_pts','start_time','extradata_size','extradata_hash')},[{k:x.get(k) for k in ('pts','dts','duration','size','data_hash')} for x in d['packets']])
encA,encB=audio(accepted,True),audio(new,True);rawA,rawB=audio(accepted,False),audio(new,False);infoA,pkA=packets(accepted);infoB,pkB=packets(new)
a,b=np.frombuffer(rawA,dtype='<f4'),np.frombuffer(rawB,dtype='<f4')
out={'article':'46','sentence':'S6','checked_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'Read-only actual current public MP4 compared with previously accepted public MP4. No human listening, new quality approval, waiver, source/threshold/audio/control changes.','human_listening_performed':False,'confirmation_or_gate_modified':False,'input_ZIP_sha256':sha(ZIP.read_bytes()),'accepted_public_mp4':retrieval['accepted'],'current_public_mp4':{'path':str(new),'sha256':sha(new.read_bytes()),'bytes':new.stat().st_size},'ASR_evidence':ev,'AAC_ADTS_entire_track_byte_equal':encA==encB,'AAC_ADTS_sha256':{'accepted':sha(encA),'current':sha(encB)},'audio_codec_parameters_equal':infoA==infoB,'AAC_packet_payload_absolute_pts_dts_duration_size_equal':pkA==pkB,'packet_counts':{'accepted':len(pkA),'current':len(pkB)},'packet_projection_sha256':{'accepted':sha(json.dumps(pkA,sort_keys=True,separators=(',',':')).encode()),'current':sha(json.dumps(pkB,sort_keys=True,separators=(',',':')).encode())},'public_decoded_float32_entire_track_byte_equal':rawA==rawB,'public_decoded_samples':{'accepted':len(a),'current':len(b)},'public_decoded_sha256':{'accepted':sha(rawA),'current':sha(rawB)},'max_abs_public_sample_difference':float(np.max(np.abs(a-b))) if len(a)==len(b) else None,'private_native_ASR_input_PCM_not_read_or_exported':True,'native_ASR_input_identity_to_accepted_not_claimed':True,'transcript_context_observation':'Original exact sentence window: small.en light, parakeet lights. Public MP4 context with 120ms padding: both recognizers light and no word differences. Different context/window, not a sample-identity claim.'}
(HERE/'comparison-report.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:out[k] for k in ('AAC_ADTS_entire_track_byte_equal','AAC_packet_payload_absolute_pts_dts_duration_size_equal','public_decoded_float32_entire_track_byte_equal','public_decoded_samples','max_abs_public_sample_difference','human_listening_performed')},ensure_ascii=False))
