"""Original renderer static-only 1080p/4K views for source65 authorized country focus."""
import ast,datetime,functools,hashlib,importlib.util,json,os,sys
from pathlib import Path
import PIL
from PIL import Image
B=Path('/workspace/work/video-audit70-20261113');H=Path(__file__).resolve().parent;OLD=B/'final-layout';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m
def rgb(p):
 with Image.open(p)as im:return hashlib.sha256(im.convert('RGB').tobytes()).hexdigest()
assert PIL.__version__=='12.3.0'
renderer=OLD/'official/render.py';maker=OLD/'official/make_video.py';oldreport=json.loads((OLD/'report.json').read_text());assert sha(renderer)==oldreport['renderer_sha256']
for f,v in oldreport['official_font_sha256'].items():assert sha(OLD/'fonts'/f)==v
theme=next(n.value for n in ast.parse(maker.read_bytes()).body if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='T'for t in n.targets)and isinstance(n.value,ast.Call)and any(k.arg=='BG_TOP'for k in n.value.keywords))
before=H/'before/视频/脚本/65.json';after=H/'candidate-payload/视频/脚本/65.json'
report={'article':'65','book_order':'37','kind':'isolated_draft_static_only_no_MP4','user_records':['091','093'],'passed':False,'renderer_sha256':sha(renderer),'maker_theme_sha256':sha(maker),'font_sha256':oldreport['official_font_sha256'],'Pillow':PIL.__version__,'before_source_sha256':sha(before),'after_source_sha256':sha(after),'no_PAY_CI_audio_video_PDF_modified':True,'resolutions':[]}
for scale in [1,2]:
 os.environ['VIDEO_S']=str(scale);R=load('actual65_static_renderer_'+str(scale),renderer);R.F=str(OLD/'fonts')+'/'
 assert(R.W,R.H)==(1920*scale,1080*scale)
 for k in theme.keywords:setattr(R,k.arg,ast.literal_eval(k.value))
 for name,default in [('EN',600),('ZH',500)]:
  original=getattr(R,name)
  def wrap(original,default):
   @functools.lru_cache(maxsize=256)
   def cached(size,weight=None):
    f=original(size,default if weight is None else weight);f.getlength=functools.lru_cache(maxsize=1024)(f.getlength);return f
   return cached
  setattr(R,name,wrap(original,default))
 folder=H/('static-1080'if scale==1 else'static-4K');folder.mkdir(exist_ok=True);row={'width':R.W,'height':R.H,'scale':scale,'sources':[]}
 for label,path in [('before',before),('after',after)]:
  d=json.loads(path.read_text());summary=R.拆出简述页(d);R.apply_script(d);colors=R.分色(d);R.unify_colors(colors,d['sentences']);metrics=[];renders=[]
  for si,sentence in enumerate(d['sentences'],1):
   chunks=[[tuple(x)for x in c['align']]for c in sentence['chunks']];notes=[c.get('note')for c in sentence['chunks']];cs=R.sent_colors(colors,sentence);natural=R.max_es(chunks,cs,notes);cap=d.get('字号上限',{}).get('S'+str(si));size=min(natural,100*scale,float(cap)*scale if cap is not None else 100*scale);size=int(size)if size==int(size)else size
   _,height,width,_=R._measure(chunks,cs,notes,size,R._grouping(chunks,cs));orphan=R.orphan_lines(chunks,cs,notes,size);item={'sentence':si,'font_px':size,'natural_font_px':natural,'width_px':width,'height_px':height,'within_bounds':width<=R.MAXW2 and height<=R.MAXH2,'orphans':orphan};metrics.append(item);assert item['within_bounds']and not orphan,(scale,label,item)
   if si in [1,11,17]:
    for active in ([0,1]if si==17 else[0]):
     suffix='body-last-active2'if active==1 else'country-focus';p=folder/f'{label}-S{si:02}-{suffix}.png';R.ES_FIXED=size;R.frame_interlinear(chunks,cs,'',1,str(p),active=active,notes=notes);renders.append({'sentence':si,'active_chunk':active+1,'path':str(p),'PNG_sha256':sha(p),'RGB_sha256':rgb(p),'font_px':size,'total_layout_height_px':height,'vertical_margin_px':(R.H-height)/2})
  font,lines,points=R.简述排(summary);assert len(points)==5;p=folder/(label+'-summary.png');R.frame_简述(summary,1,str(p));card={'path':str(p),'font_px':font,'point_count':len(points),'PNG_sha256':sha(p),'RGB_sha256':rgb(p),'text_sha256':hashlib.sha256(summary.encode()).hexdigest(),'rows':[''.join(ch for ch,_ in line)for line in lines]}
  row['sources'].append({'label':label,'sentences':metrics,'country_focus_renders':renders,'focus_colors':{k:v for k,v in colors.items()if k in ['Norway','archipelago','Lebanon','Morocco','sowed']},'summary':card})
 old,new=row['sources'];assert all(old['summary'][k]==new['summary'][k]for k in ['font_px','point_count','RGB_sha256','text_sha256','rows'])
 # Source65's original summary size is article-specific; preserve its actual value.
 row.update(all17_sentences_both_sources_no_overflow_or_orphans=True,summary_text_font_rows_and_pixels_exact=True,changed_pages_pixel_identity_not_claimed=True);report['resolutions'].append(row)
report.update(passed=True,recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat());p=H/'static-render-report.json';p.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'passed':True,'report':str(p),'bytes':p.stat().st_size,'sha256':sha(p)},ensure_ascii=False))
