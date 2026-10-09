# 全面核对（标题和所有句子）：clean_tail 在句首、句尾修剪掉的部分有没有剪到词。（停顿位置改由 停顿位置精确核对.py 负责）
# 2026-10-09 修正两处错误（A10b 复犯）：① 基准改成本句最响的 5 ms 帧（原来用单个采样点的峰值，比 5 ms 帧高约 10 dB，等于把门槛放宽了 10 dB）；
# ② 合成前先经过数字读法 spoken()、去掉粗体和中文说明（与出片程序 say()/sentence_audio 完全相同；原来直接合成原文，数字处与成片不是同一段声音）。
# 判定（电平都相对本句最响的 5 ms 帧，能听见 = ≥-55 dB，A13）：
#   句首：剪掉的部分里有能听见的帧，并且它和留下的第一个能听见的帧之间听不见的部分不到 15 ms（3 帧，与 纯人声核对 ④ 同一口径）= 与词相连，剪到了第一个词的起音 → BAD；
#        隔着 ≥15 ms 听不见部分的，是开口前孤立的杂音（纯人声要删），列出不报错。（06 S5：剪点前 15–20 ms 一个 -55 dB、重心 4.2 kHz 的杂点，与 A 的起音隔着 25 ms 静音）
#   句尾：剪掉的部分里有任何能听见的帧 → BAD（可能是词尾塞音的除阻，要用实际声音核实）。
#   淡出：句尾淡出改动过的样本里，原来的声音有 ≥-55 dB 的帧 → BAD（A21：原来用 -40 dB，-40～-55 dB 的词尾除阻被压低也放过了，06 intelligent.）。
import re,json,sys
sys.path.insert(0,".")
exec(open('make_video.py').read().split("if __name__")[0])
F5=int(0.005*SR)
def db5(x,ref):
    m=len(x)//F5
    return 20*np.log10(np.sqrt(np.mean(x[:m*F5].reshape(m,F5)**2,axis=1))/ref+1e-9) if m else np.zeros(0)
def head_conn(raw,st,ref):
    """句首剪点 st：剪掉的部分里最靠后的能听见的帧离剪点几帧、与留下的第一个能听见的帧之间隔几帧；隔不到 3 帧（15 ms）= 与词相连"""
    nb=st//F5; pre=db5(raw[st-nb*F5:st],ref)[::-1]; post=db5(raw[st:st+int(0.5*SR)],ref)
    k_pre=next((i for i,v in enumerate(pre) if v>=AUD_DB),None); j_post=next((i for i,v in enumerate(post) if v>=AUD_DB),len(post))
    return k_pre is not None and k_pre+j_post<3, k_pre, j_post, (float(pre.max()) if len(pre) else -99.0)
