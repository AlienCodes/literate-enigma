from pathlib import Path
import hashlib,json,os,subprocess,sys
N=Path(__file__).resolve().parent;ROOT=Path(os.environ['GITHUB_WORKSPACE']);M=Path(os.environ['RUNNER_TEMP'])/'completion-machine';T=ROOT/'official-main/视频/工具'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
EXPECTED_ROOT_SHA='f3aa158510cc662779ab26585ca11e3a6a257039d7e06c8952c385b08efde4e2';EXPECTED_HELPER_SHA='e7420d7372dd1acadf75b080f2117c0366614848dcce51dcbf4d86b165c2f0d7';EXPECTED_PROFILE_SHA='64b1abf5a8a0efbf93e7de6bdc0b651de9eb410c116b35f067d575766d53eab3';EXPECTED_ARGV_SHA='3dfd054fec59c42397d7ff88818bc5ebb525916b5121e638ca221e420befffae'
assert sha(N/'root-original-G35-actual-scope.json')==EXPECTED_ROOT_SHA
assert sha(N/'observe35_only_S15_two_actual_PV_windows.py')==EXPECTED_HELPER_SHA and sha(N/'source35-S15-two-PV-profile.json')==EXPECTED_PROFILE_SHA and sha(N/'native-arguments.json')==EXPECTED_ARGV_SHA
mapping={'{{TOOLS}}':str(T),'{{VIDEO_ROOT}}':str(M),'{{GITHUB_WORKSPACE}}':str(ROOT),'{{ACTUAL_ROOT_EXECUTION_ADOPTION_JSON}}':str(N/'root-original-G35-actual-scope.json'),'{{ACTUAL_ROOT_EXECUTION_ADOPTION_FULLSHA}}':EXPECTED_ROOT_SHA,'{{GITHUB_OUTPUT}}':os.environ['GITHUB_OUTPUT']}
d=json.loads((N/'native-arguments.json').read_text());args=[]
for key,value in d['arguments'].items():
 for old,new in mapping.items():value=value.replace(old,new)
 assert '{{'not in value,(key,value)
 args.extend([key,value])
raise SystemExit(subprocess.run([sys.executable,str(ROOT/d['helper']),*args]).returncode)
