#!/usr/bin/env python3
"""机器复听（音频保障第 4 层，2026-10-25 主对话：“像用户一样从头听一遍”）：离线语音识别（sherpa-onnx + whisper small.en，
模型从 GitHub release 下载，校验码见 音频体检基准.json 旁的 机器复听模型.json）把成片每一句转成文字，和脚本逐词比。
比的是读音不是拼写：两边都用配音模型同一个注音程序（espeak，kokoro_onnx 的 Tokenizer）转成音标，同音词（crew's / cruise）不算错；
数字两边都去掉逗号和序数词尾（13th / 13）。读音对不上的词（漏词、多词、读错、吞音）列出来。
用法（视频工作目录）：python3 机器复听.py NN [成片或 a.wav]；--自检 NN（把一句的一个词换成别的词的声音，必须报出这个词；原样不误报）
"""
import os, sys, re, json, difflib, numpy as np
try: import soundfile as sf; from scipy.signal import resample_poly   # 重依赖只有真听声音时才要；--比较自检 在只有标准库 + numpy 的容器（主会话）也能跑
except ImportError: sf = resample_poly = None
T = os.path.dirname(os.path.abspath(__file__)); V = os.path.dirname(T)
MD = os.path.expanduser('~/asr/sherpa-onnx-whisper-small.en')   # 准备机器.sh 下载到这里
PD = os.path.expanduser('~/asr/sherpa-onnx-nemo-parakeet-tdt-0.6b-v2-int8')
路名 = ('small.en', 'parakeet')   # 2026-10-26 第二阶段 2（主会话定：查全优先）：任一路报就报，每一路各自打印；少一路就停，不许悄悄退回单识别器

def 识别器():
    """每一路一个离线识别器 {名: 识别器}。small.en（whisper，带语言模型补全）+ parakeet（NeMo TDT 0.6B int8）：
    注入实测（改门_音频上GitHub.md 第二阶段）任一报就报，漏读、词中截断、句尾截断、咔哒、削波每类查全都比 small.en 单用高"""
    p = lambda d, x: os.path.join(d, x)
    for d, f, u in ((MD, 'small.en-encoder.int8.onnx', 'sherpa-onnx-whisper-small.en'), (PD, 'encoder.int8.onnx', 'sherpa-onnx-nemo-parakeet-tdt-0.6b-v2-int8')):
        if not os.path.exists(p(d, f)): raise SystemExit(f'【停止】没有识别模型 {d}：bash 准备机器.sh 会下载（GitHub release k2-fsa/sherpa-onnx asr-models/{u}）；机器复听每一路都要有，不许少一路')
    import sherpa_onnx   # 先查模型在不在（没有模型就停，不先要求装好识别程序）
    return {'small.en': sherpa_onnx.OfflineRecognizer.from_whisper(encoder=p(MD, 'small.en-encoder.int8.onnx'), decoder=p(MD, 'small.en-decoder.int8.onnx'), tokens=p(MD, 'small.en-tokens.txt'), num_threads=4),
            'parakeet': sherpa_onnx.OfflineRecognizer.from_transducer(encoder=p(PD, 'encoder.int8.onnx'), decoder=p(PD, 'decoder.int8.onnx'), joiner=p(PD, 'joiner.int8.onnx'), tokens=p(PD, 'tokens.txt'), model_type='nemo_transducer', num_threads=4)}

def 转写(rec, x16):
    s = rec.create_stream(); s.accept_waveform(16000, x16); rec.decode_stream(s); return s.result.text.strip()
def 各路(recs, ref, x16):
    """每一路听一遍：(听到的文字 {名: 文字}, 对不上的 [(脚本词, 听到词〔路名〕)])，任一路报就报"""
    t = {n: 转写(r, x16) for n, r in recs.items()}
    return t, [(a, f'{b}〔{n}〕') for n in recs for a, b in 比(ref, t[n])]

