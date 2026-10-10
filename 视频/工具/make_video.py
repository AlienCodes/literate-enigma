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
# A23 读音改正（2026-10-09 用户：“每个单词的读音，尤其是这种额外的这种人名啊，或者是物名或者是机构名等等……一定得是正确的……
# 我们是权威性的，这个教学性文章你读错了就完蛋了”）：配音模型的注音程序（espeak 拼读规则）会把词典里没有的词猜错（07 Inky 注成 ɪŋkˈaɪ，
# 正确 /ˈɪŋki/）。读错的词按“词 → 正确音标”登记在 工具/发音词典/读音改正.json（由 读音核对.py 查证后写入，每条带来源）：
# 整句注音后，把这个词被注出的音标换成正确音标再合成；每个登记的词在句中出现几次就必须换掉几次，换不到就停下（不许悄悄漏过）。
# 不含这些词的句子，声音逐样本不变。出片、核查、带时长模型都经过 k.create / KT.create_timed，用的是同一串音标。
_PRON_PATH=os.path.join(os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else '.', '读音改正.json')
for _cand in (_PRON_PATH,'读音改正.json','/home/user/postgraduate-vocabulary/视频/工具/发音词典/读音改正.json'):
    if os.path.exists(_cand):
        _pj=json.load(open(_cand)); PRON_WORDS={k_:v_['读音'] for k_,v_ in _pj.items()}
        PRON_EXTRA={k_:v_['语境错读'] for k_,v_ in _pj.items() if v_.get('语境错读')}   # 单读没错、连读时才读错的写法（08 cholera ravaged → kˈɑːlɚɹɚ）
        break
else: PRON_WORDS={'Inky':'ˈɪŋki'}; PRON_EXTRA={}
def _stress_free_re(ph):
    """不管重音号在哪（音标里每个符号前后都可能有，McArthur 的重音号在空格之后），都能对上这串音标"""
    return ''.join(r'\s*' if ch==' ' else '[ˈˌ]?'+re.escape(ch) for ch in re.sub('[ˈˌ]','',ph))+'[ˈˌ]?'
PRON_FIX={}
def phonemes_of(text):
    ph=KT.tokenizer.phonemize(text,'en-us')
    for w_,good in PRON_WORDS.items():
        n_=len(re.findall(r"(?<![A-Za-z])"+re.escape(w_)+r"(?![A-Za-z])",text,flags=re.I))
        if not n_: continue
        bad=re.sub(r'[,;:.!?]','',KT.tokenizer.phonemize(w_,'en-us')).strip(); PRON_FIX[bad]=good
        if PRON_EXTRA.get(w_):                                          # 连读时另有错法的词：每种错法都换成正确读音，换完这个词每一处都必须是正确读音
            B_="(?<![^\\s,;:.!?])"; E_="(?=[\\s,;:.!?]|$)"
            for f_ in [bad]+list(PRON_EXTRA[w_]):
                if f_!=good: ph=re.sub(B_+_stress_free_re(f_)+E_,good,ph)
            got_=len(re.findall(B_+_stress_free_re(good)+"(?:z)?"+E_,ph))   # 所有格 cholera's 注成 …ɹəz，算正确读音
            if got_!=n_: raise SystemExit(f'【停止】读音改正没有全部换到（A23）：{w_} 出现 {n_} 次，整句里正确读音 {got_} 处：{text[:60]}')
            continue
        if re.sub('[ˈˌ]','',bad)==re.sub('[ˈˌ]','',good) and bad==good: continue
        ph,cnt=re.subn("(?<![^\\s,;:.!?])"+_stress_free_re(bad)+"(?=[\\s,;:.!?]|$)",good,ph)
        if cnt!=n_: raise SystemExit(f'【停止】读音改正没有全部换到（A23）：{w_} 出现 {n_} 次，换了 {cnt} 次：{text[:60]}')
    return ph
