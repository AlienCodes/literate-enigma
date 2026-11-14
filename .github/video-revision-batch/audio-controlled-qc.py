#!/usr/bin/env python3
"""Supplemental QC for exact root-approved intentional audio changes.

Called only after the unchanged official draft/final/stamp gates. This program
never synthesizes, repairs, writes a source, exports private PCM, or replaces an
official gate. Diagnostic mode cannot certify a production delivery.
"""
import argparse
import contextlib
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import wave

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SR = 48000
STEP = 480


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def canonical(document):
    return hashlib.sha256(json.dumps(document, ensure_ascii=False,
        separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    sys.modules[name] = value
    spec.loader.exec_module(value)
    return value


def capture(args):
    return subprocess.check_output([str(x) for x in args])


def aac_sha(path):
    return hashlib.sha256(capture(['ffmpeg', '-v', 'error', '-nostdin', '-i', path,
        '-map', '0:a:0', '-c:a', 'copy', '-f', 'adts', '-'])).hexdigest()


def json_safe(value):
    if isinstance(value, dict):
        return {str(k): json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_safe(v) for v in value]
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.floating):
        return float(value) if np.isfinite(value) else None
    if isinstance(value, float) and not np.isfinite(value):
        return None
    return value


def check_row(checks, name, passed, **details):
    checks.append(dict(name=name, passed=bool(passed), **json_safe(details)))


@contextlib.contextmanager
def directory(path):
    before = Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(before)


def outside_measurements(U, old, new, ranges, checks, padding=.15):
    count = min(len(old), len(new)) // STEP
    of = old[:count * STEP].reshape(count, STEP)
    nf = new[:count * STEP].reshape(count, STEP)
    odb = 10 * np.log10(np.mean(of ** 2, axis=1) + 1e-30)
    ndb = 10 * np.log10(np.mean(nf ** 2, axis=1) + 1e-30)
    times = (np.arange(count) + .5) * .01
    untouched = odb > -40
    allowed = np.zeros(count, bool)
    for start, end in ranges:
        allowed |= (times >= start) & (times <= end)
        untouched &= ~((times >= start - padding) & (times <= end + padding))
    check_row(checks, 'outside-approved-active-coverage', int(untouched.sum()) >= 100,
              actual_active_frames=int(untouched.sum()))
    if not untouched.any():
        return dict(blocks=[], outside=None)
    result = U.fit(of[untouched].ravel(), nf[untouched].ravel())
    p95 = float(np.percentile(abs(ndb[untouched] - odb[untouched]), 95))
    check_row(checks, 'outside-approved-ranges-same-voice-timing-gain',
        abs(result['gain_db']) <= .35 and result['correlation'] >= .985 and
        result['gain_compensated_residual_snr_db'] >= 22 and p95 <= .8,
        **result, p95_absolute_frame_gain_db=p95)
    blocks = []
    for start in range(0, count, 100):
        keep = untouched[start:start + 100]
        if keep.sum() < 10:
            continue
        part = U.fit(of[start:start + 100][keep].ravel(),
                     nf[start:start + 100][keep].ravel())
        part.update(start_s=start * .01, passed=abs(part['gain_db']) <= .5 and
            part['correlation'] >= .98 and part['gain_compensated_residual_snr_db'] >= 20)
        blocks.append(part)
    check_row(checks, 'every-untouched-active-one-second-block-preserved',
              bool(blocks) and all(x['passed'] for x in blocks),
              checked_blocks=len(blocks), failed_blocks=[x for x in blocks if not x['passed']])
    quiet = ndb[(odb < -70) & allowed]
    check_row(checks, 'no-new-click-or-noise-in-modified-pauses',
              not len(quiet) or float(quiet.max()) < -55,
              maximum_actual_10ms_dbfs=float(quiet.max()) if len(quiet) else None)
    return dict(outside=result, blocks=blocks)


def original_full_track(R, Q, path, work, actual, checks):
    with directory(work):
        samples = R.pcm(str(path))
        tm = R.momentary(str(path))
        metrics = Q.指标(samples, actual['no'])
        baseline = json.loads((Path(Q.__file__).parent / '音频体检基准.json').read_text())
        notes = []
        health_bad = Q.超限(metrics, baseline, Q.确认(actual['no']), notes)
        global_lufs, _, _, loud_bad, summary = R.check(str(path), samples)
    check_row(checks, 'original-audio-health-all-items', not health_bad,
              metrics=metrics, failures=health_bad, original_confirmation_notes=notes)
    check_row(checks, 'original-whole-track-loudness', not loud_bad,
              global_lufs=global_lufs, failures=loud_bad, summary=summary)
    spans = [(s / R.SR, e / R.SR) for s, e in Q.句段(samples)]
    expected = len(actual['sentences']) + 1
    check_row(checks, 'independent-title-and-every-body-sentence-map',
              len(spans) == expected, actual_spans=spans, expected_count=expected)
    if len(spans) != expected:
        return dict(sentences=[], title=None, mapping_valid=False), tm
    body = spans[1:]
    with tempfile.TemporaryDirectory(prefix='controlled-public-timing-') as td:
        sj = Path(td) / f'work_{actual["no"]}' / '分段.json'
        sj.parent.mkdir()
        sj.write_text(json.dumps({f'S{i}': [{'时刻': [x, y]}]
            for i, (x, y) in enumerate(body, 1)}, ensure_ascii=False))
        adjacent = R.句内(str(path), samples, tm, str(sj))
        adjacent_bad = R.句内报(adjacent)
        suppressed = R.压小(str(path), samples, tm, str(sj))
    check_row(checks, 'original-within-sentence-adjacent-level-rule',
              not adjacent_bad, failures=adjacent_bad, comparisons=adjacent)
    check_row(checks, 'original-suppressed-segment-rule-every-body-sentence',
              not suppressed, failures=suppressed)
    whole = R.gated(tm[(tm[:, 0] >= body[0][0] + .4) &
                      (tm[:, 0] <= body[-1][1] + .05), 1])
    rows = []
    prior = None
    for i, ((start, end), parts) in enumerate(zip(body, R.分段(samples, body)), 1):
        raw = R.段响度(tm, start, end)
        level = R.等效(raw, start, end, R.短起(actual['no']))
        check_row(checks, f'all-body-including-S1-global-level:S{i}',
                  level is not None and whole is not None and abs(level - whole) <= R.DEV,
                  effective_lufs=level, global_lufs=whole, original_limit_lu=R.DEV)
        if prior is not None:
            check_row(checks, f'all-body-including-S1-adjacent-level:S{i-1}-S{i}',
                      level is not None and abs(level - prior) <= R.ADJ,
                      difference_lu=None if level is None else level - prior,
                      original_limit_lu=R.ADJ)
        prior = level
        groups = []
        for j, (x, y) in enumerate(parts, 1):
            value, peak = R.段量(tm, x, y)
            groups.append(dict(part=j, start=x, end=y, raw_lufs=value,
                effective_lufs=R.等效(value, x, y, R.短起(actual['no'])),
                peak_momentary_lufs=peak))
        rows.append(dict(sentence=f'S{i}', start=start, end=end,
                         effective_lufs=level, parts=groups))
    return dict(title=dict(start=spans[0][0], end=spans[0][1],
        raw_lufs=R.段响度(tm, *spans[0])), global_lufs=whole,
        sentences=rows, mapping_valid=True), tm


def audit(args):
    reference = Path(args.reference or HERE / 'audio-controlled-qc-reference.json')
    all_profiles = json.loads(reference.read_text())
    profile = all_profiles['profiles'].get(args.article)
    checks = []
    diagnostic = bool(args.diagnostic)
    report = dict(article=args.article, passed=False, repair_applied=False,
        diagnostic_only=diagnostic, production_delivery_eligible=False,
        kind='root-approved-current-source-controlled-audio-repair',
        official_gates_replaced_or_thresholds_modified=False,
        official_full_gates_are_separate_required_precondition=True,
        program_sha256=sha(__file__), reference_sha256=sha(reference), checks=checks,
        private_caches_GT_or_PCM_exported=False,
        subjective_listening_claimed=False)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    try:
        if not profile or profile.get('state') != 'approved-exact-profile':
            raise ValueError('Article profile is pending; no approved complete profile is enabled.')
        up = HERE / 'audio-qc.py'
        if sha(up) != all_profiles['numeric_utilities_sha256']:
            raise ValueError('Existing numeric utilities fingerprint differs.')
        U = module('unchanged_controlled_numeric_utilities', up)
        request = Path(args.request)
        req_path = request / f'视频/脚本/{args.article}.json'
        gen_path = request / f'视频/工具/初稿生成/gen{args.article}.py'
        work = Path(args.work).resolve()
        actual_path = Path(args.actual_source or work / f'scripts/{args.article}.json')
        raw_path = Path(args.raw_pcm or work / f'work_{args.article}/a.wav')
        requested = json.loads(req_path.read_text())
        actual = json.loads(actual_path.read_text())
        fingerprints = dict(request_source_sha256=sha(req_path), request_generator_sha256=sha(gen_path),
            actual_full_source_sha256=sha(actual_path), actual_raw_WAV_sha256=sha(raw_path),
            accepted_video_sha256=sha(args.accepted_source),
            canonical_video_sha256=sha(args.canonical_video),
            canonical_AAC_ADTS_sha256=aac_sha(args.canonical_video),
            accepted_AAC_ADTS_sha256=aac_sha(args.accepted_source))
        report.update(fingerprints=fingerprints,
            source_current_sha256=fingerprints['actual_full_source_sha256'],
            accepted_sha256=fingerprints['accepted_video_sha256'],
            canonical_sha256=fingerprints['canonical_video_sha256'])
        expected = profile['fingerprints']
        for key in ['request_source_sha256', 'request_generator_sha256',
                    'actual_raw_WAV_sha256', 'accepted_video_sha256',
                    'canonical_AAC_ADTS_sha256', 'accepted_AAC_ADTS_sha256']:
            check_row(checks, 'exact-approved-fingerprint:' + key,
                      fingerprints[key] == expected[key], actual=fingerprints[key], expected=expected[key])
        review_keys = tuple(profile['existing_review_only_top_level_keys'])
        if review_keys != ('核对确认', '区间声音指纹'):
            raise ValueError('Unexpected review-only key expansion.')
        core = lambda d: {k: v for k, v in d.items() if k not in review_keys}
        check_row(checks, 'exact-request-nonreview-document',
            canonical(core(requested)) == profile['approved_nonreview_document_sha256'])
        check_row(checks, 'actual-entire-nonreview-source-exact-approved-document',
            canonical(core(actual)) in profile['approved_actual_nonreview_document_sha256'],
            actual_nonreview_sha256=canonical(core(actual)),
            exact_approved_nonreview_sha256=profile['approved_actual_nonreview_document_sha256'],
            permitted_review_only_keys=review_keys)
        controls = {key: actual.get(key) for key in profile['approved_audio_controls']}
        check_row(checks, 'all-approved-audio-controls-exact',
                  controls == profile['approved_audio_controls'], actual=controls,
                  expected=profile['approved_audio_controls'])
        with wave.open(str(raw_path), 'rb') as wav:
            shape = dict(rate=wav.getframerate(), channels=wav.getnchannels(),
                         width=wav.getsampwidth(), samples=wav.getnframes())
        check_row(checks, 'actual-raw-WAV-shape', shape == profile['raw_WAV_shape'], actual=shape)
        info = json.loads(capture(['ffprobe', '-v', 'error', '-show_streams', '-of', 'json', args.canonical_video]))
        audio = next(x for x in info['streams'] if x['codec_type'] == 'audio')
        check_row(checks, 'actual-original-audio-format',
                  int(audio['sample_rate']) == 48000 and int(audio['channels']) == 1)
        video = [x for x in info['streams'] if x['codec_type'] == 'video']
        if not diagnostic:
            check_row(checks, 'production-actual-original-canonical-4K-present',
                      len(video) == 1 and (video[0]['width'], video[0]['height']) == (3840, 2160))
        old = U.decode(args.accepted_source)
        new = U.decode(args.canonical_video)
        check_row(checks, 'actual-no-digital-clipping-or-nonfinite',
                  np.isfinite(new).all() and float(np.max(abs(new))) < 1.,
                  sample_peak_dbfs=float(20 * np.log10(np.max(abs(new)) + 1e-30)))
        old_tm, old_global, old_log = U.r128(args.accepted_source)
        new_tm, new_global, new_log = U.r128(args.canonical_video)
        (output.parent / f'{args.article}-controlled-accepted-r128.log').write_text(old_log)
        (output.parent / f'{args.article}-controlled-actual-r128.log').write_text(new_log)
        report.update(accepted_global=old_global, actual_global=new_global)
        check_row(checks, 'actual-true-peak-below-zero', new_global['true_peak_dbtp'] < 0,
                  actual_dbtp=new_global['true_peak_dbtp'])
        check_row(checks, 'whole-track-level-preserved',
            abs(new_global['integrated_lufs'] - old_global['integrated_lufs']) <= .8,
            delta_lu=new_global['integrated_lufs'] - old_global['integrated_lufs'])
        lag, lags = U.alignment_lag(old, new, profile['alignment_reference_spans'])
        duration = (len(new) - len(old)) / SR
        check_row(checks, 'duration-preserved', abs(duration) <= .06, delta_s=duration)
        check_row(checks, 'encoding-alignment-only', abs(lag) / SR <= .02 and
                  max(lags) - min(lags) <= round(.006 * SR), lag_samples=lag, local_lags_samples=lags)
        # A waveform identity hash does not excuse a measured alignment failure.
        aligned = U.align_new(new, lag, len(old))
        report['outside_measurements'] = outside_measurements(U, old, aligned,
            profile['allowed_audio_changes'], checks)
        units = profile['units']
        fits = {}
        for name, expected_gain in profile['constant_gain_units'].items():
            start, end = units[name]
            lo, hi = round(start * SR), round(end * SR)
            fit = U.fit(old[lo:hi], aligned[lo:hi])
            om = U.measure(old, (start, end), old_tm)
            nm = U.measure(aligned, (start, end), new_tm)
            delta = U.difference(nm['crop_bs1770_lufs'], om['crop_bs1770_lufs'])
            check_row(checks, 'actual-gain-and-same-waveform:' + name,
                delta is not None and abs(fit['gain_db'] - expected_gain) <= .45 and
                fit['correlation'] >= .985 and fit['gain_compensated_residual_snr_db'] >= 20 and
                abs(delta - expected_gain) <= .55, expected_gain_db=expected_gain,
                actual_lufs_delta=delta, accepted=om, actual=nm, **fit)
            fits[name] = fit
        for name, ramp in profile['ramp_units'].items():
            start, end = units[name]
            a, b = ramp['entire_piece_span_s']
            lo, hi = round(start * SR), round(end * SR)
            t = np.arange(lo, hi) / SR
            expected_db = ramp['base_delta_db'] + ramp['ramp_start_db'] + (
                ramp['ramp_end_db'] - ramp['ramp_start_db']) * (t - a) / (b - a)
            predicted = old[lo:hi] * 10 ** (expected_db / 20)
            fit = U.fit(predicted, aligned[lo:hi])
            check_row(checks, 'actual-approved-ramp-waveform:' + name,
                abs(fit['gain_db']) <= .45 and fit['correlation'] >= .985 and
                fit['gain_compensated_residual_snr_db'] >= 20, **fit)
            count = (hi - lo) // STEP
            ov = old[lo:lo + count * STEP].reshape(count, STEP)
            nv = aligned[lo:lo + count * STEP].reshape(count, STEP)
            odb = 10 * np.log10(np.mean(ov ** 2, axis=1) + 1e-30)
            ndb = 10 * np.log10(np.mean(nv ** 2, axis=1) + 1e-30)
            times = (np.arange(count) * STEP + lo + STEP / 2) / SR
            keep = odb > -35
            exp = ramp['base_delta_db'] + ramp['ramp_start_db'] + (
                ramp['ramp_end_db'] - ramp['ramp_start_db']) * (times - a) / (b - a)
            err = abs((ndb - odb - exp)[keep])
            check_row(checks, 'actual-approved-smooth-ramp:' + name,
                len(err) > 20 and float(np.median(err)) <= .65 and float(np.percentile(err, 95)) <= 1.1,
                active_frames=len(err), median_error_db=float(np.median(err)) if len(err) else None,
                p95_error_db=float(np.percentile(err, 95)) if len(err) else None)
            fits[name] = fit
        report['actual_waveform_fits'] = fits
        tools = Path(args.tools or ROOT / '视频/工具')
        for name, digest in profile['original_tool_sha256'].items():
            if sha(tools / name) != digest:
                raise ValueError('Unmodified original tool fingerprint differs: ' + name)
        sys.path.insert(0, str(tools))
        R = module('响度一致性核对', tools / '响度一致性核对.py')
        R.FF = 'ffmpeg'  # Same numeric ffmpeg convention as the existing supplementary audit.
        Q = module('controlled_original_audio_health', tools / '音频体检.py')
        track, tm = original_full_track(R, Q, str(Path(args.canonical_video).resolve()), work, actual, checks)
        report['original_full_track_supplement'] = track
        groups_file = work / f'work_{args.article}/分段.json'
        groups = json.loads(groups_file.read_text())
        normalized = {label: [{k: row[k] for k in ('段', '增益', '停顿', '时刻')}
            for row in values] for label, values in groups.items()}
        check_row(checks, 'actual-production-all-piece-times-and-effective-gains',
                  normalized == profile['expected_producer_piece_metadata'],
                  actual_public_piece_metadata=normalized, actual_file_sha256=sha(groups_file))
        report['actual_public_piece_ranges'] = {
            f'{label}:{row["段"]}': row['时刻'] for label, values in normalized.items() for row in values}
        # The original suppression rule is also evaluated with both independently
        # measured and producer boundaries, using the original 20/40ms review grid.
        if track['mapping_valid']:
            measured = next(x for x in track['sentences'] if x['sentence'] == 'S9')['parts']
            variants = {'independent': [(x['start'], x['end']) for x in measured],
                        'producer': [tuple(x['时刻']) for x in normalized['S9']]}
            sensitive = []
            for label, spans in variants.items():
                failures = []
                for ds in (-.04, -.02, 0, .02, .04):
                    for de in (-.04, -.02, 0, .02, .04):
                        x, y = spans[2][0] + ds, spans[2][1] + de
                        v, pk = R.段量(tm, x, y)
                        v = R.等效(v, x, y, True)
                        for ni in (1, 3):
                            a, b = spans[ni]
                            nv, npk = R.段量(tm, a, b)
                            nv = R.等效(nv, a, b, True)
                            if nv - v > R.IN_DIP_G and npk - pk > R.IN_DIP_PK:
                                failures.append(dict(start=x, end=y, neighbor=ni + 1,
                                    effective_difference_lu=nv - v, peak_difference_lu=npk - pk))
                                break
                check_row(checks, 'S9-repair-original-rule-20-40ms-boundaries:' + label,
                          not failures, checked_variants=25, failures=failures)
                sensitive.append(dict(basis=label, checked=25, failures=failures))
            report['original_boundary_sensitivity'] = sensitive
        import parselmouth
        pitch = {}
        pitch_spans = [("title", (track['title']['start'], track['title']['end']))] if track['title'] else []
        pitch_spans += [(row['sentence'], (row['start'], row['end'])) for row in track['sentences']]
        for name, (start, end) in pitch_spans:
            lo, hi = round(start * SR), round(end * SR)
            tracks = [parselmouth.Sound(v[lo:hi], sampling_frequency=SR).to_pitch_ac(
                time_step=.01, pitch_floor=60, pitch_ceiling=400).selected_array['frequency']
                for v in (old, aligned)]
            size = min(map(len, tracks))
            a, b = (x[:size] for x in tracks)
            keep = (a > 0) & (b > 0)
            cents = abs(1200 * np.log2(b[keep] / a[keep]))
            result = dict(voiced_pairs=len(cents), median_absolute_cents=float(np.median(cents)) if len(cents) else None,
                p90_absolute_cents=float(np.percentile(cents, 90)) if len(cents) else None)
            check_row(checks, 'actual-pitch-preserved:' + name, len(cents) > 10 and
                result['median_absolute_cents'] <= 40 and result['p90_absolute_cents'] <= 150, **result)
            pitch[name] = result
        report['pitch_comparison'] = pitch
        report['passed'] = bool(checks) and all(x['passed'] for x in checks)
        report['repair_applied'] = report['passed']
        report['production_delivery_eligible'] = report['passed'] and not diagnostic
    except BaseException as exc:
        report['error'] = dict(type=type(exc).__name__, detail=str(exc))
        report['passed'] = False
        report['production_delivery_eligible'] = False
    report['failed_checks'] = [x['name'] for x in checks if not x['passed']]
    output.write_text(json.dumps(json_safe(report), ensure_ascii=False, indent=2, allow_nan=False) + '\n')
    return report


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--article', choices=['67', '68', '70'], required=True)
    p.add_argument('--accepted-source', required=True)
    p.add_argument('--canonical-video', required=True)
    p.add_argument('--work', required=True)
    p.add_argument('--request', required=True)
    p.add_argument('--output', required=True)
    p.add_argument('--actual-source')
    p.add_argument('--raw-pcm')
    p.add_argument('--tools')
    p.add_argument('--reference')
    p.add_argument('--diagnostic', action='store_true')
    result = audit(p.parse_args())
    print(json.dumps(dict(article=result['article'], passed=result['passed'],
        diagnostic_only=result['diagnostic_only'], production_delivery_eligible=result['production_delivery_eligible'],
        failed_checks=result['failed_checks'], error=result.get('error')), ensure_ascii=False))
    raise SystemExit(0 if result['passed'] else 1)
