#!/usr/bin/env python3
"""机器复听（音频保障第 4 层，2026-10-25 主对话：“像用户一样从头听一遍”）：离线语音识别（sherpa-onnx + whisper small.en，
模型从 GitHub release 下载，校验码见 音频体检基准.json 旁的 机器复听模型.json）把成片每一句转成文字，和脚本逐词比。
比的是读音不是拼写：两边都用配音模型同一个注音程序（espeak，kokoro_onnx 的 Tokenizer）转成音标，同音词（crew's / cruise）不算错；
数字两边都去掉逗号和序数词尾（13th / 13）。读音对不上的词（漏词、多词、读错、吞音）列出来。
用法（视频工作目录）：python3 机器复听.py NN [成片或 a.wav]；--自检 NN（把一句的一个词换成别的词的声音，必须报出这个词；原样不误报）
"""
import os, sys, re, json, difflib, numpy as np, soundfile as sf
from scipy.signal import resample_poly
T = os.path.dirname(os.path.abspath(__file__)); V = os.path.dirname(T)
MD = os.path.expanduser('~/asr/sherpa-onnx-whisper-small.en')   # 准备机器.sh 下载到这里

def 识别器():
    import sherpa_onnx
    p = lambda x: os.path.join(MD, x)
    if not os.path.exists(p('small.en-encoder.int8.onnx')): raise SystemExit(f'【停止】没有识别模型 {MD}：bash 准备机器.sh 会下载（GitHub release k2-fsa/sherpa-onnx asr-models/sherpa-onnx-whisper-small.en）')
    return sherpa_onnx.OfflineRecognizer.from_whisper(encoder=p('small.en-encoder.int8.onnx'), decoder=p('small.en-decoder.int8.onnx'), tokens=p('small.en-tokens.txt'), num_threads=4)

_tk = None
def 音标(w):
    global _tk
    if _tk is None:
        from kokoro_onnx.tokenizer import Tokenizer; _tk = Tokenizer()
    x = re.sub(r'[ˈˌː\s]', '', _tk.phonemize(w, 'en-us'))
    return x.translate(str.maketrans({'ᵻ': 'ɪ', 'ɐ': 'ə', 'ɾ': 't'})).replace('ɚ', 'əɹ')   # 注音变体（eleven/11、organised/organized）归一

_月 = 'january|february|march|april|may|june|july|august|september|october|november|december'
def 词(t):
    t = re.sub(r'(?<=\d),(?=\d{3})', '', t.lower())
    t = re.sub(rf'\b([1-9]|[12]\d|3[01]) ({_月})\b', r'the \1 of \2', t)   # 出片程序把 6 January 读成 the sixth of January（make_video spoken）
    t = re.sub(r'(\d+)(st|nd|rd|th)\b', r'\1', t)
    return re.findall(r"[a-z0-9]+(?:'[a-z]+)?", t)

_核 = None
def 已核实():
    global _核
    if _核 is None: _核 = {k.lower() for k, v in json.load(open(f'{T}/发音词典/已核实读音.json')).items() if v.get('判定') == '正确'}
    return _核
def 比(ref, hyp):
    """读音对不上的 [(脚本里的词, 听到的词)]"""
    R, H = 词(ref), 词(hyp); pr = [音标(w) for w in R]; ph = [音标(w) for w in H]
    专名 = {w.lower() for w in re.findall(r"(?<![.!?]\s)(?<!^)\b[A-Z][A-Za-z]+(?:'[a-z]+)?", ref)}
    sm = difflib.SequenceMatcher(None, pr, ph, autojunk=False); out = []
    for op, a1, a2, b1, b2 in sm.get_opcodes():
        if op == 'equal': continue
        if ''.join(pr[a1:a2]) == ''.join(ph[b1:b2]): continue   # 连写/拆写（switches / switch is 读音一样不算；every one / everyone）
        if op == 'replace' and all(w in 已核实() and w in 专名 for w in R[a1:a2]): continue   # A23 已对权威来源查过读音（读音核对 出片前把关）的专名（脚本里大写）：识别器不认识、听成别的不算；漏掉、多出照报
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
        s = rec.create_stream(); s.accept_waveform(16000, x); rec.decode_stream(s)
        ref = ' '.join(re.sub(r'\*\*', '', c['en']) for c in d['sentences'][i]['chunks'])
        res.append((k, s.result.text.strip(), 比(ref, s.result.text)))
    return res

