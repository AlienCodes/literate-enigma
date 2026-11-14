import numpy as np
SR=24000; WIN=240
def env_db(w,win=WIN):
    n=len(w)//win
    e=np.sqrt(np.mean(w[:n*win].reshape(n,win)**2,axis=1))
    return 20*np.log10(e+1e-9)
def centroid(seg):
    if len(seg)<64: return 0
    f=np.abs(np.fft.rfft(seg*np.hanning(len(seg)))); fr=np.fft.rfftfreq(len(seg),1/SR)
    return (f*fr).sum()/(f.sum()+1e-9)
def runs(mask):
    r=[];i=0;n=len(mask)
    while i<n:
        if mask[i]:
            j=i
            while j<n and mask[j]: j+=1
            r.append((i,j)); i=j
        else: i+=1
    return r
def clean_tail(w, report=None):
    w=np.asarray(w,dtype=np.float32)
    for _ in range(4):
        db=env_db(w); peak=db.max(); rr=runs(db>peak-40)
        if len(rr)<2: break
        (a0,b0),(a,b)=rr[-2],rr[-1]
        gap=(a-b0)*WIN/SR; dur=(b-a)*WIN/SR; c=centroid(w[a*WIN:b*WIN])
        if gap>=0.25 and dur<0.05 and (b-a)>0 and env_db(w)[a:b].max()<peak-25:
            if report is not None: report.append((round(dur,2),round(c)))
            w=w[:b0*WIN]
        else: break
    db=env_db(w); peak=db.max(); idx=np.where(db>peak-48)[0]
    st=max(0,idx[0]*WIN-int(0.02*SR)); end=min(len(w),(idx[-1]+1)*WIN+int(0.08*SR))
    w=w[st:end].copy()
    f=int(0.05*SR); w[-f:]*=np.linspace(1,0,f)**2
    g=int(0.01*SR); w[:g]*=np.linspace(0,1,g)
    return w
