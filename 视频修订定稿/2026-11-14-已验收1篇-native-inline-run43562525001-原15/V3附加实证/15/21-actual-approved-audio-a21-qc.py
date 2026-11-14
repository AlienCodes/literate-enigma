#!/usr/bin/env python3
"""Actual-MP4 QC for four specifically approved original-release repairs.

No TTS, raw producer PCM, cache or ground truth is read. The accepted MP4 is
only a baseline for unchanged sound. Its known duplicate release must fail.
The original official sound gates remain unchanged and mandatory upstream.
"""
import argparse
import ast
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import subprocess
import sys

import numpy as np
from scipy import signal

SR = 48000
STEP = 480
A21_SR = 24000
PHASES_S = (-.005, -.0025, 0., .0025, .005)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def utility_module():
    path = Path(__file__).with_name('audio-qc.py')
    spec = importlib.util.spec_from_file_location('approved_actual_audio_utilities', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def public_decode24(path):
    raw = subprocess.check_output(['ffmpeg', '-v', 'error', '-nostdin', '-i', str(path),
        '-map', '0:a:0', '-vn', '-ac', '1', '-ar', str(A21_SR), '-f', 'f32le', '-'])
    return np.frombuffer(raw, np.float32).astype(np.float64)


def original_a21(tools):
    path = Path(tools) / '词尾辅音核对.py'
    text = path.read_text()
    tree = ast.parse(text)
    functions = {'frames_back', 'release', 'centroid', 'lf_peak', 'periodicity', '双爆破', 'judge'}
    constants = {'F5', 'HP', 'TH_HF', 'TH_P', 'CEN_MIN', 'DUR_MAX', 'LP8', 'LF_MAX', 'PER_MAX'}
    selected = []
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name in functions:
            selected.append(node)
        elif isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id in constants for t in node.targets):
            selected.append(node)
    namespace = {'np': np, 'ss': signal, 'SR': A21_SR, 'AUD_DB': -55.}
    exec(compile(ast.Module(body=selected, type_ignores=[]), str(path) + '#unmodified-pure-A21', 'exec'), namespace)
    assert functions <= set(namespace) and constants <= set(namespace)
    return namespace, sha(path)


def a21_measure(audio24, sentence_span, endpoint, phoneme, original):
    """All sound is decoded public MP4; use the original 5ms/HP/LF functions."""
    lo = max(0, round(float(sentence_span[0]) * A21_SR))
    hi = min(len(audio24), round(float(sentence_span[1]) * A21_SR))
    x = audio24[lo:hi]
    F = original['F5']
    n = len(x) // F
    if n < 4:
        raise ValueError('Actual public sentence window is too short for A21.')
    ref = float(np.sqrt(np.mean(x[:n * F].reshape(n, F) ** 2, axis=1)).max())
    if ref <= 0:
        raise ValueError('Actual public sentence window has no sound.')
    hp = signal.sosfiltfilt(original['HP'], x)
    results = []
    for offset in PHASES_S:
        P = round((float(endpoint) + offset) * A21_SR) - lo
        if not 0 < P <= len(x):
            raise ValueError('Actual endpoint is outside its actual sentence window.')
        z = original['release'](x, hp, P, ref)
        previous = original['release'](x, hp, z[3][0], ref) if z else None
        double = original['双爆破'](x, hp, z, ref)
        def describe(value):
            if value is None:
                return None
            return {'fullband_db': value[0], 'above_2khz_db': value[1], 'duration_ms': value[2],
                    'actual_public_range_s': [(lo + k) / A21_SR for k in value[3]],
                    'closure_min_db': value[4], 'centroid_hz': original['centroid'](x, *value[3]),
                    'periodicity': original['periodicity'](x, *value[3]),
                    'below_800hz_peak_db': original['lf_peak'](x, *value[3])}
        results.append({'endpoint_offset_s': offset, 'actual_endpoint_s': float(endpoint) + offset,
                        'single_release_original_A21_passed': bool(original['judge'](x, z, phoneme)),
                        'double_release': double, 'main_release': describe(z), 'previous_release': describe(previous)})
    return {'sentence_window_s': list(sentence_span), 'endpoint_s': endpoint,
            'sample_rate': A21_SR, 'phase_results': results,
            'single_release_passed_all_phases': all(r['single_release_original_A21_passed'] for r in results),
            'double_release_detected_any_phase': any(r['double_release'] is not None for r in results),
            'double_release_detected_all_phases': all(r['double_release'] is not None for r in results)}


