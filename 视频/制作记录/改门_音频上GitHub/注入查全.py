#!/usr/bin/env python3
"""机器复听查全证明（改门 音频上GitHub 第二阶段，2026-10-26）：每句分别造一种坑，small.en 与 parakeet 各听一遍，按现行 机器复听.比 判报没报。
用法（视频工作目录，先 快速重建核查.sh NN 出 work_NN/a.wav、分段.json；parakeet 装在 ~/asr，见 改门_音频上GitHub.md 第二阶段 2 交接）：
  python3 注入查全.py 输出.json 20 21 22 23 24 26        # 2026-10-26 实测约 30 分钟（沙盒 4 核）
  python3 注入查全.py --统计 输出.json                    # 每类坑：small.en / parakeet / 两个都报 / 任一报 的查全，原样误报
2026-10-26 第二阶段 2：加第三个识别器 ctc（NeMo CTC conformer-small 贪心，不带语言模型）、加一类坑“虚词漏读”（parakeet 逐词时刻找本句第一个
a/an/the/it/and/of/to，整词切掉，接缝两边各 10 ms 交叉淡化，不留静音），结果里存每路听到的文字（--统计 现场按 机器复听.比 重判，比() 改了不用重听）。
坑：词尾截断（每个逗号分行结尾 80 ms 静音）、句尾截断（句末 80 ms）、词中截断（最长分行中点 0.12 秒）、漏读（中点 0.36 秒）、咔哒（中点 +0.5）、削波（×4 削顶）。
改门实施后：把 R 换成新 机器复听 的识别器组合，每类查全不得低于本文件 2026-10-26 记录的 small.en 单用。
"""
import sys, json, re, numpy as np, glob, os
if sys.argv[1] == '--统计':
    T='/home/user/postgraduate-vocabulary/视频/工具'; sys.path.insert(0,T); import 机器复听 as M
    r = json.load(open(sys.argv[2])); N = [n for n in ('small', 'parakeet', 'ctc') if n in r[0]['听到']]
    r = [x for x in r if '听到' in x] + [x for x in r if '听到' not in x]
    for x in r:
        if '听到' in x: x.update({n: bool(M.比(x['ref'], x['听到'][n])) for n in N})
    base = {(x['篇'], x['句']): x for x in r if x['坑'] == '原样'}
    组 = {'small': lambda x: x['small'], 'parakeet': lambda x: x['parakeet'], 's|p': lambda x: x['small'] or x['parakeet']}
    if 'ctc' in N: 组.update({'ctc': lambda x: x['ctc'], 's|c': lambda x: x['small'] or x['ctc'], 's|p|c': lambda x: x['small'] or x['parakeet'] or x['ctc']})
    print('| 坑 | 句数 | ' + ' | '.join(组) + ' |')
    print(f'| 原样误报 | {len(base)} | ' + ' | '.join(str(sum(f(x) for x in base.values())) for f in 组.values()) + ' |')
    for k in ['词尾截断', '句尾截断', '词中截断', '漏读', '咔哒', '削波', '虚词漏读']:
        xs = [x for x in r if x['坑'] == k]   # 每种组合只在它原样不报的句子上算（查全 = 抓到 / 这些句数），原样就报的句子不算“抓到”
        if xs: print(f'| {k} | {len(xs)} | ' + ' | '.join(f'{sum(f(x) for x in xs if not f(base[(x["篇"], x["句"])]))}/{sum(1 for x in xs if not f(base[(x["篇"], x["句"])]))}' for f in 组.values()) + ' |')
    print('虚词漏读 跳过（句中没有这些词）', sum(1 for x in r if x['坑'] == '虚词漏读跳过'))
    if '--误报' in sys.argv:
        for x in base.values():
            for n in N:
                if x[n]: print(x['篇'], x['句'], n, M.比(x['ref'], x['听到'][n]))
    sys.exit(0)