def _pron(fn):
    def g(text,voice,speed=1.0,lang='en-us',**kw):
        if not kw.get('is_phonemes') and any(re.search(r"(?<![A-Za-z])"+re.escape(w_)+r"(?![A-Za-z])",text,flags=re.I) for w_ in PRON_WORDS):
            return fn(phonemes_of(text),voice=voice,speed=speed,lang=lang,is_phonemes=True,**kw)
        return fn(text,voice=voice,speed=speed,lang=lang,**kw)
    return g
k.create=_pron(k.create); KT.create_timed=_pron(KT.create_timed)
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
    w,_=k.create(spoken(re.sub(r'\*\*','',R.strip_gloss(t))),voice=V,speed=SPEED,lang='en-us'); c=clean_tail(w); return _keep_tail(w,c,_head_offset(w,c))
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
    if full!=phonemes_of(spoken(' '.join(texts))): raise SystemExit('【停止】带时长模型的音素与朗读文字对不上（L14）')
    cat='';starts=[]
    for t_ in texts:
        p_=phonemes_of(spoken(t_)).strip()
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
DEL_AT={}; NONVOICE={}; GRAFT={}
for _p in sorted(_glob.glob('scripts/*.json')):
    _d=_json.load(open(_p))
    for _k,_v in _d.get('停顿删除区间',{}).items():
        _s=_d['sentences'][int(_k[1:])-1]
        DEL_AT[' '.join(re.sub(r'\*\*','',R.strip_gloss(c['en'])).strip() for c in _s['chunks'])]={int(g):x for g,x in _v.items()}
    for _k,_v in _d.get('非人声区间',{}).items():
        if _k=='标题': NONVOICE['标题::'+_d['title_en']]=_v; continue          # 标题里的呼吸声（03 Bacteria · to）
        _s=_d['sentences'][int(_k[1:])-1]
        NONVOICE[' '.join(re.sub(r'\*\*','',R.strip_gloss(c['en'])).strip() for c in _s['chunks'])]=_v
    for _k,_v in _d.get('词尾除阻',{}).items():                     # A21（见 _graft）
        GRAFT['标题::'+_d['title_en'] if _k=='标题' else ' '.join(re.sub(r'\*\*','',R.strip_gloss(c['en'])).strip() for c in _d['sentences'][int(_k[1:])-1]['chunks'])]=_v
