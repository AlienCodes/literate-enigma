"""Assemble fresh chapters, formal frontmatter and matching approved covers.

The front cover is physical page1 and the approved preface is physical page2.
Process/version/provenance reports stay outside the book. Attribution is added
only after all pages and links are final, using the required repository engine.
"""
from __future__ import annotations
import argparse, hashlib, importlib.util, io, json, re
from html import escape
from pathlib import Path
import fitz
from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
import build_print as B

HERE=Path(__file__).resolve().parent
REPO=Path('/workspace/work/github-publication/target')
FRONT=REPO/'朋克英语署名版/2026-11-13-v1/封面/PUNK-ENGLISH-BOOK-COVER.png'
BACK=HERE/'cover/back-cover-watercolor.png'
W,H,M,CW=B.W,B.H,B.M,B.CW

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def write(path,data):path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
def para(c,text,x,top,width,font,size,leading,color=B.INK):
 p,h=B.measure(text,width,font,size,leading,font.startswith('CN'),color)
 if top-h<53:raise ValueError(('Frontmatter exceeds B5 safe area',top,h,text[:80]))
 p.drawOn(c,x,top-h);return top-h
def header(c,title):
 c.setFillColor(B.PAPER);c.rect(0,0,W,H,stroke=0,fill=1);B.label(c,'考研学人',M,H-37,size=8.4,color=B.MUTED);B.label(c,title,M,H-79,'CNB',22,B.FOREST)
def footer(c,page):
 B.rule(c,M,36,CW);B.label(c,'考研学人',M,22,size=8.1,color=B.MUTED);c.setFont('SANS',8.7);c.setFillColor(B.MUTED);c.drawRightString(W-M,22,str(page))

def frontmatter(chapters,approved,path):
 assert approved['title']=='考研学人' and approved['subtitle']=='70篇趣味英语阅读'
 assert isinstance(approved['preface_paragraphs'],list) and approved['preface_paragraphs']
 assert FRONT.is_file() and BACK.is_file(),'Use actual approved artwork; no placeholder cover'
 starts=[];at=10
 for ch in chapters:starts.append(at);at+=ch['pages']
 c=canvas.Canvas(str(path),pagesize=(W,H),pageCompression=1,invariant=1);c.setTitle('考研学人');c.setAuthor('朋克英语')
 c.drawImage(str(FRONT),0,0,width=W,height=H);c.showPage()
 header(c,approved.get('preface_title','前言'));top=H-118
 for text in approved['preface_paragraphs']:top=para(c,escape(text),M,top,CW,'CN',12,21)-14
 footer(c,2);c.showPage();links=[]
 for page in range(7):
  header(c,'目录');top=H-116;B.label(c,'篇目',M,top,'CN',9.5,B.MUTED);c.setFont('CN',9.5);c.setFillColor(B.MUTED);c.drawRightString(W-M,top,'页码');top-=19
  for ch,start in zip(chapters[page*10:page*10+10],starts[page*10:page*10+10]):
   d=json.loads((HERE/'data'/f'{ch["id"]}.json').read_text());rowtop=top;B.label(c,d['id'],M,top-13,'SANSB',10.5,B.FOREST);x=M+34;zt=para(c,escape(d['title_zh']),x,top,CW-71,'CNB',11.8,16,B.FOREST);bt=para(c,escape(d['title_en']),x,zt-3,CW-71,'ENI',9.3,12.4,B.MUTED)
   c.setFont('SANS',10);c.setFillColor(B.FOREST);c.drawRightString(W-M,rowtop-13,str(start));bottom=min(bt-7,rowtop-41);B.rule(c,M,bottom,CW);links.append({'frontmatter_page':page+2,'from':[M,H-rowtop,W-M,H-bottom],'full_target_page':start-1});top=bottom-8
  assert top>53,(page,top);footer(c,page+3);c.showPage()
 c.save()
 with fitz.open(path) as doc:assert len(doc)==9
 return starts,links

def back_cover(approved,path):
 c=canvas.Canvas(str(path),pagesize=(W,H),pageCompression=1,invariant=1);c.setTitle('考研学人｜封底');c.setAuthor('朋克英语');c.drawImage(str(BACK),0,0,width=W,height=H)
 text=approved['back_cover_text'];assert isinstance(text,str) and text.strip()
 top=H-148;top=para(c,'考研学人',M+18,top,CW-36,'CNB',23,33,B.FOREST)-19
 para(c,escape(text),M+18,top,CW-36,'CN',12.3,22,B.FOREST);c.showPage();c.save()

def replace_page_number(page,number,cover=False):
 # Remove only the previously generated local footer number. No chapter body,
 # illustration, source notes, or other footer text is redacted or rewritten.
 box=fitz.Rect(W-M-47,H-33,W-M+2,H-13)
 fill=tuple(float(x) for x in (B.PAPER.red,B.PAPER.green,B.PAPER.blue)) if cover else (1,1,1)
 page.add_redact_annot(box,fill=fill);page.apply_redactions(images=0,graphics=0,text=0)
 fontfile=B.FONT_SOURCES['SANS'];f=fitz.Font(fontfile=str(fontfile));size=8.7;point=(W-M-f.text_length(str(number),fontsize=size),H-22)
 page.insert_text(point,str(number),fontname='PKENPageNumber',fontfile=str(fontfile),fontsize=size,color=(B.MUTED.red,B.MUTED.green,B.MUTED.blue))

