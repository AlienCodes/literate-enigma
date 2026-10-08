# 标定 2：局部子序列对齐（S）与停顿后第一个可闻帧（P）。只读
import sys, os, re, json, numpy as np, soundfile as sf
hsrc=open('/home/user/postgraduate-vocabulary/视频/工具/高亮同步核对.py').read()
src=open('make_video.py').read().split("if __name__")[0]; exec(src)
exec(hsrc[hsrc.index('def logmel'):hsrc.index('bad = 0; rows = []')])
def lm_raw(x, sr=24000, n_fft=600, hop=240, nm=40):
    x=np.asarray(x,float); win=np.hanning(n_fft); n=1+max(0,(len(x)-n_fft)//hop)
    fr=np.stack([x[i*hop:i*hop+n_fft]*win for i in range(n)]); sp=np.abs(np.fft.rfft(fr,axis=1))**2
    f=np.fft.rfftfreq(n_fft,1/sr); mel=lambda h:2595*np.log10(1+h/700); pts=700*(10**(np.linspace(mel(60),mel(8000),nm+2)/2595)-1)
    fb=np.zeros((nm,len(f)))
    for m in range(nm):
        l,c,r=pts[m:m+3]; fb[m]=np.clip(np.minimum((f-l)/(c-l),(r-f)/(r-c)),0,None)
    return np.log(sp@fb.T+1e-8)
def subseq_start(q, r):
    """q 在 r 里的最佳子序列对齐：起点、终点自由；返回 r 中的起始帧"""
    n,m=len(q),len(r); C=np.sqrt(((q[:,None,:]-r[None,:,:])**2).sum(2))
    D=np.full((n,m),np.inf); S=np.zeros((n,m),int)
    D[0]=C[0]; S[0]=np.arange(m)
    for i in range(1,n):
        D[i,0]=D[i-1,0]+C[i,0]; S[i,0]=S[i-1,0]
        for j in range(1,m):
            a,b,c=D[i-1,j-1],D[i-1,j],D[i,j-1]
            if a<=b and a<=c: D[i,j]=C[i,j]+a; S[i,j]=S[i-1,j-1]
            elif b<=c: D[i,j]=C[i,j]+b; S[i,j]=S[i-1,j]
            else: D[i,j]=C[i,j]+c; S[i,j]=S[i,j-1]
    j=int(np.argmin(D[-1])); return S[-1,j]
no=sys.argv[1]; wk=sys.argv[2]
d=json.load(open(f'scripts/{no}.json'))
ent=re.findall(r"file '([^']+)'\nduration ([\d.]+)", open(f'{wk}_{no}/list.txt').read())
nch=sum(len(s['chunks']) for s in d['sentences']); scr=ent[-nch:]; t0=sum(float(x) for _,x in ent[:-nch]); starts=[]
for _,du in scr: starts.append(t0); t0+=float(du)
A,sr=sf.read(f'{wk}_{no}/a.wav'); A=np.asarray(A,float)
kc=0; prev_para=None; out=[]
for si,s in enumerate(d['sentences']):
    ch=s['chunks']; lead=P_FIRST if si==0 else P_LEAD+(P_PARA_EXTRA if prev_para is not None and s['para']!=prev_para else 0); prev_para=s['para']
    if len(ch)==1: kc+=1; continue
    texts=[re.sub(r'\*\*','',R.strip_gloss(c['en'])).strip() for c in ch]; sent=' '.join(texts)
    a0=starts[kc]+lead; a1=(starts[kc+len(ch)] if kc+len(ch)<len(starts) else len(A)/sr)-P_HOLD
    seg=A[int(a0*sr):int(a1*sr)]; ls=logmel(seg)
    tb,_,sp=KT.create_timed(spoken(sent),voice=V,speed=SPEED,lang='en-us',clause_pause=0,sentence_pause=0); toks=list(sp)
    js=chunk_token_starts(texts,toks); mpa=dtw_map(logmel(tb),ls)
    m=lambda t: mpa[min(len(mpa)-1,int(round(t*100)))]
    R_=lm_raw(seg); mu=R_.mean(0); sd=R_.std(0)+1e-6; Rn=(R_-mu)/sd
    # 停顿：成片里插入的静音是精确的 0
    z=np.concatenate([[0],(seg==0).astype(np.int8),[0]]); dz=np.diff(z); zr=[(a,b) for a,b in zip(np.where(dz==1)[0],np.where(dz==-1)[0]) if b-a>=int(0.1*sr)]
    env=lm_raw(seg).max(1)
    for ci in range(1,len(ch)):
        j=js[ci]; i=j-1
        while i>=0 and toks[i].phoneme in 'ˈˌ': i-=1
        c3f=m(toks[i].start) if toks[i].phoneme==' ' else m(toks[j].start)
        part=say(texts[ci]); of=onset_frame(part,0); Q=lm_raw(part)[of:of+60]; Qn=(Q-mu)/sd
        lo=max(0,c3f-50); hi=min(len(Rn),c3f+50+len(Qn))
        sS=a0+(lo+subseq_start(Qn,Rn[lo:hi]))/100
        punct=texts[ci-1].rstrip()[-1] in ',;:'
        pz=''
        if punct:
            # 本块前面是第几个标点停顿
            k_=len(re.findall(r'[,;:](?=\s)',' '.join(texts[:ci])+' '))
            if k_-1<len(zr):
                b=zr[k_-1][1]; x=seg[b:b+int(0.3*sr)]; n5=120; e=[20*np.log10(np.sqrt(np.mean(x[q:q+n5]**2))/np.abs(seg).max()+1e-9) for q in range(0,len(x)-n5,n5)]
                f5=next((q for q,v in enumerate(e) if v>-55),0); pz=f'{a0+(b+f5*n5)/sr:.3f}'
            else: pz='none'
        out.append(f"{no} S{si+1} b{ci+1} {'P' if punct else 'N'} S {sS:.3f} c3 {a0+c3f/100:.3f} PZ {pz} first={texts[ci].split()[0]} prev={texts[ci-1].split()[-1]} nz={len(zr)}")
    kc+=len(ch)
print('\n'.join(out))
