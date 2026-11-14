#!/usr/bin/env python3
"""Run only after a real successful native full certificate has been retrieved."""
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

O = Path(__file__).resolve().parent
launch = json.loads((O / 'native-launch-state.json').read_text())
R = launch['run_id']
N = O / 'native-results' / str(R) / 'case-consistent-producer'
PKG = O / 'native-ready/.github/producer-dispatch-certification'
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
C = json.loads((N / 'certification.json').read_text())
receipt = json.loads((N / 'artifact-receipt.json').read_text())
assert C['passed'] is True and C['stage'] == 'independent-core-certification-passed'
assert receipt['run_id'] == R and receipt['source_commit'] == launch['commit']
assert receipt['full_ZIP_digest_verified_before_extraction'] is True
checks = {x['name']: x for x in C['checks']}
for key in ['new-dispatch-real-native-tests', 'prepare-native16-private-reference-cache', 'new-cuts-mode-real-tests', 'new-pronunciation-selftest-real-tests', 'new-ending-mode-real-tests', 'original-full-fastcheck', 'real-stamp-validation', 'new-mode-functional-tests']:
    assert checks[key]['exit'] == 0
stamp = N / 'real-fastcheck-stamp.json'
assert sha(stamp) == C['real_fastcheck_stamp_SHA256']
S = json.loads(stamp.read_text())
manifest = json.loads((PKG / 'overlay-manifest.json').read_text())
assert len(manifest['files']) == 6
ending = json.loads((N / 'real-ending-mode-tests.json').read_text())
assert ending['status'] == 'passed_real_complete_original_namespace_ending_mode_tests'
assert ending['good_original_source']['JSON_all_bytes_and_all_metadata_preserved'] is True
assert all(x['original_bad_point_gate_rejected'] and x['no_automatic_fallback_or_write'] for x in ending['bad_front_and_tail'])
assert ending['default_mode']['original_vs_candidate_auto_full_JSON_deep_exact'] is True
assert ending['actual_shell_pipeline_bad_point_exit_propagated'] is True
assert ending['no_existing_points_uses_exact_original_auto_algorithm'] is True
pron = json.loads((N / 'real-pronunciation-selftest-tests.json').read_text())
assert pron['status'] == 'passed_real_original_namespace_pronunciation_selftest_repair'
assert pron['candidate_original_full_selftest_true'] and pron['all_non_selftest_AST_nodes_exact']
assert pron['original_normal_checker_full_output_exact_before_after'] and pron['normal_original_BAD_count'] == 0
assert len(pron['actual_nine_real_uncorrected_bad_words']) == 9
assert all(x['unchanged_real_checker_reported_BAD'] for x in pron['actual_nine_real_uncorrected_bad_words'])
assert pron['all_dictionary_keys_values_restored'] and pron['unrelated_exception_propagates_and_entry_restored']
full = (N / 'original-full-fastcheck.log').read_text()
assert '快测通过' in full and 'a.wav、分段.json 逐字节、每屏像素一致' in full
assert '交付核查 出片前/出片后 + 出片守门自检：全过' in full
for x in C['real_cached_source_measurements']:
    assert x['source_JSON_and_approved_gain_byte_exact_after_measurement'] and x['actual_audio_file_byte_exact_after_measurement']
cuts = json.loads((N / 'real-cuts-mode-tests.json').read_text())
assert cuts['status'] == 'passed_real_complete02_keep_reviewed_cuts_mode'
for k in ['full_actual_shell_no_routing_stubs', 'default_original5_vs_candidate_physical_NV_PCM_AAC_exact',
          'default_original5_vs_candidate_complete_JSON_deep_exact', 'explicit_mode_all_original_NV_preserved',
          'explicit_mode_actual_PCM_and_AAC_match_accepted_original', 'real_automatic_S14_proposal_still_printed_and_saved',
          'original_new_noise_selftests_passed_on_actual02', 'existing_bad_typed_NV_still_rejected_by_original_producer']:
    assert cuts[k] is True, k
for row in cuts['real_calls']:
    assert sha(N / (row['name'] + '.log')) == row['log_SHA256']
assert cuts['all_three_actual_shell_cases'][2]['actual_AAC_ADTS_SHA256'] == 'c026dfff1f9591a3e11539cc40e87e3da0ed247cec3bf883d265011126e094d3'
for row in C['checks']:
    assert sha(N / (row['name'] + '.log')) == row['log_SHA256']
