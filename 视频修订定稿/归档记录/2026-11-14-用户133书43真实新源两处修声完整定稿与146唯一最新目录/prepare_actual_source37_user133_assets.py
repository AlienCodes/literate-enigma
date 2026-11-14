"""Frozen actual source37/user133 source-QA plus normal18 assets only."""
from pathlib import Path
import tempfile,shutil,json,hashlib,subprocess,sys
B=Path('/workspace/work/video-archive-batches-20261114');C=Path(__file__).parent
H=Path('/dev/shm/review43-hold06-intake/validated/37/archive-handoff.json');hs='4e8aa48331f061427e111c0f90a1f120464e64e5600e78ee25fa17f6d18554a3';assert hashlib.sha256(H.read_bytes()).hexdigest()==hs;h=json.loads(H.read_text())
R=Path(tempfile.mkdtemp(prefix='user133-source37-isolated-assets-',dir='/dev/shm'));W=R/'run43640826249-37-user133-review-normal18-v1';W.mkdir();P=R/'payload-data';P.mkdir();(W/'payload').symlink_to(P,target_is_directory=True)
for name in ['prepare_new_sourceQA_normal18_assets.py','source37_public_diagnostic_contexts.py','video_title_authorization.py','archive_batch.py','resume_layout_isolated_asset_transport.py','verify_dual_media_asset_blobs.py','emit_ready_revision_download_manifest.py','cleanup_closed_media_asset_bare.py']:shutil.copyfile(B/name,R/name)
M0=Path('/dev/shm/article37-user131-draft-20261114/safe-source37-user133-text-static-and-measured-audio-evidence-whitelist.json');raw=M0.read_bytes();ms='2a5ff2d9e9e68bbb6ad4ea465f427328cd4d7ea5e9acf2c977027831e9342b0f';assert hashlib.sha256(raw).hexdigest()==ms
rows=[{'path':str(M0),'bytes':len(raw),'sha256':ms,'archive_relative_path':'source-static-and-public-audio-evidence/original-safe-manifest.json'}]
for i,x in enumerate(json.loads(raw)['files'],1):
 p=Path(x['path'])if 'path'in x else M0.parent/x['name'];assert p.stat().st_size==x['bytes']and hashlib.sha256(p.read_bytes()).hexdigest()==x['sha256'],str(p);rows.append({'path':str(p),'bytes':x['bytes'],'sha256':x['sha256'],'archive_relative_path':f'source-static-and-public-audio-evidence/{i:03d}-'+p.name})
art=h['articles'][0]['section']['illustration']
for name,x in [('actual-prepared4K-37.png',art),('original-approved-book37.png',art['native_source'])]:rows.append({'path':x['path'],'bytes':x['bytes'],'sha256':x['sha256'],'archive_relative_path':'actual-approved-illustration/'+name})
D=Path('/dev/shm/book43-source37-user133-hold06-20261114')
for p in sorted(D.iterdir()):
 if p.is_file()and p.suffix in {'.json','.py','.log'}:rows.append({'path':str(p),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'archive_relative_path':'actual-normal18-producer/'+p.name})
p=Path('/dev/shm/review43-hold06-intake/recursive-final-input-section-evidence-integrity-before-freeze.json');sha=hashlib.sha256(p.read_bytes()).hexdigest();assert sha=='42900439a2814cd87b17e829a7a0d230c58e4120d1798e0ccc0c0e18f0bcb363';rows.append({'path':str(p),'bytes':p.stat().st_size,'sha256':sha,'archive_relative_path':'adjacent-integrity-not-H-rewrite/'+p.name})
M=R/'explicit-safe-source37-public-evidence.json';M.write_text(json.dumps({'source_id':'37','book_order':'43','kind':'only-specific-approved-safe-source-static-public-processed-contexts-and-actual-producer','files':rows,'no_private_PCM_GT_cache_PDF_ROOT_state':True,'diagnostic_clips_only_exact_source37_public_context_contract':True},ensure_ascii=False,indent=2)+'\n')
cmd=[sys.executable,R/'prepare_new_sourceQA_normal18_assets.py','--handoff',H,'--expected-handoff-sha256',hs,'--work-dir',W,'--explicit-public-manifest',M,'--explicit-public-manifest-sha256',hashlib.sha256(M.read_bytes()).hexdigest()];p=subprocess.run(list(map(str,cmd)),capture_output=True,text=True);(R/'actual-prepare.log').write_text(p.stdout+p.stderr);assert p.returncode==0,(p.stdout+p.stderr)[-3000:]
idx=json.loads((W/'payload-file-index.json').read_text());deny={'b9a257a23820944ee95d568b67d1cd78947b1c1814bb70dc99a45871f488f778','55026ce1b7cdb7e9c1a72da2f715e3d9e6e6f45050a8ddd575dc052b09dca872','bcb37d8930d804988c95da94b9cfeaaab2c7b026df96e6e4567f9b698ce88fbf'};assert not any(x['sha256']in deny for x in idx)
loc={'root':str(R),'work_dir':str(W),'source_id':'37','new_id':'43','handoff':str(H),'handoff_sha256':hs,'files':len(idx),'logical_bytes':sum(x['bytes']for x in idx)};(C/'active-source37-user133-asset-staging-location.json').write_text(json.dumps(loc,indent=2)+'\n');print(json.dumps(loc),flush=True)
