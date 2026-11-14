"""Read-only exact native61 reconstruction, hash binding, original G45 scalars.

No TTS inference, source/confirmation change, workflow, private PCM/cache export,
or quality acceptance. Temporary private WAV/AAC are removed in all cases.
"""
import ast
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import textwrap
import traceback

sys.dont_write_bytecode = True
import numpy as np
import soundfile as sf

HERE = Path(__file__).resolve().parent
B = HERE.parent
ORIGINAL = B / 'readonly-failed54-61-66-69-43543967031/61/public-original-metadata'
REPLAYER = B / 'audio65-69-source-readonly/replay_original_sources.py'
PROBE = B / 'diagnosis61-public-20261114/probe61_native_onset.py'
TOOLS = Path('/workspace/work/audit-repo/视频/工具')


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def dump(name, value):
    (HERE / name).write_text(json.dumps(value, ensure_ascii=False, indent=2,
                                      default=lambda v: float(v)) + '\n')


def native_levels(a, sr):
    rows = []
    F = round(.01 * sr)
    for tick in range(10600, 11200, 10):
        t = tick / 1000
        i = round(t * sr)
        w = a[max(0, i - 2 * sr):i + 2 * sr]
        n = len(w) // F
        ref = np.sqrt(np.mean(w[:n * F].reshape(n, F) ** 2, axis=1)).max() + 1e-12
        seg = a[i:i + F]
        power = abs(np.fft.rfft(seg * np.hanning(F))) ** 2
        freq = np.fft.rfftfreq(F, 1 / sr)
        rows.append({'actual_native_WAV_start_s': t, 'end_s': round(t + .01, 3),
                     'RMS_relative_to_local4s_peak10ms_dB': float(20 * np.log10(np.sqrt(np.mean(seg ** 2)) / ref + 1e-12)),
                     'Hann_power_spectral_centroid_Hz': float(np.sum(power * freq) / (np.sum(power) + 1e-30))})
    return rows


