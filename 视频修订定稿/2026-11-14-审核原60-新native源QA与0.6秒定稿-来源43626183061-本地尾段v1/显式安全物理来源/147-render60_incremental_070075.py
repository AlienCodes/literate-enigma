"""Actual pinned original renderer, incremental authorized draft pages only; no MP4."""
import ast,datetime,functools,hashlib,importlib.util,json,os,sys
from pathlib import Path
import PIL
from PIL import Image
B=Path('/workspace/work/video-audit70-20261113');H=B/'article60-user-review-draft-20261114';O=Path('/dev/shm/article60-text-review-draft-20261114/static-070075');O.mkdir(exist_ok=True);F=B/'final-layout';CI=Path('/workspace/work/video-revision-batch-ci/.github/video-revision-batch/approved-video-layouts70.json');sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(n,p):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);sys.modules[n]=m;s.loader.exec_module(m);return m
def rgb(p):
 with Image.open(p)as im:return hashlib.sha256(im.convert('RGB').tobytes()).hexdigest()
assert PIL.__version__=='12.3.0';approval=json.loads(CI.read_text());a=next(x for x in approval['articles']if x['source_id']=='60');renderer=F/'official/render.py';maker=F/'official/make_video.py';assert sha(renderer)=='477a516f7100ac05dab15d3b176e2d8c49779aa4bd8713087b737f4d25833b67';theme=next(n.value for n in ast.parse(maker.read_bytes()).body if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='T'for t in n.targets)and isinstance(n.value,ast.Call)and any(k.arg=='BG_TOP'for k in n.value.keywords));before=H/'before/视频/脚本/60.json';after=H/'candidate-payload/视频/脚本/60.json';assert sha(after)=='8be8d9d4e0efcc6552b737b312af5697e188cdef4d70aeb8bb02976ba6cdc6fd';fonts=json.loads((F/'report.json').read_text())['official_font_sha256'];assert all(sha(F/'fonts'/k)==v for k,v in fonts.items())
targets={1:(1,'original-T34-apparent-vicinity'),7:(0,'accepted-to-dazzle-note070'),10:(1,'law071'),11:(0,'governs-ejects073'),13:(1,'miss074'),15:(0,'after-all075')};report=dict(article='60',book_order='36',draft_only=True,native_or_final_authorized=False,PAY_CI_audio_PDF_untouched=True,kind='actual-original-renderer-incremental-static070-075-and-T34-only',source_sha256=sha(after),reference_original_source_sha256=sha(before),renderer_sha256=sha(renderer),theme_maker_sha256=sha(maker),Pillow=PIL.__version__,fonts=fonts,prior062069_report_preserved={'path':str(H/'static-render-report.json'),'sha256':sha(H/'static-render-report.json')},resolutions=[])
for scale in[1,2]:
 os.environ['VIDEO_S']=str(scale);R=load('draft60incremental'+str(scale),renderer);R.F=str(F/'fonts')+'/'
 for k in theme.keywords:setattr(R,k.arg,ast.literal_eval(k.value))
 for name,default in[('EN',600),('ZH',500)]:
  original=getattr(R,name)
  def wrapper(original,default):
   @functools.lru_cache(maxsize=256)
   def cached(size,weight=None):
    f=original(size,default if weight is None else weight);f.getlength=functools.lru_cache(maxsize=1024)(f.getlength);return f
   return cached
  setattr(R,name,wrapper(original,default))
 folder=O/('1080'if scale==1 else'4K');folder.mkdir(exist_ok=True);res={'scale':scale,'sources':[]}
 for label,path in[('original-before',before),('after062075',after)]:
  d=json.loads(path.read_text());summary=R.拆出简述页(d);R.apply_script(d);colors=R.分色(d);R.unify_colors(colors,d['sentences']);metrics=[];renders=[]
  for si,(active,term)in targets.items():
   sent=d['sentences'][si-1];chunks=[[tuple(x)for x in c['align']]for c in sent['chunks']];notes=[c.get('note')for c in sent['chunks']];cs=R.sent_colors(colors,sent);natural=R.max_es(chunks,cs,notes);cap=d.get('字号上限',{}).get('S'+str(si));size=min(natural,100*scale,float(cap)*scale if cap is not None else 100*scale);size=int(size)if size==int(size)else size;_,height,width,_=R._measure(chunks,cs,notes,size,R._grouping(chunks,cs));orph=R.orphan_lines(chunks,cs,notes,size);metric=dict(sentence=si,font_px=size,natural_font_px=natural,width_px=width,height_px=height,within_bounds=width<=R.MAXW2 and height<=R.MAXH2,orphans=orph);metrics.append(metric);assert metric['within_bounds']and not orph,(scale,label,metric)
   if label=='after062075':
    p=folder/f'{label}-S{si:02}-C{active+1}-{term}.png';R.ES_FIXED=size;R.frame_interlinear(chunks,cs,'',1,str(p),active=active,notes=notes);renders.append(dict(sentence=si,active_chunk=active+1,path=str(p),PNG_sha256=sha(p),RGB_sha256=rgb(p)))
   if si==15:
    p=folder/f'{label}-actual-body-tail-S15-C2.png';R.ES_FIXED=size;R.frame_interlinear(chunks,cs,'',1,str(p),active=1,notes=notes);tail=dict(path=str(p),PNG_sha256=sha(p),RGB_sha256=rgb(p),font_px=size,width_px=width,height_px=height)
  size,lines,first=R.简述排(summary);p=folder/f'{label}-unchanged-summary.png';R.frame_简述(summary,1,str(p));card=dict(path=str(p),PNG_sha256=sha(p),RGB_sha256=rgb(p),font_px=size,point_count=len(first),rows=[''.join(ch for ch,_ in line)for line in lines],text_sha256=hashlib.sha256(summary.encode()).hexdigest(),canonical_unwrapped_text_sha256=hashlib.sha256(summary.replace('\n','').replace('▹','').encode()).hexdigest());assert len(first)==5
  if scale==2:assert card['font_px']==a['summary_font_4k_px']and card['RGB_sha256']==a['summary_rgb_sha256']and card['canonical_unwrapped_text_sha256']==a['approved_summary_text_sha256']
  res['sources'].append(dict(label=label,changed_page_metrics=metrics,changed_page_renders=renders,actual_body_tail=tail,summary=card))
 old,new=res['sources'];assert all(old['summary'][k]==new['summary'][k]for k in old['summary']if k!='path');res.update(incremental_pages_all_within_bounds_and_no_orphans=True,new_tail_RGB_equal_old=old['actual_body_tail']['RGB_sha256']==new['actual_body_tail']['RGB_sha256'],new_tail_geometry_equal_old=all(old['actual_body_tail'][k]==new['actual_body_tail'][k]for k in['font_px','width_px','height_px']),new_tail_text_focus_changed_by075=True,new_tail_must_be_retained_for_future_hold06=True,summary_text_font_rows_RGB_exact=True,focus_correspondence_preserved_fixed_RGB_not_claimed=True);report['resolutions'].append(res)
report.update(passed=True,actual_NEW_page_images_rendered=12,actual_NEW_body_tail_images_rendered=2,created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat());p=O/'incremental-static-report.json';p.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(dict(passed=True,report=str(p),sha256=sha(p),source_sha256=sha(after)),ensure_ascii=False))
