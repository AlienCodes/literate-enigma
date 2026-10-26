#!/usr/bin/env python3
"""机器复听查全证明（改门 音频上GitHub 第二阶段，2026-10-26）：每句分别造一种坑，small.en 与 parakeet 各听一遍，按现行 机器复听.比 判报没报。
用法（视频工作目录，先 快速重建核查.sh NN 出 work_NN/a.wav、分段.json；parakeet 装在 ~/asr，见 改门_音频上GitHub.md 第二阶段 2 交接）：
  python3 注入查全.py 输出.json 20 21 22 23 24 26        # 2026-10-26 实测约 30 分钟（沙盒 4 核）
  python3 注入查全.py --统计 输出.json                    # 每类坑：small.en / parakeet / 两个都报 / 任一报 的查全，原样误报
坑：词尾截断（每个逗号分行结尾 80 ms 静音）、句尾截断（句末 80 ms）、词中截断（最长分行中点 0.12 秒）、漏读（中点 0.36 秒）、咔哒（中点 +0.5）、削波（×4 削顶）。
改门实施后：把 R 换成新 机器复听 的识别器组合，每类查全不得低于本文件 2026-10-26 记录的 small.en 单用。
"""
import sys, json, re, numpy as np, glob, os
if sys.argv[1] == '--统计':
    r = json.load(open(sys.argv[2])); base = {(x['篇'], x['句']): x for x in r if x['坑'] == '原样'}
    print('原样误报', {n: sum(x[n] for x in base.values()) for n in ('small', 'parakeet')}, '两个都报', sum(x['small'] and x['parakeet'] for x in base.values()), '任一', sum(x['small'] or x['parakeet'] for x in base.values()), '/', len(base))
    for k in ['词尾截断', '句尾截断', '词中截断', '漏读', '咔哒', '削波']:
        xs = [x for x in r if x['坑'] == k and not base[(x['篇'], x['句'])]['small']]
        print(k, len(xs), 'small', sum(x['small'] for x in xs), 'parakeet', sum(x['parakeet'] for x in xs), '两个都报', sum(x['small'] and x['parakeet'] for x in xs), '任一', sum(x['small'] or x['parakeet'] for x in xs))
    sys.exit(0)
OUT, NOS = sys.argv[1], sys.argv[2:]
import soundfile as sf
from scipy.signal import resample_poly
T='/home/user/postgraduate-vocabulary/视频/工具'; sys.path.insert(0,T); import 机器复听 as M, sherpa_onnx
A=os.path.expanduser('~/asr')
R={'small':M.识别器(),
   'parakeet':sherpa_onnx.OfflineRecognizer.from_transducer(encoder=f'{A}/sherpa-onnx-nemo-parakeet-tdt-0.6b-v2-int8/encoder.int8.onnx',decoder=f'{A}/sherpa-onnx-nemo-parakeet-tdt-0.6b-v2-int8/decoder.int8.onnx',joiner=f'{A}/sherpa-onnx-nemo-parakeet-tdt-0.6b-v2-int8/joiner.int8.onnx',tokens=f'{A}/sherpa-onnx-nemo-parakeet-tdt-0.6b-v2-int8/tokens.txt',model_type='nemo_transducer',num_threads=4)}
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
    return x
K=['原样','词尾截断','句尾截断','词中截断','漏读','咔哒','削波']; out=[]
for no in NOS:
    d=json.load(open(f'scripts/{no}.json')); seg=json.load(open(f'work_{no}/分段.json')); a,sr=sf.read(f'work_{no}/a.wav'); a=a if a.ndim==1 else a.mean(1)
    for i,(key,v) in enumerate(seg.items()):
        t0,t1=v[0]['时刻'][0],v[-1]['时刻'][1]; x=a[int(t0*sr):int(t1*sr)]
        ref=' '.join(re.sub(r'\{\{.*?\}\}|\*\*','',c['en']) for c in d['sentences'][i]['chunks'])
        for k in K:
            y=坑(x,sr,v,t0,k); out.append({'篇':no,'句':key,'坑':k,**{n:bool(M.比(ref,asr(r,y,sr))) for n,r in R.items()}})
    print(no,len(out),flush=True)
json.dump(out,open(OUT,'w'),ensure_ascii=False)
