"""Read the archived public MP4s, hash them, and capture body-tail/card stills. No videos are generated."""
import concurrent.futures
from fractions import Fraction
import hashlib,json,os,subprocess,tempfile
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont

ROOT=Path('/workspace/work/github-publication/target')
OUT=Path('/workspace/work/video-audit70-20261113')
CATALOG=json.loads((ROOT/'成果归档/视频定稿文件清单.json').read_text())['videos']
CONFIRMED=set(json.loads((OUT/'review01-24.json').read_text())['confirmed_remove_ids'])
for d in ['frames/body','frames/card','frames/body-full','contacts']:(OUT/d).mkdir(parents=True,exist_ok=True)

def run(args,**kw):return subprocess.run(list(map(str,args)),check=True,capture_output=True,**kw)
def one(row):
    no=row['id']
    with tempfile.TemporaryDirectory(prefix='accepted-video-',dir=OUT) as td:
        video=Path(td)/f'{no}.mp4'
        with video.open('wb') as f:
            subprocess.run(['git','cat-file','blob',row['git_blob_sha']],cwd=ROOT,env={**os.environ,'GIT_NO_LAZY_FETCH':'1'},stdout=f,stderr=subprocess.PIPE,check=True)
        digest=hashlib.sha256(video.read_bytes()).hexdigest()
        assert digest==row['sha256'],no
        info=json.loads(run(['ffprobe','-v','error','-show_streams','-show_format','-of','json',video]).stdout)
        vs=next(s for s in info['streams'] if s['codec_type']=='video')
        assert (vs['width'],vs['height'])==(3840,2160),no
        fps=Fraction(vs['r_frame_rate']);assert fps==30
        frames=int(vs['nb_frames']);card_start=(frames-60)/float(fps)
        records={}
        for kind,sec in [('body',card_start-.2),('card',card_start+1)]:
            dest=OUT/'frames'/kind/f'{no}.png'
            run(['ffmpeg','-v','error','-threads','1','-ss',f'{sec:.6f}','-i',video,'-frames:v','1','-vf','scale=1280:720:flags=lanczos','-threads','1',dest])
            records[kind]={'seconds':sec,'png':str(dest.relative_to(OUT)),'sha256':hashlib.sha256(dest.read_bytes()).hexdigest()}
        if no in CONFIRMED or no in {'01','10','25','70'}:
            dest=OUT/'frames/body-full'/f'{no}.png'
            run(['ffmpeg','-v','error','-threads','1','-ss',f'{card_start-.2:.6f}','-i',video,'-frames:v','1','-threads','1',dest])
        return {'id':no,'accepted_video_sha256':digest,'accepted_git_blob':row['git_blob_sha'],'width':3840,'height':2160,'frames':frames,'standalone_summary_start':card_start,'standalone_summary_seconds':2,'stills':records}

records=[]
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
    for completed in concurrent.futures.as_completed([pool.submit(one,row) for row in CATALOG]):
        r=completed.result();records.append(r)
        (OUT/'delivered-video-inspection.json').write_text(json.dumps({'videos':sorted(records,key=lambda x:x['id']),'checked':len(records),'video_generation':False},ensure_ascii=False,indent=2)+'\n')
        if len(records)%10==0:print('Inspected accepted MP4s',len(records),'/ 70',flush=True)

font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',28)
for kind in ['body','card']:
    for start in range(1,71,9):
        ids=[f'{n:02d}' for n in range(start,min(start+9,71))]
        canvas=Image.new('RGB',(2880,3*585),(234,239,237));draw=ImageDraw.Draw(canvas)
        for k,no in enumerate(ids):
            im=Image.open(OUT/'frames'/kind/f'{no}.png').convert('RGB');im.thumbnail((960,540))
            x=(k%3)*960;y=(k//3)*585
            draw.text((x+12,y+4),no+(' LEGACY RECAP' if no in CONFIRMED else ''),font=font,fill=(160,32,25) if no in CONFIRMED else (20,42,35))
            canvas.paste(im,(x,y+40))
        canvas.save(OUT/'contacts'/f'{kind}-{start:02d}-{min(start+8,70):02d}.jpg',quality=92,subsampling=0)
print('Finished inspecting all 70 accepted MP4s and making still-image contact sheets. No MP4 created or changed.',flush=True)
