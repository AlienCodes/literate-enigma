#!/usr/bin/env python3
"""Supplemental actual-file QA for the single approved05 screening word-tail repair.

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
    refpath = folder / 'audio05-tail-qc-reference.json'
    ref = json.loads(refpath.read_text())
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    checks = []
    def check(name, ok, **data):
        checks.append({'name': name, 'passed': bool(ok), **data})
    report = {'article': '05', 'passed': False, 'repair_applied': False,
        'kind': 'controlled_audio_repair', 'scope': 'Only preserve the previously over-trimmed screening /ŋ/ tail at S12.',
        'original_quality_gates_modified': False, 'subjective_listening_claimed': False,
        'requires_separate_original_complete_pipeline_pass': True,
        'private_raw_GT_or_cache_arrays_exported': False, 'checks': checks,
        'program_sha256': sha(__file__), 'reference_sha256': sha(refpath),
        'accepted_sha256': sha(args.accepted_source), 'canonical_sha256': sha(args.canonical_video)}
    try:
        request = Path(args.request) / '视频/脚本/05.json'
        data = json.loads(request.read_text())
        check('exact-approved-request-source', sha(request) == ref['approved_request_sha256'])
        check('exact-approved-request-generator', sha(Path(args.request) / '视频/工具/初稿生成/gen05.py') == ref['approved_generator_sha256'])
        check('exact-approved-accepted-MP4', sha(args.accepted_source) == ref['accepted_sha256'])
        check('accepted-approved-AAC', aac_sha(args.accepted_source) == ref['accepted_aac_sha256'])
        actual_aac = aac_sha(args.canonical_video)
        check('actual-entire-AAC-matches-exact-approved-physical-source-reconstruction', actual_aac == ref['expected_actual_aac_sha256'], actual=actual_aac)
        raw = Path(args.work) / 'work_05/a.wav'
        check('actual-entire-producer-PCM-matches-approved-physical-source-reconstruction', raw.is_file() and sha(raw) == ref['expected_actual_pcm_sha256'],
            actual=sha(raw) if raw.is_file() else None)
        keys = ref['audio_control_keys']
        check('request-all-approved-audio-controls-exact', {k: data[k] for k in keys if k in data} == ref['approved_audio_controls'])
        meta = q.actual_metadata(args.work, '05', len(data['sentences']))
        check('actual-native-timings-and-working-source-present', meta is not None)
        if meta is None:
            raise ValueError('Native source and original segment metadata are required.')
        check('actual-working-all-approved-audio-controls-exact', {k: meta['source'][k] for k in keys if k in meta['source']} == ref['approved_audio_controls'])
        report['actual_native_metadata'] = {k: v for k, v in meta.items() if k != 'source'}
        old, current = u.decode(args.accepted_source), u.decode(args.canonical_video)
        _, ol, oldlog = u.r128(args.accepted_source)
        _, nl, newlog = u.r128(args.canonical_video)
        (output.parent / '05-tail-accepted-r128.log').write_text(oldlog)
        (output.parent / '05-tail-actual-r128.log').write_text(newlog)
        report['accepted_global'], report['actual_global'] = ol, nl
        media = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-select_streams', 'a:0',
            '-show_entries', 'stream=sample_rate,channels', '-of', 'json', str(args.canonical_video)]))['streams'][0]
        check('original-audio-format', int(media['sample_rate']) == SR and int(media['channels']) == 1)
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
        check('only-approved-105ms-complete-screening-tail-duration-restored', abs(lp) <= .02 * SR and abs(delta - .105) <= .006 and
            max(pre) - min(pre) <= .006 * SR and max(post) - min(post) <= .006 * SR and abs((len(current) - len(old)) / SR - delta) <= .04,
            before_lag_samples=lp, after_lag_samples=la, measured_tail_duration_restored_s=delta, encoded_duration_delta_s=(len(current) - len(old)) / SR)
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
            if index == 12:
                continue
            lag = lp if index < 12 else la
            a, b = pieces[0]['actual_time_s'][0], pieces[-1]['actual_time_s'][1]
            x, y = old[round(a * SR) - lag:round(b * SR) - lag], current[round(a * SR):round(b * SR)]
            if len(x) != len(y):
                raise ValueError('Untouched whole sentence was shortened: ' + label)
            fit = u.fit(x, y)
            sentences.append({'sentence': label, **fit, 'passed': abs(fit['gain_db']) <= .35 and fit['correlation'] >= .985 and fit['gain_compensated_residual_snr_db'] >= 22})
            ok, p = u.pitch_preservation(x, y)
            pitch.append({'sentence': label, 'passed': ok, **p})
        check('all-other-whole-sentences-preserved', len(sentences) == 18 and all(r['passed'] for r in sentences), failed=[r for r in sentences if not r['passed']])
        check('all-other-whole-sentence-pitch-preserved', len(pitch) == 18 and all(r['passed'] for r in pitch), failed=[r for r in pitch if not r['passed']])
        x = old[round(85.9 * SR):round((begin - padding) * SR)]
        y = current[round(85.9 * SR) + lp:round((begin - padding) * SR) + lp]
        ok, p = u.pitch_preservation(x, y)
        check('S12-voiced-prefix-before-restored-nasal-pitch-preserved', ok, **p)
        first, following = meta['segments']['S12'][:2]
        gaplo, gaphi = first['actual_time_s'][1] + padding, following['actual_time_s'][0] - padding
        check('original-S12-comma-still-present', abs(first['actual_time_s'][1] - 92.295) <= .006 and abs(following['actual_time_s'][0] - 92.675) <= .006)
        if gaphi > gaplo:
            z = current[math.ceil(gaplo * 100) * STEP:math.floor(gaphi * 100) * STEP].reshape(-1, STEP)
            peak = float((10 * np.log10(np.mean(z * z, axis=1) + 1e-30)).max())
            check('repaired-word-following-pause-remains-quiet', peak < -55, maximum_actual_10ms_dbfs=peak)
        report['untouched_active_blocks'], report['untouched_whole_sentences'], report['pitch'] = blocks, sentences, pitch
        report['alignment'] = {'before_samples': lp, 'after_samples': la, 'old_change_span_s': [begin, end], 'AAC_boundary_padding_s': padding}
        report['approved_weak_nasal_preservation_evidence'] = ref['weak_nasal_preservation_evidence']
        report['passed'] = bool(checks) and all(x['passed'] for x in checks)
        report['repair_applied'] = report['passed']
    except Exception as exc:
        report['error'] = {'type': type(exc).__name__, 'message': str(exc)[:1600]}
        check('measurement-completed', False, error=report['error'])
    output.write_text(json.dumps(q.clean_json(report), ensure_ascii=False, indent=2, allow_nan=False) + '\n')
    print(json.dumps({'article': '05', 'passed': report['passed'], 'failed_checks': [r['name'] for r in checks if not r['passed']]}))
    return report

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--article', choices=['05'], required=True)
    for name in ['accepted-source', 'canonical-video', 'work', 'request', 'output']:
        parser.add_argument('--' + name, type=Path, required=True)
    sys.exit(0 if audit(parser.parse_args())['passed'] else 1)
