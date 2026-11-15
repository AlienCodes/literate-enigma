from pathlib import Path
import hashlib,json,os,subprocess,sys
N=Path(__file__).resolve().parent;ROOT=Path(os.environ['GITHUB_WORKSPACE']);M=Path(os.environ['RUNNER_TEMP'])/'completion-machine';T=ROOT/'official-main/视频/工具'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
EXPECTED_ROOT_SHA='21ee0326f6fa51ced831c023c0b1a5e1e380a3e0f1cd0180cba6c4ce12741d4d';EXPECTED_HELPER_SHA='cce02596ed63cb79753513117130bf5872cd77b73cb88a6b1e52e4c718a93397';EXPECTED_PROFILE_SHA='9ca186322f08128addd7a87f8e0423ceac224705e6df2ea5d291394cb59eaa73';EXPECTED_ARGV_SHA='fc074a518f0f8b0484191690e0c2e280431714f7354595b650df556be938e684'
assert sha(N/'onlyS16-gain-derived-execution-binding.json')==EXPECTED_ROOT_SHA
assert sha(N/'observe23_onlyS16_minus0p2_cachedwhole_and_original_LQ.py')==EXPECTED_HELPER_SHA and sha(N/'source23-onlyS16-gain-LQ-profile.json')==EXPECTED_PROFILE_SHA and sha(N/'native-arguments.json')==EXPECTED_ARGV_SHA
mapping={'{{TOOLS}}':str(T),'{{VIDEO_ROOT}}':str(M),'{{GITHUB_WORKSPACE}}':str(ROOT),'{{ACTUAL_ROOT_EXECUTION_ADOPTION_JSON}}':str(N/'onlyS16-gain-derived-execution-binding.json'),'{{ACTUAL_ROOT_EXECUTION_ADOPTION_FULLSHA}}':EXPECTED_ROOT_SHA,'{{GITHUB_OUTPUT}}':os.environ['GITHUB_OUTPUT']}
d=json.loads((N/'native-arguments.json').read_text());args=[]
for key,value in d['arguments'].items():
 for old,new in mapping.items():value=value.replace(old,new)
 assert '{{'not in value,(key,value)
 args.extend([key,value])
raise SystemExit(subprocess.run([sys.executable,str(ROOT/d['helper']),*args]).returncode)
