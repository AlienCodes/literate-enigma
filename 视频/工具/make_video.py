import json,re,os,sys,subprocess,numpy as np,soundfile as sf,imageio_ffmpeg
sys.path.insert(0,'../tts')
from kokoro_onnx import Kokoro
from clean import clean_tail,SR
import render as R
import title2 as T2
TTS='../tts'
k=Kokoro(f'{TTS}/kokoro-v1.0.onnx',f'{TTS}/voices-v1.0.bin'); V=np.load(f'{TTS}/'+os.environ.get('VOICE','voice_mb.npy'))
KT=Kokoro(f'{TTS}/kokoro-v1.0-timed.onnx',f'{TTS}/voices-v1.0.bin')  # 只用来取每个音的准确时间（定位标点），声音仍用上面的原模型
# 合成缓存（2026-10-09，提速）：同一模型、同一音色、同一语速、同一段文字，合成结果逐样本相同（各篇配音指纹多次重做都一致），
# 所以第一次合成后存进 ../tts/cache_tts/，以后直接读，出片和所有核查程序（都 exec 本文件）不再反复合成；声音与不缓存时逐样本相同。
# 键里有模型文件（大小、修改时间）、音色数组的校验码、语速、语言、全部参数；任何一项变了就重新合成。独立复核（独立复核/synth.py）自己合成，不用这个缓存。
import hashlib as _hl, pickle as _pk
_CACHE=f'{TTS}/cache_tts'; os.makedirs(_CACHE,exist_ok=True)
def _cached(obj,meth,model):
    fn=getattr(obj,meth); mid=f'{model}:{os.path.getsize(model)}:{int(os.path.getmtime(model))}'
    def g(text,voice,speed=1.0,lang='en-us',**kw):
        vh=_hl.sha1(np.ascontiguousarray(voice).tobytes()).hexdigest() if not isinstance(voice,str) else voice
        p=f"{_CACHE}/{_hl.sha1(repr((meth,mid,text,vh,float(speed),lang,sorted(kw.items()))).encode()).hexdigest()}.pkl"
        if os.path.exists(p):
            with open(p,'rb') as f: return _pk.load(f)
        r=fn(text,voice=voice,speed=speed,lang=lang,**kw)
        if meth=='create_timed': r=(r[0],r[1],list(r[2]))
        q=f'{p}.{os.getpid()}'
        with open(q,'wb') as f: _pk.dump(r,f)
        os.replace(q,p); return r
    return g
k.create=_cached(k,'create',f'{TTS}/kokoro-v1.0.onnx'); KT.create_timed=_cached(KT,'create_timed',f'{TTS}/kokoro-v1.0-timed.onnx')
AF=open(f'{TTS}/'+os.environ.get('AFFILE','AF.txt')).read().strip(); FF=imageio_ffmpeg.get_ffmpeg_exe(); SPEED=0.95
T=dict(BG_TOP=(14,36,30),BG_BOT=(20,48,40),FG_EN=(240,247,242),FG_ZH=(170,196,182),DIM=(110,140,125),
   PAL=[(251,191,36),(56,189,248),(244,114,182),(190,242,100),(196,181,253),(251,146,60),(94,234,212),(252,165,165)])
for a,b in T.items(): setattr(R,a,b)

P_CHUNK=0.6; P_COMMA=0.4; P_HOLD=0.7; P_LEAD=0.3; P_PARA_EXTRA=0.2; P_TITLE=0.6; P_FIRST=0.4;  # 标题读完停 0.6 秒 → 切到正文第一屏 → 再停 0.4 秒开读（共 1 秒）
P_LIST=0.2  # 牛津逗号列举（A, B, and C）里的逗号：0.2 秒

