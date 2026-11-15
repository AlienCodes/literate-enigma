"""Original full-source collector, exact book56/source69; new public consent is separate from frozen QA H."""
from pathlib import Path
import tempfile,shutil,json,hashlib,subprocess,sys,os
B=Path(__file__).parent;C=Path('/dev/shm/archive-writer-main061')
H=Path('/workspace/work/review69-finalV3/43724729006-normal18/archive-handoff.json')
HS='d7bdc897ff024d80e69716e58b3c0661a396d39ee0deca788d9008d1eac62b58'
CONSENT=Path('/workspace/work/all-project-deliverables-and-final70-release-authorities-20261115/USER-ALL-PROJECT-GENERATED-DELIVERABLES-GITHUB-ARCHIVE-AUTHORITY.json')
CS='b00a133cc88ed37496e225a181898863ce52e9a774e6b5c2991a310691fd4312'
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert H.stat().st_size==65040 and digest(H)==HS
assert CONSENT.stat().st_size==2088 and digest(CONSENT)==CS
consent=json.loads(CONSENT.read_bytes());assert consent['author']=='user' and consent['kind']=='actual-user-all-project-generated-deliverables-existing-and-future-GitHub-archive-authorization'
assert {'final4K_videos','production_manuscripts_translation_notes_scripts','change_records_and_useful_validation_evidence'} <= set(consent['authorized_project_output_roles'])
assert consent['original9034_eight_article_consent_remains_historical_bytes_unchanged'] is True
h=json.loads(H.read_bytes());a=h['articles'][0]
assert a['source_id']=='69' and a['new_id']=='56'
assert a['final_mp4']['bytes']==16749644 and a['final_mp4']['sha256']=='38b5b9243e3b71cc8ecb72d6367e73e316df96a3a44baa83293e257b63f7b670'
assert os.statvfs('/workspace').f_bavail*os.statvfs('/workspace').f_frsize>=419430400+64*1024*1024, 'Original400 reserve plus writer32 and misc32 required'
R=Path(tempfile.mkdtemp(prefix='book56-source69-full-host-isolated-assets-',dir=str(B)))
W=R/'run43724729006-69-book56-review-normal18-v1';W.mkdir()
P=R/'payload-data';P.mkdir();(W/'payload').symlink_to(P,target_is_directory=True)
for n in ['prepare_new_sourceQA_normal18_assets.py','video_title_authorization.py','archive_batch.py','verify_dual_media_asset_blobs.py','emit_ready_revision_download_manifest.py','cleanup_closed_media_asset_bare.py']:
 shutil.copyfile(B/n,R/n)
IO=Path('/workspace/work/source69-book56-standalone-public-master-collector-IO-CODE-ONLY-20261115')
assert digest(B/'prepare_new_sourceQA_normal18_assets.py')=='1a9b92473c96f3133fc2be0ffae9e7a0a307b079ae0e41ea1f2a3c53ac5ad64e'
assert digest(IO/'prepare_new_sourceQA_normal18_assets.py')=='1277d2920e7a7415707fc1c6d86d150b12e610bc4f6f259539cb9e95fd39f142'
assert digest(IO/'source69_public_master_export.py')=='cdd9bb9cd1d6e32ce59b4bd8b35a13ef9d3d9609077eb0aeb9d91091ed5a0412'
assert digest(IO/'INDEPENDENT-SOLE-WRITER-EXACT69-MASTER-COLLECTOR-IO-ADOPTION.json')=='5b229684153fa84c6075df00883ac6c55d0a526cd84e9ef1c53fef7f71e3162d'
shutil.copyfile(IO/'prepare_new_sourceQA_normal18_assets.py',R/'prepare_new_sourceQA_normal18_assets.py')
shutil.copyfile(IO/'source69_public_master_export.py',R/'source69_public_master_export.py')
rows=[]
def add(p,rel,expected=None):
 p=Path(p);s=digest(p)
 if expected:assert s==expected
 rows.append({'path':str(p),'bytes':p.stat().st_size,'sha256':s,'archive_relative_path':rel})
art=a['section']['illustration']
for name,x in [('actual-approved-prepared4K-69.png',art),('original-approved-book69.png',art['native_source'])]:
 assert Path(x['path']).stat().st_size==x['bytes'] and digest(x['path'])==x['sha256'];add(x['path'],'actual-approved-illustration/'+name,x['sha256'])
