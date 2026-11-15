"""Read-only original renderer geometry for both actual native resolutions."""
import ast, functools, hashlib, importlib.util, json, os, sys
from pathlib import Path
import PIL

B=Path('/workspace/work/video-audit70-20261113/final-layout')
R=Path(__file__).resolve().parent
source=R/'artifact-files/09-actual-working-source.json'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert PIL.__version__ == '12.3.0'
official=json.loads((B/'report.json').read_text())
renderer=B/'official/render.py'
assert sha(renderer)==official['renderer_sha256']
for name,fingerprint in official['official_font_sha256'].items():
    assert sha(B/'fonts'/name)==fingerprint
maker=B/'official/make_video.py'
theme=next(n.value for n in ast.parse(maker.read_bytes()).body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='T' for t in n.targets) and isinstance(n.value,ast.Call) and any(k.arg=='BG_TOP' for k in n.value.keywords))
report={'kind':'actual-working-source09-original-renderer-dual-resolution-all-page-measurement','article':'09','book_order':'52','source_sha256':sha(source),'renderer_sha256':sha(renderer),'maker_theme_source_sha256':sha(maker),'font_sha256':official['official_font_sha256'],'no_source_or_audio_or_video_mutation':True,'resolutions':[]}
for scale in (1,2):
    os.environ['VIDEO_S']=str(scale)
    s=importlib.util.spec_from_file_location('actual09_original_renderer_'+str(scale),renderer)
    m=importlib.util.module_from_spec(s);sys.modules[s.name]=m;s.loader.exec_module(m);m.F=str(B/'fonts')+'/'
    for k in theme.keywords:setattr(m,k.arg,ast.literal_eval(k.value))
    for name,default in [('EN',600),('ZH',500)]:
        original=getattr(m,name)
        def wrap(original,default):
            @functools.lru_cache(maxsize=256)
            def cached(size,weight=None):
                f=original(size,default if weight is None else weight);f.getlength=functools.lru_cache(maxsize=1024)(f.getlength);return f
            return cached
        setattr(m,name,wrap(original,default))
    data=json.loads(source.read_text());summary=m.拆出简述页(data);m.apply_script(data);colors=m.分色(data);m.unify_colors(colors,data['sentences']);rows=[]
    for si,sent in enumerate(data['sentences'],1):
        chunks=[[tuple(x)for x in c['align']]for c in sent['chunks']];notes=[c.get('note')for c in sent['chunks']];cs=m.sent_colors(colors,sent);natural=m.max_es(chunks,cs,notes);cap=data.get('字号上限',{}).get('S'+str(si));size=min(natural,100*scale,float(cap)*scale if cap is not None else 100*scale);size=int(size)if size==int(size)else size
        _,height,width,_=m._measure(chunks,cs,notes,size,m._grouping(chunks,cs));orphans=m.orphan_lines(chunks,cs,notes,size)
        rows.append({'sentence':si,'font_px':size,'natural_font_px':natural,'width_px':width,'height_px':height,'width_limit_px':m.MAXW2,'height_limit_px':m.MAXH2,'within_bounds':width<=m.MAXW2 and height<=m.MAXH2,'orphans':orphans})
    font,lines,points=m.简述排(summary)
    report['resolutions'].append({'width':m.W,'height':m.H,'sentences':rows,'summary_font_px':font,'summary_point_count':len(points),'summary_rows':[''.join(ch for ch,_ in line)for line in lines],'all18_no_overflow_or_orphans':len(rows)==18 and all(x['within_bounds']and not x['orphans']for x in rows)})
report['passed']=all(x['all18_no_overflow_or_orphans'] and x['summary_point_count']==5 for x in report['resolutions'])
p=R/'actual-working-source09-original-dual-resolution-geometry-report.json';p.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'report':str(p),'sha256':sha(p),'bytes':p.stat().st_size,'passed':report['passed']},ensure_ascii=False))
assert report['passed']
