"""Freeze only existing three-video isolated staging receipts, count stays55.

No cumulative inventory generation, canonical writes, audio/video processing,
source changes or Release operations. The payload has only public small records.
"""
import pathlib,json,hashlib,shutil,datetime
D=pathlib.Path(__file__).resolve().parent;B=D.parent
SIDRUN=[('61','43560056264'),('15','43562525001'),('17','43562525001')]
def load(p):return json.loads(pathlib.Path(p).read_text())
def save(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
state=load(B/'CURRENT-ARCHIVE-STATE.json');assert state['permanently_archived_count']==55
blobs=load(D/'dual-isolated-asset-blob-verification.json');assert blobs['passed'] and blobs['total_dual_blob_rows']==766
articles=[];streams=[]
for sid,run in SIDRUN:
 W=B/f'run{run}-{sid}';m=load(W/'prepared-archive.json');p=load(W/'assets-primary.json');b=load(W/'assets-backup.json');s=load(W/'remote-video-byte-verification.json')
 assert p['asset_commit']==b['asset_commit'] and p['video_tree_sha']==b['video_tree_sha'] and s['passed']
 assert len(s['streams'])==2 and all(x['http_status']==200 and x['passed'] for x in s['streams']);streams+=s['streams']
 articles.append({**m['articles'][0],'asset_commit':p['asset_commit'],'video_tree_sha':p['video_tree_sha'],'asset_branch':p['asset_branch'],'prefix':m['prefix'],'files_in_each_repo':p['files'],'work_dir':str(W),'noncanonical_only':True})
closure={'status':'independent_three_passed_assets_dual_saved_verified','checked_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'Only preserving existing true-passed61/15/17 original media; canonical count remains55, source window belongs to root','permanently_canonical_archived_count_unchanged':55,'canonical_main':state['primary_main'],'canonical_backup':state['backup_head'],'articles':articles,'dual_actual_blob_rows':766,'actual_full_public_MP4_HTTP200_SHA256_streams':streams,'native_transport_run':43566043819,'native_transport_code_commit':'3ccfda56bb9119788786d89ac1459116975885c9','original_record53_subtree_preserved':'25cf175c31b6a1c5a35af4c0cfe3d203f4784359','native_inline_final_bytes_preserved_without_rerender_or_append':True,'source_programs_certificates_or_QC_gates_applied_or_changed':False,'review_release_tag_or_media_modified':False,'new_review_feedback_applied':False,'latest_user_pause_observed':'No new video/PDF generation while user finishes review; only original object transport and read verification performed','audio15_17_old_accepted_AAC_claimed_unchanged':False,'public_clip_scope':'Only four explicitly SHA-bound processed public MP4 control excerpts, no private PCM/GT/cache or mother bytes','source30_not_claimed_delivery_passed':True}
save(D/'independent-stage-closure.json',closure)
O=B/'independent-stage-records-61-15-17-20261114';prefix=pathlib.Path('视频修订定稿/归档记录/2026-11-14-独立已验资产61-15-17');pay=O/'payload';dest=pay/prefix
assert not O.exists();dest.mkdir(parents=True)
def add(source,rel):
 source=pathlib.Path(source);target=dest/rel;target.parent.mkdir(parents=True,exist_ok=True);assert not target.exists();shutil.copyfile(source,target)
for source in sorted(D.iterdir()):
 if source.is_file():
  assert source.suffix in {'.py','.json','.yml','.zip'} and 'request' not in source.name
  add(source,pathlib.Path('原生对象运输与只读实证')/source.name)
for sid,run in SIDRUN:
 W=B/f'run{run}-{sid}'
 for name in ['prepared-archive.json','payload-file-index.json','asset-local.json','assets-primary.json','assets-backup.json','remote-video-byte-verification.json']:
  add(W/name,pathlib.Path('逐篇独立资产回执')/sid/name)
add(B/'archive_batch.py',pathlib.Path('archive_batch.py'));change=load(B/'archive-helper-public-clips-provenance-20261114.json');add(B/'archive-helper-public-clips-provenance-20261114.json',pathlib.Path('归档公开控制片段变更记录.json'));add(change['before_path'],pathlib.Path('archive_batch.before-public-clips.py'));add(B/'CURRENT-ARCHIVE-STATE.json',pathlib.Path('正式55状态只读快照.json'))
(dest/'独立保存范围说明.md').write_text('# 既有合格原件的独立保存记录\n\n本记录只保全此前已通过完整验收的61、15、17三篇原件。两仓逐对象校验与六次完整MP4回读通过，未重新制作视频、PDF、插图、音频或片尾，未处理新的审核意见。\n\n正式主干累计仍为55篇。这里的三个孤立资产分支不等于正式56至58篇，不更新累计清单，不动主干、备仓专用源分支、master或审核Release。第15、17篇保留真实批准修音历史，并未声称旧AAC未变。\n')
files=[]
for p in sorted(dest.rglob('*')):
 if p.is_file():files.append({'repo_path':str(p.relative_to(pay)),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
save(O/'prepared-archive.json',{'prefix':str(prefix),'asset_branch':'codex/passed4k-staging-records-61-15-17-20261114','articles':[],'scope':'Existing passed payload preservation only; canonical count remains55'})
save(O/'payload-file-index.json',files)
print(json.dumps({'work_dir':str(O),'files':len(files),'bytes':sum(x['bytes'] for x in files),'canonical_count_still':55},ensure_ascii=False))
