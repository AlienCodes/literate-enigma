"""Original full-source collector, exact book48/source46; new public consent is separate from frozen QA H."""
from pathlib import Path
import tempfile,shutil,json,hashlib,subprocess,sys,os
B=Path(__file__).parent;C=Path('/dev/shm/archive-writer-main061')
H=Path('/workspace/work/review48-source46-E52-normal18-intake/validated/archive-handoff.json')
HS='d9cd2e3c533c91b2bf127937b3438c6ffbade5cecd6f38da4466a8515c5caf95'
CONSENT=Path('/dev/shm/USER-EXPLICIT-EIGHT-FINAL-SOURCE-DOCUMENT-PUBLICATION-CONSENT-20261115.json')
CS='9034beaf30fc4afcfcaf1a84197f01ca4ed3f1a0b64e2ae4dcf971c823eda3b0'
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert H.stat().st_size==95832 and digest(H)==HS
assert CONSENT.stat().st_size==1826 and digest(CONSENT)==CS
consent=json.loads(CONSENT.read_bytes());assert consent['author']=='user' and {'book':48,'source':'46'} in consent['authorized_final_article_pairs']
assert consent['actual_raw_user_question_reply'][0]['answer']=='允许，继续制作并保存这些源文档'
h=json.loads(H.read_bytes());a=h['articles'][0]
assert a['source_id']=='46' and a['new_id']=='48'
assert a['final_mp4']['bytes']==16126260 and a['final_mp4']['sha256']=='cc21ba260651f536e5403d5bf1dfb5a40c02e36307eceb96f4aa80e4adbf4cb9'
R=Path(tempfile.mkdtemp(prefix='book48-source46-full-host-isolated-assets-',dir=str(B)))
W=R/'run43702082473-46-book48-review-normal18-v1';W.mkdir()
P=R/'payload-data';P.mkdir();(W/'payload').symlink_to(P,target_is_directory=True)
for n in ['prepare_new_sourceQA_normal18_assets.py','video_title_authorization.py','archive_batch.py','verify_dual_media_asset_blobs.py','emit_ready_revision_download_manifest.py','cleanup_closed_media_asset_bare.py']:
 shutil.copyfile(B/n,R/n)
rows=[]
def add(p,rel,expected=None):
 p=Path(p);s=digest(p)
 if expected:assert s==expected
 rows.append({'path':str(p),'bytes':p.stat().st_size,'sha256':s,'archive_relative_path':rel})
art=a['section']['illustration']
for name,x in [('actual-approved-prepared4K-46.png',art),('original-approved-book46.png',art['native_source'])]:
 assert Path(x['path']).stat().st_size==x['bytes'] and digest(x['path'])==x['sha256'];add(x['path'],'actual-approved-illustration/'+name,x['sha256'])
add(CONSENT,'separate-new-user-source-publication-consent.json',CS)
add('/workspace/work/USER-BOOK48-FINALIZATION-AFTER-BRIGHTENING-20261115.json','actual-book48-finalization-authority.json','82cd0b5dbe9b796faef7c8c108aad00efef68fb9797d7eaef6d8ea5a97da9038')
M=R/'explicit-safe-source46-book48-public-evidence.json'
M.write_text(json.dumps({'kind':'exact-source46-final-H-declared-material-and-actual-eight-article-user-publication-consent',
 'source_id':'46','book_order':'48','files':rows,'source_publication_consent_sha256':CS,
 'frozen_quality_H_original_publication_scope_preserved_not_rewritten':True,
 'new_publication_authority_is_actual_received_user_answer_not_implied_by_QA':True,
 'all_source_native_normal18_and_failure_history_already_declared_in_frozen_H':True,
 'no_private_RAW_GT_cache_models_tokens_signedURL_ROOTSTATE_PDF_or_other_article_content':True},ensure_ascii=False,indent=2)+'\n')
cmd=[sys.executable,R/'prepare_new_sourceQA_normal18_assets.py','--handoff',H,'--expected-handoff-sha256',HS,
 '--work-dir',W,'--explicit-public-manifest',M,'--explicit-public-manifest-sha256',digest(M)]
p=subprocess.run(list(map(str,cmd)),capture_output=True,text=True,env={**os.environ,'TMPDIR':str(R),'PYTHONDONTWRITEBYTECODE':'1'})
(R/'actual-prepare.log').write_text(p.stdout+p.stderr);assert p.returncode==0,(p.stdout+p.stderr)[-2500:]
m=json.loads((W/'prepared-archive.json').read_bytes());row=m['articles'][0]
assert row['source_id']=='46' and row['new_id']=='48' and row['postprocessing_full_V3_handoff_sha256']==HS
assert row['local_tail_postprocessing_audio_repair_applied'] is False
shutil.copyfile(__file__,P/m['prefix']/'归档程序'/Path(__file__).name)
idx=[{'repo_path':str(p.relative_to(P)),'bytes':p.stat().st_size,'sha256':digest(p)} for p in sorted(P.rglob('*')) if p.is_file()]
(W/'payload-file-index.json').write_text(json.dumps(idx,ensure_ascii=False,indent=2)+'\n')
deny={'b9a257a23820944ee95d568b67d1cd78947b1c1814bb70dc99a45871f488f778','55026ce1b7cdb7e9c1a72da2f715e3d9e6e6f45050a8ddd575dc052b09dca872','bcb37d8930d804988c95da94b9cfeaaab2c7b026df96e6e4567f9b698ce88fbf'}
assert not any(x['sha256'] in deny for x in idx)
loc={'root':str(R),'work_dir':str(W),'source_id':'46','new_id':'48','handoff':str(H),'handoff_sha256':HS,
 'source_publication_consent':str(CONSENT),'source_publication_consent_sha256':CS,
 'files':len(idx),'logical_bytes':sum(x['bytes'] for x in idx),'source_native_audio_repair_applied':row['source_native_audio_repair_applied'],
 'host_hardlinks_and_host_Git_TMPDIR_only':True,'no_remote_write_by_this_local_preparation':True}
(C/'active-source46-book48-full-asset-staging-location.json').write_text(json.dumps(loc,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(loc,ensure_ascii=False),flush=True)
