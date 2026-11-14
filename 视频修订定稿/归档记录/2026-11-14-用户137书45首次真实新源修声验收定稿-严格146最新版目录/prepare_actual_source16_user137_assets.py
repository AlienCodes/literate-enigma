"""Frozen actual source16/user137 first accepted source-QA plus normal18 assets."""
from pathlib import Path
import tempfile,shutil,json,hashlib,subprocess,sys
B=Path('/workspace/work/video-archive-batches-20261114');C=Path(__file__).parent
H=Path('/dev/shm/review45-hold06-intake/validated/16/archive-handoff.json');hs='77598ea4bb129a077a320e11d5a0f7f031ed3135b3095d3b9d264a9b7f725fb7';assert H.stat().st_size==52165 and hashlib.sha256(H.read_bytes()).hexdigest()==hs;h=json.loads(H.read_text())
R=Path(tempfile.mkdtemp(prefix='user137-source16-isolated-assets-',dir='/dev/shm'));W=R/'run43644041957-16-user137-review-normal18-v1';W.mkdir();P=R/'payload-data';P.mkdir();(W/'payload').symlink_to(P,target_is_directory=True)
for name in ['prepare_new_sourceQA_normal18_assets.py','video_title_authorization.py','archive_batch.py','resume_layout_isolated_asset_transport.py','verify_dual_media_asset_blobs.py','emit_ready_revision_download_manifest.py','cleanup_closed_media_asset_bare.py']:shutil.copyfile(B/name,R/name)
M0=Path('/dev/shm/article16-user135137-final-20261114/root-selected-actual-native-diagnostic/safe-source16-root-selected-source-evidence-whitelist.json');raw=M0.read_bytes();ms='0813c870d94f7ab48f59c122f88c03167622dccdc8ffa6358916fb3a481893a6';assert hashlib.sha256(raw).hexdigest()==ms
rows=[{'path':str(M0),'bytes':len(raw),'sha256':ms,'archive_relative_path':'root-selected-explicit-safe-source-evidence/original-safe-manifest.json'}]
for i,x in enumerate(json.loads(raw)['files'],1):
 p=Path(x['path']);sha=x.get('sha256',x.get('SHA256'));assert sha and p.stat().st_size==x['bytes']and hashlib.sha256(p.read_bytes()).hexdigest()==sha,str(p);rows.append({'path':str(p),'bytes':x['bytes'],'sha256':sha,'archive_relative_path':f'root-selected-explicit-safe-source-evidence/{i:03d}-'+p.name})
art=h['articles'][0]['section']['illustration']
for name,x in [('actual-prepared4K-16.png',art),('original-approved-book16.png',art['native_source'])]:rows.append({'path':x['path'],'bytes':x['bytes'],'sha256':x['sha256'],'archive_relative_path':'actual-approved-illustration/'+name})
D=Path('/dev/shm/book45-source16-user137-hold06-20261114')
for p in sorted(D.iterdir()):
 if p.is_file()and p.suffix in {'.json','.py','.log'}:rows.append({'path':str(p),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'archive_relative_path':'actual-normal18-producer/'+p.name})
M=R/'explicit-safe-source16-public-evidence.json';M.write_text(json.dumps({'source_id':'16','book_order':'45','kind':'only-specific-approved-source-and-controlled-Origin-repair-history-with-actual-producer','files':rows,'no_private_PCM_GT_cache_PDF_ROOT_state':True,'new_actual_AAC_not_falsely_described_as_old_accepted_equal':True},ensure_ascii=False,indent=2)+'\n')
cmd=[sys.executable,R/'prepare_new_sourceQA_normal18_assets.py','--handoff',H,'--expected-handoff-sha256',hs,'--work-dir',W,'--explicit-public-manifest',M,'--explicit-public-manifest-sha256',hashlib.sha256(M.read_bytes()).hexdigest()];p=subprocess.run(list(map(str,cmd)),capture_output=True,text=True);(R/'actual-prepare.log').write_text(p.stdout+p.stderr);assert p.returncode==0,(p.stdout+p.stderr)[-3000:]
idx=json.loads((W/'payload-file-index.json').read_text());deny={'b9a257a23820944ee95d568b67d1cd78947b1c1814bb70dc99a45871f488f778','55026ce1b7cdb7e9c1a72da2f715e3d9e6e6f45050a8ddd575dc052b09dca872','bcb37d8930d804988c95da94b9cfeaaab2c7b026df96e6e4567f9b698ce88fbf'};assert not any(x['sha256']in deny for x in idx)
loc={'root':str(R),'work_dir':str(W),'source_id':'16','new_id':'45','handoff':str(H),'handoff_sha256':hs,'files':len(idx),'logical_bytes':sum(x['bytes']for x in idx)};(C/'active-source16-user137-asset-staging-location.json').write_text(json.dumps(loc,indent=2)+'\n');print(json.dumps(loc),flush=True)
