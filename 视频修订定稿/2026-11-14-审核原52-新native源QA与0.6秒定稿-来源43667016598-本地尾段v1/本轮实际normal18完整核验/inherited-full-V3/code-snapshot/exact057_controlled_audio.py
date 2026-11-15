"""Candidate: exact two real first34 instruments, not a new acoustic checker.

No media is generated or approved here. Actual native full quality gates and
the unchanged V3 canonical-to-card/final complete packet comparisons remain
required separately. Bindings are snapshots, to be refreshed only from the
producer's actually frozen request/reference before using a new artifact.
"""
import json
import re
from pathlib import Path


def require(ok, message):
    if not ok:
        raise ValueError(message)


PROFILES = json.loads((Path(__file__).with_name('exact057-instrument-bindings.json')).read_text())['profiles']


def actual_exact057_repair_scope(review, native, raw_audio, article):
    require(article in PROFILES, 'Exact057 repair is limited to source05/source67')
    p = PROFILES[article]
    require(raw_audio.get('article') == native.get('article') == article,
            'Exact057 instrument/source ID mismatch')
    require(native.get('passed') is True and native.get('canonical_pipeline_passed') is True and
            native.get('stage') == 'final4K-passed',
            'Exact057 instrument cannot replace actual complete native quality gates')
    require(raw_audio.get('kind') == p['report_kind'] and
            raw_audio.get('passed') is True and raw_audio.get('repair_applied') is True and
            not raw_audio.get('error') and native.get('approved_audio_qc') == raw_audio,
            'Exact057 actual original dedicated report is not passed or differs from native')
    scope = native.get('approved_audio_repair_scope', {})
    require(scope.get('kind') == 'controlled_audio_repair' and scope.get('repair_applied') is True and
            scope.get('actual_original_full_pipeline_passed_first') is True and
            scope.get('whole_track_actual_audio_and_approved_unchanged_regions_required') is True,
            'Exact057 original native repair scope absent')
    f = p['fingerprints']
    request = native.get('request_source_sha256', {})
    require(request.get('视频/脚本/' + article + '.json') ==
            scope.get('request_source_sha256') == review.get('request_source_sha256') ==
            f['request_source_sha256'] and
            request.get('视频/工具/初稿生成/gen' + article + '.py') == f['request_generator_sha256'],
            'Exact057 immutable request/source/GEN binding differs')
    require(review.get('tool') == p['runtime_helper_name'] and
            native.get('approved_audio_qc_program_sha256') == raw_audio.get('program_sha256') ==
            review.get('program_sha256') == p['program_sha256'] and
            scope.get('reference_file_sha256') == raw_audio.get('reference_sha256') ==
            review.get('reference_file_sha256') == p['reference_sha256'],
            'Exact057 actual program/reference identity differs')
    require(native.get('final_wav_sha256') == f['actual_raw_WAV_sha256'] and
            native.get('canonical_aac_adts_sha256') == f['canonical_AAC_ADTS_sha256'] and
            native.get('accepted_source', {}).get('sha256') == f['accepted_video_sha256'] and
            native.get('accepted_source', {}).get('aac_adts_sha256') == f['accepted_AAC_ADTS_sha256'] and
            raw_audio.get('canonical_sha256') == native.get('canonical_video_sha256') and
            re.fullmatch('[0-9a-f]{64}', raw_audio.get('canonical_sha256', '')) is not None and
            raw_audio.get('accepted_sha256') == f['accepted_video_sha256'],
            'Exact057 new actual canonical/raw/AAC or historical accepted lineage differs')
    checks = raw_audio.get('checks', [])
    by_name = {r.get('name'): r for r in checks}
    require(checks and len(by_name) == len(checks) and
            set(p['required_check_names']) <= set(by_name) and
            all(r.get('passed') is True for r in checks),
            'Exact057 real original supplement has missing/duplicate/failed checks')
    if article == '05':
        # This ORIGINAL instrument does not export diagnostic_only or an
        # eligibility boolean. Actual native success above is the prerequisite.
        require(raw_audio.get('original_quality_gates_modified') is False and
                raw_audio.get('requires_separate_original_complete_pipeline_pass') is True and
                raw_audio.get('private_raw_GT_or_cache_arrays_exported') is False,
                'Source05 original supplement must preserve the separate native gates')
        require(by_name['actual-entire-AAC-matches-exact-approved-physical-source-reconstruction'].get('actual') ==
                f['canonical_AAC_ADTS_sha256'] and
                by_name['actual-entire-producer-PCM-matches-approved-physical-source-reconstruction'].get('actual') ==
                f['actual_raw_WAV_sha256'],
                'Source05 measured whole raw/AAC fingerprint differs')
    else:
        require(raw_audio.get('diagnostic_only') is False and
                raw_audio.get('production_delivery_eligible') is True and
                raw_audio.get('official_gates_replaced_or_thresholds_modified') is False and
                raw_audio.get('official_full_gates_are_separate_required_precondition') is True and
                raw_audio.get('private_caches_GT_or_PCM_exported') is False,
                'Source67 diagnostic or incomplete instrument cannot approve production')
        actual = raw_audio.get('fingerprints', {})
        require(all(actual.get(k) == v for k, v in f.items()) and
                actual.get('canonical_video_sha256') == raw_audio['canonical_sha256'] and
                actual.get('actual_full_source_sha256') == raw_audio.get('source_current_sha256') and
                re.fullmatch('[0-9a-f]{64}', actual.get('actual_full_source_sha256', '')) is not None,
                'Source67 exact actual whole-source/raw/AAC fingerprints differ')
    return True
