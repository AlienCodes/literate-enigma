"""Verify real staged edits and generate clearly labelled static image evidence; no video/PDF."""
import ast,copy,hashlib,importlib.util,json,os,re,sys
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont

ROOT=Path('/workspace/work/github-publication/target')
OUT=Path('/workspace/work/video-audit70-20261113')
PAY=OUT/'payload'
REPORT=PAY/'视频/制作记录/旧简述清理-2026-11-13'
os.environ['VIDEO_S']='2';sys.dont_write_bytecode=True
spec=importlib.util.spec_from_file_location('canonical_static_renderer','/workspace/work/video05-keywords/render.py')
R=importlib.util.module_from_spec(spec);spec.loader.exec_module(R)
R.F='/workspace/work/audit-repo/视频/工具/fonts/'
module=ast.parse(Path('/workspace/work/video05-keywords/make_video.py').read_text())
node=next(n.value for n in module.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='T' for t in n.targets) and isinstance(n.value,ast.Call) and any(k.arg=='BG_TOP' for k in n.value.keywords))
for k in node.keywords:setattr(R,k.arg,ast.literal_eval(k.value))
result=json.loads((OUT/'cleanup-validation.json').read_text());ids=result['original_ids']

def clean_en(text):return re.sub(r'\{\{.*?\}\}','',text).replace('**','')
def clean_zh(text):
    text=re.sub(r'\{\{.*?\}\}','',text,flags=re.S)
    return re.sub(r'\*\*([^*]+)\*\*\([^)]*\)',r'\1',text).replace('**','').replace('\n','')

all70=[]
for n in range(1,71):
    no=f'{n:02d}';before=json.loads((OUT/'sources'/f'{no}.json').read_text())
    staged=PAY/f'视频/脚本/{no}.json';after=json.loads(staged.read_text()) if staged.exists() else copy.deepcopy(before)
    bs=before['sentences'][-1]['chunks'][-1]['note'].split('（简述：',1)[1]
    ns=after['sentences'][-1]['chunks'][-1]['note'].split('（简述：',1)[1]
    assert bs==ns,no
    for old_s,new_s in zip(before['sentences'],after['sentences']):
        assert len(old_s['chunks'])==len(new_s['chunks']),no
        for old_c,new_c in zip(old_s['chunks'],new_s['chunks']):
            assert clean_en(old_c['en'])==clean_en(new_c['en']),(no,'English words')
            assert clean_zh(old_c['zh'])==clean_zh(new_c['zh']),(no,'Chinese body words')
    c=copy.deepcopy(after);summary=R.拆出简述页(c)
    assert summary.startswith('（简述：')
    prefix=c['sentences'][-1]['chunks'][-1].get('note','')
    if no in ids:
        assert '（结局：' not in prefix
        old=next(x['removed_legacy_exact'] for x in result['changes'] if x['original_id']==no)
        assert old not in prefix
    all70.append({'id':no,'new_summary_sha256':hashlib.sha256(summary.encode()).hexdigest(),'new_summary_preserved':True,'visible_english_and_chinese_body_preserved':True,'legacy_removed':no in ids})

preview=REPORT/'清理后静态预览';preview.mkdir(exist_ok=True)
def body_frame(data,si,ci,path):
    d=copy.deepcopy(data);R.拆出简述页(d);R.apply_script(d)
    colors=R.分色(d);R.unify_colors(colors,d['sentences'])
    s=d['sentences'][si];cs=R.sent_colors(colors,s)
    chunks=[[tuple(p) for p in c['align']] for c in s['chunks']];notes=[c.get('note') for c in s['chunks']]
    es=min(R.max_es(chunks,cs,notes),100*R.S)
    for key,limit in d.get('字号上限',{}).items():
        if int(key[1:])-1==si:es=min(es,float(limit)*R.S)
    R.ES_FIXED=es
    R.frame_interlinear(chunks,cs,'',.98,str(path),active=ci,notes=notes)
    groups=R._grouping(chunks,cs);rowsets,total,width,dims=R._measure(chunks,cs,notes,es,groups)
    assert total<=R.H+1,(data['no'],'body height')
    return {'font_px':es,'total_height':total,'measured_width':width,'rows':groups},(rowsets,dims,cs)

for no in ids:
    d=json.loads((PAY/f'视频/脚本/{no}.json').read_text())
    body_frame(d,len(d['sentences'])-1,len(d['sentences'][-1]['chunks'])-1,preview/f'{no}-正文尾页-静态预览.png')

d12=json.loads((PAY/'视频/脚本/12.json').read_text())
new,details=body_frame(d12,0,1,preview/'12-sip对齐修复-4K静态预览.png')
rowsets,dims,colors=details
zs,ef,zf,gapx,lhE,lhZ,rgap,cgap,lhN=dims
centers={}
for ci,rows in enumerate(rowsets):
    if ci!=1:continue
    for row in rows:
        assert not isinstance(row,tuple)
        tw=sum(col['w'] for col in row)+gapx*(len(row)-1);x=(R.W-tw)/2
        for col in row:
            xe,xz=R.col_place(col,ef,zf,x);cursor=xe
            for text,color in col['se']:
                if text=='sip':centers[text]=cursor+ef.getlength(text)/2
                cursor+=ef.getlength(text)
            for k,line in enumerate(col['zl']):
                zx=xz[k];ux=R._under_x(col,k,zf,x,xz[k-1] if k else None)
                if ux is not None:zx=ux
                for text,color in line:
                    if text in ('啜饮','（小口喝；抿）'):centers[text]=zx+zf.getlength(text)/2
                    zx+=zf.getlength(text)
            x+=col['w']+gapx
assert len(centers)==3 and max(centers.values())-min(centers.values())<.01,centers
body_frame(d12,13,1,preview/'12-百事CEO说明-4K静态预览.png')
alignment={'resolution':[3840,2160],'theme':'official make_video.py green theme','centers_x':centers,'maximum_center_error_px':max(centers.values())-min(centers.values()),'layout':new,'video_generated':False}
(REPORT/'新可乐对齐核对/4K实际主题对齐核对.json').write_text(json.dumps(alignment,ensure_ascii=False,indent=2)+'\n')

font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',28)
for start in [0,6]:
    subset=ids[start:start+6];canvas=Image.new('RGB',(2880,1170),(234,239,237));draw=ImageDraw.Draw(canvas)
    for k,no in enumerate(subset):
        im=Image.open(preview/f'{no}-正文尾页-静态预览.png');im.thumbnail((960,540));x=k%3*960;y=k//3*585
        draw.text((x+14,y+4),no+' AFTER - STATIC PREVIEW',font=font,fill=(20,42,35));canvas.paste(im,(x,y+40))
    canvas.save(preview/f'after-{start+1:02d}-{start+len(subset):02d}.jpg',quality=92,subsampling=0)

(REPORT/'核查记录/源稿修订后70篇复核.json').write_text(json.dumps({'articles':all70,'checked':70,'summaries_preserved':70,'body_words_preserved':70,'video_generation':False,'pdf_generation':False},ensure_ascii=False,indent=2)+'\n')
shutil_source=OUT/'verify_previews.py'
(REPORT/'核查程序/verify_previews.py').write_bytes(shutil_source.read_bytes())
print(json.dumps({'source_articles_rechecked':70,'legacy_sources_cleaned':12,'all_new_summaries_preserved':True,'sip_4K_center_error_px':alignment['maximum_center_error_px'],'MP4_generated':False,'PDF_generated':False},ensure_ascii=False),flush=True)
