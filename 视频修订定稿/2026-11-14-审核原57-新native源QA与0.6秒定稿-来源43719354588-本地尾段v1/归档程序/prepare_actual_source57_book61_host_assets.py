"""Original full-source collector, exact book61/source57; new public consent is separate from frozen QA H."""
from pathlib import Path
import tempfile,shutil,json,hashlib,subprocess,sys,os
B=Path(__file__).parent;C=Path('/dev/shm/archive-writer-main061')
H=Path('/workspace/work/review57-finalV3/43719354588-normal18/archive-handoff.json')
HS='52ece356690469b7c40738c16eca26946e458ddc3aa71ff208377131fd742ec8'
CONSENT=Path('/workspace/work/all-project-deliverables-and-final70-release-authorities-20261115/USER-ALL-PROJECT-GENERATED-DELIVERABLES-GITHUB-ARCHIVE-AUTHORITY.json')
CS='b00a133cc88ed37496e225a181898863ce52e9a774e6b5c2991a310691fd4312'
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert H.stat().st_size==59261 and digest(H)==HS
assert CONSENT.stat().st_size==2088 and digest(CONSENT)==CS
consent=json.loads(CONSENT.read_bytes());assert consent['author']=='user' and consent['kind']=='actual-user-all-project-generated-deliverables-existing-and-future-GitHub-archive-authorization'
assert {'final4K_videos','production_manuscripts_translation_notes_scripts','change_records_and_useful_validation_evidence'} <= set(consent['authorized_project_output_roles'])
assert consent['original9034_eight_article_consent_remains_historical_bytes_unchanged'] is True
h=json.loads(H.read_bytes());a=h['articles'][0]
assert a['source_id']=='57' and a['new_id']=='61'
assert a['final_mp4']['bytes']==16462436 and a['final_mp4']['sha256']=='f18ae9c03d163e83b929dbdb113786f9bc9e048bb5d2e17783cdd9b4cefd559e'
R=Path(tempfile.mkdtemp(prefix='book61-source57-full-host-isolated-assets-',dir=str(B)))
W=R/'run43719354588-57-book61-review-normal18-v1';W.mkdir()
P=R/'payload-data';P.mkdir();(W/'payload').symlink_to(P,target_is_directory=True)
for n in ['prepare_new_sourceQA_normal18_assets.py','video_title_authorization.py','archive_batch.py','verify_dual_media_asset_blobs.py','emit_ready_revision_download_manifest.py','cleanup_closed_media_asset_bare.py']:
 shutil.copyfile(B/n,R/n)
rows=[]
def add(p,rel,expected=None):
 p=Path(p);s=digest(p)
 if expected:assert s==expected
 rows.append({'path':str(p),'bytes':p.stat().st_size,'sha256':s,'archive_relative_path':rel})
art=a['section']['illustration']
for name,x in [('actual-approved-prepared4K-57.png',art),('original-approved-book57.png',art['native_source'])]:
 assert Path(x['path']).stat().st_size==x['bytes'] and digest(x['path'])==x['sha256'];add(x['path'],'actual-approved-illustration/'+name,x['sha256'])
