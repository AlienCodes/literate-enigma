"""Functional writer-guard tests: actual frozen request JSON + clearly synthetic calibration audio."""
from pathlib import Path
import argparse,subprocess,tempfile,json,hashlib,os,sys,numpy as np,shutil
p=argparse.ArgumentParser();p.add_argument('--tools',required=True,type=Path);p.add_argument('--requests',required=True,type=Path);p.add_argument('--output',required=True,type=Path);a=p.parse_args();T=a.tools.resolve();sys.path.insert(0,str(T));import 响度一致性核对 as R
sha=lambda b:hashlib.sha256(b).hexdigest();reports=[]
def wave(wd,no,levels):
 sr=R.SR;rng=np.random.default_rng(14);parts=[np.zeros(2*sr)];rec=[];t=2.
 for i,g in enumerate(levels):
  n=int(1.2*sr);parts.extend([rng.standard_normal(n)*0.05*10**(g/20)*np.hanning(n)**0.1,np.zeros(int(.4*sr))]);rec.append({'段':i+1,'原始':[0,0],'停顿':.4 if i<3 else None,'时刻':[t,t+1.2]});t+=1.6
 parts.append(np.zeros(2*sr));w=wd/f'work_{no}';w.mkdir(exist_ok=True);(w/'分段.json').write_text(json.dumps({'S1':rec}));subprocess.run([R.FF,'-y','-loglevel','error','-f','s16le','-ar',str(sr),'-ac','1','-i','-',str(w/'a.wav')],input=(np.concatenate(parts)*32767).astype(np.int16).tobytes(),check=True)
for no in ['10','11','12']:
 src=a.requests/f'{no}.json';raw=src.read_bytes()
 with tempfile.TemporaryDirectory(prefix='keep-reviewed-gain-') as tmp:
  wd=Path(tmp);(wd/'scripts').mkdir();jp=wd/'scripts'/f'{no}.json';jp.write_bytes(raw);wave(wd,no,[0,0,-4,0]);wav=wd/f'work_{no}/a.wav';wavsha=sha(wav.read_bytes())
  args=[sys.executable,str(T/'句内响度.py'),no,'--写入','--保持已审增益'];r=subprocess.run(args,cwd=wd,capture_output=True,text=True)
  assert r.returncode==0,(no,r.stdout,r.stderr);assert jp.read_bytes()==raw;assert sha(wav.read_bytes())==wavsha;assert '未写入' in r.stdout and '→' in r.stdout
  bad=subprocess.run([sys.executable,str(T/'响度一致性核对.py'),str(wav),'--句内','--分段',str(wd/f'work_{no}/分段.json')],capture_output=True,text=True);assert bad.returncode==1,bad.stdout
  # Backward compatibility: the same request/signal still receives calculated gain in default write mode.
  default=subprocess.run([sys.executable,str(T/'句内响度.py'),no,'--写入'],cwd=wd,capture_output=True,text=True);assert default.returncode==0 and jp.read_bytes()!=raw
  jp.write_bytes(raw);wave(wd,no,[0,0,0,0]);good=subprocess.run([sys.executable,str(T/'响度一致性核对.py'),str(wav),'--句内','--分段',str(wd/f'work_{no}/分段.json')],capture_output=True,text=True);assert good.returncode==0,good.stdout
  reports.append({'article':no,'actual_request_JSON_SHA256':sha(raw),'request_JSON_byte_exact_in_keep_mode':True,'calibration_audio_byte_exact_in_keep_mode':True,'signal_kind':'synthetic four-segment calibration only; no claim of production audio acceptance','measurement_and_suggestion_output':r.stdout.strip().splitlines(),'unchanged_original_bad_loudness_gate_exit':bad.returncode,'unchanged_original_good_loudness_gate_exit':good.returncode,'default_write_mode_still_updates_gain':True})
# Execute the actual shell in a deliberately isolated harness. Non-loudness stages are inert,
# while both real loudness invocations execute the actual original measurement code.
with tempfile.TemporaryDirectory(prefix='keep-gain-shell-') as tmp:
 wd=Path(tmp);(wd/'scripts').mkdir();no='12';raw=(a.requests/'12.json').read_bytes();jp=wd/'scripts/12.json';jp.write_bytes(raw);wave(wd,no,[0,0,-4,0]);stub=wd/'stub';stub.mkdir();bins=wd/'bin';bins.mkdir()
 (stub/'快速重建核查.sh').write_text('#!/bin/bash\nexit 0\n')
 wrapper=bins/'python3';wrapper.write_text('#!'+sys.executable+'\nimport os,sys\nfrom pathlib import Path\na=sys.argv[1:]\nif a and (a[0]=="-c" or Path(a[0]).name=="句内响度.py"):\n if a[0]!="-c":a[0]='+repr(str(T/'句内响度.py'))+'\n os.execv(sys.executable,[sys.executable]+a)\n');wrapper.chmod(0o755)
 env={**os.environ,'PATH':str(bins)+':'+os.environ['PATH'],'XG_TOOLS':str(stub),'XG_KEEP_REVIEWED_GAIN':'1'}
 r=subprocess.run(['bash',str(T/'草稿声音.sh'),no],cwd=wd,env=env,capture_output=True,text=True);assert jp.read_bytes()==raw and '未写入' in r.stdout,(r.stdout,r.stderr)
 shell={'actual_shell_environment_mode_keeps_request_JSON_byte_exact':True,'stdout':r.stdout.strip().splitlines(),'harness_scope':'All unrelated sound stages inert; real loudness measurement CLI executes unchanged. Not a full production run.'}
a.output.parent.mkdir(parents=True,exist_ok=True);result={'passed':True,'production_audio_acceptance':False,'original_loudness_checker_SHA256':sha((T/'响度一致性核对.py').read_bytes()),'cases':reports,'shell_wiring':shell};a.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'passed':True,'actual_request_cases':3,'bad_gate_refused':3,'good_gate_passed':3,'default_write_compatible':3,'shell_wiring_passed':True}))
