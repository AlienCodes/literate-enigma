#!/usr/bin/env python3
"""Exact article27 two-opening repair supplement, after all official gates.

The profile remains disabled until the measured source/candidate hashes and
selected gains are explicitly frozen. This never repairs or produces audio.
"""
import argparse
import importlib.util
import json
from pathlib import Path
import sys
import wave

import numpy as np

HERE = Path(__file__).resolve().parent
COMMON_SHA = '3d830350b30bcb818ce9e46a5e52ee722ef8b87aa2a5f1c3c4aff3e33d82ae12'
UTILITY_SHA = '3a2bd846386b16bd74e9785c548e97283131efcad9989b9e886f64e86e57c7c6'
SR = 48000


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    sys.modules[name] = value
    spec.loader.exec_module(value)
    return value


def audit(args):
    import hashlib
    sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
    report = dict(article='27', passed=False, repair_applied=False,
        diagnostic_only=bool(args.diagnostic), production_delivery_eligible=False,
        kind='exact-two-approved-opening-pieces-controlled-audio-repair',
        official_full_gates_are_separate_required_precondition=True,
        official_gates_replaced_or_thresholds_modified=False,
        program_sha256=sha(__file__))
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    checks = []
    try:
        reference = Path(args.reference or HERE/'audio27-controlled-qc-reference.json')
        profile = json.loads(reference.read_text())
        report['reference_file_sha256'] = sha(reference)
        if profile.get('article') != '27' or profile.get('enabled') is not True:
            raise ValueError('Article27 exact approved source/gains/fingerprints pending; profile disabled.')
        if args.article != '27':
            raise ValueError('This helper accepts article27 only.')
        assert sha(HERE/'audio-controlled-qc.py') == COMMON_SHA
        assert sha(HERE/'audio-qc.py') == UTILITY_SHA
        C = load('article27_pinned_shared_numeric_functions', HERE/'audio-controlled-qc.py')
        U = load('article27_unchanged_audio_numeric_utilities', HERE/'audio-qc.py')
        add = lambda name, passed, **kw: C.check_row(checks, name, passed, **kw)
        work = Path(args.work).resolve()
        request = Path(args.request).resolve()
        requested_path = request/'视频/脚本/27.json'
        generator_path = request/'视频/工具/初稿生成/gen27.py'
        actual_path = Path(args.actual_source or work/'scripts/27.json')
        raw_path = Path(args.raw_pcm or work/'work_27/a.wav')
        requested = json.loads(requested_path.read_text())
        actual = json.loads(actual_path.read_text())
        assert str(requested['no']).zfill(2) == str(actual['no']).zfill(2) == '27'
        fingerprints = dict(request_source_sha256=sha(requested_path),
            request_generator_sha256=sha(generator_path),
            actual_full_source_sha256=sha(actual_path), actual_raw_WAV_sha256=sha(raw_path),
            accepted_video_sha256=sha(args.accepted_source),
            canonical_video_sha256=sha(args.canonical_video),
            accepted_AAC_ADTS_sha256=C.aac_sha(args.accepted_source),
            canonical_AAC_ADTS_sha256=C.aac_sha(args.canonical_video))
        report.update(fingerprints=fingerprints,
            accepted_sha256=fingerprints['accepted_video_sha256'],
            canonical_sha256=fingerprints['canonical_video_sha256'],
            source_current_sha256=fingerprints['actual_full_source_sha256'])
        for key in ['request_source_sha256','request_generator_sha256','actual_raw_WAV_sha256',
                    'accepted_video_sha256','accepted_AAC_ADTS_sha256','canonical_AAC_ADTS_sha256']:
            add('exact-approved-fingerprint:'+key,
                fingerprints[key] == profile['fingerprints'][key],
                actual=fingerprints[key], expected=profile['fingerprints'][key])
        assert profile['existing_review_only_top_level_keys'] == ['核对确认','区间声音指纹']
        core = lambda d: {k:v for k,v in d.items() if k not in ('核对确认','区间声音指纹')}
        add('exact-entire-request-nonreview-document',
            C.canonical(core(requested)) == profile['approved_request_nonreview_document_sha256'])
        add('exact-entire-actual-nonreview-document',
            C.canonical(core(actual)) in profile['approved_actual_nonreview_document_sha256'],
            actual_nonreview_sha256=C.canonical(core(actual)))
        add('all-approved-audio-controls-exact',
            {k:actual.get(k) for k in profile['approved_audio_controls']} == profile['approved_audio_controls'])
        with wave.open(str(raw_path),'rb') as f:
            shape = dict(rate=f.getframerate(),channels=f.getnchannels(),width=f.getsampwidth(),samples=f.getnframes())
        add('actual-raw-WAV-shape',shape == profile['raw_WAV_shape'],actual=shape)
        info = json.loads(C.capture(['ffprobe','-v','error','-show_streams','-of','json',args.canonical_video]))
        audio = [s for s in info['streams'] if s['codec_type']=='audio']
        add('actual-original-audio-format',len(audio)==1 and int(audio[0]['sample_rate'])==48000 and int(audio[0]['channels'])==1)
        if not args.diagnostic:
            video = [s for s in info['streams'] if s['codec_type']=='video']
            add('production-original-canonical-4K-present',len(video)==1 and (video[0]['width'],video[0]['height'])==(3840,2160))
        old = U.decode(args.accepted_source)
        new = U.decode(args.canonical_video)
        add('actual-no-clipping-or-nonfinite',np.isfinite(new).all() and float(np.max(abs(new)))<1.,
            sample_peak_dbfs=float(20*np.log10(np.max(abs(new))+1e-30)))
        old_tm,old_global,old_log = U.r128(args.accepted_source)
        new_tm,new_global,new_log = U.r128(args.canonical_video)
        (output.parent/'27-controlled-accepted-r128.log').write_text(old_log)
        (output.parent/'27-controlled-actual-r128.log').write_text(new_log)
        report.update(accepted_global=old_global,actual_global=new_global)
        add('actual-true-peak-below-zero',new_global['true_peak_dbtp']<0,
            actual_dbtp=new_global['true_peak_dbtp'])
        add('whole-track-level-preserved',abs(new_global['integrated_lufs']-old_global['integrated_lufs'])<=.8,
            delta_lu=new_global['integrated_lufs']-old_global['integrated_lufs'])
        lag,lags = U.alignment_lag(old,new,profile['alignment_reference_spans'])
        add('duration-preserved',abs(len(new)-len(old))/SR<=.06,delta_s=(len(new)-len(old))/SR)
        add('encoding-alignment-only',abs(lag)/SR<=.02 and max(lags)-min(lags)<=round(.006*SR),
            lag_samples=lag,local_lags_samples=lags)
        aligned = U.align_new(new,lag,len(old))
        # Exact two producer pieces only. No broad sentence/range exemption.
        assert set(profile['approved_opening_units']) == {'S13#1','S14#1'}
        units = profile['approved_opening_units']
        for name,row in units.items():
            sentence = name.split('#')[0]
            # Bind every allowed window to the actual original first piece,
            # rather than accepting an arbitrary caller-supplied time range.
            assert row['span_s'] == profile['approved_producer_group_metadata'][sentence][0]['时刻']
        ranges = [row['span_s'] for row in units.values()]
        report['outside_measurements'] = C.outside_measurements(U,old,aligned,ranges,checks)
        fits = {}
        for name,row in units.items():
            span = row['span_s']
            start,end = span
            gain = row['gain_delta_dB']
            lo,hi = round(start*SR),round(end*SR)
            fit = U.fit(old[lo:hi],aligned[lo:hi])
            om,nm = U.measure(old,span,old_tm),U.measure(aligned,span,new_tm)
            delta = U.difference(nm['crop_bs1770_lufs'],om['crop_bs1770_lufs'])
            add('approved-gain-articulation-and-waveform:'+name,
                delta is not None and abs(fit['gain_db']-gain)<=.45 and abs(delta-gain)<=.55 and
                fit['correlation']>=.985 and fit['gain_compensated_residual_snr_db']>=20,
                expected_gain_db=gain,actual_lufs_delta=delta,accepted=om,actual=nm,**fit)
            fits[name]=fit
        report['actual_opening_waveform_fits']=fits
        tools = Path(args.tools or HERE.parents[1]/'视频/工具')
        for name,want in profile['original_tool_sha256'].items():
            assert sha(tools/name)==want, 'Original tool changed: '+name
        sys.path.insert(0,str(tools))
        R=C.module('响度一致性核对',tools/'响度一致性核对.py');R.FF='ffmpeg'
        Q=C.module('article27_original_health',tools/'音频体检.py')
        track,tm=C.original_full_track(R,Q,str(Path(args.canonical_video).resolve()),work,actual,checks)
        report['original_full_track_supplement']=track
        groups=json.loads((work/'work_27/分段.json').read_text())
        normalized={label:[{k:r[k] for k in ('段','增益','停顿','时刻')} for r in values]for label,values in groups.items()}
        add('actual-all-producer-group-times-and-gains-exact',normalized==profile['approved_producer_group_metadata'])
        import parselmouth
        spans=[('title',(track['title']['start'],track['title']['end']))] if track['title'] else []
        spans += [(r['sentence'],(r['start'],r['end'])) for r in track['sentences']]
        pitch={}
        for name,(start,end) in spans:
            lo,hi=round(start*SR),round(end*SR)
            tracks=[parselmouth.Sound(v[lo:hi],sampling_frequency=SR).to_pitch_ac(time_step=.01,pitch_floor=60,pitch_ceiling=400).selected_array['frequency']for v in (old,aligned)]
            count=min(map(len,tracks));a,b=(t[:count]for t in tracks);keep=(a>0)&(b>0);cents=abs(1200*np.log2(b[keep]/a[keep]))
            result=dict(voiced_pairs=len(cents),median_absolute_cents=float(np.median(cents))if len(cents)else None,p90_absolute_cents=float(np.percentile(cents,90))if len(cents)else None)
            add('actual-pitch-preserved:'+name,len(cents)>10 and result['median_absolute_cents']<=40 and result['p90_absolute_cents']<=150,**result)
            pitch[name]=result
        report['pitch_comparison']=pitch
        report['passed']=bool(checks) and all(r['passed']for r in checks)
        report['repair_applied']=report['passed']
        report['production_delivery_eligible']=report['passed'] and not args.diagnostic
    except BaseException as exc:
        report['error']=dict(type=type(exc).__name__,detail=str(exc))
    report['checks']=checks
    output.write_text(json.dumps(report,ensure_ascii=False,indent=2,default=lambda x:x.item() if isinstance(x,np.generic)else str(x))+'\n')
    return 0 if report['passed'] else 1


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--article',default='27')
    for arg in ['accepted-source','canonical-video','work','request','output']:
        p.add_argument('--'+arg,required=True)
    for arg in ['actual-source','raw-pcm','tools','reference']:
        p.add_argument('--'+arg)
    p.add_argument('--diagnostic',action='store_true')
    sys.exit(audit(p.parse_args()))
