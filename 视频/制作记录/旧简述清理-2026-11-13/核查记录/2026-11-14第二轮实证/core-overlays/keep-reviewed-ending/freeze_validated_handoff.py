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
N = O / 'native-results/43544532286/keep-reviewed-ending'
PKG = O / 'native-ready/.github/reviewed-ending-certification'
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
C = json.loads((N / 'certification.json').read_text())
receipt = json.loads((N / 'artifact-receipt.json').read_text())
assert C['passed'] is True and C['stage'] == 'independent-core-certification-passed'
assert receipt['run_id'] == 43544532286 and receipt['source_commit'] == 'cc3ee0b02f42f70fb3f4041501dc6036d3240a89'
assert receipt['full_ZIP_digest_verified_before_extraction'] is True
checks = {x['name']: x for x in C['checks']}
for key in ['new-ending-mode-real-tests', 'original-full-fastcheck', 'real-stamp-validation', 'new-mode-functional-tests']:
    assert checks[key]['exit'] == 0
stamp = N / 'real-fastcheck-stamp.json'
assert sha(stamp) == C['real_fastcheck_stamp_SHA256']
S = json.loads(stamp.read_text())
manifest = json.loads((PKG / 'overlay-manifest.json').read_text())
assert len(manifest['files']) == 4
ending = json.loads((N / 'real-ending-mode-tests.json').read_text())
assert ending['status'] == 'passed_real_complete_original_namespace_ending_mode_tests'
assert ending['good_original_source']['JSON_all_bytes_and_all_metadata_preserved'] is True
assert all(x['original_bad_point_gate_rejected'] and x['no_automatic_fallback_or_write'] for x in ending['bad_front_and_tail'])
assert ending['default_mode']['original_vs_candidate_auto_full_JSON_deep_exact'] is True
assert ending['actual_shell_pipeline_bad_point_exit_propagated'] is True
assert ending['no_existing_points_uses_exact_original_auto_algorithm'] is True
full = (N / 'original-full-fastcheck.log').read_text()
assert '快测通过' in full and 'a.wav、分段.json 逐字节、每屏像素一致' in full
assert '交付核查 出片前/出片后 + 出片守门自检：全过' in full
for x in C['real_cached_source_measurements']:
    assert x['source_JSON_and_approved_gain_byte_exact_after_measurement'] and x['actual_audio_file_byte_exact_after_measurement']
D = O / 'validated-install'
files = []
for f in manifest['files']:
    src = PKG / 'patch' / f['path']
    assert sha(src) == f['patch_SHA256'] == C['actual_core_SHA256'][f['path']]
    assert S['程序'][f['path'][len('视频/工具/'):]] == f['patch_SHA256'][:16]
    dst = D / f['path']
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dst)
    files.append({'path': f['path'], 'original_main_SHA256': f['main_SHA256'],
                  'previous_certified_SHA256': f.get('certified_before_SHA256', f['patch_SHA256']),
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
assert len(files) == 6
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
report = {'status': 'validated_four_program_runtime_install_ready_not_installed',
          'run_id': 43544532286, 'job_id': 132292612475, 'source_commit': receipt['source_commit'],
          'actual_full_quickcheck_exit': 0, 'actual_full_quickcheck_seconds': checks['original-full-fastcheck']['seconds'],
          'original_full_log_SHA256': sha(N / 'original-full-fastcheck.log'), 'artifact': receipt,
          'program_count': 4, 'runtime_file_count': 6, 'runtime_install_files': files,
          'mode_environment': {'XG_KEEP_REVIEWED_GAIN': '1', 'XG_KEEP_REVIEWED_ENDING': '1'},
          'default_original_auto_behavior_real_pair_deep_exact': True, 'existing_bad_join_original_gate_and_shell_reject': True,
          'actual_model_namespace_tests': str(N / 'real-ending-mode-tests.json'),
          'producer_unchanged_SHA256': '4c85e1fbdd2e82c5646d5f58df63c85eca60af4ef521f1d36f765575a568d6f3',
          'audit_unchanged_SHA256': 'bfe12dab6bec96c9b765faea286ae30a067589f6c5ef78461b21d12b955f1e22',
          'all_checkers_unchanged_claim': False, 'original_full_fastcheck_program_changed': False,
          'quality_thresholds_lowered': False, 'original_audio_MD5_baseline_changed': False,
          'approved_67gold_SHA256': sha(gold), 'actual_original_full_stamp_SHA256': sha(stamp),
          'complete_production_T_original_stamp_validation': str(O / 'actual-production-full-T-stamp-proof.json'),
          'all_production_program_count_verified': len(after_map),
          'production_install_or_source_JSON_GEN_MD_write': False, 'private_PCM_exported': False,
          'installation_scope': 'Only these6 runtime files. Historical test fixtures stay in independent regression context, never production article JSON/GEN/MD/confirmations.',
          'article_audio_or_video_accepted_by_this_certificate': False}
(D / 'manifest.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
(O / 'validated-final-report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'status': report['status'], 'runtime_files': 6, 'full_production_programs': len(after_map),
                  'actual_stamp_SHA256': sha(stamp), 'original_full_exit': 0, 'production_written': False}, ensure_ascii=False))
