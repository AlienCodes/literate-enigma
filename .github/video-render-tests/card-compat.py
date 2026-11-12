#!/usr/bin/env python3
"""Inspect legacy pixels, audit 70 real end cards, and run the relevant original layout regression."""
import ast
import base64
import copy
import functools
import hashlib
import importlib.util
import io
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

import numpy as np
from PIL import Image

ROOT=Path.cwd()
BASE='c9d52b26fe981ef8e4c412189ca289716ab8bf00'
SUMMARY_COMMIT='5756b8b10bd84ba54aa882febe65739652b21c89'
REVIEW=ROOT/'pilot-review'
OUT=ROOT/'card-compat-output'
TOKEN=r"[A-Za-z0-9]+(?:[.,:'’/-][A-Za-z0-9]+)*(?:[%％])?|."
import re

def run(args,**kw):
    return subprocess.run([str(x) for x in args],check=True,**kw)
def get(args):
    return run(args,capture_output=True,text=True).stdout
def materialize(paths):
    run(['git','sparse-checkout','add','--stdin'],input=''.join('/'+p+'\n' for p in paths),text=True)
def raw(path,commit=BASE):
    return run(['git','show',commit+':'+path],capture_output=True).stdout
def js(path,commit=BASE):
    return json.loads(raw(path,commit))
def emit_image(path,im,**metadata):
    output=io.BytesIO();im.convert('RGB').save(output,format='JPEG',quality=80,optimize=True)
    path.write_text(json.dumps({'mime_type':'image/jpeg','data':base64.b64encode(output.getvalue()).decode(),**metadata},ensure_ascii=False)+'\n')
def spec_module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def configured(path,name):
    os.environ['VIDEO_S']='2'
    m=spec_module(name,path);m.F=str(ROOT/'视频/工具/fonts')+'/'
    tree=ast.parse(raw('视频/工具/make_video.py').decode())
    node=next(n.value for n in tree.body if isinstance(n,ast.Assign)
              and any(isinstance(t,ast.Name) and t.id=='T' for t in n.targets)
              and isinstance(n.value,ast.Call) and isinstance(n.value.func,ast.Name)
              and n.value.func.id=='dict' and any(k.arg=='BG_TOP' for k in n.value.keywords))
    for k in node.keywords:setattr(m,k.arg,ast.literal_eval(k.value))
    # Cache immutable font objects and exact glyph advances without changing geometry.
    original=m.ZH
    @functools.lru_cache(maxsize=800)
    def font(size,weight=500):
        f=original(size,weight);f.getlength=functools.lru_cache(maxsize=2048)(f.getlength);return f
    m.ZH=font
    return m

