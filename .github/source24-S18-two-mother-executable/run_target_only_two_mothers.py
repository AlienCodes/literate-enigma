from pathlib import Path
import os,json,subprocess,sys,hashlib
N=Path(__file__).resolve().parent;ROOT=Path(os.environ['GITHUB_WORKSPACE']);M=Path(os.environ['RUNNER_TEMP'])/'completion-machine';T=ROOT/'official-main/视频/工具';O=ROOT/'mother24-public';O.mkdir(exist_ok=True)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert sha(N/'prepare24_only_S18_two_mothers_spoken20_internal_delegate_fixed.py')=='9eb456290065ee2aa02818db53ba7e420455ec8b159221776a504825c5ab0c5b'
d=json.loads((N/'native-arguments-internal-delegate-fixed.json').read_text());mapping={'{{TOOLS}}':str(T),'{{VIDEO_ROOT}}':str(M),'{{ACTUAL_ROOT_EXECUTION_ADOPTION_JSON}}':str(N/'actual-root-two-mother-execution-adoption.json'),'{{ACTUAL_ROOT_EXECUTION_ADOPTION_FULLSHA}}':'992e591c4374570a70bdb14f23c4fbf3de0722554dd786af8aa2c7fe4d6b8ea6','{{ACTUAL_COMBINED20_CERTIFICATION_PUBLIC_JSON}}':str(N/'actual-spoken20-certification.json'),'{{GITHUB_OUTPUT}}':os.environ['GITHUB_OUTPUT']}
args=[]
for key,value in d['arguments'].items():
 if value in mapping:value=mapping[value]
 elif value.startswith('{{PUBLIC_OUTPUT}}/'):value=str(O/value.split('/',1)[1])
 elif value.startswith('.github/'):value=str(ROOT/value)
 assert '{{'not in value,(key,value)
 args.extend([key,value])
raise SystemExit(subprocess.run([sys.executable,str(ROOT/d['program']),*args]).returncode)
