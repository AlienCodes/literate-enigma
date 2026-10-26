#!/usr/bin/env python3
"""音频上 GitHub 评估（改门_音频上GitHub.md 第一阶段，只评估、不改门）。
  正例 TTS OUT          合成标准答案：读音改正表里配音原来读错的词（读错版 = 真问题、改正版 = 不该报）、漏一个词的句子（真问题）
  听 模型 片 OUT.json   某个识别模型听一片：成片 01–26 每句（用户认可 = 不该报）或 正例
  汇总 目录             每个模型、两两投票的查准率/查全率
  打分 片 OUT.json      MOS 自动打分（UTMOS22、DNSMOS）：成片每句基线 + 造坑副本（咔哒、截断、电流音、发闷、噪声、削波）
  精度 TTS OUT.json     配音模型 fp32（现用）/ fp16 / int8 同一句对比
"""
import os, sys, re, json, glob, time, hashlib, numpy as np
G = os.environ.get('GITHUB_WORKSPACE', '/home/user/literate-enigma'); V = f'{G}/视频'; T = f'{V}/工具'; sys.path.insert(0, T)
import soundfile as sf
from scipy.signal import resample_poly

def 句子(no):
    import 音频体检 as Q; return Q.文本(no)

def 改正表():
    d = json.load(open(f'{T}/发音词典/读音改正.json')); return {k: v for k, v in d.items()}

def 注音(K, text, skip=None):
    """整句注音，读音改正表里的词换成正确音标（skip 这个词不换 = 配音原来的读法）"""
    s = lambda x: ''.join('[ˈˌ]?' + re.escape(c) for c in re.sub('[ˈˌ ]', '', x)) + '[ˈˌ]?'
    ph = K.tokenizer.phonemize(text, 'en-us'); n = 0
    for w, v in 改正表().items():
        if w == skip or not re.search(r"(?<![A-Za-z])" + re.escape(w) + r"(?![A-Za-z])", text, re.I): continue
        bad = re.sub(r'[,;:.!?]', '', K.tokenizer.phonemize(w, 'en-us')).strip()
        ph, c = re.subn("(?<![^\\s,;:.!?])" + s(bad) + "(?=[sz]?[\\s,;:.!?]|$)", v['读音'], ph); n += c
    return ph

