from pathlib import Path
import os,json,subprocess,sys,hashlib
N=Path(__file__).resolve().parent;ROOT=Path(os.environ['GITHUB_WORKSPACE']);M=Path(os.environ['RUNNER_TEMP'])/'completion-machine';T=ROOT/'official-main/视频/工具';O=ROOT/'whole24-selected-tailgain-WAV-MD5-public';O.mkdir(exist_ok=True)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
EXPECTED_ROOT_CODE_ADOPTION_SHA='0d2119ee13673cbef28d824f2fdc2de79dba33a4f1e8b803770020811843d4d8'
assert len(EXPECTED_ROOT_CODE_ADOPTION_SHA)==64 and sha(N/'derived-selected-tailgain-MD5-execution-binding.json')==EXPECTED_ROOT_CODE_ADOPTION_SHA,'Actual ROOT-derived MD5-only execution binding must be bound before dispatch'
EXPECTED_PEAK_METADATA_ADOPTION_SHA='64c22904ede732dee7f445e82e6db2d1fb79a2ff8507c0580661fefec1688107'
assert sha(N/'root-actual-peak-metadata-code-adoption.json')==EXPECTED_PEAK_METADATA_ADOPTION_SHA,'Actual root metadata-only code adoption required'
assert sha(N/'observe24_strict_cached_oldcurrent_and_selected_tailgain_whole.py')=='d5fcc2ae9bf4818e02c6c2eca1bb1ebd51895d9be930447ce34f9dcc3bf4e22e'
assert sha(N/'actual-ROOT-selected-S18-piece2-gain.json')=='2e827b8a0015bbd703f9ce56727e6d0470250acd2344849114226d3ea7391c8c','Actual ROOT selected gain adoption required'
assert sha(N/'selected-tailgain-original-whole-input-profile.json')=='118272fb1aa93b2d73f6946d313de3e09003ea5935e537bc7e5bf218b604321f','Exact selected gain observer profile required'
d=json.loads((N/'native-arguments.json').read_text());mapping={'{{TOOLS}}':str(T),'{{VIDEO_ROOT}}':str(M)}
args=[]
for key,value in d['arguments'].items():
 if value in mapping:value=mapping[value]
 elif value.startswith('{{PUBLIC_OUTPUT}}/'):value=str(O/value.split('/',1)[1])
 elif value.startswith('.github/'):value=str(ROOT/value)
 assert '{{'not in value,(key,value)
 args.extend([key,value])
raise SystemExit(subprocess.run([sys.executable,str(ROOT/d['program']),*args]).returncode)
