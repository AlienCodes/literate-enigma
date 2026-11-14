"""出片前必跑（由 交付核查.py 调用）：逐处核对标点停顿——实际停顿是否等于标准、被删部分是否只是停顿里的底噪（A9/A10）。"""
# 逐处核对每个标点：被删部分是否全是无声、词尾是否完整、实际听到的停顿是否等于标准
import re,json,sys
sys.path.insert(0,".")
exec(open('make_video.py').read().split("if __name__")[0])
BREATH_GAP=0.10   # A19：停顿后"第一次有声音"到"真正开口"（10 ms 窗比本句最响的 10 ms 低不到 30 dB，与 L14 同一口径）相隔超过这么久 = 中间有一段不是词的声音（吸气声）
def breath_after(out,t1):
    """停顿静音结束处 t1（秒）之后：第一次有声音（5 ms 帧 ≥ -55 dB）到真正开口（10 ms ≥ -30 dB）相隔多少秒。"""
    e5=_env5(out); F5=int(0.005*SR); b=int(t1*SR)//F5
    while b<len(e5) and e5[b]<AUD_DB: b+=1
    n=int(0.01*SR); m=len(out)//n; d10=10*np.log10(np.mean(out[:m*n].reshape(m,n)**2,axis=1)+1e-20); d10-=d10.max()
    g=next((x for x in range((b*F5)//n,m) if d10[x]>=-30),m)
    return max(0.0,g*n/SR-b*F5/SR)
if '--自检' in sys.argv:
    # 阳性对照：在一句的第一个逗号停顿之后插进 0.2 秒、-40 dB 的"吸气声"（1–2.5 kHz 带通噪声），必须报出；原样必须不报
    d=json.load(open(f'scripts/{sys.argv[1]}.json'))
    for s in d['sentences']:
        sent=' '.join(re.sub(r'\*\*','',R.strip_gloss(c['en'])).strip() for c in s['chunks']); ms=list(re.finditer(r'[,;:](?=\s)',sent))
        if not ms: continue
        pieces=[];p0=0
        for mm in ms: pieces.append((p0,mm.end())); p0=mm.end()+1
        pieces.append((p0,len(sent))); clips,tm=sentence_audio(sent,pieces,[P_COMMA]*len(ms)); out=np.concatenate(clips); t1=tm[1][2]
        rng=np.random.default_rng(0); nz=rng.standard_normal(int(0.2*SR)); X=np.fft.rfft(nz); f=np.fft.rfftfreq(len(nz),1/SR); X[(f<1000)|(f>2500)]=0
        nz=np.fft.irfft(X,len(nz)); nz*=np.hanning(len(nz)); n5=int(0.005*SR); m=len(out)//n5
        ref=np.sqrt(np.mean(out[:m*n5].reshape(m,n5)**2,axis=1)).max(); nz*=ref*10**(-40/20)/np.sqrt(np.mean(nz[len(nz)//2-n5:len(nz)//2+n5]**2))
        i=int(t1*SR); bad=np.concatenate([out[:i],nz,out[i:]])
        g0=breath_after(out,t1); g1=breath_after(bad,t1); ok=g0<BREATH_GAP<=g1
        print(f"{'✔' if ok else '✘'} A19 自检：{sent[:30]}… 原样 {g0:.3f}s（不报）、插入假吸气声 {g1:.3f}s（必须报）"); sys.exit(0 if ok else 1)
bad=0;rows=[]
for no in sys.argv[1:]:
    d=json.load(open(f'scripts/{no}.json'))
    for si,s in enumerate(d['sentences'],1):
        sent=' '.join(re.sub(r'\*\*','',R.strip_gloss(c['en'])).strip() for c in s['chunks'])
        ms=list(re.finditer(r'[,;:](?=\s)',sent))
        if not ms: continue
        lst = list_commas(sent)   # 列举逗号与出片程序同一个函数（make_video.list_commas）
        pieces=[];p0=0;gaps=[]
        for mm in ms: pieces.append((p0,mm.end())); p0=mm.end()+1; gaps.append(P_LIST if mm.start() in lst else P_COMMA)
        pieces.append((p0,len(sent)))
        try: clips,tm=sentence_audio(sent,pieces,gaps)
        except SystemExit as ex: print('FAIL',no,si,ex); bad+=1; continue
        gaps=LAST.get('gaps',gaps)                                     # 这一句实际用的标准停顿（结尾句最后一段前是结尾的长度）
        out=np.concatenate(clips); e=_env5(out); F=int(0.005*SR)
        for k2 in range(len(ms)):
            t_sil0=tm[k2][3]; t_sil1=tm[k2+1][2]   # 插入静音的起止（秒）
            f0=int(t_sil0*SR)//F; f1=int(t_sil1*SR)//F
            a=f0
            while a>0 and e[a-1]<AUD_DB: a-=1
            b=f1
            while b<len(e) and e[b]<AUD_DB: b+=1
            heard=(b-a)*F/SR
            ok=abs(heard-gaps[k2])<=0.04
            bg=breath_after(out,t_sil1)
            if bg>=BREATH_GAP:
                ok=False; rows.append(f"{no} S{si} BAD A19 「{sent[max(0,ms[k2].start()-16):ms[k2].end()]}」 停顿后有 {bg:.2f}s 不是词的声音（吸气声），词到词比标准长：用实际声音找出切点写进“停顿删除区间”或“非人声区间”（纯人声，不留任何呼吸声）")
            if not ok: bad+=1
            rows.append(f"{no} S{si} {'OK ' if ok else 'BAD'} 「{sent[max(0,ms[k2].start()-16):ms[k2].end()]}」 标准 {gaps[k2]}s，实际听到 {heard:.2f}s")
print('\n'.join(rows)); print('问题数',bad)
