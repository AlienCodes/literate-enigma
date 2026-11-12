#!/usr/bin/env python3
"""Prepare the canonical machine and fresh independent ground truth for the old 05 voice."""
import json,os,shutil,subprocess,traceback
from pathlib import Path
import numpy as np
ROOT=Path.cwd();OUT=ROOT/"article05-diagnostics";machine=Path(os.environ["RUNNER_TEMP"])/"completion-machine";tools=ROOT/"视频/工具";work=machine/"video"
def run(args,cwd=None,env=None,log=None):
    if log:
        with (OUT/log).open("w") as f:
            p=subprocess.run(list(map(str,args)),cwd=cwd,env=env,stdout=f,stderr=subprocess.STDOUT)
        if p.returncode:raise RuntimeError(f"{log}: exit {p.returncode}")
    else:subprocess.run(list(map(str,args)),check=True,cwd=cwd,env=env)
try:
    paths=["视频/工具","视频/脚本","视频/配音缓存","视频/制作记录","视频/音频核对","视频/*.md","新版定稿","视频/资源/字体","视频/视频/27.mp4","最终版4K视频/27*"]
    subprocess.run(["git","sparse-checkout","add","--stdin"],input="".join("/"+p+"\n" for p in paths),text=True,check=True)
    run(["bash",tools/"环境/准备机器.sh",ROOT,machine],log="machine-preparation.log")
    target=ROOT/"视频/资源/字体"
    if not target.exists():
        target.parent.mkdir(parents=True,exist_ok=True);target.symlink_to(tools/"fonts",target_is_directory=True)
    shutil.copy2(ROOT/"previous-diagnostics/scripts/05.json",work/"scripts/05.json")
    shutil.copytree(ROOT/"previous-diagnostics/work_05",work/"work_05",dirs_exist_ok=True)
    env={**os.environ,"VIDEO_ROOT":str(machine),"XG_P":str(ROOT),"XG_TOOLS":str(tools),"XG_WORK":str(work)}
    run(["python3",tools/"独立复核/synth.py","05"],cwd=work,env=env,log="fresh-ground-truth.log")
    run(["python3",tools/"独立复核/labels.py","05"],cwd=work,env=env,log="fresh-labels.log")
    run(["python3",tools/"独立复核/audit.py","05"],cwd=work,env=env,log="fresh-audit.log")
    qc=machine/"qc_independent"
    for p in (qc/"report2_05.json",qc/"report2_05.txt",qc/"gt/05_meta.json",qc/"gt/05_labels.json"):
        shutil.copy2(p,OUT/("fresh-"+p.name))
    rep=json.loads((qc/"report2_05.json").read_text());meta=json.loads((qc/"gt/05_meta.json").read_text())
    evidence=[]
    def rms(z):return float(20*np.log10(max(1e-12,float(np.sqrt(np.mean(z*z)))))) if len(z) else -240.
    for tr,it in zip(rep["texts"],meta):
        raw=np.load(it["file"]);ref=float(tr["peak_rms_ref"])
        for e in tr["edits"]:
            if not(e["edge_bad"] or e["tail_cut_ms"]>0 or e["onset_cut_ms"]>0):continue
            a,b=e["raw_k1"],e["raw_k2"];rows=[]
            for n in range(max(0,a-2400),min(len(raw)-480,b+2400),120):
                z=raw[n:n+120].astype(float);w=raw[max(0,n-180):n+300].astype(float);f=np.fft.rfftfreq(4096,1/24000);sp=abs(np.fft.rfft(w*np.hanning(len(w)),n=4096))**2+1e-30;ac=np.correlate(w-w.mean(),w-w.mean(),"full")[len(w)-1:]
                rows.append({"raw_s":round(n/24000,5),"db":round(rms(z)-20*np.log10(ref),2),"centroid":round(float((np.sqrt(sp)*f).sum()/np.sqrt(sp).sum())),"low150":round(float(10*np.log10(sp[f<150].sum()/sp.sum())),2),"period":round(float(ac[60:343].max()/max(1e-20,ac[0])),3)})
            evidence.append({"S":tr["idx"]+1,"text":tr["text"],"edit":e,"rows":rows})
    (OUT/"fresh-edit-evidence.json").write_text(json.dumps(evidence,ensure_ascii=False,indent=1))
    print("Fresh reference and real splice evidence exported.",flush=True)
except Exception:
    (OUT/"prepare-error.txt").write_text(traceback.format_exc());raise
