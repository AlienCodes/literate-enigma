"""Fresh B5 print book from frozen current-source data; no old PDF page reuse."""
from __future__ import annotations
import argparse, copy, hashlib, importlib.util, json, math, re, shutil
from html import escape
from pathlib import Path
import fitz
from concurrent.futures import ProcessPoolExecutor
from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.utils import ImageReader
from reportlab.platypus import Paragraph as NativeParagraph

HERE=Path(__file__).resolve().parent
OLD=Path('/workspace/work/booklet70')
SIGN=Path('/workspace/work/github-publication/target/朋克英语署名版/2026-11-13-v1')
W,H=176*72/25.4,250*72/25.4
M=37.0;CW=W-2*M;BOTTOM=53.0
FOREST=colors.HexColor('#284E43');INK=colors.HexColor('#293B35');MUTED=colors.HexColor('#77837A');PAPER=colors.HexColor('#FDFBF6');YELLOW=colors.HexColor('#E7C46E');LINE=colors.HexColor('#DFE5DB')
spec=importlib.util.spec_from_file_location('approved_cjk_layout',OLD/'cjk_layout.py');CJK=importlib.util.module_from_spec(spec);spec.loader.exec_module(CJK)
Paragraph=CJK.SafeParagraph
FONT_SOURCES={'CN':OLD/'fonts/NotoSansSC-400.ttf','CNB':OLD/'fonts/NotoSansSC-600.ttf','EN':Path('/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf'),'ENB':Path('/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf'),'ENI':Path('/usr/share/fonts/truetype/liberation/LiberationSerif-Italic.ttf'),'SANS':Path('/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf'),'SANSB':Path('/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf')}
for name,path in FONT_SOURCES.items():pdfmetrics.registerFont(TTFont(name,str(path)))

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def write(path,data):path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
def plain_markup(t):return re.sub(r'\*\*([^*]+)\*\*\([^)]*\)',r'\1',t).replace('**','')
def rich(t,zh=False):
 if zh:t=re.sub(r'(\*\*[^*]+\*\*)\([^)]*\)',r'\1',t)
 bits=re.split(r'(\*\*[^*]+\*\*)',t);font='CNB' if zh else 'ENB'
 return ''.join(f'<font name="{font}" color="#284E43">{escape(s[2:-2])}</font>' if s.startswith('**') else escape(s) for s in bits)
def style(font,size,leading,color=INK,cjk=False):return ParagraphStyle('body',fontName=font,fontSize=size,leading=leading,textColor=color,wordWrap='CJK' if cjk else None,splitLongWords=False,allowWidows=False,allowOrphans=False)
def measure(text,width,font,size,leading,cjk=False,color=INK):
 p=Paragraph(text,style(font,size,leading,color,cjk));_,height=p.wrap(width,H*4);return p,height
def rule(c,x,y,width):c.setStrokeColor(LINE);c.setLineWidth(.6);c.line(x,y,x+width,y)
def label(c,text,x,y,font='CN',size=10,color=INK):c.setFont(font,size);c.setFillColor(color);c.drawString(x,y,text)
def balanced_parts(heights,k):
 n=len(heights);s=[0]
 for h in heights:s.append(s[-1]+h)
 dp=[[math.inf]*(n+1) for _ in range(k+1)];back={};dp[0][0]=0
 for j in range(1,k+1):
  for i in range(j,n+1):dp[j][i],back[j,i]=min((max(dp[j-1][m],s[i]-s[m]),m) for m in range(j-1,i))
 ends=[n];i=n
 for j in range(k,0,-1):i=back[j,i];ends.append(i)
 ends.reverse();return dp[k][n],[(ends[i],ends[i+1]) for i in range(k)]

