"""Finite proposed HOST role for actual source35/book54 authorized new S15.

Not A21, not legacy/current-voice equality, and not a dedicated MP4 acoustic
report. Quality remains the real complete native verdict. The pinned ROOT
phoneme/acoustic semantics and strict whole observer prove permission/scope,
never quality acceptance or human listening. Requires specific ROOT code review.
"""
from pathlib import Path
import hashlib
import json

PROFILE_PATH = Path(__file__).with_name('exact-formal-source35-new-S15-profile.json')
PROFILE_SHA = hashlib.sha256(PROFILE_PATH.read_bytes()).hexdigest()
P = json.loads(PROFILE_PATH.read_text())
BASIS = 'actual_original_native_audio_gates_plus_exact_authorized_new_S15_scope'
IDENTITY = 'source35_authorized_new_S15_physical_identity'


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1048576), b''):
            h.update(block)
    return h.hexdigest()


def is_candidate(article, native):
    return bool(article == '35' and native.get('article') == '35'
                and native.get('review_only') is False
                and native.get('user_individual_finalization_authorized') is True
                and native.get(IDENTITY, {}).get('identity_binding_passed') is True)


def checked(row, require):
    path = Path(row['path'])
    require(path.is_file() and not path.is_symlink() and path.resolve() == path
            and path.stat().st_size == row['bytes'] and digest(path) == row['sha256'],
            'Exact proposed formal35 public metadata pin differs: ' + str(path))
    return path


def scope_fields(scope, require):
    require((scope['source_id'], scope['book_order'], scope['target_sentence']) == ('35', 54, 'S15'),
            'Strict whole observer belongs only to source35/book54 S15')
    require(all(scope.get(k) is False for k in ('quality_acceptance', 'formal_acceptance',
                'production_delivery_eligible', 'immutable_owner_source_GEN_MD_or_CF_written')),
            'Do not promote diagnostic scope into quality/production acceptance or source edits')
    require(all(scope.get(k) is True for k in ('diagnostic_completed', 'exact_scope_proved',
                'no_new_TTS_authorized', 'both_actual_original_whole_observations_completed',
                'all_non_target_pre_master_and_effective_DSP_exact',
                'all_non_target_post_master_float_and_PCM16_exact',
                'actual_native_G35_WAV_AAC_packetcount_and_master1_hardmatched',
                'all_existing_private_cache_files_exact_before_after',
                'all_frozen_inputs_exact_after', 'runtime_contract_files_exact_after',
                'normal_original110_stamp_exact_after')),
            'Actual strict whole-scope or restoration facts are not complete')
    require(scope['forbidden_model_events'] == [] and scope['errors'] == []
            and scope['actual_new_target_original_G36'] == {}
            and scope['actual_global_master_scale_ratio_selected_over_baseline'] == 1.0
            and all(value is True for value in scope['restoration'].values()),
            'No new model/G36, master change, failure or un-restored inputs permitted')
    rows = scope['all_non_target_title_and_sentence_identity']
    require(len(rows) == 21 and {row['segment'] for row in rows}
            == {'title'} | {'S'+str(i) for i in range(1, 22) if i != 15},
            'All title and20 non-target sentence scopes must be present exactly once')
    for row in rows:
        require(all(row.get(k) is True for k in ('pre_master_array_exact',
                    'effective_source_DSP_exact', 'post_master_float_array_exact',
                    'actual_WAV_PCM16_array_exact'))
                and all(row['baseline_'+k] == row['selected_'+k]
                        for k in ('pre_SHA256', 'post_SHA256', 'PCM16_SHA256'))
                and {key: row[key] for key in ('baseline_clock', 'selected_clock')}
                == P['actual_non_target_clock_map'][row['segment']]
                and row['baseline_clock']['end_sample_exclusive']-row['baseline_clock']['start_sample']
                == row['selected_clock']['end_sample_exclusive']-row['selected_clock']['start_sample'],
                'Non-target local PCM/DSP or exact actual old/new clock-map changed')
    selected = scope['phases']['selected']
    wav = selected['actual_complete_WAV']
    require(wav['file_sha256'] == P['RAW_SHA256'] and wav['file_bytes'] == P['master_bytes']
            and wav['file_md5'] == '7c7afa6f721a1311976e81993c8a7ced'
            and wav['file_md5_first12'] == '7c7afa6f721a'
            and wav['sample_rate'] == 24000 and wav['subtype'] == 'PCM_16'
            and selected['actual_codec_packet_payload_side_and_absolute_clock'] == P['actual_audio_chain'],
            'Strict observer must bind actual selected master and entire AAC/packet clock')
    return True


