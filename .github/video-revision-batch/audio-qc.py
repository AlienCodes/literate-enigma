#!/usr/bin/env python3
"""Measure accepted vs actual reconstructed public audio; never rebuild audio.

Only decoded final MP4 samples, public timing/control data and selected final-file
clips enter the report. Private TTS caches and raw ground-truth files are unused.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess

import numpy as np
import pyloudnorm as pyln
from scipy import signal

SR = 48000
STEP = 480


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def decode(path):
    raw = subprocess.check_output(['ffmpeg','-v','error','-nostdin','-i',str(path),
        '-map','0:a:0','-vn','-ac','1','-ar',str(SR),'-f','f32le','-'])
    return np.frombuffer(raw,np.float32).astype(np.float64)


def gated(values):
    values=np.asarray(values); values=values[values>-70]
    if not len(values): return None
    threshold=10*np.log10(np.mean(10**(values/10)))-10
    return float(10*np.log10(np.mean(10**(values[values>threshold]/10))))


def r128(path):
    result=subprocess.run(['ffmpeg','-hide_banner','-nostdin','-nostats','-v','verbose',
        '-i',str(path),'-map','0:a:0','-vn','-af','ebur128=framelog=verbose:peak=true',
        '-f','null','-'],capture_output=True,text=True,check=True)
    rows=re.findall(r't:\s*([\d.]+)\s+TARGET:\S+ LUFS\s+M:\s*(-?[\d.]+|-inf)',result.stderr)
    moments=np.array([(float(t),float(m)) for t,m in rows])
    assert len(moments)>10,'Actual ffmpeg R128 records missing'
    integrated=re.findall(r'Integrated loudness:\s+I:\s*(-?[\d.]+)',result.stderr)
    true_peak=re.findall(r'True peak:\s+Peak:\s*(-?[\d.]+)',result.stderr)
    lra=re.findall(r'Loudness range:\s+LRA:\s*([\d.]+)',result.stderr)
    return moments,{'integrated_lufs':float(integrated[-1]),'true_peak_dbtp':float(true_peak[-1]),
        'lra_lu':float(lra[-1])},result.stderr


def finite(value):
    return float(value) if np.isfinite(value) else None


def difference(a,b):
    return a-b if a is not None and b is not None else None


def measure(audio,span,moments=None):
    start,end=span; value=audio[round(start*SR):round(end*SR)]
    n=len(value)//STEP
    rms=10*np.log10(np.mean(value[:n*STEP].reshape(n,STEP)**2,axis=1)+1e-30)
    active=rms[rms>-45]
    loudness=pyln.Meter(SR).integrated_loudness(value) if len(value)>=.4*SR else -np.inf
    selected=moments[(moments[:,0]>=start+.4-1e-5)&(moments[:,0]<=end+.05),1] if moments is not None else []
    return {'start_s':start,'end_s':end,'crop_bs1770_lufs':finite(loudness),
        'gated_400ms_lufs':gated(selected) if len(selected) else None,
        'max_400ms_lufs':float(max(selected)) if len(selected) else None,
        'active_10ms_rms_dbfs':finite(10*np.log10(np.mean(10**(active/10)))) if len(active) else None,
        'rms_dbfs':finite(20*np.log10(np.sqrt(np.mean(value**2))+1e-30)),
        'sample_peak_dbfs':finite(20*np.log10(max(abs(value))+1e-30))}


def fit(old,new):
    denominator=float(np.dot(old,old))
    gain=float(np.dot(old,new)/denominator) if denominator else 1.
    residual=new-gain*old
    return {'gain_db':float(20*np.log10(max(gain,1e-20))),
        'correlation':float(np.dot(old,new)/(np.linalg.norm(old)*np.linalg.norm(new)+1e-30)),
        'gain_compensated_residual_snr_db':float(10*np.log10((np.mean((gain*old)**2)+1e-30)/(np.mean(residual**2)+1e-30)))}


def alignment_lag(old,new,spans,margin_seconds=.03):
    lags=[]
    for start,end in spans:
        lo=round(start*SR);hi=round(end*SR); margin=round(margin_seconds*SR)
        template=old[lo:hi];search=new[max(0,lo-margin):hi+margin]
        corr=signal.correlate(search,template,mode='valid',method='fft')
        lags.append(int(np.argmax(corr))-margin)
    return int(np.median(lags)),lags


def align_new(new,lag,length):
    if lag>=0: value=new[lag:]
    else: value=np.pad(new,(-lag,0))
    return value[:length] if len(value)>=length else np.pad(value,(0,length-len(value)))


def source_value(document,pointer):
    for key in pointer.strip('/').split('/'):document=document[key]
    return document


def waveform_plot(old,new,span,path,title):
    # Pillow is already part of the pinned production environment.
    from PIL import Image,ImageDraw,ImageFont
    im=Image.new('RGB',(1200,420),'white');d=ImageDraw.Draw(im)
    try: font=ImageFont.truetype('DejaVuSans.ttf',18)
    except OSError:font=ImageFont.load_default()
    d.text((30,12),title,fill='black',font=font)
    d.text((30,40),'10ms RMS dBFS: accepted gray / actual reconstruction blue',fill='black',font=font)
    for db in (-50,-40,-30,-20,-10):
        y=370-(db+55)/50*280;d.line((70,y,1160,y),fill='#dddddd');d.text((15,y-10),str(db),fill='black',font=font)
    start,end=span
    for value,color in ((old,'#999999'),(new,'#1368bc')):
        x=value[round(start*SR):round(end*SR)];n=len(x)//STEP
        rms=10*np.log10(np.mean(x[:n*STEP].reshape(n,STEP)**2,axis=1)+1e-30)
        points=[(70+i/max(1,n-1)*1090,370-(min(-5,max(-55,float(v)))+55)/50*280) for i,v in enumerate(rms)]
        if len(points)>1:d.line(points,fill=color,width=2)
    d.text((70,385),f'{start:.2f}s',fill='black',font=font);d.text((1060,385),f'{end:.2f}s',fill='black',font=font)
    im.save(path)


def audit(args):
    references=json.loads((Path(__file__).with_name('audio-qc-reference.json')).read_text())
    ref=references[args.article];out=Path(args.output);out.parent.mkdir(parents=True,exist_ok=True)
    old=decode(args.accepted_source);new_raw=decode(args.canonical_video)
    old_tm,old_global,old_log=r128(args.accepted_source)
    new_tm,new_global,new_log=r128(args.canonical_video)
    (out.parent/f'{args.article}-accepted-r128.log').write_text(old_log)
    (out.parent/f'{args.article}-actual-r128.log').write_text(new_log)
    title_a21=None
    if args.article=='12':
        module_path=Path(__file__).with_name('title_k_qc.py')
        spec=importlib.util.spec_from_file_location('original_title_A21',module_path)
        title_module=importlib.util.module_from_spec(spec);spec.loader.exec_module(title_module)
        tools=Path(__file__).resolve().parents[2]/'视频/工具'
        before=title_module.measure_title(args.accepted_source,tools)
        after=title_module.measure_title(args.canonical_video,tools)
        title_a21={'accepted':before,'actual_canonical':after,
            'actual_voice_endpoint_shift_s':after['last_audible_5ms_window_end_seconds']-before['last_audible_5ms_window_end_seconds']}
        lag,local_lags=alignment_lag(old,new_raw,ref['alignment_reference_spans'],.18)
        prefix_lag,prefix_lags=alignment_lag(old,new_raw,[ref['title_unchanged_prefix_span']])
        new=align_new(new_raw,lag,len(old))
        switch=round(ref['allowed_audio_changes'][0][1]*SR)
        new[:switch]=new_raw[:switch]
        new_tm[new_tm[:,0]>ref['allowed_audio_changes'][0][1]+lag/SR,0]-=lag/SR
    else:
        lag,local_lags=alignment_lag(old,new_raw,ref['alignment_reference_spans'])
        new=align_new(new_raw,lag,len(old))
        new_tm[:,0]-=lag/SR
    accepted={k:measure(old,v,old_tm) for k,v in ref['units'].items()}
    actual={k:measure(new,v,new_tm) for k,v in ref['units'].items()}
    checks=[]
    def check(name,passed,**data):checks.append({'name':name,'passed':bool(passed),**data})
    check('accepted-public-source-sha256',sha(args.accepted_source)==ref['accepted_sha256'])
    duration_delta=(len(new_raw)-len(old))/SR
    if args.article=='12':
        check('actual-accepted-legacy-duplicate-confirmed',title_a21['accepted']['has_double_release_all_settings'])
        check('actual-canonical-original-A21-passes-all-settings',not title_a21['actual_canonical']['has_double_release_any_setting'] and title_a21['actual_canonical']['release_passes_all_settings'])
        check('title-removal-duration-shift-only',-.18<=lag/SR<=.01 and abs(duration_delta-lag/SR)<=.04 and abs(title_a21['actual_voice_endpoint_shift_s']-lag/SR)<=.025,duration_delta_s=duration_delta,body_shift_s=lag/SR,voice_endpoint_shift_s=title_a21['actual_voice_endpoint_shift_s'])
        check('unchanged-title-prefix-and-constant-body-timing',abs(prefix_lag)/SR<=.006 and max(local_lags)-min(local_lags)<=round(.006*SR),title_prefix_lag_samples=prefix_lag,body_lags_samples=local_lags)
        lo=round(.4*SR);hi=round((ref['allowed_audio_changes'][0][0]-.01)*SR)
        prefix=fit(old[lo:hi],new_raw[lo+prefix_lag:hi+prefix_lag])
        check('actual-title-before-controlled-k-is-unchanged',abs(prefix['gain_db'])<=.35 and prefix['correlation']>=.985 and prefix['gain_compensated_residual_snr_db']>=22,**prefix)
    else:
        check('duration-preserved',abs(duration_delta)<=.06,delta_s=duration_delta)
        check('encoding-alignment-only',abs(lag)/SR<=.02 and max(local_lags)-min(local_lags)<=round(.006*SR),lag_samples=lag,local_lags_samples=local_lags)
    media=json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','a:0','-show_entries','stream=sample_rate,channels','-of','json',str(args.canonical_video)]))['streams'][0]
    check('actual-original-audio-format',int(media['sample_rate'])==48000 and int(media['channels'])==1,actual=media)
    check('actual-no-digital-clipping-or-nonfinite',np.isfinite(new_raw).all() and np.max(abs(new_raw))<1.,sample_peak_dbfs=float(20*np.log10(np.max(abs(new_raw))+1e-30)))
    check('actual-true-peak-below-zero',new_global['true_peak_dbtp']<0.,measured_dbtp=new_global['true_peak_dbtp'])
    check('whole-track-level-preserved',abs(new_global['integrated_lufs']-old_global['integrated_lufs'])<=.8,accepted=old_global,actual=new_global)
    count=min(len(old),len(new))//STEP
    old_frames=old[:count*STEP].reshape(count,STEP);new_frames=new[:count*STEP].reshape(count,STEP)
    old_db=10*np.log10(np.mean(old_frames**2,axis=1)+1e-30);new_db=10*np.log10(np.mean(new_frames**2,axis=1)+1e-30)
    times=(np.arange(count)+.5)*.01;unmodified=(old_db>-40)
    padding=ref.get('encoding_boundary_padding_s',.15)
    for start,end in ref['allowed_audio_changes']:
        unmodified&=~((times>=start-padding)&(times<=end+padding))
    outside=fit(old_frames[unmodified].ravel(),new_frames[unmodified].ravel())
    frame_deltas=new_db[unmodified]-old_db[unmodified]
    check('outside-approved-ranges-same-voice-timing-gain',abs(outside['gain_db'])<=.35 and outside['correlation']>=.985 and outside['gain_compensated_residual_snr_db']>=22 and np.percentile(abs(frame_deltas),95)<=.8,**outside,p95_absolute_frame_gain_db=float(np.percentile(abs(frame_deltas),95)))
    outside_blocks=[]
    for start in range(0,count,100):
        keep=unmodified[start:start+100]
        if int(keep.sum())<10:continue
        block=fit(old_frames[start:start+100][keep].ravel(),new_frames[start:start+100][keep].ravel())
        block['start_s']=start*.01
        block['passed']=abs(block['gain_db'])<=.5 and block['correlation']>=.98 and block['gain_compensated_residual_snr_db']>=20
        outside_blocks.append(block)
    check('every-untouched-active-one-second-block-preserved',bool(outside_blocks) and all(b['passed'] for b in outside_blocks),checked_blocks=len(outside_blocks),failed_blocks=[b for b in outside_blocks if not b['passed']])
    changed_quiet=old_db<-70
    in_allowed=np.zeros(count,dtype=bool)
    for start,end in ref['allowed_audio_changes']:in_allowed|=(times>=start)&(times<=end)
    quiet_levels=new_db[changed_quiet&in_allowed]
    check('no-new-click-or-noise-in-modified-pauses',not len(quiet_levels) or max(quiet_levels)<-55,maximum_actual_10ms_dbfs=float(max(quiet_levels)) if len(quiet_levels) else None)
    requested=json.loads((Path(args.request)/f'视频/脚本/{args.article}.json').read_text())
    for pointer,expected in ref['requested_audio_controls'].items():
        value=source_value(requested,pointer);check('requested-control:'+pointer,value==expected,actual=value,expected=expected)
    for pointer in ref.get('requested_absent_controls',[]):
        try:source_value(requested,pointer);absent=False
        except KeyError:absent=True
        check('requested-removed-duplicate-control:'+pointer,absent)
    segment_file=Path(args.work)/f'work_{args.article}/分段.json'
    public_piece_ranges={}
    if segment_file.exists():
        segments=json.loads(segment_file.read_text())
        for sentence,piece in ref['piece_references']:
            rows=segments[sentence];row=next(r for r in rows if int(r['段'])==piece)
            public_piece_ranges[f'{sentence}:{piece}']=row['时刻']
    check('actual-production-piece-timings-present',len(public_piece_ranges)==len(ref['piece_references']))
    unit_fits={}
    for key,expected_gain in ref['constant_gain_units'].items():
        start,end=ref['units'][key];lo=round(start*SR);hi=round(end*SR)
        measured=fit(old[lo:hi],new[lo:hi]);unit_fits[key]=measured
        delta_lu=difference(actual[key]['crop_bs1770_lufs'],accepted[key]['crop_bs1770_lufs'])
        check('actual-gain-and-same-waveform:'+key,delta_lu is not None and abs(measured['gain_db']-expected_gain)<=.45 and measured['correlation']>=.985 and measured['gain_compensated_residual_snr_db']>=20 and abs(delta_lu-expected_gain)<=.55,expected_gain_db=expected_gain,actual_lufs_delta=delta_lu,**measured)
    if args.article=='10':
        delta_peak=difference(actual['If_so']['max_400ms_lufs'],actual['last_main']['max_400ms_lufs'])
        delta_mean=difference(actual['If_so']['crop_bs1770_lufs'],actual['last_main']['crop_bs1770_lufs'])
        check('actual-final-phrase-strength-and-mean',delta_peak is not None and delta_mean is not None and abs(delta_peak)<=1.0 and abs(delta_mean)<=2.6,strongest400ms_delta_lu=delta_peak,mean_delta_lu=delta_mean)
    elif args.article=='51':
        delta_peak=actual['opening_OK']['max_400ms_lufs']-actual['following_words']['max_400ms_lufs']
        check('actual-opening-OK-strength',abs(delta_peak)<=1.1,strongest400ms_delta_lu=delta_peak)
        local_delta=difference(actual['OW_letters']['active_10ms_rms_dbfs'],actual['oll_wright']['active_10ms_rms_dbfs'])
        parallel_delta=difference(actual['OW_phrase']['crop_bs1770_lufs'],actual['KY_phrase']['crop_bs1770_lufs'])
        check('actual-OW-oll-wright-local-continuity',local_delta is not None and parallel_delta is not None and abs(local_delta)<=1.5 and abs(parallel_delta)<=2.5,letters_minus_oll_wright_active_rms_db=local_delta,OW_minus_KY_lufs=parallel_delta)
        if 'S2:3' in public_piece_ranges:
            start,end=public_piece_ranges['S2:3'];at=(times>=max(start,19.71))&(times<=min(end,22.02))&(old_db>-35)
            expected=-2.+4.5*(times[at]-start)/(end-start)
            error=(new_db[at]-old_db[at])-expected
            check('actual-approved-smooth-ramp',len(error)>20 and np.median(abs(error))<=.65 and np.percentile(abs(error),95)<=1.1,median_error_db=float(np.median(abs(error))),p95_error_db=float(np.percentile(abs(error),95)),actual_piece_range=[start,end])
            lo=round(max(start,19.71)*SR);hi=round(min(end,22.02)*SR)
            ts=np.arange(lo,hi)/SR;gain_db=-2.+4.5*(ts-start)/(end-start)
            predicted=old[lo:hi]*10**(gain_db/20);wave=fit(predicted,new[lo:hi]);unit_fits['OW_ramp']=wave
            check('actual-ramp-same-waveform-no-new-distortion',abs(wave['gain_db'])<=.45 and wave['correlation']>=.985 and wave['gain_compensated_residual_snr_db']>=20,**wave)
    elif args.article=='44':
        # Preserve the following two groups and natural within-group prosody.
        first=actual['Norway_Finland'];following=actual['with_border_crossings']
        mean_delta=first['crop_bs1770_lufs']-following['crop_bs1770_lufs']
        active_delta=first['active_10ms_rms_dbfs']-following['active_10ms_rms_dbfs']
        peak_delta=first['max_400ms_lufs']-following['max_400ms_lufs']
        check('actual-S4-local-level-continuity',abs(mean_delta)<=.8 and abs(active_delta)<=1.2 and abs(peak_delta)<=2.8,
              first_minus_following_mean_lu=mean_delta,first_minus_following_active_rms_db=active_delta,
              first_minus_following_strongest400ms_lu=peak_delta)
        if 'S4:1' in public_piece_ranges:
            start,end=public_piece_ranges['S4:1']
            check('actual-S4-first-piece-boundary-preserved',abs(start-33.97)<=.12 and abs(end-36.30)<=.12,
                  actual_piece_range=[start,end],accepted_acoustic_range=[33.97,36.30])
        # Original A21 pure functions only; no producer/model or private GT.
        import ast
        tools=Path(__file__).resolve().parents[2]/'视频/工具'
        original=tools/'词尾辅音核对.py';tree=ast.parse(original.read_text())
        names={'frames_back','release','centroid','lf_peak','periodicity','judge'}
        nodes=[node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name in names]
        ns={'np':np,'ss':signal,'SR':24000,'F5':120,'AUD_DB':-55.,'TH_HF':-36.,'TH_P':-33.,
            'CEN_MIN':1000,'DUR_MAX':110,'LF_MAX':-20.,'PER_MAX':.6,
            'HP':signal.butter(6,2000,'highpass',fs=24000,output='sos'),
            'LP8':signal.butter(6,800,'lowpass',fs=24000,output='sos')}
        exec(compile(ast.Module(body=nodes,type_ignores=[]),str(original),'exec'),ns)
        right_t=[]
        value=signal.resample_poly(new[round(33.90*SR):round(44.98*SR)],1,2)
        n=len(value)//120;reference=float(np.sqrt(np.mean(value[:n*120].reshape(n,120)**2,axis=1)).max())
        hp=signal.sosfiltfilt(ns['HP'],value)
        for endpoint in (36.295,36.300,36.305):
            release=ns['release'](value,hp,round((endpoint-33.9)*24000),reference)
            right_t.append({'endpoint_s':endpoint,'original_A21_passes':bool(ns['judge'](value,release,'t')),
                            'release_metrics':release})
        unit_fits['actual_right_t_A21']=right_t
        check('actual-S4-right-t-release-preserved',all(row['original_A21_passes'] for row in right_t),
              original_A21_actual_public_audio=right_t)
    # Voice/onset integrity is judged on decoded reconstructed samples, not the proposal model.
    try:
        import parselmouth
        pitch_results={}
        for key in ref['pitch_units']:
            start,end=ref['units'][key];lo=round(start*SR);hi=round(end*SR)
            pitches=[parselmouth.Sound(v[lo:hi],sampling_frequency=SR).to_pitch_ac(time_step=.01,pitch_floor=60,pitch_ceiling=400).selected_array['frequency'] for v in (old,new)]
            size=min(map(len,pitches));a,b=(v[:size] for v in pitches);good=(a>0)&(b>0);cents=abs(1200*np.log2(b[good]/a[good]))
            result={'voiced_pairs':int(good.sum()),'median_absolute_cents':float(np.median(cents)) if len(cents) else None,'p90_absolute_cents':float(np.percentile(cents,90)) if len(cents) else None};pitch_results[key]=result
            check('actual-pitch-preserved:'+key,len(cents)>10 and result['median_absolute_cents']<=40 and result['p90_absolute_cents']<=150,**result)
    except ImportError:
        pitch_results={};check('actual-pitch-measurement-available',False)
    import soundfile as sf
    clip_files=[]
    for key,span in ref['delivery_clips'].items():
        clip_new=new_raw if args.article=='12' else new
        for label,value in (('accepted',old),('actual',clip_new)):
            fn=out.parent/f'{args.article}-{key}-{label}.wav';sf.write(fn,value[round(span[0]*SR):round(span[1]*SR)],SR,subtype='PCM_16');clip_files.append(fn.name)
        waveform_plot(old,clip_new,span,out.parent/f'{args.article}-{key}-actual-comparison.png',f'{args.article}: {key} actual MP4 samples')
    evidence={'article':args.article,'passed':all(c['passed'] for c in checks),'validation_basis':'Actual accepted and reconstructed public MP4 decoded samples; no simulated values determine passed.','accepted_sha256':sha(args.accepted_source),'canonical_sha256':sha(args.canonical_video),'accepted_global':old_global,'actual_global':new_global,'accepted_units':accepted,'actual_units':actual,'actual_waveform_fits':unit_fits,'pitch_comparison':pitch_results,'actual_public_piece_ranges':public_piece_ranges,'actual_title_A21':title_a21,'checks':checks,'public_listening_clips':clip_files,'subjective_listening':'Public final-file clips saved for root listening; this program does not claim listening acceptance.','private_caches_or_GT_exported':False}
    out.write_text(json.dumps(evidence,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'article':args.article,'passed':evidence['passed'],'failed_checks':[c['name'] for c in checks if not c['passed']]},ensure_ascii=False))
    return evidence


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--article',choices=['10','12','44','51'],required=True)
    parser.add_argument('--accepted-source',required=True)
    parser.add_argument('--canonical-video',required=True)
    parser.add_argument('--work',required=True)
    parser.add_argument('--request',required=True)
    parser.add_argument('--output',required=True)
    arguments=parser.parse_args()
    result=audit(arguments)
    raise SystemExit(0 if result['passed'] else 1)
