import json,re,os,sys,subprocess,numpy as np,soundfile as sf,imageio_ffmpeg
sys.path.insert(0,'../tts')
from kokoro_onnx import Kokoro
from clean import clean_tail,SR
import render as R
import title2 as T2
TTS='../tts'
k=Kokoro(f'{TTS}/kokoro-v1.0.onnx',f'{TTS}/voices-v1.0.bin'); V=np.load(f'{TTS}/'+os.environ.get('VOICE','voice_mb.npy'))
KT=Kokoro(f'{TTS}/kokoro-v1.0-timed.onnx',f'{TTS}/voices-v1.0.bin')  # 只用来取每个音的准确时间（定位标点），声音仍用上面的原模型
AF=open(f'{TTS}/'+os.environ.get('AFFILE','AF.txt')).read().strip(); FF=imageio_ffmpeg.get_ffmpeg_exe(); SPEED=0.95
T=dict(BG_TOP=(14,36,30),BG_BOT=(20,48,40),FG_EN=(240,247,242),FG_ZH=(170,196,182),DIM=(110,140,125),
   PAL=[(251,191,36),(56,189,248),(244,114,182),(190,242,100),(196,181,253),(251,146,60),(94,234,212),(252,165,165)])
for a,b in T.items(): setattr(R,a,b)

P_CHUNK=0.6; P_COMMA=0.4; P_HOLD=0.7; P_LEAD=0.3; P_PARA_EXTRA=0.2; P_TITLE=0.6; P_FIRST=0.4;  # 标题读完停 0.6 秒 → 切到正文第一屏 → 再停 0.4 秒开读（共 1 秒）
P_LIST=0.2  # 牛津逗号列举（A, B, and C）里的逗号：0.2 秒
def say(t):
    w,_=k.create(re.sub(r'\*\*','',R.strip_gloss(t)),voice=V,speed=SPEED,lang='en-us'); return clean_tail(w)
def sil(s): return np.zeros(int(round(s*SR)),np.float32)

def _quiet_runs(w,thr_db=-38,min_len=0.05):
    n=int(0.01*SR); peak=np.abs(w).max()+1e-9; runs=[]; st=None
    for i in range(0,len(w)-n,n):
        q=20*np.log10(np.sqrt(np.mean(w[i:i+n]**2))/peak+1e-9)<thr_db
        if q and st is None: st=i
        if not q and st is not None:
            if (i-st)/SR>=min_len: runs.append((st,i))
            st=None
    return runs
SIL_DB=-55   # 真正无声：比本句最响处低 55 dB 以上（模型停顿里的底噪约 -55～-75 dB；词尾 /s/ /f/ /z/ 只有 -25～-45 dB，绝不能删）
AUD_DB=-45   # 能听见的声音：比最响处低不到 45 dB（用来量"实际听到的停顿"长度）
def _env5(w):
    n=int(0.005*SR); pk=np.abs(w).max()+1e-9; m=len(w)//n
    return 20*np.log10(np.sqrt(np.mean(w[:m*n].reshape(m,n)**2,axis=1))/pk+1e-9)
INNER_MAX=0.22; INNER_TO=0.18   # 没有标点的地方：模型自己停顿超过 0.22 s 的，压缩到 0.18 s（硬性条件：无标点处整句连读）
def _cap_inner(seg):
    """只压缩句中（非标点处）过长的无声段；只删听不见的部分（低于 -45 dB），两头各保留一半，不碰任何读音。"""
    e=_env5(seg); F=int(0.005*SR); keep=[];prev=0;st=None
    for f in range(len(e)+1):
        q=f<len(e) and e[f]<AUD_DB
        if q and st is None: st=f
        if not q and st is not None:
            if (f-st)*0.005>INNER_MAX and st>4 and f<len(e)-4:
                h=int(INNER_TO/2/0.005)
                keep.append(seg[prev:(st+h)*F]); prev=(f-h)*F
            st=None
    keep.append(seg[prev:])
    return np.concatenate(keep)