def semantic_fields(semantic, require):
    require((semantic['source_id'], semantic['book_order'], semantic['sentence']) == ('35', 54, 'S15')
            and semantic['human_listening_or_user_confirmation_performed'] is False
            and semantic['no_quality_threshold_waiver_or_fake_user_grant'] is True
            and semantic['actual_selected_whole_WAV_SHA256'] == P['RAW_SHA256']
            and semantic['actual_selected_whole_MD5'] == '7c7afa6f721a1311976e81993c8a7ced'
            and semantic['actual_raw_S15_FP'] == '6a4205ab64e1',
            'Only actual ROOT acoustic-semantic review, never human/user listening')
    decisions = semantic['two_exact_decisions']
    require(len(decisions) == 2 and [row['native_PV_id'] for row in decisions] == [12, 13]
            and [row['native_displayed_window_s'] for row in decisions]
            == [[100.72, 100.83], [102.67, 102.72]]
            and [row['absolute_window_s'] for row in decisions]
            == [[100.725, 100.825], [102.665, 102.72]]
            and [row['raw_w_window_s'] for row in decisions] == [[1.295, 1.395], [3.235, 3.29]]
            and [row['decision'] for row in decisions] == [
                'retain_speech_do_not_cut; permit exact-window assistant-reviewed speech false-positive metadata',
                'retain_twist_final_t_release_do_not_cut; permit exact-window assistant-reviewed speech false-positive metadata'],
            'Only the two actually reviewed speech-bearing windows may be retained')
    return True


def native_fields(native, article, require):
    require(is_candidate(article, native) and native.get('book_order', 54) == 54,
            'Only exact personally finalized source35/book54, not review-only')
    require(native.get('passed') is True and native.get('canonical_pipeline_passed') is True
            and native.get('stage') == 'final4K-passed'
            and native.get('original_audit_and_quality_thresholds_unchanged') is True
            and native.get('preview_only', False) is False,
            'Actual complete native quality verdict is still required separately')
    require(native.get('original_maker_unchanged') is False
            and native.get('core_repair_manifest_sha256') == P['expected_core_manifest']
            and native.get('actual_native_fastcheck_stamp') == P['expected_stamp']
            and native.get('actual_native_core_certification') == P['expected_native_core_certification']
            and all(native.get(k) is True for k in ('reviewed_gain_preservation_mode',
                'reviewed_existing_ending_preservation_mode',
                'reviewed_existing_physical_cuts_preservation_mode')),
            'Actual approved changed maker/core20 certificate/stamp/GAIN/ENDING/CUTS differs')
    require(native.get('request_source_sha256') == P['request_source_sha256']
            and native.get('specific_final_authorization_sha256') == P['specific_final_authority_SHA256'],
            'Actual source/GEN/MD/confirmation/user final authority differs')
    require(native.get('final_wav_sha256') == P['RAW_SHA256']
            and native.get('canonical_aac_adts_sha256') == P['actual_audio_chain']['aac_adts_sha256']
            and native.get('canonical_video_sha256') == P['raw_canonical_video_SHA256'],
            'Actual new native master/AAC/raw canonical differs')
    require(native.get('accepted_prior_aac_identical') is False
            and native.get('accepted_source') == P['legacy_source']
            and native['canonical_aac_adts_sha256'] != P['legacy_source']['aac_adts_sha256'],
            'Keep new S15 audio and legacy AAC distinct')
    binding = native.get(IDENTITY, {})
    require(binding == P['actual_identity_document']
            and binding['identity_binding_passed'] is True
            and binding['formal_quality_acceptance'] is False
            and binding['all_original_native_quality_checks_required_and_reported_passed'] is True,
            'Identity-only binder is missing, changed or promoted to quality')
    require('approved_audio_qc' not in native and 'approved_audio_repair_scope' not in native
            and native.get('original_confirmation_migration') == P['expected_migration']
            and native.get('confirmation_continuity') == P['expected_continuity'],
            'Do not fabricate A21/dedicated QC or overwrite actual confirmation migration')
    return True


