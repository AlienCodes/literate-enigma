# 查"没有标点却停顿"的地方：每句配音里，非标点处、听不见的连续段 ≥0.12 s 的位置；超过 0.22 s 即不合格
import re,json,sys
sys.path.insert(0,".")
exec(open('make_video.py').read().split("if __name__")[0])
for no in sys.argv[1:]:
    d=json.load(open(f'scripts/{no}.json'))
    for si,s in enumerate(d['sentences'],1):
        sent=' '.join(re.sub(r'\*\*','',R.strip_gloss(c['en'])).strip() for c in s['chunks'])
        ms=list(re.finditer(r'[,;:](?=\s)',sent)); pieces=[];p0=0
        for mm in ms: pieces.append((p0,mm.end())); p0=mm.end()+1
        pieces.append((p0,len(sent)))
        clips,tm=sentence_audio(sent,pieces,[0.4]*len(ms))
        for (x0,x1,t0,t1),c in zip(tm,clips[::2]):
            e=_env5(c); F=int(0.005*SR); st=None
            for f in range(len(e)+1):
                q=f<len(e) and e[f]<AUD_DB
                if q and st is None: st=f
                if not q and st is not None:
                    L=(f-st)*0.005
                    if L>=0.12 and st>4 and f<len(e)-4:
                        pos=x0+int((x1-x0)*(st*0.005)/max(0.01,(t1-t0)))
                        print(f"{no} S{si} 句中无标点停顿 {L:.2f}s 约在「{sent[max(x0,pos-25):pos]}|{sent[pos:pos+15]}」")
                    st=None
