"""Exact116 source43 QC report consumer; all numerical/acoustic judgments remain original."""
import json,re
from pathlib import Path
P=json.loads(Path(__file__).with_name('exact116-source43-instrument-binding.json').read_text())
def require(v,m):
 if not v:raise ValueError(m)
def actual_source43_repair_scope(review,native,raw,article):
 p=P;f=p['fingerprints'];fp=raw.get('fingerprints',{});scope=native.get('approved_audio_repair_scope',{});req=native.get('request_source_sha256',{})
 require(article==native.get('article')==raw.get('article')=='43','Only exact source43 user116 actual acoustic instrument')
 require(native.get('passed')is True and native.get('canonical_pipeline_passed')is True and native.get('stage')=='final4K-passed','Source43 original complete native gates must really pass first')
 require(raw.get('kind')=='controlled_audio_repair'and raw.get('passed')is True and raw.get('repair_applied')is True and raw.get('diagnostic_only')is False and raw.get('production_delivery_eligible')is True and not raw.get('error')and native.get('approved_audio_qc')==raw,'Actual source43 formal production QC missing, replaced, failed or diagnostic only')
 require(raw.get('official_full_gates_are_separate_required_precondition')is True and raw.get('official_gates_replaced_or_thresholds_modified')is False and raw.get('private_caches_GT_or_PCM_exported')is False,'Original formal gates, thresholds or private-data roles differ')
 require(scope.get('kind')=='controlled_audio_repair'and scope.get('repair_applied')is True and scope.get('actual_original_full_pipeline_passed_first')is True and scope.get('whole_track_actual_audio_and_approved_unchanged_regions_required')is True,'Actual source43 native repair scope required')
 require(review.get('tool')=='audio43-controlled-qc.py'and native.get('approved_audio_qc_program_sha256')==raw.get('program_sha256')==review.get('program_sha256')==p['program_sha256']and scope.get('reference_file_sha256')==raw.get('reference_file_sha256')==review.get('reference_file_sha256')==p['reference_file_sha256'],'Exact enabled actual source43 program/reference differs')
 require(req.get('视频/脚本/43.json')==scope.get('request_source_sha256')==review.get('request_source_sha256')==f['request_source_sha256']and req.get('视频/工具/初稿生成/gen43.py')==f['request_generator_sha256'],'Actual source43 request/GEN differs')
 require(all(fp.get(k)==v for k,v in f.items())and fp.get('canonical_video_sha256')==raw.get('canonical_sha256')==native.get('canonical_video_sha256')and fp.get('actual_full_source_sha256')==raw.get('source_current_sha256')and re.fullmatch('[0-9a-f]{64}',fp.get('actual_full_source_sha256',''))is not None,'Source43 actual full-source/raw/AAC/canonical bindings differ')
 require(native.get('final_wav_sha256')==f['actual_raw_WAV_sha256']and native.get('canonical_aac_adts_sha256')==f['canonical_AAC_ADTS_sha256']and f['canonical_AAC_ADTS_sha256']!=f['accepted_AAC_ADTS_sha256'],'Exact new552e/8ad controlled voice required; old AAC equality is not claimed')
 before=native.get('approved_audio_qc_comparison_reference',{});legacy=native.get('accepted_source',{})
 require(legacy.get('sha256')==p['native_pipeline_historical_accepted_video_sha256']and legacy.get('aac_adts_sha256')==f['accepted_AAC_ADTS_sha256']and before.get('kind')=='actual-latest-formally-accepted-current-before-resource-only-for-controlled-QC'and before.get('source_native_run')==43533004625 and before.get('sha256')==raw.get('accepted_sha256')==f['accepted_video_sha256']and before.get('AAC_ADTS_sha256')==f['accepted_AAC_ADTS_sha256']and before.get('original_native_pipeline_historical_accepted_source_unchanged')is True and legacy.get('sha256')!=before.get('sha256'),'Keep original native1812 and controlled-QC current8a47 as distinct actual reference roles with same e68a AAC')
 require(native.get('core_repair_manifest_sha256')==p['core_manifest_sha256'],'Only actual certified17 source43 original producer')
 rows=raw.get('checks',[]);names={x.get('name')for x in rows};require(rows and len(names)==len(rows)and set(p['required_original_check_names'])<=names and all(x.get('passed')is True for x in rows),'Actual source43 original checks missing, duplicated or failed')
 require(raw.get('source_authorization_ids')==p['source_authorization_ids'],'Exact source43 original user113/115/116 authorization identities required')
 s=raw.get('approved_audio_repair_scope',{})
 require(s.get('source_id')=='43'and s.get('spoken_comma_new_mother_sentences')==p['approved_new_mother_sentences']==['S16']and s.get('approved_gain_only_sentences')==p['approved_gain_only_sentences']==['S13']and s.get('only_voice_changed_sentences')==p['approved_voice_changed_sentences']==['S13','S16']and s.get('non_target_title_and_body_pre_master_identity_count')==p['stage1_non_target_count']==p['non_target_pre_master_identity_count']==20 and s.get('master_multiplier_before')==p['master_multiplier_before']==s.get('master_multiplier_after')==p['master_multiplier_after']and s.get('ASR_confirmations_not_renewed_by_this_helper')is True and s.get('old_new_whole_duration_AAC_packets_or_new_mother_pitch_not_claimed_equal')is True and s.get('selected_new_mother_NV')==p['selected_new_mother_NV']and s.get('actual_stage1_diagnostic_run')==p['stage1_run']==43643745207 and s.get('actual_single_final_candidate_diagnostic_run')==p['stage2_run']==43655794845,'Only actual two-stage S13 gain, S16 spoken mother and selected post-d NV scope may be accepted')
 require(raw.get('comparison_before_is_formally_accepted_whole')is True and raw.get('accepted_AAC_is_intentionally_different_after_approved_new_mothers')is True,'Actual current8a47 accepted-before role and new8ad repair must remain explicit')

 return True

def actual_source43_evidence(evidence_hashes):
 require({P[k]['sha256']for k in ['root_authority','source_freeze','stage1_diagnostic_evidence','stage2_diagnostic_evidence','metadata_authority','metadata_pair_selection','metadata_input_handoff']}<=evidence_hashes,'Actual root43 and exact source freeze plus both real diagnostic stages must be retained; neither substitutes for formal native gates')
 return True