def tail_vals(raw,w,st,ref):
    """句尾：剪掉的部分（raw 在 w 之后的部分）最响的帧；淡出改动过的样本（w 与原始合成不同的部分，句首 10 ms 淡入除外）原来最响的帧。
    A21：改动处原来能听见（≥-55 dB）= 淡出压低了词尾（原来的口径是“淡出段原响度 ≥-40 dB”，-40～-55 dB 的词尾除阻被压低也放过了：06 intelligent. 的 /t/）"""
    en=st+len(w); tail=db5(raw[en:],ref); n=min(len(w),len(raw)-st)
    ch=np.where(w[int(0.01*SR):n]!=raw[st+int(0.01*SR):st+n])[0]
    fade=db5(raw,ref)[(st+int(0.01*SR)+ch[0])//F5:(min(en,len(raw))+F5-1)//F5] if len(ch) else np.zeros(0)   # 按原始合成的 5 ms 帧（与出片程序 _keep_tail 同一套帧）
    mx=lambda x: float(x.max()) if len(x) else -99.0
    return mx(tail),mx(fade)
def tail_flags(raw,w,st,ref):
    tl,fd=tail_vals(raw,w,st,ref); return tl>=AUD_DB or fd>=AUD_DB
if '--自检' in sys.argv:
    # 阳性对照：把第一句的句首剪点挪到第一个词起音之后 10 ms（剪进起音），必须报“与词相连”；原样剪点不得这样报
    no=sys.argv[1]; d=json.load(open(f'scripts/{no}.json')); s0=d['sentences'][0]
    sent=' '.join(re.sub(r'\*\*','',R.strip_gloss(c['en'])).strip() for c in s0['chunks'])
    raw,_=k.create(spoken(sent),voice=V,speed=SPEED,lang='en-us'); raw=np.asarray(raw,np.float32); w=clean_tail(raw); st=_head_offset(raw,w)
    m=len(raw)//F5; ref=np.sqrt(np.mean(raw[:m*F5].reshape(m,F5)**2,axis=1)).max()
    post=db5(raw[st:],ref); j=next(i for i,v in enumerate(post) if v>=AUD_DB); bad_st=st+(j+2)*F5
    c0=head_conn(raw,st,ref)[0]; c1=head_conn(raw,bad_st,ref)[0]
    # 句尾（A21）：把 S1 的句尾剪进最后一个能听见的帧之前 20 ms、再淡出 50 ms（旧 clean_tail 剪 intelligent. 的样子），必须报；原样不报
    w=_keep_tail(raw,w,st); t0=tail_flags(raw,w,st,ref)
    au=np.where(db5(raw,ref)>=AUD_DB)[0]; cut=(au[-1]+1)*F5-int(0.02*SR)-st; wb=w[:cut].copy(); fz=int(0.05*SR); wb[-fz:]*=np.linspace(1,0,fz)**2
    t1=tail_flags(raw,wb,st,ref); ok=(not c0) and c1 and (not t0) and t1
    print(f"{'✔' if ok else '✘'} 句首句尾核对 自检：{no} S1 原剪点 {st/SR:.3f}s {'报' if c0 else '不报'}；挪进起音 10 ms（{bad_st/SR:.3f}s）{'报出' if c1 else '没报出'}；"
          f"句尾原样{'报' if t0 else '不报'}，剪进听得见的词尾 20 ms 并淡出{'报出' if t1 else '没报出'}")
    sys.exit(0 if ok else 1)
bad=0
for no in sys.argv[1:]:
    d=json.load(open(f'scripts/{no}.json'))
    texts=[d['title_en']]+[' '.join(re.sub(r'\*\*','',R.strip_gloss(c['en'])).strip() for c in s['chunks']) for s in d['sentences']]
    for si,sent in enumerate(texts):
        raw,_=k.create(spoken(re.sub(r'\*\*','',R.strip_gloss(sent))),voice=V,speed=SPEED,lang='en-us'); raw=np.asarray(raw,np.float32); w=clean_tail(raw)
        st=_head_offset(raw,w); w=_keep_tail(raw,w,st); en=st+len(w)          # A21：与出片程序同一个句尾（听得见的词尾接上，淡出只在听不见的 5 ms）
        m=len(raw)//F5; ref=np.sqrt(np.mean(raw[:m*F5].reshape(m,F5)**2,axis=1)).max()
        # 以剪点为界往前、往后各按 5 ms 分帧（帧边界对齐剪点）
        conn,k_pre,j_post,hf=head_conn(raw,st,ref)                           # 剪掉的能听见的声音与留下的声音之间听不见的部分不到 15 ms = 相连
        tl,fd=tail_vals(raw,w,st,ref)
        flag=conn or (tl>=AUD_DB) or (fd>=AUD_DB)
        if flag: bad+=1
        note=('（剪掉的能听见的声音与第一个词相连：剪到了起音）' if conn else f'（剪掉了开口前孤立的杂音：最响 {hf:.0f}dB，离剪点 {5*k_pre} ms，与词之间隔着 {5*(k_pre+j_post)} ms 听不见的部分，不是词）') if k_pre is not None else ''
        print(f"{no} {'标题' if si==0 else 'S%d'%si} {'BAD' if flag else 'OK '} 句首删掉 {st/SR:.3f}s 最响 {hf:.0f}dB{note}｜句尾删掉 {(len(raw)-en)/SR:.3f}s 最响 {tl:.0f}dB｜淡出改动处原响度 {fd:.0f}dB")
print('问题数',bad)