# 结尾句（2026-10-10，用户听过试听后同意：“行，那就先把零七的这种4k最终视频做出来”）：全篇最后一句前段用较快语速、
# 最后一段（最后一个标点之后）用较慢语速，最后一段前的停顿加长，读出结尾的感觉。同一句整句合成两遍，在最后一个标点后那段静音里的
# “接点”（两遍里各一个样本位置，用实际声音核实过：两侧各 10 ms 都低于 -55 dB）接起来，当成这一句的原始合成；之后的处理
# （非人声、移植、停顿、高亮、所有核查、独立复核）都把它当一次合成看待（都用 _ending_raw）。
#   "结尾句"：{"S16": {"前段语速": 0.90, "最后一段语速": 0.78, "最后一段前停顿": 0.70, "接点": [前段样本, 最后一段样本]}}
#   最后一句没有句中标点（01、02）：{"S18": {"整句语速": 0.80}}——整句一个较慢的语速（与 07 试听 B 版的定义一致）
ENDING={}
for _p in sorted(_glob.glob('scripts/*.json')):
    _d=_json.load(open(_p))
    for _k,_v in _d.get('结尾句',{}).items():
        ENDING[' '.join(re.sub(r'\*\*','',R.strip_gloss(c['en'])).strip() for c in _d['sentences'][int(_k[1:])-1]['chunks'])]=_v
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
# A21 词尾除阻（2026-10-09 用户：“Date后面那个t都没有翻译。Intelligent后面那个特也没有翻译”）：配音模型在停顿前（, ; : 和句末）
# 常把词尾 /t/ /k/ 读成不除阻——只闭塞，没有 t 那一下爆破送气（06 date, 的“除阻”-39 dB、重心 1 kHz，不是 t；intelligent. 只有 -49 dB，
# 还被句尾修剪剪掉）。换音素写法（加 ʰ、h）整句重新合成，时好时坏，不可靠（制作记录 A21 有逐处测量）。
# 办法：同一音色在句末清楚除阻的 /t/、/k/（供体：固定的一句话，合成结果有校验码）移植到弱的地方——从闭塞最低点之后起换成供体的爆破送气，
# 响度 = 本句最响 5 ms 帧 -27 dB（01–07 里清楚的词尾 t 是 -21～-30 dB）。长度不变，句子其余部分逐样本不变，人工核实过的区间照样有效。
# 位置写在 scripts/NN.json 的"词尾除阻"：{"S2": {"3": [4.0, "t"]}, "S3": {"句末": [7.1, "t"]}, "标题": {...}}——w 里的秒（精确到样本），
# 由 词尾辅音核对.py --写入 用实际声音量出来（不凭感觉）；哪些要补也由它按门槛判定。出片和所有核查程序（都 exec 本文件）用同一份。
DONOR={'t':("Bring a pipe, and then they left.",'ac4047d887b8'),'k':("Their brains began alike.",'b6329f1b0c07')}
GRAFT_DB=-27
def _release(e,pf,maxback=16):
    """e：5 ms 帧电平（dB，相对本句最响帧）；pf：停顿开始（或最后一个能听见的帧之后）的帧号。往回：跳过听不见的帧 → 除阻 →
    闭塞（比除阻最响低 ≥6 dB 的低谷，取最低点）→ 前面的音。返回 (除阻开始帧 = 闭塞最低帧的下一帧, 除阻结束帧, 除阻最响 dB)；
    往回 80 ms 内一路升高、没有低谷 = 没有单独的除阻，返回 None"""
    q=pf-1
    while q>=0 and e[q]<AUD_DB: q-=1
    if q<0: return None
    pk=e[q]; c=None; r=q
    while r>=0:
        if c is None:
            if e[r]>pk: pk=e[r]
            elif e[r]<=pk-6: c=r
            elif q-r>maxback: return None
        else:
            if e[r]<e[c]: c=r
            elif e[r]>=e[c]+6: break
        r-=1
    return None if c is None else (c+1,q+1,float(pk))
_DON={}
def _donor(kind):
    """供体的爆破送气（从闭塞最低点之后到最后一个能听见的帧），归一到最响 5 ms 帧 = 1"""
    if kind not in _DON:
        txt,md=DONOR[kind]; x,_=k.create(txt,voice=V,speed=SPEED,lang='en-us'); x=np.asarray(x,np.float32)
        if _hl.md5(x.tobytes()).hexdigest()[:12]!=md: raise SystemExit(f'【停止】供体的合成变了（A21）：{txt}')
        F_=int(0.005*SR); e=_env5(x); pf=int(np.where(e>=AUD_DB)[0][-1])+1; z=_release(e,pf)
        if z is None: raise SystemExit(f'【停止】供体里找不到除阻（A21）：{txt}')
        seg=x[z[0]*F_:z[1]*F_]; m_=len(seg)//F_
        _DON[kind]=seg/np.sqrt(np.mean(seg[:m_*F_].reshape(m_,F_)**2,axis=1)).max()
    return _DON[kind]
