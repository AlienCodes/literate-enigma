"""Identity-only proposal for source54; does not execute or waive any QA gate."""
import copy,hashlib,json
from pathlib import Path

def validate(profile,requested,actual,request_sha,gen_sha,wav_sha,aac_sha,legacy_aac_sha,comparison_sha):
 checks=[]
 def add(name,result):checks.append({'name':name,'passed':bool(result)})
 add('only54_review102_not_individual_final',profile['source_id']=='54'and profile['authorized_review_feedback']=='102'and profile['individual_final_authorized']is False)
 add('current_reference_not_old_formal_acceptance',profile['formally_accepted_whole']is False and profile['reference_role']=='latest-current-native-reference-not-formally-accepted-whole')
 add('exact_original_latest_request_source_and_generator',request_sha==profile['request_source_sha256']and gen_sha==profile['request_GEN_sha256'])
 expected=copy.deepcopy(requested)
 for case in profile['exact_two_existing_confirmation_fingerprint_changes']:
  key=case['exact_review_path'][2]
  add('existing_entry_verbatim_'+key,requested.get('核对确认',{}).get('响度骤降',{}).get(key)==case['existing_entry_verbatim'])
  expected['核对确认']['响度骤降'][key]=copy.deepcopy(case['proposed_entry'])
 # The original G35 observed last-note fold is the only mechanical source variation.
 if actual.get('sentences')and actual['sentences'][-1]['chunks'][-1].get('note')==profile['actual_observed_original_G35_last_note']:
  expected['sentences'][-1]['chunks'][-1]['note']=profile['actual_observed_original_G35_last_note']
 add('actual_fullsource_only_exact2_CF_fingerprints_and_knownG35',actual==expected)
 add('actual_whole_WAV_exact_current_reference',wav_sha==profile['current_reference_WAV_sha256'])
 add('actual_whole_AAC_exact_current_reference',aac_sha==profile['current_reference_AAC_adts_sha256'])
 add('historical_legacy_AAC_unchanged_and_distinct',legacy_aac_sha==profile['legacy_accepted_AAC_adts_sha256']and legacy_aac_sha!=aac_sha)
 add('wholeS11_S13_and_actual_global_context_report_exact',comparison_sha==profile['actual_public_wholeS11_S13_and_comparison_context']['sha256'])
 return {'kind':'source54-specific-current-reference-and-two-existing-CF-identity-only','identity_binding_passed':all(x['passed']for x in checks),'checks':checks,'formal_quality_acceptance':False,'repair_applied':False,'old_original_failure_preserved':True,'no_original_gate_threshold_or_audio_waiver':True,'all_original_native_gates_ASR_and_final_media_V3_still_required':True}
