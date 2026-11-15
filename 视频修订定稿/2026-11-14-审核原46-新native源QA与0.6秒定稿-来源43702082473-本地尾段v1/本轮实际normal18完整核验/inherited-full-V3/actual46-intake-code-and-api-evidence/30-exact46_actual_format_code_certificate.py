"""Exact actual source46 format-code certification; never acoustic acceptance.

The original source and full-media validators remain unchanged. This additional
entry check preserves the old95 stamp role and requires the actually generated
new stamp and complete original fastcheck before consuming this one native run.
"""
from pathlib import Path
import hashlib
import json
import delivery as D


def checked(row):
    path = Path(row['path'])
    D.require(path.is_file() and path.stat().st_size == row['bytes']
              and D.digest(path) == row['sha256'], 'Exact46 code-certificate evidence differs')
    return path


def verify(profile, native):
    D.require(profile['article'] == native['article'] == '46'
              and profile['book_order'] == '48' and profile['run_id'] == 43702082473
              and profile['head_sha'] == '43844a158ae2a4aae76e05377a5a5337331f5bcc',
              'Only actual source46 run43702082473 format-code roles')
    D.require(native['passed'] is True and native['canonical_pipeline_passed'] is True
              and native['original_maker_unchanged'] is False
              and native['original_audit_and_quality_thresholds_unchanged'] is True
              and native['original_numeric_rules_and_all_native_quality_gates_unchanged'] is True
              and native['audio_or_confirmation_metadata_approved_by_format_helper'] is False,
              'Real native gates and truthful modified-maker/code-only roles required')
    roles = profile['exact_format_roles']
    cert = D.load(checked(roles['actual_certificate']))
    D.require(native['exact_user_requested_format_code_certification'] == cert,
              'Native and exported format-code certificate differ')
    D.require(cert['article'] == '46' and cert['book_order'] == 48
              and cert['code_certification_passed'] is True and cert['runtime_installed'] is True
              and cert['native_article_passed'] is False and cert['article_audio_accepted'] is False
              and cert['audio_or_confirmation_metadata_approved_by_format_helper'] is False,
              'Format code certification must not impersonate article/audio acceptance')
    expected = '118f49d11edf54345cdc4064ca4241f5aa7cecc3a00ff646f610f5e3f003d1f7'
    D.require(cert['immutable_request_sha256'] == expected
              == native['request_source_sha256']['视频/脚本/46.json'], 'Actual46 request differs')
    reviewed = D.load(checked(roles['reviewed_code_profile']))
    D.require(cert['candidate_programs'] == reviewed['candidate_programs']
              and cert['actual_root_code_adoption']['sha256'] == roles['root_code_adoption']['sha256']
              and cert['actual_setup_fix_root_code_adoption']['sha256'] == roles['root_setup_font_adoption']['sha256'],
              'Exact root-adopted four programs and font/setup roles required')
    core = D.load(checked(roles['original_core_manifest']))
    D.require(native['core_repair_manifest_sha256'] == roles['original_core_manifest']['sha256']
              == 'f169b9b2110bff4b346f010661033c4b6bc5367e31ea1bfcecf015d435db778c'
              and native['reviewed_gain_preservation_mode'] is True
              and native['reviewed_existing_ending_preservation_mode'] is True,
              'Actual original fivecore/GAIN/ENDING roles required')
    old_path = checked(roles['original_old95_stamp'])
    new_path = checked(roles['actual_new_stamp'])
    D.require(roles['original_old95_stamp']['sha256'] == cert['original_fivecore_stamp_sha256']
              == native['actual_native_fastcheck_stamp']['sha256']
              == '95a51b15bb4b71b8842851da8d16bb4109231f1ba69e24826792f2a718ef4a4a'
              and roles['actual_new_stamp']['sha256'] != roles['original_old95_stamp']['sha256']
              and cert['actual_original_generated_new_stamp']['sha256'] == roles['actual_new_stamp']['sha256']
              and cert['actual_original_generated_new_stamp']['bytes'] == roles['actual_new_stamp']['bytes'],
              'Old original95 cannot represent newly installed format-code certification')
    old_stamp, new_stamp = D.load(old_path), D.load(new_path)
    expected_programs = dict(old_stamp['程序'])
    expected_programs.update({name: row['sha256'][:16] for name, row in cert['candidate_programs'].items()})
    D.require(new_stamp['程序'] == expected_programs
              and {k:v for k,v in old_stamp.items() if k != '程序'}
              == {k:v for k,v in new_stamp.items() if k != '程序'},
              'Only the exact four adopted format programs may change original stamp identity')
    expected_steps = ['original-fivecore-stamp-before-format-install',
                      'original-module-copy-with-exact-format-helper',
                      'original-full-fastcheck-after-format-install', 'original-new-stamp-verification']
    D.require([r['name'] for r in cert['actual_steps']] == expected_steps
              and all(r['exit'] == 0 for r in cert['actual_steps']), 'Complete actual original fastcheck required')
    root = Path(profile['native_root']) / 'artifact-files'
    for row in cert['actual_steps']:
        path = root / (row['name'] + '.log')
        D.require(path.is_file() and D.digest(path) == row['log_sha256'],
                  'Actual original full-fastcheck/stamp log differs')
    fixtures = cert['actual_original95_historical_fixture_context']
    D.require(fixtures['all_sources_preflight_SHA_passed'] is True
              and fixtures['original_files_or_absence_restored'] is True
              and fixtures['historical_fixtures_active_only_inside_original_fullquick_context'] is True
              and fixtures['restore_errors'] == [], 'Original fixture context was not restored')
    D.require(cert['actual_original_font_context']['original_four_font_fullSHA_exact_in_all_three_roles'] is True
              and cert['actual_original_font_context']['font_files_changed'] is False
              and cert['original_alias_and_ROOT_W_fonts_preexist_before_fullquick'] is True,
              'Exact original font/context role differs')
    return {'actual_code_certificate_and_new_stamp_verified': True,
            'modified_maker_role_retained_false': True,
            'article_audio_acceptance_from_format_helper_claimed': False,
            'original_fastcheck_log_and_new_stamp_verified': True}
