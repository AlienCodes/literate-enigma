"""Narrow identity evidence for two latest-current native voice references.

This is NOT a quality verdict or an accepted-prior-voice replacement. It does
not execute or waive the original source/audio/ASR/stamp/highlight gates.
The only permitted purpose is a user102 review rebuild of these exact sources.
"""
from pathlib import Path
import copy, hashlib, json, re

PRESENTATION_KEYS={'no','title_zh','title_fx','核对确认','结尾解说','allow_clash',
 '高亮按实际开口','高亮开口门槛','术语','换行变更已获同意','换行变更记录','字号上限',
 '重点词颜色','朗读分块颜色','字距','行距'}

def digest(value):
 return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()

def audio_document(data):
 """Original full bare English, paragraphs/chunks and all nonpresentation data.

Unknown top-level fields are retained, so a newly inserted unreviewed voice
control cannot disappear from the equality check. Typed confirmations are
checked separately rather than renewed by this diagnostic.
 """
 out={k:copy.deepcopy(v) for k,v in data.items() if k not in PRESENTATION_KEYS|{'sentences'}}
 out['sentences']=[{'para':s['para'],'chunks':[re.sub(r'\{\{.*?\}\}|\*\*','',c['en']).strip()for c in s['chunks']]}for s in data['sentences']]
 return out

def validate(profile,source_id,requested,actual,request_sha,gen_sha,wav_sha,current_aac_sha,legacy_aac_sha):
 checks=[]
 def add(name,value):checks.append({'name':name,'passed':bool(value)})
 add('only_exact_review_sources_68_or70',source_id in {'68','70'}and source_id==profile['source_id'])
 add('new_review_only_not_individual_final',profile['authorized_review_feedback']=='102'and profile['individual_final_authorized']is False)
 add('current_reference_not_formally_accepted_whole',profile['formally_accepted_whole']is False and profile['reference_role']=='latest-current-native-reference-not-formally-accepted-whole')
 add('exact_latest_request_source_bytes',request_sha==profile['request_json_sha256'])
 add('exact_latest_request_generator_bytes',gen_sha==profile['request_GEN_sha256'])
 add('requested_complete_voice_document_bound',digest(audio_document(requested))==profile['audio_document_sha256'])
 add('actual_complete_voice_document_same_as_requested',audio_document(actual)==audio_document(requested))
 add('typed_machine_and_other_confirmations_unchanged',actual.get('核对确认')==requested.get('核对确认'))
 add('actual_whole_WAV_exact_to_latest_native_reference',wav_sha==profile['current_native_WAV_sha256'])
 add('actual_whole_AAC_exact_to_latest_native_reference',current_aac_sha==profile['current_native_AAC_adts_sha256'])
 add('actual_legacy_AAC_reference_retained_truthfully',legacy_aac_sha==profile['legacy_accepted_AAC_adts_sha256'])
 add('legacy_current_AAC_difference_explicit_not_relabelled',legacy_aac_sha!=current_aac_sha)
 return {'kind':'source-specific-current-native-voice-identity-binding-only',
  'source_id':source_id,'identity_binding_passed':all(x['passed']for x in checks),
  'checks':checks,'formal_article_acceptance':False,'repair_applied':False,
  'original_full_source_audio_ASR_pronunciation_cut_highlight_stamp_and_media_gates_still_required':True,
  'current_native_reference_is_not_legacy_accepted_audio':True,
  'no_audio_source_confirmations_or_thresholds_modified':True}
