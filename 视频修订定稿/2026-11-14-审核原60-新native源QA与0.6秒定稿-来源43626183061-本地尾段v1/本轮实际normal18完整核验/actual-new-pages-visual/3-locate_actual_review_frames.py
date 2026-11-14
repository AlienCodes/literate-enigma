from pathlib import Path
import subprocess,json,hashlib
import numpy as np
from PIL import Image,ImageDraw,ImageFont
root=Path(__file__).parent;prepared=json.loads((root/'prepared-inline-section.json').read_text());video=Path(prepared['final']['path']);body=prepared['decoded_frames_to_actually_view'][1]['frame']
H=Path('/dev/shm/article60-text-review-draft-20261114')
initial=json.loads(Path('/workspace/work/video-audit70-20261113/article60-user-review-draft-20261114/static-render-report.json').read_text());incremental=json.loads((H/'static-070075/incremental-static-report.json').read_text());last=json.loads((H/'static-076/incremental-static076-report.json').read_text())
a=next(s for r in initial['resolutions']if r['scale']==2 for s in r['sources']if s['label']=='after')
b=next(s for r in incremental['resolutions']if r['scale']==2 for s in r['sources']if s['label']=='after062075')
c=next(s for r in last['resolutions']if r['scale']==2 for s in r['sources']if s['label']=='after062076')
by={(r['sentence'],r['active_chunk']):r for r in a['actual_changed_page_renders']}
for r in b['changed_page_renders']:by[(r['sentence'],r['active_chunk'])]=r
for r in c['changed_page_renders']:by[(r['sentence'],r['active_chunk'])]={**r,'term':'looked-past-after-all-user-comment076'}
by[(15,2)]={**c['actual_body_tail'],'sentence':15,'active_chunk':2,'term':'final-user-comment076-centered'}
rows=[{**v,'term':v.get('term',f'S{k[0]}-C{k[1]}')} for k,v in sorted(by.items())]
out=root/'actual-focus-frames';out.mkdir(exist_ok=True)
refs=[np.asarray(Image.open(r['path']).convert('RGB').resize((384,216)),dtype=np.float32)[:-2]for r in rows];best=[(float('inf'),None)for r in rows]
cmd=['ffmpeg','-v','error','-i',str(video),'-vf',f"select='lt(n,{body})*not(mod(n,15))',scale=384:216",'-fps_mode','passthrough','-pix_fmt','rgb24','-f','rawvideo','-']
p=subprocess.Popen(cmd,stdout=subprocess.PIPE);i=0;size=384*216*3
while True:
 data=p.stdout.read(size)
 if not data:break
 assert len(data)==size
 a=np.frombuffer(data,dtype=np.uint8).reshape(216,384,3).astype(np.float32)[:-2]
 for j,ref in enumerate(refs):
  score=float(np.abs(a-ref).mean())
  if score<best[j][0]:best[j]=(score,i*15)
 i+=1
assert p.wait()==0
frames=sorted({x[1]for x in best});select='+'.join(f'eq(n,{n})'for n in frames)
subprocess.run(['ffmpeg','-v','error','-i',str(video),'-vf',f"select='{select}'",'-fps_mode','passthrough',str(out/'actual-native-%03d.png')],check=True)
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();mapped={n:out/f'actual-native-{j+1:03d}.png'for j,n in enumerate(frames)}
result=[]
for row,(score,frame)in zip(rows,best):
 f=mapped[frame];result.append({'sentence':row['sentence'],'active_chunk_reference':row['active_chunk'],'term':row['term'],'frame':frame,'path':str(f),'bytes':f.stat().st_size,'sha256':sha(f),'video_sha256':sha(video),'frame_decoded_from_actual_native_MP4':True,'locator_thumbnail_difference_not_a_pass_fail_test':score})
report={'kind':'actual-native-frame-location-for-independent-visual-review','source_id':'60','quality_book_order':'36','requested_video_order':'36','native_run':43626183061,'actual_native_MP4':prepared['final'],'native_body_frames':body,'human_review_or_media_quality_pass_not_claimed_by_locator':True,'frames':result};(out/'actual-new-focus-frames-index.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
w=640;h=360;pad=35;cols=3;rr=(len(result)+cols-1)//cols;contact=Image.new('RGB',(cols*w,rr*(h+pad)),(15,30,25));draw=ImageDraw.Draw(contact);font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',18)
for j,row in enumerate(result):
 x=j%cols*w;y=j//cols*(h+pad);im=Image.open(row['path']).convert('RGB').resize((w,h));contact.paste(im,(x,y));draw.text((x+5,y+h+5),f"S{row['sentence']:02d} {row['term']} / frame {row['frame']}",font=font,fill='white')
contact.save(out/'actual-review-target-pages-contact.jpg',quality=95)
print(json.dumps({'index':str(out/'actual-new-focus-frames-index.json'),'targets':len(result),'contact':str(out/'actual-review-target-pages-contact.jpg')},ensure_ascii=False))
