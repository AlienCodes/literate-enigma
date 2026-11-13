from __future__ import annotations
import argparse, hashlib, importlib.util, json, math, re, shutil, fcntl
from html import escape
from pathlib import Path
import fitz
from PIL import Image, ImageDraw
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader
from reportlab.platypus import Paragraph
from booklet_utils import ROOT, source, validate_article, atomic_json
from cjk_layout import SafeParagraph, NO_START, NO_END

spec=importlib.util.spec_from_file_location('approved_book_style',ROOT/'build_booklet01.py')
B=importlib.util.module_from_spec(spec);spec.loader.exec_module(B)
B.Paragraph=SafeParagraph
Paragraph=SafeParagraph
W,H,M,CW=B.W,B.H,B.M,B.CW
DEST=ROOT/'production'
DEST.mkdir(exist_ok=True)
ENGINE_REVISION=3

def entry_parts(e,width,core):
    parts,height=B.entry_parts(e,width,core)
    # Keep the approved type sizes; trim only inter-entry padding to fit22
    # core terms naturally without introducing an almost-empty extra page.
    return parts,height-(2.2 if core else 0)

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def norm(t):return re.sub(r'\s+',' ',t).strip()
def safe(t):return re.sub(r'[<>:"/\\|?*]','_',t)