def ncc_lag(old, current, begin, end, search_margin=.18):
    i0, i1 = round(begin * SR), round(end * SR)
    template = old[i0:i1]
    margin = round(search_margin * SR)
    lo = max(0, i0 - margin)
    hi = min(len(current) - len(template), i0 + margin)
    if hi < lo or len(template) < STEP or float(template @ template) <= 1e-20:
        return None
    search = current[lo:hi + len(template)]
    c = signal.correlate(search, template, mode='valid', method='fft')
    cs = np.r_[0., np.cumsum(search * search)]
    energy = cs[len(template):] - cs[:-len(template)]
    values = c / (np.linalg.norm(template) * np.sqrt(np.maximum(energy, 1e-25)) + 1e-25)
    # Prevent FFT roundoff in digital silence from masquerading as correlation.
    valid = (energy > max(float(energy.max()) * 1e-8, 1e-12)) & (np.abs(values) <= 1.00001)
    if not valid.any():
        return None
    values = np.where(valid, values, -1.)
    j = int(np.argmax(values))
    return {'lag_samples': lo + j - i0, 'NCC_alignment': float(values[j])}


def sample_shift(current, old_length, before_lag, after_lag, split_s):
    indices = np.arange(old_length, dtype=np.int64)
    indices += np.where(indices < round(split_s * SR), before_lag, after_lag)
    valid = (indices >= 0) & (indices < len(current))
    aligned = np.zeros(old_length, np.float64)
    aligned[valid] = current[indices[valid]]
    return aligned, int((~valid).sum())


def actual_metadata(work, no, expected_sentences):
    work = Path(work)
    segment_path = work / f'work_{no}/分段.json'
    graft_path = work / f'work_{no}/词尾除阻.json'
    source_path = work / f'scripts/{no}.json'
    if not all(p.is_file() for p in (segment_path, graft_path, source_path)):
        return None
    data = json.loads(segment_path.read_text())
    assert set(data) == {f'S{i}' for i in range(1, expected_sentences + 1)}
    public = {}
    previous = -1.
    for i in range(1, expected_sentences + 1):
        label = f'S{i}'
        rows = data[label]
        assert rows and [int(r['段']) for r in rows] == list(range(1, len(rows) + 1))
        kept = []
        for row in rows:
            a, b = map(float, row['时刻'])
            assert math.isfinite(a) and math.isfinite(b) and 0 <= a < b and a >= previous
            previous = b
            kept.append({'piece': int(row['段']), 'actual_time_s': [a, b],
                         'gain_db': row.get('增益'), 'following_pause_s': row.get('停顿')})
        public[label] = kept
    grafts = json.loads(graft_path.read_text())
    assert isinstance(grafts, list)
    safe_grafts = [{k: row[k] for k in ('句', '位置', '开始', '结束') if k in row} for row in grafts]
    return {'segments': public, 'grafts': safe_grafts,
            'source': json.loads(source_path.read_text()),
            'file_sha256': {segment_path.name: sha(segment_path), graft_path.name: sha(graft_path),
                            source_path.name: sha(source_path)}}


def control_value(document, field, sentence, key):
    return document.get(field, {}).get(sentence, {}).get(key)


