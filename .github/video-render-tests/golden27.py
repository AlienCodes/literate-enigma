#!/usr/bin/env python3
"""Public original27 golden fixture: approve only the last-screen change, keep every old sound gate."""
import ast,copy,functools,hashlib,importlib.util,json,os,subprocess,sys
from pathlib import Path
ROOT=Path.cwd();SOURCE='9408415b502f57f58ac7a795e38de4ae56cafd5e';ORIGINAL='c9d52b26fe981ef8e4c412189ca289716ab8bf00'
OUT=ROOT/'golden27-probe';OUT.mkdir(exist_ok=True)
def raw(commit,path):return subprocess.check_output(['git','show',commit+':'+path])
def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def hashes(images):return [name+':'+hashlib.sha256(im.tobytes()).hexdigest()[:16] for name,im in images]
def sem(d):return hashlib.sha256(json.dumps(d['sentences'],ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
work=OUT/'source';work.mkdir(exist_ok=True)
for name in ('render.py','make_video.py','title_anim.py','title2.py','定稿视频核对.py'):
 (work/name).write_bytes(raw(SOURCE,'视频/工具/'+name))
(work/'fonts').symlink_to(ROOT/'视频/工具/fonts',target_is_directory=True)
input_bytes=raw(ORIGINAL,'视频/脚本/27.json')
assert input_bytes==raw(SOURCE,'视频/脚本/27.json')
assert hashlib.sha1(b'blob '+str(len(input_bytes)).encode()+b'\0'+input_bytes).hexdigest()=='c19daf92fac1cc09fdf18060622e441222dd2f45'
d=json.loads(input_bytes);original_baseline=json.loads(raw(SOURCE,'视频/工具/新管/回归基准_27.json'))
assert original_baseline['a.wav']=='79f315bb8b448052379b5929d9e19963'
assert original_baseline['分段.json']=='f4275f9b9e571dd414e78a86dc6f1f1a'
(work/'original-render.py').write_bytes(raw(ORIGINAL,'视频/工具/render.py'))
os.environ['VIDEO_S']='2';os.chdir(work);sys.path.insert(0,str(work))
checker=load('official_golden_checker',work/'定稿视频核对.py')
current=checker.R;old=load('original_golden_renderer',work/'original-render.py')
old.F=str(work/'fonts')+'/'
src=(work/'make_video.py').read_text();exec(src[src.index('T=dict(BG_TOP'):src.index('P_CHUNK=')],{'R':old})
for r in (old,current):
 original_font=r.ZH
 @functools.lru_cache(maxsize=800)
 def cached_font(size,weight=500,_font=original_font):
  f=_font(size,weight);f.getlength=functools.lru_cache(maxsize=2048)(f.getlength);return f
 r.ZH=cached_font
checker.R=old
old_images=checker.render_screens(d,str(OUT/'old'))
assert hashes(old_images)==original_baseline['画面'],'Public original27 no longer reproduces the stored golden images.'
checker.R=current
new_images=checker.render_screens(d,str(OUT/'new'))
old_h,new_h=hashes(old_images),hashes(new_images)
assert len(old_h)==66 and len(new_h)==67
assert new_h[:64]==old_h[:64]
assert [x.split(':',1)[0] for x in old_h[64:]]==['S16-1','S16-2']
assert [x.split(':',1)[0] for x in new_h[64:]]==['S16-1','S16-2','简述']
assert [i for i,(a,b) in enumerate(zip(old_h,new_h)) if a!=b]==[64,65]
# Independent causal control: the OLD renderer, with only the old summary
# removed and its now-obsolete last-sentence width exception removed.
manual=copy.deepcopy(d);c=manual['sentences'][-1]['chunks'][-1]
c['note']=c['note'].split('（简述：',1)[0].rstrip('\n')
manual.get('说明放宽特批',{}).pop('S16',None)
checker.R=old
manual_images=checker.render_screens(manual,str(OUT/'manual-note-removal'),only={16})
assert hashes(manual_images)==new_h[64:66],'Last-body differences are not solely caused by removing the old note.'
updated=copy.deepcopy(original_baseline)
updated['画面']=original_baseline['画面'][:64]+new_h[64:]
assert updated['a.wav']==original_baseline['a.wav'] and updated['分段.json']==original_baseline['分段.json']
checker.R=current
expected=dict(x.split(':',1) for x in new_h)
negative={}
for kind,sentence,oldtext,newtext in [('first-body',1,'灾难','灾祸'),('last-body',16,'迟缓','缓慢')]:
 bad=copy.deepcopy(d);s=bad['sentences'][sentence-1];count=0
 for c in s['chunks']:
  if oldtext in c['zh']:
   c['zh']=c['zh'].replace(oldtext,newtext,1)
   for pair in c['align']:
    if oldtext in pair[1]:pair[1]=pair[1].replace(oldtext,newtext,1);break
   count+=1;break
 assert count==1
 rendered=checker.render_screens(bad,str(OUT/kind),only={sentence})
 changed=[name for name,im in rendered if hashlib.sha256(im.tobytes()).hexdigest()[:16]!=expected[name]]
 assert changed,(kind,'Real changed Chinese text escaped the golden image check.')
 negative[kind]={'caught':True,'changed_screens':changed}
bad=copy.deepcopy(d);last=bad['sentences'][-1]['chunks'][-1]
assert '切尔诺贝利' in last['note'];last['note']=last['note'].replace('切尔诺贝利','切尔诺贝里',1)
rendered=checker.render_screens(bad,str(OUT/'last-summary'),only={16})
changed=[name for name,im in rendered if hashlib.sha256(im.tobytes()).hexdigest()[:16]!=expected[name]]
assert changed==['简述'],changed
negative['last-summary']={'caught':True,'changed_screens':changed}
assert old_h!=updated['画面']
negative['old-inline-behaviour-restored']={'caught':True,'old_screen_count':66,'required_screen_count':67}
proof={'source_commit':SOURCE,'original_commit':ORIGINAL,'source_path':'视频/脚本/27.json',
 'source_blob':'c19daf92fac1cc09fdf18060622e441222dd2f45','raw_sha256':hashlib.sha256(input_bytes).hexdigest(),
 'sentences_sha256':sem(d),'last_note_sha256':hashlib.sha256(d['sentences'][-1]['chunks'][-1]['note'].encode()).hexdigest(),
 'all_66_original_images_reproduce_old_golden':True,'first_64_golden_images_unchanged':True,
 'changed_original_indices':[64,65],'changed_names':['S16-1','S16-2'],'added_name':'简述',
 'old_renderer_manual_note_removal_matches_new_last_body_pixels':True,
 'last_sentence_english_chinese_alignment_and_ordinary_notes_unchanged':True,
 'audio_baseline_changed':False,'segments_baseline_changed':False,'all_negative_controls':negative,
 'new_tail':new_h[64:],'raw_cache_data_read_or_exported':False}
candidate={'candidates':[{'name':'public-original27-c9-and-940','sources':[ORIGINAL,SOURCE],
 'source_path':proof['source_path'],'source_blob':proof['source_blob'],'raw_sha256':proof['raw_sha256'],
 'sentences_sha256':sem(d),'last_note_sha256':proof['last_note_sha256'],'baseline':updated}],
 'proof':proof}
dest=ROOT/'pilot-review';dest.mkdir(exist_ok=True)
(dest/'reference27.json').write_text(json.dumps(candidate,ensure_ascii=False,indent=2)+'\n')
(dest/'golden27-proof.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n')
(dest/'golden27-updated-baseline.json').write_text(json.dumps(updated,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(proof,ensure_ascii=False),flush=True)
