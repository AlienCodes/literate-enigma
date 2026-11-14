"""Consume source65's actual approved acoustic instrument; no new sound checker.

Only user094 source65/book37 and the frozen real request/GEN/program/reference
are registered. The original native gates and complete new-canonical -> card
-> final AAC payload, codec, side-data and absolute-time checks remain separate.
"""
import json,re
from pathlib import Path

PROFILE=json.loads(Path(__file__).with_name('exact094-source65-instrument-binding.json').read_text())

def require(ok,message):
    if not ok:raise ValueError(message)

def actual_source65_repair_scope(review,native,raw_audio,article):
    p=PROFILE;f=p['fingerprints']
    require(article==native.get('article')==raw_audio.get('article')=='65','User094 source65 instrument belongs to another source')
    require(native.get('passed')is True and native.get('canonical_pipeline_passed')is True and native.get('stage')=='final4K-passed','Source65 supplement requires the actual complete original native quality gates')
    require(raw_audio.get('kind')=='controlled_audio_repair' and raw_audio.get('passed')is True and raw_audio.get('repair_applied')is True and not raw_audio.get('error') and raw_audio.get('diagnostic_only')is False and raw_audio.get('production_delivery_eligible')is True and native.get('approved_audio_qc')==raw_audio,'Source65 actual production acoustic report absent, diagnostic, failed or different')
    require(raw_audio.get('official_full_gates_are_separate_required_precondition')is True and raw_audio.get('official_gates_replaced_or_thresholds_modified')is False and raw_audio.get('private_caches_GT_or_PCM_exported')is False,'Source65 original sound standards or evidence privacy declaration differs')
    scope=native.get('approved_audio_repair_scope',{});request=native.get('request_source_sha256',{})
    require(scope.get('kind')=='controlled_audio_repair'and scope.get('repair_applied')is True and scope.get('actual_original_full_pipeline_passed_first')is True and scope.get('whole_track_actual_audio_and_approved_unchanged_regions_required')is True,'Source65 real native repair scope absent')
    require(request.get('视频/脚本/65.json')==scope.get('request_source_sha256')==review.get('request_source_sha256')==f['request_source_sha256'] and request.get('视频/工具/初稿生成/gen65.py')==f['request_generator_sha256'],'Source65 actual immutable request/GEN differs from user094 frozen source')
    require(review.get('tool')=='audio65-controlled-qc.py'and native.get('approved_audio_qc_program_sha256')==raw_audio.get('program_sha256')==review.get('program_sha256')==p['program_sha256']and scope.get('reference_file_sha256')==raw_audio.get('reference_file_sha256')==review.get('reference_file_sha256')==p['reference_file_sha256'],'Source65 actual acoustic program/reference binding differs')
    fp=raw_audio.get('fingerprints',{})
    require(all(fp.get(k)==v for k,v in f.items())and fp.get('canonical_video_sha256')==raw_audio.get('canonical_sha256')==native.get('canonical_video_sha256')and fp.get('actual_full_source_sha256')==raw_audio.get('source_current_sha256')and re.fullmatch('[0-9a-f]{64}',fp.get('actual_full_source_sha256',''))is not None,'Source65 actual measured source/raw/AAC fingerprint differs')
    require(native.get('final_wav_sha256')==f['actual_raw_WAV_sha256'] and native.get('canonical_aac_adts_sha256')==f['canonical_AAC_ADTS_sha256'], 'Source65 actual new canonical voice differs')
    require(raw_audio.get('comparison_before_role')==p['comparison_before_role'] and raw_audio.get('comparison_before_is_formally_accepted_whole')is False and raw_audio.get('accepted_sha256')==f['accepted_video_sha256'] and p['comparison_before_role']['formally_accepted_whole']is False and p['comparison_before_role']['outer_legacy_AAC_identity_guard_passed']is False, 'Source65 current comparison is not an accepted legacy voice; preserve its truthful role')
    legacy=p['historical_accepted_legacy']
    require(raw_audio.get('historical_accepted_legacy')==legacy and native.get('accepted_source',{}).get('sha256')==legacy['video_sha256'] and native.get('accepted_source',{}).get('aac_adts_sha256')==legacy['AAC_sha256'], 'Source65 immutable legacy history differs; do not overwrite it with the current comparison')
    rows=raw_audio.get('checks',[]);by_name={r.get('name'):r for r in rows}
    require(rows and len(by_name)==len(rows)and set(p['required_original_check_names'])<=set(by_name)and all(r.get('passed')is True for r in rows),'Source65 actual original acoustic checks are incomplete, duplicated or failed')
    measured_scope=raw_audio.get('approved_audio_repair_scope',{})
    require(measured_scope.get('source_control_leaf')==p['source_control_leaf'] and measured_scope.get('target_span_s')==p['target_span_s']and measured_scope.get('unchanged_title_and_other_16_sentences')is True and measured_scope.get('S2_other_two_punctuation_pieces_unchanged')is True and measured_scope.get('ASR_confirmations_not_renewed_by_this_helper')is True,'Source65 measured sole approved gain/unchanged-region scope differs')
    return True
