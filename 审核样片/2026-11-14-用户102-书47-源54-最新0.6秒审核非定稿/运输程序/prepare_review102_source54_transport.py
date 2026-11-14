"""Exact immutable source54 user102 review-only logistics adapter."""
from pathlib import Path
import hashlib,json,shutil,tempfile
OLD=Path('/dev/shm/review102-68-70-isolated-assets-zusxowb6');R=Path(__file__).parent
T=Path(tempfile.mkdtemp(prefix='review102-54-isolated-assets-',dir='/dev/shm'))
names=['archive_batch.py','original-source28-collector-reference.py','verify_review102_dual_asset_blobs.py','cleanup_review102_closed_own_bare.py','transport_exact_review102_assets.py'];original={}
for name in names:
 raw=(OLD/name).read_bytes();original[name]=hashlib.sha256(raw).hexdigest()
 if name in names[2:]:raw=raw.replace(b"('68','70')",b"('54',)")
 (T/name).write_bytes(raw)
s=(OLD/'prepare_review102_exact_assets.py').read_text();start=s.index('CONTRACT=');end=s.index('\nDENY=',start)
contract={'54':{'hsha':'78ab6f9cf5717dc8a3faa3a926b2c08d34ac3c07bef853ecb59ed97ea1d0e338','book':'47','sha':'6223bf386aa819bf66117705fffc9afa07bf83909a8a3dd14758b3be5ba7e19c','bytes':18013554,'kind':'authorized-review102-source54-hold18-local-tail'}}
s=s[:start]+'CONTRACT='+repr(contract)+s[end:];s=s.replace('prepare_review102_source68_source70_transport.py','prepare_review102_source54_transport.py');(T/'prepare_review102_exact_assets.py').write_text(s)
shutil.copyfile(__file__,T/Path(__file__).name)
binding={'kind':'only-frozen-review102-source54-logistics-identity-adapter','contracts':contract,'previous_transport_program_sha256':original,'current_transport_program_sha256':{n:hashlib.sha256((T/n).read_bytes()).hexdigest()for n in names},'previous_collector_sha256':hashlib.sha256((OLD/'prepare_review102_exact_assets.py').read_bytes()).hexdigest(),'current_collector_sha256':hashlib.sha256((T/'prepare_review102_exact_assets.py').read_bytes()).hexdigest(),'only_source_contract_allowlist_and_own_transport_scope_changed':True,'all_review_only_production_false_guards_retained':True,'original_ENOSPC_failure_and_legacy_raw_status_history_not_promoted':True,'source_or_quality_or_H_or_media_or_current_index_alias_or_PDF_changed':False}
(T/'exact-logistics-adapter-binding.json').write_text(json.dumps(binding,ensure_ascii=False,indent=2)+'\n');(R/'review102-source54-staging-location.json').write_text(json.dumps({'root':str(T),'contracts':contract},indent=2)+'\n');print(str(T))
