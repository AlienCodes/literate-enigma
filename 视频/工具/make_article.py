import re,sys,os,subprocess,numpy as np,soundfile as sf,imageio_ffmpeg
from kokoro_onnx import Kokoro
from clean import clean_tail,env_db,SR
k=Kokoro('kokoro-v1.0.onnx','voices-v1.0.bin'); VOICE=np.load('voice_mf.npy')
FF=imageio_ffmpeg.get_ffmpeg_exe(); SPEED=float(os.environ.get('SPEED','0.92'))
PAUSE={'lead':0.5,',':None,';':0.45,':':0.45,'dash':0.35,'paren':0.25,'.':0.7,'?':0.75,'para':1.0,'title':1.2,'end':1.2}
def split_inner(s):
    # split at ; : dashes and parentheses so we control those pauses; commas left to the model (~0.28s)
    out=[];buf=''
    toks=re.split(r'(;\s+|:\s+|\s+[–—]\s+|\s*\(|\)\s*)',s)
    for t in toks:
        if t is None or t=='': continue
        k_=t.strip()
        if k_ in (';',':'): out.append((buf+k_,k_)); buf=''
        elif k_ in ('–','—'): out.append((buf.rstrip()+',', 'dash')); buf=''
        elif k_=='(': 
            if buf.strip(): out.append((buf.rstrip()+',', 'paren')); buf=''
        elif k_==')': out.append((buf.rstrip()+',', 'paren')); buf=''
        else: buf+=t
    if buf.strip(): out.append((buf.strip(),'.'))
    return [(t.strip(),tl) for t,tl in out if re.search(r'[A-Za-z0-9]',t)]
def sentences(p):
    s=re.split(r'(?<=[.!?])\s+(?=[A-Z0-9"“])',p.strip())
    return [x for x in s if x]
def article(md_path,out_mp3,log=None):
    md=open(md_path).read()
    title=[l[5:].strip() for l in md.split('\n') if l.startswith('# EN:')][0]
    en=md.split('## 英文')[1].split('## 中文')[0]
    paras=[re.sub(r'\*\*','',p).strip() for p in en.strip().split('\n\n') if p.strip()]
    sil=lambda s: np.zeros(int(s*SR),dtype=np.float32)
    P=PAUSE
    parts=[sil(P['lead'])]; removed=0
    blocks=[[title]]+[sentences(p) for p in paras]
    for bi,blk in enumerate(blocks):
        for si,s in enumerate(blk):
            chunks=split_inner(s)
            for ci,(txt,tail) in enumerate(chunks):
                w,_=k.create(txt,voice=VOICE,speed=SPEED,lang='en-us'); rep=[]
                parts.append(clean_tail(w,rep)); removed+=len(rep)
                if ci<len(chunks)-1: parts.append(sil(P[tail]))
            if si<len(blk)-1: parts.append(sil(P['?'] if s.rstrip().endswith('?') else P['.']))
            else: parts.append(sil(P['title'] if bi==0 else P['para']))
    parts[-1]=sil(P['end'])
    a=np.concatenate(parts)
    a=a/np.max(np.abs(a))*0.89
    tmp=out_mp3+'.wav'; sf.write(tmp,a,SR)
    subprocess.run([FF,'-y','-loglevel','error','-i',tmp,'-af',open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'AF.txt')).read().strip(),'-ar','24000','-ac','1','-b:a','160k',out_mp3],check=True)
    os.remove(tmp)
    if log is not None: log.append((os.path.basename(out_mp3),round(len(a)/SR,1),removed))
    return a
if __name__=='__main__':
    L=[]; article(sys.argv[1],sys.argv[2],L); print(L)