def diagnose():
    materialize(['视频/工具/render.py','视频/工具/make_video.py','视频/工具/fonts'])
    production=spec_module('production',ROOT/'.github/video-batch/run.py')
    paths=production.tree_paths()
    for no in ('67','69'):
        folder=OUT/f'diagnose-{no}';folder.mkdir(parents=True,exist_ok=True)
        source=folder/'source.mp4'
        original=next(p for p in paths if p.startswith('最终版4K视频/'+no+' - ') and p.endswith('.mp4'))
        source.write_bytes(raw(original))
        data=js('视频/脚本/'+no+'.json')
        vs=next(s for s in production.probe(source)['streams'] if s['codec_type']=='video')
        end,checks=production.voice_end(source,float(vs['duration']))
        transition=math.ceil(end*30)
        for name,f in [('last',int(vs['nb_frames'])-1),('before-voice-end',transition-1)]:
            run(['ffmpeg','-v','error','-y','-ss',f'{f/30:.9f}','-i',source,'-frames:v','1','-update','1',folder/f'{name}.png'])
        production.OUT=folder
        try:
            classification=production.find_old_summary(no,source,data,int(vs['nb_frames']),transition)
            error=None
        except Exception as exc:
            classification=None;error=repr(exc)
        panels=[folder/'last.png',folder/'before-voice-end.png']
        references=sorted(folder.glob(no+'-old-body-active*.png'))
        if references:panels.append(references[-1])
        golden='视频/制作记录/69_末页截图.png'
        if no=='69':
            try:
                p=folder/'archived.png';p.write_bytes(raw(golden));Image.open(p).verify();panels.append(p)
            except Exception:pass
        collage=Image.new('RGB',(1920,1080),(14,36,30))
        for i,p in enumerate(panels[:4]):
            im=Image.open(p).convert('RGB').resize((960,540),Image.Resampling.LANCZOS);collage.paste(im,((i%2)*960,(i//2)*540))
        emit_image(REVIEW/f'{no}-source-diagnosis.json',collage,article=no,
                   panels=[p.name for p in panels],source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                   source_frames=int(vs['nb_frames']),voice_end_seconds=end,classification=classification,error=error)
        print('LEGACY_DIAGNOSIS',no,json.dumps({'classification':classification,'error':error},ensure_ascii=False),flush=True)

def summaries():
    paths=get(['git','-c','core.quotepath=off','ls-tree','-rz','--name-only',SUMMARY_COMMIT]).split('\0')
    out={}
    for p in paths:
        if p.startswith('.github/video-batch/summaries/') and p.endswith('.json'):
            part=js(p,SUMMARY_COMMIT);assert not (out.keys()&part.keys());out.update(part)
    assert set(out)=={f'{i:02d}' for i in range(1,71)}
    return out
def boundaries(lines):
    text=''.join(''.join(c for c,b in line) for line in lines)
    edges=[];offset=0
    for line in lines[:-1]:
        offset+=len(line);edges.append(offset)
    return [{'token':m.group(0),'offset':e} for m in re.finditer(TOKEN[:-2],text)
            for e in edges if m.start()<e<m.end()]
def layout(r,text):
    sz,lines,first=r.简述排(text);f=r.ZH(sz,400);b=r.ZH(sz,700);ind=f.getlength('• ')
    widths=[sum((b if bold else f).getlength(c) for c,bold in line)+(0 if i in first else ind)
            for i,line in enumerate(lines)]
    return sz,lines,first,widths
def cards():
    materialize(['视频/工具/render.py','视频/工具/make_video.py','视频/工具/fonts'])
    oldpath=OUT/'baseline-render.py';oldpath.write_bytes(raw('视频/工具/render.py'))
    old=configured(oldpath,'old_cards');new=configured(ROOT/'视频/工具/render.py','new_cards')
    combined=summaries();changed=[];old_broken=[];reports=[];thumbs=[]
    images=OUT/'cards';images.mkdir(exist_ok=True)
    for no,items in sorted(combined.items()):
        text='（简述：'+''.join('▸'+label+'：'+body for label,body in items)+'）'
        a=layout(old,text);b=layout(new,text)
        bad=boundaries(a[1]);good=boundaries(b[1]);assert not good,(no,good)
        assert len(b[2])==5 and len(b[1])*b[0]*1.5 <= (new.H-8*new.S)*.9+1
        assert max(b[3]) <= new.W*.92+1,(no,max(b[3]))
        differs=(a[0],a[1],a[2])!=(b[0],b[1],b[2])
        if bad:old_broken.append(no)
        if differs:changed.append(no)
        new.简述排=lambda *args,_b=b,**kw:_b[:3]
        new.frame_简述(text,1,images/f'{no}.png')
        del new.简述排
        # Restore module-level function after memoizing its exact layout once.
        exec(compile(ast.Module([n for n in ast.parse((ROOT/'视频/工具/render.py').read_text()).body
                                if isinstance(n,ast.FunctionDef) and n.name=='简述排'],[]),'layout','exec'),new.__dict__)
        im=Image.open(images/f'{no}.png').convert('RGB')
        thumbs.append(im.resize((256,144),Image.Resampling.LANCZOS))
        if differs:
            old.简述排=lambda *args,_a=a,**kw:_a[:3]
            old.frame_简述(text,1,images/f'{no}-old.png')
            del old.简述排
            exec(compile(ast.Module([n for n in ast.parse(oldpath.read_text()).body
                                    if isinstance(n,ast.FunctionDef) and n.name=='简述排'],[]),'layout','exec'),old.__dict__)
            collage=Image.new('RGB',(1920,540))
            collage.paste(Image.open(images/f'{no}-old.png').resize((960,540),Image.Resampling.LANCZOS),(0,0))
            collage.paste(im.resize((960,540),Image.Resampling.LANCZOS),(960,0))
            emit_image(REVIEW/f'wrap-{no}-before-after.json',collage,article=no,old_broken_tokens=bad)
        reports.append({'article':no,'changed':differs,'old_broken_tokens':bad,'new_broken_tokens':good,
                        'old_font_px':a[0],'new_font_px':b[0],'old_lines':len(a[1]),'new_lines':len(b[1]),
                        'new_max_width':max(b[3]),'new_lines_text':[''.join(c for c,_ in line) for line in b[1]]})
        print('CARD_AUDIT',no,'changed' if differs else 'unchanged',json.dumps(bad,ensure_ascii=False),flush=True)
    overview=Image.new('RGB',(1792,1440),(14,36,30))
    for i,im in enumerate(thumbs):overview.paste(im,((i%7)*256,(i//7)*144))
    emit_image(REVIEW/'70-overview-updated.json',overview,summary_commit=SUMMARY_COMMIT)
    source=Image.open(io.BytesIO(raw('简述重制预览/70篇总览.jpg',SUMMARY_COMMIT))).convert('RGB')
    source.thumbnail((1792,1470),Image.Resampling.LANCZOS)
    b=io.BytesIO();source.save(b,format='JPEG',quality=65,optimize=True)
    (REVIEW/'70-overview-original.json').write_text(json.dumps({'mime_type':'image/jpeg','data':base64.b64encode(b.getvalue()).decode(),'source_commit':SUMMARY_COMMIT})+'\n')
    for no in ('03','23','54','65'):
        p=REVIEW/f'{no}-before-after.b64'
        if p.exists():(REVIEW/f'{no}-before-after.json').write_text(json.dumps({'mime_type':'image/jpeg','data':p.read_text().strip()})+'\n')
    (REVIEW/'wrap-audit.json').write_text(json.dumps({'summary_commit':SUMMARY_COMMIT,'audited':70,
        'changed_articles':changed,'old_broken_token_articles':old_broken,'all_new_ascii_tokens_intact':True,
        'all_new_cards_within_bounds':True,'cards':reports},ensure_ascii=False,indent=2)+'\n')
    print('AFFECTED_ARTICLES',','.join(changed),flush=True)

def canonical():
    materialize(['视频/工具/*.py','视频/工具/fonts','视频/工具/新管/回归基准_27.json',
                 '视频/脚本/23.json','视频/脚本/24.json','视频/脚本/27.json'])
    oldpath=OUT/'baseline-render.py';oldpath.write_bytes(raw('视频/工具/render.py'))
    old=configured(oldpath,'old_regression');new=configured(ROOT/'视频/工具/render.py','new_regression')
    assert all(new.简述页起(str(i)) and new.简述页起(f'{i:02d}') for i in range(1,71))
    invalid=[0,71,-1,None,'','abc','3a','1.0',1.0,'²','１２']
    assert not any(new.简述页起(i) for i in invalid)
    d=js('视频/脚本/27.json');after=copy.deepcopy(d);extracted=new.拆出简述页(after)
    prefix,expected=new.拆简述(d['sentences'][-1]['chunks'][-1].get('note'))
    assert extracted==expected and after['sentences'][-1]['chunks'][-1].get('note')==prefix
    new.apply_script(after)
    assert after.get('说明放宽特批',{}).get('S16',{}).get('倍数')!='整屏'
    original=ast.parse(oldpath.read_text());updated=ast.parse((ROOT/'视频/工具/render.py').read_text())
    funcs=lambda tree:{n.name:ast.dump(n,include_attributes=False) for n in tree.body if isinstance(n,ast.FunctionDef)}
    fa,fb=funcs(original),funcs(updated)
    allowed={'简述页起','_折简','拆出简述页'}
    assert all(fa[k]==fb[k] for k in fa.keys()-allowed),'Other rendering logic changed.'
    sys.path.insert(0,str(ROOT/'视频/工具'))
    os.chdir(ROOT/'视频/工具')
    checker=spec_module('official_checker',ROOT/'视频/工具/定稿视频核对.py')
    only=set(range(1,len(d['sentences'])))
    checker.R=old;before_images=checker.render_screens(d,str(OUT/'regression-old'),only=only)
    checker.R=new;after_images=checker.render_screens(d,str(OUT/'regression-new'),only=only)
    assert [n for n,_ in before_images]==[n for n,_ in after_images]
    assert all(np.array_equal(a,b) for (_,a),(_,b) in zip(before_images,after_images))
    baseline=json.loads(raw('视频/工具/新管/回归基准_27.json'))['画面']
    baseline=dict(x.split(':',1) for x in baseline)
    current={n:hashlib.sha256(im.tobytes()).hexdigest()[:16] for n,im in before_images}
    baseline_mismatch=[n for n,v in current.items() if baseline.get(n)!=v]
    p=subprocess.run([sys.executable,str(ROOT/'视频/工具/排版自检.py')],capture_output=True,text=True,
                     env={**os.environ,'VIDEO_S':'1','IMAGEIO_FFMPEG_EXE':'/usr/bin/ffmpeg'})
    report={'rules_01_to_70':True,'invalid_ids_rejected':True,'last_summary_extracted_27':True,
            'obsolete_last_fullscreen_exception_cleared':True,'non_summary_render_functions_identical':True,
            'official_27_nonfinal_screens_compared':len(before_images),'official_27_nonfinal_pixels_identical':True,
            'existing_27_stored_baseline_mismatches':baseline_mismatch,'existing_layout_selftest_returncode':p.returncode,
            'existing_layout_selftest_output':p.stdout+p.stderr,'audio_pipeline_modified':False,
            'full_audio_quicktest_rerun':False,'expected_change':'Only the last summary becomes a separate page; ASCII words/numbers no longer split.'}
    (REVIEW/'canonical-regression.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(report,ensure_ascii=False),flush=True)
    assert p.returncode==0,'Original layout selftest failed; see retained report.'

if __name__=='__main__':
    REVIEW.mkdir(exist_ok=True);OUT.mkdir(exist_ok=True)
    {'diagnose':diagnose,'cards':cards,'canonical':canonical}[sys.argv[1]]()