class Book:
 def __init__(self,data,offset=0):
  self.d=data;self.offset=offset;self.no=data['id'];self.folder=HERE/'unsigned/chapters'/self.no;self.folder.mkdir(parents=True,exist_ok=True)
  for old in self.folder.glob('page-*.png'):old.unlink()
  self.path=self.folder/f'{self.no} {data["title_zh"]}.pdf';self.c=canvas.Canvas(str(self.path),pagesize=(W,H),pageCompression=1,invariant=1);self.c.setTitle(f'{self.no} {data["title_zh"]}｜考研学人');self.c.setAuthor('朋克英语');self.c.setSubject(data['title_en']);self.layout=[];self.sections=[];self.body_mapping=[];self.top=0
 def para(self,text,x,top,width,font='CN',size=12,leading=20,cjk=True,color=INK,kind='text'):
  p,h=measure(text,width,font,size,leading,cjk,color)
  if top-h<BOTTOM-1 or top>H-24:raise ValueError((self.no,'Text outside safe body area',kind,top,h,text[:90]))
  p.drawOn(self.c,x,top-h);self.layout.append({'page':self.c.getPageNumber(),'kind':kind,'bbox':[x,top-h,x+width,top],'font':font,'font_size':size,'text':re.sub('<[^>]+>','',text)});return top-h
 def finish(self):
  rule(self.c,M,36,CW);label(self.c,f'{self.no}  {self.d["title_zh"]}',M,22,size=8.1,color=MUTED);self.c.setFont('SANS',8.7);self.c.setFillColor(MUTED);self.c.drawRightString(W-M,22,str(self.c.getPageNumber()+self.offset));self.c.showPage()
 def start(self,title,continuation=False):
  self.c.setFillColor(colors.white);self.c.rect(0,0,W,H,stroke=0,fill=1);label(self.c,'考研学人',M,H-36,size=8.4,color=MUTED)
  key=f'section-{len(self.sections)}';self.c.bookmarkPage(key);self.c.addOutlineEntry(title+('（续）' if continuation else ''),key,0,False);self.sections.append({'title':title,'page':self.c.getPageNumber()})
  self.top=self.para(escape(title+('（续）' if continuation else '')),M,H-62,CW,'CNB',19,27,True,FOREST,kind='heading')-22
 def ensure(self,height,title):
  if self.top-height<BOTTOM:self.finish();self.start(title,True)
 def cover(self):
  c=self.c;c.setFillColor(PAPER);c.rect(0,0,W,H,stroke=0,fill=1);c.bookmarkPage('chapter');c.addOutlineEntry(self.d['title_zh'],'chapter',0,False);label(c,'考研学人',M,H-37,size=9,color=FOREST)
  c.setFillColor(YELLOW);c.roundRect(W-M-35,H-57,35,27,6,stroke=0,fill=1);label(c,self.no,W-M-27,H-49,'ENB',18,FOREST)
  title=self.d['title_zh'];top=self.para(escape(title),M,H-83,CW,'CNB',26,35,True,FOREST,'chapter title')-14;top=self.para(escape(self.d['title_en']),M,top,CW,'ENI',17.4,21.8,False,INK,'English title')-20
  iw,ih=ImageReader(self.d['illustration']).getSize();ihp=CW*ih/iw
  if top-ihp<138:ihp=top-138;iwp=ihp*iw/ih;ix=(W-iwp)/2
  else:iwp=CW;ix=M
  bottom=top-ihp;c.drawImage(self.d['illustration'],ix,bottom,width=iwp,height=ihp,preserveAspectRatio=True,mask='auto');self.layout.append({'page':1,'kind':'illustration','bbox':[ix,bottom,ix+iwp,top],'pixels':[iw,ih],'effective_ppi':[iw/(iwp/72),ih/(ihp/72)],'source_sha256':sha(self.d['illustration'])})
  self.para(escape(self.d['cover_question']),M,bottom-22,CW,'CN',11.2,17,True,FOREST,'chapter question');self.finish()
 def body(self,kind):
  title='英文原文' if kind=='en' else '中文译文';self.start(title);markup=self.d['english_markup_paragraphs' if kind=='en' else 'chinese_markup_paragraphs'];plain=self.d['english_paragraphs' if kind=='en' else 'chinese_paragraphs'];font,size,leading=('EN',12.7,19.8) if kind=='en' else ('CN',12,20)
  for marked,expected in zip(markup,plain):
   content=rich(marked,kind=='zh');_,h=measure(content,CW,font,size,leading,kind=='zh');self.ensure(h+8.5,title)
   if h>H-165:raise ValueError((self.no,'Single body paragraph too long at approved font',h))
   top=self.top;self.top=self.para(content,M,top,CW,font,size,leading,kind=='zh',kind='body-'+kind)-8.5;self.body_mapping.append({'section':kind,'page':self.c.getPageNumber(),'bbox':[M,self.top+8.5,W-M,top],'text':expected})
  self.finish()
 def vocabulary(self):
  title='词汇与表达';self.start(title);col=(CW-24)/2;available=self.top-BOTTOM;prepared=[]
  for entry in self.d['vocabulary']:
   # Exact approved B5 word-table sizes and spacing: existing short source
   # examples use the former core-entry style; other entries use the former
   # complementary-entry style. No font is reduced to hit a page-count target.
   form=entry['form_in_text'];pos=entry['pos'];meaning=entry['meaning_zh'];context=entry['context_phrase'];core=bool(context);head_size=11.5 if core else 10.8;meaning_size=10.5 if core else 10.2;meaning_leading=14.4 if core else 13.7
   parts=[(escape(form),'ENB',head_size,14 if core else 13.1,False,FOREST),(escape(meaning),'CN',meaning_size,meaning_leading,True,INK)]
   if context:parts.append((escape(context),'ENI',9.5,12.1,False,MUTED))
   inline_pos=pdfmetrics.stringWidth(form,'ENB',head_size)+pdfmetrics.stringWidth(pos,'CN',7.8)+8<=col
   if not inline_pos:parts.insert(1,(escape(pos),'CN',8,11,True,MUTED))
   height=sum(measure(t,col,font,size,leading,cjk,color)[1] for t,font,size,leading,cjk,color in parts)+(5.6 if core else 4.2)
   prepared.append((entry,parts,height,inline_pos))
  heights=[x[2] for x in prepared];pages=max(1,math.ceil(sum(heights)/(2*available)))
  while True:
   tallest,cuts=balanced_parts(heights,2*pages)
   if tallest<=available:break
   pages+=1
  for page in range(pages):
   if page:self.start(title,True)
   for column in range(2):
    y=self.top;x=M+column*(col+24);a,b=cuts[page*2+column]
    for entry,parts,height,inline_pos in prepared[a:b]:
     if inline_pos:self.c.setFont('CN',7.8);self.c.setFillColor(MUTED);self.c.drawRightString(x+col,y-10,entry['pos'])
     start=y
     for text,font,size,leading,cjk,color in parts:y=self.para(text,x,y,col,font,size,leading,cjk,color,'vocabulary')
     y=start-height;rule(self.c,x,y+5,col)
   self.finish()
 def notes(self):
  title='注释';self.start(title);available=self.top-BOTTOM;items=[]
  for note in self.d['notes']:
   en=escape(note['source_English']);text=escape(note['text']).replace('\n','<br/>');eh=measure(en,CW,'ENI',9.5,13,False,MUTED)[1];p,h=measure(text,CW,'CN',11,18,True)
   if eh+h+17<=available:items.append((en,text,eh+h+17))
   else:
    lines=CJK.format_lines(text,style('CN',11,18,INK,True),CW).split('<br/>')
    group=[]
    for line in lines:
     if len(group)*18+eh+35>available:items.append((en,'<br/>'.join(group),eh+len(group)*18+17));group=[]
     group.append(line)
    if group:items.append((en,'<br/>'.join(group),eh+len(group)*18+17))
  heights=[x[2] for x in items];pages=max(1,math.ceil(sum(heights)/available))
  while True:
   tallest,cuts=balanced_parts(heights,pages)
   if tallest<=available:break
   pages+=1
  for page,(a,b) in enumerate(cuts):
   if page:self.start(title,True)
   for en,text,height in items[a:b]:self.top=self.para(en,M,self.top,CW,'ENI',9.5,13,False,MUTED,'note source')-4;self.top=self.para(text,M,self.top,CW,'CN',11,18,True,INK,'source note')-13
   self.finish()
 def summary(self):
  title='文章简述';self.start(title)
  for name,text in self.d['approved_summary']:
   content=f'<font name="CNB" color="#284E43">{escape(name)}：</font>{escape(text)}';_,h=measure(content,CW-13,'CN',11.5,19,True);self.ensure(h+13,title);self.c.setFillColor(YELLOW);self.c.circle(M+2.8,self.top-8.5,2.4,stroke=0,fill=1);self.top=self.para(content,M+13,self.top,CW-13,'CN',11.5,19,True,INK,'current summary')-13
  self.finish()
 def exercise(self):
  title='词汇练习';self.start(title)
  for i,q in enumerate(self.d['questions'],1):
   text=f'{i:02d}  '+q['text_with_blank'];_,h=measure(escape(text),CW,'EN',12,19,False);self.ensure(h+15,title);self.top=self.para(escape(text),M,self.top,CW,'EN',12,19,False,INK,'exercise')-15
  self.top-=10;rule(self.c,M,self.top,CW);self.top-=22;self.top=self.para('参考答案',M,self.top,CW,'CNB',11,17,True,FOREST,'answer heading')-7;answers='　　'.join(f'{i}  {q["answer"]}' for i,q in enumerate(self.d['questions'],1));self.para(escape(answers),M,self.top,CW,'CN',10.5,17,True,MUTED,'answers');self.finish()
 def build(self):
  # The compact main book follows the approved reading-book scope. Sentence
  # analysis and exercises remain in frozen source data, not printed chapters.
  self.cover();self.body('en');self.body('zh');self.vocabulary();self.summary();self.c.save()
  with fitz.open(self.path) as doc:
   assert all(abs(p.rect.width-W)<.01 and abs(p.rect.height-H)<.01 for p in doc)
   for item in self.body_mapping:
    text=doc[item['page']-1].get_textbox(fitz.Rect([item['bbox'][0],H-item['bbox'][3],item['bbox'][2],H-item['bbox'][1]]))
    normal=lambda s:re.sub(r'\s+','',s)
    assert normal(text)==normal(item['text']),(self.no,item['section'],'Actual PDF text mismatch',text,item['text'])
   pages=len(doc)
  result={'id':self.no,'source_id':self.d['source_id'],'title_zh':self.d['title_zh'],'pdf':str(self.path),'pages':pages,'sha256':sha(self.path),'source_hashes':self.d['source_hashes'],'engine_sha256':sha(__file__),'sections':self.sections,'body_mappings':self.body_mapping,'placed_elements':self.layout,'body_text_extracted_from_actual_PDF_exact':True,'all_current_focus_count':len(self.d['vocabulary']),'source_notes_preserved_in_data_only_count':len(self.d['notes']),'source_notes_printed':False,'exercises_or_answers_printed':False,'approved_summary_points':len(self.d['approved_summary']),'offset':self.offset}
  write(self.folder/'layout-and-content-qc.json',result)
  for i in range(pages):
   with fitz.open(self.path) as doc:doc[i].get_pixmap(matrix=fitz.Matrix(1.2,1.2),alpha=False).save(self.folder/f'page-{i+1:02d}.png')
  print(json.dumps({k:result[k] for k in ('id','source_id','pages','sha256')},ensure_ascii=False),flush=True);return result

