"""Collect only frozen user148 final and its declared public evidence; host hardlinks."""
from pathlib import Path
import tempfile, shutil, json, hashlib, subprocess, sys, os
B=Path(__file__).parent; C=Path('/dev/shm/archive-writer-main061')
H=Path('/workspace/work/review47-source54-user148-E41-actual-hold06-intake/validated/54/archive-handoff.json')
HS='46a63b140490b461852010212e1fc850221bc0ae4bced15b482673f921cb50e7'
def digest(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert H.stat().st_size==56722 and digest(H)==HS
h=json.loads(H.read_text()); a=h['articles'][0]
assert a['source_id']=='54' and a['new_id']=='47'
assert a['final_mp4']['bytes']==22100097 and a['final_mp4']['sha256']=='dffa42ac5cc04d93a52a414a371d278037568f0485a3814f2f09cba86edf2fe2'
R=Path(tempfile.mkdtemp(prefix='user148-source54-host-isolated-assets-',dir=str(B)))
W=R/'run43667925349-54-user148-review-normal18-v1'; W.mkdir()
P=R/'payload-data'; P.mkdir(); (W/'payload').symlink_to(P,target_is_directory=True)
for n in ['prepare_new_sourceQA_normal18_assets.py','video_title_authorization.py','archive_batch.py','verify_dual_media_asset_blobs.py','emit_ready_revision_download_manifest.py','cleanup_closed_media_asset_bare.py']:
 shutil.copyfile(B/n,R/n)
rows=[]
def add(p,relative,expected=None):
 p=Path(p); sha=digest(p)
 if expected: assert sha==expected
 rows.append({'path':str(p),'bytes':p.stat().st_size,'sha256':sha,'archive_relative_path':relative})
art=a['section']['illustration']
for n,x in [('actual-approved-prepared4K-54.png',art),('original-approved-book54.png',art['native_source'])]:
 assert Path(x['path']).stat().st_size==x['bytes'] and digest(x['path'])==x['sha256']; add(x['path'],'actual-approved-illustration/'+n,x['sha256'])
add('/workspace/work/review47-source54-user148-E41-actual-hold06-intake/validated/source54-user148-final-freeze-receipt.json','adjacent-final-freeze-not-H-rewrite/source54-user148-final-freeze-receipt.json','59f442a0801cde4f0007b8dfccce87c9af934627a38e65aef828f502ffc2ec81')
M=R/'explicit-safe-source54-user148-public-evidence.json'
M.write_text(json.dumps({'source_id':'54','book_order':'47','kind':'only-final-H-declared-source-QA-plus-approved-illustration-and-freeze','files':rows,'all_source_native_normal148_and_failed_ENOSPC_history_already_exactly_declared_in_frozen_H':True,'no_private_PCM_GT_cache_PDF_ROOT_state':True},ensure_ascii=False,indent=2)+'\n')
cmd=[sys.executable,R/'prepare_new_sourceQA_normal18_assets.py','--handoff',H,'--expected-handoff-sha256',HS,'--work-dir',W,'--explicit-public-manifest',M,'--explicit-public-manifest-sha256',digest(M)]
p=subprocess.run(list(map(str,cmd)),capture_output=True,text=True,env={**os.environ,'TMPDIR':str(R),'PYTHONDONTWRITEBYTECODE':'1'})
(R/'actual-prepare.log').write_text(p.stdout+p.stderr); assert p.returncode==0,(p.stdout+p.stderr)[-3500:]
m=json.loads((W/'prepared-archive.json').read_text()); row=m['articles'][0]
assert row['source_native_audio_repair_applied'] is False and row['local_tail_postprocessing_audio_repair_applied'] is False
reg=json.loads((C/'latest_requests.json').read_text()); entry=next(x for x in reg['articles']if x['source_id']=='54')
assert entry['newest_user_revision_records']==['147','148'] and entry['latest_finalization_authority']=='148'
historical=entry['latest_pending_scope']['old_qualified_review_only_video_is_history_until_this_request_is_resolved']
row['previous_qualified_review_versions']=[{**historical,'role':'historical_user102_review_only_not_previously_accepted_final','superseded_by_user_records':['147','148']}]
m['articles'][0]=row
for path in [W/'prepared-archive.json',P/m['prefix']/'archive-manifest.json']: path.write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n')
shutil.copyfile(__file__,P/m['prefix']/'归档程序'/Path(__file__).name)
idx=[{'repo_path':str(p.relative_to(P)),'bytes':p.stat().st_size,'sha256':digest(p)} for p in sorted(P.rglob('*')) if p.is_file()]
(W/'payload-file-index.json').write_text(json.dumps(idx,ensure_ascii=False,indent=2)+'\n')
deny={'b9a257a23820944ee95d568b67d1cd78947b1c1814bb70dc99a45871f488f778','55026ce1b7cdb7e9c1a72da2f715e3d9e6e6f45050a8ddd575dc052b09dca872','bcb37d8930d804988c95da94b9cfeaaab2c7b026df96e6e4567f9b698ce88fbf'}
assert not any(x['sha256']in deny for x in idx)
loc={'root':str(R),'work_dir':str(W),'source_id':'54','new_id':'47','handoff':str(H),'handoff_sha256':HS,'files':len(idx),'logical_bytes':sum(x['bytes']for x in idx),'host_hardlinks_and_host_Git_TMPDIR_only':True}
(C/'active-source54-user148-asset-staging-location.json').write_text(json.dumps(loc,indent=2)+'\n')
print(json.dumps(loc),flush=True)