dispatch = json.loads((N / 'real-dispatch-mode-tests.json').read_text())
assert dispatch['status'] == 'passed_actual_native_case_consistent_producer_dispatch'
assert dispatch['all_other_AST_exact'] and dispatch['only_AST_keyword_change_re_I_to_existing_wf']
assert dispatch['ordinary_next_restored_to_original_text_input'] and dispatch['proper_NeXT_and_correct_Origin_Haber_and_BASF_inputs_exact']
cache16 = json.loads((N / '16-native-current-reference-cache.json').read_text())
assert cache16['status'] == 'prepared_exact_native16_origin_mothers_for_internal_cache'
assert cache16['normal_internal_Actions_cache_saved'] is True
assert cache16['normal_internal_Actions_cache_key'] == 'Linux-native16-origin-dce6d1-989b1c-' + str(R)
for k in ['all_preexisting_private_cache_bytes_unchanged', 'public_repository_cache_unchanged', 'preexisting_PCM_and_source_unchanged']:
    assert cache16[k] is True
assert len(cache16['actual_calls']) == 2
assert all(x['native_writer_and_marker_check_passed'] for x in cache16['actual_calls'])
D = O / 'validated-install'
files = []
prior_four_manifest = O.parent / 'keep-reviewed-cuts/validated-install/manifest.json'
prior_four = json.loads(prior_four_manifest.read_text())
prior_four_programs = {x['path']: x['after_SHA256'] for x in prior_four['runtime_install_files'] if x['kind'] == 'program'}
for f in manifest['files']:
    src = PKG / 'patch' / f['path']
    assert sha(src) == f['patch_SHA256'] == C['actual_core_SHA256'][f['path']]
    assert S['程序'][f['path'][len('视频/工具/'):]] == f['patch_SHA256'][:16]
    dst = D / f['path']
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dst)
    files.append({'path': f['path'], 'original_main_SHA256': f['main_SHA256'],
                  'previous_certified_SHA256': prior_four_programs.get(f['path'], f['main_SHA256']),
                  'after_SHA256': sha(dst), 'kind': 'program', 'source': str(src)})
gold = PKG / 'approved-regression/回归基准_27.json'
assert sha(gold) == 'b8ddb4656ae27cbfc7ec8e3b99511983b4e568997bd4ad4ee33c364f3926ae94'
assert sha(N / 'approved-visual-baseline.json') == sha(gold)
for src, rel, kind in [(gold, '视频/工具/新管/回归基准_27.json', 'pre-existing approved visual baseline; original audio baseline unchanged'),
                       (stamp, '视频/工具/新管/快测通过.json', 'actual original-full-generated stamp, never edited')]:
    dst = D / rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dst)
    files.append({'path': rel, 'after_SHA256': sha(dst), 'kind': kind, 'source': str(src)})
assert len(files) == 8
# Check the complete real production T, not audit-repo and not just the four overlay paths.
production = Path('/workspace/work/video-audit70-20261113/core3-final-install-mirror/视频/工具')
base_proof = json.loads((production.parent.parent / 'actual-production-source-stamp-install-proof.json').read_text())
assert base_proof['production_source_ref'] == 'e5446f35ffc522e96cf8cabdf36d1a182551a6a9'
spec = importlib.util.spec_from_file_location('real_original_production_stamp', production / '新管/印章.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
mod.T = str(production)
mod.H = str(production / '新管')
mod.章 = str(production / '新管/快测通过.json')
assert mod.查() == []
base_map = mod.程序哈希()
mirror = O / 'production-full-T-install-mirror/视频/工具'
assert not mirror.exists(), 'Fresh isolated production-program mirror required'
for rel in base_map:
    src, dst = production / rel, mirror / rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dst)
