# 全面核对（所有句子）：①句尾修剪掉的部分是否全是听不见的；②每个标点停顿前的那段文字，长度是否与单独朗读该段一致（防止停顿落在词中间）
import re,json,sys
sys.path.insert(0,".")
exec(open('make_video.py').read().split("if __name__")[0])
bad=0
for no in sys.argv[1:]:
    d=json.load(open(f'scripts/{no}.json'))
    texts=[d['title_en']]+[' '.join(re.sub(r'\*\*','',R.strip_gloss(c['en'])).strip() for c in s['chunks']) for s in d['sentences']]
    for si,sent in enumerate(texts):
        raw,_=k.create(sent,voice=V,speed=SPEED,lang='en-us'); w=clean_tail(raw)
        # ① 找到 w 在 raw 中的位置，检查被修剪掉的首尾部分
        pk=np.abs(raw).max(); n=int(0.005*SR)
        st=next(i for i in range(0,len(raw)-len(w)+1) if np.allclose(raw[i+n*10:i+n*10+200],w[n*10:n*10+200],atol=1e-6))
        head=raw[:st]; tail=raw[st+len(w):]
        def mx(x): 
            if len(x)<n: return -99
            m=len(x)//n; return float((20*np.log10(np.sqrt(np.mean(x[:m*n].reshape(m,n)**2,axis=1))/pk+1e-9)).max())
        # 淡出段（最后 50 ms）原本的响度
        fade=raw[st+len(w)-int(0.05*SR):st+len(w)]
        h,tl,fd=mx(head),mx(tail),mx(fade)
        flag=(h>=AUD_DB) or (tl>=AUD_DB) or (fd>=-35)
        if flag: bad+=1
        print(f"{no} {'标题' if si==0 else 'S%d'%si} {'BAD' if flag else 'OK '} 句首删掉 {len(head)/SR:.2f}s 最响 {h:.0f}dB｜句尾删掉 {len(tail)/SR:.2f}s 最响 {tl:.0f}dB｜淡出段原响度 {fd:.0f}dB")
        # ② 停顿位置
        ms=list(re.finditer(r'[,;:](?=\s)',sent))
        if si==0 or not ms: continue
        pieces=[];p0=0
        for mm in ms: pieces.append((p0,mm.end())); p0=mm.end()+1
        pieces.append((p0,len(sent)))
        clips,tm=sentence_audio(sent,pieces,[0.4]*len(ms))
        for x0,x1,t0,t1 in tm[:-1]:
            ref=len(say(sent[x0:x1]))/SR; r=(t1-t0)/ref
            ok=0.75<r<1.15
            if not ok: bad+=1
            print(f"     {'OK ' if ok else 'BAD'} 停顿前「{sent[x0:x1][-24:]}」句中 {t1-t0:.2f}s / 单读 {ref:.2f}s = {r:.2f}")
print('问题数',bad)
