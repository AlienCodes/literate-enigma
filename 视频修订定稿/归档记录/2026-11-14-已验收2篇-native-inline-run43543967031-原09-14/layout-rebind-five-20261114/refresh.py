#!/workspace/work/video-venv/bin/python
"""Re-render five authorized sound-control source deltas; bind CI only after exact visual equality."""
import ast, copy, functools, hashlib, importlib.util, json, os, sys, datetime
from pathlib import Path
import PIL
from PIL import Image

BASE=Path('/workspace/work/video-audit70-20261113')
OLD=BASE/'final-layout'; OUT=Path(__file__).resolve().parent
CI=Path('/workspace/work/video-revision-batch-ci/.github/video-revision-batch/approved-video-layouts70.json')
EXPECTED={'05':'47fa4c8746deecb0583e08633d1b52751ed3e6046ee5c1e46d032c443d220fba','15':'0934aa067f19814028c398b0c70a400bb09e354f744bde4000742950d77f441e','17':'2e9971ea5ce7857e119226fe95def06e6eb9c3ef9823d8e8c4f3456f46a3bbb0','18':'8cffbad6f0b8451e46ad1a65d5f629c450ceff2c771218445770c8cbfd77ebca','30':'cdf727cb4c6832063421df9da6ab8ae7729cf9df01d6be089a8981c92c360f06'}
sha=lambda b:hashlib.sha256(b).hexdigest()
def load_module(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def rgb(path):
    with Image.open(path)as im:
        assert im.size==(3840,2160);return sha(im.convert('RGB').tobytes())
def changes(a,b,path=''):
    if isinstance(a,dict)and isinstance(b,dict):
        return [p for k in sorted(set(a)|set(b))for p in ([path+'/'+k]if k not in a or k not in b else changes(a[k],b[k],path+'/'+k))]
    if isinstance(a,list)and isinstance(b,list):
        return [path]if len(a)!=len(b)else[p for i,(x,y)in enumerate(zip(a,b))for p in changes(x,y,path+'/'+str(i))]
    return []if a==b else[path]
def main():
    assert PIL.__version__=='12.3.0'and sys.executable=='/workspace/work/video-venv/bin/python'
    os.environ['VIDEO_S']='2'
    oldreport=json.loads((OLD/'report.json').read_text());raw=CI.read_bytes();approved=json.loads(raw)
    (OUT/'approved-video-layouts70.before.json').write_bytes(raw)
    assert approved['passed']and approved['count']==70
    renderer=OLD/'official/render.py';maker=OLD/'official/make_video.py'
    assert sha(renderer.read_bytes())==approved['renderer_sha256']==oldreport['renderer_sha256']
    assert sha(maker.read_bytes())==oldreport['maker_sha256']
    R=load_module('unchanged_official_renderer',renderer);R.F=str(OLD/'fonts')+'/'
    assert(R.S,R.W,R.H)==(2,3840,2160)
    for name,fingerprint in oldreport['official_font_sha256'].items():assert sha((OLD/'fonts'/name).read_bytes())==fingerprint
    tree=ast.parse(maker.read_bytes());node=next(n.value for n in tree.body if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='T'for t in n.targets)and isinstance(n.value,ast.Call)and any(k.arg=='BG_TOP'for k in n.value.keywords))
    for k in node.keywords:setattr(R,k.arg,ast.literal_eval(k.value))
    for name,default in [('EN',600),('ZH',500)]:
        original=getattr(R,name)
        def wrap(original,default):
            @functools.lru_cache(maxsize=256)
            def cached(size,weight=None):
                f=original(size,default if weight is None else weight);f.getlength=functools.lru_cache(maxsize=1024)(f.getlength);return f
            return cached
        setattr(R,name,wrap(original,default))
    T=load_module('unchanged_tail_digest',BASE/'illustrated-tail/illustrated_tail.py')
    rows={r['source_id']:r for r in approved['articles']};report={'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'evidence_kind':'actual_official_static_4K_rerender_only_not_new_video','Pillow':PIL.__version__,'renderer_sha256':sha(renderer.read_bytes()),'maker_sha256':sha(maker.read_bytes()),'font_sha256':oldreport['official_font_sha256'],'unchanged_helper_sha256':sha((BASE/'illustrated-tail/illustrated_tail.py').read_bytes()),'helper_ignore_keys_unchanged':list(T.REVIEW_ONLY_TOP_LEVEL_KEYS),'CI_manifest_path':str(CI),'before_manifest_sha256':sha(raw),'frozen_or_local_baseline_manifests_modified':False,'source_or_audio_or_video_modified':False,'articles':[],'passed':False}
    for no,want in EXPECTED.items():
        oldraw=(OLD/'inputs'/f'{no}.json').read_bytes();newpath=BASE/'payload/视频/脚本'/f'{no}.json';newraw=newpath.read_bytes();assert sha(newraw)==want;old=json.loads(oldraw);new=json.loads(newraw);a=rows[no]
        assert sha(oldraw)==a['source_json_sha256']and T.source_layout_digest(old)==a['source_layout_structural_sha256']
        (OUT/f'{no}-approved-before-source.json').write_bytes(oldraw);(OUT/f'{no}-current-approved-sound-source.json').write_bytes(newraw)
        assert old['sentences']==new['sentences'],'Any visible sentence/translation/alignment/note/summary changed: '+no
        for key in ['title_en','title_zh','title_fx','字号上限']:assert old.get(key)==new.get(key),(no,key)
        records=[]
        for label,data in [('before',copy.deepcopy(old)),('after',copy.deepcopy(new))]:
            summary=R.拆出简述页(data);assert sha(summary.encode())==a['approved_summary_text_sha256'];R.apply_script(data);colors=R.分色(data);R.unify_colors(colors,data['sentences']);metrics=[]
            for i,sentence in enumerate(data['sentences']):
                chunks=[[tuple(pair)for pair in c['align']]for c in sentence['chunks']];notes=[c.get('note')for c in sentence['chunks']];cs=R.sent_colors(colors,sentence);natural=R.max_es(chunks,cs,notes);cap=data.get('字号上限',{}).get(f'S{i+1}');configured=min(natural,100*R.S,float(cap)*R.S if cap is not None else 100*R.S);configured=int(configured)if configured==int(configured)else configured;_,height,width,_=R._measure(chunks,cs,notes,configured,R._grouping(chunks,cs));assert width<=R.MAXW2 and height<=R.MAXH2;assert not R.orphan_lines(chunks,cs,notes,configured);metrics.append({'sentence':i+1,'font_4k_px':configured,'width':width,'height':height})
            s=data['sentences'][-1];chunks=[[tuple(pair)for pair in c['align']]for c in s['chunks']];notes=[c.get('note')for c in s['chunks']];R.ES_FIXED=metrics[-1]['font_4k_px'];body=OUT/f'{no}-{label}-body-tail.png';R.frame_interlinear(chunks,R.sent_colors(colors,s),'',1,str(body),active=len(chunks)-1,notes=notes)
            size,lines,first=R.简述排(summary);assert size==a['summary_font_4k_px']and len(first)==5;card=OUT/f'{no}-{label}-summary.png';R.frame_简述(summary,1,str(card));assert rgb(card)==a['summary_rgb_sha256'];records.append({'label':label,'summary_text_sha256':sha(summary.encode()),'summary_font_4k_px':size,'summary_text_rows':[''.join(ch for ch,_ in line)for line in lines],'summary_rgb_sha256':rgb(card),'summary_png_sha256':sha(card.read_bytes()),'summary_png':str(card),'body_tail_rgb_sha256':rgb(body),'body_tail_png':str(body),'sentence_font_and_geometry':metrics})
        assert records[0]['sentence_font_and_geometry']==records[1]['sentence_font_and_geometry'];assert records[0]['summary_text_rows']==records[1]['summary_text_rows'];assert records[0]['body_tail_rgb_sha256']==records[1]['body_tail_rgb_sha256']==rgb(OLD/'body-tail'/f'{no}.png')
        report['articles'].append({'source_id':no,'latest_source_path':str(newpath),'before_source_json_sha256':sha(oldraw),'after_source_json_sha256':sha(newraw),'before_source_layout_structural_sha256':a['source_layout_structural_sha256'],'after_source_layout_structural_sha256':T.source_layout_digest(new),'source_changed_paths':changes(old,new),'all_body_text_translation_alignment_notes_and_summary_exact':True,'all_sentence_fonts_and_geometry_exact':True,'body_tail_pixels_exact_original_approved_static':True,'summary_RGB_text_rows_font_exact_original_approved':True,'actual_renders':records})
    for item in report['articles']:
        no=item['source_id'];assert sha((BASE/'payload/视频/脚本'/f'{no}.json').read_bytes())==EXPECTED[no];rows[no]['source_json_sha256']=item['after_source_json_sha256'];rows[no]['source_layout_structural_sha256']=item['after_source_layout_structural_sha256']
    changed=changes(json.loads(raw),approved);assert len(changed)==10 and all(p.endswith('/source_json_sha256')or p.endswith('/source_layout_structural_sha256')for p in changed),changed
    assert CI.read_bytes()==raw,'CI manifest concurrently changed'
    after=(json.dumps(approved,ensure_ascii=False,indent=2)+'\n').encode();(OUT/'approved-video-layouts70.after.json').write_bytes(after);temp=CI.with_suffix('.json.refresh-five.tmp');temp.write_bytes(after);temp.replace(CI)
    report.update(passed=True,only_manifest_field_changes=changed,after_manifest_sha256=sha(after),PNG_RGB_font_and_approval_fields_unchanged=True,modified_manifest_only_working_CI=True)
    (OUT/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'passed':True,'manifest':str(CI),'manifest_sha256':sha(after),'report':str(OUT/'report.json'),'report_sha256':sha((OUT/'report.json').read_bytes()),'source_ids':list(EXPECTED)},ensure_ascii=False))
if __name__=='__main__':main()