for item in files:
    dst = mirror.parent.parent / item['path']
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(D / item['path'], dst)
spec = importlib.util.spec_from_file_location('new_full_T_original_stamp', mirror / '新管/印章.py')
installed = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installed)
installed.T, installed.H = str(mirror), str(mirror / '新管')
installed.章 = str(mirror / '新管/快测通过.json')
after_map = installed.程序哈希()
assert after_map == S['程序'], 'Full production T differs from the actual native full stamp'
env = {**os.environ, 'XG_TOOLS': str(mirror), 'XG_NOPUSH': '1'}
r = subprocess.run([sys.executable, str(mirror / '新管/印章.py')], env=env, cwd=O, text=True, capture_output=True)
(O / 'actual-production-full-T-stamp.log').write_text(r.stdout + r.stderr)
assert r.returncode == 0, r.stdout + r.stderr
proof = {'status': 'passed_actual_production_complete_T_stamp_compatibility',
         'actual_production_base': base_proof, 'production_program_count': len(base_map),
         'all_production_program_paths_before': base_map, 'all_installed_program_paths_after': after_map,
         'actual_native_stamp_all_program_map_deep_exact': True, 'original_stamp_exit': r.returncode,
         'original_stamp_stdout': r.stdout, 'actual_generated_stamp_sha256': sha(stamp),
         'production_T_or_source_written': False, 'isolated_mirror_only': str(mirror)}
(O / 'actual-production-full-T-stamp-proof.json').write_text(json.dumps(proof, ensure_ascii=False, indent=2) + '\n')
report = {'status': 'validated_six_program_runtime_install_ready_not_installed',
          'run_id': R, 'job_id': receipt['job_id'], 'source_commit': receipt['source_commit'],
          'actual_full_quickcheck_exit': 0, 'actual_full_quickcheck_seconds': checks['original-full-fastcheck']['seconds'],
          'original_full_log_SHA256': sha(N / 'original-full-fastcheck.log'), 'artifact': receipt,
          'program_count': 6, 'runtime_file_count': 8, 'runtime_install_files': files,
          'prior_certified_five_program_manifest_SHA256': sha(prior_four_manifest),
          'mode_environment': {'XG_KEEP_REVIEWED_GAIN': '1', 'XG_KEEP_REVIEWED_ENDING': '1', 'XG_KEEP_REVIEWED_CUTS': '1'},
          'default_original_auto_behavior_real_pair_deep_exact': True, 'existing_bad_join_original_gate_and_shell_reject': True,
          'actual_complete02_cuts_tests': str(N / 'real-cuts-mode-tests.json'),
          'actual_model_namespace_tests': str(N / 'real-ending-mode-tests.json'),
          'actual_pronunciation_original_namespace_tests': str(N / 'real-pronunciation-selftest-tests.json'),
          'pronunciation_normal_checker_all_AST_and_output_unchanged': True,
          'producer_before_SHA256': '4c85e1fbdd2e82c5646d5f58df63c85eca60af4ef521f1d36f765575a568d6f3',
          'producer_after_SHA256': '6945e9bee6db143029bace6c04b4f4df7110c41ba647eee7236b0d0e5ed75203',
          'producer_changed_only_pron_dictionary_activation_case_policy': True,
          'audit_unchanged_SHA256': 'bfe12dab6bec96c9b765faea286ae30a067589f6c5ef78461b21d12b955f1e22',
          'all_checkers_unchanged_claim': False, 'original_full_fastcheck_program_changed': False,
          'quality_thresholds_lowered': False, 'original_audio_MD5_baseline_changed': False,
          'approved_67gold_SHA256': sha(gold), 'actual_original_full_stamp_SHA256': sha(stamp),
          'complete_production_T_original_stamp_validation': str(O / 'actual-production-full-T-stamp-proof.json'),
          'all_production_program_count_verified': len(after_map),
          'production_install_or_source_JSON_GEN_MD_write': False, 'private_PCM_exported': False,
          'installation_scope': 'Only these8 runtime files. Historical test fixtures stay in independent regression context, never production article JSON/GEN/MD/confirmations.',
          'article_audio_or_video_accepted_by_this_certificate': False,
          'actual_native_dispatch_tests': str(N / 'real-dispatch-mode-tests.json'),
          'native16_internal_cache_evidence': cache16,
          'historical_overlay_program_count_correction': {'original_artifact_field': manifest.get('final_integrated_program_count'), 'actual_unique_program_files_verified': len(manifest['files']), 'original_artifact_preserved': True}}
(D / 'manifest.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
(O / 'validated-final-report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'status': report['status'], 'runtime_files': 8, 'full_production_programs': len(after_map),
                  'actual_stamp_SHA256': sha(stamp), 'original_full_exit': 0, 'production_written': False}, ensure_ascii=False))
