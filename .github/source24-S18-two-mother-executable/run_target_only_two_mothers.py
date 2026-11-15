from pathlib import Path
import os,json,subprocess,sys,hashlib
N=Path(__file__).resolve().parent;ROOT=Path(os.environ['GITHUB_WORKSPACE']);M=Path(os.environ['RUNNER_TEMP'])/'completion-machine';T=ROOT/'official-main/视频/工具';O=ROOT/'mother24-public';O.mkdir(exist_ok=True)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert sha(N/'prepare24_only_S18_two_mothers_spoken20.py')=='e0d0f1ee1d9d716f85a0c2dd23814399d97fead2b508f02acd3f2ecca41eab90'
d=json.loads((N/'native-arguments-spoken20.json').read_text());mapping={'{{TOOLS}}':str(T),'{{VIDEO_ROOT}}':str(M),'{{ACTUAL_ROOT_EXECUTION_ADOPTION_JSON}}':str(N/'actual-root-two-mother-execution-adoption.json'),'{{ACTUAL_ROOT_EXECUTION_ADOPTION_FULLSHA}}':'755849ec13209b619897279a690f31e266609f564e93ee119a0d6fda437826de','{{ACTUAL_COMBINED20_CERTIFICATION_PUBLIC_JSON}}':str(N/'actual-spoken20-certification.json'),'{{GITHUB_OUTPUT}}':os.environ['GITHUB_OUTPUT']}
args=[]
for key,value in d['arguments'].items():
 if value in mapping:value=mapping[value]
 elif value.startswith('{{PUBLIC_OUTPUT}}/'):value=str(O/value.split('/',1)[1])
 elif value.startswith('.github/'):value=str(ROOT/value)
 assert '{{'not in value,(key,value)
 args.extend([key,value])
raise SystemExit(subprocess.run([sys.executable,str(ROOT/d['program']),*args]).returncode)