def 自检(no):
    """把某句中间一个词的声音换成静音（模拟吞音/漏词），必须报出；原样报出的不变"""
    rec = 识别器(); r0 = 听(no, rec=rec); bad0 = {k for k, _, b in r0 if b}
    ok = [k for k, _, b in r0 if not b]
    if not ok: return ['自检前提不成立：每一句都已有对不上的词']
    k = ok[len(ok) // 2]
    def 吞(a, sr, seg):
        v = seg[k]; i = max(range(len(v)), key=lambda j: v[j]['时刻'][1] - v[j]['时刻'][0]); t0, t1 = v[i]['时刻']; m = (t0 + t1) / 2
        a = a.copy(); a[int((m - 0.18) * sr):int((m + 0.18) * sr)] = 0; return a
    r1 = 听(no, rec=rec, 改=吞); bad1 = {k_ for k_, _, b in r1 if b}
    f = []
    if k not in bad1: f.append(f'没抓到：{k} 中间 0.36 秒声音被吞掉，机器复听没报')
    if bad1 - bad0 - {k}: f.append(f'误报：没动的句子也报了 {sorted(bad1 - bad0 - {k})}')
    return f

def 带自检(no):
    """正式复听一遍；再把一句没问题的中间吞掉 0.36 秒，只重新识别这一句，必须报出（自检不过 = 核查失灵）"""
    rec = 识别器(); r0 = 听(no, rec=rec); ok = [k for k, _, b in r0 if not b]; f = []
    if ok:
        k = ok[len(ok) // 2]; d = json.load(open(f'scripts/{no}.json')); seg = json.load(open(f'work_{no}/分段.json')); v = seg[k]
        a, sr = sf.read(f'work_{no}/a.wav'); a = a if a.ndim == 1 else a.mean(axis=1)
        i = max(range(len(v)), key=lambda j: v[j]['时刻'][1] - v[j]['时刻'][0]); t0, t1 = v[i]['时刻']; m = (t0 + t1) / 2
        x = a[int(v[0]['时刻'][0] * sr):int(v[-1]['时刻'][1] * sr)].copy(); o = int((m - v[0]['时刻'][0]) * sr); x[o - int(0.18 * sr):o + int(0.18 * sr)] = 0
        x = resample_poly(x, 16000, sr).astype(np.float32); s = rec.create_stream(); s.accept_waveform(16000, x); rec.decode_stream(s)
        si = list(seg).index(k); ref = ' '.join(re.sub(r'\*\*', '', c['en']) for c in d['sentences'][si]['chunks'])
        if not 比(ref, s.result.text): f.append(f'没抓到：{k} 中间 0.36 秒声音被吞掉，机器复听没报')
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
            x = resample_poly(a[s0:e0], 1, 3).astype(np.float32); st = rec.create_stream(); st.accept_waveform(16000, x); rec.decode_stream(st)
            b = 比(ref, st.result.text)
            if b: bad.append(f'S{i}：' + '；'.join(f'脚本“{x_}” 听到“{y_}”' for x_, y_ in b))
        n += len(bad); print(f'- **{no}**：{len(bad)} 句' + ''.join(f'\n  - {x}' for x in bad), flush=True)
    print(f'\n共 {n} 句。要改哪篇，用户说了再改（改了要重出 4K、过交付核查、重新归档，G9）。')

def 比较自检():
    """不用识别模型：比() 的归一规则。序数、同音、注音变体、日期展开不报；少一个词、读错一个词必报"""
    f = []
    for r_, h_ in (('On April 13th', 'On April 13'), ("the crew's capsule", 'the cruise capsule'), ('organised eleven', 'organized 11'), ('On 6 January', 'On the 6 of January'), ('some 200,000 miles', 'some 200000 miles')):
        if 比(r_, h_): f.append(f'误报：“{r_}”听成“{h_}”读音一样，却报了 {比(r_, h_)}')
    if 比('He met Windhandel there', 'He met Vinthehandel there') and 'windhandel' in 已核实(): f.append('误报：已核实读音的专名被识别器听错也报了')
    for r_, h_ in (('the cat sat on the mat', 'the cat on the mat'), ('the cabbies waited', 'the cabins waited'), ('He sat there', 'He set there')):
        if not 比(r_, h_): f.append(f'没抓到：“{r_}”听成“{h_}”')
    return f

if __name__ == '__main__':
    if sys.argv[1:2] == ['--比较自检']:
        e = 比较自检(); print('\n'.join(e) or '机器复听 比较自检通过（序数、同音、注音变体、日期、千分位不报；漏词、读错必报）'); sys.exit(1 if e else 0)
    if sys.argv[1:2] == ['--清单']: 清单(sys.argv[2]); sys.exit(0)
    if sys.argv[1:2] == ['--带自检']:
        r0, f = 带自检(sys.argv[2]); bad = [(k, b) for k, _, b in r0 if b]
        print(('✘ 机器复听 自检：' + '；'.join(f)) if f else '✔ 机器复听 自检：吞掉一句中间 0.36 秒必报')
        print(f'机器复听 {len(r0)} 句：读音对不上的 {len(bad)} 句')
        for k, b in bad: print(f'  {k}：' + '；'.join(f'脚本“{x}” 听到“{y}”' for x, y in b))
        sys.exit(2 if f else (1 if bad else 0))
    a_ = sys.argv[1:]
    if a_[0] == '--自检':
        e = 自检(a_[1]); print(('✘ ' if e else '✔ ') + '机器复听 自检：' + ('；'.join(e) if e else '吞掉一句中间 0.36 秒必报、别的句子不误报')); sys.exit(1 if e else 0)
    res = 听(a_[0], a_[1] if len(a_) > 1 else None); bad = [(k, b) for k, _, b in res if b]
    print(f'机器复听 {len(res)} 句：读音对不上的 {len(bad)} 句')
    for k, b in bad: print(f'  {k}：' + '；'.join(f'脚本“{x}” 听到“{y}”' for x, y in b))
    sys.exit(1 if bad else 0)
