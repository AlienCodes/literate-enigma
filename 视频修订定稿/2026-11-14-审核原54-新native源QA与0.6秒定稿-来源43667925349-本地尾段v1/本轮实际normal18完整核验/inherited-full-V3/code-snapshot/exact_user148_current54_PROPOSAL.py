"""Proposed exact book47/source54 final consumer; inactive until actual results freeze.

This does not produce media, certify acoustics, promote the review102 artifact,
or change original checks. It consumes a FRESH genuine native all-gates result
under user148 and preserves the current-versus-legacy distinction.
"""
import json
from pathlib import Path

PROFILE = json.loads(Path(__file__).with_name('exact-user148-current54-PROPOSAL-profile.json').read_text())
BASIS = 'actual_original_audio_gates_plus_user148_current_native_final'


def role(native, article):
    """Narrow importer dispatch only; final check() remains mandatory."""
    return (article == '54' and native.get('article') == '54'
            and native.get('review_only') is False
            and native.get('user_individual_finalization_authorized') is True
            and native.get('request_source_sha256') == PROFILE['exact_request_source_sha256'])


def check(review, native, article, actual_aac_sha, evidence_hashes, status_sha, require):
    p = PROFILE
    # Deliberately false in the proposal. Only actual probe/native artifacts,
    # actual root review, and immutable native identities can populate/freeze it.
    require(p['frozen_after_actual_native_results'] is True,
            'Exact148 proposal is not an actual frozen production result')
    f = p['fresh_native_binding']
    require(isinstance(f, dict) and role(native, article),
            'Only exact54 new user148 source/GEN/MD/aux formal native result')
    require(f['run_id'] != 43642838698 and f['upstream_status_sha256'] == status_sha,
            'The historical user102 status cannot be promoted as a new user148 result')
    require(review['tool'] == 'native_official_audio_gates'
            and review['actual_new_output'] is True and review['status'] == 'passed'
            and review['report_sha256'] == status_sha and status_sha in evidence_hashes
            and native.get('passed') is True and native.get('canonical_pipeline_passed') is True
            and native.get('stage') == 'final4K-passed',
            'Actual fresh complete original native gates remain mandatory')
    require(native.get('original_audit_and_quality_thresholds_unchanged') is True
            and native.get('original_maker_unchanged') is True
            and native.get('strict_production_cache') is True
            and native.get('core_repair_manifest_sha256') == p['original_five_core_contract_sha256']
            and native.get('checker_reference_preparation', {}).get('maker_sha256') == p['original_maker_sha256']
            and all(native.get(k) is True for k in
                    ('reviewed_gain_preservation_mode', 'reviewed_existing_ending_preservation_mode',
                     'reviewed_existing_physical_cuts_preservation_mode')),
            'Original maker, five-core runtime, thresholds, strict cache and reviewed controls differ')
    require(review['canonical_video_sha256'] == native['video_sha256']
            == f['selected_canonical_video_sha256']
            and native['canonical_video_sha256'] == f['raw_canonical_video_sha256'],
            'The reviewed canonical and native original containers must bind actual fresh bytes')
    require(native['final_wav_sha256'] == p['current_audio']['whole_WAV_sha256']
            and native['canonical_aac_adts_sha256'] == actual_aac_sha
            == p['current_audio']['aac_adts_sha256'],
            'This exact no-audio-change route requires the real entire current WAV/AAC')
    require(native.get('accepted_prior_aac_identical') is False
            and native['accepted_source']['sha256'] == p['legacy_provenance']['video_sha256']
            and native['accepted_source']['aac_adts_sha256'] == p['legacy_provenance']['aac_adts_sha256']
            and actual_aac_sha != p['legacy_provenance']['aac_adts_sha256'],
            'Keep legacy provenance historical; never invent legacy AAC equality')
    c = native['actual_source_collection']['files']
    require(c['request_json']['sha256'] == p['exact_request_source_sha256']['视频/脚本/54.json']
            and c['actual_working_source']['sha256'] == f['actual_working_source_sha256']
            == '0b5a23c782d606bd8333c468438c8d975f98ab97116a73975b84a8bcba4dac18'
            and f['actual_final_LF_only_source_role_observation_sha256'] in evidence_hashes
            and c['request_generator']['sha256'] == c['used_generator']['sha256']
            == p['exact_request_source_sha256']['视频/工具/初稿生成/gen54.py']
            and c['request_manuscript']['sha256'] == c['actual_working_manuscript']['sha256']
            == p['exact_request_source_sha256']['新版定稿/54-the-sound-that-shook-the-world.md'],
            'New source collection must preserve exact candidate and all observed source identities')
    require(native['reviewed_gain_control_preservation']
            and all(x['exactly_preserved'] is True and x['requested_gain_controls'] == x['actual_gain_controls'] == {}
                    for x in native['reviewed_gain_control_preservation']),
            'No new manual gain or blanket confirmation edits allowed by this route')
    a = f['actual_S6_probe_and_root_decision']
    require(a['source_sha256'] == p['current_before_source_sha256']
            and a['helper_sha256'] == p['S6_probe_helper_sha256']
            and a['finding'] == 'actual_onset_and_levels_do_not_require_audio_change'
            and all(x in evidence_hashes for x in
                    (a['report_sha256'], a['root_actual_result_decision_sha256'],
                     f['root_final_consumer_adoption_decision_sha256'],
                     f['native_user_authorization_sha256'],
                     p['user147_raw_sha256'], p['user148_raw_sha256'],
                     p['root_probe_code_adoption_sha256'])),
            'Actual probe, actual root finding and user148 authority must be physically bound evidence')
    return True


def current_packet_identity(actual_chain, require):
    """Called with delivery.actual_aac(canonical), not a claimed metadata string."""
    p = PROFILE['current_audio']
    require(all(actual_chain[k] == p[k] for k in
                ('aac_adts_sha256', 'packet_projection_sha256', 'packet_count')),
            'Exact current entire AAC payload/absolute packet clock/priming/count differ')

