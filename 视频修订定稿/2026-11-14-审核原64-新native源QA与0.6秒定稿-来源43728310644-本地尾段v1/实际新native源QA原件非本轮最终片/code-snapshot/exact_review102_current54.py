"""Exact user102 current-native identity consumption; never legacy acceptance or repair QC."""
import json
from pathlib import Path
PROFILES=json.loads(Path(__file__).with_name('exact-review102-current54-profile.json').read_text())
def check(review,native,article,actual_aac_sha,evidence_hashes,status_sha,require):
 require(article in PROFILES and native.get('article')==article,'Only exact54 current-native and two existing CF reference')
 p=PROFILES[article];r=p['reference_document'];binding=native.get('approved_current_reference_review_binding',{})
 require(status_sha==p['actual_upstream_native_status_sha256'] and p['reference']['sha256']in evidence_hashes and p['actual_identity_report']['sha256']in evidence_hashes and 'e04a52c1a6e3027d0fd515a017593c31ed60315c4f37281d7e0d2eed4595aed6'in evidence_hashes,'Actual original status/reference/identity/root evidence differs')
 require(review['tool']=='native_official_audio_gates'and review['report_sha256']==status_sha and native.get('passed')is True and native.get('canonical_pipeline_passed')is True and native.get('stage')=='final4K-passed'and native.get('review_only')is True,'All actual original complete gates remain required for review-only')
 require(r['authorized_review_feedback']=='102'and r['individual_final_authorized']is False and r['formally_accepted_whole']is False and r['reference_role']=='latest-current-native-reference-not-formally-accepted-whole','Current reference is not a formally accepted legacy or personal final')
 req=native['request_source_sha256'];require(req.get('视频/脚本/'+article+'.json')==r['request_source_sha256']and req.get('视频/工具/初稿生成/gen'+article+'.py')==r['request_GEN_sha256'],'Exact latest source/GEN differs')
 require(native.get('final_wav_sha256')==r['current_reference_WAV_sha256']and native.get('canonical_aac_adts_sha256')==actual_aac_sha==r['current_reference_AAC_adts_sha256']and native.get('canonical_video_sha256')==p['new_raw_canonical_sha256'],'Actual current wholeWAV/AAC/new canonical differs')
 require(native.get('accepted_prior_aac_identical')is False and native['accepted_source']['sha256']==p['legacy_video_sha256']and native['accepted_source']['aac_adts_sha256']==r['legacy_accepted_AAC_adts_sha256']and actual_aac_sha!=r['legacy_accepted_AAC_adts_sha256'],'Keep current-versus-legacy difference honest')
 require(binding==p['actual_identity_document']and binding['identity_binding_passed']is True and binding['formal_quality_acceptance']is False and binding['repair_applied']is False and binding['program_sha256']=='cf946dd36c42d4fcbe8661869cf2adcb81b1ac302da143e3d9a67f5dbaffce7d'and binding['reference_sha256']==p['reference']['sha256']and binding['original_complete_pipeline_passed_before_identity_binding']is True and binding['no_original_gate_threshold_or_audio_waiver']is True and binding['checks']and all(x['passed']is True for x in binding['checks']),'Actual identity-only verifier failed or relabelled as an acoustic waiver')
 return True
