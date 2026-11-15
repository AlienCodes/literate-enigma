from pathlib import Path
import ast,copy,functools,hashlib,importlib.util,json,math,os,sys
import argparse,tempfile
import numpy as np
from PIL import Image
p=argparse.ArgumentParser()
for name in ['tools','source','old-renderer','new-renderer','output']:p.add_argument('--'+name,type=Path,required=True)
A=p.parse_args();TEMP=tempfile.TemporaryDirectory(prefix='source64-renderer-static-controls-');D=Path(TEMP.name);O=A.tools;OLD=A.old_renderer;NEW=A.new_renderer;maker=O/'make_video.py';source=json.loads(A.source.read_text())
assert hashlib.sha256(OLD.read_bytes()).hexdigest()=='477a516f7100ac05dab15d3b176e2d8c49779aa4bd8713087b737f4d25833b67'
assert hashlib.sha256(NEW.read_bytes()).hexdigest()=='323d8440d89659783cdc36615c5fa84069a51dfff33a8b1a3cf3f83002b58122'
assert hashlib.sha256(maker.read_bytes()).hexdigest()=='4c85e1fbdd2e82c5646d5f58df63c85eca60af4ef521f1d36f765575a568d6f3'
assert hashlib.sha256(A.source.read_bytes()).hexdigest()=='c1625706d1674fb8b05fef0cb66ce4fd929bd35e536891a294bf8066c6b32f8e'
assert source['no']=='64' and source['正常分栏连线'] is True
theme=next(n.value for n in ast.parse(maker.read_text()).body if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='T'for t in n.targets)and isinstance(n.value,ast.Call)and any(k.arg=='BG_TOP'for k in n.value.keywords))
def sp(p):p=Path(p);b=p.read_bytes();return{'path':str(p),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
def rgb(p):
 with Image.open(p)as im:return np.asarray(im.convert('RGB')).copy()
records=[];counter=0

def render(path,label,si,active,link=True,opt=True,spy=False):
 global counter
 label="v2-"+label
 counter+=1;os.environ['VIDEO_S']='2';ss=importlib.util.spec_from_file_location('source64_normal_links_'+str(counter),path);m=importlib.util.module_from_spec(ss);sys.modules[ss.name]=m;ss.loader.exec_module(m);m.F=str(O/'fonts')+'/'
 for k in theme.keywords:setattr(m,k.arg,ast.literal_eval(k.value))
 for n,w in [('EN',600),('ZH',500)]:
  orig=getattr(m,n)
  def cache(orig,w):
   @functools.lru_cache(maxsize=256)
   def f(s,weight=None):
    x=orig(s,w if weight is None else weight);x.getlength=functools.lru_cache(maxsize=1024)(x.getlength);return x
   return f
  setattr(m,n,cache(orig,w))
 d=copy.deepcopy(source);d['连线']=d['连线']if link else[];d['正常分栏连线']=opt;summary=m.拆出简述页(d);m.apply_script(d);colors=m.分色(d);m.unify_colors(colors,d['sentences']);s=d['sentences'][si-1];chunks=[[tuple(x)for x in c['align']]for c in s['chunks']];notes=[c.get('note')for c in s['chunks']];cs=m.sent_colors(colors,s);natural=m.max_es(chunks,cs,notes);cap=d.get('字号上限',{}).get('S'+str(si));size=min(natural,200,float(cap)*2 if cap is not None else 200);size=int(size)if size==int(size)else size;_,height,width,_=m._measure(chunks,cs,notes,size,m._grouping(chunks,cs));orphans=m.orphan_lines(chunks,cs,notes,size);assert width<=m.MAXW2 and height<=m.MAXH2 and not orphans,(si,width,height,orphans)
 calls=[]
 if spy:
  primitive=m._link_under
  class Proxy:
   def __init__(self,draw):self.draw=draw
   def __getattr__(self,name):return getattr(self.draw,name)
   def line(self,xy,*a,**kw):calls.append({'xy':list(xy),'fill':list(kw.get('fill')),'width':kw.get('width')});return self.draw.line(xy,*a,**kw)
  def observe(draw,units,font,y):return primitive(Proxy(draw),units,font,y)
  m._link_under=observe
 p=D/f'{label}-S{si:02}-C{active+1}-4K.png';m.ES_FIXED=size;m.frame_interlinear(chunks,cs,'',1,str(p),active=active,notes=notes)
 r={'label':label,'sentence':si,'active_chunk':active+1,'source':sp(A.source),'renderer':sp(path),'original_link_phrases':d['连线'],'explicit_normal_optin':opt,'font_px':size,'height_px':height,'width_px':width,'within_original_bounds_no_orphans':True,'image':sp(p),'RGB_sha256':hashlib.sha256(rgb(p).tobytes()).hexdigest(),'recorded_existing_primitive_line_strokes':calls,'plain_colors':{'English':list(m.FG_EN),'Chinese':list(m.FG_ZH)}};records.append(r);return r
try:
 base=render(OLD,'original-without-links',2,1,False,False);oldlinks=render(OLD,'original-explicit-links-ineffective',2,1,True,True);newspy=render(NEW,'new-explicit-links-observed',2,1,True,True,True);newactual=render(NEW,'new-explicit-links-actual',2,1,True,True);newoff=render(NEW,'new-no-optin',2,1,True,False);newempty=render(NEW,'new-no-links',2,1,False,True)
 assert base['RGB_sha256']==oldlinks['RGB_sha256']==newoff['RGB_sha256']==newempty['RGB_sha256'];assert newspy['RGB_sha256']==newactual['RGB_sha256'];assert len(newspy['recorded_existing_primitive_line_strokes'])==2;fills=[x['fill']for x in newspy['recorded_existing_primitive_line_strokes']];assert fills==[newspy['plain_colors']['English'],newspy['plain_colors']['Chinese']]
 a=rgb(base['image']['path']);b=rgb(newactual['image']['path']);different=np.any(a!=b,axis=2);assert different.any();mask=np.zeros(different.shape,dtype=bool)
 for line in newspy['recorded_existing_primitive_line_strokes']:
  (x0,y0),(x1,y1)=line['xy'];pad=line['width']+2;left=max(0,math.floor(min(x0,x1))-pad);right=min(3840,math.ceil(max(x0,x1))+pad+1);top=max(0,math.floor(min(y0,y1))-pad);bottom=min(2160,math.ceil(max(y0,y1))+pad+1);mask[top:bottom,left:right]=True
 assert not np.any(different&~mask);ys,xs=np.where(different);pixelproof={'original_LINKS_metadata_alone_entire_RGB_identical':True,'new_optin_disabled_or_noLINKS_entire_RGB_identical_to_original':True,'actual_unwrapped_renderer_pixels_equal_observation_proxy':True,'exact_two_existing_primitive_line_strokes':newspy['recorded_existing_primitive_line_strokes'],'both_lines_use_ordinary_foreground_colors':True,'all_RGB_pixels_outside_two_stroke_envelopes_exact':True,'different_pixel_count':int(different.sum()),'different_pixel_bbox':[int(xs.min()),int(ys.min()),int(xs.max())+1,int(ys.max())+1]}
 keyword=[]
 for si,active,label in [(3,0,'taps'),(3,1,'queue'),(5,2,'metropolitan-area'),(7,1,'deadline')]:
  original=render(OLD,'original-keywords-'+label,si,active);new=render(NEW,'new-keywords-'+label,si,active);assert original['RGB_sha256']==new['RGB_sha256'];keyword.append({'target':label,'original':original['image'],'new':new['image'],'entire_RGB_equal':True})
 report={'kind':'actual_4K_static_original_AB_links_ineffective_and_code_only_narrow_optin_underlines','source':sp(A.source),'original_renderer':sp(OLD),'proposal_renderer':sp(NEW),'original_theme':sp(maker),'pixel_scope':pixelproof,'all_static_executions':records,'keyword_pages_original_and_patch_pixels_exact':keyword,'not_native_video_audio_or_code_certification_acceptance':True,'new_actual_original_fullquick_stamp_still_required_before_formal_execution':True}
 for rec in records:
  rec['private_image_name']=Path(rec['image']['path']).name
  del rec['image']['path']
 report['all_static_PNGs_private_temporary_and_deleted_after_measurement']=True
 report['no_TTS_models_GT_ASR_audio_encoding_or_source_write']=True
 p=A.output;p.parent.mkdir(parents=True,exist_ok=True);assert not p.exists();p.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(sp(p),ensure_ascii=False))

finally:
 TEMP.cleanup()
