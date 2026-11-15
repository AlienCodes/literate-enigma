from pathlib import Path
import os,json,subprocess,sys,hashlib
N=Path(__file__).resolve().parent;ROOT=Path(os.environ['GITHUB_WORKSPACE']);M=Path(os.environ['RUNNER_TEMP'])/'completion-machine';T=ROOT/'official-main/视频/工具';O=ROOT/'whole24-public';O.mkdir(exist_ok=True)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
EXPECTED_ROOT_CODE_ADOPTION_SHA='d7dd82af59515389c7e5af03d100bf1b79196b70a9c43ee25e010c7cfcd8e8f0'
assert len(EXPECTED_ROOT_CODE_ADOPTION_SHA)==64 and sha(N/'root-actual-whole-observer-code-adoption.json')==EXPECTED_ROOT_CODE_ADOPTION_SHA,'Real root whole observer code adoption must be bound before dispatch'
assert sha(N/'observe24_strict_cached_oldcurrent_and_selected_shadow_whole.py')=='9a7853d23e27830e243e5f6888dd5d296950f80aecc31912788da505ac4652f5'
d=json.loads((N/'native-arguments.json').read_text());mapping={'{{TOOLS}}':str(T),'{{VIDEO_ROOT}}':str(M)}
args=[]
for key,value in d['arguments'].items():
 if value in mapping:value=mapping[value]
 elif value.startswith('{{PUBLIC_OUTPUT}}/'):value=str(O/value.split('/',1)[1])
 elif value.startswith('.github/'):value=str(ROOT/value)
 assert '{{'not in value,(key,value)
 args.extend([key,value])
raise SystemExit(subprocess.run([sys.executable,str(ROOT/d['program']),*args]).returncode)
