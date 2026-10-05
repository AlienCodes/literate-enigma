import json,re,os,sys,subprocess,numpy as np,soundfile as sf,imageio_ffmpeg
sys.path.insert(0,'../tts')
from kokoro_onnx import Kokoro
from clean import clean_tail,SR
import render as R
import title2 as T2
TTS='../tts'
k=Kokoro(f'{TTS}/kokoro-v1.0.onnx',f'{TTS}/voices-v1.0.bin'); V=np.load(f'{TTS}/'+os.environ.get('VOICE','voice_mb.npy'))
AF=open(f'{TTS}/'+os.environ.get('AFFILE','AF.txt')).read().strip(); FF=imageio_ffmpeg.get_ffmpeg_exe(); SPEED=0.95
T=dict(BG_TOP=(14,36,30),BG_BOT=(20,48,40),FG_EN=(240,247,242),FG_ZH=(170,196,182),DIM=(110,140,125),
   PAL=[(251,191,36),(56,189,248),(244,114,182),(190,242,100),(196,181,253),(251,146,60),(94,234,212),(252,165,165)])
for a,b in T.items(): setattr(R,a,b)

P_CHUNK=0.6; P_COMMA=0.6; P_HOLD=0.7; P_LEAD=0.3; P_PARA_EXTRA=0.5; P_TITLE=1.2
def say(t):
    w,_=k.create(re.sub(r'\*\*','',t),voice=V,speed=SPEED,lang='en-us'); return clean_tail(w)
def sil(s): return np.zeros(int(round(s*SR)),np.float32)
def build(js,out):
    d=json.load(open(js)); no=d['no']
    work=f'work_{no}'; os.makedirs(work,exist_ok=True)
    # colors
    colors={}; i=0
    for s in d['sentences']:
        for c in s['chunks']:
            for w in re.findall(r'\*\*([^*]+)\*\*',c['en']):
                if w.lower() not in colors: colors[w.lower()]=R.PAL[i%len(R.PAL)]; i+=1
    R.unify_colors(colors,d['sentences'])
    header=f"{no} · {d['title_en']}　{d['title_zh']}"
    segs=[]  # (image_key, duration) ; audio list
    audio=[sil(0.4)]; tl=[]  # (screen_id,active,dur)
    # title
    ta=say(d['title_en'])
    tl.append((('title',None),0.4+len(ta)/SR+P_TITLE)); audio+=[ta,sil(P_TITLE)]
    prev_para=None
    for si,s in enumerate(d['sentences']):
        ch=s['chunks']; lead=P_LEAD+(P_PARA_EXTRA if prev_para is not None and s['para']!=prev_para else 0)
        prev_para=s['para']
        # read the whole sentence naturally: pause only at punctuation (, ; :), not at line breaks
        texts=[re.sub(r'\*\*','',c['en']).strip() for c in ch]
        sent=' '.join(texts)
        bounds=[];pos=0
        for t in texts: bounds.append(pos); pos+=len(t)+1
        pieces=[];p0=0
        for mm in re.finditer(r'[,;:](?=\s)',sent):
            pieces.append((p0,mm.end())); p0=mm.end()+1
        pieces.append((p0,len(sent)))
        clips=[];tmap=[];t=0.0
        for k2,(x0,x1) in enumerate(pieces):
            w=say(sent[x0:x1]); dur=len(w)/SR
            tmap.append((x0,x1,t,t+dur)); clips.append(w); t+=dur
            if k2<len(pieces)-1: clips.append(sil(P_COMMA)); t+=P_COMMA
        def c2t(cpos):
            for x0,x1,t0,t1 in tmap:
                if cpos<=x1: return t0+(t1-t0)*max(0,cpos-x0)/max(1,x1-x0)
            return t
        a=np.concatenate(clips)
        starts=[0.0]+[c2t(bounds[i]) for i in range(1,len(ch))]+[len(a)/SR]
        audio+=[sil(lead),a,sil(P_HOLD)]
        for ci in range(len(ch)):
            dur=starts[ci+1]-starts[ci]+(lead if ci==0 else 0)+(P_HOLD if ci==len(ch)-1 else 0)
            tl.append(((si,ci),dur))
    audio.append(sil(0.8)); tl[-1]=(tl[-1][0],tl[-1][1]+0.8)
    A=np.concatenate(audio); A=A/np.abs(A).max()*0.89
    total=sum(x for _,x in tl)
    # render images: one uniform size = largest that fits every screen with locked layout
    sizes=[R.max_es([[tuple(p) for p in c['align']] for c in s['chunks']],colors,[c.get('note') for c in s['chunks']]) for s in d['sentences']]
    print('sizes',sizes)
    files=[]; t=0
    for (key,dur) in tl:
        prog=min(1,(t+dur)/total)
        fn=f"{work}/{len(files):04d}.png"
        if key[0]=='title':
            T2.frame_title2(no,d['title_en'],d['title_zh'],d.get('title_fx',{}).get('hl',[]),d.get('title_fx',{}).get('ghost',[]),fn)
        else:
            si,ci=key; R.ES_FIXED=min(sizes[si],100*R.S); R.frame_interlinear([[tuple(p) for p in c['align']] for c in d['sentences'][si]['chunks']],colors,header,prog,fn,active=ci,notes=[c.get('note') for c in d['sentences'][si]['chunks']])
        files.append((fn,dur)); t+=dur
    with open(f'{work}/list.txt','w') as f:
        for fn,dur in files: f.write(f"file '{os.path.abspath(fn)}'\nduration {dur:.3f}\n")
        f.write(f"file '{os.path.abspath(files[-1][0])}'\n")
    sf.write(f'{work}/a.wav',A,SR)
    subprocess.run([FF,'-y','-loglevel','error','-f','concat','-safe','0','-i',f'{work}/list.txt','-i',f'{work}/a.wav',
        '-af',AF,'-c:v','libx264','-tune','stillimage','-crf','16','-preset','slow','-pix_fmt','yuv420p','-r','30','-c:a','aac','-b:a','256k','-shortest','-movflags','+faststart',out],check=True)
    print(out,round(total,1),'s',len(files),'screens')
if __name__=='__main__': build(sys.argv[1],sys.argv[2])