OUT, NOS = sys.argv[1], sys.argv[2:]
import soundfile as sf
from scipy.signal import resample_poly
T='/home/user/postgraduate-vocabulary/视频/工具'; sys.path.insert(0,T); import 机器复听 as M, sherpa_onnx
A=os.path.expanduser('~/asr')
R={'small':M.识别器(),
   'parakeet':sherpa_onnx.OfflineRecognizer.from_transducer(encoder=f'{A}/sherpa-onnx-nemo-parakeet-tdt-0.6b-v2-int8/encoder.int8.onnx',decoder=f'{A}/sherpa-onnx-nemo-parakeet-tdt-0.6b-v2-int8/decoder.int8.onnx',joiner=f'{A}/sherpa-onnx-nemo-parakeet-tdt-0.6b-v2-int8/joiner.int8.onnx',tokens=f'{A}/sherpa-onnx-nemo-parakeet-tdt-0.6b-v2-int8/tokens.txt',model_type='nemo_transducer',num_threads=4),
   'ctc':sherpa_onnx.OfflineRecognizer.from_nemo_ctc(model=f'{A}/sherpa-onnx-nemo-ctc-en-conformer-small/model.int8.onnx',tokens=f'{A}/sherpa-onnx-nemo-ctc-en-conformer-small/tokens.txt',num_threads=4)}
虚词 = {'a', 'an', 'the', 'it', 'and', 'of', 'to'}
def 虚词段(x, sr):
    """parakeet 逐词时刻：本句第一个虚词的 [起, 止)（秒，相对本句开头）；没有返回 None"""
    y = resample_poly(x, 16000, sr).astype(np.float32); s = R['parakeet'].create_stream(); s.accept_waveform(16000, y); R['parakeet'].decode_stream(s); res = s.result
    ws = []   # [词, 起, 止]
    for t, a_, d_ in zip(res.tokens, res.timestamps, res.durations):
        if t.startswith(' ') or not ws: ws.append([t.strip().lower(), a_, a_ + d_])
        else: ws[-1][0] += t; ws[-1][2] = a_ + d_
    for i, (w, a_, b_) in enumerate(ws):
        if w in 虚词: return a_, min(b_, ws[i + 1][1]) if i + 1 < len(ws) else b_
    return None
def asr(r,x,sr):
    x=resample_poly(x,16000,sr).astype(np.float32); s=r.create_stream(); s.accept_waveform(16000,x); r.decode_stream(s); return s.result.text
def 坑(x,sr,v,t0,k):
    x=x.copy(); o=lambda t:int((t-t0)*sr)
    if k=='词尾截断':   # 每个分行（逗号处）结尾的词尾 80 ms 变静音
        for c in v[:-1]: e=o(c['时刻'][1]); x[max(0,e-int(.08*sr)):e]=0
    if k=='句尾截断': e=o(v[-1]['时刻'][1]); x[max(0,e-int(.08*sr)):e]=0
    i=max(range(len(v)),key=lambda j:v[j]['时刻'][1]-v[j]['时刻'][0]); m=o((v[i]['时刻'][0]+v[i]['时刻'][1])/2)
    if k=='词中截断': x[m-int(.06*sr):m+int(.06*sr)]=0
    if k=='漏读': x[m-int(.18*sr):m+int(.18*sr)]=0
    if k=='咔哒': x[m]+=0.5
    if k=='削波': x=np.clip(x*4,-1,1)/4
    if k=='虚词漏读':
        g=虚词段(x,sr)
        if g is None: return None
        i0,i1=int(g[0]*sr),int(g[1]*sr); f=int(.01*sr); w=np.linspace(0,1,f)
        a_,b_=x[:i0],x[i1:]
        if len(a_)<f or len(b_)<f: return None
        x=np.concatenate([a_[:-f],a_[-f:]*(1-w)+b_[:f]*w,b_[f:]])
    return x
K=['原样','词尾截断','句尾截断','词中截断','漏读','咔哒','削波','虚词漏读']; out=[]
for no in NOS:
    d=json.load(open(f'scripts/{no}.json')); seg=json.load(open(f'work_{no}/分段.json')); a,sr=sf.read(f'work_{no}/a.wav'); a=a if a.ndim==1 else a.mean(1)
    for i,(key,v) in enumerate(seg.items()):
        t0,t1=v[0]['时刻'][0],v[-1]['时刻'][1]; x=a[int(t0*sr):int(t1*sr)]
        ref=' '.join(re.sub(r'\{\{.*?\}\}|\*\*','',c['en']) for c in d['sentences'][i]['chunks'])
        for k in K:
            y=坑(x,sr,v,t0,k)
            if y is None: out.append({'篇':no,'句':key,'坑':k+'跳过'}); continue
            out.append({'篇':no,'句':key,'坑':k,'ref':ref,'听到':{n:asr(r,y,sr) for n,r in R.items()}})
    print(no,len(out),flush=True); json.dump(out,open(OUT,'w'),ensure_ascii=False)   # 每篇存一次
