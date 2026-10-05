"""用另一版片头重出视频：复用 work_NN 里已渲染的正文画面和音频，只换标题页。
用法（在 video/ 目录下）：python3 title_variant_video.py scripts/03.json logo/A_stamp/title_logo.py 03_A.mp4
"""
import json,os,sys,shutil,subprocess,importlib.util,imageio_ffmpeg
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
js,mod_path,out=sys.argv[1:4]
d=json.load(open(js)); no=d['no']
src=f'work_{no}'; key=os.path.basename(os.path.dirname(mod_path)); dst=f'work_{no}_{key}'
if os.path.exists(dst): shutil.rmtree(dst)
shutil.copytree(src,dst)
import render as R  # 与 make_video.py 相同的配色设置，保证标题页渲染环境一致
T=dict(BG_TOP=(14,36,30),BG_BOT=(20,48,40),FG_EN=(240,247,242),FG_ZH=(170,196,182),DIM=(110,140,125),
   PAL=[(251,191,36),(56,189,248),(244,114,182),(190,242,100),(196,181,253),(251,146,60),(94,234,212),(252,165,165)])
for a,b in T.items(): setattr(R,a,b)
spec=importlib.util.spec_from_file_location('tvar',mod_path); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
fx=d.get('title_fx',{})
m.frame_title2(no,d['title_en'],d['title_zh'],fx.get('hl',[]),fx.get('ghost',[]),f'{dst}/0000.png')
lst=open(f'{src}/list.txt').read().replace(os.path.abspath(src)+'/',os.path.abspath(dst)+'/')
open(f'{dst}/list.txt','w').write(lst)
AF=open('../tts/'+os.environ.get('AFFILE','AF.txt')).read().strip(); FF=imageio_ffmpeg.get_ffmpeg_exe()
subprocess.run([FF,'-y','-loglevel','error','-f','concat','-safe','0','-i',f'{dst}/list.txt','-i',f'{dst}/a.wav',
    '-af',AF,'-c:v','libx264','-tune','stillimage','-crf','16','-preset','slow','-pix_fmt','yuv420p','-r','30','-c:a','aac','-b:a','256k','-shortest','-movflags','+faststart',out],check=True)
print(out)