def main():
 p=argparse.ArgumentParser();p.add_argument('--approved',type=Path,default=HERE/'frontmatter-approved.json');p.add_argument('--volumes',action='store_true');args=p.parse_args()
 approved=json.loads(args.approved.read_text());chapters=[];current_mismatches=[]
 for n in range(1,71):
  no=f'{n:02d}';d=json.loads((HERE/'data'/f'{no}.json').read_text());receipt=HERE/'unsigned/chapters'/no/'layout-and-content-qc.json';ch=json.loads(receipt.read_text());assert ch['source_hashes']==d['source_hashes'] and sha(ch['pdf'])==ch['sha256'],(no,'Stale chapter render')
  for key,path in d['source_paths'].items():
   if sha(path)!=d['source_hashes'][key]:current_mismatches.append({'new_id':no,'source_id':d['source_id'],'field':key})
  chapters.append(ch)
 assert not current_mismatches,('PAY changed; prepare_sources + build cached changed articles first',current_mismatches)
 out=HERE/'unsigned/book';out.mkdir(parents=True,exist_ok=True);fm=out/'frontmatter.pdf';starts,links=frontmatter(chapters,approved,fm);back=out/'back-cover.pdf';back_cover(approved,back)
 doc=fitz.open(fm);toc=[[1,'封面',1],[1,approved.get('preface_title','前言'),2],[1,'目录',3]];body_proofs=[]
 for ch,start in zip(chapters,starts):
  with fitz.open(ch['pdf']) as src:
   first=len(doc);doc.insert_pdf(src,links=True,annots=True)
   for k,page in enumerate(src):
    dest=doc[first+k];replace_page_number(dest,first+k+1,k==0)
    area=fitz.Rect(0,0,W,H-40);assert page.get_textbox(area)==dest.get_textbox(area),(ch['id'],k,'Chapter body text changed during binding')
    assert page.get_pixmap(clip=area,alpha=False).samples==dest.get_pixmap(clip=area,alpha=False).samples,(ch['id'],k,'Chapter body pixels changed during binding')
   body_proofs.append({'new_id':ch['id'],'source_id':ch['source_id'],'start_page':start,'pages':len(src),'source_pdf_sha256':ch['sha256'],'body_pixels_and_text_unchanged':True})
  toc.append([1,f'{ch["id"]} {ch["title_zh"]}',start])
  for sec in ch['sections']:toc.append([2,sec['title'],start+sec['page']-1])
 with fitz.open(back) as b:doc.insert_pdf(b)
 for link in links:doc[link['frontmatter_page']].insert_link({'kind':fitz.LINK_GOTO,'from':fitz.Rect(link['from']),'page':link['full_target_page']})
 doc.set_toc(toc);doc.set_metadata({'title':'考研学人｜70篇趣味英语阅读','author':'朋克英语','subject':'70篇故事 · 中英双语 · 重点词与短语 · 文章简述'})
 unsigned=out/'PUNK-ENGLISH-70-STORIES.pdf';doc.save(unsigned,garbage=4,deflate=True,no_new_id=True);pages=len(doc);doc.close()
 signed=HERE/'signed/book/PUNK-ENGLISH-70-STORIES.pdf';signed.parent.mkdir(parents=True,exist_ok=True);signature=B.stamp_and_verify(unsigned,signed)
 rec={'pages':pages,'chapters':body_proofs,'chapter_count':70,'order_source_sha256':sha(HERE/'order-source.json'),'approved_frontmatter_sha256':sha(args.approved),'fresh_conversion_sha256':sha(HERE/'conversion-report.json'),'unsigned_pdf':str(unsigned),'unsigned_sha256':sha(unsigned),'signed_pdf':str(signed),'signed_sha256':sha(signed),'provenance':signature,'cover_native_pixels':{},'physical_page_2_is_preface':True,'contents_links':70,'old_PDF_pages_reused':False,'all_chapter_body_pixels_and_text_preserved_on_binding':True,'visible_process_language_scan_pending':True}
 for name,image in (('front',FRONT),('back',BACK)):
  w,h=Image.open(image).size;rec['cover_native_pixels'][name]={'path':str(image),'sha256':sha(image),'pixels':[w,h],'effective_ppi_at_B5':[w/(176/25.4),h/(250/25.4)],'no_claim_of_native_300dpi':True}
 write(HERE/'assembly-report.json',rec);print(json.dumps({k:rec[k] for k in ('pages','signed_pdf','signed_sha256','contents_links')},ensure_ascii=False),flush=True)
 if args.volumes:
  volume_records=[]
  for v in range(7):
   # Reuse newly rendered pages only. No old release PDF is an input.
   unsigned_v=HERE/'unsigned/volumes'/f'考研学人 第{v+1}册.pdf';unsigned_v.parent.mkdir(parents=True,exist_ok=True);vd=fitz.open();items=chapters[v*10:v*10+10]
   for ch in items:
    with fitz.open(ch['pdf']) as chapter:vd.insert_pdf(chapter,links=True,annots=True)
   vd.set_toc([[1,f'{ch["id"]} {ch["title_zh"]}',1+sum(x['pages'] for x in items[:i])] for i,ch in enumerate(items)]);vd.set_metadata({'title':f'考研学人 第{v+1}册','author':'朋克英语'});vd.save(unsigned_v,garbage=4,deflate=True);vd.close();sv=HERE/'signed/volumes'/unsigned_v.name;sv.parent.mkdir(parents=True,exist_ok=True);proof=B.stamp_and_verify(unsigned_v,sv);volume_records.append({'volume':v+1,'new_ids':[ch['id'] for ch in items],'pdf':str(sv),'provenance':proof})
  write(HERE/'volumes-report.json',volume_records)

if __name__=='__main__':main()
