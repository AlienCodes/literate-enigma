from pathlib import Path
import os,json,subprocess,sys,hashlib
N=Path(__file__).resolve().parent;ROOT=Path(os.environ['GITHUB_WORKSPACE']);M=Path(os.environ['RUNNER_TEMP'])/'completion-machine';T=ROOT/'official-main/视频/工具';O=ROOT/'mother68-public';O.mkdir(exist_ok=True)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert sha(N/'prepare68_only_S2_two_mothers_spoken20_internal_delegate_fixed.py')=='29fb324a58d2b40c236317bd8b627cca953f0f2fda91ed8adf45b62b54e8b358'
d=json.loads((N/'native-arguments-internal-delegate-fixed.json').read_text());mapping={'{{TOOLS}}':str(T),'{{VIDEO_ROOT}}':str(M),'{{ACTUAL_ROOT_EXECUTION_ADOPTION_JSON}}':str(N/'actual-root-two-mother-execution-adoption.json'),'{{ACTUAL_ROOT_EXECUTION_ADOPTION_FULLSHA}}':'dfd744aba3350278072432563a8d05bc9c4b14b3b3b4c3ae13f534e6c1f08244','{{ACTUAL_COMBINED20_CERTIFICATION_PUBLIC_JSON}}':str(N/'actual20-certification43693920217.json'),'{{GITHUB_OUTPUT}}':os.environ['GITHUB_OUTPUT']}
args=[]
for key,value in d['arguments'].items():
 if value in mapping:value=mapping[value]
 elif value.startswith('{{PUBLIC_OUTPUT}}/'):value=str(O/value.split('/',1)[1])
 elif value.startswith('.github/'):value=str(ROOT/value)
 assert '{{'not in value,(key,value)
 args.extend([key,value])
raise SystemExit(subprocess.run([sys.executable,str(ROOT/d['program']),*args]).returncode)
