# 标定：每个块边界，几种估计 vs 乙（单独合成拼接 + DTW）。只读，不改任何文件
import sys, os, re, json, numpy as np, soundfile as sf
hsrc=open('/home/user/postgraduate-vocabulary/视频/工具/高亮同步核对.py').read()
src=open('make_video.py').read().split("if __name__")[0]; exec(src)
exec(hsrc[hsrc.index('def logmel'):hsrc.index('bad = 0; rows = []')])
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
    parts=[say(t) for t in texts]; cat=np.concatenate(parts); bnd=np.cumsum([0]+[len(p) for p in parts])//240
    mpb=dtw_map(logmel(cat),ls)
    m=lambda t: a0+mpa[min(len(mpa)-1,int(round(t*100)))]/100
    for ci in range(1,len(ch)):
        j=js[ci]; c1=m(toks[j].start)
        i=j-1
        while i>=0 and toks[i].phoneme in 'ˈˌ': i-=1
        sp_=toks[i] if toks[i].phoneme==' ' else None
        c3=m(sp_.start) if sp_ else c1
        punct=texts[ci-1].rstrip()[-1] in ',;:.!?'
        ob=a0+mpb[min(len(mpb)-1,onset_frame(cat,bnd[ci]))]/100
        out.append(f"{no} S{si+1} b{ci+1} {'P' if punct else 'N'} B {ob:.3f} c1 {c1:.3f} c3 {c3:.3f} sw {starts[kc+ci]:.3f} first={texts[ci].split()[0]} prev={texts[ci-1].split()[-1]}")
    kc+=len(ch)
print('\n'.join(out))
