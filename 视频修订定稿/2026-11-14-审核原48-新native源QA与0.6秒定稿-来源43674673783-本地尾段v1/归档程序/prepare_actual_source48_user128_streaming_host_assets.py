"""Only root-approved208205 frozen collection, exact same-content I/O; no network."""
from pathlib import Path
import tempfile,shutil,json,hashlib,subprocess,sys,os
B=Path(__file__).parent;C=Path('/dev/shm/archive-writer-main061');D=Path('/workspace/work/source48-low-disk-streaming-transport-review-20261115')
H=Path('/workspace/work/review42-source48-E44-RAM-original128-hold06-intake/validated/48/archive-handoff.json');HS='2082052baf9f71be9a0dcc5090234129a08e297714dc1738be8e2c1ffb099ece'
def digest(p):
 h=hashlib.sha256()
 with Path(p).open('rb')as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def spec(p):
 p=Path(p);return {'path':str(p),'bytes':p.stat().st_size,'sha256':digest(p)}
assert H.stat().st_size==75467 and digest(H)==HS;h=json.loads(H.read_text());a=h['articles'][0]
assert (a['source_id'],a['new_id'])==('48','42') and a['final_mp4']['bytes']==20307318 and a['final_mp4']['sha256']=='612b53f821b5487406f3c0c6b3e82c57413c553f45509ffa0f045238d8c4ee5b'
IO=Path('/workspace/work/root-source48-final208205-collector-samecontent-IO-adoption-decision.json');assert digest(IO)=='4b6914e7b2d778c8412cc43897b80fdb73dc9cad6bb3b1bc898b54992480d620'
assert digest(D/'streaming_git_data_asset_transport.py')=='b2a563d63a4976cbbdbe2bbe3eccee38b0a6dcb15d009fc77228152aba70e2cc'
assert digest(D/'source48_same_content_collector_io.py')=='3de3baecb1f70435debc368b58ee9e2fddb8625b51f77eb457f3baebbf9aa0b0'
assert digest(D/'prepare_source48_exact208205_same_content_IO_assets.py')=='a3516aeba62aa83aa4f4376b6f4de5c54600118236f33f4a06711a4dff8e33b3'
s=json.loads(Path(h['current_source_validation_handoff']['path']).read_text());declared=[]
def bind(x):
 p=Path(x['path']);assert p.stat().st_size==x['bytes']and digest(p)==x['sha256'];declared.append(dict(x))
for x in s['validation_files']+h['validation_files']:bind(x)
bind(h['current_source_validation_handoff'])
for p in [H,h['report_path'],h['input_path']]:declared.append(spec(p))
for n,sha in h['tool_source_sha256'].items():
 p=Path(h['code_snapshot_path'])/n;assert digest(p)==sha;declared.append(spec(p))
for x in h['global_approved_evidence'].values():bind(x)
for x in h['additional_public_media_inputs']+a['section']['stills']:bind(x)
for k in ['final_mp4','canonical_source_mp4','immutable_native_zip']:bind(a[k])
art=a['section']['illustration'];bind(art);bind(art['native_source'])
rows=[]
for n,x in [('actual-approved-prepared4K-48.png',art),('original-approved-book48.png',art['native_source'])]:rows.append({**spec(x['path']),'archive_relative_path':'actual-approved-illustration/'+n})
freeze=Path('/workspace/work/review42-source48-E44-RAM-original128-hold06-intake/SOURCE48-USER128-FINAL-FULLV3-FREEZE-RECEIPT.json');assert digest(freeze)=='03b8fe7a926fca411a4a719f8d331ec2f1f8ba02f8fc8dbade0c862735a660ac'
for p in [freeze,IO,Path('/workspace/work/root-source48-user128-final208205-fullV3-adoption-for-dual-current-archive-decision.json'),D/'source48-collector-IO-only-actual.diff',D/'source48-collector-IO-only-actual-boundary-tests.json',D/'actual-source48-frozen-H-readonly-collector-budget.json',D/'source48_same_content_collector_io.py',D/'streaming_git_data_asset_transport.py',B/'prepare_new_sourceQA_normal18_assets.py']:
 x=spec(p);rows.append({**x,'archive_relative_path':'exact-source48-frozen-archive-IO-and-code/'+p.name});declared.append(x)