def _graft(w,items,label):
    """w 里每一处（秒，供体种类）起换成供体的爆破送气（两头各 2 ms 淡入淡出），响度 = 本句最响 5 ms 帧 GRAFT_DB。
    守门：换掉的那一段原来不能有 ≥-30 dB 的帧（只能是弱除阻和停顿里的静音，不能碰到词）；紧挨着的前 5 ms 必须是闭塞（<-40 dB）。"""
    F_=int(0.005*SR); e=_env5(w); rr=np.sqrt(np.mean(w[:len(e)*F_].reshape(len(e),F_)**2,axis=1)).max(); w=w.copy()
    lv=lambda x:20*np.log10(np.sqrt(np.mean(x**2))/(rr+1e-12)+1e-12) if len(x) else -240.0
    for g,(sec,kind) in items.items():
        d=_donor(kind); p=int(round(float(sec)*SR)); n=len(d)
        if p+n>len(w): w=np.concatenate([w,np.zeros(p+n-len(w),np.float32)])
        seg=w[p:p+n]; m_=n//F_
        if p<F_ or max(lv(seg[i*F_:(i+1)*F_]) for i in range(m_))>=-30 or lv(w[p-F_:p])>=-40:
            raise SystemExit(f'【停止】词尾除阻的位置不对（换掉的部分有词的声音，或前面不是闭塞）（A21）：{label[:60]} {g} {sec}')
        h=int(0.002*SR); r=np.ones(n,np.float32); r[:h]=np.linspace(0,1,h); r[-h:]=np.linspace(1,0,h)
        w[p:p+n]=(d*rr*10**(GRAFT_DB/20)).astype(np.float32)*r          # 整段换掉（两头 2 ms 从零淡入淡出；原来这里只有闭塞和停顿里的静音，不与原声混）
    return w
def _keep_tail(raw,w,head):
    """A21：clean_tail 的句尾（最后一个比峰值低 48 dB 的 10 ms 帧往后 80 ms，最后 50 ms 淡出）会剪掉、压低听得见的词尾（06 intelligent. 的 /t/）。
    原始合成里，从 w 淡出开始处往后、与前面的声音相隔不到 150 ms 的能听见的帧（≥-55 dB，基准本句最响 5 ms 帧）都是词的一部分
    （词尾塞音的闭塞最长 150 ms：01 effect. 的闭塞 110 ms 后才除阻）：w 接长到最后一个这样的帧，再加 5 ms（听不见）在这 5 ms 里淡出。
    隔着 ≥150 ms 的（换气声等）不接。淡出段里没有能听见的帧的句子，w 不变。"""
    F_=int(0.005*SR); x=np.asarray(raw,np.float32); m=len(x)//F_
    e=20*np.log10(np.sqrt(np.mean(x[:m*F_].reshape(m,F_)**2,axis=1))/(np.sqrt(np.mean(x[:m*F_].reshape(m,F_)**2,axis=1)).max()+1e-12)+1e-12)
    fs=(head+len(w)-int(0.05*SR))//F_                      # w 淡出开始处（raw 的帧号）
    au=[f for f in range(fs,m) if e[f]>=AUD_DB]
    if not au: return w
    last=None; prev=max([f for f in range(max(0,fs-30),fs) if e[f]>=AUD_DB],default=fs)
    for f in au:
        if f-prev>30: break
        last=prev=f
    if last is None: return w
    keep=head+len(w)-int(0.05*SR); end=(last+2)*F_
    if end<=head+len(w)-int(0.05*SR): return w
    out=np.concatenate([w[:len(w)-int(0.05*SR)],x[keep:end],np.zeros(max(0,end-len(x)),np.float32)]).astype(np.float32)   # 原始合成在这里就结束了的补零（02 S12）
    out[-F_:]*=np.linspace(1,0,F_)**2
    return out
