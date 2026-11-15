"""Freeze only measured source58 native member roles. Does not accept quality."""
from pathlib import Path
import json,hashlib
R=Path(__file__).resolve().parent;C=R/'source-consumer-code'
A=Path('/workspace/work/review58-native/43736478355/58/artifact-files')
def sp(p):
 p=Path(p);return {'path':str(p),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
status=A/'58-status.json';s=json.loads(status.read_text());stdout=Path('/workspace/work/source58-native43736478355-actual-job-stdout.parsed-actual-status-from-stdout.json')
assert sp(status)['sha256']==sp(stdout)['sha256']=='9cf6b05bdfc29c31068806269899a63bc6b785098f5582f0dd2b8b6a72c3a423'
assert s['article']=='58'and s['book_order']==67 and s['passed']is True and s['canonical_pipeline_passed']is True and s['stage']=='final4K-passed'and s['review_only']is False and s['user_individual_finalization_authorized']is True
assert all(k not in s for k in ['core_repair_manifest_sha256','reviewed_gain_preservation_mode','reviewed_existing_ending_preservation_mode','reviewed_existing_physical_cuts_preservation_mode'])
assert s['stock_code_profile']['stock_code_profile_SHA256']=='d53a780360169676d43b739215c1880f0e44b67f8cc07ba61398df3ffed851f2'and s['stock_code_profile']['actual_program_count']==110 and s['stock_code_profile']['stock_mode_environment']=={}and s['stock_code_profile']['core_repairs_applied']is False
assert s['actual_native_stock_code_certification']['certification_SHA256']=='2c8de34d9f1d637ce50d5d2dc767df6321ddd89eee58321ec8da35d738058b85'and s['actual_native_fastcheck_stamp']['sha256']=='a5b7d65975509b54e8380df1e717458d7f95ca121be1530efadf09ab8ce2842f'
assert s['original_maker_unchanged']is True and s['accepted_prior_aac_identical']is True and s['final_wav_sha256']=='3bfba6a7aff011312ee82fca359ec69947aef371a05abc56c42dbf45918bf5d5'
assert s['source58_original_voice_identity']['formal_quality_acceptance']is False and s['source58_original_voice_identity']['identity_binding_passed']is True
req=json.loads((A/'58-request-source.json').read_text());work=json.loads((A/'58-actual-working-source.json').read_text());assert '结尾句'not in req and '结尾句'not in work
coll=json.loads((A/'58-actual-source-collection.json').read_text());assert coll==s['actual_source_collection']and coll['generator_execution_observed']is False
p=json.loads((C/'actual58-bound-source-profile-PENDING.json').read_text());assert p['article']=='58'and p['book_order']=='67'and not p['profile_frozen']
roles={}
for role,v in coll['files'].items():
 hits=list(A.rglob(v['file']));assert len(hits)==1 and sp(hits[0])['sha256']==v['sha256'];roles[role]=sp(hits[0])
assert roles['request_json']['sha256']=='9736d265e3ea9552011b6111935a04bfea5dabbbd323e9ee85cea37380074512'and roles['request_generator']['sha256']=='8a0e9135258837309538c76c328f0f9759712c03c06e7d734de877e18a60c33f'
for row in p['mandatory_evidence']:assert sp(row['path'])==row
p.update(kind='actual-stock58-full110-new-referenceIO-a0c-immutable-ZIP-and-six-source-roles-bound-not-quality-waiver',profile_frozen=True,actual_physical_ZIP_not_downloaded=False,zip=sp(A.parent/'article58-passed-output.zip'),actual_status=sp(status),request_source_sha256=s['request_source_sha256'],observed_source_files=roles)
p['mandatory_evidence']+=[sp(R/'ACTUAL-UNIQUE-WHOLE-SHA-CRC-SAFE-PATH-EXPANDED-BUDGET-INTAKE.json'),sp(R/'actual-fresh-artifact-API.json'),sp(Path(__file__))]
dest=C/'actual58-bound-source-profile.json';assert not dest.exists();dest.write_text(json.dumps(p,ensure_ascii=False,indent=2)+'\n')
o={'kind':'actual58-physical-original-ZIP-and-live-full110-referenceIO-sourceQA-profile-activation','actual_artifact_status':sp(status),'actual_stdout_wholeSHA_equal':sp(stdout),'actual_top_level_book_order':67,'selected_profile':sp(dest),'actual_source_collection_roles':roles,'actual_stock110_d53_cert2c8de_stamp_a5b7_all_bound':True,'CORE_and_KEEP_keys_absent_not_null':True,'ENDING_absent_in_both_request_and_working':True,'actual_identity_only_not_quality_acceptance':True,'actual_native_fullQC_passed_distinct_from_future_HOST_sourceQA':True,'no_sourceQA_H_or_media_generation_or_cloud_write_by_activation':True,'first_readonly_book_order_absence_assumption_rejected_before_any_profile_write':True,'source18_no_book_order_not_reused_as_source58_fact':True}
h=R/'ACTUAL-SOURCE58-PHYSICAL-INTAKE-TO-ORIGINAL-SOURCEQA-PROFILE-ACTIVATION-RECORD.json';h.write_text(json.dumps(o,ensure_ascii=False,indent=2)+'\n');print(json.dumps(sp(h)))
