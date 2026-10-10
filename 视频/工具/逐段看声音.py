"""逐 2.5 ms 看一句整句合成声音 w 的任意一段（w 秒）：python3 <工具目录>/逐段看声音.py NN S# 起 止 [S# 起 止 ...]（在 sb_NN/video 里运行）
列：w 秒｜2.5 ms 电平 dB（基准 = 本句最响 5 ms 帧，与出片程序 _env5 相同）｜此刻之前 5 ms｜此刻之后 5 ms｜20 ms 周期｜10 ms 低频占比（150 Hz 以下，dB）｜10 ms 重心 Hz｜这 2.5 ms 里的过零点（w 秒，6 位小数=样本精度）
还会列出带时长模型给的附近音素（w 秒）。"""
import re,json,sys,numpy as np
sys.path.insert(0,'.')
exec(open('make_video.py').read().split("if __name__")[0],globals())
no=sys.argv[1]; d=json.load(open(f'scripts/{no}.json')); args=sys.argv[2:]
def per(x):
    x=x-x.mean()
    if np.sqrt(np.mean(x**2))<1e-9: return 0.0
    ac=np.correlate(x,x,'full')[len(x)-1:]; ac=ac/(ac[0]+1e-12); return float(ac[60:343].max())
def spec(x):
    X=np.abs(np.fft.rfft(x*np.hanning(len(x)),n=4096))**2; f=np.fft.rfftfreq(4096,1/SR)
    return float((np.sqrt(X)*f).sum()/(np.sqrt(X).sum()+1e-12)), float(10*np.log10(X[f<150].sum()/(X.sum()+1e-20)+1e-12))
for q in range(0,len(args),3):
    si=int(args[q].lstrip('S')); t0=float(args[q+1]); t1=float(args[q+2])
    s=d['sentences'][si-1]; sent=' '.join(re.sub(r'\*\*','',R.strip_gloss(c['en'])).strip() for c in s['chunks'])
    if sent in ENDING: raw=_ending_raw(sent,ENDING[sent]); sp=_ending_toks(sent,ENDING[sent]); scale=1.0     # 结尾句：两遍接起来（与出片同一个函数）
    else:
        raw,_=k.create(spoken(sent),voice=V,speed=SPEED,lang='en-us')
        tb,_,sp=KT.create_timed(spoken(sent),voice=V,speed=SPEED,lang='en-us',clause_pause=0,sentence_pause=0); scale=len(raw)/len(tb)
    w=clean_tail(raw); head=_head_offset(raw,w)
    toks=[(x.phoneme,(x.start*scale*SR-head)/SR,(x.end*scale*SR-head)/SR) for x in sp]
    n=120; m=len(w)//n; ref=np.sqrt(np.mean(w[:m*n].reshape(m,n)**2,axis=1)).max()
    lv=lambda x:20*np.log10(np.sqrt(np.mean(x**2))/ref+1e-9) if len(x) else -99
    print(f'== {no} S{si} w {t0:.4f}–{t1:.4f}s（w 全长 {len(w)/SR:.3f}s）「{sent[:70]}」')
    print('   附近音素（带时长模型，w 秒，约有 ±0.05 秒偏差）：'+' '.join(f'{p}[{a:.3f}]' for p,a,b in toks if p.strip() and b>t0-0.2 and a<t1+0.2))
    for t in np.arange(t0,t1,0.0025):
        i=int(round(t*SR)); x=w[i:i+60]; c,lo=spec(w[max(0,i-90):i+150]) if i>90 else (0,0)
        zc=[round((i+j)/SR,6) for j in range(1,len(x)) if x[j-1]*x[j]<=0]
        print(f'   {t:.4f} {lv(x):6.1f} | 前 {lv(w[max(0,i-120):i]):6.1f} | 后 {lv(w[i:i+120]):6.1f} | 周期 {per(w[max(0,i-210):i+270]):.2f} | 低频 {lo:6.1f} | 重心 {c:5.0f} | 过零 {zc[:4]}')
