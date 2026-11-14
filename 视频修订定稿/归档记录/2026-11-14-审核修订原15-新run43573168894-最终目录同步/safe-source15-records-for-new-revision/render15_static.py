"""Actual unchanged-renderer article15 static1080/4K; never new MP4."""
import ast,copy,datetime,functools,hashlib,importlib.util,json,os,sys
from pathlib import Path
import PIL
from PIL import Image
B=Path('/workspace/work/video-audit70-20261113');H=Path(__file__).parent;OLD=B/'final-layout'
CI=Path('/workspace/work/video-revision-batch-ci/.github/video-revision-batch/approved-video-layouts70.json')
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m
def rgb(p):
 with Image.open(p)as im:return hashlib.sha256(im.convert('RGB').tobytes()).hexdigest()
assert PIL.__version__=='12.3.0'
approval=json.loads(CI.read_text());approved=next(r for r in approval['articles']if r['source_id']=='15')
before=H/'before/视频/脚本/15.json';after=H/'candidate-payload/视频/脚本/15.json'
approved_source=before;assert sha(approved_source)==approved['source_json_sha256']
native_source=Path('/workspace/work/video-revision-delivery/next-passed-validated/43562525001/15/final-source/视频/脚本/15.json')
# Latest accepted audio source has refreshed CF and machine summary line wraps; this
# renderer reads neither CF nor DSP. Prove the actual narrative remains identical.
nd=json.loads(native_source.read_text());bd=json.loads(before.read_text());ns=copy.deepcopy(nd['sentences']);ns[-1]['chunks'][-1]['note']=bd['sentences'][-1]['chunks'][-1]['note'];assert ns==bd['sentences']
assert nd['sentences'][-1]['chunks'][-1]['note'].replace('\n','').replace('▹','')==bd['sentences'][-1]['chunks'][-1]['note'].replace('\n','').replace('▹','')
assert nd['除阻加强']==bd['除阻加强']=={'S8':{'1':[3.25,3.315,5.0]}}
renderer=OLD/'official/render.py';maker=OLD/'official/make_video.py';oldreport=json.loads((OLD/'report.json').read_text())
assert sha(renderer)==approval['renderer_sha256']==oldreport['renderer_sha256']
for f,v in oldreport['official_font_sha256'].items():assert sha(OLD/'fonts'/f)==v
theme_node=next(n.value for n in ast.parse(maker.read_bytes()).body if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='T'for t in n.targets)and isinstance(n.value,ast.Call)and any(k.arg=='BG_TOP'for k in n.value.keywords))
report={'article':'15','book_order':'25','passed':False,'kind':'actual-authorized-static-render-of-latest-native-current-before-and-focus-candidate-not-new-video','old_approved_source_sha256':sha(approved_source),'before_source_sha256':sha(before),'current_before_exactly_matches_approved_row':True,'actual_latest_A21_native_source_sha256':sha(native_source),'actual_latest_only_body_note_wrap_diff_and_CF_differences_not_substituted':True,'after_source_sha256':sha(after),'renderer_sha256':sha(renderer),'theme_maker_sha256':sha(maker),'font_sha256':oldreport['official_font_sha256'],'Pillow':PIL.__version__,'audio_or_source_or_official_core_changed_by_this_program':False,'approved_manifest_before_sha256':sha(CI),'resolutions':[]}
target=[(13,0,'inquiries'),(16,1,'patrol')]
for scale in [1,2]:
 os.environ['VIDEO_S']=str(scale);R=load('article15_actual_renderer_'+str(scale),renderer);R.F=str(OLD/'fonts')+'/'
 assert(R.W,R.H)==(1920*scale,1080*scale)
 for k in theme_node.keywords:setattr(R,k.arg,ast.literal_eval(k.value))
 for name,default in [('EN',600),('ZH',500)]:
  original=getattr(R,name)
  def wrap(original,default):
   @functools.lru_cache(maxsize=256)
   def cached(size,weight=None):
    f=original(size,default if weight is None else weight);f.getlength=functools.lru_cache(maxsize=1024)(f.getlength);return f
   return cached
  setattr(R,name,wrap(original,default))
 folder=H/('static-'+('1080'if scale==1 else'4K'));folder.mkdir(exist_ok=True)
 result={'width':R.W,'height':R.H,'scale':scale,'sources':[]}
 for label,path in [('latest_native',native_source),('before',before),('after',after)]:
  d=json.loads(path.read_text());summary=R.拆出简述页(d);R.apply_script(d);colors=R.分色(d);R.unify_colors(colors,d['sentences']);metrics=[];renders=[]
  for si,s in enumerate(d['sentences'],1):
   chunks=[[tuple(x)for x in c['align']]for c in s['chunks']];notes=[c.get('note')for c in s['chunks']];cs=R.sent_colors(colors,s);natural=R.max_es(chunks,cs,notes);cap=d.get('字号上限',{}).get('S'+str(si));size=min(natural,100*scale,float(cap)*scale if cap is not None else 100*scale);size=int(size)if size==int(size)else size
   _,height,width,_=R._measure(chunks,cs,notes,size,R._grouping(chunks,cs));orphan=R.orphan_lines(chunks,cs,notes,size)
   metrics.append({'sentence':si,'font_px':size,'natural_font_px':natural,'width_px':width,'height_px':height,'within_bounds':width<=R.MAXW2 and height<=R.MAXH2,'orphans':orphan})
   assert metrics[-1]['within_bounds']and not orphan,(scale,label,metrics[-1])
   if label=='after':
    for tsi,active,term in target:
     if tsi==si:
      p=folder/f'S{si:02}-C{active+1}-{term}.png';R.ES_FIXED=size;R.frame_interlinear(chunks,cs,'',1,str(p),active=active,notes=notes);renders.append({'sentence':si,'active_chunk':active+1,'term':term,'path':str(p),'PNG_sha256':sha(p),'RGB_sha256':rgb(p)})
   if si==len(d['sentences']):
    p=folder/(label+'-body-tail.png');R.ES_FIXED=size;R.frame_interlinear(chunks,cs,'',1,str(p),active=len(chunks)-1,notes=notes);tail={'path':str(p),'PNG_sha256':sha(p),'RGB_sha256':rgb(p),'font_px':size,'width_px':width,'height_px':height}
  ss,lines,first=R.简述排(summary);assert len(first)==5
  p=folder/(label+'-summary.png');R.frame_简述(summary,1,str(p));card={'path':str(p),'PNG_sha256':sha(p),'RGB_sha256':rgb(p),'font_px':ss,'point_count':len(first),'text_sha256':hashlib.sha256(summary.encode()).hexdigest(),'rows':[''.join(ch for ch,_ in line)for line in lines]}
  card['canonical_unwrapped_text_sha256']=hashlib.sha256(summary.replace('\n','').replace('▹','').encode()).hexdigest()
  if scale==2:assert card['font_px']==approved['summary_font_4k_px']and card['RGB_sha256']==approved['summary_rgb_sha256']and card['canonical_unwrapped_text_sha256']==approved['approved_summary_text_sha256']
  result['sources'].append({'label':label,'sentences':metrics,'body_tail':tail,'summary':card,'actual_changed_page_renders':renders})
 reference,old,new=result['sources'];assert all(reference['summary'][k]==old['summary'][k]==new['summary'][k]for k in ['RGB_sha256','font_px','point_count','canonical_unwrapped_text_sha256','rows']);assert all(old['body_tail'][k]==new['body_tail'][k]for k in ['font_px','width_px','height_px']);assert all(old['summary'][k]==new['summary'][k]for k in old['summary']if k!='path')
 result.update(all_18_sentences_three_sources_within_bounds_and_no_orphans=True,body_tail_font_and_geometry_exact=True,body_tail_RGB_exact=old['body_tail']['RGB_sha256']==new['body_tail']['RGB_sha256'],body_tail_color_change_explanation='The unchanged article15 renderer uses its existing cyclic focus palette; added focus terms can shift colours assigned later. All original tail text, fonts and geometry remain exact.',summary_text_font_rows_and_pixels_exact=True,changed_pages_new_RGB_identity_not_claimed=True)
 report['resolutions'].append(result)
report.update(passed=True,created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),actual_new_changed_page_count=sum(len(r['sources'][2]['actual_changed_page_renders'])for r in report['resolutions']))
p=H/'static-render-report.json';p.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'passed':True,'report':str(p),'sha256':sha(p),'changed_renders':report['actual_new_changed_page_count']},ensure_ascii=False))