def 正例(tts, out):
    from kokoro_onnx import Kokoro
    K = Kokoro(f'{tts}/kokoro-v1.0.onnx', f'{tts}/voices-v1.0.bin'); VO = np.load(f'{tts}/voice_mb.npy')
    os.makedirs(out, exist_ok=True); man = []; nos = [f'{i:02d}' for i in range(1, 28) if i != 5]
    allS = [(no, i, t) for no in nos for i, t in enumerate(句子(no) or []) if i > 0]
    st = lambda x: re.sub('[ˈˌ ]', '', x or '')
    def syn(id_, ph, meta):
        w, _ = K.create(ph, voice=VO, speed=0.95, lang='en-us', is_phonemes=True)
        sf.write(f'{out}/{id_}.wav', np.asarray(w, np.float32), 24000); meta['id'] = id_; man.append(meta)
    for w, v in 改正表().items():
        hit = next(((no, i, t) for no, i, t in allS if re.search(r"(?<![A-Za-z])" + re.escape(w) + r"(?![A-Za-z])", t, re.I)), None)
        if not hit: continue
        no, i, t = hit; kind = '读错' if st(v.get('配音原来读作')) != st(v['读音']) else '只差重音'
        h = hashlib.md5(w.encode()).hexdigest()[:8]
        syn(f'bad_{h}', 注音(K, t, skip=w), {'类': kind, '真问题': True, '篇': no, '句': i, 'ref': t, '词': w, '原读': v.get('配音原来读作'), '正读': v['读音']})
        syn(f'fix_{h}', 注音(K, t), {'类': '改正版', '真问题': False, '篇': no, '句': i, 'ref': t, '词': w})
    rng = np.random.default_rng(7)
    for no, i, t in [allS[j] for j in rng.choice(len(allS), 60, replace=False)]:
        ws = t.split(); cand = [j for j in range(2, len(ws) - 2) if re.fullmatch(r'[a-z]{4,}', ws[j])]
        if not cand: continue
        j = cand[len(cand) // 2]; t2 = ' '.join(ws[:j] + ws[j + 1:])
        syn(f'omit_{no}_{i}', 注音(K, t2), {'类': '漏词', '真问题': True, '篇': no, '句': i, 'ref': t, '词': ws[j]})
    json.dump(man, open(f'{out}/清单.json', 'w'), ensure_ascii=False, indent=0); print('正例', len(man), '条')

# ---------- 识别模型 ----------
def 识别器(name):
    import sherpa_onnx; d = os.path.expanduser(f'~/asr/{name}')
    g = lambda p: sorted(glob.glob(f'{d}/{p}'))[0]
    if 'parakeet' in name:
        return sherpa_onnx.OfflineRecognizer.from_transducer(encoder=g('encoder*.onnx'), decoder=g('decoder*.onnx'), joiner=g('joiner*.onnx'),
                                                            tokens=g('tokens.txt'), model_type='nemo_transducer', num_threads=4)
    q = '.int8.onnx' if glob.glob(f'{d}/*encoder.int8.onnx') else '.onnx'
    return sherpa_onnx.OfflineRecognizer.from_whisper(encoder=g('*encoder' + q), decoder=g('*decoder' + q), tokens=g('*tokens.txt'), num_threads=4)

class FW:
    def __init__(s, name):
        from faster_whisper import WhisperModel; s.m = WhisperModel(name.split(':')[1], device='cpu', compute_type='float32', cpu_threads=4)
    def 听(s, x):
        seg, _ = s.m.transcribe(x, language='en', beam_size=5, condition_on_previous_text=False); return ' '.join(z.text for z in seg)

def 转写(rec, x):
    if isinstance(rec, FW): return rec.听(x)
    st = rec.create_stream(); st.accept_waveform(16000, x); rec.decode_stream(st); return st.result.text

def 听(name, part, out):
    import 机器复听 as M
    rec = FW(name) if name.startswith('fw:') else 识别器(name); res = []; t0 = time.time(); dur = 0
    if part.startswith('正例'):
        k, n = map(int, part[2:].split('/')); man = json.load(open(f'{os.environ["正例"]}/清单.json'))
        for m in man[k::n]:
            a, sr = sf.read(f'{os.environ["正例"]}/{m["id"]}.wav'); x = resample_poly(a, 2, 3).astype(np.float32); dur += len(x) / 16000
            h = 转写(rec, x); res.append({**m, 'hyp': h, '报': M.比(m['ref'], h)})
    else:
        import 音频体检 as Q
        for no in part.split(','):
            f = glob.glob(f'{V}/视频/{no}.mp4')[0]; a = Q.读(f); seg = Q.句段(a); txt = 句子(no)
            if len(txt) != len(seg): print(no, '句数对不上'); continue
            for i, ((s0, e0), ref) in enumerate(zip(seg[1:], txt[1:]), 1):
                x = resample_poly(a[s0:e0], 1, 3).astype(np.float32); dur += len(x) / 16000
                h = 转写(rec, x); res.append({'类': '成片', '真问题': False, '篇': no, '句': i, 'ref': ref, 'hyp': h, '报': M.比(ref, h), '秒': len(x) / 16000})
    json.dump({'模型': name, '片': part, '用时': time.time() - t0, '声音秒': dur, '结果': res}, open(out, 'w'), ensure_ascii=False)
    print(name, part, len(res), '句', f'{time.time() - t0:.0f} 秒 / 声音 {dur:.0f} 秒', '报', sum(bool(r['报']) for r in res))

def 中(r):
    """这一句报没报（真问题要报到那个词上）"""
    if not r['报']: return False
    if not r['真问题']: return True
    w = r['词'].lower()
    return any(w in x.lower() or (r['类'] == '漏词' and y == '（没听到）') for x, y in r['报'])

def 汇总(d):
    by = {}
    for f in glob.glob(f'{d}/**/听_*.json', recursive=True):
        j = json.load(open(f)); m = by.setdefault(j['模型'], {'r': {}, '用时': 0, '声音秒': 0})
        m['用时'] += j['用时']; m['声音秒'] += j['声音秒']
        for r in j['结果']: m['r'][(r['类'], r.get('id') or f"{r['篇']}_{r['句']}")] = r
    L = ['# 机器复听：各识别模型查准查全（标准答案：01–26 成片每句 = 用户认可不该报；读音改正表 86 处配音原读错 = 该报；漏一个词 = 该报）', '']
    def 统计(hit, keys, R):
        out = {}
        for c in ('成片', '改正版', '读错', '只差重音', '漏词'):
            ks = [k for k in keys if k[0] == c]; out[c] = (sum(hit(k) for k in ks), len(ks))
        tp = out['读错'][0] + out['漏词'][0]; P = out['读错'][1] + out['漏词'][1]; fp = out['成片'][0] + out['改正版'][0]; N = out['成片'][1] + out['改正版'][1]
        out['查全'] = tp / max(P, 1); out['误报率'] = fp / max(N, 1); out['查准'] = tp / max(tp + fp, 1); return out
    rows = []
    for name, m in sorted(by.items()):
        rows.append((name, 统计(lambda k: 中(m['r'][k]), list(m['r']), m['r']), m))
    names = sorted(by)
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            ks = [k for k in by[a]['r'] if k in by[b]['r']]
            rows.append((f'{a} 且 {b}', 统计(lambda k: 中(by[a]['r'][k]) and 中(by[b]['r'][k]), ks, None), None))
            rows.append((f'{a} 或 {b}', 统计(lambda k: 中(by[a]['r'][k]) or 中(by[b]['r'][k]), ks, None), None))
    L.append('| 模型 | 成片误报（句） | 改正版误报 | 读错查出 | 漏词查出 | 只差重音查出 | 查全 | 查准 | 识别用时/声音时长 |'); L.append('|---|---|---|---|---|---|---|---|---|')
    for n, o, m in rows:
        f = lambda c: f'{o[c][0]}/{o[c][1]}'
        L.append(f"| {n} | {f('成片')} | {f('改正版')} | {f('读错')} | {f('漏词')} | {f('只差重音')} | {o['查全']:.0%} | {o['查准']:.0%} | {m['用时'] / max(m['声音秒'], 1):.2f}" + ' |' if m else ' | — |')
    L += ['', '## 各模型在成片上的误报（逐句）', '']
    for name, m in sorted(by.items()):
        b = [r for k, r in m['r'].items() if k[0] == '成片' and r['报']]
        L.append(f'- **{name}**：{len(b)} 句：' + '；'.join(f"{r['篇']} S{r['句']} " + ','.join(f'{x}→{y}' for x, y in r['报']) for r in b))
    L += ['', '## 各模型漏掉的读错（该报没报）', '']
    for name, m in sorted(by.items()):
        b = [r for k, r in m['r'].items() if k[0] == '读错' and not 中(r)]
        L.append(f'- **{name}**：{len(b)} 处：' + '；'.join(f"{r['词']}（/{r['原读']}/→/{r['正读']}/ 听到“{r['hyp'][:50]}”）" for r in b))
    print('\n'.join(L))

# ---------- MOS ----------
def 打分(part, out):
    import torch, onnxruntime as ort, 音频体检 as Q
    torch.set_num_threads(4)
    ut = torch.hub.load('tarepan/SpeechMOS:v1.2.0', 'utmos22_strong', trust_repo=True)
    dn = os.path.expanduser('~/dnsmos'); S1 = ort.InferenceSession(f'{dn}/sig_bak_ovr.onnx'); S2 = ort.InferenceSession(f'{dn}/model_v8.onnx')
    def dnsmos(x):   # 16 kHz；微软 DNSMOS P.835（SIG/BAK/OVRL，个人化前的多项式校准）+ P.808
        L = int(9.01 * 16000); y = np.tile(x, int(np.ceil(L / len(x))))[:L].astype(np.float32) if len(x) < L else x[:L].astype(np.float32)
        import librosa
        sig, bak, ovr = S1.run(None, {S1.get_inputs()[0].name: y[None]})[0][0]
        mel = librosa.feature.melspectrogram(y=y[:-160], sr=16000, n_fft=321, hop_length=160, n_mels=120)
        mel = (librosa.power_to_db(mel, ref=np.max) + 40) / 40
        p808 = S2.run(None, {S2.get_inputs()[0].name: mel.T[None].astype(np.float32)})[0][0][0]
        P = lambda c, v: np.polyval(c, v)
        return dict(SIG=float(P([-0.08397278, 1.22083953, 0.0052439], sig)), BAK=float(P([-0.13166888, 1.60915514, -0.39604546], bak)),
                    OVRL=float(P([-0.06766283, 1.11546468, 0.04602535], ovr)), P808=float(p808))
    def utmos(x): return float(ut(torch.from_numpy(x.astype(np.float32))[None], 16000).item())
    def 坑(x, k, sr=48000):
        x = x.copy(); n = len(x)
        if k == '咔哒': x[n // 2] += 0.3
        if k == '截断60ms': x[-int(0.06 * sr):] = 0
        if k == '电流音4800Hz': x += 10 ** (-50 / 20) * np.sin(2 * np.pi * 4800 * np.arange(n) / sr)
        if k == '发闷4k低通':
            from scipy.signal import butter, sosfilt; x = sosfilt(butter(8, 4000, fs=sr, output='sos'), x)
        if k == '噪声-45dB': x += np.random.default_rng(0).normal(0, 10 ** (-45 / 20), n)
        if k == '削波+6dB': x = np.clip(x * 2, -1, 1) / 2
        return x
    res = []; t0 = time.time()
    for no in part.split(','):
        a = Q.读(glob.glob(f'{V}/视频/{no}.mp4')[0]); seg = Q.句段(a)
        for i, (s0, e0) in enumerate(seg[1:], 1):
            for k in ['原样'] + (['咔哒', '截断60ms', '电流音4800Hz', '发闷4k低通', '噪声-45dB', '削波+6dB'] if i % 3 == 1 else []):
                x48 = a[s0:e0] if k == '原样' else 坑(a[s0:e0], k); x = resample_poly(x48, 1, 3).astype(np.float32)
                res.append({'篇': no, '句': i, '坑': k, 'UTMOS': utmos(x), **dnsmos(x)})
        print(no, len(res), f'{time.time() - t0:.0f} 秒', flush=True)
    json.dump({'片': part, '用时': time.time() - t0, '结果': res}, open(out, 'w'), ensure_ascii=False)

def 打分汇总(d):
    rs = [r for f in glob.glob(f'{d}/**/打分_*.json', recursive=True) for r in json.load(open(f))['结果']]
    base = [r for r in rs if r['坑'] == '原样']; L = ['# MOS 自动打分：01–26 成片每句基线，造坑副本能不能被打分抓到', '']
    for m in ('UTMOS', 'OVRL', 'SIG', 'BAK', 'P808'):
        v = np.array([r[m] for r in base]); lo = v.min()
        L.append(f'## {m}：基线 {len(v)} 句 中位 {np.median(v):.2f}，最低 {lo:.2f}（{min(base, key=lambda r: r[m])["篇"]} S{min(base, key=lambda r: r[m])["句"]}），5% 分位 {np.percentile(v, 5):.2f}')
        o = {(r['篇'], r['句']): r[m] for r in base}
        for k in sorted({r['坑'] for r in rs} - {'原样'}):
            x = [(r[m], o[(r['篇'], r['句'])]) for r in rs if r['坑'] == k]
            d_ = np.array([b - a for a, b in x]); caught = sum(a < lo for a, _ in x)
            L.append(f'- {k}：平均降 {d_.mean():.2f}（同一句比），低于全片最低基线（=会被“低于基线就停”抓到）{caught}/{len(x)}')
        L.append('')
    print('\n'.join(L))

def 精度(tts, out):
    import onnxruntime as ort
    from kokoro_onnx import Kokoro
    VO = np.load(f'{tts}/voice_mb.npy'); txt = [t for no in ('03', '12', '26') for t in 句子(no)[1:4]]; R = {}
    for v in ('kokoro-v1.0.onnx', 'kokoro-v1.0.fp16.onnx', 'kokoro-v1.0.int8.onnx'):
        if not os.path.exists(f'{tts}/{v}'): continue
        so = ort.SessionOptions(); so.intra_op_num_threads = 1
        K = Kokoro.from_session(ort.InferenceSession(f'{tts}/{v}', so, providers=['CPUExecutionProvider']), f'{tts}/voices-v1.0.bin'); t0 = time.time()
        R[v] = [np.asarray(K.create(t, voice=VO, speed=0.95, lang='en-us')[0], np.float32) for t in txt]; print(v, f'{time.time() - t0:.1f} 秒')
        os.makedirs(os.path.dirname(out) or '.', exist_ok=True)
        for i, w in enumerate(R[v][:2]): sf.write(f'{os.path.dirname(out) or "."}/精度_{v[:-5]}_{i}.wav', w, 24000)
    ref = R['kokoro-v1.0.onnx']; o = {}
    for v, ws in R.items():
        d = [float(np.max(np.abs(a[:min(len(a), len(b))] - b[:min(len(a), len(b))]))) for a, b in zip(ws, ref)]
        snr = [float(10 * np.log10(np.sum(b ** 2) / max(np.sum((a[:len(b)] - b[:len(a)]) ** 2), 1e-20))) if len(a) == len(b) else None for a, b in zip(ws, ref)]
        o[v] = {'最大差': max(d), '与fp32信噪比dB': snr, '长度一样': all(len(a) == len(b) for a, b in zip(ws, ref))}
    json.dump(o, open(out, 'w'), ensure_ascii=False, indent=1); print(json.dumps(o, ensure_ascii=False)[:800])

if __name__ == '__main__':
    c, *a = sys.argv[1:]
    {'正例': 正例, '听': 听, '汇总': 汇总, '打分': 打分, '打分汇总': 打分汇总, '精度': 精度}[c](*a)