add(CONSENT,'separate-new-user-source-publication-consent.json',CS)
add('/workspace/work/book56-source69-final-preparation-after-five-feedback-20261115/USER-BOOK56-SOURCE69-ACTUAL-FINALIZATION-AFTER-FIVE-FEEDBACK-20261115.json','actual-book56-finalization-authority.json','8bdaaa08ced24377833ab3cc22bf551726499d6731e6dd52e68364c82b48df73')
add('/workspace/work/book56-source69-actual43724729006-original-HOST-preparation-20261115/BOOK56-SOURCE69-ACTUAL-NATIVE-SOURCEQA-AND-ORIGINAL-NORMAL18-FINALV3-ROOT-AND-SOLE-WRITER-HANDOFF.json','actual-independent-book56-source-and-finalV3-intake-handoff.json','d0f29ed09eec241b4190bf665dde146a5d768daaeaa1a046367603456b0fde88')
add(B/'book56-source69-full-current-intake-20261115/ACTUAL-SOLE-WRITER-BOOK56-ALL-SPEC-AND-FIVE-CURRENT-FRAME-ADOPTION.json','sole-writer-actual-frozen-H-recursive-spec-intake.json','ab2e79884116deca2868a1de57579e1dd1bda10bb8b1dfb4c7b4957304df0275')
add('/workspace/work/book56-source69-actual43724729006-original-HOST-preparation-20261115/BOOK56-SOURCE69-FINAL-COMPLETE-EXPLICIT-STANDALONE-MASTER-WAV-AND-EVIDENCE-WRITER-HANDOFF.json','actual-explicit-standalone-original-master-WAV-and-role-evidence-handoff.json','24f50ef296e37cdff9bfa465437505bc3a350d3f5cd4e3012739061b2a2b047b')
for label,name in [('new-collector-IO-only-review-handoff.json','SOURCE69-BOOK56-STANDALONE-EXPORTED-MASTER-COLLECTOR-IO-CODE-ONLY-REVIEW-HANDOFF.json'),('independent-master-IO-review-and-adoption.json','INDEPENDENT-SOLE-WRITER-EXACT69-MASTER-COLLECTOR-IO-ADOPTION.json'),('actual-master-positive-and16-negative-cases.json','ACTUAL-SOURCE69-PHYSICAL-MASTER-POSITIVE-SAMEFS-AND16-NEGATIVE-COLLECTOR-IO-TESTS.json'),('collector-IO-only-complete.diff','COMPLETE-ORIGINAL-COLLECTOR-TO-EXACT69-MASTER-IO.diff')]:add(IO/name,'original-master-explicit-IO-contract/'+label)
add('/workspace/work/actual-exported-master-WAV-sourceQA-role-binding-CODE-ONLY-20261115/bind_actual_exported_master.py','original-master-explicit-IO-contract/bind_actual_exported_master.py','ae19dae189e42f1787ef214a26d7baa5f329e21d9eea0f2513f469eb9fb50679')
M=R/'explicit-safe-source69-book56-public-evidence.json'
M.write_text(json.dumps({'kind':'exact-source69-final-H-declared-material-and-actual-all-project-user-publication-consent',
 'source_id':'69','book_order':'56','files':rows,'source_publication_consent_sha256':CS,
 'frozen_quality_H_original_publication_scope_preserved_not_rewritten':True,
 'new_publication_authority_is_actual_b00_user_project_archive_message_not_implied_by_QA':True,
 'all_source_native_normal18_and_failure_history_already_declared_in_frozen_H':True,
 'no_private_RAW_GT_cache_models_tokens_signedURL_ROOTSTATE_PDF_or_other_article_content':True},ensure_ascii=False,indent=2)+'\n')
cmd=[sys.executable,R/'prepare_new_sourceQA_normal18_assets.py','--handoff',H,'--expected-handoff-sha256',HS,
 '--work-dir',W,'--explicit-public-manifest',M,'--explicit-public-manifest-sha256',digest(M)]
p=subprocess.run(list(map(str,cmd)),capture_output=True,text=True,env={**os.environ,'TMPDIR':str(R),'PYTHONDONTWRITEBYTECODE':'1'})
(R/'actual-prepare.log').write_text(p.stdout+p.stderr);assert p.returncode==0,(p.stdout+p.stderr)[-2500:]
m=json.loads((W/'prepared-archive.json').read_bytes());row=m['articles'][0]
assert row['source_id']=='69' and row['new_id']=='56' and row['postprocessing_full_V3_handoff_sha256']==HS
assert row['local_tail_postprocessing_audio_repair_applied'] is False
shutil.copyfile(__file__,P/m['prefix']/'归档程序'/Path(__file__).name)
idx=[{'repo_path':str(p.relative_to(P)),'bytes':p.stat().st_size,'sha256':digest(p)} for p in sorted(P.rglob('*')) if p.is_file()]
(W/'payload-file-index.json').write_text(json.dumps(idx,ensure_ascii=False,indent=2)+'\n')
deny={'b9a257a23820944ee95d568b67d1cd78947b1c1814bb70dc99a45871f488f778','55026ce1b7cdb7e9c1a72da2f715e3d9e6e6f45050a8ddd575dc052b09dca872','bcb37d8930d804988c95da94b9cfeaaab2c7b026df96e6e4567f9b698ce88fbf'}
assert not any(x['sha256'] in deny for x in idx)
loc={'root':str(R),'work_dir':str(W),'source_id':'69','new_id':'56','handoff':str(H),'handoff_sha256':HS,
 'source_publication_consent':str(CONSENT),'source_publication_consent_sha256':CS,
 'files':len(idx),'logical_bytes':sum(x['bytes'] for x in idx),'source_native_audio_repair_applied':row['source_native_audio_repair_applied'],
 'host_hardlinks_and_host_Git_TMPDIR_only':True,'no_remote_write_by_this_local_preparation':True}
(C/'active-source69-book56-full-asset-staging-location.json').write_text(json.dumps(loc,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(loc,ensure_ascii=False),flush=True)