def full_precision_routes(replay, d, cache, A, sr, parts):
    """Execute original timing fragment/functions with exact native A and G72 inputs.

    No original list.txt survived artifact collection. Its S1 boundary is replayed
    through the exact producer fragment and labelled reconstructed, never acquired.
    """
    ns, sent = replay.scope(d, 1, cache)
    maker = replay.m.source
    checker_path = TOOLS / '高亮同步核对.py'
    checker = checker_path.read_text()
    nosound = [n for n in ast.parse(maker).body if isinstance(n, ast.Assign)
               and any(isinstance(t, ast.Name) and t.id == '_NOSOUND' for t in n.targets)]
    assert len(nosound) == 1
    exec(compile(ast.Module(body=nosound, type_ignores=[]), str(TOOLS / 'make_video.py'), 'exec'), ns)
    ch = d['sentences'][0]['chunks']
    texts = [re.sub(r'\*\*', '', ns['R'].strip_gloss(c['en'])).strip() for c in ch]
    assert sent == ' '.join(texts) and len(ch) == 2
    bounds, pos = [], 0
    for t in texts:
        bounds.append(pos)
        pos += len(t) + 1
    clips, tmap = [], []
    pieces, gaps, p0 = [], [], 0
    listed = ns['list_commas'](sent)
    for mt in re.finditer(r'[,;:](?=\s)', sent):
        pieces.append((p0, mt.end()))
        p0 = mt.end() + 1
        gaps.append(.2 if mt.start() in listed else .4)
    pieces.append((p0, len(sent)))
    clips, tmap = ns['sentence_audio'](sent, pieces, gaps)
    clips, a, _, _ = ns['句增益'](d, d['no'], 0, sent, pieces, gaps, clips, tmap, np.concatenate(clips))
    a0, a1 = parts[1]['start_s'], parts[1]['end_s']
    assert parts[1]['sentence'] == 'S1'
    lead = .4
    prefix_samples = round((a0 - lead) * sr)
    fragment = textwrap.dedent(maker[maker.index('        ct=chunk_times(texts);'):maker.index('        for r_ in seg_rec[')])
    ns.update({'d': d, 'no': d['no'], 'ch': ch, 'texts': texts, 'sent': sent, 'bounds': bounds,
               'tmap': tmap, 'clips': clips, 'a': a, 'si': 0, 'lead': lead,
               'audio': [A[:prefix_samples]], 'len': len})
    exec(compile(fragment, str(TOOLS / 'make_video.py') + '#unchanged-highlight-fragment', 'exec'), ns)
    sw = float(ns['t_at'] + ns['starts'][1])
    assert ns['t_at'] == a0
    funcs = [n for n in ast.parse(checker).body if isinstance(n, ast.FunctionDef)
             and n.name in {'logmel', 'dtw_map', 'onset_frame'}]
    assert len(funcs) == 3
    exec(compile(ast.Module(body=funcs, type_ignores=[]), str(checker_path), 'exec'), ns)
    ns.update({'sr': sr, 'a0': a0, 'a1': a1, 'seg': A[int(a0 * sr):int(a1 * sr)]})
    ns['ls'] = ns['logmel'](ns['seg'])
    # The exact original alignment body, stopping before confirmation handling.
    alignment = textwrap.dedent(checker[checker.index('        # 甲\n'):checker.index("            key = f'S")])
    ns.update({'starts': [a0 - lead, sw], 'kc': 0})
    exec(compile(alignment, str(checker_path) + '#unchanged-two-route-body', 'exec'), ns)
    sample_clock_refs = {k: float(v) for k, v in ns['ref'].items()}
    # Original list.txt serializes EVERY animated-title frame duration to .3f.
    # Replay its real title wrap/timeline without rendering or exporting images.
    import render as R
    import title2 as T
    import title_anim as TA
    font_path = B / 'preflight-frozen66-v2-part1/mirror/视频/工具/fonts/Inter.ttf'
    font_raw = replay.m.git('视频/工具/fonts/Inter.ttf')
    assert font_path.read_bytes() == font_raw
    R.F = str(font_path.parent) + '/'
    fx = d.get('title_fx', {})
    hl, ghost, en = fx.get('hl', []), fx.get('ghost', []), d['title_en']
    title_source = (TOOLS / 'title_anim.py').read_text()
    wrap_fragment = textwrap.dedent(title_source[title_source.index('    words = '):title_source.index('    zf = ')])
    title_env = {'R': R, 'T': T, 'S': R.S, 'en': en, 'hl': hl, 'ghost': ghost}
    exec(compile(wrap_fragment, str(TOOLS / 'title_anim.py') + '#original-title-wrap-only', 'exec'), title_env)
    line_count = len(title_env['lines'])
    _, animation_end = TA.timeline(line_count)
    animation_n = int(math.ceil(animation_end * TA.FPS))
    title_duration = a0 - lead
    animated_durations = [1 / TA.FPS] * animation_n
    title_durations = animated_durations + [title_duration - sum(animated_durations)]
    serialized_title_durations = [float(f'{v:.3f}') for v in title_durations]
    first_screen_list_start = sum(serialized_title_durations)
    # Alignment already replaced ns['starts'] with absolute screen starts.
    # The producer duration uses the original sentence-relative boundary.
    relative_producer_boundary = sw - a0
    first_screen_duration = float(f"{relative_producer_boundary + lead:.3f}")
    second_screen_duration = float(f"{len(a) / sr - relative_producer_boundary + .7:.3f}")
    list_sw = first_screen_list_start + first_screen_duration
    list_a0 = first_screen_list_start + lead
    list_a1 = list_sw + second_screen_duration - .7
    ns.update({'a0': list_a0, 'a1': list_a1, 'seg': A[int(list_a0 * sr):int(list_a1 * sr)],
               'starts': [first_screen_list_start, list_sw], 'kc': 0})
    ns['ls'] = ns['logmel'](ns['seg'])
    exec(compile(alignment, str(checker_path) + '#unchanged-body-serialized-list-clock', 'exec'), ns)
    refs = {k: float(v) for k, v in ns['ref'].items()}
    g45 = module('cf_original_G45_probe61', PROBE).official_functions(checker_path)
    cf_t = 10.85
    cf_pass = bool(g45['确认可收']('61', A, sr, cf_t))
    cf_deviation = abs(list_sw - cf_t)
    return {'actual_original_list_txt_acquired': False,
            'reconstructed_original_list_boundary_s': list_sw,
            'producer_exact_sample_clock_boundary_s': sw,
            'initial_raw_sample_clock_alignment_diagnostic_only': sample_clock_refs,
            'reconstruction_method': 'unchanged maker highlight fragment, exact original font/title wrap/timeline, original per-entry .3f list serialization, and unchanged checker two-route functions; list.txt itself was not collected',
            'original_title_English_line_count': line_count,
            'original_title_animation_intervals': animation_n,
            'original_title_animation_FPS': TA.FPS,
            'each_original_animation_interval_s': 1 / TA.FPS,
            'each_serialized_animation_interval_s': float(f'{1 / TA.FPS:.3f}'),
            'sample_clock_title_duration_s': title_duration,
            'serialized_list_title_duration_s': first_screen_list_start,
            'title_font_sha256': sha(font_raw),
            'title_wrap_fragment_sha256': sha(wrap_fragment.encode()),
            'checker_sentence_list_a0_s': list_a0,
            'checker_sentence_list_a1_s': list_a1,
            'sentence_raw_start_s': a0, 'sentence_raw_end_s': a1,
            'two_route_actual_full_precision_seconds': refs,
            'current_actual_deviation_seconds': {k: list_sw-v for k, v in refs.items()},
            'reconstructed_two_route_boolean_NOT_original_job_verdict': all(abs(list_sw-v) <= .15 for v in refs.values()),
            'original_actual_job_highlight_verdict_remains_failure': True,
            'near_limit_replay_scope': 'Replayed decimal values match the printed original values, but the original list.txt was not collected. A difference around machine precision at0.15 must not be claimed as reproduction of the actual failed boolean. Native G45 and the exact WAV/AAC binding are independent of this reconstruction.',
            'visual_only_candidate_seconds': 10.9,
            'candidate_deviation_seconds': {k: 10.9-v for k, v in refs.items()},
            'candidate_would_meet_unchanged_original_two_route_limit': all(abs(10.9-v) <= .15 for v in refs.values()),
            'original_auto_mean_rule_applicable': abs(refs['甲'] - refs['乙']) <= .05,
            'root_review_confirmation_candidate_only': {
                'key': 'S1 第2块', '开始读': cf_t, '配音指纹': '7499cce91ea3',
                'actual_original_G45_accepts': cf_pass,
                'actual_full_native_WAV_fingerprint_matches': True,
                'deviation_from_reconstructed_serialized_list_highlight_s': cf_deviation,
                'original_confirmation_condition_would_accept_in_memory': cf_pass and cf_deviation <= .15,
                'start_is_from_exact_native_scalar_probe_not_public_clock_or_human_listening': True,
                'not_written_or_claimed_as_full_article_QC': True},
            'maker_fragment_sha256': sha(fragment.encode()),
            'alignment_fragment_sha256': sha(alignment.encode()),
            'no_confirmation_or_source_write': True}


