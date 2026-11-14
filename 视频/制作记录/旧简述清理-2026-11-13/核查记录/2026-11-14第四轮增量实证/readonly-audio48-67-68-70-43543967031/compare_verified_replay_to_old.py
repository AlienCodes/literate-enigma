"""Diagnostic scalars only; private original-cache reconstruction is deleted.

The reconstruction must match native internal WAV AND native AAC before it can
describe the failed native attempt. This is not a quality-acceptance branch.
"""
import datetime, hashlib, importlib.util, json, pathlib, subprocess, sys, tempfile, traceback
import numpy as np
import soundfile as sf
from scipy import signal

B=pathlib.Path(__file__).parent
P=B/'replay_cache_provenance.py'
spec=importlib.util.spec_from_file_location('safe_cache_replay',P)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
orig=m.orig
SR=48000
sha=lambda x:hashlib.sha256(x).hexdigest()
def decode(p):
    return np.frombuffer(subprocess.check_output(['ffmpeg','-v','error','-nostdin','-i',str(p),'-vn','-ac','1','-ar',str(SR),'-f','f32le','-']),np.float32)
def fit(x,y):
    x=x.astype(float);y=y.astype(float)
    xx=x@x;yy=y@y;g=float(x@y/(xx+1e-30));err=y-g*x
    return dict(fitted_gain_dB=float(20*np.log10(max(g,1e-30))),NCC=float(x@y/np.sqrt(xx*yy+1e-30)),
        residual_SNR_dB=float(10*np.log10((np.mean((g*x)**2)+1e-30)/(np.mean(err**2)+1e-30))),
        exact_decoded_sample_equality=bool(np.array_equal(x,y)),different_samples=int(np.count_nonzero(x!=y)))
