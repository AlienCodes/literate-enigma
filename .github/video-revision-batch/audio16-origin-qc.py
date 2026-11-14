#!/usr/bin/env python3
"""Supplemental actual-file QA for the single approved16 Origin stress correction.

The original complete production quality gates must pass separately. This helper
cannot approve an article by itself and never changes sound or confirmations.
"""
import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import subprocess
import sys
import numpy as np

SR, STEP = 48000, 480

def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def aac_sha(path):
    return hashlib.sha256(subprocess.check_output(['ffmpeg', '-v', 'error', '-nostdin', '-i', str(path),
        '-map', '0:a:0', '-c:a', 'copy', '-f', 'adts', '-'])).hexdigest()

def audit(args):
    folder = Path(__file__).parent
    u, q = module('shared_existing_audio_numeric', folder / 'audio-qc.py'), module('shared_existing_alignment', folder / 'audio-a21-qc.py')
    refpath = folder / 'audio16-origin-qc-reference.json'
    ref = json.loads(refpath.read_text())
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    checks = []
    def check(name, ok, **data):
        checks.append({'name': name, 'passed': bool(ok), **data})
    report = {'article': '16', 'passed': False, 'repair_applied': True,
        'diagnostic_only': False, 'production_delivery_eligible': False,
        'kind': 'controlled_audio_repair', 'scope': 'Only correct Origin stress in S15 and restore ordinary next dispatch; preserve all other audio.',
        'original_quality_gates_modified': False, 'subjective_listening_claimed': False,
        'requires_separate_original_complete_pipeline_pass': True,
        'private_raw_GT_or_cache_arrays_exported': False, 'checks': checks,
        'program_sha256': sha(__file__), 'reference_sha256': sha(refpath),
        'accepted_sha256': sha(args.accepted_source), 'canonical_sha256': sha(args.canonical_video)}
    try:
        request = Path(args.request) / '视频/脚本/16.json'
        data = json.loads(request.read_text())
        check('exact-approved-request-source', sha(request) == ref['approved_request_sha256'])
        check('exact-approved-accepted-MP4', sha(args.accepted_source) == ref['accepted_sha256'])
        check('accepted-approved-AAC', aac_sha(args.accepted_source) == ref['accepted_aac_sha256'])
        actual_aac = aac_sha(args.canonical_video)
        check('corrected-Origin-AAC-honestly-differs-from-old-pronunciation', actual_aac != ref['accepted_aac_sha256'])
        raw = Path(args.work) / 'work_16/a.wav'
        check('actual-producer-PCM-present', raw.is_file())
        report['actual_producer_PCM_sha256'] = sha(raw) if raw.is_file() else None
        cache_report_path = output.parent / '16-native-correct-Origin-cache-readback.json'
        cache = json.loads(cache_report_path.read_text())
        check('actual-certified-Origin-native-cache-readback',
            cache['exact_certified_internal_reference_cache_verified'] is True
            and cache['audio_inference_performed'] is False
            and cache['private_cache_or_source_modified'] is False
            and cache['maker_SHA256'] == ref['certified_maker_sha256']
            and cache['contract_SHA256'] == ref['native_cache_contract_sha256']
            and cache['program_SHA256'] == ref['native_cache_readback_program_sha256'])
        check('same-exact-frozen-request-used-for-native-Origin-cache-readback', cache['request_SHA256'] == sha(request))
        check('S13-ordinary-next-exact-accepted-text-mother-restored',
            cache['ordinary_next_exact_accepted_text_mother_verified'] is True
            and len(cache['ordinary_next_dispatch_observed']) == 1
            and cache['ordinary_next_dispatch_observed'][0]['actual_pkl_SHA256'] == ref['ordinary_next_accepted_text_mother']['pkl_sha256']
            and cache['ordinary_next_dispatch_observed'][0]['actual_array_SHA256'] == ref['ordinary_next_accepted_text_mother']['array_sha256'])
        observed = {row['native_cache_filename']: row['actual_file_SHA256'] for row in cache['all_four_actual_file_readbacks']}
        check('all-four-correct-Origin-native-cache-files-exact', observed == ref['native_cache_files_sha256'])
        report['certified_correct_Origin_cache_readback'] = {'file': cache_report_path.name, 'sha256': sha(cache_report_path),
            'actual_native_cache_key': cache['actual_native_cache_key'], 'input_bindings': cache['producer_input_bindings']}
        keys = ref['audio_control_keys']
        check('request-all-approved-audio-controls-exact', {k: data[k] for k in keys if k in data} == ref['approved_audio_controls'])
        meta = q.actual_metadata(args.work, '16', len(data['sentences']))
        check('actual-native-timings-and-working-source-present', meta is not None)
        if meta is None:
            raise ValueError('Native source and original segment metadata are required.')
        check('actual-working-all-approved-audio-controls-exact', {k: meta['source'][k] for k in keys if k in meta['source']} == ref['approved_audio_controls'])
        report['actual_native_metadata'] = {k: v for k, v in meta.items() if k != 'source'}
        old, current = u.decode(args.accepted_source), u.decode(args.canonical_video)
        _, ol, oldlog = u.r128(args.accepted_source)
        _, nl, newlog = u.r128(args.canonical_video)
        (output.parent / '16-origin-accepted-r128.log').write_text(oldlog)
        (output.parent / '16-origin-actual-r128.log').write_text(newlog)
        report['accepted_global'], report['actual_global'] = ol, nl
        media = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-select_streams', 'a:0',
            '-show_entries', 'stream=sample_rate,channels', '-of', 'json', str(args.canonical_video)]))['streams'][0]
        check('original-audio-format', int(media['sample_rate']) == SR and int(media['channels']) == 1)
        stream_info = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-select_streams', 'v:0',
            '-show_entries', 'stream=width,height', '-of', 'json', str(args.canonical_video)]))['streams']
        check('actual-original-canonical-4K-present', len(stream_info) == 1 and
            (stream_info[0]['width'], stream_info[0]['height']) == (3840, 2160))
        check('finite-and-no-digital-clipping', len(current) > 0 and np.isfinite(current).all() and np.max(np.abs(current)) < 1.)
        check('true-peak-below-zero', nl['true_peak_dbtp'] < 0., measured_dbtp=nl['true_peak_dbtp'])
        check('whole-track-level-preserved', abs(nl['integrated_lufs'] - ol['integrated_lufs']) <= .8, accepted=ol, actual=nl)
        begin, end = ref['old_change_span_s']
        padding = .15  # Existing actual-audio QC AAC boundary allowance.
        blocks = []
        for zone, lo, hi in [('before', 0., begin - padding), ('after', end + padding, len(old) / SR)]:
            for second in range(math.floor(lo), math.ceil(hi)):
                a, b = math.ceil(max(lo, second) * 100), math.floor(min(hi, second + 1) * 100)
                if b <= a:
                    continue
                frame = old[a * STEP:b * STEP].reshape(-1, STEP)
                db = 10 * np.log10(np.mean(frame * frame, axis=1) + 1e-30)
                active = db > -40
                if active.sum() < 10:
                    continue
                alignment = q.ncc_lag(old, current, a / 100, b / 100)
                if alignment is None:
                    blocks.append({'zone': zone, 'old_start_s': a / 100, 'passed': False})
                    continue
                lag = alignment['lag_samples']
                observed = current[a * STEP + lag:b * STEP + lag]
                if len(observed) != frame.size:
                    blocks.append({'zone': zone, 'old_start_s': a / 100, 'passed': False})
                    continue
                fit = u.fit(frame[active].ravel(), observed.reshape(-1, STEP)[active].ravel())
                ok = abs(fit['gain_db']) <= .5 and fit['correlation'] >= .98 and fit['gain_compensated_residual_snr_db'] >= 20
                blocks.append({'zone': zone, 'old_start_s': a / 100, **alignment, **fit, 'passed': bool(ok)})
        pre = [r['lag_samples'] for r in blocks if r['zone'] == 'before' and 'lag_samples' in r]
        post = [r['lag_samples'] for r in blocks if r['zone'] == 'after' and 'lag_samples' in r]
        check('every-untouched-active-second-preserved', bool(blocks) and all(r['passed'] for r in blocks), failed=[r for r in blocks if not r['passed']])
        if not pre or not post:
            raise ValueError('Independent actual waveform alignments on both sides of the repaired tail are required.')
        lp, la = int(np.median(pre)), int(np.median(post))
        delta = (la - lp) / SR
        check('only-approved-Origin-stress-correction-duration-step', abs(lp) <= .02 * SR and abs(delta + .070) <= .020 and
            max(pre) - min(pre) <= .006 * SR and max(post) - min(post) <= .006 * SR and abs((len(current) - len(old)) / SR - delta) <= .04,
            before_lag_samples=lp, after_lag_samples=la, measured_Origin_correction_duration_step_s=delta, encoded_duration_delta_s=(len(current) - len(old)) / SR)
        aligned, _ = q.sample_shift(current, len(old), lp, la, (begin + end) / 2)
        count = len(old) // STEP
        frames, newframes = old[:count * STEP].reshape(-1, STEP), aligned[:count * STEP].reshape(-1, STEP)
        db, ndb = [10 * np.log10(np.mean(x * x, axis=1) + 1e-30) for x in (frames, newframes)]
        times = (np.arange(count) + .5) * .01
        outside = (times < begin - padding) | (times > end + padding)
        active = outside & (db > -40)
        fit = u.fit(frames[active].ravel(), newframes[active].ravel())
        p95 = float(np.percentile(np.abs(ndb[active] - db[active]), 95))
        check('outside-single-tail-range-same-voice-level-timing', abs(fit['gain_db']) <= .35 and fit['correlation'] >= .985 and fit['gain_compensated_residual_snr_db'] >= 22 and p95 <= .8,
            **fit, p95_absolute_10ms_gain_db=p95)
        quiet = outside & (db < -70)
        check('no-new-noise-in-untouched-pauses', not quiet.any() or ndb[quiet].max() < -55,
            maximum_actual_10ms_dbfs=float(ndb[quiet].max()) if quiet.any() else None)
        sentences, pitch = [], []
        for label, pieces in meta['segments'].items():
            index = int(label[1:])
            if index == 15:
                continue
            lag = lp if index < 15 else la
            a, b = pieces[0]['actual_time_s'][0], pieces[-1]['actual_time_s'][1]
            x, y = old[round(a * SR) - lag:round(b * SR) - lag], current[round(a * SR):round(b * SR)]
            if len(x) != len(y):
                raise ValueError('Untouched whole sentence was shortened: ' + label)
            fit = u.fit(x, y)
            sentences.append({'sentence': label, **fit, 'passed': abs(fit['gain_db']) <= .35 and fit['correlation'] >= .985 and fit['gain_compensated_residual_snr_db'] >= 22})
            ok, p = u.pitch_preservation(x, y)
            pitch.append({'sentence': label, 'passed': ok, **p})
        check('all-other-whole-sentences-preserved', len(sentences) == 17 and all(r['passed'] for r in sentences), failed=[r for r in sentences if not r['passed']])
        check('all-other-whole-sentence-pitch-preserved', len(pitch) == 17 and all(r['passed'] for r in pitch), failed=[r for r in pitch if not r['passed']])
        target = meta['segments']['S15']
        start, finish = target[0]['actual_time_s'][0], target[-1]['actual_time_s'][1]
        check('single-corrected-Origin-sentence-timing', abs(start - 110.365) <= .006
            and abs((finish - 119.370) - delta) <= .006,
            old_sentence_s=[110.365, 119.370], actual_sentence_s=[start, finish])
        om = u.measure(old, [110.365, 119.370])
        nm = u.measure(current, [start, finish])
        check('corrected-sentence-level-preserved',
            om['crop_bs1770_lufs'] is not None and nm['crop_bs1770_lufs'] is not None
            and abs(nm['crop_bs1770_lufs'] - om['crop_bs1770_lufs']) <= .8,
            accepted=om, actual=nm)
        report['untouched_active_blocks'], report['untouched_whole_sentences'], report['pitch'] = blocks, sentences, pitch
        report['alignment'] = {'before_samples': lp, 'after_samples': la, 'old_change_span_s': [begin, end], 'AAC_boundary_padding_s': padding}
        report['approved_correct_Origin_reference_evidence'] = ref['correct_Origin_evidence']
        report['passed'] = bool(checks) and all(x['passed'] for x in checks)
        report['production_delivery_eligible'] = report['passed']
    except Exception as exc:
        report['error'] = {'type': type(exc).__name__, 'message': str(exc)[:1600]}
        check('measurement-completed', False, error=report['error'])
    output.write_text(json.dumps(q.clean_json(report), ensure_ascii=False, indent=2, allow_nan=False) + '\n')
    print(json.dumps({'article': '16', 'passed': report['passed'], 'failed_checks': [r['name'] for r in checks if not r['passed']]}))
    return report

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--article', choices=['16'], required=True)
    for name in ['accepted-source', 'canonical-video', 'work', 'request', 'output']:
        parser.add_argument('--' + name, type=Path, required=True)
    sys.exit(0 if audit(parser.parse_args())['passed'] else 1)
