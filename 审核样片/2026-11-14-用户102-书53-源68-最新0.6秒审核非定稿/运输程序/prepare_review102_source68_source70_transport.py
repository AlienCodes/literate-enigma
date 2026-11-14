"""Exact immutable review102 logistics adapter; no media/QA or final install."""
from pathlib import Path
import hashlib,json,shutil,tempfile

OLD=Path('/dev/shm/review102-66-69-isolated-assets-79x3nkjw')
R=Path(__file__).parent
T=Path(tempfile.mkdtemp(prefix='review102-68-70-isolated-assets-',dir='/dev/shm'))
names=['archive_batch.py','original-source28-collector-reference.py','verify_review102_dual_asset_blobs.py','cleanup_review102_closed_own_bare.py','transport_exact_review102_assets.py']
original={}
for name in names:
 raw=(OLD/name).read_bytes();original[name]=hashlib.sha256(raw).hexdigest()
 if name in names[2:]:raw=raw.replace(b"('66','69')",b"('68','70')")
 (T/name).write_bytes(raw)
s=(OLD/'prepare_review102_exact_assets.py').read_text()
start=s.index('CONTRACT={');end=s.index('\nDENY=',start)
contract={
 '68':{'hsha':'293940f1a4d39fda9601bb9aa1d1cd522239ae09d3673a95b36c8cc40f3da119','book':'53','sha':'df900c7b5ef1f68dd24b4701a2e3cf655430b42497711b3ebdc0b5569c9926ed','bytes':16000776,'kind':'authorized-review102-source68-hold18-local-tail'},
 '70':{'hsha':'60f64f47e55ebd544c4bbd1f191583868c4a7a12780c84dcb20abf711221f885','book':'50','sha':'a702d771215142c071cad12fb52d26eea558357d8036758b0c568bd892fd270c','bytes':14903195,'kind':'authorized-review102-source70-hold18-local-tail'}}
s=s[:start]+'CONTRACT='+repr(contract)+s[end:]
s=s.replace("for helper in ('verify_review102_dual_asset_blobs.py','cleanup_review102_closed_own_bare.py','transport_exact_review102_assets.py'):","for helper in ('verify_review102_dual_asset_blobs.py','cleanup_review102_closed_own_bare.py','transport_exact_review102_assets.py','exact-logistics-adapter-binding.json','prepare_review102_source68_source70_transport.py'):")
(T/'prepare_review102_exact_assets.py').write_text(s)
shutil.copyfile(__file__,T/Path(__file__).name)
binding={'kind':'only-two-frozen-review102-source68-source70-logistics-identity-adapter','contracts':contract,'previous_transport_program_sha256':original,'current_transport_program_sha256':{n:hashlib.sha256((T/n).read_bytes()).hexdigest()for n in names},'previous_collector_sha256':hashlib.sha256((OLD/'prepare_review102_exact_assets.py').read_bytes()).hexdigest(),'current_collector_sha256':hashlib.sha256((T/'prepare_review102_exact_assets.py').read_bytes()).hexdigest(),'only_source_contract_allowlist_and_own_transport_scope_changed':True,'all_review_only_production_false_guards_retained':True,'source_or_quality_or_H_or_media_or_current_index_alias_or_PDF_changed':False}
(T/'exact-logistics-adapter-binding.json').write_text(json.dumps(binding,ensure_ascii=False,indent=2)+'\n')
(R/'review102-source68-source70-staging-location.json').write_text(json.dumps({'root':str(T),'contracts':contract},indent=2)+'\n')
print(str(T))