def _ending_parts(sent,e):
    """结尾句的两遍合成与接点；接点两侧各 10 ms 必须低于 -55 dB（只在听不见的静音里接），否则停"""
    rF,_=k.create(spoken(sent),voice=V,speed=float(e['前段语速']),lang='en-us'); rS,_=k.create(spoken(sent),voice=V,speed=float(e['最后一段语速']),lang='en-us')
    rF=np.asarray(rF,np.float32); rS=np.asarray(rS,np.float32); mF,mS=int(e['接点'][0]),int(e['接点'][1]); F_=int(0.005*SR)
    for r_,m_,nm_ in ((rF,mF,'前段'),(rS,mS,'最后一段')):
        e_=_env5(r_); seg_=e_[max(0,(m_-int(0.01*SR))//F_):(m_+int(0.01*SR))//F_+1]
        if not len(seg_) or seg_.max()>=-55: raise SystemExit(f'【停止】结尾句的接点不在静音里（{nm_}，样本 {m_}，两侧 10 ms 最响 {seg_.max() if len(seg_) else 0:.1f} dB）：{sent[:60]}')
    return rF,rS,mF,mS
def _ending_toks(sent,e):
    """结尾句每个音的时刻（接起来的声音里的秒）：接点前取前段那遍的，接点后取最后一段那遍的（平移过来）"""
    import types as _ty
    if '整句语速' in e:                                                # 没有句中标点的结尾句：整句一个较慢的语速，一次合成
        r_,_=k.create(spoken(sent),voice=V,speed=float(e['整句语速']),lang='en-us')
        tb_,_,ts_=KT.create_timed(spoken(sent),voice=V,speed=float(e['整句语速']),lang='en-us',clause_pause=0,sentence_pause=0); sc_=len(r_)/len(tb_)
        return [_ty.SimpleNamespace(phoneme=t_.phoneme,start=t_.start*sc_,end=t_.end*sc_) for t_ in ts_]
    rF_,rS_,mF_,mS_=_ending_parts(sent,e); toks=[]
    for sp_,r_,m_,first_ in ((float(e['前段语速']),rF_,mF_,True),(float(e['最后一段语速']),rS_,mS_,False)):
        tb_,_,ts_=KT.create_timed(spoken(sent),voice=V,speed=sp_,lang='en-us',clause_pause=0,sentence_pause=0); sc_=len(r_)/len(tb_)
        sh_=0 if first_ else mS_-mF_
        for t_ in ts_:
            if (t_.start*sc_*SR<m_)==first_: toks.append(_ty.SimpleNamespace(phoneme=t_.phoneme,start=(t_.start*sc_*SR-sh_)/SR,end=(t_.end*sc_*SR-sh_)/SR))
    return toks
def _ending_raw(sent,e):
    if '整句语速' in e:                                                # 没有句中标点的结尾句：整句一个较慢的语速
        r_,_=k.create(spoken(sent),voice=V,speed=float(e['整句语速']),lang='en-us'); return np.asarray(r_,np.float32)
    rF,rS,mF,mS=_ending_parts(sent,e); return np.concatenate([rF[:mF],rS[mS:]])
# A27 结尾句放慢不许丢音（2026-10-10 02 结尾句整句 0.80 倍速时，perseveres 词尾的 /z/ 没了，读成“a child persevere depends”；
# 原速 0.95 时 /z/ 清楚）：结尾句的每一个 /s z ʃ ʒ/，在原速那遍里清楚（这个音前后 80 ms 内，5 ms 帧 4 kHz 以上能量占比 ≥0.5、电平 >-40 dB），
# 在结尾句那遍里也必须清楚，否则程序停下（换一个保得住这个音的语速，写进 结尾句 并说明）。
def _sib_strength(r_,toks_):
    r_=np.asarray(r_,np.float32); F_=int(0.005*SR); W_=int(0.01*SR); n_=len(r_)//F_
    rms_=np.sqrt(np.mean(r_[:n_*F_].reshape(n_,F_)**2,axis=1)); lv_=20*np.log10(rms_/(rms_.max()+1e-12)+1e-9)
    f_=np.fft.rfftfreq(W_,1/SR); hw_=np.hanning(W_); out=[]
    for t_ in toks_:
        if t_.phoneme in 'szʃʒ':
            best=0.0
            for i_ in range(max(1,int((t_.start-0.08)*SR)//F_),min(n_,int((t_.end+0.08)*SR)//F_+1)):
                x_=r_[i_*F_-60:i_*F_-60+W_]
                if len(x_)<W_ or lv_[i_]<=-40: continue
                X_=np.abs(np.fft.rfft(x_*hw_))**2; best=max(best,float(X_[f_>4000].sum()/(X_.sum()+1e-20)))
            out.append((t_.phoneme,round(t_.start,2),best))
    return out
def _ending_sib_guard(sent,e,raw_e,toks_e):
    import types as _ty
    r0_,_=k.create(spoken(sent),voice=V,speed=SPEED,lang='en-us')
    tb_,_,ts_=KT.create_timed(spoken(sent),voice=V,speed=SPEED,lang='en-us',clause_pause=0,sentence_pause=0); sc_=len(r0_)/len(tb_)
    a_=_sib_strength(r0_,[_ty.SimpleNamespace(phoneme=t_.phoneme,start=t_.start*sc_,end=t_.end*sc_) for t_ in ts_]); b_=_sib_strength(raw_e,toks_e)
    if len(a_)!=len(b_): raise SystemExit(f'【停止】结尾句的擦音个数对不上（A27，原速 {len(a_)} 个、结尾句 {len(b_)} 个）：{sent[:60]}')
    lost=[(x_,y_) for x_,y_ in zip(a_,b_) if x_[2]>=0.5 and y_[2]<0.5]
    if lost: raise SystemExit(f'【停止】结尾句放慢后丢了擦音（A27）：'+'；'.join(f'/{x_[0]}/ 原速 {x_[1]}s 强度 {x_[2]:.2f} → 结尾句 {y_[1]}s 强度 {y_[2]:.2f}' for x_,y_ in lost)+f'。换一个保得住这个音的语速：{sent[:60]}')
def sentence_audio(sent,pieces,gaps):
    """整句一次合成（原模型，声音不变）。标点位置用带时长输出的同版模型精确定位（A9）；
    在标点处只删除"真正无声"的部分（A10：绝不删词尾的 s/f/z 等弱音），再补静音，使实际听到的停顿 = 标准时长。"""
    E_=ENDING.get(sent)
    if E_:                                                            # 结尾句：两遍合成接起来，最后一段前的停顿用结尾的长度
        raw=_ending_raw(sent,E_); gaps=list(gaps)
        if gaps and '最后一段前停顿' in E_: gaps[-1]=float(E_['最后一段前停顿'])
    else: raw,_=k.create(spoken(sent),voice=V,speed=SPEED,lang='en-us')
    w=clean_tail(raw)
    w=_keep_tail(raw,w,_head_offset(raw,w))
    if sent in NONVOICE: w=_nonvoice(w,NONVOICE[sent],sent)
    if sent in GRAFT: w=_graft(w,GRAFT[sent],sent)
    if E_: toks=_ending_toks(sent,E_); scale=1.0                         # 每个音的时刻（接起来的声音里的秒）
    if E_: _ending_sib_guard(sent,E_,raw,toks)                         # A27 结尾句放慢不许丢音
    else:
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
            # A25（2026-10-10，07 S16 放慢后“Inky-s”）：下一个词以 s/z/ʃ 开头时，切口必须在这个擦音之前——
            # 切口前 30 ms 的高频（>4 kHz）占比：元音约 0.1，/s/ 约 0.8；超过 0.4 说明 s 被留在了前一个词上
            if nxt.phoneme in 'szʃ' and prv.phoneme not in 'szʃʒfθvð':
                seg_=w[max(0,ca-int(0.03*SR)):ca]; sp_=np.abs(np.fft.rfft(seg_*np.hanning(len(seg_))))**2; fq_=np.fft.rfftfreq(len(seg_),1/SR)
                if len(seg_) and np.sqrt(sp_[fq_>4000].sum()/(sp_.sum()+1e-20))>0.4:
                    raise SystemExit(f'【停止】连读处的停顿插在了下一个词开头的 {nxt.phoneme} 后面，{nxt.phoneme} 被留在前一个词上（A25）：{sent[:60]} 第{gi+1}个标点')
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
                    if r0*F<=cx<=r1*F and e[cx//F-1]<PAUSE_DB: ca=cb=cx
                    else:
                        # A28（2026-10-10，04 S17 结尾句 learned, it：程序选中的“短停顿”其实是下一个词 it 的 /t/ 闭塞，停顿插进了 it 里，
                        # 听成 learned it…… seems）：人工用实际声音核实的插入点不在程序选中的短停顿里时，说明程序选错了词缝——
                        # 按人工核实的点插（两词连读、只插不删），守门条件与连读处的人工插入点相同（A15：在该标点附近；是低谷或已很轻）
                        f_=cx//F
                        if not (pe-60<=f_<=ns+20) or (e[f_]>min(e[max(0,f_-2):f_+3]) and e[f_]>-24):
                            raise SystemExit(f'【停止】人工核实的插入点不在这一段短停顿里，也不在该标点附近的低谷（A15/A19/A28）：{sent[:60]} 第{gi+1}个标点')
                        if nxt.phoneme in 'szʃ' and prv.phoneme not in 'szʃʒfθvð':   # A25 同样把关
                            seg_=w[max(0,cx-int(0.03*SR)):cx]; sp_=np.abs(np.fft.rfft(seg_*np.hanning(len(seg_))))**2; fq_=np.fft.rfftfreq(len(seg_),1/SR)
                            if len(seg_) and np.sqrt(sp_[fq_>4000].sum()/(sp_.sum()+1e-20))>0.4:
                                raise SystemExit(f'【停止】连读处的停顿插在了下一个词开头的 {nxt.phoneme} 后面（A25）：{sent[:60]} 第{gi+1}个标点')
                        ca=cb=cx; keep=0.0; r0=r1=None
        dv=DEL_AT.get(sent,{}).get(gi+1)
        if dv is not None:
            rr=np.sqrt(np.mean(w[:len(e)*F].reshape(len(e),F)**2,axis=1)).max()
            lv=lambda x:20*np.log10(np.sqrt(np.mean(x**2))/(rr+1e-12)+1e-9)   # 与 _env5 同一基准
        if dv is not None:   # A19：用实际声音核实过的删除区间
            ca,cb=int(round(float(dv[0])*SR)),int(round(float(dv[1])*SR))
            gv=GRAFT.get(sent,{}).get(str(gi+1))
            if gv is not None:                                        # A21：移植的除阻不能被删——删除从移植段结束处开始（只少删、不多删）
                ge=int(round(float(gv[0])*SR))+len(_donor(gv[1]))
                if ge>=cb: raise SystemExit(f'【停止】移植的除阻伸进了下一个词前面（A21）：{sent[:60]} 第{gi+1}个标点')
                ca=max(ca,ge)
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
    # A22（用户 2026-10-09：“一定要过渡，非常自然，不要整的跟个机器人说的一样”）：说话人连读、只能在声音还响的地方插停顿时
    # （插入点电平 ≥ -45 dB，如 07 Inky, | somewhere），前一个词用 XF_OUT 秒余弦渐弱收尾、后一个词用 XF_IN 秒渐强起音，像真人说完一个词声音自然落下，
    # 不再在声音最响处一刀切断。
    XF_OUT=float(os.environ.get('XF_OUT','0.06')); XF_IN=float(os.environ.get('XF_IN','0.015'))
    fades_=[]
    if XF_OUT>0:
        w=w.copy()
        for ca_,cb_,_ in cuts:
            if cb_==ca_ and 20*np.log10(np.sqrt(np.mean(w[max(0,ca_-F):ca_]**2))/(np.sqrt(np.mean(w[:len(e)*F].reshape(len(e),F)**2,axis=1)).max()+1e-12)+1e-12)>=-45:
                no_=int(XF_OUT*SR); ni_=int(XF_IN*SR)
                w[ca_-no_:ca_]*=(0.5+0.5*np.cos(np.linspace(0,np.pi,no_))).astype(np.float32)
                w[ca_:ca_+ni_]*=(0.5-0.5*np.cos(np.linspace(0,np.pi,ni_))).astype(np.float32)
                fades_.append((ca_-no_,ca_,ca_+ni_))
        hd_=_head_offset(raw,w); fades_=[(a_+hd_,c_+hd_,b_+hd_) for a_,c_,b_ in fades_]   # 淡出起点、切点、淡入终点（原始合成里的样本位置；独立复核在标准答案同一位置做同样的淡入淡出）
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
    gts=[]
    for g_,(sec_,kind_) in GRAFT.get(sent,{}).items():                 # A21：移植段在这一句成片里的时刻（纯人声核对据此认出它，不当杂音）
        p_=int(round(float(sec_)*SR)); n_=len(_donor(kind_))
        for a0,b0,t0,rm in segs:
            if a0<=p_<b0:
                q_=p_-a0; q_-=sum(min(q_,y)-x for x,y in rm if x<q_); gts.append((g_,t0+q_/SR,t0+(q_+n_)/SR)); break
        else: raise SystemExit(f'【停止】移植段不在保留的声音里（A21）：{sent[:60]} {g_}')
    LAST.clear(); LAST.update(toks=toks,scale=scale,head=_head_offset(raw,w),segs=segs,total=len(pur)/SR,cuts=cuts,grafts=gts,gaps=list(gaps),fades=fades_)
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
    if '标题::'+title in GRAFT: w=_graft(w,GRAFT['标题::'+title],'标题 '+title)
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
    prev_para=None; graft_times=[]; fade_rec={}
    if '标题::'+d['title_en'] in GRAFT: raise SystemExit('【停止】标题的词尾除阻还没有接到 纯人声核对 的时刻表（A21），先补上')
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
        t_at=sum(len(x_) for x_ in audio)/SR+lead
        if LAST.get('fades'): fade_rec[f'S{si+1}']=[list(map(int,f_)) for f_ in LAST['fades']]
        graft_times+=[{'句':f'S{si+1}','位置':('句末' if g_=='句末' else f'第{g_}个标点'),'开始':round(t_at+t0_,4),'结束':round(t_at+t1_,4)} for g_,t0_,t1_ in LAST['grafts']]
        audio+=[sil(lead),a,sil(P_HOLD)]
        for ci in range(len(ch)):
            dur=starts[ci+1]-starts[ci]+(lead if ci==0 else 0)+(P_HOLD if ci==len(ch)-1 else 0)
            tl.append(((si,ci),dur))
    END=2.0-P_HOLD; audio.append(sil(END)); tl[-1]=(tl[-1][0],tl[-1][1]+END)  # 片尾：读完后共停 2 秒
    A=np.concatenate(audio); A=A/np.abs(A).max()*0.89
    json.dump(graft_times,open(f'{work}/词尾除阻.json','w'),ensure_ascii=False,indent=1)   # A21：移植段在 a.wav 里的时刻
    json.dump(fade_rec,open(f'{work}/淡入淡出.json','w'),ensure_ascii=False,indent=1)   # A22：连读处插停顿的淡出/淡入在原始合成里的样本位置（独立复核用）
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
    orph=[(si+1,b,w_) for si,s in enumerate(d['sentences']) for b,w_ in R.orphan_lines([[tuple(p) for p in c['align']] for c in s['chunks']],colors,[c.get('note') for c in s['chunks']],min(sizes[si],100*R.S))]
    if orph: raise SystemExit('【停止】整组折行后最后一行只剩一个词（L3）：'+'；'.join(f'S{a} 第{b}块末行“{c_}”' for a,b,c_ in orph)+'。这一组加 {{=}} 保持一行（字号自动缩到放得下），或经用户同意改分组')
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