declared.append(spec(freeze));declared.append(spec('/workspace/work/first50-review-release/USER-REVIEW-2026-11-14-051.json'))
hostdev=B.stat().st_dev;host={};unique={}
for x in declared:
 key=(x['bytes'],x['sha256']);unique.setdefault(key,x)
 if Path(x['path']).stat().st_dev==hostdev:host.setdefault(key,x)
cross=[x for k,x in unique.items()if k not in host];required=sum((x['bytes']+4095)//4096*4096 for x in cross);available=os.statvfs(B).f_bavail*os.statvfs(B).f_frsize
assert available>required+10*1024*1024
R=Path(tempfile.mkdtemp(prefix='user128-source48-streaming-host-isolated-assets-',dir=str(B)));W=R/'run43674673783-48-user128-review-normal18-v1';W.mkdir();P=R/'payload-data';P.mkdir();(W/'payload').symlink_to(P,target_is_directory=True)
for n in ['video_title_authorization.py','archive_batch.py','verify_dual_media_asset_blobs.py','emit_ready_revision_download_manifest.py']:shutil.copyfile(B/n,R/n)
shutil.copyfile(D/'prepare_source48_exact208205_same_content_IO_assets.py',R/'prepare_new_sourceQA_normal18_assets.py')
for n in ['source48_same_content_collector_io.py','streaming_git_data_asset_transport.py']:shutil.copyfile(D/n,R/n)
M=R/'explicit-safe-source48-user128-public-evidence-and-exact-IO-pins.json'
M.write_text(json.dumps({'source_id':'48','book_order':'42','kind':'only-source48-frozen-H-plus-illustration-root-adoption-and-exact-IO-source','files':rows,'same_content_IO_scope_handoff_sha256':HS,'same_content_HOST_IO_candidates':[{k:x[k]for k in ['path','bytes','sha256']}for x in host.values()],'no_private_PCM_GT_cache_PDF_ROOT_state':True},ensure_ascii=False,indent=2)+'\n')
cmd=[sys.executable,R/'prepare_new_sourceQA_normal18_assets.py','--handoff',H,'--expected-handoff-sha256',HS,'--work-dir',W,'--explicit-public-manifest',M,'--explicit-public-manifest-sha256',digest(M)]
p=subprocess.run(list(map(str,cmd)),capture_output=True,text=True,env={**os.environ,'TMPDIR':str(R),'PYTHONDONTWRITEBYTECODE':'1'});(R/'actual-prepare.log').write_text(p.stdout+p.stderr);assert p.returncode==0,(p.stdout+p.stderr)[-3000:]
m=json.loads((W/'prepared-archive.json').read_text());row=m['articles'][0];assert row['source_native_audio_repair_applied']is True and row['local_tail_postprocessing_audio_repair_applied']is False
shutil.copyfile(__file__,P/m['prefix']/'归档程序'/Path(__file__).name)
idx=[{'repo_path':str(p.relative_to(P)),'bytes':p.stat().st_size,'sha256':digest(p)}for p in sorted(P.rglob('*'))if p.is_file()];(W/'payload-file-index.json').write_text(json.dumps(idx,ensure_ascii=False,indent=2)+'\n')
deny={'b9a257a23820944ee95d568b67d1cd78947b1c1814bb70dc99a45871f488f778','55026ce1b7cdb7e9c1a72da2f715e3d9e6e6f45050a8ddd575dc052b09dca872','bcb37d8930d804988c95da94b9cfeaaab2c7b026df96e6e4567f9b698ce88fbf'};assert not any(x['sha256']in deny for x in idx)
loc={'root':str(R),'work_dir':str(W),'source_id':'48','new_id':'42','handoff':str(H),'handoff_sha256':HS,'files':len(idx),'logical_bytes':sum(x['bytes']for x in idx),'prepared_sha256':digest(W/'prepared-archive.json'),'index_sha256':digest(W/'payload-file-index.json'),'streaming_module_sha256':digest(R/'streaming_git_data_asset_transport.py'),'crossfs_unique_copy_allocated_budget':required,'host_available_before':available,'host_available_after':os.statvfs(B).f_bavail*os.statvfs(B).f_frsize,'no_POST_or_network_or_ref_or_canonical_changed':True}
(C/'active-source48-user128-streaming-staging-location.json').write_text(json.dumps(loc,indent=2)+'\n');(R/'actual-source48-collection-completed-not-upload.json').write_text(json.dumps(loc,indent=2)+'\n');print(json.dumps(loc),flush=True)