def stamp_and_verify(source,output):
 spec=importlib.util.spec_from_file_location('required_provenance',SIGN/'provenance.py');P=importlib.util.module_from_spec(spec);spec.loader.exec_module(P)
 rec=P.stamp_pdf(source,output,source_commit='PAY snapshot '+sha(HERE/'conversion-report.json'))
 rec.update({'engine_sha256':sha(SIGN/'provenance.py'),'pages_default_pixels_equal':[],'pages_reveal_changed':[]})
 with fitz.open(source) as src,fitz.open(output) as stamped:
  assert len(src)==len(stamped)
  for a,b in zip(src,stamped):
   ap=a.get_pixmap(alpha=False);bp=b.get_pixmap(alpha=False);assert ap.samples==bp.samples,(source,'Hidden layer changed visible pixels',a.number);assert a.get_text()==b.get_text();rec['pages_default_pixels_equal'].append(hashlib.sha256(ap.samples).hexdigest())
  ui=next(x for x in stamped.layer_ui_configs() if x['text']==P.LAYER_NAME);stamped.set_layer_ui_config(ui['number'],action=0)
  for a,b in zip(src,stamped):assert a.get_pixmap(alpha=False).samples!=b.get_pixmap(alpha=False).samples,(source,'Layer reveal ineffective',a.number);rec['pages_reveal_changed'].append(b.number+1)
 rec['all_pages_default_pixels_equal']=True;rec['all_pages_reveal_verified']=True
 return rec

