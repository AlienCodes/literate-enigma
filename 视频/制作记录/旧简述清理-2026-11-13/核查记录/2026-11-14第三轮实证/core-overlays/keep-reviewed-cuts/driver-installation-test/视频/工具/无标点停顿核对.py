# 查"没有标点却停顿"的地方：每句配音里，非标点处、听不见的连续段 ≥0.12 s 的位置；超过 0.22 s 即不合格
import re,json,sys
sys.path.insert(0,".")
exec(open('make_video.py').read().split("if __name__")[0])
碎声帧, 碎声上限, 碎声两边 = 3, AUD_DB + 10, 10   # K146（39 S5 1998 | President）：两段听不见（各 ≥50 ms）中间只夹着 ≤15 ms、最响不到 -45 dB 的碎声（气声残尾），不算词，停顿连起来量；
# 碎声离词只隔几帧的（37 S15 on | 10：5 ms -54 dB、离下一个词 10 ms，是起音余波）不并
def 查段(c, 并碎声=False):
    """一段（标点之间）声音里，听不见的连续段 ≥0.12 s 的位置（帧号, 秒）；并碎声：夹在两段听不见之间的碎声并进停顿（37 起）"""
    e=_env5(c); st=None; out=[]; q_=[f<len(e) and e[f]<AUD_DB for f in range(len(e)+1)]
    if 并碎声:
        f=0
        while f<len(e):
            if not q_[f] and f>0 and q_[f-1]:
                g=f
                while g<len(e) and not q_[g]: g+=1
                前=f-max([k for k in range(f) if not q_[k]],default=-1)-1; 后=next((k for k in range(g,len(e)) if not q_[k]),len(e))-g
                if g<len(e) and g-f<=碎声帧 and max(e[f:g])<碎声上限 and 前>=碎声两边 and 后>=碎声两边:
                    for k in range(f,g): q_[k]=True
                f=g
            else: f+=1
    for f in range(len(e)+1):
        q=q_[f]
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
    # K146 坏样本：0.18 秒静音 + 15 ms -54 dB 碎声 + 0.17 秒静音（39 S5），并碎声时必须报出；好样本：中间是 15 ms -30 dB 的除阻（真辅音），不并
    F_=int(0.005*SR); m_=len(c)//F_; ref_=float(np.sqrt(np.mean(np.asarray(c[:m_*F_],np.float64).reshape(m_,F_)**2,axis=1)).max())   # 本句最响 5 ms 帧（_env5 的基准）
    z1,z2=np.zeros(int(0.18*SR),dtype=c.dtype),np.zeros(int(0.17*SR),dtype=c.dtype); ns=np.random.default_rng(5).standard_normal(int(0.015*SR))
    bl=lambda dB:(ns/np.sqrt(np.mean(ns**2))*ref_*10**(dB/20)).astype(c.dtype)
    c3=np.concatenate([c[:k],z1,bl(-54),z2,c[k:]]); c4=np.concatenate([c[:k],z1,bl(-28),z2,c[k:]])
    c5=np.concatenate([c[:k],np.zeros(int(0.215*SR),dtype=c.dtype),bl(-54)[:int(0.005*SR)],np.zeros(int(0.01*SR),dtype=c.dtype),c[k:]])   # 37 S15：碎声离下一个词 10 ms，不并
    o3=[L for _,L in 查段(c3,True) if L>0.22]; o3旧=[L for _,L in 查段(c3) if L>0.22]; o4=[L for _,L in 查段(c4,True) if L>0.22]
    o5=[L for _,L in 查段(c5,True) if L>0.22]
    ok=ok and bool(o3) and not o3旧 and not o4 and not o5 and not [L for _,L in 查段(c,True) if L>0.22]
    print(f"{'✔' if ok else '✘'} 无标点停顿核对 自检：{no} S1 原样{'报（前提不成立）' if o0 else '不报'}、插入 0.25 秒静音{'报出' if o1 else '没抓到'}（A4）；"
          f"0.18+碎声+0.17 秒{'报出' if o3 else '没抓到'}（K146，不并碎声时{'不报' if not o3旧 else '也报（样本没造对）'}）、中间是真辅音{'误报' if o4 else '不报'}、碎声贴着词{'误报' if o5 else '不报'}")
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
            for st,L in 查段(c, str(no).isdigit() and int(no)>=37):   # K146：37 起并碎声；01–36 已定稿不回头改
                pos=x0+int((x1-x0)*(st*0.005)/max(0.01,(t1-t0)))
                print(f"{no} S{si} 句中无标点停顿 {L:.2f}s 约在「{sent[max(x0,pos-25):pos]}|{sent[pos:pos+15]}」")
