"""Preserve completed public publication facts; no media or live state collection."""
from pathlib import Path
import hashlib,json,shutil,tempfile,zipfile

C=Path(__file__).parent
D=Path('/dev/shm/book38-tulip-mania-publisher-preparation-20261114')
T=Path(tempfile.mkdtemp(prefix='user109-publication-safe-records-',dir='/dev/shm'))
W=T/'user109-actual-native-publication-and-current-folder-public-proofs'
W.mkdir()
P=W/'payload'
prefix=Path('视频修订定稿/归档记录/2026-11-14-用户109第38篇实际公开发行及最新目录公开核验')
Q=P/prefix
Q.mkdir(parents=True)
deny={'b9a257a23820944ee95d568b67d1cd78947b1c1814bb70dc99a45871f488f778','55026ce1b7cdb7e9c1a72da2f715e3d9e6e6f45050a8ddd575dc052b09dca872','bcb37d8930d804988c95da94b9cfeaaab2c7b026df96e6e4567f9b698ce88fbf'}
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def collect(p,name=None):
 raw=p.read_bytes();assert hashlib.sha256(raw).hexdigest() not in deny
 assert p.suffix in {'.json','.py','.yml','.zip'}
 (Q/(name or p.name)).write_bytes(raw)
 return {'archive_name':name or p.name,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}

z=D/'actual-native-release-result/artifact.zip'
j=D/'actual-native-release-result/files/RELEASE-VERIFICATION.json'
assert z.stat().st_size==915 and hashlib.sha256(z.read_bytes()).hexdigest()=='14ed6ca2cfcfe1edf845a252848c5096dd3e7e0871882e82eb1c68b3d524227e'
assert hashlib.sha256(j.read_bytes()).hexdigest()=='17932cd6b01d5f1d81133ffd4ed863dae90b6ae78b4c9cb836625636016a193a'
with zipfile.ZipFile(z) as f:
 assert f.testzip() is None
 names=[x for x in f.namelist() if x.endswith('RELEASE-VERIFICATION.json')]
 assert len(names)==1 and f.read(names[0])==j.read_bytes()
records=[]
for name in ['publish_single.py','publish-single.yml','publish_actual_manifest.py','save_prepared_sources.py','prepare_code.py','ACTUAL-CODE-ONLY-DUAL-SAVE.json','ACTUAL-MANIFEST-PUBLICATION-TRIGGER.json','MANIFEST.json']:
 records.append(collect(D/name))
records.append(collect(z,'native-release-verification-artifact.zip'))
records.append(collect(j))
for name in ['root-book38-single109-public-complete-download-verification.json','root-user146-latest-final-folder-post19-remote-verification.json']:
 p=Path('/dev/shm')/name;x=json.loads(p.read_text());assert x['passed'] is True
 assert not any(s in p.read_text() for s in ['/dev/shm/','/workspace/','CURRENT-ROOT'])
 records.append(collect(p))
profile=json.loads((D/'PUBLICATION-PROFILE.json').read_text())
assert profile.pop('directory')==str(D)
save(Q/'PUBLICATION-PROFILE-public-facts.json',profile)
save(Q/'ACTUAL-PUBLICATION-ARCHIVE-FACTS.json',{
 'kind':'completed-user109-publication-and-purpose-built-public-folder-verification-records',
 'source_id':'19','frozen_book_order':'38','user_review_authority':'109',
 'native_publication_run_id':43639397499,'native_publication_attempt':2,
 'native_publication_commit':'95036baa3d93ab43acaa4679417d14ec10f1198a',
 'public_release_id':445583415,'public_video_bytes':16083772,
 'public_video_sha256':'8d39d745c27db6fd682a6c273c800d6efa8c22aa759f562720eb9e7cfcf54ee0',
 'unique_verification_artifact_bytes':915,'unique_verification_artifact_CRC_and_embedded_JSON_checked':True,
 'original_public_profile_directory_field_omitted':True,
 'native_attempt1_transport_timeout_retained_as_history_not_media_QA_failure':True,
 'attempt1_original_log_not_collected_in_this_package':True,
 'existing_actual_complete_HTTP_proofs_reused_without_repeating_video_download':True,
 'main_current_video_source_QA_PDF_or_Release_modified_by_this_archive':False,
 'live_ROOT_or_denied_raw_payload_collected':False,'explicit_original_files':records})
shutil.copyfile(__file__,Q/Path(__file__).name)
push=(C/'push_user144_source40_draft.py').read_text().replace('source40-draft-static-staging-location.json','user109-publication-records-staging-location.json')
start=push.index("scope={'kind':");end=push.index('\nsp=P/',start)
push=push[:start]+"scope={'kind':'completed-user109-publication-small-records-and-purpose-built-public-folder-proofs','original_records':index,'no_media_redownload_current_QA_PDF_ROOT_or_Release_operation':True}"+push[end:]
(C/'push_user109_publication_records.py').write_text(push)
shutil.copyfile(C/'push_user109_publication_records.py',Q/'push_user109_publication_records.py')
meta={'prefix':str(prefix),'asset_branch':'codex/user109-completed-publication-and-public-folder-proofs-20261114'}
save(W/'prepared-archive.json',meta)
idx=[{'repo_path':str(p.relative_to(P)),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}for p in sorted(P.rglob('*'))if p.is_file()]
assert all(x['sha256'] not in deny for x in idx)
save(W/'payload-file-index.json',idx)
shutil.copyfile('/workspace/work/video-archive-batches-20261114/archive_batch.py',T/'archive_batch.py')
save(C/'user109-publication-records-staging-location.json',{'root':str(T),'work_dir':str(W),'files':len(idx),'bytes':sum(x['bytes']for x in idx)})
print(json.dumps({'work_dir':str(W),'files':len(idx),'bytes':sum(x['bytes']for x in idx)}))