def sentence_audio(sent,pieces,gaps):
    """整句一次合成（原模型，声音不变）。标点位置用带时长输出的同版模型精确定位（A9）；
    在标点处只删除"真正无声"的部分（A10：绝不删词尾的 s/f/z 等弱音），再补静音，使实际听到的停顿 = 标准时长。"""
    raw,_=k.create(sent,voice=V,speed=SPEED,lang='en-us'); w=clean_tail(raw)
    tb,_,sp=KT.create_timed(sent,voice=V,speed=SPEED,lang='en-us',clause_pause=0,sentence_pause=0)
    scale=len(raw)/len(tb); toks=list(sp)
    idxs=[i for i,x in enumerate(toks) if x.phoneme in ',;:']
    if len(idxs)!=len(pieces)-1: raise SystemExit(f'【停止】标点数对不上（A9）：{sent[:60]}')
    e=_env5(w); F=int(0.005*SR); cuts=[]; M=2   # M：停顿两头各保留 2 帧（10 ms）
    for gi,i in enumerate(idxs):
        prv=next(x for x in reversed(toks[:i]) if x.phoneme.strip() and x.phoneme not in ',;:.!?')
        nxt=next(x for x in toks[i+1:] if x.phoneme.strip() and x.phoneme not in ',;:.!?')
        pe=int(prv.end*scale*SR)//F; ns=int(nxt.start*scale*SR)//F
        # 带时长模型与原模型的局部时间有 0.05–0.1 s 偏差：在标点前后 0.25 s 内找"听不见的连续段"
        lo=max(0,pe-50); hi=min(len(e)-1,ns+50)
        if cuts: lo=max(lo,cuts[-1][1]//F+1)
        runs=[];st=None
        for f in range(lo,hi+1):
            q=e[f]<AUD_DB
            if q and st is None: st=f
            if (not q or f==hi) and st is not None:
                en=f if not q else f+1
                if en-st>=3:
                    floor=cuts[-1][1]//F+1 if cuts else 0
                    while st-1>=floor and st>pe-120 and e[st-1]<AUD_DB: st-=1       # 停顿可能早于查找范围就开始：往前延伸到它真正的起点
                    while en<len(e) and en<ns+120 and e[en]<AUD_DB: en+=1            # 同理往后延伸
                    runs.append((st,en))
                st=None
        long=[r for r in runs if r[1]-r[0]>=16]                    # ≥80 ms：标点处的真停顿（词内塞音闭塞只有 30–60 ms）
        mid=(pe+ns)/2
        if long: r0,r1=max(long,key=lambda r:r[1]-r[0])
        elif runs: r0,r1=min(runs,key=lambda r:abs((r[0]+r[1])/2-mid))
        else: r0=r1=None
        if r0 is not None:
            ca,cb=(r0+M)*F,max(r0+M,r1-M)*F
            keep=((ca-r0*F)+(r1*F-cb))/SR
        else:                                                         # 两词之间完全连读：在最安静处插入，不删任何声音
            f=min(range(max(lo,pe-20),min(hi,ns+20)+1),key=lambda f:e[f]); ca=cb=f*F; keep=0.0
        if cb>ca and e[ca//F:cb//F].max()>=AUD_DB:
            raise SystemExit(f'【停止】标点处要删的部分里有能听见的声音（A10 词尾被切）：{sent[:60]}')
        cuts.append((ca,cb,max(0.03,gaps[gi]-keep)))
    clips=[];tmap=[];t=0.0;prev=0
    for k2,(x0,x1) in enumerate(pieces):
        end=cuts[k2][0] if k2<len(cuts) else len(w)
        seg=_cap_inner(w[prev:end]); d=len(seg)/SR
        tmap.append((x0,x1,t,t+d)); clips.append(seg); t+=d
        if k2<len(cuts): clips.append(sil(cuts[k2][2])); t+=cuts[k2][2]; prev=cuts[k2][1]
    return clips,tmap
def _split_audio(sent,pieces,gaps):
    clips=[];tmap=[];t=0.0
    for k2,(x0,x1) in enumerate(pieces):
        w=say(sent[x0:x1]); d=len(w)/SR
        tmap.append((x0,x1,t,t+d)); clips.append(w); t+=d
        if k2<len(pieces)-1: clips.append(sil(gaps[k2])); t+=gaps[k2]
    raise SystemExit('【停止】找不到逗号处的自然停顿，不允许退回分段合成（A8）：'+sent[:60])
    return clips,tmap
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
        ch=s['chunks']; lead=P_FIRST if si==0 else P_LEAD+(P_PARA_EXTRA if prev_para is not None and s['para']!=prev_para else 0)
        prev_para=s['para']
        # read the whole sentence naturally: pause only at punctuation (, ; :), not at line breaks
        texts=[re.sub(r'\*\*','',R.strip_gloss(c['en'])).strip() for c in ch]
        sent=' '.join(texts)
        bounds=[];pos=0
        for t in texts: bounds.append(pos); pos+=len(t)+1
        # 牛津逗号列举 A, B, and C / A, B, or C：列举内部的逗号只停 P_LIST
        lst=set()
        for ml in re.finditer(r"(?:\b[\w'-]+(?: [\w'-]+){0,4}, ){2,}(?:and|or) ",sent):  # 并列项每项不超过 5 个词
            for mc in re.finditer(r',',ml.group(0)): lst.add(ml.start()+mc.start())
        pieces=[];p0=0;gaps=[]
        for mm in re.finditer(r'[,;:](?=\s)',sent):
            pieces.append((p0,mm.end())); p0=mm.end()+1; gaps.append(P_LIST if mm.start() in lst else P_COMMA)
        pieces.append((p0,len(sent)))
        # 整句一次合成（2026-10-05 用户定：分段合成会让逗号后的开头发闷），再把模型在逗号处的自然停顿拉长到标准时长
        clips,tmap=sentence_audio(sent,pieces,gaps)
        t=sum(len(c) for c in clips)/SR
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
    END=2.0-P_HOLD; audio.append(sil(END)); tl[-1]=(tl[-1][0],tl[-1][1]+END)  # 片尾：读完后共停 2 秒
    A=np.concatenate(audio); A=A/np.abs(A).max()*0.89
    total=sum(x for _,x in tl)
    # render images: one uniform size = largest that fits every screen with locked layout
    sizes=[R.max_es([[tuple(p) for p in c['align']] for c in s['chunks']],colors,[c.get('note') for c in s['chunks']]) for s in d['sentences']]
    print('sizes',sizes)
    files=[]; t=0
    for (key,dur) in tl:
        prog=min(1,(t+dur)/total)
        fn=f"{work}/{len(files):04d}.png"
        if key[0]=='title':  # 片头：约 1.5 秒入场动画（title_anim），最后一帧停住到片头结束
            import title_anim as TA; fx=d.get('title_fx',{})
            af=TA.render_frames(d['title_en'],d['title_zh'],fx.get('hl',[]),fx.get('ghost',[]),work)
            files+=af[:-1]; t+=sum(x for _,x in af[:-1]); files.append((af[-1][0],dur-sum(x for _,x in af[:-1]))); t+=dur-sum(x for _,x in af[:-1]); continue
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