def metadata(require):
    require((P['source_id'], P['book_order'], P['native_run'], P['native_HEAD'],
             P['native_artifact_id']) == ('35', 54, 43741796325,
             '69bae0668167df392226582af5297311e11e23b7', 14173591877)
            and P['new_finite_contract_requires_ROOT_specific_code_review'] is True
            and P['dedicated_acoustic_MP4_QC_report_exists'] is False
            and P['human_listening_or_user_hearing_claimed'] is False,
            'Only actual source35 finite role; dedicated QC/human claims remain absent')
    for row in P['pins'].values():
        checked(row, require)
    def read(key): return json.loads(Path(P['pins'][key]['path']).read_text())
    native_fields(read('formal_main_stdout_aux_not_ART_member'), '35', require)
    scope_fields(read('actual_scope_diagnostic_not_acceptance'), require)
    semantic_fields(read('actual_two_PV_ROOT_acoustic_semantics_not_human'), require)
    source = read('request:视频/脚本/35.json')
    require(source['结尾句'] == {'S21': P['expected_original_S21_ending']}
            and source['除阻加强'] == {'S15': {'句末': [3.235, 3.295, 4.0]}}
            and source['区间声音指纹']['S15'] == '6a4205ab64e1',
            'Actual S15-only original G35 boost/raw mother or original S21 ending differs')
    confirmations = source['核对确认']['非人声']
    require(len(confirmations) == 21 and all(confirmations[key]['配音指纹'] == '7c7afa6f721a'
            and '非人耳听审、非用户确认' in confirmations[key]['依据']
            for key in ('100.72–100.83s', '102.67–102.72s')),
            'Preserve19 exact-PCM migrated NVs plus only two actual acoustic-semantic CFs')
    return True


def role_metadata():
    return dict(kind='exact-source35-authorized-new-S15-distinct-original-native-quality-and-scope',
                quality_verdict_source='actual complete original native gates',
                quality_report_SHA256=P['pins']['formal_main_stdout_aux_not_ART_member']['sha256'],
                scope_report_SHA256=P['pins']['actual_scope_diagnostic_not_acceptance']['sha256'],
                ROOT_acoustic_semantic_SHA256=P['pins']['actual_two_PV_ROOT_acoustic_semantics_not_human']['sha256'],
                final_authority_SHA256=P['specific_final_authority_SHA256'],
                changed_audio=True, accepted_prior_aac_identical=False,
                original_maker_unchanged=False, dedicated_MP4_acoustic_QC_report_exists=False,
                diagnostic_scope_quality_acceptance=False, identity_formal_quality_acceptance=False,
                human_listening_or_user_confirmation_performed=False)


def check(review, native, article, actual_aac_sha, evidence_hashes, status_sha, strict_review, require):
    require(strict_review is True, 'Actual new S15 must remain changed audio, never repair waiver')
    metadata(require)
    native_fields(native, article, require)
    require(review['tool'] == 'native_official_audio_gates'
            and review['actual_new_output'] is True and review['status'] == 'passed'
            and review['canonical_video_sha256'] == native['video_sha256']
            and review['report_sha256'] == status_sha and status_sha in evidence_hashes,
            'Original actual selected canonical native QC status identity/evidence differs')
    required = {row['sha256'] for row in P['pins'].values()} | {PROFILE_SHA, digest(__file__)}
    require(required <= set(evidence_hashes), 'Complete native/scope/semantic/core/authority evidence required')
    require(actual_aac_sha == P['actual_audio_chain']['aac_adts_sha256'],
            'Selected AAC differs from actual authorized new S15 native')
    return True


def actual_audio(audio, require):
    require(all(audio.get(k) == v for k, v in P['actual_audio_chain'].items())
            and audio.get('projection', {}).get('codec') == P['codec'],
            'Actual entire AAC/codec/packet count/absolute clock differs from new S15')
    return True


