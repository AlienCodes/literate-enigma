"""Original full-source collector, exact book64/source18; new public consent is separate from frozen QA H."""
from pathlib import Path
import tempfile,shutil,json,hashlib,subprocess,sys,os
B=Path(__file__).parent;C=Path('/dev/shm/archive-writer-main061')
H=Path('/workspace/work/review70-finalV3/43731802299-normal18/archive-handoff.json')
HS='1146e58a20d50f0496291064fbe0574fada14a7e52e774adb264d7a0879a9996'
CONSENT=Path('/workspace/work/all-project-deliverables-and-final70-release-authorities-20261115/USER-ALL-PROJECT-GENERATED-DELIVERABLES-GITHUB-ARCHIVE-AUTHORITY.json')
CS='b00a133cc88ed37496e225a181898863ce52e9a774e6b5c2991a310691fd4312'
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert H.stat().st_size==75173 and digest(H)==HS
assert CONSENT.stat().st_size==2088 and digest(CONSENT)==CS
consent=json.loads(CONSENT.read_bytes());assert consent['author']=='user' and consent['kind']=='actual-user-all-project-generated-deliverables-existing-and-future-GitHub-archive-authorization'
assert {'final4K_videos','production_manuscripts_translation_notes_scripts','change_records_and_useful_validation_evidence'} <= set(consent['authorized_project_output_roles'])
assert consent['original9034_eight_article_consent_remains_historical_bytes_unchanged'] is True
h=json.loads(H.read_bytes());a=h['articles'][0]
assert a['source_id']=='18' and a['new_id']=='64'
assert a['final_mp4']['bytes']==16309163 and a['final_mp4']['sha256']=='b30f64bdddac235acb6676ee118a0f55e99678a100190d08f7e48a4d2e1a2e34'
assert os.statvfs('/workspace').f_bavail*os.statvfs('/workspace').f_frsize>=419430400+64*1024*1024, 'Original400 reserve plus writer32 and misc32 required'
R=Path(tempfile.mkdtemp(prefix='book64-source18-full-host-isolated-assets-',dir=str(B)))
W=R/'run43731802299-18-book64-review-normal18-v1';W.mkdir()
P=R/'payload-data';P.mkdir();(W/'payload').symlink_to(P,target_is_directory=True)
for n in ['prepare_new_sourceQA_normal18_assets.py','video_title_authorization.py','archive_batch.py','verify_dual_media_asset_blobs.py','emit_ready_revision_download_manifest.py','cleanup_closed_media_asset_bare.py']:
 shutil.copyfile(B/n,R/n)
IO=Path('/workspace/work/source18-book64-standalone-public-master-collector-IO-CODE-ONLY-20261115')
assert digest(B/'prepare_new_sourceQA_normal18_assets.py')=='1a9b92473c96f3133fc2be0ffae9e7a0a307b079ae0e41ea1f2a3c53ac5ad64e'
assert digest(IO/'prepare_new_sourceQA_normal18_assets.py')=='c97f426d16175ad3535477a9b41344c8a0735cd95f702b64d3bebba1ab1ce59d'
assert digest(IO/'source18_public_master_export.py')=='0d4892f2115a51af131546982c6cd61a062e7a252b9725297b17795790d1043c'
assert digest(IO/'INDEPENDENT-SOLE-WRITER-EXACT18-MASTER-COLLECTOR-IO-ADOPTION.json')=='7a2cdc67aff7afdba15cc4ed5fc2abf0459d21f7ed7623a9d3d22ecd9bfcc823'
shutil.copyfile(IO/'prepare_new_sourceQA_normal18_assets.py',R/'prepare_new_sourceQA_normal18_assets.py')
shutil.copyfile(IO/'source18_public_master_export.py',R/'source18_public_master_export.py')
rows=[]
def add(p,rel,expected=None):
 p=Path(p);s=digest(p)
 if expected:assert s==expected
 rows.append({'path':str(p),'bytes':p.stat().st_size,'sha256':s,'archive_relative_path':rel})
art=a['section']['illustration']
for name,x in [('actual-approved-prepared4K-18.png',art),('original-approved-book18.png',art['native_source'])]:
 assert Path(x['path']).stat().st_size==x['bytes'] and digest(x['path'])==x['sha256'];add(x['path'],'actual-approved-illustration/'+name,x['sha256'])
