"""Preserve exactly source30's found newer native for user102 review, never final."""
from pathlib import Path
import os,shutil
from archive_batch import load,write,digest,now
B=Path(__file__).resolve().parent
HP=Path('/dev/shm/review102-existing30-sourceQA/43562525001/archive-handoff.json')
HSHA='ac03f85dc1a3c55a5cbebdfb7236bb21e20cc9968ef5483f44098e77f3d61fc1'
DENY={'b9a257a23820944ee95d568b67d1cd78947b1c1814bb70dc99a45871f488f778','55026ce1b7cdb7e9c1a72da2f715e3d9e6e6f45050a8ddd575dc052b09dca872','bcb37d8930d804988c95da94b9cfeaaab2c7b026df96e6e4567f9b698ce88fbf'}
SAFE={'.json','.py','.sh','.md','.txt','.log','.csv','.diff','.patch','.yml','.yaml','.png','.jpg','.mp4','.zip'}
FLAGS={'review_only':True,'preview_only':True,'preview_delivery_eligible':True,'production_delivery_eligible':False,'final_user_acceptance':False,'active_final_replacement_authorized':False}
def main():
 assert digest(HP)==HSHA;h=load(HP);assert h['source_run']==43562525001 and h['kind']=='existing-native-V3-reviewed-source30-for-user102-review-only' and h['status']=='passed_existing_native_inline_source_and_media_V3_for_user102_review'
 assert h['review_delivery_eligible'] is True and h['user_final_acceptance_claimed'] is False and h['active_final_replacement_authorized'] is False and h['new_render_native_or_TTS_claimed'] is False
 assert len(h['articles'])==1;a=h['articles'][0];assert a['source_id']=='30' and a['new_id']=='55' and a['passed_per_article'] is True
 media=a['final_mp4'];assert media['bytes']==15667413 and media['sha256']=='9bb0be9d36cc219b8c1bdf286a1dc4b990a91160d8254cc55e323050ebed79b2'
 w=B/'run43562525001-30-user102-existing-native-review-only-v1';pay=w/'payload';prefix=Path('审核样片/2026-11-14-用户102-书55-源30-已有较新原生审核非定稿');bindings=[];destinations={}
 def add(p,rel,size=None,sha=None):
  p=Path(p);assert p.is_file() and p.suffix.lower() in SAFE and '__pycache__' not in p.parts
  assert not any(s in str(p) for s in ('CURRENT-ROOT-DELIVERY','ROOTSTATE','USER-REVIEW-2026-11-14-055.json','USER-REVIEW-2026-11-14-056.json'))
  actual=digest(p);assert actual not in DENY;assert size is None or p.stat().st_size==size,str(p);assert sha is None or actual==sha,str(p)
  assert str(rel) not in destinations or destinations[str(rel)]==actual;destinations[str(rel)]=actual;q=pay/rel;q.parent.mkdir(parents=True,exist_ok=True)
  if q.exists():assert digest(q)==actual
  else:
   try:os.link(p,q)
   except OSError:shutil.copyfile(p,q)
  bindings.append({'original_path':str(p.resolve()),'repo_path':str(rel),'bytes':p.stat().st_size,'sha256':actual})
 def spec(r,rel):add(r['path'],rel,r['bytes'],r['sha256'])
 for r in h['validation_files']:
  rel=r.get('relative_validation_path',r.get('validation_relative_path'));assert rel;spec(r,prefix/'真实完整源V3逐项证据'/rel)
 add(HP,prefix/'真实完整源V3逐项证据/archive-handoff.json');add(h['report_path'],prefix/'真实完整源V3逐项证据/report.json');add(h['input_path'],prefix/'真实完整源V3逐项证据/actual-inputs.json');add(a['validated_record'],prefix/'真实完整源V3逐项证据/validated-article-record.json');spec(a['section']['qc'],prefix/'真实完整源V3逐项证据/actual-QC.json');spec(h['purpose_and_word_class_caveat'],prefix/'审核用途与未应用词性提案/source30-review-purpose-caveat.json')
 for key,r in h['global_approved_evidence'].items():spec(r,prefix/'实际批准依据'/f'{key}-{Path(r["path"]).name}')
 codes=Path(h['code_snapshot_path'])
 for name,sha in h['tool_source_sha256'].items():add(codes/name,prefix/'实际冻结核验程序'/name,sha=sha)
 if (codes/'snapshot-manifest.json').exists():add(codes/'snapshot-manifest.json',prefix/'实际冻结核验程序/snapshot-manifest.json')
 inp=load(h['input_path']);ia=next(r for r in inp['articles'] if r['id']=='30')
 for n,r in enumerate(ia.get('evidence',[]),1):spec(r,prefix/'本篇显式原输入证据'/f'{n:03d}-{Path(r["path"]).name}')
 for role in ('request_source','final_source'):
  for key,r in a['section'][role].items():spec({**r,'path':str(Path(inp[role+'_root'])/r['path'])},prefix/('原请求源码' if role=='request_source' else '实际最终源码')/r['path'])
 video=prefix/'视频/55-source30-found-newer-native-user102-review-only-4K.mp4';spec(media,video);spec(a['canonical_source_mp4'],prefix/'实际官方原生底片'/Path(a['canonical_source_mp4']['path']).name);spec(a['immutable_native_zip'],prefix/'实际原生不可变ZIP'/Path(a['immutable_native_zip']['path']).name)
 for r in a['section']['stills']:spec(r,prefix/'实际原生五边界帧'/Path(r['path']).name)
 ill=a['section']['illustration'];spec(ill,prefix/'实际批准插图/4K.png');spec(ill['native_source'],prefix/'实际批准插图/original-book-image.png')
 for helper in (Path(__file__).name,'archive_batch.py','verify_source30_review_dual_asset_blobs.py','cleanup_source30_review_closed_own_bare.py','transport_source30_existing_review_assets.py'):add(B/helper,prefix/'运输程序'/helper)
 row={'source_id':'30','new_id':'55','frozen_book_order':'55','current_video_order':'55','source_run':43562525001,'video_repo_path':str(video),'bytes':media['bytes'],'sha256':media['sha256'],'passed_per_article':True,'source_quality_passed_per_article_original_role':True,**FLAGS,'new_normal18_or_new_final_acceptance_claimed':False,'existing_native_original_bytes_preserved':True}
 meta={'kind':'user102-exact-existing-source30-qualified-review-only-immutable-assets','prefix':str(prefix),'asset_branch':'codex/review102-assets-43562525001-30-found-newer-native-only-v1','created_utc':now(),'source_run':43562525001,'articles':[row],**FLAGS,'real_V3_handoff_sha256':HSHA,'original_handoff_kind':h['kind'],'original_handoff_status':h['status'],'material_source_bindings':bindings,'active_final_index_aliases_or_PDF_modified':False,'new_native_render_or_TTS_claimed':False,'tail_policy':'preserved_existing_source30'}
 write(pay/prefix/'review-archive-manifest.json',meta);write(w/'prepared-archive.json',meta);index=[{'repo_path':str(p.relative_to(pay)),'bytes':p.stat().st_size,'sha256':digest(p)} for p in sorted(pay.rglob('*')) if p.is_file()];write(w/'payload-file-index.json',index);print({'work_dir':str(w),'files':len(index),'logical_bytes':sum(r['bytes'] for r in index),'review_only':True,'active_final_replacement_authorized':False})
if __name__=='__main__':main()
