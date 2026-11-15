from pathlib import Path
import os,json,subprocess,sys,hashlib
N=Path(__file__).resolve().parent;ROOT=Path(os.environ['GITHUB_WORKSPACE']);M=Path(os.environ['RUNNER_TEMP'])/'completion-machine';T=ROOT/'official-main/视频/工具';O=ROOT/'S18-five-clips-public';O.mkdir(exist_ok=True)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
EXPECTED_ROOT_CODE_ADOPTION_SHA='d7dd82af59515389c7e5af03d100bf1b79196b70a9c43ee25e010c7cfcd8e8f0'
assert len(EXPECTED_ROOT_CODE_ADOPTION_SHA)==64 and sha(N/'root-actual-whole-observer-code-adoption.json')==EXPECTED_ROOT_CODE_ADOPTION_SHA,'Historical original whole observer code record differs'
EXPECTED_PEAK_METADATA_ADOPTION_SHA='64c22904ede732dee7f445e82e6db2d1fb79a2ff8507c0580661fefec1688107'
assert sha(N/'root-actual-peak-metadata-code-adoption.json')==EXPECTED_PEAK_METADATA_ADOPTION_SHA,'Historical original peak scalar code record differs'
assert sha(N/'observe24_S18_only_five_original_speechclips_scalar.py')=='ab9bc1954bd32ca9c7ec9d271c5e26aac906a37bacbbd9964461611d466ed172'
d=json.loads((N/'native-arguments.json').read_text());mapping={'{{TOOLS}}':str(T),'{{VIDEO_ROOT}}':str(M)}
args=[]
for key,value in d['arguments'].items():
 if value in mapping:value=mapping[value]
 elif value.startswith('{{PUBLIC_OUTPUT}}/'):value=str(O/value.split('/',1)[1])
 elif value.startswith('.github/'):value=str(ROOT/value)
 assert '{{'not in value,(key,value)
 args.extend([key,value])
raise SystemExit(subprocess.run([sys.executable,str(ROOT/d['program']),*args]).returncode)