_tk = None
_自检读音 = {"crew's": 'kɹuːz', 'cruise': 'kɹuːz', 'organised': 'ɔɹɡənaɪzd', 'organized': 'ɔɹɡənaɪzd', 'eleven': 'ɪlɛvən', '11': 'ɪlɛvən', 'walkie': 'wɔki', 'scorchy': 'skɔɹtʃi', 'scorchie': 'skɔɹki', 'fifty': 'fɪfti', '50': 'fɪfti'}   # espeak 的读音（kokoro 注音实测）
def 音标(w):
    global _tk
    if _tk is None:
        try: from kokoro_onnx.tokenizer import Tokenizer; _tk = Tokenizer()
        except ImportError: _tk = False
    if _tk is False:   # 没有注音程序的容器（主会话）：只为 --比较自检 用内置的几组读音，真听声音一定在有配音模型的工作目录
        if sf is not None: raise SystemExit('【停止】有声音程序却没有 kokoro_onnx 注音程序：机器复听不能按读音比')
        return _自检读音.get(w, w)
    return 归一音标(_tk.phonemize(w, 'en-us'))   # 注音变体（eleven/11、organised/organized）归一

_月 = 'january|february|march|april|may|june|july|august|september|october|november|december'
def 词(t):
    t = re.sub(r'(?<=\d),(?=\d{3})', '', t.lower())
    t = re.sub(rf'\b([1-9]|[12]\d|3[01]) ({_月})\b', r'the \1 of \2', t)   # 出片程序把 6 January 读成 the sixth of January（make_video spoken）
    t = re.sub(r'(\d+)(st|nd|rd|th)\b', r'\1', t)
    t = re.sub(r'(\d)\s*%', r'\1 per cent', t); t = re.sub(r'\bpercent\b', 'per cent', t)   # G56（27 S14）：识别器写 40%，脚本 per cent
    return re.findall(r"[^\W_]+(?:'[^\W_]+)?", t)   # 带变音符的专名（Ötztal）整词保留

_核 = None
def 已核实(专名=False):
    global _核
    if _核 is None:
        # 对权威来源查过、读音核对把关的：正确、改正后正确（20 Ötztal）、可接受、配音读错已写进读音改正表
        ok_ = lambda p_: str(p_).startswith(('正确', '改正后正确', '可接受')) or '已写进 读音改正' in str(p_)
        j = {k: v for k, v in json.load(open(f'{T}/发音词典/已核实读音.json')).items() if ok_(v.get('判定'))}
        _核 = ({k.lower() for k in j}, {k for k in j if k[:1].isupper()})   # 专名一侧按原样大小写（SAT 是专名，sat 不是）
    return _核[1 if 专名 else 0]
_改 = None
def 改正读音():
    """读音改正.json（与出片程序 phonemes_of 同一份表）：配音实际读的是改正后的读音。键小写 → 归一后的音标；连字符复合词键去掉连字符"""
    global _改
    if _改 is None:
        _改 = {k.lower().replace('-', ''): 归一音标(v['读音']) for k, v in json.load(open(f'{T}/发音词典/读音改正.json')).items() if v.get('读音')}
    return _改
def 复合词(): return [k for k in json.load(open(f'{T}/发音词典/读音改正.json')) if '-' in k]
def 归一音标(x):
    x = re.sub(r'[ˈˌː\s]', '', x)
    return x.translate(str.maketrans({'ᵻ': 'ɪ', 'ɐ': 'ə', 'ɾ': 't'})).replace('ɚ', 'əɹ')
def 拼写归一(t):
    """英美拼写变体归成一种（kilometres/kilometers、colour/color、organise/organize、analyse/analyze、catalogue/catalog、travelled/traveled、defence/defense）"""
    t = re.sub(r'(?<=[a-z])tre(s?)\b', r'ter\1', t); t = re.sub(r'(?<=[a-z])our(s|ed|ing|ful|ite|ites)?\b', r'or\1', t)
    t = re.sub(r'(?<=[a-z])is(e|es|ed|ing|ation|ations)\b', r'iz\1', t); t = re.sub(r'(?<=[a-z])ys(e|es|ed|ing)\b', r'yz\1', t)
    t = re.sub(r'(?<=[a-z])ogue(s?)\b', r'og\1', t); t = re.sub(r'(?<=[aeiou])ll(ed|ing|er|ers)\b', r'l\1', t); t = re.sub(r'(?<=[a-z])ence\b', 'ense', t)
    return t
