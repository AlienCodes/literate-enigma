from pathlib import Path
import hashlib,json,os,subprocess,sys
N=Path(__file__).resolve().parent;ROOT=Path(os.environ['GITHUB_WORKSPACE']);M=Path(os.environ['RUNNER_TEMP'])/'completion-machine';T=ROOT/'official-main/视频/工具'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
EXPECTED_ROOT_SHA='04323aad680bb207ffeca5fbdfb26eb5b03921c60133a2a74714bb44339ecf95';EXPECTED_HELPER_SHA='f1be19bf37a450332fd55f99dd55f2e1d74b92a3fb519c867cb6cac8adf5e4a2';EXPECTED_PROFILE_SHA='7e5cb923c53fba859718e37d254f39c26dfd348cecb86e007339f19a3884fb85';EXPECTED_ARGV_SHA='88554025eb785762955d3175cf0671afd1d721d2ad0d4e7d192de84c149a6296'
assert sha(N/'root-actual-whole-observer-code-adoption.json')==EXPECTED_ROOT_SHA
assert sha(N/'observe35_strict_cached_baseline_and_selected_whole.py')==EXPECTED_HELPER_SHA and sha(N/'source35-strict-cached-whole-profile.json')==EXPECTED_PROFILE_SHA and sha(N/'native-arguments.json')==EXPECTED_ARGV_SHA
mapping={'{{TOOLS}}':str(T),'{{VIDEO_ROOT}}':str(M),'{{GITHUB_WORKSPACE}}':str(ROOT),'{{ACTUAL_ROOT_EXECUTION_ADOPTION_JSON}}':str(N/'root-actual-whole-observer-code-adoption.json'),'{{ACTUAL_ROOT_EXECUTION_ADOPTION_FULLSHA}}':EXPECTED_ROOT_SHA,'{{GITHUB_OUTPUT}}':os.environ['GITHUB_OUTPUT']}
d=json.loads((N/'native-arguments.json').read_text());args=[]
for key,value in d['arguments'].items():
 for old,new in mapping.items():value=value.replace(old,new)
 assert '{{'not in value,(key,value)
 args.extend([key,value])
raise SystemExit(subprocess.run([sys.executable,str(ROOT/d['helper']),*args]).returncode)
