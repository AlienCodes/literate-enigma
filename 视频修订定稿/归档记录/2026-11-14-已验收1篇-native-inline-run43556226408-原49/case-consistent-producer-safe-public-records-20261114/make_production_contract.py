#!/usr/bin/env python3
"""Freeze an installation contract only after a real native certificate."""
import copy
import hashlib
import json
from pathlib import Path
import shutil

O = Path(__file__).resolve().parent
sha = lambda path: hashlib.sha256(Path(path).read_bytes()).hexdigest()
r = json.loads((O / 'validated-final-report.json').read_text())
assert r['actual_full_quickcheck_exit'] == 0 and r['program_count'] == 6
assert r['all_production_program_count_verified'] == 110 and r['runtime_file_count'] == 8
assert r['production_install_or_source_JSON_GEN_MD_write'] is False
D = O / 'production-contract'
N = O / 'native-results' / str(r['run_id']) / 'case-consistent-producer'
old = O.parent / 'keep-reviewed-cuts/production-contract/manifest.json'
q = copy.deepcopy(json.loads(old.read_text()))
for row in r['runtime_install_files']:
    dst = D / 'files' / row['path']
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(O / 'validated-install' / row['path'], dst)
    assert sha(dst) == row['after_SHA256']
for item in q['core_files']:
    item['patched_sha256'] = sha(D / item['file'])
q['core_files'].append({
    'target': '视频/工具/make_video.py', 'file': 'files/视频/工具/make_video.py',
    'original_sha256': '4c85e1fbdd2e82c5646d5f58df63c85eca60af4ef521f1d36f765575a568d6f3',
    'patched_sha256': sha(D / 'files/视频/工具/make_video.py'),
    'repair_scope': 'Only _pron outer dictionary activation uses existing _wf(w_) case policy. Ordinary next restores its original text input; literal NeXT and correct Origin/Haber/BASF inputs unchanged. No dictionary/model/voice/audio-transform/threshold edits.'})
assert len(q['core_files']) == 6
q['kind'] = 'actual-original-fastcheck-certified-six-core-case-consistent-producer-repair'
q['actual_native_fastcheck_stamp']['sha256'] = r['actual_original_full_stamp_SHA256']
q['actual_native_fastcheck_stamp']['origin'] = 'actual unmodified original full quickcheck, native run' + str(r['run_id'])
q['actual_native_certification'] = {
    'run_id': r['run_id'], 'job_id': r['job_id'], 'commit': r['source_commit'],
    'actual_full_quickcheck_exit': 0, 'actual_full_quickcheck_seconds': r['actual_full_quickcheck_seconds'],
    'artifact_id': r['artifact']['artifact_id'], 'artifact_zip_sha256': r['artifact']['ZIP_SHA256'],
    'full_original_quickcheck_log_sha256': r['original_full_log_SHA256'],
    'article_audio_or_video_passed_not_implied': True}
q['whole_production_T_compatibility']['proof_SHA256'] = sha(O / 'actual-production-full-T-stamp-proof.json')
q['actual_native_pronunciation_tests']['report_SHA256'] = sha(N / 'real-pronunciation-selftest-tests.json')
q['actual_native_complete02_cuts_tests']['full_report_SHA256'] = sha(N / 'real-cuts-mode-tests.json')
q['actual_native_dispatch_tests'] = {
    'four_actual_native_tokenizer_callback_traces_passed': True,
    'all_other_AST_exact': True, 'only_re_I_to_existing_wf_activation': True,
    'ordinary_next_original_text_input_restored': True,
    'proper_NeXT_correct_Origin_Haber_BASF_inputs_exact': True,
    'prior_bug_actual_negative_control_rejected': True,
    'report_SHA256': sha(N / 'real-dispatch-mode-tests.json')}
cache = json.loads((N / '16-native-current-reference-cache.json').read_text())
assert cache['normal_internal_Actions_cache_saved'] is True
q['native16_correct_Origin_reference_cache'] = {
    'normal_internal_Actions_cache_key': cache['normal_internal_Actions_cache_key'],
    'report_SHA256': sha(N / '16-native-current-reference-cache.json'),
    'cache_paths': ['completion-machine/tts/cache_tts/' + row['exact_native_cache_key'] + suffix
                    for row in cache['actual_calls'] for suffix in ('', '.单线程')],
    'actual_calls': cache['actual_calls'],
    'reference_preparation_only_not_audio_acceptance': True,
    'all_existing_cache_PCM_source_and_accepted_public_AAC_unchanged': True,
    'private_raw_GT_pkl_or_models_exported_to_artifacts': False}
restore_rows = []
for row in cache['actual_calls']:
    key = row['exact_native_cache_key']
    value = row['actual_marker_value']
    assert value == row['actual_pkl_SHA256'][:16] and len(value) == 16
    restore_rows.append({'path_below_runner_temp': 'completion-machine/tts/cache_tts/' + key,
                         'expected_file_SHA256': row['actual_pkl_SHA256'],
                         'SHA256_basis': 'Actual native file full SHA recorded by this successful job.'})
    assert row['cache_preexisted'] is False, 'Preexisting marker file would require its own direct full-hash observation.'
    restore_rows.append({'path_below_runner_temp': 'completion-machine/tts/cache_tts/' + key + '.单线程',
                         'expected_file_SHA256': hashlib.sha256(value.encode()).hexdigest(),
                         'expected_literal_text_no_newline': value,
                         'SHA256_basis': 'Derived from observed native marker value and the unchanged original _cached new-entry writer, which writes exactly16 ASCII characters without newline. Future restore must measure the whole file; not presented as a direct native marker-file SHA observation.'})
q['native16_correct_Origin_reference_cache']['exact_four_file_restore_verification'] = restore_rows
q['native16_correct_Origin_reference_cache']['restore_instruction'] = (
    'After the original full-machine restore and before any reference preparation, '
    'actions/cache/restore@v4 must use this exact key and these same four runner.temp paths '
    'in this order on codex/finish-05-and-summaries-20261112. Require cache-hit true; '
    'read every restored file and compare its full SHA, exact marker bytes, original model/voice/input/key '
    'and G72 validation. Do not infer missing producer mothers or copy unrelated cache files.')
# The producer's intended dispatch behavior changes. The five previously
# certified control modes retain their own original default behavior.
q.pop('default_behavior_unchanged', None)
q['prior_five_control_modes_default_behavior_unchanged'] = True
q['maker_default_dispatch_changed_only_for_nonmatching_dictionary_case'] = True
q.pop('producer_unchanged_SHA256', None)
q['producer_before_SHA256'] = r['producer_before_SHA256']
q['producer_after_SHA256'] = r['producer_after_SHA256']
q['producer_dispatch_change_actual_original_full_certified'] = True
q['program_count'], q['runtime_file_count'] = 6, 8
q['historical_test_article_data_not_to_install'] = True
(D / 'manifest.json').write_text(json.dumps(q, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'contract': str(D / 'manifest.json'), 'SHA256': sha(D / 'manifest.json'),
                  'program_count': 6, 'runtime_file_count': 8, 'production_written': False}))