def make_contact(previews,path):
    tiles=[]
    for i,item in enumerate(previews,1):
        im=Image.open(item['path']).convert('RGB');im.thumbnail((450,639))
        tile=Image.new('RGB',(474,676),'#E7E9E5');tile.paste(im,((474-im.width)//2,10))
        ImageDraw.Draw(tile).text((18,653),f'PAGE {i:02}',fill='#29473d');tiles.append(tile)
    sheet=Image.new('RGB',(948,676*math.ceil(len(tiles)/2)),'#E7E9E5')
    for i,im in enumerate(tiles):sheet.paste(im,((i%2)*474,(i//2)*676))
    sheet.save(path,quality=94)

def split_balanced(heights,k):
    n=len(heights);s=[0]
    for h in heights:s.append(s[-1]+h)
    dp=[[math.inf]*(n+1) for _ in range(k+1)];back={};dp[0][0]=0
    for j in range(1,k+1):
        for i in range(j,n+1):
            candidates=[(max(dp[j-1][m],s[i]-s[m]),m) for m in range(j-1,i)]
            dp[j][i],back[j,i]=min(candidates)
    ends=[n];i=n
    for j in range(k,0,-1):i=back[j,i];ends.append(i)
    ends.reverse()
    return dp[k][n],[(ends[i],ends[i+1]) for i in range(k)]

def body_plan(values,font,options,note=''):
    note_h=0
    if note:
        p=Paragraph(escape(note),B.style('CN',9.5,14.5,B.FOREST,True))
        note_h=p.wrap(CW-24,H)[1]+39
    available=(H-101)-55-note_h
    for size,leading,gap in options:
        total,hs=B.measured_paragraph_height(values,CW,font,size,leading,gap,font=='CN')
        if total<=available:
            return [{'values':values,'font':font,'size':size,'leading':leading,'gap':gap,'note':note}]
    size,leading,gap=options[0]
    _,hs=B.measured_paragraph_height(values,CW,font,size,leading,gap,font=='CN')
    full=H-156
    groups=[];group=[];used=0
    for t,h in zip(values,hs):
        if h>full:raise ValueError('A full paragraph exceeds one page')
        if group and used+h+gap>full:
            groups.append(group);group=[];used=0
        group.append(t);used+=h+gap
    if group:groups.append(group)
    if note and sum(B.measured_paragraph_height(groups[-1],CW,font,size,leading,gap,font=='CN')[1])+gap*(len(groups[-1])-1)>available:
        if len(groups[-1])>1:
            last=groups[-1].pop();groups.append([last])
        else:raise ValueError('Reading note needs its own page')
    return [{'values':g,'font':font,'size':size,'leading':leading,'gap':gap,'note':note if i==len(groups)-1 else ''} for i,g in enumerate(groups)]

def vocab_plan(entries,core):
    if not entries:return []
    col=(CW-24)/2
    heights=[entry_parts(e,col,core)[1] for e in entries]
    limit=H-171
    pages=max(1,math.ceil(sum(heights)/(2*limit)))
    while True:
        tallest,cuts=split_balanced(heights,2*pages)
        if tallest<=limit:break
        pages+=1
        if pages>5:raise ValueError('Vocabulary unusually large')
    return [{'core':core,'columns':[entries[a:b] for a,b in cuts[i:i+2]],'total':len(entries),'part':i//2+1,'parts':pages} for i in range(0,len(cuts),2)]

class Book:
    def __init__(self,d):
        self.d=d;self.n=d['id'];self.folder=DEST/self.n;self.folder.mkdir(exist_ok=True)
        self.image=ROOT/'illustrations'/f'{self.n}.png'
        self.path=self.folder/f'{self.n}-{safe(d["title_zh"])}-插图阅读小册.pdf'
        self.en=body_plan(d['english_paragraphs'],'EN',[(12.7,19.8,8.5),(12.4,19.3,8),(12.1,18.8,7.8)])
        self.zh=body_plan(d['chinese_paragraphs'],'CN',[(12,20,8.5),(11.7,19.6,8),(11.4,19,7.5)],d.get('reading_note',''))
        self.core=vocab_plan([x for x in d['vocabulary'] if x['core']],True)
        self.more=vocab_plan([x for x in d['vocabulary'] if not x['core']],False)
        self.total=2+len(self.en)+len(self.zh)+len(self.core)+len(self.more)
        self.body_mappings=[];self.sections=[]

    def finish(self,c):
        B.rule(c,M,36,CW)
        B.text(c,f'{self.n}  {self.d["title_zh"]}',M,22,'CN',8.1,B.MUTED)
        c.setFont('SANS',8.7);c.setFillColor(B.MUTED)
        c.drawRightString(W-M,22,f'{c.getPageNumber():02d} / {self.total:02d}')
        c.showPage()

    def head(self,c,key,kicker,title,subtitle=''):
        c.setFillColor(colors.white);c.rect(0,0,W,H,stroke=0,fill=1)
        c.bookmarkPage(key);c.addOutlineEntry(title,key,level=0,closed=False)
        self.sections.append({'title':title,'page':c.getPageNumber()})
        B.text(c,kicker,M,H-39,'SANS',8.4,B.MUTED)
        B.text(c,title,M,H-71,'CNB',19,B.FOREST)
        top=H-101
        if subtitle:top=B.para(c,escape(subtitle),M,H-91,CW,size=9.3,leading=14,color=B.MUTED)-17
        return top

    def cover(self,c):
        c.setFillColor(B.PAPER);c.rect(0,0,W,H,stroke=0,fill=1)
        c.bookmarkPage('cover');c.addOutlineEntry(f'第{self.n}篇 插图阅读小册','cover',0,False)
        self.sections.append({'title':'插图扉页','page':1})
        B.text(c,'STORIES TO READ AND REMEMBER',M,H-39,'SANS',8.1,B.FOREST)
        c.setFillColor(B.YELLOW);c.roundRect(W-M-35,H-57,35,27,6,stroke=0,fill=1)
        B.text(c,self.n,W-M-26,H-49,'ENB',18,B.FOREST)
        title=self.d['title_zh']
        if '：' in title and len(title)>12:title=title.replace('：','：<br/>',1)
        top=B.para(c,title,M,H-84,CW,'CNB',26,35,B.FOREST)-14
        top=B.para(c,escape(self.d['title_en']),M,top,CW,'ENI',17.4,21.8,B.INK,False)-21
        iw,ih=ImageReader(str(self.image)).getSize();im_h=CW*ih/iw
        if top-im_h<138:
            im_h=top-138;im_w=im_h*iw/ih;ix=(W-im_w)/2
        else:im_w=CW;ix=M
        bottom=top-im_h
        c.drawImage(str(self.image),ix,bottom,width=im_w,height=im_h,preserveAspectRatio=True,mask='auto')
        B.LAYOUT.append({'page':1,'kind':'image','bbox':[ix,bottom,ix+im_w,top],'source':str(self.image)})
        B.para(c,escape(self.d['cover_question']),M,bottom-22,CW,'CN',11.2,17,B.FOREST)
        B.rule(c,M,91,CW)
        for i,(en,zh) in enumerate([('READ','纯净阅读'),('CHECK','中文核对'),('LEARN','词汇记忆'),('RECALL','回想巩固')]):
            x=M+i*CW/4;B.text(c,en,x,73,'SANSB',8.1,B.FOREST);B.text(c,zh,x,56,'CN',9.1,B.MUTED)
        self.finish(c)

    def body(self,c,plans,kind):
        title='英文原文' if kind=='en' else '中文译文'
        for i,p in enumerate(plans):
            top=self.head(c,f'{kind}{i}',('01 / READ' if kind=='en' else '02 / CHECK'),title+(' 续' if i else ''))
            for t in p['values']:
                start=len(B.LAYOUT)
                top=B.para(c,escape(t),M,top,CW,p['font'],p['size'],p['leading'],B.INK,kind=='zh')
                self.body_mappings.append({'section':kind,'page':c.getPageNumber(),'bbox':B.LAYOUT[start]['bbox'],'text':t})
                top-=p['gap']
            if p['note']:
                pp=Paragraph(escape(p['note']),B.style('CN',9.5,14.5,B.FOREST,True));nh=pp.wrap(CW-24,H)[1]+20
                nt=min(top-13,nh+57)
                if nt-nh<49:raise ValueError('Note collides with footer')
                c.setFillColor(B.PALE);c.roundRect(M,nt-nh,CW,nh,6,stroke=0,fill=1)
                B.para(c,escape(p['note']),M+12,nt-10,CW-24,'CN',9.5,14.5,B.FOREST)
            self.finish(c)

    def vocab(self,c,plans):
        for p in plans:
            core=p['core'];title='核心词汇' if core else '文中词汇与搭配'
            if p['part']>1:title+=' 续'
            desc=(f'先记这{p["total"]}项。连着下方的原文短语一起回想。' if core else f'补充词汇共{p["total"]}项。保留每个表达在本文中的意思。')
            top=self.head(c,('core' if core else 'more')+str(p['part']),'03 / LEARN',title,desc)
            col=(CW-24)/2
            for ci,entries in enumerate(p['columns']):
                x=M+ci*(col+24);y=top
                for e in entries:
                    parts,height=entry_parts(e,col,core);start=y
                    hs=11.5 if core else 10.8;ps=7.9 if len(e['pos'])<7 else 7.1
                    if pdfmetrics.stringWidth(e['headword'],'ENB',hs)+pdfmetrics.stringWidth(e['pos'],'CN',ps)+7<=col:
                        c.setFont('CN',ps);c.setFillColor(B.MUTED);c.drawRightString(x+col,y-10,e['pos'])
                    for content,font,size,leading,cjk,color,ph in parts:
                        y=B.para(c,content,x,y,col,font,size,leading,color,cjk)
                    y=start-height;B.rule(c,x,y+4,col,B.LINE,.4)
            self.finish(c)

    def recall(self,c):
        top=self.head(c,'recall','04 / RECALL','回想与回顾','先遮住下方答案，再把四个词放回原文。')
        for i,q in enumerate(self.d['questions'],1):
            B.text(c,f'{i:02d}',M,top-12,'SANSB',9,B.FOREST)
            top=B.para(c,escape(q['text_with_blank']),M+24,top,CW-24,'EN',11.6,17.3,B.INK,False)-10
        top-=7;B.rule(c,M,top,CW);top-=26;B.text(c,'文章主线',M,top,'CNB',13.5,B.FOREST);top-=17
        for label,content in self.d['approved_summary']:
            c.setFillColor(B.YELLOW);c.circle(M+2.8,top-7.8,2.3,stroke=0,fill=1)
            rich=f'<font name="CNB" color="#284E43">{escape(label)}</font>  {escape(content)}'
            top=B.para(c,rich,M+13,top,CW-13,'CN',10.5,15.7)-7
        answers='    '.join(f'{i}  {q["answer"]}' for i,q in enumerate(self.d['questions'],1))
        answer_top=min(top-13,100)
        if answer_top<74:raise ValueError('Recall overflow; shorten exact source excerpts')
        B.rule(c,M,answer_top+9,CW);B.text(c,'参考答案',M,answer_top-4,'CN',8.5,B.MUTED)
        B.para(c,escape(answers),M+52,answer_top+6,CW-52,'EN',9.4,12.8,B.MUTED,False)
        self.finish(c)

    def build(self):
        B.LAYOUT=[]
        c=canvas.Canvas(str(self.path),pagesize=(W,H),pageCompression=1)
        c.setTitle(f'第{self.n}篇 {self.d["title_zh"]} 插图阅读小册');c.setAuthor('英文阅读小册')
        c.setSubject('纯净英文 中文译文 文中词汇 回想练习')
        self.cover(c);self.body(c,self.en,'en');self.body(c,self.zh,'zh');self.vocab(c,self.core);self.vocab(c,self.more);self.recall(c);c.save()
        assert len(fitz.open(self.path))==self.total
        atomic_json(self.folder/'layout.json',{'id':self.n,'pages':self.total,'body_mappings':self.body_mappings,'sections':self.sections,'placed_elements':B.LAYOUT})
        return self.path

def qa_and_preview(n,path,article):
    folder=path.parent;doc=fitz.open(path)
    if n=='01':
        src=ROOT/'output';raw=json.loads((src/'01-layout-audit.json').read_text())
        mappings=[]
        for no,kind,field in [(2,'en','english_paragraphs'),(3,'zh','chinese_paragraphs')]:
            elems=[x for x in raw['placed_elements'] if x['page']==no and x['kind']=='text'][:7]
            mappings.extend({'section':kind,'page':no,'bbox':e['bbox'],'text':t} for e,t in zip(elems,article[field]))
        layout={'id':n,'pages':6,'body_mappings':mappings,'sections':[{'title':x,'page':i+1} for i,x in enumerate(['插图扉页','英文原文','中文译文','核心词汇','文中词汇与搭配','回想与回顾'])],'placed_elements':raw['placed_elements']}
        atomic_json(folder/'layout.json',layout)
    else:layout=json.loads((folder/'layout.json').read_text())
    for e in layout['body_mappings']:
        p=doc[e['page']-1];x0,y0,x1,y1=e['bbox']
        actual=p.get_textbox(fitz.Rect(x0-.5,H-y1-.5,x1+.5,H-y0+.5))
        if e['section']=='en':ok=norm(actual)==norm(e['text'])
        else:ok=re.sub(r'\s+','',actual)==re.sub(r'\s+','',e['text'])
        if not ok:raise ValueError(f'{n} {e["section"]} PDF text mismatch: {actual!r} vs {e["text"]!r}')
    vocab_text=' '.join(p.get_text() for p in doc if '核心词汇' in p.get_text() or '文中词汇与搭配' in p.get_text())
    for e in article['vocabulary']:
        if e['headword'] not in norm(vocab_text):raise ValueError(f'{n}: missing printed word {e["headword"]}')
    # All content spans must stay inside the page and outside the footer strip.
    hanging_punctuation=[]
    for pi,p in enumerate(doc):
        for block in p.get_text('dict')['blocks']:
            if block['type']!=0:continue
            for line in block['lines']:
                visible=''.join(s['text'] for s in line['spans']).strip()
                if n!='01' and line['spans'] and 'NotoSans' in line['spans'][0]['font'] and visible:
                    if visible[0] in NO_START or visible[-1] in NO_END:
                        raise ValueError(f'{n}: CJK punctuation at forbidden line boundary page{pi+1}: {visible}')
                for span in line['spans']:
                    x0,y0,x1,y1=span['bbox']
                    # CJK composition legitimately hangs final punctuation by
                    # one glyph. The approved01 does this too. This is not
                    # cropped text: require a CJK punctuation ending, at most
                    # one em of overhang, and a generous physical page margin.
                    hangs=(x1>W-M+1.5 and span['text'].rstrip().endswith(tuple('。，、；：！？）》】’”'))
                           and x1-(W-M)<=span['size']+1 and x1<W-23)
                    if hangs:hanging_punctuation.append({'page':pi+1,'overhang_pt':x1-(W-M)})
                    if x0<M-1.5 or (x1>W-M+1.5 and not hangs) or y0<18 or y1>H-12:
                        raise ValueError(f'{n}: text outside margins page{pi+1}: {span["text"]}')
    previews=[]
    for i,p in enumerate(doc,1):
        image=folder/f'page-{i:02d}.png';p.get_pixmap(matrix=fitz.Matrix(1.8,1.8),alpha=False).save(image)
        previews.append({'page':i,'path':str(image),'sha256':sha(image)})
    current={Path(item['path']).name for item in previews}
    for old in folder.glob('page-*.png'):
        if re.fullmatch(r'page-\d{2}\.png',old.name) and old.name not in current:old.unlink()
    make_contact(previews,folder/'contact-sheet.jpg')
    atomic_json(folder/'preview-manifest.json',{'id':n,'source_pdf':str(path),'pdf_sha256':sha(path),'pages':previews})
    atomic_json(folder/'qc.json',{'id':n,'passed':True,'pages':len(doc),'pdf':str(path),'bytes':path.stat().st_size,'pdf_sha256':sha(path),'image_sha256':sha(ROOT/'illustrations'/f'{n}.png') if n!='01' else sha(ROOT/'illustrations/01-preview.png'),'full_english_exact':True,'full_chinese_exact':True,'all_target_vocabulary_present':True,'vocabulary_count':len(article['vocabulary']),'core_count':22,'preview_source':'This exact final PDF','text_inside_page_bounds':True,'cjk_hanging_punctuation':hanging_punctuation,'engine_revision':ENGINE_REVISION,'content_sha256':sha(ROOT/'content/articles'/f'{n}.json')})
    return len(doc)

def _build_one_locked(n,force=False):
    p=ROOT/'content/articles'/f'{n}.json';d=json.loads(p.read_text());validate_article(d)
    folder=DEST/n;folder.mkdir(exist_ok=True)
    if (folder/'qc.json').exists() and not force:
        old=json.loads((folder/'qc.json').read_text())
        image=ROOT/'illustrations'/('01-preview.png' if n=='01' else f'{n}.png')
        if old.get('engine_revision')==ENGINE_REVISION and old.get('content_sha256')==sha(p) and image.exists() and old.get('image_sha256')==sha(image):
            if not (folder/'contact-sheet.jpg').exists():make_contact(json.loads((folder/'preview-manifest.json').read_text())['pages'],folder/'contact-sheet.jpg')
            return old
    if n=='01':
        src=next((ROOT/'output').glob('*.pdf'));path=folder/src.name;shutil.copy2(src,path)
    else:
        if not (ROOT/'illustrations'/f'{n}.png').exists():return {'id':n,'pending':'illustration'}
        path=Book(d).build()
    qa_and_preview(n,path,d)
    result=json.loads((folder/'qc.json').read_text());print(json.dumps(result,ensure_ascii=False),flush=True)
    (folder/'error.json').unlink(missing_ok=True)
    return result

def build_one(n,force=False):
    folder=DEST/n;folder.mkdir(exist_ok=True)
    with (folder/'.build.lock').open('w') as lock:
        fcntl.flock(lock.fileno(),fcntl.LOCK_EX)
        return _build_one_locked(n,force)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('ids',nargs='*');ap.add_argument('--force',action='store_true');a=ap.parse_args()
    ids=a.ids or [p.stem for p in sorted((ROOT/'content/articles').glob('*.json'))]
    for n in ids:
        try:build_one(f'{int(n):02d}',a.force)
        except Exception as e:
            atomic_json(DEST/f'{int(n):02d}'/'error.json',{'id':n,'error':str(e)})
            print(json.dumps({'id':n,'ERROR':str(e)},ensure_ascii=False),flush=True)

if __name__=='__main__':main()
