#!/usr/bin/env python3
"""Export real 05 diagnostic evidence without changing voice data or checks."""
import hashlib,json,os,shutil,subprocess,wave
from pathlib import Path
import numpy as np
ROOT=Path.cwd();OUT=ROOT/"article05-diagnostics";OUT.mkdir(exist_ok=True)
SRC=ROOT/"previous-diagnostics";machine=Path(os.environ["RUNNER_TEMP"])/"completion-machine"
files=[{"path":str(p.relative_to(SRC)),"bytes":p.stat().st_size} for p in SRC.rglob("*") if p.is_file()]
(OUT/"inventory.json").write_text(json.dumps({"previous_files":files,"machine_exists":machine.exists(),"machine_top":[str(p.relative_to(machine)) for p in machine.glob("*")],"models":[str(p) for p in (Path.home()/"asr").glob("*")]},ensure_ascii=False,indent=2))
for p in SRC.rglob("*"):
    if p.is_file() and p.suffix in (".log",".txt",".json",".csv") and p.stat().st_size<4_000_000:
        dest=OUT/"previous"/p.relative_to(SRC);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
a=next(SRC.rglob("a.wav"))
with wave.open(str(a)) as w:
    assert w.getsampwidth()==2 and w.getnchannels()==1
    sr=w.getframerate();x=np.frombuffer(w.readframes(w.getnframes()),dtype="<i2").astype(np.float64)/32768
def rms(z):return float(20*np.log10(max(1e-12,float(np.sqrt(np.mean(z*z)))))) if len(z) else -240.
def features(t):
    z=x[round(t*sr):round((t+.005)*sr)].astype(np.float64);w=x[max(0,round((t-.0075)*sr)):round((t+.0125)*sr)].astype(np.float64)
    if len(w)<100:return {}
    f=np.fft.rfftfreq(len(w),1/sr);e=abs(np.fft.rfft(w*np.hanning(len(w))))**2+1e-30
    ac=np.correlate(w,w,"full")[len(w)-1:];period=float(max(ac[round(sr/400):round(sr/70)])/max(1e-20,ac[0]))
    return {"s":round(t,4),"db":round(rms(z),2),"centroid_hz":round(float((f*e).sum()/e.sum())),"low180_db":round(float(10*np.log10(e[f<180].sum()/e.sum())),2),"high4k_db":round(float(10*np.log10(e[f>4000].sum()/e.sum())),2),"period":round(period,3)}
for label,(a0,b) in {"highlight-S5-4":[43.60,44.12],"purevoice-tail":[60.20,61.10],"breath":[116.05,116.65]}.items():
    (OUT/(label+".json")).write_text(json.dumps([features(t) for t in np.arange(a0,b,.005)],ensure_ascii=False,indent=1))
(OUT/"audio-properties.json").write_text(json.dumps({"a_wav":str(a.relative_to(SRC)),"file_md5":hashlib.md5(a.read_bytes()).hexdigest()[:12],"seconds":len(x)/sr,"rms_db":rms(x),"peak":float(abs(x).max())},indent=2))
candidates=[]
if machine.exists():
    for p in machine.rglob("*"):
        if p.is_file() and ("/qc/" in str(p) or "dossier" in p.name or "分段" in p.name) and p.suffix in (".json",".txt",".npy"):
            candidates.append({"path":str(p.relative_to(machine)),"bytes":p.stat().st_size})
(OUT/"cached-ground-truth.json").write_text(json.dumps(candidates,ensure_ascii=False,indent=2))
print("Evidence exported:",len(files),"files; cache present:",machine.exists(),flush=True)
