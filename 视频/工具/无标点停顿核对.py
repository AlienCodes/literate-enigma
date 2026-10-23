# 查"没有标点却停顿"的地方：每句配音里，非标点处、听不见的连续段 ≥0.12 s 的位置；超过 0.22 s 即不合格
import re,json,sys
sys.path.insert(0,".")
exec(open('make_video.py').read().split("if __name__")[0])
def 查段(c):
    """一段（标点之间）声音里，听不见的连续段 ≥0.12 s 的位置（帧号, 秒）"""
    e=_env5(c); st=None; out=[]
    for f in range(len(e)+1):
        q=f<len(e) and e[f]<AUD_DB
        if q and st is None: st=f
        if not q and st is not None:
            L=(f-st)*0.005
            if L>=0.12 and st>4 and f<len(e)-4: out.append((st,L))
            st=None
    return out
if '--自检' in sys.argv:
    # 阳性对照（A4）：第 1 句第一段原样不报 >0.22 s；在中间响亮处插 0.25 秒静音，必须报出
    no=[x for x in sys.argv[1:] if x!='--自检'][0]; d=json.load(open(f'scripts/{no}.json')); s=d['sentences'][0]
    sent=' '.join(re.sub(r'\*\*','',R.strip_gloss(c['en'])).strip() for c in s['chunks'])
    ms=list(re.finditer(r'[,;:](?=\s)',sent)); pieces=[];p0=0
    for mm in ms: pieces.append((p0,mm.end())); p0=mm.end()+1
    pieces.append((p0,len(sent)))
    clips,tm=sentence_audio(sent,pieces,[0.4]*len(ms)); c=clips[0]; e=_env5(c)
    loud=[i for i,v in enumerate(e) if v>AUD_DB+20]; k=loud[len(loud)//2]*int(0.005*SR)
    c2=np.concatenate([c[:k],np.zeros(int(0.25*SR),dtype=c.dtype),c[k:]])
    o0=[L for _,L in 查段(c) if L>0.22]; o1=[L for _,L in 查段(c2) if L>0.22]; ok=bool(o1) and not o0
    print(f"{'✔' if ok else '✘'} 无标点停顿核对 自检：{no} S1 原样{'报（前提不成立）' if o0 else '不报'}、插入 0.25 秒静音{'报出' if o1 else '没抓到'}（A4）")
    sys.exit(0 if ok else 1)
for no in sys.argv[1:]:
    d=json.load(open(f'scripts/{no}.json'))
    for si,s in enumerate(d['sentences'],1):
        sent=' '.join(re.sub(r'\*\*','',R.strip_gloss(c['en'])).strip() for c in s['chunks'])
        ms=list(re.finditer(r'[,;:](?=\s)',sent)); pieces=[];p0=0
        for mm in ms: pieces.append((p0,mm.end())); p0=mm.end()+1
        pieces.append((p0,len(sent)))
        clips,tm=sentence_audio(sent,pieces,[0.4]*len(ms))
        for (x0,x1,t0,t1),c in zip(tm,clips[::2]):
            for st,L in 查段(c):
                pos=x0+int((x1-x0)*(st*0.005)/max(0.01,(t1-t0)))
                print(f"{no} S{si} 句中无标点停顿 {L:.2f}s 约在「{sent[max(x0,pos-25):pos]}|{sent[pos:pos+15]}」")
