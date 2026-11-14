"""Recheck exact archived authorized post-repair scalar chain, no production."""
import datetime,hashlib,json,pathlib,subprocess,tempfile
import numpy as np
import soundfile as sf
B=pathlib.Path(__file__).parent
sha=lambda x:hashlib.sha256(x).hexdigest()
def capture(args):return subprocess.check_output([str(x)for x in args])
def pcm(p,sr,ch):return np.frombuffer(capture(['ffmpeg','-v','error','-i',p,'-map','0:a:0','-vn','-ac',ch,'-ar',sr,'-c:a','pcm_f32le','-f','f32le','-']),'<f4').reshape(-1,ch).copy()
for no in ['67','70']:
    f=B/no;rp=f/f'{no}-archived-authorized-audio-repair.json';r=json.loads(rp.read_text());st=json.loads((f/f'{no}-status.json').read_text())
    source=f/f'{no}-real-approved-repair-input-public.mp4';accepted=f/f'{no}-accepted-public.mp4';sr=r['sample_rate'];ch=r['channels']
    source_pcm=pcm(source,sr,ch);processed=source_pcm.copy();outside=np.ones(len(source_pcm),dtype=bool)
    assert sha(source_pcm.tobytes())==r['source_decoded_float32_sha256']
    for w in r['gain_windows']:
        s,a,b,e=[round(w[k]*sr)for k in ('start','attack_end','release_start','end')]
        env=np.ones(e-s,dtype=np.float64)
        env[:a-s]=.5-.5*np.cos(np.linspace(0,np.pi,a-s))
        env[b-s:]=.5+.5*np.cos(np.linspace(0,np.pi,e-b))
        amp=1+(10**(w['gain_db']/20)-1)*env
        processed[s:e]=(processed[s:e].astype(np.float64)*amp[:,None]).astype(np.float32)
        outside[s:e]=False
    assert sha(processed.tobytes())==r['processed_float32_sha256']
    assert np.array_equal(source_pcm[outside],processed[outside])
    assert sha(source_pcm[outside].tobytes())==r['outside_source_float32_sha256']==r['outside_processed_float32_sha256']
    actual_decoded=pcm(accepted,sr,ch)
    assert sha(actual_decoded.tobytes())==r['final_decoded_float32_sha256']
    report=dict(source_id=no,created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),quality_acceptance=False,
        purpose='actual archived intentionally repaired old audio provenance; not a new current-maker quality verdict',
        program_sha256=sha(pathlib.Path(__file__).read_bytes()),archived_report_sha256=sha(rp.read_bytes()),
        archive_result_commit='c68846c63bc133f6227eaed375a581a65b3e903a',source_public_MP4_sha256=sha(source.read_bytes()),
        actual_accepted_MP4_sha256=sha(accepted.read_bytes()),actual_accepted_AAC_ADTS_sha256=st['accepted_source']['aac_adts_sha256'],
        actual_original_input_decoded_PCM_sha256=sha(source_pcm.tobytes()),archived_input_PCM_exact=True,
        exact_original_gain_windows=r['gain_windows'],recreated_processed_PCM_sha256=sha(processed.tobytes()),
        archived_processed_PCM_exact=True,entire_actual_accepted_decoded_PCM_sha256=sha(actual_decoded.tobytes()),
        actual_accepted_decoded_PCM_exact_archived_report=True,
        outside_all_windows_preencoding_samples_exact=True,
        ffmpeg_version=capture(['ffmpeg','-version']).decode().splitlines()[0])
    with tempfile.TemporaryDirectory(prefix=f'private-{no}-prior-authorized-postrepair-',dir='/dev/shm')as td:
        td=pathlib.Path(td);wav=td/'processed.wav';aac=td/'processed.m4a';sf.write(wav,processed,sr,subtype='FLOAT')
        info=json.loads(capture(['ffprobe','-v','error','-show_streams','-of','json',source]));stream=next(x for x in info['streams']if x['codec_type']=='audio')
        subprocess.run(['ffmpeg','-v','error','-y','-i',str(wav),'-map','0:a:0','-c:a','aac','-b:a',str(r['aac']['bitrate']),'-ar',str(sr),'-ac',str(ch),'-t',stream['duration'],'-avoid_negative_ts','disabled',str(aac)],check=True)
        ash=sha(capture(['ffmpeg','-v','error','-i',aac,'-map','0:a:0','-c:a','copy','-f','adts','-']))
        report.update(locally_reencoded_AAC_ADTS_sha256=ash,local_reencoding_exact_old_accepted=ash==st['accepted_source']['aac_adts_sha256'])
    report['no_TTS_no_existing_source_or_cache_or_core_or_control_changed']=True
    report['private_diagnostic_PCM_and_AAC_deleted']=True
    out=f/f'{no}-approved-postrepair-provenance-replay.json';out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(no,'exact original PCM/processed PCM/actual old decoded all match; local reencoding AAC exact',report['local_reencoding_exact_old_accepted'],'reportSHA',sha(out.read_bytes()),flush=True)