def build_one(task):
 no,stamp=task;d=json.loads((HERE/'data'/f'{no}.json').read_text());receipt=HERE/'unsigned/chapters'/no/'layout-and-content-qc.json';rec=None
 if receipt.exists():
  prior=json.loads(receipt.read_text());pdf=Path(prior['pdf'])
  if prior.get('source_hashes')==d['source_hashes'] and prior.get('engine_sha256')==sha(__file__) and pdf.is_file() and sha(pdf)==prior['sha256']:rec=prior
 if rec is None:rec=Book(d).build()
 if stamp:
   target=HERE/'signed/chapters'/no/Path(rec['pdf']).name;target.parent.mkdir(parents=True,exist_ok=True);rec['provenance']=stamp_and_verify(Path(rec['pdf']),target)
 return rec

def main():
 p=argparse.ArgumentParser();p.add_argument('--ids',nargs='+',default=['17']);p.add_argument('--all',action='store_true');p.add_argument('--stamp',action='store_true');p.add_argument('--workers',type=int,default=1);args=p.parse_args();ids=[f'{n:02d}' for n in range(1,71)] if args.all else [x.zfill(2) for x in args.ids]
 if args.workers>1:
  with ProcessPoolExecutor(max_workers=args.workers) as pool:out=list(pool.map(build_one,[(no,args.stamp) for no in ids]))
 else:out=[build_one((no,args.stamp)) for no in ids]
 write(HERE/'build-report.json',{'chapters':out,'source_conversion_sha256':sha(HERE/'conversion-report.json'),'old_PDF_pages_reused':False,'formal_frontmatter_pending':True,'page_size_mm':[176,250],'font_sha256':{n:sha(p) for n,p in FONT_SOURCES.items()}})

if __name__=='__main__':main()