_币 = {'£': ('pounds', 'pound'), '$': ('dollars', 'dollar'), '€': ('euros', 'euro')}
def 比(ref, hyp):
    """读音对不上的 [(脚本里的词, 听到的词)]。听到的一侧有 £/$/€ + 数字（识别器把钱数写成符号，22 S8 £1,000、23 S18 £50 note）：
    写成 数字 + pounds 或 pound 两种，取对不上少的那种（符号本身不分单复数）"""
    m = re.search(r'([£$€])\s*(\d[\d,]*(?:\.\d+)?)', hyp)
    if not m: return _比(ref, hyp)
    vs = [_比(ref, re.sub(r'([£$€])\s*(\d[\d,]*(?:\.\d+)?)', lambda m_: f'{m_.group(2)} {_币[m_.group(1)][i]}', hyp)) for i in (0, 1)]
    return min(vs, key=len)
def _比(ref, hyp):
    改 = 改正读音()
    # 读音改正表里的连字符复合词（Walkie-Scorchie）在脚本一侧当一个词，按改正后的读音比
    for k in 复合词():
        ref = re.sub(r'(?i)(?<![^\W_])' + re.escape(k) + r'(?![^\W_])', lambda m_: m_.group(0).replace('-', ''), ref)
    R, H = 词(ref), 词(hyp); pr = [音标(w) for w in R]; ph = [音标(w) for w in H]
    专名 = {w.lower() for w in re.findall(r"(?<![.!?]\s)(?<!^)\b[A-Z][A-Za-z]+(?:'[a-z]+)?", ref)}
    核专名 = {w.lower() for w in re.findall(r"[^\W_]+", ref) if w in 已核实(专名=True)}   # 脚本里原样大写、且已核实表里就是这样大写的词（句首也算）
    sm = difflib.SequenceMatcher(None, pr, ph, autojunk=False); out = []
    for op, a1, a2, b1, b2 in sm.get_opcodes():
        if op == 'equal': continue
        if 拼写归一(' '.join(R[a1:a2])) == 拼写归一(' '.join(H[b1:b2])) and R[a1:a2]: continue   # G56（27 S4 kilometres/kilometers）：英美拼写变体是同一个词，两种读法词典都收
        if ''.join(pr[a1:a2]) == ''.join(ph[b1:b2]): continue   # 连写/拆写（switches / switch is 读音一样不算；every one / everyone）
        if R[a1:a2] and ''.join(R[a1:a2]) == ''.join(H[b1:b2]): continue   # 拼写连起来相同（脚本 walkiescorchie / 听到 walkie scorchie）
        if R[a1:a2] and ''.join(改.get(w, pr[a1 + j]) for j, w in enumerate(R[a1:a2])) == ''.join(ph[b1:b2]): continue   # 读音改正表：配音读的是改正后的读音（22 S11 Walkie-Scorchie 听成 scorchy）
        if op == 'replace' and all(w in 核专名 or w in 已核实() and w in 专名 for w in R[a1:a2]): continue   # 已核实表里大写开头的键（专名），句首也豁免（20 S17 Ötzi）   # A23 已对权威来源查过读音（读音核对 出片前把关）的专名（脚本里大写）：识别器不认识、听成别的不算；漏掉、多出照报
        out.append((' '.join(R[a1:a2]) or '（多出）', ' '.join(H[b1:b2]) or '（没听到）'))
    return out

def 听(no, src=None, rec=None, 改=None):
    d = json.load(open(f'scripts/{no}.json')); seg = json.load(open(f'work_{no}/分段.json'))
    a, sr = sf.read(src or f'work_{no}/a.wav'); a = a if a.ndim == 1 else a.mean(axis=1)
    if 改: a = 改(a, sr, seg)
    rec = rec or 识别器(); res = []
    for i, (k, v) in enumerate(seg.items()):
        x = a[int(v[0]['时刻'][0] * sr):int(v[-1]['时刻'][1] * sr)]
        x = resample_poly(x, 16000, sr).astype(np.float32) if sr != 16000 else x.astype(np.float32)
        ref = ' '.join(re.sub(r'\{\{.*?\}\}|\*\*', '', c['en']) for c in d['sentences'][i]['chunks'])
        t, b = 各路(rec, ref, x); res.append((k, t, b))
    return res