add(CONSENT,'separate-new-user-source-publication-consent.json',CS)
add('/workspace/work/book64-source18-enlisted-collecting-20261115/USER-BOOK64-SOURCE18-TWO-KEYWORDS-FINALIZATION-20261115.json','actual-book64-finalization-authority.json','11b2c8f5b9393b58b95f3bbcef2cfb952fb56fab9ce27fd6af26e61d8ecbd85e')
add('/workspace/work/book64-source18-actual43731802299-original-HOST-preparation-20261115/BOOK64-SOURCE18-ACTUAL-NATIVE-SOURCEQA-AND-ORIGINAL-NORMAL18-FINALV3-ROOT-AND-SOLE-WRITER-HANDOFF.json','actual-independent-book64-source-and-finalV3-intake-handoff.json','273ee249e496f8f82662ffcd6d25db64d35a3ee0d364da757743d6969b7259c4')
add(B/'book64-source18-full-current-intake-20261115/ACTUAL-SOLE-WRITER-BOOK64-ALL-SPEC-AND-FIVE-CURRENT-FRAME-ADOPTION.json','sole-writer-actual-frozen-H-recursive-spec-intake.json','7a56e8a2a07bbfc37649c849cad96a6e4fec1824a27e98c1adeab99b764a9de1')
add('/workspace/work/book64-source18-actual43731802299-original-HOST-preparation-20261115/BOOK64-SOURCE18-FINAL-COMPLETE-EXPLICIT-STANDALONE-MASTER-WAV-AND-EVIDENCE-WRITER-HANDOFF.json','actual-explicit-standalone-original-master-WAV-and-role-evidence-handoff.json','1749def2b6ab466859c195c514f7e0ceb8663cee2775df242d095f3a5523b250')
for label,name in [('new-collector-IO-only-review-handoff.json','SOURCE18-BOOK64-STANDALONE-EXPORTED-MASTER-COLLECTOR-IO-CODE-ONLY-REVIEW-HANDOFF.json'),('independent-master-IO-review-and-adoption.json','INDEPENDENT-SOLE-WRITER-EXACT18-MASTER-COLLECTOR-IO-ADOPTION.json'),('actual-master-positive-and16-negative-cases.json','ACTUAL-SOURCE18-PHYSICAL-MASTER-POSITIVE-SAMEFS-AND16-NEGATIVE-COLLECTOR-IO-TESTS.json'),('collector-IO-only-complete.diff','COMPLETE-ORIGINAL-COLLECTOR-TO-EXACT18-MASTER-IO.diff')]:add(IO/name,'original-master-explicit-IO-contract/'+label)
add('/workspace/work/book64-source18-actual43731802299-original-HOST-preparation-20261115/bind_actual_exported_master_exact18.py','original-master-explicit-IO-contract/bind_actual_exported_master.py','dcbca51d9ad19f8f84dd3099c5cba7fbb6f328c317a052e70bb7cc98785dfbdd')
M=R/'explicit-safe-source18-book64-public-evidence.json'
M.write_text(json.dumps({'kind':'exact-source18-final-H-declared-material-and-actual-all-project-user-publication-consent',
 'source_id':'70','book_order':'50','files':rows,'source_publication_consent_sha256':CS,
 'frozen_quality_H_original_publication_scope_preserved_not_rewritten':True,
 'new_publication_authority_is_actual_b00_user_project_archive_message_not_implied_by_QA':True,
 'all_source_native_normal18_and_failure_history_already_declared_in_frozen_H':True,
 'no_private_RAW_GT_cache_models_tokens_signedURL_ROOTSTATE_PDF_or_other_article_content':True},ensure_ascii=False,indent=2)+'\n')
cmd=[sys.executable,R/'prepare_new_sourceQA_normal18_assets.py','--handoff',H,'--expected-handoff-sha256',HS,
 '--work-dir',W,'--explicit-public-manifest',M,'--explicit-public-manifest-sha256',digest(M)]
p=subprocess.run(list(map(str,cmd)),capture_output=True,text=True,env={**os.environ,'TMPDIR':str(R),'PYTHONDONTWRITEBYTECODE':'1'})
(R/'actual-prepare.log').write_text(p.stdout+p.stderr);assert p.returncode==0,(p.stdout+p.stderr)[-2500:]
m=json.loads((W/'prepared-archive.json').read_bytes());row=m['articles'][0]
assert row['source_id']=='18' and row['new_id']=='64' and row['postprocessing_full_V3_handoff_sha256']==HS
assert row['local_tail_postprocessing_audio_repair_applied'] is False
shutil.copyfile(__file__,P/m['prefix']/'归档程序'/Path(__file__).name)
idx=[{'repo_path':str(p.relative_to(P)),'bytes':p.stat().st_size,'sha256':digest(p)} for p in sorted(P.rglob('*')) if p.is_file()]
(W/'payload-file-index.json').write_text(json.dumps(idx,ensure_ascii=False,indent=2)+'\n')
deny={'b9a257a23820944ee95d568b67d1cd78947b1c1814bb70dc99a45871f488f778','55026ce1b7cdb7e9c1a72da2f715e3d9e6e6f45050a8ddd575dc052b09dca872','bcb37d8930d804988c95da94b9cfeaaab2c7b026df96e6e4567f9b698ce88fbf'}
assert not any(x['sha256'] in deny for x in idx)
loc={'root':str(R),'work_dir':str(W),'source_id':'70','new_id':'50','handoff':str(H),'handoff_sha256':HS,
 'source_publication_consent':str(CONSENT),'source_publication_consent_sha256':CS,
 'files':len(idx),'logical_bytes':sum(x['bytes'] for x in idx),'source_native_audio_repair_applied':row['source_native_audio_repair_applied'],
 'host_hardlinks_and_host_Git_TMPDIR_only':True,'no_remote_write_by_this_local_preparation':True}
(C/'active-source18-book64-full-asset-staging-location.json').write_text(json.dumps(loc,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(loc,ensure_ascii=False),flush=True)
