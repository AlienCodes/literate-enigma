from pathlib import Path
import hashlib,json,os,subprocess,sys
N=Path(__file__).resolve().parent;ROOT=Path(os.environ['GITHUB_WORKSPACE']);M=Path(os.environ['RUNNER_TEMP'])/'completion-machine';T=ROOT/'official-main/视频/工具'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
EXPECTED_ROOT_SHA='922dfa8744dd02097decc611c9dab4196a37dcc84578c594b164f8c10070d781';EXPECTED_HELPER_SHA='128de00687a82daa6c784e0c7884e4c9fc48d0d4c9ef7f32ed80558f2388aede';EXPECTED_PROFILE_SHA='7c860bc890e5e88ae087b5e16b6ac9e271fea2497930898f0a70b20223fc9669';EXPECTED_ARGV_SHA='64be299c8a29f8578dd608efabcec4f1deb9bd798fb8dea9b89e9609a985d356'
assert sha(N/'root-actual-whole-observer-code-adoption.json')==EXPECTED_ROOT_SHA
assert sha(N/'observe68_strict_cached_baseline_and_selected_whole.py')==EXPECTED_HELPER_SHA and sha(N/'source68-strict-cached-whole-profile.json')==EXPECTED_PROFILE_SHA and sha(N/'native-arguments.json')==EXPECTED_ARGV_SHA
mapping={'{{TOOLS}}':str(T),'{{VIDEO_ROOT}}':str(M),'{{GITHUB_WORKSPACE}}':str(ROOT),'{{ACTUAL_ROOT_EXECUTION_ADOPTION_JSON}}':str(N/'root-actual-whole-observer-code-adoption.json'),'{{ACTUAL_ROOT_EXECUTION_ADOPTION_FULLSHA}}':EXPECTED_ROOT_SHA,'{{GITHUB_OUTPUT}}':os.environ['GITHUB_OUTPUT']}
d=json.loads((N/'native-arguments.json').read_text());args=[]
for key,value in d['arguments'].items():
 for old,new in mapping.items():value=value.replace(old,new)
 assert '{{'not in value,(key,value)
 args.extend([key,value])
raise SystemExit(subprocess.run([sys.executable,str(ROOT/d['helper']),*args]).returncode)
