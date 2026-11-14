from pathlib import Path
import ast,copy,functools,importlib.util,json,os,sys
B=Path('/workspace/work/video-audit70-20261113');H=Path(__file__).parent;os.environ['VIDEO_S']='1';sp=importlib.util.spec_from_file_location('original47_layout_probe',B/'final-layout/official/render.py');R=importlib.util.module_from_spec(sp);sp.loader.exec_module(R);R.F=str(B/'final-layout/fonts')+'/'
for name,default in [('EN',600),('ZH',500)]:
 original=getattr(R,name)
 def wrap(original,default):
  @functools.lru_cache(maxsize=256)
  def cached(size,weight=None):
   f=original(size,default if weight is None else weight);f.getlength=functools.lru_cache(maxsize=1024)(f.getlength);return f
  return cached
 setattr(R,name,wrap(original,default))
d=json.loads((B/'payload/视频/脚本/47.json').read_text());R.拆出简述页(d);R.apply_script(d);colors=R.分色(d);R.unify_colors(colors,d['sentences']);s=d['sentences'][3];old=s['chunks'][-1]['note'];opts={'current_four_rows':old,'exact_words_one_row':old.replace('\n',' ').replace(' -> ','→'),'concise_same_four_mechanisms':'（狼回归（威慑力）→麋鹿不敢在河边吃草（行为改变）→柳树繁茂（植被恢复）→河岸泥土固定（地貌重塑））','concise_natural':'（狼群回归施威→麋鹿不敢在河边吃草→柳树繁茂起来→河岸泥土得以固定）'};results=[]
for name,note in opts.items():
 ss=copy.deepcopy(s);ss['chunks'][-1]['note']=note;chunks=[[tuple(p)for p in c['align']]for c in ss['chunks']];notes=[c.get('note')for c in ss['chunks']];cs=R.sent_colors(colors,ss);size=min(R.max_es(chunks,cs,notes),100);_,height,width,params=R._measure(chunks,cs,notes,size,R._grouping(chunks,cs));results.append({'name':name,'note':note,'note_characters':len(note),'main_font_1080_px':size,'note_font_1080_px':int(int(size*R.ZR)*.9),'height':height,'width':width,'wide_notes':R.wide_notes(chunks,cs,notes,size),'orphans':R.orphan_lines(chunks,cs,notes,size)})
p=H/'actual-note-one-line-width-candidates.json';p.write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n');print(json.dumps(results,ensure_ascii=False))