def 吞段(v):
    """自检吞掉的那一截：这一句最长一段（停顿隔开）的中间七成，几个词连着没了。
    只吞 0.36 秒，whisper 会靠上下文把短词补回来（27 S9 “near the most” 被补回，自检误判失灵，2026-10-26）"""
    i = max(range(len(v)), key=lambda j: v[j]['时刻'][1] - v[j]['时刻'][0]); t0, t1 = v[i]['时刻']; L = t1 - t0
    return t0 + 0.15 * L, t1 - 0.15 * L

def 自检(no):
    """把某句中间一个词的声音换成静音（模拟吞音/漏词），必须报出；原样报出的不变"""
    rec = 识别器(); r0 = 听(no, rec=rec); bad0 = {k for k, _, b in r0 if b}
    ok = [k for k, _, b in r0 if not b]
    if not ok: return ['自检前提不成立：每一句都已有对不上的词']
    k = ok[len(ok) // 2]
    def 吞(a, sr, seg):
        t0, t1 = 吞段(seg[k]); a = a.copy(); a[int(t0 * sr):int(t1 * sr)] = 0; return a
    r1 = 听(no, rec=rec, 改=吞); bad1 = {k_ for k_, _, b in r1 if b}
    f = []
    for n in rec:
        if not any(y.endswith(f'〔{n}〕') for k_, _, b in r1 if k_ == k for _, y in b): f.append(f'没抓到（{n} 这一路）：{k} 最长一段中间七成声音被吞掉，没报')
    if bad1 - bad0 - {k}: f.append(f'误报：没动的句子也报了 {sorted(bad1 - bad0 - {k})}')
    return f

def 带自检(no):
    """正式复听一遍；再把一句没问题的中间吞掉最长一段的中间七成，只重新识别这一句，必须报出（自检不过 = 核查失灵）"""
    rec = 识别器(); r0 = 听(no, rec=rec); ok = [k for k, _, b in r0 if not b]; f = []
    if ok:
        k = ok[len(ok) // 2]; d = json.load(open(f'scripts/{no}.json')); seg = json.load(open(f'work_{no}/分段.json')); v = seg[k]
        a, sr = sf.read(f'work_{no}/a.wav'); a = a if a.ndim == 1 else a.mean(axis=1)
        t0, t1 = 吞段(v); b0 = v[0]['时刻'][0]
        x = a[int(b0 * sr):int(v[-1]['时刻'][1] * sr)].copy(); x[int((t0 - b0) * sr):int((t1 - b0) * sr)] = 0
        x = resample_poly(x, 16000, sr).astype(np.float32)
        si = list(seg).index(k); ref = ' '.join(re.sub(r'\{\{.*?\}\}|\*\*', '', c['en']) for c in d['sentences'][si]['chunks'])
        t, b = 各路(rec, ref, x)
        for n in rec:   # 每一路都必须各自抓到（任一路失灵 = 自检不过）
            if not any(y.endswith(f'〔{n}〕') for _, y in b): f.append(f'没抓到（{n} 这一路）：{k} 最长一段中间七成声音被吞掉，没报（听到“{t[n]}”）')
    else: f.append('自检前提不成立：每一句都已有对不上的词')
    return r0, f

def 清单(vdir):
    """01–24 已定稿只列不改：成片按 ≥0.7 秒静音切句（片头标题是第 0 段），每句识别后和脚本比"""
    import glob; sys.path.insert(0, T); import 音频体检 as Q
    rec = 识别器(); print('# 机器复听清单（01–24 已定稿：只列不改；读音对不上的词，含识别器本身听错的，交用户看）\n'); n = 0
    for f in sorted(glob.glob(os.path.join(vdir, '[0-2][0-9].mp4'))):
        no = os.path.basename(f)[:2]
        if int(no) >= 25: continue
        a = Q.读(f); seg = Q.句段(a); txt = Q.文本(no)
        if not txt or len(txt) != len(seg): print(f'- **{no}**：句数对不上（声音 {len(seg)} 段、脚本 {len(txt or [])} 句），没比'); continue
        bad = []
        for i, ((s0, e0), ref) in enumerate(zip(seg[1:], txt[1:]), 1):
            x = resample_poly(a[s0:e0], 1, 3).astype(np.float32); _, b = 各路(rec, ref, x)
            if b: bad.append(f'S{i}：' + '；'.join(f'脚本“{x_}” 听到“{y_}”' for x_, y_ in b))
        n += len(bad); print(f'- **{no}**：{len(bad)} 句' + ''.join(f'\n  - {x}' for x in bad), flush=True)
    print(f'\n共 {n} 句。要改哪篇，用户说了再改（改了要重出 4K、过交付核查、重新归档，G9）。')

def 比较自检():
    """不用识别模型：比() 的归一规则。序数、同音、注音变体、日期展开不报；少一个词、读错一个词必报"""
    f = []
    for r_, h_ in (('some 3,000 kilometres away', 'some 3000 kilometers away'), ('about 40 per cent less', 'about 40% less'), ('the colour of', 'the color of'),
                   ('On April 13th', 'On April 13'), ("the crew's capsule", 'the cruise capsule'), ('organised eleven', 'organized 11'), ('On 6 January', 'On the 6 of January'), ('some 200,000 miles', 'some 200000 miles')):
        if 比(r_, h_): f.append(f'误报：“{r_}”听成“{h_}”读音一样，却报了 {比(r_, h_)}')
    if 比('He met Windhandel there', 'He met Vinthehandel there') and 'windhandel' in 已核实(): f.append('误报：已核实读音的专名被识别器听错也报了')
    for r_, h_ in (('Ötzi was found in 1991', 'Erzi was found in 1991'), ('It sold as the Walkie-Scorchie in London', 'It sold as the walkie scorchy in London'),
                   ('a fine of 1,000 pounds each', 'a fine of £1,000 each'), ('a fifty-pound note', 'a £50 note'), ('a trek in the Ötztal Alps', 'a trek in the Erzdal Alps')):   # 第二阶段 2 通用规则（20 S17、22 S11、22 S8、23 S18）
        if 比(r_, h_): f.append(f'误报：“{r_}”听成“{h_}”（句首已核实专名 / 读音改正表 / 货币符号），却报了 {比(r_, h_)}')
    for r_, h_ in (('He sat there', 'He set there'), ('a fine of 1,000 pounds each', 'a fine of £1,000'), ('Ötzi was found in 1991', 'was found in 1991')):   # 小写 sat 不因已核实表里有 SAT 豁免；货币归一后漏词、专名漏掉照报
        if not 比(r_, h_): f.append(f'没抓到：“{r_}”听成“{h_}”')
    for r_, h_ in (('the cat sat on the mat', 'the cat on the mat'), ('the cabbies waited', 'the cabins waited'), ('He sat there', 'He set there')):
        if not 比(r_, h_): f.append(f'没抓到：“{r_}”听成“{h_}”')
    global MD, PD, _tk, sf   # 前提门（G79 门变异：以前只有真听声音的主流程走得到）：没有识别模型、有声音程序却没有注音程序，都必须停
    o_ = (MD, PD, _tk, sf)
    try:
        MD = PD = '/不存在的识别模型目录'
        try: 识别器(); f.append('没抓到：没有识别模型也开听')
        except SystemExit as x_:
            if '没有识别模型' not in str(x_): f.append(f'停错了：{x_}')
        _tk, sf = False, object()
        try: 音标('cruise'); f.append('没抓到：有声音程序却没有 kokoro_onnx 注音程序，也按内置读音比')
        except SystemExit as x_:
            if '没有 kokoro_onnx' not in str(x_): f.append(f'停错了：{x_}')
    finally: MD, PD, _tk, sf = o_
    return f

def 分类(md):
    """把 --清单 的结果分成两类（不重跑识别）：
    识别器听不准：脚本里大写的专名；或两边音标只差元音（近音词，配音读音由读音核对把关）。
    疑似真问题：漏词、多词；或脚本的音标 = 听到的音标 + 词尾辅音（词尾 -ed/-s/-t 没听到，可能被切或吞掉）；其余读音差别也算。"""
    vow = set('aeiouæɑɒɔəɛɜɪʊʌyɐᵻɚː')
    sys.path.insert(0, T); import 音频体检 as Q
    out_r, out_q = [], []
    for blk in re.split(r'\n(?=- \*\*\d\d\*\*)', open(md).read()):
        m = re.match(r'- \*\*(\d\d)\*\*', blk)
        if not m: continue
        no = m.group(1); txt = Q.文本(no) or []
        for sm_ in re.finditer(r'  - S(\d+)：(.+)', blk):
            si = int(sm_.group(1)); ref = txt[si] if si < len(txt) else ''
            for x, y in re.findall(r'脚本“([^”]*)” 听到“([^”]*)”', sm_.group(2)):
                y = re.sub(r'〔[^〕]*〕$', '', y)   # 路名（small.en / parakeet）
                bad_ = x != '（多出）' and not all(re.search(rf"(?<![^\W_]){re.escape(w)}(?![^\W_])", ref, re.I) for w in x.split())   # 旧清单按 a–z 切词，Ötztal 成了 tztal
                cap = bad_ or x != '（多出）' and all(re.search(rf"(?<!^)\b{re.escape(w)}\b", ref, re.I) and re.search(rf"\b{re.escape(w[0].upper() + w[1:])}", ref) for w in x.split())
                px = ''.join(音标(w) for w in x.split()) if x != '（多出）' else ''; py = ''.join(音标(w) for w in y.split()) if y != '（没听到）' else ''
                cons = lambda t: ''.join(c for c in t if c not in vow)
                item = f'{no} S{si}：脚本“{x}” 听到“{y}”（音标 /{px}/ → /{py}/）'
                if x == '（多出）' or y == '（没听到）': out_q.append(item + ' —— 漏词或多词'); continue
                if px.startswith(py) and py and cons(px[len(py):]) == px[len(py):]: out_q.append(item + f' —— 词尾少了 /{px[len(py):]}/（可能被切或吞掉）'); continue
                if cap: out_r.append(item + ' —— 专名（脚本里大写），识别器不认识'); continue
                if cons(px) == cons(py): out_r.append(item + ' —— 只差元音，近音词'); continue
                out_q.append(item + ' —— 读音不同')
    return out_q, out_r

if __name__ == '__main__':
    if sys.argv[1:2] == ['--分类']:
        q, r = 分类(sys.argv[2])
        print('# 机器复听清单（01–24 已定稿：只列不改）\n\n由 `机器复听.py --分类` 把 `--清单` 的结果分成两类。用户只需听“疑似真问题”那几句。\n')
        print(f'## 疑似真问题（{len(q)} 处，先听这些）\n'); print('\n'.join('- ' + x for x in q) or '（无）')
        print(f'\n## 识别器听不准（{len(r)} 处）\n'); print('\n'.join('- ' + x for x in r) or '（无）'); sys.exit(0)
    if sys.argv[1:2] == ['--比较自检']:
        e = 比较自检(); print('\n'.join(e) or '机器复听 比较自检通过（序数、同音、注音变体、日期、千分位、%、英美拼写、句首已核实专名、读音改正表、货币符号不报；漏词、读错必报）'); sys.exit(1 if e else 0)
    if sys.argv[1:2] == ['--清单']: 清单(sys.argv[2]); sys.exit(0)
    if sys.argv[1:2] == ['--带自检']:
        r0, f = 带自检(sys.argv[2]); bad = [(k, b) for k, _, b in r0 if b]
        print(('✘ 机器复听 自检：' + '；'.join(f)) if f else f'✔ 机器复听 自检：吞掉一句最长一段的中间七成，{"、".join(路名)} 每一路都报')
        print(f'机器复听 {len(r0)} 句：读音对不上的 {len(bad)} 句')
        for k, b in bad: print(f'  {k}：' + '；'.join(f'脚本“{x}” 听到“{y}”' for x, y in b))
        sys.exit(2 if f else (1 if bad else 0))
    a_ = sys.argv[1:]
    if a_[0] == '--自检':
        e = 自检(a_[1]); print(('✘ ' if e else '✔ ') + '机器复听 自检：' + ('；'.join(e) if e else '吞掉一句最长一段的中间七成必报、别的句子不误报')); sys.exit(1 if e else 0)
    res = 听(a_[0], a_[1] if len(a_) > 1 else None); bad = [(k, b) for k, _, b in res if b]
    print(f'机器复听 {len(res)} 句：读音对不上的 {len(bad)} 句')
    for k, b in bad: print(f'  {k}：' + '；'.join(f'脚本“{x}” 听到“{y}”' for x, y in b))
    sys.exit(1 if bad else 0)
