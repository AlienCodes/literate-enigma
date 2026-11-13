"""Process every inventoried PDF; keep source archives and ordinary page pixels intact."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from urllib.parse import quote
from urllib.request import urlopen, Request
import hashlib, json, os, shutil, subprocess, sys
import fitz
from reportlab.pdfgen import canvas
from provenance import ROOT, FONT, LAYER_NAME, stamp_pdf, sha

REPO_ROOT = ROOT.parents[1]
WORK = Path(os.environ.get('PUNK_PDF_WORK','/workspace/work/github-publication/attribution-working'))
INPUTS = WORK/'inputs'
UNIQUE = WORK/'unique'
QC = ROOT/'核验/单文档'
FONT_ROOT = REPO_ROOT/'插图阅读小册/fonts'
REVISION = sha(ROOT/'provenance.py')

def write(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')

def git_sha(path):
    h=hashlib.sha1(b'blob '+str(Path(path).stat().st_size).encode()+b'\0')
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
    return h.hexdigest()

def materialize(item):
    dest=INPUTS/(item['sha']+'.pdf')
    if dest.exists() and git_sha(dest)==item['sha']:return dest
    local=REPO_ROOT/item['path']
    if local.exists() and git_sha(local)==item['sha']:
        os.link(local,dest)
    else:
        available=subprocess.run(['git','cat-file','-e',item['sha']],cwd=REPO_ROOT,
                  capture_output=True,env={**os.environ,'GIT_NO_LAZY_FETCH':'1'}).returncode==0
        if available:
            with dest.open('wb') as f:
                subprocess.run(['git','cat-file','blob',item['sha']],cwd=REPO_ROOT,stdout=f,
                               check=True,env={**os.environ,'GIT_NO_LAZY_FETCH':'1'})
        else:
            url='https://raw.githubusercontent.com/alienalgorithm/postgraduate-vocabulary/'+item['source_commit']+'/'+quote(item['path'],safe='/')
            with urlopen(Request(url,headers={'User-Agent':'Punk-English-PDF-archive'}),timeout=120) as response,dest.open('wb') as f:
                shutil.copyfileobj(response,f,4*1024*1024)
    assert git_sha(dest)==item['sha'],item['path']
    return dest

def build_new_book(baseline):
    cover_png=ROOT/'封面/PUNK-ENGLISH-BOOK-COVER.png'
    cover=WORK/'cover-before-attribution.pdf'
    with fitz.open(baseline) as src:
        width,height=src[0].rect.width,src[0].rect.height
    c=canvas.Canvas(str(cover),pagesize=(width,height),invariant=1,pageCompression=1)
    c.setTitle('考研学人｜70篇趣味英语阅读｜书封');c.setAuthor('朋克英语')
    c.drawImage(str(cover_png),0,0,width=width,height=height);c.showPage();c.save()
    output=WORK/'book-with-cover-before-attribution.pdf'
    if output.exists():output.unlink()
    counter_checks=[];toc_links=[]
    with fitz.open(baseline) as src,fitz.open(cover) as coverdoc:
        doc=fitz.open();doc.insert_pdf(coverdoc);doc.insert_pdf(src,links=True,annots=True)
        sans=fitz.Font(fontfile=str(FONT_ROOT/'LiberationSans-Regular.ttf'))
        for i in range(7):
            page=doc[i+1]
            old_links=src[i].get_links()
            assert len(old_links)==10 and all(x['kind']==fitz.LINK_GOTO for x in old_links)
            for link in page.get_links():page.delete_link(link)
            spans=[s for b in page.get_text('dict')['blocks'] for l in b.get('lines',[]) for s in l['spans']
                   if s['text'].isdigit() and s['bbox'][0]>width*.8 and 170<s['bbox'][1]<height-50]
            assert len(spans)==10,(i,len(spans))
            for s in spans:
                box=fitz.Rect(s['bbox'])+(-.5,-.5,.5,.5)
                page.add_redact_annot(box,fill=(253/255,251/255,246/255))
            page.apply_redactions(images=0,graphics=0,text=0)
            for s in spans:
                value=str(int(s['text'])+1);size=s['size']
                point=(width-37-sans.text_length(value,fontsize=size),s['origin'][1])
                page.insert_text(point,value,fontname='PKENContentsNumber',
                    fontfile=str(FONT_ROOT/'LiberationSans-Regular.ttf'),fontsize=size,
                    color=fitz.sRGB_to_pdf(s['color']))
                counter_checks.append({'page':i+1,'value':value,
                    'rect':[width-80,s['bbox'][1]-2,width-30,s['bbox'][3]+2]})
            for link in old_links:
                entry={'kind':fitz.LINK_GOTO,'from':fitz.Rect(link['from']),
                       'page':link['page']+1,'to':link.get('to',fitz.Point(0,0))}
                page.insert_link(entry)
                toc_links.append({'toc_page':i+1,'target':entry['page']})
        doc.set_toc([[1,'封面',1]]+[[level,title,page+1] for level,title,page in src.get_toc()])
        doc.set_metadata({'title':'考研学人｜70篇趣味英语阅读（新顺序合订本）',
                          'author':'朋克英语','subject':'70篇文章；含书封、目录、双语阅读与词汇'})
        assert len(doc)==475
        for i in range(7,len(src)):
            assert doc[i+1].rect==src[i].rect and doc[i+1].get_text()==src[i].get_text()
        doc.save(output,garbage=4,deflate=True,no_new_id=True);doc.close()
    with fitz.open(output) as d:
        assert len(d.get_toc())==72
        for item in counter_checks:
            assert d[item['page']].get_textbox(fitz.Rect(item['rect'])).strip()==item['value'],item
        assert sum(len(d[i].get_links()) for i in range(1,8))==70
        for i in range(7):
            actual=sorted(x['page'] for x in d[i+1].get_links())
            expected=sorted(x['target'] for x in toc_links if x['toc_page']==i+1)
            assert actual==expected
    write(ROOT/'核验/新封面与目录核验.json',{'passed':True,'pages':475,'cover_pages':1,
          'contents_pages':7,'contents_links':70,'bookmarks':72,'counters_shifted_by':1,
          'chapter_text_and_page_geometry_preserved':True,'counter_checks':counter_checks})
    return cover,output

def process_one(task):
    source=Path(task['input']);key=sha(source);output=UNIQUE/(key+'.pdf');report=QC/(key+'.json')
    if report.exists() and output.exists():
        cached=json.loads(report.read_text())
        if cached.get('engine_revision')==REVISION and cached.get('sha256')==sha(output):return cached
    result=stamp_pdf(source,output,preserve_original_author=task.get('reference',False),
                     source_commit=task['source_commit'])
    page_pixels=[]
    with fitz.open(source) as a,fitz.open(output) as b:
        assert len(a)==len(b) and a.get_toc()==b.get_toc()
        for i in range(len(a)):
            assert a[i].rect==b[i].rect
            assert a[i].get_text()==b[i].get_text(),('normal_text',task['label'],i+1)
            first=a[i].get_pixmap(alpha=False);second=b[i].get_pixmap(alpha=False)
            assert first.width==second.width and first.height==second.height
            assert first.samples==second.samples,('normal_pixels',task['label'],i+1)
            page_pixels.append(hashlib.sha256(first.samples).hexdigest())
        default_pix=b[0].get_pixmap(alpha=False).samples
        ui=next(x for x in b.layer_ui_configs() if x['text']==LAYER_NAME)
        b.set_layer_ui_config(ui['number'],action=0)
        assert b[0].get_pixmap(alpha=False).samples!=default_pix,('reveal',task['label'])
        assert '朋克英语' in b[0].get_text()
    result.update({'engine_revision':REVISION,'normal_text_unchanged':True,
                   'normal_page_pixels_unchanged':True,'layer_reveal_verified':True,
                   'page_pixel_SHA256':page_pixels})
    write(report,result)
    return result

def main():
    for p in [WORK,INPUTS,UNIQUE,QC]:p.mkdir(parents=True,exist_ok=True)
    inventory=json.loads((ROOT/'SOURCE-INVENTORY.json').read_text());source_commit=inventory['source_commit']
    unique={x['sha']:{**x,'source_commit':source_commit} for x in inventory['pdfs']}
    with ThreadPoolExecutor(max_workers=2) as pool:
        list(pool.map(materialize,unique.values()))
    print(json.dumps({'inputs_ready':len(unique),'bytes':sum(p.stat().st_size for p in INPUTS.glob('*.pdf'))}),flush=True)
    baseline=next(x for x in inventory['pdfs'] if x['path']=='顺序重排版/合订本/70篇插图英语阅读小册 新顺序合订本.pdf')
    cover,book=build_new_book(INPUTS/(baseline['sha']+'.pdf'))
    tasks=[{'input':str(INPUTS/(x['sha']+'.pdf')),'label':x['path'],'source_commit':source_commit,
            'reference':x['path'].startswith('素材库/')} for x in unique.values()]
    tasks += [{'input':str(cover),'label':'新增封面及全书/考研学人-书封.pdf','source_commit':source_commit},
              {'input':str(book),'label':'新增封面及全书/考研学人-70篇新顺序合订本.pdf','source_commit':source_commit}]
    results={};failures=[]
    with ProcessPoolExecutor(max_workers=2) as pool:
        future_map={pool.submit(process_one,t):t for t in tasks}
        for number,future in enumerate(as_completed(future_map),1):
            task=future_map[future]
            try:
                result=future.result();results[sha(Path(task['input']))]=result
            except Exception as error:
                failures.append({'task':task,'error':repr(error)})
                print(json.dumps({'failed':task['label'],'error':repr(error)},ensure_ascii=False),flush=True)
            write(WORK/'progress.json',{'completed':number,'total':len(tasks),'failures':failures})
            if number%10==0 or number==len(tasks):print(json.dumps({'completed':number,'total':len(tasks),'failures':len(failures)}),flush=True)
    assert not failures,failures
    records=[]
    existing=[{**x,'input':str(INPUTS/(x['sha']+'.pdf'))} for x in inventory['pdfs']]
    new=[{'path':t['label'],'input':t['input'],'sha':None} for t in tasks[-2:]]
    for item in existing+new:
        key=sha(Path(item['input']));result=results[key];dest=ROOT/'所有PDF'/item['path'];dest.parent.mkdir(parents=True,exist_ok=True)
        if dest.exists():dest.unlink()
        os.link(UNIQUE/(key+'.pdf'),dest)
        records.append({'original_path':item['path'],'source_git_blob':item['sha'],
                        'pdf':str(dest.relative_to(ROOT)),**{k:v for k,v in result.items() if k not in ['input_path','page_pixel_SHA256']}})
    book_record=next(r for r in records if r['original_path']==tasks[-1]['label'])
    cover_record=next(r for r in records if r['original_path']==tasks[-2]['label'])
    result={'passed':True,'repository':'alienalgorithm/postgraduate-vocabulary',
       'release_tag':'punk-english-pdfs-2026.11.13-v1','source_commit':source_commit,
       'owner':'朋克英语','layer_name':LAYER_NAME,'default_hidden':True,
       'existing_PDF_paths':len(inventory['pdfs']),'new_PDFs':2,'PDF_paths':len(records),
       'unique_PDFs':len(results),'pages_in_unique_PDFs':sum(v['pages'] for v in results.values()),
       'all_normal_page_pixels_and_text_preserved':True,'all_layers_reveal_verified':True,
       'book':book_record,'cover':cover_record,'files':records}
    write(ROOT/'manifest.json',result)
    with fitz.open(ROOT/book_record['pdf']) as d:
        d[0].get_pixmap(matrix=fitz.Matrix(1.8,1.8),alpha=False).save(ROOT/'核验/封面-正常阅读.png')
        d[1].get_pixmap(matrix=fitz.Matrix(1.8,1.8),alpha=False).save(ROOT/'核验/目录首页-正常阅读.png')
        d.set_layer_ui_config(next(x for x in d.layer_ui_configs() if x['text']==LAYER_NAME)['number'],action=0)
        d[0].get_pixmap(matrix=fitz.Matrix(1.8,1.8),alpha=False).save(ROOT/'核验/封面-显示署名.png')
        d[8].get_pixmap(matrix=fitz.Matrix(1.8,1.8),alpha=False).save(ROOT/'核验/首篇-显示署名.png')
    print(json.dumps({k:v for k,v in result.items() if k not in ['files','book','cover']},ensure_ascii=False),flush=True)

if __name__=='__main__':main()