def controlled_repair_card(review, native, article, selected_sha, audio, evidence_hashes, status_sha, require):
    """Adapt the real passed native verdict; diagnostic scope never supplies it."""
    require(set(review) == {'tool', 'actual_new_output', 'status', 'canonical_video_sha256', 'report_sha256'}
            and review['canonical_video_sha256'] == selected_sha,
            'Controlled metadata card must bind exact native verdict fields and selected container')
    check(review, native, article, audio['aac_adts_sha256'], evidence_hashes, status_sha, True, require)
    actual_audio(audio, require)
    require(type(review['actual_new_output']) is bool and type(native['accepted_prior_aac_identical']) is bool,
            'Controlled metadata card requires actual boolean native roles')
    return dict(
        kind='metadata-adapter-of-real-native-quality-verdict-and-authorized-new-S15-scope-not-dedicated-MP4-QC',
        source_id='35', book_order=54, target_sentence='S15',
        status=review['status'], actual_new_output=review['actual_new_output'],
        canonical_video_sha256=selected_sha, report_sha256=status_sha,
        quality_verdict_source='actual passed original canonical native status; not diagnostic scope',
        canonical_qc=dict(review),
        authorization=dict(
            specific_user_final_authority_SHA256=P['specific_final_authority_SHA256'],
            original_native_user_authority_SHA256=P['pins']['actual_native_user_authority']['sha256'],
            original_G35_scope_ROOT_authority_SHA256=P['pins']['actual_scope_authority_not_acceptance']['sha256'],
            two_PV_acoustic_semantic_ROOT_authority_SHA256=P['pins']['actual_two_PV_ROOT_acoustic_semantics_not_human']['sha256'],
            public_archive_authority_SHA256=P['pins']['actual_global_archive_authority']['sha256']),
        actual_new_RAW_SHA256=P['RAW_SHA256'],
        actual_new_audio_chain=dict(P['actual_audio_chain']), actual_new_codec=dict(P['codec']),
        actual_native_status_SHA256=status_sha,
        actual_original_raw_body_video_SHA256=P['raw_canonical_video_SHA256'],
        actual_selected_canonical_video_SHA256=selected_sha,
        actual_original20_maker_SHA256=P['actual_original20_program_SHA256']['make_video.py'],
        actual_original20_core_manifest_SHA256=P['expected_core_manifest'],
        actual_original20_certificate=dict(P['expected_native_core_certification']),
        actual_original20_stamp=dict(P['expected_stamp']),
        repair_applied=True, accepted_prior_aac_identical=False, original_maker_unchanged=False,
        legacy_accepted_AAC_SHA256=P['legacy_source']['aac_adts_sha256'],
        dedicated_MP4_acoustic_QC_report_exists=False, A21_report_claimed=False,
        identity_formal_quality_acceptance=False,
        scope=dict(report_SHA256=P['pins']['actual_scope_diagnostic_not_acceptance']['sha256'],
                   quality_acceptance=False, formal_acceptance=False, production_delivery_eligible=False,
                   title_and20_nontarget_local_PCM_and_DSP_exact=True, master_ratio=1.0,
                   old_new_whole_absolute_packet_clock_equality_claimed=False,
                   actual_S16_through_S21_delta_samples=-6960,
                   exact_old_and_new_sample_clock_map_profile_SHA256=PROFILE_SHA),
        two_PV_semantics=dict(ROOT_record_SHA256=P['pins']['actual_two_PV_ROOT_acoustic_semantics_not_human']['sha256'],
                              actual_raw_S15_FP='6a4205ab64e1', actual_whole_MD5_prefix='7c7afa6f721a',
                              exact_native_displayed_windows_s=[[100.72, 100.83], [102.67, 102.72]],
                              human_listening_or_user_confirmation_performed=False,
                              no_new_quality_threshold_or_fake_hearing_claim=True))


def typed_metadata(value):
    if isinstance(value, dict):
        return ('dict', tuple(sorted((key, typed_metadata(part)) for key, part in value.items())))
    if isinstance(value, list):
        return ('list', tuple(typed_metadata(part) for part in value))
    return (type(value).__name__, value)


def validate_controlled_repair_card(card, review, native, article, selected_sha, audio,
                                    evidence_hashes, status_sha, require):
    expected = controlled_repair_card(review, native, article, selected_sha, audio,
                                      evidence_hashes, status_sha, require)
    require(type(card) is dict and typed_metadata(card) == typed_metadata(expected),
            'Controlled metadata card differs from actual native verdict/authority/scope/voice')
    require(card['status'] == 'passed' and card['actual_new_output'] is True
            and card['repair_applied'] is True and card['accepted_prior_aac_identical'] is False
            and card['original_maker_unchanged'] is False,
            'Original all70 controlled-repair status and truthful new S15 roles remain required')
    return True
