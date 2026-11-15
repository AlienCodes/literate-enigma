"""Exact128 source48 QC report consumer; all numerical/acoustic judgments remain original."""
import json,re
from pathlib import Path
P=json.loads(Path(__file__).with_name('exact128-source48-instrument-binding.json').read_text())
def require(v,m):
 if not v:raise ValueError(m)
def actual_source48_repair_scope(review,native,raw,article):
 p=P;require(p['frozen_after_actual_native_results']is True and isinstance(p['fresh_native_binding'],dict),'Source48 current513d consumer is inactive until a genuine fresh native success is frozen')
 f=p['fingerprints'];fp=raw.get('fingerprints',{});scope=native.get('approved_audio_repair_scope',{});req=native.get('request_source_sha256',{});fresh=p['fresh_native_binding']
 require(native.get('review_only',False)is False and native.get('preview_only',False)is False and native.get('original_audit_and_quality_thresholds_unchanged')is True,'Review-only, preview or changed native thresholds cannot become source48 final')
 require(native.get('accepted_prior_aac_identical')is False and raw.get('source_authorization_ids')==p['source_authorization_ids'],'Do not invent prior legacy AAC identity or replace the user125-128 source authority')
 require(fresh['raw_canonical_video_sha256']==native.get('canonical_video_sha256') and fresh['actual_full_source_sha256']==fp.get('actual_full_source_sha256'),'Only the actually observed fresh source48 canonical and working source may bind')
 require(article==native.get('article')==raw.get('article')=='48','Only exact source48 user128 actual acoustic instrument')
 require(native.get('passed')is True and native.get('canonical_pipeline_passed')is True and native.get('stage')=='final4K-passed','Source48 original complete native gates must really pass first')
 require(raw.get('kind')=='controlled_audio_repair'and raw.get('passed')is True and raw.get('repair_applied')is True and raw.get('diagnostic_only')is False and raw.get('production_delivery_eligible')is True and not raw.get('error')and native.get('approved_audio_qc')==raw,'Actual source48 formal production QC missing, replaced, failed or diagnostic only')
 require(raw.get('official_full_gates_are_separate_required_precondition')is True and raw.get('official_gates_replaced_or_thresholds_modified')is False and raw.get('private_caches_GT_or_PCM_exported')is False,'Original formal gates, thresholds or private-data roles differ')
 require(scope.get('kind')=='controlled_audio_repair'and scope.get('repair_applied')is True and scope.get('actual_original_full_pipeline_passed_first')is True and scope.get('whole_track_actual_audio_and_approved_unchanged_regions_required')is True,'Actual source48 native repair scope required')
 require(review.get('tool')=='audio48-controlled-qc.py'and native.get('approved_audio_qc_program_sha256')==raw.get('program_sha256')==review.get('program_sha256')==p['program_sha256']and scope.get('reference_file_sha256')==raw.get('reference_file_sha256')==review.get('reference_file_sha256')==p['reference_file_sha256'],'Exact enabled actual source48 program/reference differs')
 require(req.get('视频/脚本/48.json')==scope.get('request_source_sha256')==review.get('request_source_sha256')==f['request_source_sha256']and req.get('视频/工具/初稿生成/gen48.py')==f['request_generator_sha256'],'Actual source48 request/GEN differs')
 require(all(fp.get(k)==v for k,v in f.items())and fp.get('canonical_video_sha256')==raw.get('canonical_sha256')==native.get('canonical_video_sha256')and fp.get('actual_full_source_sha256')==raw.get('source_current_sha256')and re.fullmatch('[0-9a-f]{64}',fp.get('actual_full_source_sha256',''))is not None,'Source48 actual full-source/raw/AAC/canonical bindings differ')
 require(native.get('final_wav_sha256')==f['actual_raw_WAV_sha256']and native.get('canonical_aac_adts_sha256')==f['canonical_AAC_ADTS_sha256']and native.get('accepted_source',{}).get('sha256')==raw.get('accepted_sha256')==f['accepted_video_sha256']and native.get('accepted_source',{}).get('aac_adts_sha256')==f['accepted_AAC_ADTS_sha256']and f['canonical_AAC_ADTS_sha256']!=f['accepted_AAC_ADTS_sha256'],'Keep new repaired voice distinct from exact legacy accepted reference')
 require(native.get('core_repair_manifest_sha256')==p['core_manifest_sha256'],'Only original fivecore source48 approved producer')
 rows=raw.get('checks',[]);names={x.get('name')for x in rows};require(rows and len(names)==len(rows)and set(p['required_original_check_names'])<=names and all(x.get('passed')is True for x in rows),'Actual source48 original checks missing, duplicated or failed')
 s=raw.get('approved_audio_repair_scope',{});require(s.get('source_id')=='48'and s.get('approved_new_S15_mother_sentences')==p['approved_new_mother_sentences']==['S15']and s.get('approved_gain_only_sentences')==p['approved_gain_only_sentences']==[]and s.get('only_voice_changed_sentences')==p['approved_voice_changed_sentences']==['S9','S10','S12','S13','S15']and s.get('non_target_title_and_body_pre_master_identity_count')==p['non_target_pre_master_identity_count']==14 and s.get('master_multiplier_before')==p['master_multiplier_before']==s.get('master_multiplier_after')==p['master_multiplier_after']and s.get('ASR_confirmations_not_renewed_by_this_helper')is True and s.get('old_new_whole_duration_AAC_packets_or_new_mother_pitch_not_claimed_equal')is True,'Only current513d four exact physical protections plus prior proper295 correct-context S15 new mothers; title+13 proper295 identity and original normalization stay distinct')
 require(raw.get('comparison_before_is_formally_accepted_whole')is False and raw.get('comparison_before_role')=='current513d scalar proof and proper295 physical-reference chain; older4f remains diagnostic, not formalaccepted legacy'and raw.get('legacy_accepted_source_role')=='exact wrapper accepted-videos48 input and measured whole-level reference only'and raw.get('legacy_accepted_file_not_falsely_used_for_16sentence_premaster_identity')is True and raw.get('accepted_AAC_is_intentionally_different_after_approved_new_mothers')is True,'Current4f diagnostic and legacyf7d reference roles must not be merged')
 return True

def actual_source48_evidence(evidence_hashes):
 require(P['frozen_after_actual_native_results']is True and isinstance(P['fresh_native_binding'],dict),'Source48 pending native cannot become frozen source/final quality evidence')
 require({P[k]['sha256']for k in P['required_evidence_keys']}<=evidence_hashes,'Exact current57/proper295/legacy/root128/English/specific-boundary authority chain required')
 f=P['fresh_native_binding']
 require({f['actual_native_status_sha256'],f['actual_QC_report_sha256'],f['actual_native_layout_sha256']}<=evidence_hashes and f['actual_native_layout_sha256']==P['expected_layout_sha256'],'Only the actual observed fresh native status/QC/layout can activate current513d')
 return True

def actual_source48_packet_identity(actual_chain):
 require(P['frozen_after_actual_native_results']is True and isinstance(P['fresh_native_binding'],dict),'Source48 current packet identity cannot be inferred before actual native success')
 require(actual_chain['aac_adts_sha256']==P['fingerprints']['canonical_AAC_ADTS_sha256'] and actual_chain['packet_count']==P['expected_current_AAC_packet_count']==7085 and actual_chain['packet_projection_sha256']==P['fresh_native_binding']['actual_canonical_AAC_packet_projection_sha256'],'Exact new current513d entire AAC payload/count/absolute packet projection differs')
 return True