# 朗读用的数字读法（A11：配音模型把 1995 读成 "nineteen hundred ninety-five"、1960s 读成 "nineteen hundred sixty z"）
_ONES='zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen'.split()
_TENS='_ _ twenty thirty forty fifty sixty seventy eighty ninety'.split()
_ORD={'one':'first','two':'second','three':'third','five':'fifth','eight':'eighth','nine':'ninth','twelve':'twelfth'}
def _n2w(n):
    if n<20: return _ONES[n]
    return _TENS[n//10]+('' if n%10==0 else '-'+_ONES[n%10])
def _ordinal(n):
    w=_n2w(n); last=w.split('-')[-1]
    o=_ORD.get(last, last[:-1]+'ieth' if last.endswith('y') else last+'th')
    return '-'.join(w.split('-')[:-1]+[o])
def _year(y):
    hi,lo=divmod(y,100)
    if lo==0: return _n2w(hi)+' hundred'
    return _n2w(hi)+' '+('oh '+_ONES[lo] if lo<10 else _n2w(lo))
_PL={'twenty':'twenties','thirty':'thirties','forty':'forties','fifty':'fifties','sixty':'sixties','seventy':'seventies','eighty':'eighties','ninety':'nineties'}
_MONTHS='January|February|March|April|May|June|July|August|September|October|November|December'
def spoken(t):
    t=re.sub(r'\b(1[1-9])(\d)0s\b',lambda m:_n2w(int(m.group(1)))+' '+_PL[_TENS[int(m.group(2))]],t)          # 1960s → nineteen sixties
    t=re.sub(r'\b([1-9]|[12]\d|3[01]) ('+_MONTHS+r')\b',lambda m:'the '+_ordinal(int(m.group(1)))+' of '+m.group(2),t)  # 6 January → the sixth of January
    t=re.sub(r'(?<!\d,)(?<!\d)\b(1[1-9]\d\d)\b(?!,\d)(?!\d)',lambda m:_year(int(m.group(1))),t)                       # 1995 → nineteen ninety-five
    # 引号不停顿（2026-10-08 用户定）：配音时不读引号（模型读到引号会把前一个词拖长、顿一下），屏幕照常显示；
    # 双引号一律去掉；单引号只去掉当引号用的（词中间的撇号 Stanford's、don't 保留）
    t=re.sub(r'["“”‘]|(?<![A-Za-z])[\'’]|[\'’](?![A-Za-z])','',t)
    return t
def say(t):
    w,_=k.create(spoken(re.sub(r'\*\*','',R.strip_gloss(t))),voice=V,speed=SPEED,lang='en-us'); return clean_tail(w)
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
PAUSE_DB=-40  # 找停顿用：比本句最响帧低 40 dB 以上
AUD_DB=-55   # 能听见 = 比本句最响 5 ms 帧低不到 55 dB（A13：判断听不听得见一律以 -55 dB 为准，不得另设“可闻线”）；用来保住词尾词头、量“实际听到的停顿”（词到词）
def _env5(w):
    # 基准 = 本句最响的 5 ms 帧的平均响度（A10 复查：用单个采样峰值做基准会高约 10 dB，等于放宽门槛，词尾 /f/ /k/ 仍被切）
    n=int(0.005*SR); m=len(w)//n; r=np.sqrt(np.mean(w[:m*n].reshape(m,n)**2,axis=1))
    return 20*np.log10(r/(r.max()+1e-12)+1e-9)
INNER_MAX=0.22; INNER_TO=0.18   # 没有标点的地方：模型自己停顿超过 0.22 s 的，压缩到 0.18 s（硬性条件：无标点处整句连读）
def _purify(x):
    """纯人声（用户 2026-10-09：“底噪也不要”）：低于本句最响 5 ms 帧 55 dB 的连续段（≥15 ms，或挨着插入的静音）换成数字静音；
    挨着声音的一头各留 1 帧（5 ms），供核查确认词尾已衰减到 -55 dB、下一个词从 -55 dB 处开始。长度不变，时间轴不变。"""
    x=x.copy(); F_=int(0.005*SR); n_=len(x)//F_
    if n_==0: return x
    r_=np.sqrt(np.mean(x[:n_*F_].reshape(n_,F_)**2,axis=1)); q_=20*np.log10(r_/(r_.max()+1e-12)+1e-9)<AUD_DB
    f_=0
    while f_<n_:
        if not q_[f_]: f_+=1; continue
        g_=f_
        while g_<n_ and q_[g_]: g_+=1
        a_=f_+(1 if f_>0 else 0); b_=g_-(1 if g_<n_ else 0)
        if g_-f_>=3 and b_>a_: x[a_*F_:b_*F_]=0          # 插入的静音也算在这一段里，所以停顿两边留下的底噪一并清掉
        f_=g_
    if n_*F_<len(x) and q_[-1]: x[n_*F_:]=0
    return x
def _edges(x):
    """A20（句号、段落、标题、片尾的停顿也按词到词量）：返回能听见的部分 [hs, te)——从第一个到最后一个比本句最响 5 ms 帧低不到 55 dB 的帧。
    两头听不见的部分（_purify 之后只剩数字静音和紧挨声音的 1 帧）都去掉，句与句之间插入的静音就正好等于停顿表的时长。
    （原来两头各多出 0.02–0.08 秒听不见的部分，句号、段落停顿词到词实际是 1.05–1.10 / 1.25–1.30 秒。）"""
    F_=int(0.005*SR); n_=len(x)//F_
    r_=np.sqrt(np.mean(x[:n_*F_].reshape(n_,F_)**2,axis=1)); au=np.where(20*np.log10(r_/(r_.max()+1e-12)+1e-9)>=AUD_DB)[0]
    if not len(au): raise SystemExit('【停止】这一段没有能听见的声音（A20）')
    return int(au[0])*F_,int(au[-1]+1)*F_
def _cap_inner(seg):
    """只压缩句中（非标点处）过长的无声段；只删听不见的部分（低于 -55 dB，AUD_DB），两头各保留一半，不碰任何读音。"""
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
def _cap_spans(seg):
    """与 _cap_inner 完全相同的判断，返回被压缩掉的段 [(a,b)]（seg 内的样本位置），用于高亮时间换算"""
    e=_env5(seg); F=int(0.005*SR); out=[];st=None
    for f in range(len(e)+1):
        q=f<len(e) and e[f]<AUD_DB
        if q and st is None: st=f
        if not q and st is not None:
            if (f-st)*0.005>INNER_MAX and st>4 and f<len(e)-4:
                h=int(INNER_TO/2/0.005); out.append(((st+h)*F,(f-h)*F))
            st=None
    return out
def _head_offset(raw,w):
    """clean_tail 在句首裁掉了多少样本（w = raw[st:...]，开头 10 ms 有淡入，从第 10 ms 起逐样本相同）"""
    raw=np.asarray(raw,np.float32); g=int(0.01*SR)+5
    for i in np.where(raw==w[g])[0]-g:
        if 0<=i and i+g+200<=len(raw) and np.array_equal(raw[i+g:i+g+200],w[g:g+200]): return int(i)
    raise SystemExit('【停止】找不到句首裁剪位置（高亮时间无法换算，L14）')
LAST={}
_NOSOUND=set(' ,;:.!?"\'“”‘’()—–-…')
def chunk_token_starts(texts,toks):
    """每一块第一个音在带时长模型音素序列里的位置：逐块转成音素，与整句音素序列做序列比对（不按空格数词：模型会把 in the、to be 连成一组）"""
    import difflib
    full=''.join(x.phoneme for x in toks)
    if full!=KT.tokenizer.phonemize(spoken(' '.join(texts)),'en-us'): raise SystemExit('【停止】带时长模型的音素与朗读文字对不上（L14）')
    cat='';starts=[]
    for t_ in texts:
        p_=KT.tokenizer.phonemize(spoken(t_),'en-us').strip()
        starts.append(len(cat)+(1 if cat else 0)); cat=(cat+' '+p_) if cat else p_
    bl=[b_ for b_ in difflib.SequenceMatcher(None,cat,full,autojunk=False).get_matching_blocks() if b_.size>0]
    out=[]
    for i in starts:
        j=next((b_.b+(i-b_.a) for b_ in bl if b_.a<=i<b_.a+b_.size),None)
        if j is None: j=next((b_.b for b_ in bl if b_.a>i),len(full))
        while j<len(full) and full[j] in _NOSOUND: j+=1
        out.append(j)
    if any(b2<=a2 for a2,b2 in zip(out,out[1:])): raise SystemExit('【停止】各块开头在音素序列里的位置不是递增的（L14）')
    return out
def chunk_times(texts):
    """（L14）每一块开始读的时刻（秒，相对这一句配音的开头）：取这一块第一个音前面那个"空格"的开头（= 上一个词读完），
    换到原始合成 → 减去句首裁剪 → 经过删停顿/补停顿/压缩长停顿换算到成片。
    用空格开头而不是第一个音素的开头：带时长模型标的音素开头常常已经是元音，下一个词的辅音（/l/ /s/ /h/ /f/）其实在空格里就开始了，
    按音素开头会推后 0.06–0.15 秒（01–04 共 8 处用实际声音核对：空格开头 7 处误差 ≤0.05 秒）。
    标点处（逗号、分号、冒号后开始的块）不用这里的结果，出片程序从停顿结束处往后找真正开口的时刻（见 build）。"""
    toks=LAST['toks']; js=chunk_token_starts(texts,toks); out=[]
    for j in js[1:]:
        i=j-1
        while i>=0 and toks[i].phoneme in 'ˈˌ': i-=1
        t_=toks[i].start if i>=0 and toks[i].phoneme==' ' else toks[j].start
        p=int(round(t_*LAST['scale']*SR))-LAST['head']                  # 在 w 里的样本位置
        tt=None
        for k_,(a,b,t0,rm) in enumerate(LAST['segs']):
            if p<a: tt=t0; break                                          # 落在被删的停顿里：从下一段开头算
            if p<b:
                q=p-a; q-=sum(min(q,y)-x for x,y in rm if x<q); tt=t0+q/SR; break
        out.append(LAST['total'] if tt is None else tt)
    return out
# 人工用实际声音核实过的连读处插入点（A15）：scripts/NN.json 的"停顿插入点"：{"S7": {"1": 0.815}}（第几句：{第几个标点: 秒（可精确到样本，取两词交界处的过零点，避免咔哒声）}，
# 秒数是整句一次合成后的声音 w 里的位置），依据写在"核对确认.停顿位置"。出片和所有核查程序（都 exec 本文件）用同一份。
import glob as _glob, json as _json
INSERT_AT={}
for _p in sorted(_glob.glob('scripts/*.json')):
    _d=_json.load(open(_p))
    for _k,_v in _d.get('停顿插入点',{}).items():
        _s=_d['sentences'][int(_k[1:])-1]
        INSERT_AT[' '.join(re.sub(r'\*\*','',R.strip_gloss(c['en'])).strip() for c in _s['chunks'])]={int(g):float(x) for g,x in _v.items()}
# A19：停顿后紧跟一段吸气声时，程序把吸气声当成下一个词的开头，"词到词"的停顿就比标准长（06：0.2 秒的列举逗号实际 0.53 秒）。
# 用实际声音核实后写进 scripts/NN.json：
#   "停顿删除区间"：{"S6": {"2": [起, 止]}}——这一处删掉 w 里 [起, 止) 秒（精确到样本，可越过吸气声；两头紧贴的 5 ms 必须低于 -55 dB，删掉的部分不能有词的声音）；
# 用户 2026-10-09：“不要有任何的呼吸声 语气声……底噪也不要 就要绝对的纯人声”。
#   "非人声区间"：{"S9": [[起, 止], [起, 止, "紧贴词尾"/"紧贴词头"]]}——w 里 [起, 止) 秒是呼吸声、噗声等非人声，先换成数字静音（长度不变），
#   之后停顿和句中空隙照常处理（标点处补成标准停顿，句中过长的压到 0.18 秒）。两头紧贴的 5 ms 都要低于 -55 dB；
#   非人声与词尾/词头之间没有 -55 dB 低谷的，标"紧贴词尾"/"紧贴词头"/"紧贴两头"，那一头切在过零点（词本身不动），依据写进 核对确认.删除段。
#   依据写在"核对确认.停顿删除"/"核对确认.删除段"。出片和所有核查程序（都 exec 本文件）用同一份。
DEL_AT={}; NONVOICE={}
for _p in sorted(_glob.glob('scripts/*.json')):
    _d=_json.load(open(_p))
    for _k,_v in _d.get('停顿删除区间',{}).items():
        _s=_d['sentences'][int(_k[1:])-1]
        DEL_AT[' '.join(re.sub(r'\*\*','',R.strip_gloss(c['en'])).strip() for c in _s['chunks'])]={int(g):x for g,x in _v.items()}
    for _k,_v in _d.get('非人声区间',{}).items():
        if _k=='标题': NONVOICE['标题::'+_d['title_en']]=_v; continue          # 标题里的呼吸声（03 Bacteria · to）
        _s=_d['sentences'][int(_k[1:])-1]
        NONVOICE[' '.join(re.sub(r'\*\*','',R.strip_gloss(c['en'])).strip() for c in _s['chunks'])]=_v
def _nonvoice(w,ivs,label):
    """非人声区间换成数字静音（长度不变）。守门：区间里不能有 ≥-30 dB 的声音；不紧贴词的一头，外侧紧挨着的 5 ms 必须 <-55 dB；
    紧贴词尾/词头的一头必须在过零点（词本身不动）。"""
    e0=_env5(w); F0=int(0.005*SR); rr0=np.sqrt(np.mean(w[:len(e0)*F0].reshape(len(e0),F0)**2,axis=1)).max()
    lv0=lambda x:20*np.log10(np.sqrt(np.mean(x**2))/(rr0+1e-12)+1e-9)
    w=w.copy()
    for iv in ivs:
        x0,x1=int(round(float(iv[0])*SR)),int(round(float(iv[1])*SR)); flag=iv[2] if len(iv)>2 else ''
        if not (0<x0<x1<len(w)) or lv0(w[x0:x1])>-30 or e0[x0//F0:x1//F0].max()>=-30 \
           or (flag not in ('紧贴词尾','紧贴两头') and lv0(w[x0-F0:x0])>=AUD_DB) or (flag not in ('紧贴词头','紧贴两头') and lv0(w[x1:x1+F0])>=AUD_DB) \
           or (flag in ('紧贴词尾','紧贴两头') and w[x0-1]*w[x0]>0 and abs(w[x0])>1e-4) or (flag in ('紧贴词头','紧贴两头') and w[x1-1]*w[x1]>0 and abs(w[x1])>1e-4):
            raise SystemExit(f'【停止】非人声区间不对（有词的声音、两头不够安静，或紧贴词尾/词头的一头不在过零点）：{label[:60]} {iv}')
        w[x0:x1]=0
    return w
def sentence_audio(sent,pieces,gaps):
    """整句一次合成（原模型，声音不变）。标点位置用带时长输出的同版模型精确定位（A9）；
    在标点处只删除"真正无声"的部分（A10：绝不删词尾的 s/f/z 等弱音），再补静音，使实际听到的停顿 = 标准时长。"""
    raw,_=k.create(spoken(sent),voice=V,speed=SPEED,lang='en-us'); w=clean_tail(raw)
    if sent in NONVOICE: w=_nonvoice(w,NONVOICE[sent],sent)
    tb,_,sp=KT.create_timed(spoken(sent),voice=V,speed=SPEED,lang='en-us',clause_pause=0,sentence_pause=0)
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
        # ① 找停顿：比最响帧低 40 dB 以上的连续段（含模型停顿里的底噪、换气声）
        runs=[];st=None
        for f in range(lo,hi+1):
            q=e[f]<PAUSE_DB
            if q and st is None: st=f
            if (not q or f==hi) and st is not None:
                en=f if not q else f+1
                if en-st>=3:
                    floor=cuts[-1][1]//F+1 if cuts else 0
                    while st-1>=floor and st>pe-120 and e[st-1]<PAUSE_DB: st-=1
                    while en<len(e) and en<ns+120 and e[en]<PAUSE_DB: en+=1
                    if en>=pe-30 and st<=ns+8: runs.append((st,en))   # 必须在逗号前后这两个词之间
                st=None
        long=[r for r in runs if r[1]-r[0]>=16]
        r0=r1=None; f=None
        if long: r0,r1=max(long,key=lambda r:r[1]-r[0])
        else:
            # A15：没有长的自然停顿时，候选 = 短静音段 + 足够安静的低谷（与窗口最安静处相差不超过 6 dB），
            # 选离"前一个词结尾 pe"最近的一个。不能按"窗口里最安静"或"离两词中点最近"选：下一个词里 /t/ 的闭塞
            # 常常更安静（cabbies, i|ts），而带时长模型每次运行的时长略有不同，按中点选会时对时错（learned, it）。
            win=list(range(max(lo,pe-16),min(hi,ns+2)+1)); deep=min(e[g] for g in win)
            dips=[g for g in win if e[g]<=min(e[max(0,g-4):g+5]) and e[g]<=deep+6 and not any(s0<=g<s1 for s0,s1 in runs)]
            cand=[(max(s0-pe,pe-(s1-1),0),0,(s0,s1)) for s0,s1 in runs]+[(abs(g-pe),1,g) for g in dips]
            if cand:
                best=min(cand,key=lambda c:(c[0],c[1]))
                if best[1]==0: r0,r1=best[2]
                else: f=best[2]
            else: f=min(win,key=lambda g:e[g])
        if r0 is None:                                                # 两词连读：在选中的低谷处插入，不删任何声音
            ov=INSERT_AT.get(sent,{}).get(gi+1); cx=None
            if ov is not None:                                        # 用实际声音核实过的插入点（A15）：精确到样本（可取两词交界处的过零点）
                cx=int(round(ov*SR)); f=cx//F
                # 必须在该标点附近；是低谷，或虽不是低谷但已很轻（≤ -24 dB，如 /n/→/h/ 的交界：/h/ 比 /n/ 更轻，没有低谷）
                if not (pe-60<=f<=ns+20) or (e[f]>min(e[max(0,f-2):f+3]) and e[f]>-24):
                    raise SystemExit(f'【停止】人工核实的插入点不在该标点附近，或落在响亮的声音上（A15）：{sent[:60]} 第{gi+1}个标点')
            ca=cb=(cx if cx is not None else f*F); keep=0.0
        else:
            # ② 两头往里收：上一个词的尾音保留到它衰减到 -55 dB；下一个词从 -55 dB 处开始保留（A10）
            a=r0
            while a<r1 and e[a]>=AUD_DB: a+=1
            b=r1
            while b>a and e[b-1]>=AUD_DB: b-=1
            if b-a>=2*M+1:
                ca,cb=(a+M)*F,(b-M)*F
                keep=((ca-a*F)+(b*F-cb))/SR          # 听到的停顿从尾音衰减到 -55 dB 起算（与核对口径一致）
            else:
                f=min(range(r0,r1),key=lambda f:e[f]); ca=cb=f*F; keep=max(0,b-a)*F/SR
                ov=INSERT_AT.get(sent,{}).get(gi+1)
                if ov is not None:                                    # 停顿太短、只插不删的这一种，也认人工核实的插入点（A19：06 S2 subtraction, 的 /n/ 余音）
                    cx=int(round(ov*SR))
                    if not (r0*F<=cx<=r1*F) or e[cx//F-1]>=PAUSE_DB:
                        raise SystemExit(f'【停止】人工核实的插入点不在这一段短停顿里（A15/A19）：{sent[:60]} 第{gi+1}个标点')
                    ca=cb=cx
        dv=DEL_AT.get(sent,{}).get(gi+1)
        if dv is not None:
            rr=np.sqrt(np.mean(w[:len(e)*F].reshape(len(e),F)**2,axis=1)).max()
            lv=lambda x:20*np.log10(np.sqrt(np.mean(x**2))/(rr+1e-12)+1e-9)   # 与 _env5 同一基准
        if dv is not None:   # A19：用实际声音核实过的删除区间
            ca,cb=int(round(float(dv[0])*SR)),int(round(float(dv[1])*SR))
            if not (pe-120<=ca//F<cb//F<=ns+120) or e[ca//F:cb//F].max()>=-30 or lv(w[ca-F:ca])>=AUD_DB or lv(w[cb:cb+F])>=AUD_DB:
                raise SystemExit(f'【停止】人工核实的停顿删除区间不在该标点处、删到了词的声音，或两头紧贴的 5 ms 不够安静（A10/A19）：{sent[:60]} 第{gi+1}个标点')
        if dv is not None:
            fa=(ca-1)//F
            while fa>0 and e[fa-1]<AUD_DB: fa-=1
            fb=cb//F
            while fb<len(e) and e[fb]<AUD_DB: fb+=1
            keep=((ca-fa*F)+(fb*F-cb))/SR
            if gaps[gi]-keep<0.03: raise SystemExit(f'【停止】保留的部分已超过标准停顿，放不下静音（A19）：{sent[:60]} 第{gi+1}个标点')
        else:
            if r0 is not None and not (r0*F<=ca<=cb<=r1*F):
                raise SystemExit(f'【停止】删除范围超出了停顿（A9/A10）："{sent[:60]}" 第{gi+1}个标点')
            if cb>ca and (e[ca//F:cb//F].max()>=PAUSE_DB or e[ca//F-M]>=AUD_DB or e[min(len(e)-1,cb//F+M-1)]>=AUD_DB):
                raise SystemExit(f'【停止】标点处要删的部分里有词的声音，或没有保住词尾/词头（A10）：{sent[:60]}')
        cuts.append((ca,cb,max(0.03,gaps[gi]-keep)))
    clips=[];tmap=[];t=0.0;prev=0;segs=[]
    for k2,(x0,x1) in enumerate(pieces):
        end=cuts[k2][0] if k2<len(cuts) else len(w)
        seg=_cap_inner(w[prev:end]); d=len(seg)/SR
        rm=_cap_spans(w[prev:end]); assert len(seg)==end-prev-sum(b-a for a,b in rm)
        segs.append((prev,end,t,rm))
        tmap.append((x0,x1,t,t+d)); clips.append(seg); t+=d
        if k2<len(cuts): clips.append(sil(cuts[k2][2])); t+=cuts[k2][2]; prev=cuts[k2][1]
    ln=[len(c_) for c_ in clips]; pur=_purify(np.concatenate(clips))
    hs,te=_edges(pur); ln[0]-=hs; ln[-1]-=len(pur)-te                  # A20：句首句尾只留能听见的部分
    if ln[0]<=0 or ln[-1]<=0: raise SystemExit(f'【停止】句首/句尾听不见的部分超过了第一段/最后一段（A20）：{sent[:60]}')
    pur=pur[hs:te]; clips=[]; p_=0; sh=hs/SR
    for l_ in ln: clips.append(pur[p_:p_+l_]); p_+=l_
    tmap=[(x0,x1,max(0.0,t0-sh),t1-sh) for x0,x1,t0,t1 in tmap]; tmap[-1]=tmap[-1][:3]+(len(pur)/SR,)
    segs=[(a0,b0,t0-sh,rm) for a0,b0,t0,rm in segs]
    LAST.clear(); LAST.update(toks=toks,scale=scale,head=_head_offset(raw,w),segs=segs,total=len(pur)/SR,cuts=cuts)
    return clips,tmap
def _split_audio(sent,pieces,gaps):
    clips=[];tmap=[];t=0.0
    for k2,(x0,x1) in enumerate(pieces):
        w=say(sent[x0:x1]); d=len(w)/SR
        tmap.append((x0,x1,t,t+d)); clips.append(w); t+=d
        if k2<len(pieces)-1: clips.append(sil(gaps[k2])); t+=gaps[k2]
    raise SystemExit('【停止】找不到逗号处的自然停顿，不允许退回分段合成（A8）：'+sent[:60])
    return clips,tmap
def title_audio(title):
    """标题：整句合成 → 非人声区间（脚本里键为"标题"）换成静音 → 无标点处的长停顿压缩到 0.18 秒（与句子同一条规则）→ 去底噪 → 只留能听见的部分（A20）"""
    w=say(title)
    if '标题::'+title in NONVOICE: w=_nonvoice(w,NONVOICE['标题::'+title],'标题 '+title)
    w=_purify(_cap_inner(w)); return w[slice(*_edges(w))]
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
    ta=title_audio(d['title_en'])
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
        a=np.concatenate(clips)
        # L14：每一块的高亮在这一块开始读时切换（原来按字母个数平均分，数字、长词处会提前或推后 1 秒多）
        # 逗号、分号、冒号后开始的块：从停顿结束处往后找真正开口的时刻——第一个比本句最响 10 ms 低不到 30 dB 的 10 ms
        # （停顿后常有 0.3–0.45 秒的吸气声，比最响处低 38 dB 以上，不算开口；01–04 共 48 处标定，与独立对齐相差 -0.03～+0.05 秒）；
        # 其余块：上一个词读完（空格开头，chunk_times）
        ct=chunk_times(texts); p0={x0:t0 for x0,x1,t0,t1 in tmap}
        n10=int(0.01*SR); m10=len(a)//n10; db10=10*np.log10(np.mean(a[:m10*n10].reshape(m10,n10)**2,axis=1)+1e-20); thr=db10.max()-30
        def speech_on(t):
            f0=int(round(t/0.01)); g=next((x for x in range(f0,min(m10,f0+100)) if db10[x]>=thr),None)
            if g is None: raise SystemExit(f'【停止】标点停顿后 1 秒内找不到开口（L14）：{sent[:60]}')
            return g*0.01
        starts=[0.0]+[speech_on(p0[bounds[ci]]) if bounds[ci] in p0 else ct[ci-1] for ci in range(1,len(ch))]+[len(a)/SR]
        if any(y<=x for x,y in zip(starts,starts[1:])): raise SystemExit(f'【停止】高亮时间不是递增的（L14）：{sent[:60]}')
        audio+=[sil(lead),a,sil(P_HOLD)]
        for ci in range(len(ch)):
            dur=starts[ci+1]-starts[ci]+(lead if ci==0 else 0)+(P_HOLD if ci==len(ch)-1 else 0)
            tl.append(((si,ci),dur))
    END=2.0-P_HOLD; audio.append(sil(END)); tl[-1]=(tl[-1][0],tl[-1][1]+END)  # 片尾：读完后共停 2 秒
    A=np.concatenate(audio); A=A/np.abs(A).max()*0.89
    total=sum(x for _,x in tl)
    if os.environ.get('AUDIO_ONLY'):
        # 只出声音（用户 2026-10-09：“先不要做成视频，我们确定最后的定稿再做成视频”）：写配音 a.wav、时间表 list.txt
        # （片头一项 + 每块一项，时长与正式出片完全相同；图片位置留空），再用同一套后期 AF 做成只有声音的 out，供全部声音核查使用。不画任何画面
        with open(f'{work}/list.txt','w') as f:
            for (key,dur) in tl: f.write(f"file 'AUDIO_ONLY'\nduration {dur:.3f}\n")
            f.write("file 'AUDIO_ONLY'\n")
        sf.write(f'{work}/a.wav',A,SR)
        subprocess.run([FF,'-y','-loglevel','error','-i',f'{work}/a.wav','-af',AF,'-c:a','aac','-b:a','256k','-movflags','+faststart',out],check=True)
        print(out,round(total,1),'s','只出声音（没有画面）'); return
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
