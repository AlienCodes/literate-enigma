"""出片前必跑（由 交付核查.py 调用）：逐处核对标点停顿——实际停顿是否等于标准、被删部分是否只是停顿里的底噪（A9/A10）。"""
# 逐处核对每个标点：被删部分是否全是无声、词尾是否完整、实际听到的停顿是否等于标准
import re,json,sys
sys.path.insert(0,".")
exec(open('make_video.py').read().split("if __name__")[0])
bad=0;rows=[]
for no in sys.argv[1:]:
    d=json.load(open(f'scripts/{no}.json'))
    for si,s in enumerate(d['sentences'],1):
        sent=' '.join(re.sub(r'\*\*','',R.strip_gloss(c['en'])).strip() for c in s['chunks'])
        ms=list(re.finditer(r'[,;:](?=\s)',sent))
        if not ms: continue
        lst=set()
        for ml in re.finditer(r"(?:\b[\w'-]+(?: [\w'-]+){0,4}, ){2,}(?:and|or) ",sent):
            for mc in re.finditer(r',',ml.group(0)): lst.add(ml.start()+mc.start())
        pieces=[];p0=0;gaps=[]
        for mm in ms: pieces.append((p0,mm.end())); p0=mm.end()+1; gaps.append(P_LIST if mm.start() in lst else P_COMMA)
        pieces.append((p0,len(sent)))
        try: clips,tm=sentence_audio(sent,pieces,gaps)
        except SystemExit as ex: print('FAIL',no,si,ex); bad+=1; continue
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
            if not ok: bad+=1
            rows.append(f"{no} S{si} {'OK ' if ok else 'BAD'} 「{sent[max(0,ms[k2].start()-16):ms[k2].end()]}」 标准 {gaps[k2]}s，实际听到 {heard:.2f}s")
print('\n'.join(rows)); print('问题数',bad)
