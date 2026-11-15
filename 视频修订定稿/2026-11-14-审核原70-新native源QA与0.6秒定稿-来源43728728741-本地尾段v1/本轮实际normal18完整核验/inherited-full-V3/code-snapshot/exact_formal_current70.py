"""Only the individually finalized source70 native's original current voice.

This consumes original passed native records and an already measured current
reference. It never generates audio, changes a verdict, or claims legacy AAC
equality. The original artifact/remote, source and media gates remain callers.
"""
from pathlib import Path
import hashlib
import json

PROFILE_PATH = Path(__file__).with_name('exact-formal-source70-current-reference-profile.json')
PROFILE_SHA = hashlib.sha256(PROFILE_PATH.read_bytes()).hexdigest()
P = json.loads(PROFILE_PATH.read_text())
BASIS = 'actual_original_audio_gates_plus_exact_individual_final_current_reference'
IDENTITY = 'source70_original_current_review_voice_identity'


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1048576), b''):
            h.update(block)
    return h.hexdigest()


def is_candidate(article, native):
    return bool(article == '70' and native.get('article') == '70'
                and native.get('review_only') is False
                and native.get('user_individual_finalization_authorized') is True
                and native.get(IDENTITY, {}).get('identity_binding_passed') is True)


def checked(row, require):
    p = Path(row['path'])
    require(p.is_file() and not p.is_symlink() and p.resolve() == p
            and p.stat().st_size == row['bytes'] and digest(p) == row['sha256'],
            'Exact formal70 metadata pin differs: ' + str(p))
    return p


def metadata(require):
    require((P['source_id'], P['book_order'], P['native_run'], P['native_HEAD'],
             P['native_artifact_id']) == ('70', 50, 43728728741,
             '24f2cc7653cce2d07481b3dbc67dbe263e0e3b18', 14168420068),
            'Only actual source70/book50 final native metadata')
    for row in P['pins'].values():
        checked(row, require)
    old_h = json.loads(Path(P['pins']['old_review_H']['path']).read_text())
    old_r = json.loads(Path(P['pins']['old_review_record']['path']).read_text())
    old_s = json.loads(Path(P['pins']['old_review_status']['path']).read_text())
    old_p = json.loads(Path(P['pins']['old_review_voice_profile']['path']).read_text())
    require(old_h['source_run'] == 43638596213 and old_h['review_only'] is True
            and old_h['production_delivery_eligible'] is False
            and old_h['user_individual_finalization_authorized'] is False,
            'Historical review remains review-only, not whole/final acceptance')
    require(old_r['actual_audio_chain'] == P['actual_audio_chain']
            and old_s['final_wav_sha256'] == old_p['current_native_WAV_sha256'] == P['RAW_SHA256']
            and old_s['canonical_aac_adts_sha256'] == old_p['current_native_AAC_adts_sha256']
            == P['actual_audio_chain']['aac_adts_sha256'],
            'Actual old-current reference RAW/AAC/full packet clock differs')
    require(old_p['individual_final_authorized'] is False
            and old_p['formally_accepted_whole'] is False
            and old_p['legacy_accepted_AAC_adts_sha256'] == P['legacy_source']['aac_adts_sha256'],
            'Historical current-reference and legacy roles were relabelled')
    observed = json.loads(Path(P['pins']['formal_main_stdout_metadata']['path']).read_text())
    native_fields(observed, '70', require)
    return True


def native_fields(native, article, require):
    require(is_candidate(article, native) and native.get('book_order') == 50,
            'Only exact individually finalized source70/book50, not review-only')
    require(native.get('passed') is True and native.get('canonical_pipeline_passed') is True
            and native.get('stage') == 'final4K-passed'
            and native.get('original_audit_and_quality_thresholds_unchanged') is True
            and native.get('preview_only', False) is False,
            'All actual original complete native quality gates remain required')
    require(native.get('core_repair_manifest_sha256') == P['expected_core_manifest']
            and native.get('actual_native_fastcheck_stamp') == P['expected_stamp']
            and native.get('actual_native_core_certification') == P['expected_native_core_certification']
            and all(native.get(k) is True for k in ('reviewed_gain_preservation_mode',
                'reviewed_existing_ending_preservation_mode',
                'reviewed_existing_physical_cuts_preservation_mode')),
            'Original five-core certificate/stamp/GAIN/ENDING/CUTS differs')
    require(native.get('request_source_sha256') == P['request_source_sha256']
            and native.get('specific_final_authorization_sha256') == P['specific_final_authority_SHA256'],
            'Actual final request/GEN/MD/confirmation/final authority differs')
    require(native.get('final_wav_sha256') == P['RAW_SHA256']
            and native.get('canonical_aac_adts_sha256') == P['actual_audio_chain']['aac_adts_sha256']
            and native.get('canonical_video_sha256') == P['raw_canonical_video_SHA256'],
            'Actual final native RAW/AAC/canonical identity differs')
    require(native.get('accepted_prior_aac_identical') is False
            and native.get('accepted_source') == P['legacy_source']
            and native['canonical_aac_adts_sha256'] != P['legacy_source']['aac_adts_sha256'],
            'Keep distinct legacy accepted and current-reference AAC truthful')
    binding = native.get(IDENTITY, {})
    require(binding == P['actual_formal_identity_document']
            and binding.get('identity_binding_passed') is True
            and binding.get('formal_quality_acceptance') is False
            and binding.get('repair_applied') is False
            and binding.get('all_original_native_quality_checks_remain_required') is True
            and binding.get('actual_root_final_input_adoption_sha256') == P['root_final_source_adoption_SHA256'],
            'Actual identity-only binder is missing, changed, or promoted to quality')
    return True


def check(review, native, article, actual_aac_sha, evidence_hashes, status_sha, strict_review, require):
    require(strict_review is False, 'This exact current-reference role is not a repair waiver')
    metadata(require)
    native_fields(native, article, require)
    require(review['tool'] == 'native_official_audio_gates'
            and review['actual_new_output'] is True and review['status'] == 'passed'
            and review['canonical_video_sha256'] == native['video_sha256']
            and review['report_sha256'] == status_sha and status_sha in evidence_hashes,
            'Actual original canonical native status/review evidence differs')
    required = {row['sha256'] for row in P['pins'].values()} | {PROFILE_SHA, digest(__file__)}
    require(required <= set(evidence_hashes),
            'Original formal/current-review/authority/profile evidence is incomplete')
    require(actual_aac_sha == P['actual_audio_chain']['aac_adts_sha256'],
            'Actual selected canonical AAC differs from the original current voice')
    return True


def actual_audio(audio, require):
    require(all(audio.get(k) == v for k, v in P['actual_audio_chain'].items())
            and audio.get('projection', {}).get('codec') == P['codec'],
            'Actual copied codec/AAC/all packets/absolute clock differs from current reference')
    return True