def main(no):
    f=B/no;st=json.loads((f/f'{no}-status.json').read_text());dg=json.loads((f/f'{no}-reference-gain-diagnostic.json').read_text())
    req=pathlib.Path('/workspace/work/video-revision-batch-ci/.github/video-revision-batch/request')/no/f'视频/脚本/{no}.json'
    assert sha(req.read_bytes())==st['request_source_sha256'][f'视频/脚本/{no}.json']
    anchor=st['accepted_source'];old=f/f'{no}-accepted-public.mp4';assert sha(old.read_bytes())==anchor['sha256']
    expectedAAC=st.get('canonical_aac_adts_sha256')
    if expectedAAC is None:expectedAAC=json.loads((f/f'{no}-failed-draft-proof.json').read_text())['aac_adts_sha256']
    rep=dict(source_id=no,created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),quality_acceptance=False,
        purpose='independent physical scalar comparison of real old accepted audio against exact native-hash-matched original-cache reconstruction',
        program_sha256=sha(pathlib.Path(__file__).read_bytes()),replay_program_sha256=sha(P.read_bytes()),
        original_maker_sha256=sha(orig.m.source.encode()),source_sha256=sha(req.read_bytes()),actual_old_MP4_sha256=anchor['sha256'],actual_old_AAC_ADTS_sha256=anchor['aac_adts_sha256'])
    try:
        with tempfile.TemporaryDirectory(prefix=f'private-{no}-old-native-comparison-',dir='/dev/shm') as td:
            td=pathlib.Path(td);cache=td/'cache';cache.mkdir();audio,parts=orig.build(json.loads(req.read_text()),cache)
            wav=td/'reconstruction.wav';aac=td/'reconstruction.m4a';sf.write(wav,audio,24000)
            subprocess.run([orig.FF,'-y','-loglevel','error','-i',str(wav),'-af',orig.AF,'-c:a','aac','-b:a','256k','-movflags','+faststart',str(aac)],check=True)
            wsh=sha(wav.read_bytes());ash=sha(subprocess.check_output(['ffmpeg','-v','error','-nostdin','-i',str(aac),'-map','0:a:0','-c:a','copy','-f','adts','-']))
            rep['native_reconstruction_binding']=dict(reconstructed_WAV_sha256=wsh,native_WAV_sha256=dg['wav_sha256'],WAV_exact=wsh==dg['wav_sha256'],
                reconstructed_AAC_ADTS_sha256=ash,native_AAC_ADTS_sha256=expectedAAC,AAC_exact=ash==expectedAAC)
            assert wsh==dg['wav_sha256'] and ash==expectedAAC,'No actual-native attribution without exact WAV and AAC binding'
            oldx=decode(old);newx=decode(aac);n=min(len(oldx),len(newx));diff=np.flatnonzero(oldx[:n]!=newx[:n])
            rep.update(actual_native_AAC_equal_old=ash==anchor['aac_adts_sha256'],decoded_counts_48k=[len(oldx),len(newx)],
                decoded_duration_delta_s=(len(newx)-len(oldx))/SR,entire_decoded_arrays_exact=bool(np.array_equal(oldx,newx)),
                direct_clock_different_sample_count=len(diff),first_different_time_s=None if not len(diff) else int(diff[0])/SR,
                last_different_time_s=None if not len(diff) else int(diff[-1])/SR)
            rows=[]
            for stime in np.arange(.5,min(len(oldx),len(newx))/SR-1,2.):
                lo=round(stime*SR);hi=lo+SR;x=oldx[lo:hi];rms=float(np.sqrt(np.mean(x.astype(float)**2)))
                if rms<10**(-45/20):continue
                margin=round(.6*SR);left=max(0,lo-margin);s=newx[left:min(len(newx),hi+margin)]
                corr=signal.correlate(s,x,'valid',method='fft');idx=int(np.argmax(corr));start=left+idx;y=s[idx:idx+len(x)]
                rows.append(dict(old_span_s=[float(stime),float(stime+1)],correlated_actual_native_span_s=[start/SR,(start+len(x))/SR],
                    lag_samples=start-lo,lag_s=(start-lo)/SR,old_RMS_dBFS=float(20*np.log10(rms)),**fit(x,y)))
            rep['independently_correlated_active_1s_rows']=rows
            segrows=[]
            for sentence,segs in dg['public_producer_timing_metadata']['segments'].items():
                for seg in segs:
                    t0,t1=seg['时刻'];start=t0+.08;end=min(t1-.06,start+1)
                    if end-start<.12:continue
                    a0,a1=round(start*SR),round(end*SR);y=newx[a0:a1]
                    margin=round(.6*SR);left=max(0,a0-margin);s=oldx[left:min(len(oldx),a1+margin)]
                    cor=signal.correlate(s,y,'valid',method='fft');idx=int(np.argmax(cor));oldstart=left+idx;x=s[idx:idx+len(y)]
                    segrows.append(dict(sentence=sentence,segment=seg['段'],actual_native_gain_dB=seg['增益'],
                        native_span_s=[start,end],independently_correlated_old_span_s=[oldstart/SR,(oldstart+len(y))/SR],
                        old_minus_native_lag_s=(oldstart-a0)/SR,**fit(x,y)))
            rep['public_producer_segment_comparisons']=segrows
            rep['native_title_and_sentences_safe_timing']=parts
    except BaseException as ex:
        rep['error']=dict(type=type(ex).__name__,detail=str(ex),traceback=traceback.format_exc());print(traceback.format_exc(),flush=True)
    rep['no_TTS_no_media_production_no_source_or_control_or_gate_change']=True
    rep['private_reconstructed_audio_deleted']=True;rep['no_private_raw_or_GT_or_PCM_exported']=True
    out=f/f'{no}-actual-old-vs-native-physical-scalars.json';out.write_text(json.dumps(rep,ensure_ascii=False,indent=2,default=lambda x:float(x) if isinstance(x,np.floating) else int(x) if isinstance(x,np.integer) else str(x))+'\n')
    print(no,'comparison',rep.get('native_reconstruction_binding'),'SHA',sha(out.read_bytes()),flush=True)
if __name__=='__main__':
    for a in sys.argv[1:]:main(a)