def main():
    proof = json.loads((ORIGINAL / '61-failed-draft-proof.json').read_text())
    status = json.loads((ORIGINAL / '61-status.json').read_text())
    source_path = ORIGINAL / '61-failed-working-source.json'
    d = json.loads(source_path.read_text())
    assert sha(source_path.read_bytes()) == proof['source_sha256']
    assert proof['aac_adts_sha256'] == status['accepted_source']['aac_adts_sha256']
    report = {'article': '61', 'purpose': 'exact old native WAV reconstruction and scalar onset diagnostic only',
              'quality_acceptance': False, 'source_audio_checker_or_confirmation_modified': False,
              'workflow_launched': False, 'subjective_listening_claimed': False,
              'failed_source_sha256': sha(source_path.read_bytes()),
              'expected_actual_failed_internal_PCM_sha256': proof['internal_pcm_sha256'],
              'expected_actual_failed_AAC_sha256': proof['aac_adts_sha256'],
              'native_replay_module_sha256': sha(REPLAYER.read_bytes()),
              'public_frozen_probe_sha256': sha(PROBE.read_bytes()),
              'original_proof_sha256': sha((ORIGINAL / '61-failed-draft-proof.json').read_bytes()),
              'temporary_private_PCM_and_AAC_removed': False}
    temp_path = None
    try:
        replay, probe = module('native_original_replay61', REPLAYER), module('native_probe61', PROBE)
        report.update({'maker_sha256': sha(replay.m.source.encode()), 'clean_sha256': sha(replay.m.clean.encode()),
                       'AF_sha256': sha(replay.AF.encode()), 'G72_repository_pin': replay.m.PIN,
                       'checker_sha256': sha((TOOLS / '高亮同步核对.py').read_bytes())})
        with tempfile.TemporaryDirectory(prefix='private-61-exact-native-onset-', dir='/dev/shm') as tmp:
            temp_path = Path(tmp)
            cache = temp_path / 'cache'
            cache.mkdir()
            x, parts = replay.build(d, cache)
            wav = temp_path / 'a.wav'
            sf.write(wav, x, 24000)
            wav_raw = wav.read_bytes()
            report.update({'actual_reconstructed_WAV_sha256': sha(wav_raw),
                           'actual_reconstructed_WAV_md5_first12': hashlib.md5(wav_raw).hexdigest()[:12],
                           'actual_native_sample_count_24k': len(x),
                           'complete_reconstructed_WAV_matches_original_native_proof': sha(wav_raw) == proof['internal_pcm_sha256']})
            assert report['complete_reconstructed_WAV_matches_original_native_proof'], 'Full reconstructed native WAV SHA differs: do not run onset probe'
            assert report['actual_reconstructed_WAV_md5_first12'] == '7499cce91ea3'
            # Bind public processing as well before measuring the exact private clock.
            aac = temp_path / 'processed.m4a'
            subprocess.run([replay.FF, '-y', '-loglevel', 'error', '-i', str(wav), '-af', replay.AF,
                            '-c:a', 'aac', '-b:a', '256k', '-movflags', '+faststart', str(aac)], check=True)
            adts = subprocess.check_output(['ffmpeg', '-v', 'error', '-nostdin', '-i', str(aac),
                                            '-map', '0:a:0', '-c:a', 'copy', '-f', 'adts', '-'])
            report['actual_reconstructed_public_ADTS_sha256'] = sha(adts)
            report['complete_reconstructed_ADTS_matches_original_failed_and_accepted'] = sha(adts) == proof['aac_adts_sha256']
            assert report['complete_reconstructed_ADTS_matches_original_failed_and_accepted'], 'Public full AAC hash not bound: stop before diagnostic'
            A, sr = sf.read(wav)
            report['actual_native_sample_rate'] = sr
            report['G45_scalars'] = probe.measure(np.asarray(A, float), sr, TOOLS / '高亮同步核对.py')
            report['native_10ms_level_and_centroid'] = native_levels(A, sr)
            accepted = [r['time_s'] for r in report['G45_scalars'] if r['unchanged_original_G45_accepts']]
            report['actual_native_G45_accepted_grid_times_s'] = accepted
            groups = []
            for value in accepted:
                if not groups or value - groups[-1][-1] > .006:
                    groups.append([value])
                else:
                    groups[-1].append(value)
            report['actual_native_G45_accepted_grid_ranges_s'] = [[g[0], g[-1]] for g in groups]
            report['target_S1C2_native_G45_accepted_grid_range_s'] = [v for v in report['actual_native_G45_accepted_grid_ranges_s'] if v[0] < 11]
            report['later_11_185_onset_is_NOT_target_chunk_opening'] = True
            report['native_probe_clock'] = 'Actual reconstructed native a.wav, complete file SHA and full processed AAC matched before G45; not public AAC-clock substitution'
            try:
                report['full_precision_original_route_replay'] = full_precision_routes(replay, d, cache, A, sr, parts)
            except BaseException as exc:
                report['full_precision_route_replay_error'] = {'type': type(exc).__name__, 'detail': str(exc), 'traceback': traceback.format_exc()}
            report['G72_mother_scalar_provenance'] = list(replay.m.cache_rows.values())
            report['exact_stored_level_JSON_scalar_provenance'] = list(replay.level_rows.values())
    except BaseException as exc:
        report['error'] = {'type': type(exc).__name__, 'detail': str(exc), 'traceback': traceback.format_exc()}
    finally:
        report['temporary_private_PCM_and_AAC_removed'] = temp_path is not None and not temp_path.exists()
        dump('61-exact-native-onset-and-route-report.json', report)
    print(json.dumps({'report': str(HERE / '61-exact-native-onset-and-route-report.json'),
                      'actual_complete_native_SHA_match': report.get('complete_reconstructed_WAV_matches_original_native_proof'),
                      'actual_complete_AAC_match': report.get('complete_reconstructed_ADTS_matches_original_failed_and_accepted'),
                      'native_G45_ranges': report.get('actual_native_G45_accepted_grid_ranges_s'),
                      'route_replay': report.get('full_precision_original_route_replay'),
                      'error': report.get('error'), 'route_error': report.get('full_precision_route_replay_error'),
                      'private_temp_removed': report['temporary_private_PCM_and_AAC_removed'],
                      'quality_acceptance': False}, ensure_ascii=False))


if __name__ == '__main__':
    main()
