"""Assemble seven B5 volumes, preserving every original chapter text page."""
from pathlib import Path
import json, hashlib, re, fcntl
from html import escape
import fitz
from reportlab.pdfgen import canvas
import build_all70 as P
from publication_payloads import payload
from booklet_utils import ROOT, atomic_json

OUT=ROOT/'volumes'; OUT.mkdir(exist_ok=True)
ORDER=json.loads(Path('/workspace/work/order70-recommended.json').read_text())['order']
B=P.B; W,H,M,CW=P.W,P.H,P.M,P.CW

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def toc_pdf(v,items,path):
    c=canvas.Canvas(str(path),pagesize=(W,H),pageCompression=1)
    c.setFillColor(B.PAPER);c.rect(0,0,W,H,stroke=0,fill=1)
    B.text(c,'STORIES TO READ AND REMEMBER',M,H-39,'SANS',8.1,B.FOREST)
    B.text(c,'插图英语阅读小册',M,H-79,'CNB',23,B.FOREST)
    B.text(c,f'第{v}册 · 十篇故事',M,H-108,'CN',12.5,B.FOREST)
    B.para(c,'按推荐顺序阅读，保留原篇号。点击篇目即可跳转；每篇依次包含插图、英文原文、中文译文、词汇与回想。',M,H-130,CW,'CN',9.5,14,B.MUTED)
    y=H-177; B.rule(c,M,y,CW);y-=16
    B.text(c,'阅读顺序 / 原篇号',M,y,'CN',8.3,B.MUTED)
    c.setFillColor(B.MUTED);c.setFont('CN',8.3);c.drawRightString(W-M,y,'本册页码')
    y-=17;links=[]
    for item in items:
        top=y; x=M+59
        B.text(c,f'{item["position"]:02d} / {item["id"]}',M,y-12,'SANS',9.1,B.FOREST)
        zbottom=B.para(c,escape(item['title_zh']),x,y,CW-101,'CNB',11.2,14.5,B.FOREST)
        bottom=min(zbottom-10,y-33)
        c.setFont('SANS',9.2);c.setFillColor(B.FOREST);c.drawRightString(W-M,y-13,str(item['start_page']))
        B.rule(c,M,bottom,CW,B.LINE,.4)
        links.append({'rect':[M,H-top,W-M,H-bottom],'target_page':item['start_page']-1})
        y=bottom-8
    if y<53: raise ValueError(f'Volume{v} TOC too tall: {y}')
    B.rule(c,M,36,CW);B.text(c,f'第{v}册 · 目录',M,22,'CN',8.1,B.MUTED)
    c.save();return links

def _build_locked(v):
    ids=ORDER[(v-1)*10:v*10]
    ps=[payload(n) for n in ids]
    items=[];start=2
    for position,p in enumerate(ps,(v-1)*10+1):
        items.append({k:p[k] for k in ['id','title_zh','title_en','pages','pdf','pdf_sha256']})
        items[-1].update(position=position,start_page=start);start+=p['pages']
    folder=OUT/f'{v:02d}';folder.mkdir(exist_ok=True)
    stamp=hashlib.sha256(json.dumps(items,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
    receipt=folder/'qc.json'
    if receipt.exists():
        old=json.loads(receipt.read_text())
        if old.get('inputs_hash')==stamp and Path(old['pdf']).exists() and sha(old['pdf'])==old['pdf_sha256']:return old
    toc=folder/'contents.pdf';links=toc_pdf(v,items,toc)
    doc=fitz.open(toc)
    for item in items:
        with fitz.open(item['pdf']) as ch: doc.insert_pdf(ch,links=True,annots=True)
    for l in links:doc[0].insert_link({'kind':fitz.LINK_GOTO,'from':fitz.Rect(l['rect']),'page':l['target_page']})
    doc.set_toc([[1,'目录',1]]+[[1,f'{i["position"]:02d} / 第{i["id"]}篇 {i["title_zh"]}',i['start_page']] for i in items])
    doc.set_metadata({'title':f'插图英语阅读小册 第{v}册','author':'英文阅读小册','subject':'十篇故事 · 完整双语阅读 · 词汇与回想'})
    original_text=[p.get_text() for p in doc]
    original_images=sorted((im[2],im[3]) for p in doc for im in p.get_images())
    raw=doc.tobytes(garbage=4,deflate=True);doc.close()
    final=folder/f'插图英语阅读小册-第{v}册-10篇.pdf'
    quality=None
    for q in [96,94,92,90]:
        d=fitz.open(stream=raw,filetype='pdf')
        d.rewrite_images(dpi_target=0,quality=q,bitonal=False)
        d.save(final,garbage=4,deflate=True);d.close()
        if final.stat().st_size<=10*1024*1024:quality=q;break
    if quality is None:raise ValueError(f'Volume{v} exceeds 10MiB')
    with fitz.open(final) as d:
        assert [p.get_text() for p in d]==original_text, 'PDF text changed during image recompression'
        assert sorted((im[2],im[3]) for p in d for im in p.get_images())==original_images,'Image pixel dimensions changed'
        assert len(d)==start-1
        for item in items:
            with fitz.open(item['pdf']) as ch:
                for k,pg in enumerate(ch):
                    target=d[item['start_page']-1+k]
                    assert target.rect==pg.rect and target.get_text()==pg.get_text(),f'Chapter{item["id"]} changed'
        assert len(d[0].get_links())==10
        d[0].get_pixmap(matrix=fitz.Matrix(1.8,1.8),alpha=False).save(folder/'contents-preview.png')
    out={'volume':v,'passed':True,'pdf':str(final),'pdf_sha256':sha(final),'bytes':final.stat().st_size,'pages':start-1,'articles':items,'chapter_text_exact':True,'image_dimensions_preserved':True,'jpeg_quality':quality,'text_vector_preserved':True,'internal_contents_links':10,'inputs_hash':stamp,'preview':str(folder/'contents-preview.png'),'preview_sha256':sha(folder/'contents-preview.png')}
    atomic_json(receipt,out);print(json.dumps({k:out[k] for k in ['volume','pages','bytes','jpeg_quality','pdf_sha256']},ensure_ascii=False),flush=True)
    return out

def build(v):
    folder=OUT/f'{v:02d}';folder.mkdir(exist_ok=True)
    with (folder/'.build.lock').open('w') as lock:
        fcntl.flock(lock.fileno(),fcntl.LOCK_EX)
        return _build_locked(v)

if __name__=='__main__':
    import sys
    for v in map(int,sys.argv[1:] or range(1,8)):
        try:build(v)
        except Exception as e: print(json.dumps({'volume':v,'pending':str(e)},ensure_ascii=False),flush=True)
