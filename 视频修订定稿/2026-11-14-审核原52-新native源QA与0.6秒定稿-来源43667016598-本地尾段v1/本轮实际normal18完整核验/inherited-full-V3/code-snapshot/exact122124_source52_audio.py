"""Exact122124 source52 QC report consumer; all numerical/acoustic judgments remain original."""
import json,re
from pathlib import Path
P=json.loads(Path(__file__).with_name('exact122124-source52-instrument-binding.json').read_text())
def require(v,m):
 if not v:raise ValueError(m)
def actual_source52_repair_scope(review,native,raw,article):
 p=P;f=p['fingerprints'];fp=raw.get('fingerprints',{});scope=native.get('approved_audio_repair_scope',{});req=native.get('request_source_sha256',{})
 require(article==native.get('article')==raw.get('article')=='52','Only exact source52 user122124 actual acoustic instrument')
 require(native.get('passed')is True and native.get('canonical_pipeline_passed')is True and native.get('stage')=='final4K-passed','Source52 original complete native gates must really pass first')
 require(raw.get('kind')=='controlled_audio_repair'and raw.get('passed')is True and raw.get('repair_applied')is True and raw.get('diagnostic_only')is False and raw.get('production_delivery_eligible')is True and not raw.get('error')and native.get('approved_audio_qc')==raw,'Actual source52 formal production QC missing, replaced, failed or diagnostic only')
 require(raw.get('official_full_gates_are_separate_required_precondition')is True and raw.get('official_gates_replaced_or_thresholds_modified')is False and raw.get('private_caches_GT_or_PCM_exported')is False,'Original formal gates, thresholds or private-data roles differ')
 require(scope.get('kind')=='controlled_audio_repair'and scope.get('repair_applied')is True and scope.get('actual_original_full_pipeline_passed_first')is True and scope.get('whole_track_actual_audio_and_approved_unchanged_regions_required')is True,'Actual source52 native repair scope required')
 require(review.get('tool')=='audio52-controlled-qc.py'and native.get('approved_audio_qc_program_sha256')==raw.get('program_sha256')==review.get('program_sha256')==p['program_sha256']and scope.get('reference_file_sha256')==raw.get('reference_file_sha256')==review.get('reference_file_sha256')==p['reference_file_sha256'],'Exact enabled actual source52 program/reference differs')
 require(req.get('视频/脚本/52.json')==scope.get('request_source_sha256')==review.get('request_source_sha256')==f['request_source_sha256']and req.get('视频/工具/初稿生成/gen52.py')==f['request_generator_sha256'],'Actual source52 request/GEN differs')
 require(all(fp.get(k)==v for k,v in f.items())and fp.get('canonical_video_sha256')==raw.get('canonical_sha256')==native.get('canonical_video_sha256')and fp.get('actual_full_source_sha256')==raw.get('source_current_sha256')and re.fullmatch('[0-9a-f]{64}',fp.get('actual_full_source_sha256',''))is not None,'Source52 actual full-source/raw/AAC/canonical bindings differ')
 require(native.get('final_wav_sha256')==f['actual_raw_WAV_sha256']and native.get('canonical_aac_adts_sha256')==f['canonical_AAC_ADTS_sha256']and f['canonical_AAC_ADTS_sha256']!=f['accepted_AAC_ADTS_sha256'],'Exact selected newc7f810/13001 controlled voice required; old AAC equality is not claimed')
 before=native.get('approved_audio_qc_comparison_reference',{});legacy=native.get('accepted_source',{})
 require(legacy.get('sha256')==p['native_pipeline_historical_accepted_video_sha256']and legacy.get('aac_adts_sha256')==f['accepted_AAC_ADTS_sha256']and before.get('kind')=='actual-latest-formally-accepted-current-before-resource-only-for-controlled-QC'and before.get('source_native_run')==43533004625 and before.get('sha256')==raw.get('accepted_sha256')==f['accepted_video_sha256']and before.get('AAC_ADTS_sha256')==f['accepted_AAC_ADTS_sha256']and before.get('original_native_pipeline_historical_accepted_source_unchanged')is True and legacy.get('sha256')!=before.get('sha256'),'Keep original native67cbe and controlled-QC current1d0cf6 as distinct actual reference roles with same ecab AAC')
 require(native.get('core_repair_manifest_sha256')==p['core_manifest_sha256'],'Only actual certified17 source52 original producer')
 rows=raw.get('checks',[]);names={x.get('name')for x in rows};require(rows and len(names)==len(rows)and set(p['required_original_check_names'])<=names and all(x.get('passed')is True for x in rows),'Actual source52 original checks missing, duplicated or failed')
 require(raw.get('source_authorization_ids')==p['source_authorization_ids'],'Exact source52 user117-124 authorization identities required')
 s=raw.get('approved_audio_repair_scope',{})
 require(s.get('source_id')=='52'and s.get('spoken_comma_new_mother_sentences')==p['approved_new_mother_sentences']==['S4','S18']and s.get('approved_gain_only_sentences')==p['approved_gain_only_sentences']==['S1','S5']and s.get('only_voice_changed_sentences')==p['approved_voice_changed_sentences']==['S1','S4','S5','S18']and s.get('non_target_title_and_body_pre_master_identity_count')==p['non_target_pre_master_identity_count']==15 and s.get('master_multiplier_before')==p['master_multiplier_before']==s.get('master_multiplier_after')==p['master_multiplier_after']and s.get('ASR_confirmations_not_renewed_by_this_helper')is True and s.get('old_new_whole_duration_AAC_packets_or_new_mother_pitch_not_claimed_equal')is True,'Only measured source52 gains/new-spoken mothers and exact selected NV are permitted')
 require(raw.get('comparison_before_is_formally_accepted_whole')is True and raw.get('accepted_AAC_is_intentionally_different_after_approved_new_mothers')is True,'Actual current1d0cf6 accepted-before and new13001 repair roles must remain explicit')

 return True

def actual_source52_evidence(evidence_hashes):
 required={P['root_pair_selection']['sha256'],P['selected_input_handoff']['sha256'],P['root_formal_QC_adoption']['sha256'],P['root_three_domain_metadata_selection']['sha256'],P['selected_three_domain_pin_H']['sha256']}|{x['sha256']for x in P['actual_evidence'].values()}
 require(required<=evidence_hashes,'Exact52 root19-CF pair, selected input, actual stage0 and selected two-NV physical evidence are required; diagnostics never substitute for actual formal native gates')
 return True
