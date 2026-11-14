"""Prepare the compact print edition for lossless Git archival, without uploading."""
from pathlib import Path
import datetime,hashlib,json,shutil,subprocess

HERE=Path(__file__).resolve().parent
PREFIX=Path('考研学人印刷版/2026-11-13-v4')
PAYLOAD=HERE/'archive-payload'
DEST=PAYLOAD/PREFIX
OLD=Path('/workspace/work/booklet70')
SIGN=Path('/workspace/work/github-publication/target/朋克英语署名版/2026-11-13-v1')
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
 return h.hexdigest()
def put(src,rel):
 out=DEST/rel;out.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,out);assert sha(src)==sha(out);return out
def write(rel,data):
 p=DEST/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n');return p
def printed_fields(d):
 return {k:d[k] for k in ('no','title_en','title_zh','sentences')}
def manuscript_without_nonprinting_paragraph_locator(text):
 before,tail=text.split('## 速查表',1);lines=[]
 for line in tail.splitlines():
  if line.startswith('|'):
   cols=[v.strip() for v in line.strip().strip('|').split('|')]
   if len(cols)>=3:line='|'+ '|'.join(cols[:2])+'|'
  lines.append(line)
 return before+'## 速查表'+'\n'.join(lines)
def main():
 assembly=json.loads((HERE/'assembly-report.json').read_text());assert assembly['pages']==475
 for name in ('actual-content-readback-QA.json','book-visible-language-QA.json','actual-binding-QA.json','print-font-embedding-QA.json'):
  r=json.loads((HERE/name).read_text());assert r.get('passed'),(name,r.get('errors'))
 source=Path(assembly['signed_pdf']);assert sha(source)==assembly['signed_sha256'];dest=DEST/'整本';parts=dest/'parts';parts.mkdir(parents=True,exist_ok=True);chunk=90*1024*1024;part_records=[];whole=hashlib.sha256();total=0
 with source.open('rb') as f:
  index=1
  while True:
   data=f.read(chunk)
   if not data:break
   name=f'PUNK-ENGLISH-70-STORIES.pdf.part{index:03d}';path=parts/name;path.write_bytes(data);whole.update(data);total+=len(data);part_records.append({'index':index,'repo_path':str(PREFIX/'整本/parts'/name),'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()});index+=1
 manifest={'schema_version':1,'repository':'alienalgorithm/postgraduate-vocabulary','branch':'main','release_name':'考研学人.pdf','edition_policy':'compact_illustrated_bilingual_vocab_summary','title':'考研学人｜70篇趣味英语阅读','pages':assembly['pages'],'bytes':total,'sha256':whole.hexdigest(),'chunk_size_bytes':chunk,'storage':'original PDF bytes split without compression or recompression','manifest_repo_path':str(PREFIX/'整本/parts-manifest.json'),'parts':part_records,'pinned_commit_provided_by_archive_receipt':True,'publication_approval_repo_path':str(PREFIX/'核验/主册正式验收.json'),'book_source_freeze_manifest':str(PREFIX/'核验/生成时源稿冻结.json'),'provenance_engine_repo_path':'朋克英语署名版/2026-11-13-v1/provenance.py','default_hidden_attribution':True}
 write('整本/parts-manifest.json',manifest);put(HERE/'reassemble_book.py',Path('整本/reassemble_book.py'))
 snapshots=[];after_deltas=[];chapter_records=[];illustrations=[]
 build=json.loads((HERE/'build-report.json').read_text());signed_by_id={x['id']:x for x in build['chapters']}
 for n in range(1,71):
  no=f'{n:02d}';d=json.loads((HERE/'data'/f'{no}.json').read_text());sid=d['source_id'];snap=HERE/'source-snapshot'/sid;frozen_json=json.loads((snap/f'{sid}.json').read_text());live=Path(d['source_paths']['JSON']);current=json.loads(live.read_text());assert printed_fields(frozen_json)==printed_fields(current),(no,'Printed source changed after render')
  used={}
  for file in snap.iterdir():
   if file.suffix in ('.json','.py','.md'):
    put(file,Path('源稿')/sid/file.name);used[file.name]=sha(file)
  live_hashes={k:sha(p) for k,p in d['source_paths'].items()}
  frozen_md=snap/Path(d['source_paths']['MD']).name
  md_only_locator=(manuscript_without_nonprinting_paragraph_locator(frozen_md.read_text())==manuscript_without_nonprinting_paragraph_locator(Path(d['source_paths']['MD']).read_text()))
  assert live_hashes['MD']==d['source_hashes']['MD'] or md_only_locator,(no,'Printed manuscript changed after rendering; refresh the actual printed source first')
  if any(live_hashes[k]!=d['source_hashes'][k] for k in live_hashes):after_deltas.append({'source_id':sid,'new_id':no,'generation_time_hashes':d['source_hashes'],'current_public_source_hashes':live_hashes,'printed_fields_unchanged':True,'MD_change_only_in_nonprinting_paragraph_locator_column':live_hashes['MD']!=d['source_hashes']['MD'] and md_only_locator,'scope':'Post-render audio/verification metadata or nonprinted paragraph locators only; generation-time JSON/GEN/MD copies are preserved, not replaced retroactively.'})
  snapshots.append({'source_id':sid,'new_id':no,'generation_time_files_SHA256':used,'printed_source_fields_unchanged_since_generation':True,'illustration_sha256':d['source_hashes']['illustration']})
  put(HERE/'data'/f'{no}.json',Path('制作程序/data')/f'{no}.json')
  ch=signed_by_id[no];signed=HERE/'signed/chapters'/no/Path(ch['pdf']).name;proof=ch['provenance'];assert sha(signed)==proof['sha256'];out=put(signed,Path('分篇PDF')/f'{no} {d["title_zh"]}.pdf');chapter_records.append({'new_id':no,'source_id':sid,'title_zh':d['title_zh'],'title_en':d['title_en'],'repo_path':str(out.relative_to(PAYLOAD)),'bytes':out.stat().st_size,'sha256':sha(out),'pages':ch['pages'],'provenance':proof})
  put(HERE/'unsigned/chapters'/no/'layout-and-content-qc.json',Path('核验/逐章')/f'{no}-layout-and-content.json')
  image=Path(d['illustration']);out=put(image,Path('插图')/f'{no}.png');illustrations.append({'new_id':no,'source_id':sid,'repo_path':str(out.relative_to(PAYLOAD)),'sha256':sha(out),'original_source_sha256':d['source_hashes']['illustration'],'same_approved_artwork':True})
  info=image.with_suffix('.json')
  if info.is_file():put(info,Path('插图/原生成记录')/f'{sid}.json')
 for rec in json.loads((HERE/'volumes-report.json').read_text()):put(rec['signed_pdf'],Path('分册PDF')/Path(rec['signed_pdf']).name)
 for file in HERE.glob('*.py'):put(file,Path('制作程序')/file.name)
 put(OLD/'cjk_layout.py',Path('制作程序/批准版式/cjk_layout.py'))
 for file in (HERE/'source-snapshot').glob('*/gen*.py'):assert file.name.startswith('gen')
 for font in (OLD/'fonts').glob('*.ttf'):put(font,Path('制作程序/批准版式/fonts')/font.name)
 for font in Path('/usr/share/fonts/truetype/liberation').glob('*.ttf'):
  if font.name.startswith(('LiberationSerif-','LiberationSans-')):put(font,Path('制作程序/批准版式/fonts')/font.name)
 put(SIGN/'provenance.py',Path('制作程序/来源署名/provenance.py'));put(SIGN/'reveal_attribution.py',Path('制作程序/来源署名/reveal_attribution.py'))
 for file in (SIGN/'字体').iterdir():
  if file.is_file():put(file,Path('制作程序/来源署名/字体')/file.name)
 put(SIGN/'封面/PUNK-ENGLISH-BOOK-COVER.png',Path('封面/前封.png'));put(HERE/'cover/back-cover-watercolor.png',Path('封面/封底.png'));put(HERE/'frontmatter-approved.json',Path('书稿/前言与封底批准稿.json'))
 for name in ('scope-correction.json','order-source.json','book-illustrations70.json','conversion-report.json','actual-content-readback-QA.json','book-visible-language-QA.json','actual-binding-QA.json','print-font-embedding-QA.json','assembly-report.json','volumes-report.json','build-report.json'):
  put(HERE/name,Path('核验')/name)
 for file in (HERE/'book-previews').glob('*.png'):put(file,Path('预览/整本')/file.name)
 for no in ('01','04','08','17','18','20'):
  file=HERE/'unsigned/chapters'/no/'compact-contact.png'
  if file.is_file():put(file,Path('预览/章样')/f'{no}-compact-contact.png')
 freeze={'edition_policy':manifest['edition_policy'],'generation_time_source_copies_preserved':True,'actual_printed_data_from_PAY':True,'sources':snapshots,'post_render_metadata_only_deltas':after_deltas,'updated_story_body_from_old_booklet_rewrites':False,'source_notes_preserved_as_source_only':True,'source_sentence_analysis_or_exercises_printed':False,'superseded_799_page_draft_published':False}
 write('核验/生成时源稿冻结.json',freeze);write('核验/70分篇与书内顺序.json',chapter_records);write('核验/70插图对应.json',illustrations)
 requirements=subprocess.check_output([str(HERE/'.venv/bin/python'),'-m','pip','freeze'],text=True);(DEST/'制作程序/requirements.txt').write_text(requirements)
 approval=json.loads((HERE/'publication-approval.json').read_text());assert approval['status']=='passed' and approval['publication_approved'] is True and approval['pdf_sha256']==manifest['sha256'] and approval['pdf_bytes']==manifest['bytes'] and approval['pages']==manifest['pages'];put(HERE/'publication-approval.json',Path('核验/主册正式验收.json'))
 (DEST/'署名图层查看说明.txt').write_text('本版PDF每页都有默认关闭的“来源署名｜朋克英语”图层。普通阅读和默认打印保持批准画面。\n\nAdobe Acrobat：打开侧边栏“图层”，在“来源署名｜朋克英语”旁开启显示。\n福昕PDF：打开“视图”中的图层面板，开启同名图层。\n也可运行：python 制作程序/来源署名/reveal_attribution.py 输入.pdf 显示署名副本.pdf\n请使用独立输出文件，不覆盖正常阅读原件。\n\n本册475页的默认像素不变、开启后可见及字体嵌入核查均记录在“核验”目录。来源署名是可主动显示的溯源记录，不是不可删除的版权锁。\n')
 (DEST/'归档与复组说明.txt').write_text('《考研学人》475页主册，B5 176×250毫米。内容为批准插图、当前中英正文、重点词与短语、篇末简述，以及另行批准的封面、第二页前言与封底。未印入句子解析、视频小字章节或额外练习答案；这些原始资料保存在源稿中供后续使用。799页扩展草稿没有发布，也没有混入本目录。\n\n完整PDF原始字节超过Git单文件限制，仓库保存不压缩的原字节分片。下载四个parts和parts-manifest.json后，在仓库根目录执行：\npython 考研学人印刷版/2026-11-13-v4/整本/reassemble_book.py 考研学人印刷版/2026-11-13-v4/整本/parts-manifest.json --repo-root . --output 考研学人.pdf\n程序逐片核对bytes和SHA-256，再核对完整文件，不重编码或降低插图质量。正式Release仅在全套70部视频通过后提供同一完整字节PDF和视频；源码、插图和详细核验留在仓库。\n\n源稿是生成当时真实JSON/GEN/MD副本。后续仅音频核验metadata或非打印段号列的变化另有记录，未把事后源码冒称生成时源码。全部原彩图、程序、署名引擎、字体、分篇/分册PDF与核查记录一并保留；本次没有改写历史版本。\n')
 record={'prefix':str(PREFIX),'payload_root':str(PAYLOAD),'edition_policy':manifest['edition_policy'],'book':manifest,'PDFs':{'book_parts':len(part_records),'signed_chapters':70,'signed_volumes':7},'old_799_page_PDFs_excluded':True,'release_created':False,'remote_upload_done':False,'pending_publication_approval_record':False,'publication_approval_bound_to_exact_book':True,'publication_approval_sha256':sha(HERE/'publication-approval.json'),'largest_blob_bytes':max(p.stat().st_size for p in DEST.rglob('*') if p.is_file())}
 assert record['largest_blob_bytes']<=90*1024*1024
 write('archive-manifest.json',record)
 files=[{'repo_path':str(p.relative_to(PAYLOAD)),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(DEST.rglob('*')) if p.is_file() and p.name!='files-SHA256.json'];write('files-SHA256.json',{'files':files,'count':len(files),'scope':'All archived payload files except this self-referential index.'})
 (HERE/'archive-plan.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'prefix':str(PREFIX),'book':manifest,'archive_files':len(files),'largest_blob_bytes':record['largest_blob_bytes']},ensure_ascii=False),flush=True)
if __name__=='__main__':main()
