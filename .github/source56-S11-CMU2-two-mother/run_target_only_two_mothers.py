from pathlib import Path
import os,json,subprocess,sys,hashlib
N=Path(__file__).resolve().parent;ROOT=Path(os.environ['GITHUB_WORKSPACE']);M=Path(os.environ['RUNNER_TEMP'])/'completion-machine';T=ROOT/'official-main/视频/工具';O=ROOT/'mother56-CMU2-public';O.mkdir(exist_ok=True)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert sha(N/'prepare56_only_S11_CMU2_two_mothers_spoken22.py')=='c7831560674aebc81249dd2d71a8ea56ad901c136fe9fda3d6b1f2918b758d28'
d=json.loads((N/'native-arguments-internal-delegate-fixed.json').read_text());mapping={'{{TOOLS}}':str(T),'{{VIDEO_ROOT}}':str(M),'{{ACTUAL_ROOT_EXECUTION_ADOPTION_JSON}}':str(N/'actual-root-two-mother-execution-adoption.json'),'{{ACTUAL_ROOT_EXECUTION_ADOPTION_FULLSHA}}':'cb29a24b4cdd11644caf168cef90580d425fc22bb88f2485b33baf2cbb110a90','{{ACTUAL_COMBINED22_CERTIFICATION_PUBLIC_JSON}}':str(N/'actual22-certification43714183305.json'),'{{GITHUB_OUTPUT}}':os.environ['GITHUB_OUTPUT']}
args=[]
for key,value in d['arguments'].items():
 if value in mapping:value=mapping[value]
 elif value.startswith('{{PUBLIC_OUTPUT}}/'):value=str(O/value.split('/',1)[1])
 elif value.startswith('.github/'):value=str(ROOT/value)
 assert '{{'not in value,(key,value)
 args.extend([key,value])
raise SystemExit(subprocess.run([sys.executable,str(ROOT/d['program']),*args]).returncode)
