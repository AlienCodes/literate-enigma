"""Archive only two exact, frozen user102 review handoffs; never install finals."""
from pathlib import Path
import argparse,hashlib,json,os,shutil
from archive_batch import digest,load,write,now
HERE=Path(__file__).resolve().parent
CONTRACT={
 '66':{'hsha':'1b9169c4682491c1b0c816725b2f883a23cfd79cdf00a227bb6fc5805de43fd1','book':'57','sha':'621662dc2de3b06b8c6ffb2022d0f8d5a3cf12cb17e1717e49fe49bdf48d9b3d','bytes':14708247,'kind':'authorized-review102-source66-hold18-local-tail'},
 '69':{'hsha':'fc6532db184f2c58de7eef5acc880b87567cf268f72559e28db69be62b5649b9','book':'56','sha':'d646e0c2f14d6075f4c6fb066ff9c0e1f1887a65c347f4a81c1de0cfddc10b75','bytes':16672746,'kind':'authorized-review102-source69-hold18-local-tail'}}
DENY={'b9a257a23820944ee95d568b67d1cd78947b1c1814bb70dc99a45871f488f778','55026ce1b7cdb7e9c1a72da2f715e3d9e6e6f45050a8ddd575dc052b09dca872','bcb37d8930d804988c95da94b9cfeaaab2c7b026df96e6e4567f9b698ce88fbf'}
SAFE={'.json','.py','.sh','.md','.txt','.log','.csv','.diff','.patch','.yml','.yaml','.png','.jpg','.mp4','.zip'}
FLAGS={'review_only':True,'preview_only':True,'preview_delivery_eligible':True,'production_delivery_eligible':False,'final_user_acceptance':False,'active_final_replacement_authorized':False}

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--source',choices=CONTRACT,required=True);a=ap.parse_args();sid=a.source;c=CONTRACT[sid]
 hp=Path(f'/dev/shm/review{sid}-hold18-intake/validated/{sid}/review-handoff.json');assert digest(hp)==c['hsha'];h=load(hp)
 assert h['kind']==c['kind'] and h['status'].startswith('passed_actual_review102_') and all(h.get(k) is v for k,v in FLAGS.items())
 assert h['local_postprocessing_only'] is True and h['new_native_job_or_TTS_claimed'] is False
 assert h['user_individual_finalization_authorized'] is False and h['normal70_final_assembly_eligible'] is False
 assert len(h['articles'])==1;art=h['articles'][0];assert art['source_id']==sid and art['new_id']==c['book'] and art['preview_passed'] is True and art['passed_per_article'] is False
 assert (art['preview_mp4']['bytes'],art['preview_mp4']['sha256'])==(c['bytes'],c['sha'])
 w=HERE/f'run{h["source_run"]}-{sid}-user102-review18-only-v1';pay=w/'payload'
 prefix=Path('审核样片')/f'2026-11-14-用户102-书{c["book"]}-源{sid}-最新0.6秒审核非定稿'
 bindings=[];destinations={}
 def add(source,relative,size=None,sha=None):
  source=Path(source);assert source.is_file(),str(source)
  assert source.suffix.lower() in SAFE and '__pycache__' not in source.parts
  assert not any(s in str(source) for s in ('CURRENT-ROOT-DELIVERY','ROOTSTATE','USER-REVIEW-2026-11-14-055.json','USER-REVIEW-2026-11-14-056.json'))
  actual=digest(source);assert actual not in DENY
  assert size is None or source.stat().st_size==size,str(source);assert sha is None or actual==sha,str(source)
  rp=str(relative);assert rp not in destinations or destinations[rp]==actual,rp;destinations[rp]=actual
  target=pay/relative;target.parent.mkdir(parents=True,exist_ok=True)
  if target.exists():assert digest(target)==actual
  else:
   try:os.link(source,target)
   except OSError:shutil.copyfile(source,target)
  bindings.append({'original_path':str(source.resolve()),'repo_path':rp,'bytes':source.stat().st_size,'sha256':actual})
 def spec(row,relative):
  original=Path(row['path'])
  if sid=='66' and original==Path('/dev/shm/source66-review102-hold18-20261114/media/upstream/66/66-review18-upstream-with-actual-source-V3-reference.json') and row['sha256']=='ad79da6ed5ad2eec6f15c3aa84e633b91e970fa1ed7e17e64c14eaa703587582':
   reconstructed=Path('/dev/shm/review66-hold18-intake/history/66-upstream-ad79-exact-reconstructed.json');assert digest(reconstructed)==row['sha256'] and reconstructed.stat().st_size==row['bytes']
   add(reconstructed,relative,row['bytes'],row['sha256']);bindings[-1].update(frozen_original_spec_path=str(original),historical_exact_SHA_reconstruction_not_claimed_as_untouched_recovered_original=True)
  else:add(row['path'],relative,row['bytes'],row['sha256'])
 for row in h['validation_files']:
  rel=row.get('relative_validation_path',row.get('validation_relative_path'));assert rel;spec(row,prefix/'真实逐项完整V3'/rel)
 add(hp,prefix/'真实逐项完整V3/review-handoff.json');add(h['report_path'],prefix/'真实逐项完整V3/whole-review-report.json');add(h['input_path'],prefix/'真实逐项完整V3/actual-review-inputs.json')
 add(art['validated_record'],prefix/'真实逐项完整V3/validated-article-record.json');spec(art['section']['qc'],prefix/'真实逐项完整V3/actual-current-QC.json');spec(h['inherited_full_V3'],prefix/'继承原生完整源QA/archive-handoff.json')
 codes=Path(h['code_snapshot_path'])
 for name,sha in h['tool_source_sha256'].items():add(codes/name,prefix/'实际冻结核验程序'/name,sha=sha)
 if (codes/'snapshot-manifest.json').exists():add(codes/'snapshot-manifest.json',prefix/'实际冻结核验程序/snapshot-manifest.json')
 for key,row in h['global_approved_evidence'].items():spec(row,prefix/'实际批准依据'/f'{key}-{Path(row["path"]).name}')
 inp=load(h['input_path']);ia=next(x for x in inp['articles'] if x['id']==sid)
 for n,row in enumerate(ia.get('evidence',[]),1):spec(row,prefix/'本篇显式实际证据'/f'{n:03d}-{Path(row["path"]).name}')
 sr=Path(h['inherited_full_V3']['path']).parent
 for role in ('request_source','final_source'):
  for key,row in art['section'][role].items():
   actual={**row,'path':str(sr/role.replace('_','-')/row['path'])};spec(actual,prefix/('原请求源码' if role=='request_source' else '实际最终源码')/row['path'])
 if sid=='66':
  history=Path('/dev/shm/review66-hold18-intake/history')
  for name in ('66-upstream-ad79-exact-reconstructed.json','66-frozen-input-ad79-and-current-adapter6173-corrective-sidecar.json','66-frozen-input-ad79-and-current-adapter6173-metadata-only.diff'):
   f=history/name
   if f.exists():add(f,prefix/'仅元数据历史原哈希及当前准确来由'/name)
  current=Path('/dev/shm/source66-review102-hold18-20261114/media/upstream/66/66-review18-upstream-with-actual-source-V3-reference.json');add(current,prefix/'仅元数据历史原哈希及当前准确来由/current-6173-source-V3-reference.json',2666,'617320f60dd3e440423cf5b4db0beee0769e099237a6bfbcafcbb8139e8b6086')
  add(HERE/'prepare_review102_exact_assets.py',prefix/'运输程序/initial-collector-before-exact-ad79-historical-resolution.py')
 media=art['preview_mp4'];video=prefix/'视频'/f'{c["book"]}-source{sid}-latest-user102-review-only-4K.mp4';spec(media,video)
 spec(art['canonical_source_mp4'],prefix/'实际原生底片'/Path(art['canonical_source_mp4']['path']).name)
 spec(art['immutable_native_zip'],prefix/'原生不可变产物'/Path(art['immutable_native_zip']['path']).name)
 for n,row in enumerate(h.get('additional_public_media_inputs',[]),1):spec(row,prefix/'实际公开中间视频输入'/f'{n:02d}-{Path(row["path"]).name}')
 for row in art['section']['stills']:spec(row,prefix/'实际最终五边界帧'/Path(row['path']).name)
 ill=art['section']['illustration'];spec(ill,prefix/'实际批准插图/actual4K.png');spec(ill['native_source'],prefix/'实际批准插图/original-book-illustration.png')
 add(Path(__file__),prefix/'运输程序'/Path(__file__).name);add(HERE/'archive_batch.py',prefix/'运输程序/archive_batch.py');add(HERE/'original-source28-collector-reference.py',prefix/'运输程序/original-source28-collector-reference.py')
 for helper in ('verify_review102_dual_asset_blobs.py','cleanup_review102_closed_own_bare.py','transport_exact_review102_assets.py'):add(HERE/helper,prefix/'运输程序'/helper)
 row={'source_id':sid,'new_id':c['book'],'frozen_book_order':c['book'],'current_video_order':c['book'],'video_repo_path':str(video),'bytes':media['bytes'],'sha256':media['sha256'],'source_run':h['source_run'],'passed_per_article':False,'preview_passed':True,**FLAGS,'normal_final_delivery_claimed':False}
 meta={'kind':'user102-exact-two-qualified-latest-review-only-immutable-assets','created_utc':now(),'prefix':str(prefix),'asset_branch':f'codex/review102-assets-{h["source_run"]}-{sid}-hold18-only-v1','source_run':h['source_run'],'articles':[row],**FLAGS,'real_V3_handoff_sha256':c['hsha'],'original_handoff_kind':h['kind'],'original_handoff_status':h['status'],'material_source_bindings':bindings,'native_run_created_or_claimed_by_archive':False,'active_final_index_aliases_or_PDF_modified':False}
 write(pay/prefix/'review-archive-manifest.json',meta);write(w/'prepared-archive.json',meta)
 index=[{'repo_path':str(p.relative_to(pay)),'bytes':p.stat().st_size,'sha256':digest(p)} for p in sorted(pay.rglob('*')) if p.is_file()]
 assert all(r['sha256'] not in DENY for r in index);write(w/'payload-file-index.json',index)
 print(json.dumps({'work_dir':str(w),'files':len(index),'logical_bytes':sum(r['bytes'] for r in index),'review_only':True,'production_delivery_eligible':False},ensure_ascii=False))
if __name__=='__main__':main()
