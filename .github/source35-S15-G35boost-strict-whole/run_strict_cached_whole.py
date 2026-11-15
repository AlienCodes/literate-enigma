from pathlib import Path
import hashlib,json,os,subprocess,sys
N=Path(__file__).resolve().parent;ROOT=Path(os.environ['GITHUB_WORKSPACE']);M=Path(os.environ['RUNNER_TEMP'])/'completion-machine';T=ROOT/'official-main/视频/工具'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
EXPECTED_ROOT_SHA='178146d9fe6df642a6f8ff0e2a678719b424bd03a958a5b08267d0d0e2107ae2';EXPECTED_HELPER_SHA='dd3d33988871e18c0e0937c496333e6844ab241f3b251f669075082cc2e6a19d';EXPECTED_PROFILE_SHA='6c4d09e107672d3dff97c7c93204bd726c2b7ff904b230125cf09ef5dc4df017';EXPECTED_ARGV_SHA='f05b19a9d6a5fb720400a545a15d5e63c015e9fbb11f1e39206b034b05500b6f'
assert sha(N/'root-actual-whole-observer-code-adoption.json')==EXPECTED_ROOT_SHA
assert sha(N/'observe35_strict_cached_baseline_and_selected_whole.py')==EXPECTED_HELPER_SHA and sha(N/'source35-strict-cached-whole-profile.json')==EXPECTED_PROFILE_SHA and sha(N/'native-arguments.json')==EXPECTED_ARGV_SHA
mapping={'{{TOOLS}}':str(T),'{{VIDEO_ROOT}}':str(M),'{{GITHUB_WORKSPACE}}':str(ROOT),'{{ACTUAL_ROOT_EXECUTION_ADOPTION_JSON}}':str(N/'root-actual-whole-observer-code-adoption.json'),'{{ACTUAL_ROOT_EXECUTION_ADOPTION_FULLSHA}}':EXPECTED_ROOT_SHA,'{{GITHUB_OUTPUT}}':os.environ['GITHUB_OUTPUT']}
d=json.loads((N/'native-arguments.json').read_text());args=[]
for key,value in d['arguments'].items():
 for old,new in mapping.items():value=value.replace(old,new)
 assert '{{'not in value,(key,value)
 args.extend([key,value])
raise SystemExit(subprocess.run([sys.executable,str(ROOT/d['helper']),*args]).returncode)