add(CONSENT,'separate-new-user-source-publication-consent.json',CS)
add('/workspace/work/book61-source57-final-preparation-after-three-feedback-20261115/USER-BOOK61-SOURCE57-FINALIZATION-AFTER-THREE-FEEDBACK-20261115.json','actual-book61-finalization-authority.json','ea0e487911876f994c4584206f753fb3942fcd70b5a0ab6382440e18f5066d54')
add('/workspace/work/book61-source57-actual43719354588-original-HOST-preparation-20261115/BOOK61-SOURCE57-ACTUAL-NATIVE-SOURCEQA-AND-ORIGINAL-NORMAL18-FINALV3-ROOT-AND-SOLE-WRITER-HANDOFF.json','actual-independent-book61-source-and-finalV3-intake-handoff.json','4046f0f8b069387a9afc9733e8e00b4e3ec2abcfcb7d068d44689c234a3c56b4')
add(B/'book61-source57-full-current-intake-20261115/ACTUAL-SOLE-WRITER-BOOK61-FROZEN-H-SOURCE-ALL-SPEC-INTAKE.json','sole-writer-actual-frozen-H-recursive-spec-intake.json','2dc9a462c13842ab3dfea7165dfb428a40d0efa9392059803f1ef37b0c2f27d8')
add(B/'book61-source57-full-current-intake-20261115/ACTUAL-SOLE-WRITER-BOOK61-FIVE-CURRENT-FRAMES-PERSONAL-VIEW.json','sole-writer-actual-five-current-decoded-frames-review.json')
add('/workspace/work/book61-source57-actual43719354588-original-HOST-preparation-20261115/BOOK61-SOURCE57-FINAL-COMPLETE-EXTRA-INTAKE-HISTORY-AND-ACTUAL-PHASE-GUARDS-HANDOFF.json','actual-source57-intake-directory-alias-history-and-phase-guards.json','cafcf9b7447ce1200cc294188bcb06413f9db86f7c14dca744e4222a6f21d40a')
M=R/'explicit-safe-source57-book61-public-evidence.json'
M.write_text(json.dumps({'kind':'exact-source57-final-H-declared-material-and-actual-all-project-user-publication-consent',
 'source_id':'57','book_order':'61','files':rows,'source_publication_consent_sha256':CS,
 'frozen_quality_H_original_publication_scope_preserved_not_rewritten':True,
 'new_publication_authority_is_actual_b00_user_project_archive_message_not_implied_by_QA':True,
 'all_source_native_normal18_and_failure_history_already_declared_in_frozen_H':True,
 'no_private_RAW_GT_cache_models_tokens_signedURL_ROOTSTATE_PDF_or_other_article_content':True},ensure_ascii=False,indent=2)+'\n')
cmd=[sys.executable,R/'prepare_new_sourceQA_normal18_assets.py','--handoff',H,'--expected-handoff-sha256',HS,
 '--work-dir',W,'--explicit-public-manifest',M,'--explicit-public-manifest-sha256',digest(M)]
p=subprocess.run(list(map(str,cmd)),capture_output=True,text=True,env={**os.environ,'TMPDIR':str(R),'PYTHONDONTWRITEBYTECODE':'1'})
(R/'actual-prepare.log').write_text(p.stdout+p.stderr);assert p.returncode==0,(p.stdout+p.stderr)[-2500:]
m=json.loads((W/'prepared-archive.json').read_bytes());row=m['articles'][0]
assert row['source_id']=='57' and row['new_id']=='61' and row['postprocessing_full_V3_handoff_sha256']==HS
assert row['local_tail_postprocessing_audio_repair_applied'] is False
shutil.copyfile(__file__,P/m['prefix']/'归档程序'/Path(__file__).name)
idx=[{'repo_path':str(p.relative_to(P)),'bytes':p.stat().st_size,'sha256':digest(p)} for p in sorted(P.rglob('*')) if p.is_file()]
(W/'payload-file-index.json').write_text(json.dumps(idx,ensure_ascii=False,indent=2)+'\n')
deny={'b9a257a23820944ee95d568b67d1cd78947b1c1814bb70dc99a45871f488f778','55026ce1b7cdb7e9c1a72da2f715e3d9e6e6f45050a8ddd575dc052b09dca872','bcb37d8930d804988c95da94b9cfeaaab2c7b026df96e6e4567f9b698ce88fbf'}
assert not any(x['sha256'] in deny for x in idx)
loc={'root':str(R),'work_dir':str(W),'source_id':'57','new_id':'61','handoff':str(H),'handoff_sha256':HS,
 'source_publication_consent':str(CONSENT),'source_publication_consent_sha256':CS,
 'files':len(idx),'logical_bytes':sum(x['bytes'] for x in idx),'source_native_audio_repair_applied':row['source_native_audio_repair_applied'],
 'host_hardlinks_and_host_Git_TMPDIR_only':True,'no_remote_write_by_this_local_preparation':True}
(C/'active-source57-book61-full-asset-staging-location.json').write_text(json.dumps(loc,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(loc,ensure_ascii=False),flush=True)
