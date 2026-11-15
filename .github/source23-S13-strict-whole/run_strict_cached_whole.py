from pathlib import Path
import hashlib,json,os,subprocess,sys
N=Path(__file__).resolve().parent;ROOT=Path(os.environ['GITHUB_WORKSPACE']);M=Path(os.environ['RUNNER_TEMP'])/'completion-machine';T=ROOT/'official-main/视频/工具'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
EXPECTED_ROOT_SHA='69e8be889d2765763ef13646ea171e41b8ff327ac7f739803cfe73677d8cf9b6';EXPECTED_HELPER_SHA='e769ced8eff7f83598da7cdbbdf6ca0742cfc54ce02233de8acc3d3956417226';EXPECTED_PROFILE_SHA='dd4f2d98703bacdef9e920d96d60e2c7810a730f836a93bd2d54141ed17bb227';EXPECTED_ARGV_SHA='4185af36f8481faced850ae60266d913226a380339768b7c74b21762d7fd5163'
assert sha(N/'root-actual-whole-observer-code-adoption.json')==EXPECTED_ROOT_SHA
assert sha(N/'observe23_strict_cached_baseline_and_selected_whole.py')==EXPECTED_HELPER_SHA and sha(N/'source23-strict-cached-whole-profile.json')==EXPECTED_PROFILE_SHA and sha(N/'native-arguments.json')==EXPECTED_ARGV_SHA
mapping={'{{TOOLS}}':str(T),'{{VIDEO_ROOT}}':str(M),'{{GITHUB_WORKSPACE}}':str(ROOT),'{{ACTUAL_ROOT_EXECUTION_ADOPTION_JSON}}':str(N/'root-actual-whole-observer-code-adoption.json'),'{{ACTUAL_ROOT_EXECUTION_ADOPTION_FULLSHA}}':EXPECTED_ROOT_SHA,'{{GITHUB_OUTPUT}}':os.environ['GITHUB_OUTPUT']}
d=json.loads((N/'native-arguments.json').read_text());args=[]
for key,value in d['arguments'].items():
 for old,new in mapping.items():value=value.replace(old,new)
 assert '{{'not in value,(key,value)
 args.extend([key,value])
raise SystemExit(subprocess.run([sys.executable,str(ROOT/d['helper']),*args]).returncode)
