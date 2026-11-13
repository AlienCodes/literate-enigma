"""Seven archive volumes from the newly rendered current chapters, not old PDFs."""
import json
from pathlib import Path
from html import escape
import fitz
from reportlab.pdfgen import canvas
import build_print as B
from assemble_print import replace_page_number,para,footer,header
HERE=Path(__file__).resolve().parent
W,H,M,CW=B.W,B.H,B.M,B.CW
def main():
 reports=[]
 for v in range(7):
  folder=HERE/'unsigned/volumes'/f'{v+1:02d}';folder.mkdir(parents=True,exist_ok=True);items=[];start=2
  for n in range(v*10+1,v*10+11):
   no=f'{n:02d}';d=json.loads((HERE/'data'/f'{no}.json').read_text());rec=json.loads((HERE/'unsigned/chapters'/no/'layout-and-content-qc.json').read_text());assert d['source_hashes']==rec['source_hashes'];assert B.sha(rec['pdf'])==rec['sha256'];items.append((d,rec,start));start+=rec['pages']
  contents=folder/'contents.pdf';c=canvas.Canvas(str(contents),pagesize=(W,H),pageCompression=1,invariant=1);header(c,'目录');top=H-116;B.label(c,f'第{v+1}册',M,top,'CN',9.5,B.MUTED);top-=19;links=[]
  for d,rec,start_page in items:
   rowtop=top;B.label(c,d['id'],M,top-13,'SANSB',10.5,B.FOREST);x=M+34;zt=para(c,escape(d['title_zh']),x,top,CW-71,'CNB',11.8,16,B.FOREST);bt=para(c,escape(d['title_en']),x,zt-3,CW-71,'ENI',9.3,12.4,B.MUTED);c.setFont('SANS',10);c.setFillColor(B.FOREST);c.drawRightString(W-M,rowtop-13,str(start_page));bottom=min(bt-7,rowtop-41);B.rule(c,M,bottom,CW);links.append((fitz.Rect(M,H-rowtop,W-M,H-bottom),start_page-1));top=bottom-8
  assert top>53;footer(c,1);c.showPage();c.save();doc=fitz.open(contents);toc=[[1,'目录',1]]
  for d,rec,start_page in items:
   with fitz.open(rec['pdf']) as ch:
    first=len(doc);doc.insert_pdf(ch,links=True,annots=True)
    for k,page in enumerate(ch):
     dest=doc[first+k];replace_page_number(dest,first+k+1,k==0);area=fitz.Rect(0,0,W,H-40);assert page.get_textbox(area)==dest.get_textbox(area);assert page.get_pixmap(clip=area,alpha=False).samples==dest.get_pixmap(clip=area,alpha=False).samples
   toc.append([1,f'{d["id"]} {d["title_zh"]}',start_page])
  for rect,target in links:doc[0].insert_link({'kind':fitz.LINK_GOTO,'from':rect,'page':target})
  doc.set_toc(toc);doc.set_metadata({'title':f'考研学人 第{v+1}册','author':'朋克英语','subject':'中英双语 · 重点词与短语 · 文章简述'});out=folder/f'考研学人 第{v+1}册.pdf';doc.save(out,garbage=4,deflate=True,no_new_id=True);pages=len(doc);doc.close();signed=HERE/'signed/volumes'/out.name;signed.parent.mkdir(parents=True,exist_ok=True);proof=B.stamp_and_verify(out,signed);rec={'volume':v+1,'new_ids':[d['id'] for d,_,_ in items],'pages':pages,'signed_pdf':str(signed),'sha256':B.sha(signed),'provenance':proof,'continuous_local_page_numbers':True,'contents_links':10,'old_release_pages_reused':False,'chapter_body_pixels_and_text_unchanged':True};reports.append(rec);B.write(folder/'qc.json',rec);print(json.dumps({'volume':v+1,'pages':pages,'sha256':rec['sha256']},ensure_ascii=False),flush=True)
 B.write(HERE/'volumes-report.json',reports)
if __name__=='__main__':main()
