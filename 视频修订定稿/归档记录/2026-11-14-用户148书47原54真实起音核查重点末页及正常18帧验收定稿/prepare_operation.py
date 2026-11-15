"""Prepare the small adjacent record for already verified archive assets.

No rendering, quality changes or main-ref writes. This only packages existing
receipts and updates the cumulative index using archive_batch.py's same code.
"""
from pathlib import Path
import argparse,datetime,hashlib,json,shutil,subprocess
import archive_revision_policy as revisions
import build_final_alias_plan as alias_builder
import final_alias_git

def load(p):return json.loads(Path(p).read_text())
def save(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def main():
 p=argparse.ArgumentParser();p.add_argument('--work-dir',required=True);p.add_argument('--batch',required=True);p.add_argument('--asset-branch',required=True);p.add_argument('--previous-inventory',required=True);p.add_argument('--article-work-dir',action='append',required=True);p.add_argument('--attach',action='append',default=[]);p.add_argument('--attach-tree',action='append',default=[]);p.add_argument('--revision-authorization');a=p.parse_args()
 assert '/' not in a.batch and a.batch not in ('.','..')
 out=Path(a.work_dir).resolve();prefix=Path('视频修订定稿')/'归档记录'/a.batch;dst=out/'payload'/prefix;dst.mkdir(parents=True,exist_ok=True)
 helper=Path(__file__).with_name('archive_batch.py');previous=Path(a.previous_inventory);prior=load(previous);streams=[];articles=[]
 auth=revisions.authorization(a.revision_authorization)
 for raw in a.article_work_dir:
  w=Path(raw).resolve();meta=load(w/'prepared-archive.json');primary=load(w/'assets-primary.json');backup=load(w/'assets-backup.json');actual=load(w/'remote-video-byte-verification.json')
  assert primary['asset_commit']==backup['asset_commit'] and primary['video_tree_sha']==backup['video_tree_sha']
  assert actual['passed'] and all(x['passed'] and x['http_status']==200 for x in actual['streams'])
  streams+=actual['streams']
  for x in meta['articles']:articles.append({**x,'asset_commit':primary['asset_commit'],'frozen_archive_subtree':primary['video_tree_sha'],'archive_prefix':meta['prefix'],'payload_files_per_repository':primary['files'],'validation_handoff_status':meta.get('validation_handoff_status')})
  if auth or 'video_order_overlay' in load(previous):
   incoming=[{**x,'asset_commit':primary['asset_commit'],'archive_prefix':meta['prefix']} for x in meta['articles']]
   batch={'prefix':meta['prefix'],'asset_commit':primary['asset_commit'],'source_ids':[x['source_id'] for x in meta['articles']]}
   save(w/'cumulative-inventory.json',revisions.merge_inventory(load(previous),incoming,batch,auth))
  else:subprocess.run(['python',str(helper),'index','--work-dir',str(w),'--existing',str(previous)],check=True)
  previous=w/'cumulative-inventory.json'
 inventory=load(previous);shutil.copyfile(previous,dst/'累计清单快照.json')
 if auth:
  authdir=dst/'用户已完成审核修订授权';authdir.mkdir()
  shutil.copyfile(a.revision_authorization,authdir/Path(a.revision_authorization).name)
  for permit in auth['document']['authorized_revisions']:
   review=Path(permit['review_record']['path']);shutil.copyfile(review,authdir/review.name)
 save(dst/'远端MP4实字节核验.json',{'passed':True,'checked_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'Only the listed actual passed final articles; complete public MP4 bytes read in both repositories','streams':streams,'temporary_videos_written':False})
 save(dst/'本批保存范围与来源.json',{'previous_archived_passed_count':prior['archived_passed_count'],'resulting_archived_passed_count':inventory['archived_passed_count'],'remaining_not_claimed_passed':inventory['remaining_not_claimed_passed'],'articles':articles,'original_outer_job_status_preserved_without_rewriting':True,'separately_derived_final_GEN_not_claimed_runtime':True,'observed_original_collector_sources_kept_with_existing_origin_labels':True,'archivist_changes_audio_or_body':False,'archivist_changes_quality_checker_or_threshold':False,'release_created':False,'whole70_passed_claimed':False})
 for raw in a.attach:
  src=Path(raw).resolve();target=dst/src.name;assert not target.exists();shutil.copyfile(src,target)
 for raw in a.attach_tree:
  source=Path(raw).resolve();tree=dst/source.name;assert source.is_dir() and not tree.exists()
  for src in sorted(source.rglob('*')):
   if not src.is_file() or '__pycache__' in src.parts:continue
   target=tree/src.relative_to(source);target.parent.mkdir(parents=True,exist_ok=True)
   if src.suffix in ('.png','.jpg','.mp4','.zip'):target.hardlink_to(src)
   else:shutil.copyfile(src,target)
 for src in (helper,Path(__file__),Path(revisions.__file__),Path(alias_builder.__file__),Path(final_alias_git.__file__)):
  target=dst/src.name;assert not target.exists();shutil.copyfile(src,target)
 (dst/'归档说明.md').write_text(f'# 实际合格成片的滚动归档\n\n本批仅保存既有完整单篇核验通过的实际成片，原任务状态与素材来源逐项保留，未将派生文件冒称运行时观察。两仓隔离assets经逐blob核对，完整MP4已实际取流重算SHA；主干按fresh HEAD合并冻结子树与累计清单。旧版成片、475页主册及其他源稿均保留，master不动。\n\n本批归档后累计{inventory["archived_passed_count"]}/70，尚未宣称全70完成或创建Release。影音质量判断沿用原实际核验，归档程序不改声画、源稿或阈值。\n')
 files=[]
 for q in sorted(dst.rglob('*')):
  if q.is_file():files.append({'repo_path':str(q.relative_to(out/'payload')),'bytes':q.stat().st_size,'sha256':hashlib.sha256(q.read_bytes()).hexdigest()})
 save(out/'prepared-archive.json',{'prefix':str(prefix),'asset_branch':a.asset_branch,'revision_authorization_sha256':auth['sha256'] if auth else None})
 save(out/'payload-file-index.json',files)
 print(json.dumps({'work_dir':str(out),'prefix':str(prefix),'files':len(files),'bytes':sum(x['bytes'] for x in files),'article_source_ids':[x['source_id'] for x in articles],'resulting_count':inventory['archived_passed_count']},ensure_ascii=False))
if __name__=='__main__':main()