def clean_json(value):
    if isinstance(value, dict):
        return {str(k): clean_json(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [clean_json(v) for v in value]
    if isinstance(value, (bool, np.bool_)):
        return bool(value)
    if isinstance(value, (int, np.integer)):
        return int(value)
    if isinstance(value, (float, np.floating)):
        return float(value) if np.isfinite(value) else None
    return value


def spectrogram_figure(audio, endpoint, path, title):
    """A diagnostic image from the actual public MP4 decode; no verdict."""
    from PIL import Image, ImageDraw, ImageFont
    lo, hi = max(0., endpoint - .5), min(len(audio) / SR, endpoint + .25)
    x = audio[round(lo * SR):round(hi * SR)]
    f, t, p = signal.spectrogram(x, fs=SR, window='hann', nperseg=960,
                                 noverlap=840, mode='psd')
    use = f <= 10000
    db = 10 * np.log10(p[use] + 1e-18)
    z = np.clip((db + 110) / 70, 0, 1)
    rgb = np.stack([255 * z, 100 * z, 255 * (1 - z)], axis=2).astype('uint8')
    picture = Image.fromarray(rgb[::-1]).resize((1100, 440))
    result = Image.new('RGB', (1250, 550), 'white')
    result.paste(picture, (100, 65))
    draw = ImageDraw.Draw(result)
    try:
        font = ImageFont.truetype('DejaVuSans.ttf', 17)
    except OSError:
        font = ImageFont.load_default()
    draw.text((20, 12), title, font=font, fill='black')
    for hz in (0, 2000, 4000, 6000, 8000, 10000):
        y = 505 - hz / 10000 * 440
        draw.text((8, y - 8), str(hz) + 'Hz', font=font, fill='black')
    draw.text((100, 515), f'{lo:.3f}s', font=font, fill='black')
    draw.text((1090, 515), f'{hi:.3f}s', font=font, fill='black')
    result.save(path)


def audit(args):
    checks = []
    def check(name, passed, **values):
        checks.append({'name': name, 'passed': bool(passed), **values})
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    evidence = {'article': args.article, 'passed': False,
                'validation_basis': 'Actual accepted/current public MP4 decoded samples and actual native timing/control metadata only.',
                'original_official_sound_gates_modified': False, 'private_GT_cache_or_raw_producer_PCM_read': False,
                'checks': checks, 'subjective_listening_acceptance_claimed': False}
    try:
        references_path = Path(__file__).with_name('audio-a21-qc-reference.json')
        reference = json.loads(references_path.read_text())['articles'][args.article]
        utilities = utility_module()
        tools = Path(os.environ.get('XG_TOOLS', str(Path(__file__).resolve().parents[2] / '视频/工具')))
        original, original_hash = original_a21(tools)
        evidence.update({'program_sha256': sha(__file__), 'reference_file_sha256': sha(references_path),
                         'common_audio_utility_sha256': sha(Path(__file__).with_name('audio-qc.py')),
                         'original_A21_program_sha256': original_hash,
                         'accepted_sha256': sha(args.accepted_source), 'canonical_sha256': sha(args.canonical_video)})
        check('accepted-original-public-MP4-sha256', evidence['accepted_sha256'] == reference['accepted_sha256'])
        check('original-A21-program-exact-approved-version', original_hash == reference['original_A21_sha256'])
        request_path = Path(args.request) / f'视频/脚本/{args.article}.json'
        request = json.loads(request_path.read_text())
        check('exact-root-approved-request-source-sha256', sha(request_path) == reference['approved_request_sha256'],
              actual_sha256=sha(request_path), expected_sha256=reference['approved_request_sha256'])
        changed = reference['approved_control_change']
        sentence = changed['sentence']
        punct = changed['punctuation_key']
        check('approved-old-donor-removed-in-request', control_value(request, changed['removed_field'], sentence, punct) is None)
        check('approved-original-release-boost-exact-in-request',
              control_value(request, '除阻加强', sentence, punct) == changed['added_boost'],
              actual=control_value(request, '除阻加强', sentence, punct), expected=changed['added_boost'])
        requested_controls = {key: request[key] for key in reference['audio_control_keys'] if key in request}
        check('all-approved-request-audio-controls-exact', requested_controls == reference['approved_audio_controls'])
        old = utilities.decode(args.accepted_source)
        current = utilities.decode(args.canonical_video)
        old24 = public_decode24(args.accepted_source)
        current24 = public_decode24(args.canonical_video)
        old_moments, old_level, old_log = utilities.r128(args.accepted_source)
        new_moments, new_level, new_log = utilities.r128(args.canonical_video)
        (output.parent / f'{args.article}-a21-accepted-r128.log').write_text(old_log)
        (output.parent / f'{args.article}-a21-actual-r128.log').write_text(new_log)
        evidence['accepted_global'] = old_level
        evidence['actual_global'] = new_level
        media = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-select_streams', 'a:0',
            '-show_entries', 'stream=sample_rate,channels', '-of', 'json', str(args.canonical_video)]))['streams'][0]
        check('actual-original-audio-format', int(media['sample_rate']) == SR and int(media['channels']) == 1, actual=media)
        check('actual-no-digital-clipping-or-nonfinite', np.isfinite(current).all() and np.max(np.abs(current)) < 1.,
              sample_peak_dbfs=20 * np.log10(np.max(np.abs(current)) + 1e-30))
        check('actual-true-peak-below-zero', new_level['true_peak_dbtp'] < 0., measured_dbtp=new_level['true_peak_dbtp'])
        check('whole-track-level-preserved', abs(new_level['integrated_lufs'] - old_level['integrated_lufs']) <= .8,
              accepted=old_level, actual=new_level)
        old_a21 = a21_measure(old24, reference['accepted_sentence_context_s'],
                              reference['accepted_endpoint_s'], reference['phoneme'], original)
        evidence['accepted_original_A21'] = old_a21
        check('accepted-original-duplicate-reproduced', old_a21['double_release_detected_all_phases'])
        change_start, change_end = reference['approved_old_release_and_graft_span_s']
        padding = .15  # Same encoded-boundary allowance as the existing actual-audio QC.
        zones = [('before', 0., max(0., change_start - padding)),
                 ('after', min(len(old) / SR, change_end + padding), len(old) / SR)]
        block_rows = []
        for zone, begin, end in zones:
            for whole_second in range(math.floor(begin), math.ceil(end)):
                a, b = max(begin, float(whole_second)), min(end, float(whole_second + 1))
                lo, hi = math.ceil(a * 100), math.floor(b * 100)
                if hi <= lo:
                    continue
                sample = old[lo * STEP:hi * STEP]
                frames = sample.reshape(-1, STEP)
                levels = 10 * np.log10(np.mean(frames * frames, axis=1) + 1e-30)
                active = levels > -40
                if int(active.sum()) < 10:
                    continue
                match = ncc_lag(old, current, lo / 100, hi / 100)
                if match is None:
                    block_rows.append({'zone': zone, 'old_start_s': lo / 100, 'old_end_s': hi / 100,
                                       'passed': False, 'error': 'No actual independent waveform alignment.'})
                    continue
                lag = match['lag_samples']
                i, j = lo * STEP + lag, hi * STEP + lag
                if i < 0 or j > len(current):
                    block_rows.append({'zone': zone, 'old_start_s': lo / 100, 'old_end_s': hi / 100,
                                       'passed': False, 'error': 'Aligned active voice would be missing.'})
                    continue
                observed = current[i:j].reshape(-1, STEP)
                values = utilities.fit(frames[active].ravel(), observed[active].ravel())
                good = abs(values['gain_db']) <= .5 and values['correlation'] >= .98 and values['gain_compensated_residual_snr_db'] >= 20
                block_rows.append({'zone': zone, 'old_start_s': lo / 100, 'old_end_s': hi / 100,
                                   'active_10ms_frames': int(active.sum()), **match, **values, 'passed': bool(good)})
        evidence['untouched_active_one_second_blocks'] = block_rows
        pre = [r['lag_samples'] for r in block_rows if r['zone'] == 'before' and 'lag_samples' in r]
        post = [r['lag_samples'] for r in block_rows if r['zone'] == 'after' and 'lag_samples' in r]
        check('every-untouched-active-one-second-block-preserved', bool(block_rows) and all(r['passed'] for r in block_rows),
              checked_blocks=len(block_rows), failed_blocks=[r for r in block_rows if not r['passed']])
        check('independent-before-and-after-waveform-alignments-present', bool(pre) and bool(post))
        if not pre or not post:
            raise ValueError('Cannot establish actual voice alignment on both sides of the one approved word repair.')
        before_lag, after_lag = int(np.median(pre)), int(np.median(post))
        step = (after_lag - before_lag) / SR
        duration_delta = (len(current) - len(old)) / SR
        check('unchanged-before-and-after-timelines-each-constant',
              abs(before_lag) / SR <= .02 and max(pre) - min(pre) <= round(.006 * SR)
              and max(post) - min(post) <= round(.006 * SR),
              before_median_lag_s=before_lag / SR, after_median_lag_s=after_lag / SR,
              before_lag_spread_s=(max(pre) - min(pre)) / SR, after_lag_spread_s=(max(post) - min(post)) / SR)
        check('single-approved-donor-removal-duration-shift-only', -.18 <= step <= .01 and abs(duration_delta - step) <= .04,
              actual_audio_duration_delta_s=duration_delta, actual_after_minus_before_shift_s=step)
        aligned, padded = sample_shift(current, len(old), before_lag, after_lag, (change_start + change_end) / 2)
        evidence['alignment'] = {'before_lag_samples': before_lag, 'after_lag_samples': after_lag,
                                 'single_time_step_s': step, 'actual_duration_delta_s': duration_delta,
                                 'zero_padded_out_of_range_samples': padded,
                                 'approved_old_physical_change_span_s': [change_start, change_end],
                                 'encoding_boundary_padding_s': padding}
        count = len(old) // STEP
        old_frames = old[:count * STEP].reshape(count, STEP)
        new_frames = aligned[:count * STEP].reshape(count, STEP)
        old_db = 10 * np.log10(np.mean(old_frames * old_frames, axis=1) + 1e-30)
        new_db = 10 * np.log10(np.mean(new_frames * new_frames, axis=1) + 1e-30)
        times = (np.arange(count) + .5) * .01
        outside = (times < change_start - padding) | (times > change_end + padding)
        active = outside & (old_db > -40)
        assert active.any()
        outside_fit = utilities.fit(old_frames[active].ravel(), new_frames[active].ravel())
        frame_difference = new_db[active] - old_db[active]
        p95 = float(np.percentile(np.abs(frame_difference), 95))
        check('outside-exact-approved-release-and-graft-ranges-same-voice',
              abs(outside_fit['gain_db']) <= .35 and outside_fit['correlation'] >= .985
              and outside_fit['gain_compensated_residual_snr_db'] >= 22 and p95 <= .8,
              **outside_fit, p95_absolute_10ms_gain_db=p95)
        quiet = outside & (old_db < -70)
        quiet_max = float(new_db[quiet].max()) if quiet.any() else None
        check('no-new-click-or-noise-in-previously-quiet-untouched-regions',
              quiet_max is None or quiet_max < -55, maximum_actual_10ms_dbfs=quiet_max)
        metadata = actual_metadata(args.work, args.article, len(request['sentences']))
        check('actual-native-public-timings-and-working-source-present', metadata is not None)
        if metadata is not None:
            evidence['actual_native_timing_metadata'] = {key: value for key, value in metadata.items() if key != 'source'}
            actual_controls = {key: metadata['source'][key] for key in reference['audio_control_keys'] if key in metadata['source']}
            check('actual-working-all-approved-audio-controls-exact', actual_controls == reference['approved_audio_controls'])
            check('actual-working-old-donor-removed', control_value(metadata['source'], changed['removed_field'], sentence, punct) is None)
            check('actual-working-approved-original-boost-exact',
                  control_value(metadata['source'], '除阻加强', sentence, punct) == changed['added_boost'])
            where = '句末' if punct == '句末' else f'第{punct}个标点'
            still_grafted = [row for row in metadata['grafts'] if row.get('句') == sentence and row.get('位置') == where]
            check('actual-native-graft-record-has-no-removed-donor', not still_grafted, unexpected=still_grafted)
            target_rows = metadata['segments'][sentence]
            check('actual-native-sentence-times-inside-actual-audio',
                  all(0 <= row['actual_time_s'][0] < row['actual_time_s'][1] <= len(current) / SR
                      for parts in metadata['segments'].values() for row in parts))
            target_piece = len(target_rows) if punct == '句末' else int(punct)
            native_end = target_rows[target_piece - 1]['actual_time_s'][1]
            independent_end = reference['accepted_endpoint_s'] + after_lag / SR
            # Native segment times describe the producer PCM clock.  A21 reads
            # the decoded public AAC clock; their offset is diagnostic, not a
            # new acoustic gate.  Locate both the endpoint and context by the
            # independent public-to-public waveform alignments above.
            evidence['native_vs_public_endpoint_clock_diagnostic'] = {
                'actual_native_endpoint_s': native_end,
                'independently_mapped_public_endpoint_s': independent_end,
                'native_minus_public_endpoint_s': native_end - independent_end,
                'used_for_original_A21_endpoint': 'independent-public-waveform-alignment',
                'raw_public_clock_equality_assumed': False,
                'quality_acceptance_implied': False}
        # This also lets an uncorrected real old MP4 demonstrate its A21 defect
        # without native metadata; the required metadata check remains false.
        current_end = reference['accepted_endpoint_s'] + after_lag / SR
        current_span = [max(0., reference['accepted_sentence_context_s'][0] + before_lag / SR),
                        reference['accepted_sentence_context_s'][1] + after_lag / SR]
        current_a21 = a21_measure(current24, current_span, current_end, reference['phoneme'], original)
        evidence['actual_original_A21'] = current_a21
        check('actual-single-original-release-passes-every-original-A21-phase', current_a21['single_release_passed_all_phases'])
        check('actual-no-double-release-in-any-original-A21-phase', not current_a21['double_release_detected_any_phase'])
        sentences = []
        pitch = []
        if metadata is not None:
            target_index = int(sentence[1:])
            for label, parts in metadata['segments'].items():
                index = int(label[1:])
                if index == target_index:
                    continue
                lag = before_lag if index < target_index else after_lag
                na, nb = parts[0]['actual_time_s'][0], parts[-1]['actual_time_s'][1]
                oa, ob = na - lag / SR, nb - lag / SR
                a = old[round(oa * SR):round(ob * SR)]
                b = current[round(na * SR):round(nb * SR)]
                if len(a) != len(b):
                    raise ValueError(f'Actual/accepted aligned sample counts differ in untouched {label}.')
                values = utilities.fit(a, b)
                good = abs(values['gain_db']) <= .35 and values['correlation'] >= .985 and values['gain_compensated_residual_snr_db'] >= 22
                sentences.append({'sentence': label, 'actual_span_s': [na, nb], 'accepted_span_s': [oa, ob], **values, 'passed': bool(good)})
                preserved, proof = utilities.pitch_preservation(a, b)
                pitch.append({'sentence': label, 'passed': preserved, **proof})
            check('every-untouched-whole-sentence-preserved', bool(sentences) and all(r['passed'] for r in sentences),
                  checked_sentences=len(sentences), failed_sentences=[r for r in sentences if not r['passed']])
            check('untouched-whole-sentence-pitch-preserved', bool(pitch) and all(r['passed'] for r in pitch),
                  failed_sentences=[r for r in pitch if not r['passed']])
            # The unchanged voiced portion before the repaired unvoiced release
            # includes the target word's vowel; use the existing pitch limits.
            first = metadata['segments'][sentence][0]['actual_time_s'][0]
            old_first = first - before_lag / SR
            old_end = change_start - padding
            a = old[round(old_first * SR):round(old_end * SR)]
            b = current[round((old_first + before_lag / SR) * SR):round((old_end + before_lag / SR) * SR)]
            preserved, proof = utilities.pitch_preservation(a, b)
            check('voiced-prefix-before-controlled-release-pitch-preserved', preserved, **proof)
            # Existing -70/-55 quiet thresholds, using the centre of the actual
            # native pause; boundary exclusion remains the existing .15s.
            following_start = None
            if target_piece < len(metadata['segments'][sentence]):
                following_start = metadata['segments'][sentence][target_piece]['actual_time_s'][0]
            elif target_index < len(request['sentences']):
                following_start = metadata['segments'][f'S{target_index + 1}'][0]['actual_time_s'][0]
            if following_start is not None:
                q0, q1 = current_end + padding, following_start - padding
                if q1 > q0:
                    q = current[math.ceil(q0 * 100) * STEP:math.floor(q1 * 100) * STEP]
                    qlevels = 10 * np.log10(np.mean(q.reshape(-1, STEP) ** 2, axis=1) + 1e-30)
                    check('actual-controlled-word-following-pause-remains-quiet', qlevels.max() < -55,
                          actual_native_pause_centre_s=[q0, q1], maximum_10ms_dbfs=float(qlevels.max()))
        evidence['untouched_whole_sentence_waveform_checks'] = sentences
        evidence['untouched_whole_sentence_pitch_checks'] = pitch
        try:
            import soundfile as sf
            clips = []
            for role, audio, centre in [('accepted', old, reference['accepted_endpoint_s']), ('actual', current, current_end)]:
                lo, hi = max(0., centre - .5), min(len(audio) / SR, centre + .25)
                path = output.parent / f'{args.article}-a21-controlled-word-{role}.wav'
                sf.write(path, audio[round(lo * SR):round(hi * SR)], SR, subtype='PCM_16')
                clips.append({'file': path.name, 'sha256': sha(path), 'actual_MP4_time_s': [lo, hi], 'role': role})
            picture = output.parent / f'{args.article}-a21-actual-public-waveform.png'
            utilities.waveform_plot(old, aligned, [change_start - .35, change_end + .35], picture,
                                   f'{args.article}: actual public MP4; old gray / new aligned blue')
            spectrum = output.parent / f'{args.article}-a21-actual-public-spectrum.png'
            spectrogram_figure(current, current_end, spectrum, f'{args.article}: actual public MP4 spectrum')
            evidence['public_actual_listening_clips'] = clips
            evidence['actual_public_waveform_figure'] = {'file': picture.name, 'sha256': sha(picture)}
            evidence['actual_public_spectrum_figure'] = {'file': spectrum.name, 'sha256': sha(spectrum)}
        except Exception as diagnostic_error:
            # Review-artifact logistics do not create a new sound-quality gate.
            evidence['review_artifact_error'] = {'type': type(diagnostic_error).__name__, 'message': str(diagnostic_error)[:500]}
        evidence['passed'] = bool(checks) and all(r['passed'] for r in checks)
    except Exception as exc:
        evidence['error'] = {'type': type(exc).__name__, 'message': str(exc)[:1600]}
        check('actual-measurement-completed', False, error=evidence['error'])
        evidence['passed'] = False
    output.write_text(json.dumps(clean_json(evidence), ensure_ascii=False, indent=2, allow_nan=False) + '\n')
    print(json.dumps({'article': args.article, 'passed': evidence['passed'],
                      'failed_checks': [r['name'] for r in checks if not r['passed']]}, ensure_ascii=False))
    return evidence


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--article', required=True, choices=['15', '17', '18', '30'])
    parser.add_argument('--accepted-source', required=True, type=Path)
    parser.add_argument('--canonical-video', required=True, type=Path)
    parser.add_argument('--work', required=True, type=Path)
    parser.add_argument('--request', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    return 0 if audit(args)['passed'] else 1


if __name__ == '__main__':
    sys.exit(main())
