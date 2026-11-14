"""Exact immutable source18 user102 review-only logistics adapter."""
from pathlib import Path
import hashlib,json,shutil,tempfile
OLD=Path('/dev/shm/review102-54-isolated-assets-tvdqk4qd');R=Path(__file__).parent
T=Path(tempfile.mkdtemp(prefix='review102-18-isolated-assets-',dir='/dev/shm'))
names=['archive_batch.py','original-source28-collector-reference.py','verify_review102_dual_asset_blobs.py','cleanup_review102_closed_own_bare.py','transport_exact_review102_assets.py'];original={}
for name in names:
 raw=(OLD/name).read_bytes();original[name]=hashlib.sha256(raw).hexdigest()
 if name in names[2:]:raw=raw.replace(b"('54',)",b"('18',)")
 (T/name).write_bytes(raw)
s=(OLD/'prepare_review102_exact_assets.py').read_text();start=s.index('CONTRACT=');end=s.index('\nDENY=',start)
contract={'18':{'hsha':'01de649724f17baf7421bd813c04618b25caa4fd27a6dfd587c90c33c2487699','book':'64','sha':'6d244cd7f0ab6dd2b48c0ecfc13c80cc7b2c5d9b902441b57364451c45414992','bytes':16624663,'kind':'authorized-review102-source18-hold18-local-tail'}}
s=s[:start]+'CONTRACT='+repr(contract)+s[end:];s=s.replace('prepare_review102_source54_transport.py','prepare_review102_source18_transport.py');(T/'prepare_review102_exact_assets.py').write_text(s)
shutil.copyfile(__file__,T/Path(__file__).name)
binding={'kind':'only-frozen-review102-source18-logistics-identity-adapter','contracts':contract,'previous_transport_program_sha256':original,'current_transport_program_sha256':{n:hashlib.sha256((T/n).read_bytes()).hexdigest()for n in names},'previous_collector_sha256':hashlib.sha256((OLD/'prepare_review102_exact_assets.py').read_bytes()).hexdigest(),'current_collector_sha256':hashlib.sha256((T/'prepare_review102_exact_assets.py').read_bytes()).hexdigest(),'only_source_contract_allowlist_and_own_transport_scope_changed':True,'all_review_only_production_false_guards_retained':True,'actual_current_new_f3dc_repair_role_kept_without_individual_final_acceptance':True,'source_or_quality_or_H_or_media_or_current_index_alias_or_PDF_changed':False}
(T/'exact-logistics-adapter-binding.json').write_text(json.dumps(binding,ensure_ascii=False,indent=2)+'\n');(R/'review102-source18-staging-location.json').write_text(json.dumps({'root':str(T),'contracts':contract},indent=2)+'\n');print(str(T))
