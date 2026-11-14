"""Preserve two independently accepted real productions without altering them."""
from pathlib import Path
import datetime, hashlib, json, os, shutil

HERE=Path(__file__).resolve().parent
PAY=HERE/'payload'
PREFIX=Path('视频修订定稿/2026-11-14-已验收2篇-run43523430839')
BASE=Path('/workspace/work/video-audit70-20261113/actual-passed-43523430839')
VAL=Path('/workspace/work/video-revision-delivery/actual53-64-validation')
TOOLS=Path('/workspace/work/video-revision-delivery/frozen-v3-actual53-64-code')
PDF=Path('/workspace/work/punk-print-20261113-v4-compact')
handoff=json.loads((VAL/'archive-handoff.json').read_text())
assert handoff['status']=='passed_actual_two_article_section_for_permanent_archive'
assert handoff['complete70_release_validated'] is False
report=json.loads((VAL/'report.json').read_text())
assert report['status']=='passed_actual_two_article_interface_only'
assert {(r['id'],r['new_id']) for r in report['actual_articles']}=={('53','35'),('64','63')}
art=json.loads((PDF/'book-illustrations70.json').read_text())['illustrations']
catalog={x['source_id']:x for x in art}
rows=[]

def digest(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def add(src,rel,size=None,sha=None):
 src=Path(src);dst=PAY/rel
 assert src.is_file() and not src.is_symlink(),str(src)
 actual=digest(src)
 assert size is None or src.stat().st_size==size,str(src)
 assert sha is None or actual==sha,str(src)
 assert src.stat().st_size<90*1024*1024,str(src)
 dst.parent.mkdir(parents=True,exist_ok=True)
 if dst.exists():assert digest(dst)==actual
 else:os.link(src,dst)
 rows.append({'repo_path':str(rel),'bytes':src.stat().st_size,'sha256':actual,'source_path':str(src)})
def spec(row,rel):add(row['path'],rel,row['bytes'],row['sha256'])

for row in handoff['validation_files']:
 spec(row,PREFIX/'V3逐项核验'/row['relative_validation_path'])
add(VAL/'archive-handoff.json',PREFIX/'V3逐项核验/archive-handoff.json')
add(BASE/'actual-illustrated-tail53-64-handoff.json',PREFIX/'尾部实际核验/actual-illustrated-tail53-64-handoff.json')
for name,sha in handoff['tool_source_sha256'].items():
 add(TOOLS/name,PREFIX/'制作与核验程序/V3本次实际验证代码'/name,sha=sha)
add(TOOLS/'snapshot-manifest.json',PREFIX/'制作与核验程序/V3本次实际验证代码/snapshot-manifest.json')
helper=Path('/workspace/work/video-audit70-20261113/illustrated-tail/illustrated_tail.py')
add(helper,PREFIX/'制作与核验程序/illustrated_tail.py',sha='dc204b91415e28297b844e9666087b0e23e67194944b359cb5fb5ddbca0f1208')
for name,row in handoff['global_approved_evidence'].items():spec(row,PREFIX/'批准依据'/Path(row['path']).name)

articles=[]
for item in handoff['articles']:
 sid=item['source_id'];nid=item['new_id'];book=catalog[sid]
 assert book['new_id']==nid and item['passed_per_article']
 title=book['title_zh'];section=item['section'];stem=f'{nid} {title}'
 spec(item['final_mp4'],PREFIX/'视频'/f'{stem}.mp4')
 spec(item['canonical_source_mp4'],PREFIX/'实际官方新底片'/f'{stem}（未插图底片）.mp4')
 spec(item['immutable_native_zip'],PREFIX/'原始Actions产物'/f'original{sid}-run43523430839-passed-output.zip')
 for row in section['stills']:spec(row,PREFIX/'实际解码帧'/nid/Path(row['path']).name)
 spec(section['illustration'],PREFIX/'插图'/f'{stem}-4K.png')
 spec(section['illustration']['native_source'],PREFIX/'插图'/f'{stem}-书内批准原图.png')
 for src in sorted((BASE/sid/'files').iterdir()):
  if src.suffix in ('.json','.png'):add(src,PREFIX/'官方原产物解包'/sid/src.name)
 add(BASE/sid/f'{sid}-visual-review.json',PREFIX/'尾部实际核验'/f'{sid}-visual-review.json')
 add(BASE/sid/f'{sid}-illustrated-tail-verification.json',PREFIX/'尾部实际核验'/f'{sid}-illustrated-tail-verification.json')
 add(BASE/sid/'illustrated-tail.log',PREFIX/'尾部实际核验'/f'{sid}-illustrated-tail.log')
 add(BASE/sid/'retrieval-receipt.json',PREFIX/'原始Actions产物'/f'{sid}-retrieval-receipt.json')
 articles.append({'source_id':sid,'new_id':nid,'title_zh':title,'title_en':book['title_en'],
                  'video_repo_path':str(PREFIX/'视频'/f'{stem}.mp4'),
                  'bytes':item['final_mp4']['bytes'],'sha256':item['final_mp4']['sha256'],
                  'passed_per_article':True,'final_GEN_origin':'derived_after_final_QC',
                  'runtime_GEN_observed':False,'final_MD_origin':'request_manuscript_with_verified_final_source_equivalence'})

for name in ['verify_remote_book_stream.py','remote-book-stream-verification.json',
             'cleanup_owned_archive_duplicates.py','cleanup-owned-duplicates-receipt.json']:
 add(PDF/name,Path('考研学人印刷版/归档记录/2026-11-13-v4')/name)

summary={'schema_version':1,'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'scope':'Only two actual new accepted4K videos, source53->book35 and source64->book63; not full70 completion.',
 'source_run':43523430839,'actual_passed_video_count':2,'total_requested':70,
 'remaining_not_claimed_passed':68,'release_created':False,'old_history_preserved':True,
 'articles':articles,'video_sequence':'English-Chinese body -> approved book illustration60frames -> approved summary60frames -> end',
 'body_and_AAC':'Actual V3 packet evidence verifies body coded pictures and AAC payload/rational timings retained exactly.',
 'provenance_limit':'Actual final working JSON is observed in immutable native ZIP. Final GEN is honestly derived after QC with unchanged official-helper fullJSON roundtrip, not an exported runtime GEN. Request MD is retained with verified final-source equivalence.',
 'frozen_book_mapping_commit':handoff['frozen_primary_mapping_commit'],
 'original_handoff_status_was_not_remote_publication':'Snapshots report false for archived/published at validation time; this later archive manifest records preservation only.',
 'material_source_bindings':rows,'all_payload_file_hashes':'files-SHA256.json'}
dest=PAY/PREFIX/'archive-manifest.json';dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
readme='''# 本轮已验收的两部4K视频\n\n这里只归档原53→书序35《不合拍的风：塔科马大桥的陨落》、原64→书序63《没有到来的零日》的真实新制作结果。两部均已通过原官方制作核验及V3独立逐项实物核验。不能据此宣称70部全部完成，本目录没有创建新Release，也没有覆盖旧历史。\n\n正式文件在“视频”目录，编号和中文篇名与475页书的最新顺序相同。正文后为同篇批准书图60帧（2秒），随后批准简述60帧（2秒）。实际解码首末帧、原始Actions ZIP、原官方状态、逐包声画证明、实际工作JSON、原请求及完整派生证据均保留。\n\n原始producer没有导出运行时GEN和MD。这里的最终GEN标记为derived_after_final_QC，并有未改官方helper的完整JSON回环记录；MD是原请求文稿，核实与最终工作JSON可见内容等价。不得把它们称为观察到的运行时文件。源缓存、模型、私人GT和原始私人PCM没有归档。\n\n各件精确字节和SHA-256见archive-manifest.json。V3报告中的未远端发布字段是验证当时的真实状态，后来归档并不回写这些原始证据。完整交付仍须等70部视频全部实际验收后，才建立只含整本PDF和70部视频的一次新Release。\n'''
(PAY/PREFIX/'README.md').write_text(readme)
add(Path(__file__),PREFIX/'制作与核验程序/prepare_archive.py')
if (HERE/'upload_assets.py').exists():add(HERE/'upload_assets.py',PREFIX/'制作与核验程序/upload_assets.py')
hashfile=PAY/PREFIX/'files-SHA256.json'
allfiles=sorted(x for x in PAY.rglob('*') if x.is_file() and x!=hashfile)
index=[]
for q in allfiles:index.append({'repo_path':str(q.relative_to(PAY)),'bytes':q.stat().st_size,'sha256':digest(q)})
hashfile.write_text(json.dumps({'excludes_only_itself':True,'files':index},ensure_ascii=False,indent=2)+'\n')
index.append({'repo_path':str(hashfile.relative_to(PAY)),'bytes':hashfile.stat().st_size,'sha256':digest(hashfile)})
index.sort(key=lambda x:x['repo_path'])
(HERE/'payload-file-index.json').write_text(json.dumps(index,ensure_ascii=False,indent=2)+'\n')
result={'video_prefix':str(PREFIX),'PDF_supplement_prefix':'考研学人印刷版/归档记录/2026-11-13-v4',
 'files':len(index),'bytes':sum(x['bytes'] for x in index),'largest':max(x['bytes'] for x in index),
 'articles':articles,'index_sha256':digest(HERE/'payload-file-index.json')}
(HERE/'prepared-archive.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(result,ensure_ascii=False,indent=2),flush=True)
