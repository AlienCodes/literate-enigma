from pathlib import Path
import json,hashlib,re,sys
import fitz
from PIL import Image,ImageDraw
ROOT=Path('/workspace/work/booklet70')
sys.path.insert(0,str(ROOT))
from booklet_utils import atomic_json
ORDER=json.loads(Path('/workspace/work/order70-recommended.json').read_text())['order']
OUT=ROOT/'workers/volume-independent-01-12';OUT.mkdir(exist_ok=True)
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
norm=lambda s:re.sub(r'\s+','',s)

def stack(paths,target,cols,width=700):
 images=[]
 for path,label in paths:
  im=Image.open(path).convert('RGB');height=round(im.height*width/im.width)
  im=im.resize((width,height),Image.Resampling.LANCZOS)
  tile=Image.new('RGB',(width,height+28),'#e8ece8');tile.paste(im,(0,28));ImageDraw.Draw(tile).text((8,6),label,fill='#173d32');images.append(tile)
 rows=(len(images)+cols-1)//cols;cellh=max(im.height for im in images)
 result=Image.new('RGB',(cols*(width+12)+12,rows*(cellh+12)+12),'#e8ece8')
 for k,im in enumerate(images):result.paste(im,(12+(k%cols)*(width+12),12+(k//cols)*(cellh+12)))
 result.save(target)

def inspect(v):
 n=f'{v:02}';q=json.loads((ROOT/'volumes'/n/'qc.json').read_text());assert q['passed'] and sha(q['pdf'])==q['pdf_sha256']
 d=fitz.open(q['pdf']);items=q['articles'];assert len(items)==10
 assert [i['id'] for i in items]==ORDER[(v-1)*10:v*10]
 expected=2;records=[];bookmarks=d.get_toc();assert len(bookmarks)==11 and bookmarks[0]==[1,'目录',1]
 links=sorted(d[0].get_links(),key=lambda x:x['from'].y0);assert len(links)==10
 for index,(item,link) in enumerate(zip(items,links)):
  assert item['position']==(v-1)*10+index+1 and item['start_page']==expected
  assert link['kind']==fitz.LINK_GOTO and link['page']==expected-1
  label=d[0].get_textbox(link['from']);compact=norm(label)
  assert f'{item["position"]:02}/{item["id"]}' in compact,(n,item['id'],label)
  assert norm(item['title_zh']) in compact,(n,item['id'],label)
  assert compact.endswith(str(expected)),(n,item['id'],label)
  assert bookmarks[index+1]==[1,f'{item["position"]:02} / 第{item["id"]}篇 {item["title_zh"]}',expected]
  with fitz.open(item['pdf']) as source:
   assert len(source)==item['pages'] and sha(item['pdf'])==item['pdf_sha256']
   assert d[expected-1].get_text()==source[0].get_text(),('cover mismatch',n,item['id'])
   assert d[expected+item['pages']-2].get_text()==source[-1].get_text(),('end mismatch',n,item['id'])
   assert d[expected-1].rect==source[0].rect
  records.append({'position':item['position'],'article':item['id'],'printed_start_page':expected,'link_target_index':link['page'],'bookmark_start_page':bookmarks[index+1][2],'printed_row':label.strip(),'chapter_cover_and_last_page_match':True})
  expected+=item['pages']
 assert len(d)==expected-1==q['pages']
 folder=OUT/n;folder.mkdir(exist_ok=True)
 picks=[('cover-first',items[0]['start_page']-1,items[0]['id']),('cover-middle',items[5]['start_page']-1,items[5]['id']),('cover-last',items[9]['start_page']-1,items[9]['id']),('english',items[0]['start_page'],items[0]['id']),('chinese',items[5]['start_page']+1,items[5]['id']),('vocabulary',items[9]['start_page']+2,items[9]['id'])]
 previews=[];art=[];text=[];samples=[]
 for label,page,article in picks:
  pg=d[page];path=folder/f'{label}.png';pg.get_pixmap(matrix=fitz.Matrix(1.6,1.6),alpha=False).save(path)
  previews.append((path,f'Volume {v} / {label} / article {article} / merged page {page+1}'))
  info={'kind':label,'article':article,'merged_page':page+1,'page_png':str(path)}
  if label.startswith('cover'):
   imgs=pg.get_image_info(xrefs=True);im=max(imgs,key=lambda z:fitz.Rect(z['bbox']).get_area());box=fitz.Rect(im['bbox']);detail=folder/f'{label}-art.png';pg.get_pixmap(matrix=fitz.Matrix(1000/box.width,1000/box.width),clip=box,alpha=False).save(detail)
   info.update({'art_pixels':[im['width'],im['height']],'art_detail_png':str(detail)});art.append((detail,f'Volume {v} / article {article} / actual merged-PDF art'))
  else:
   assert len(pg.get_text())>200
   fonts=pg.get_fonts();assert fonts
   info['vector_fonts']=list(dict.fromkeys(f[3] for f in fonts))
   box=fitz.Rect(35,80,pg.rect.width-35,350);detail=folder/f'{label}-detail.png';pg.get_pixmap(matrix=fitz.Matrix(2,2),clip=box,alpha=False).save(detail)
   info['text_detail_png']=str(detail);text.append((detail,f'Volume {v} / {label} / merged page {page+1}'))
  samples.append(info)
 stack(previews,folder/'six-page-contact.png',2,610)
 stack(art,folder/'three-art-details.png',1,1000)
 stack(text,folder/'three-text-details.png',1,860)
 evidence={'volume':v,'pdf_sha256':q['pdf_sha256'],'pdf':q['pdf'],'bytes':q['bytes'],'pages':len(d),'recommended_order_exact':True,'toc_rows_and_goto_targets':records,'all_10_bookmark_targets_match':True,'all_10_chapter_start_and_end_positions_match':True,'image_recompression_quality':q['jpeg_quality'],'samples':samples,'contact_sheet':str(folder/'six-page-contact.png'),'art_detail_sheet':str(folder/'three-art-details.png'),'text_detail_sheet':str(folder/'three-text-details.png'),'visual_review_pending':True}
 atomic_json(folder/'structural-evidence.json',evidence);d.close()
 print(json.dumps({'volume':v,'structural_pass':True,'rows':[(x['article'],x['printed_start_page']) for x in records],'samples':[(x['kind'],x['merged_page']) for x in samples]},ensure_ascii=False),flush=True)

for v in map(int,sys.argv[1:]):inspect(v)
