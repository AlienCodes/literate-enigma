from pathlib import Path
import hashlib,json,os,subprocess,sys
N=Path(__file__).resolve().parent;ROOT=Path(os.environ['GITHUB_WORKSPACE']);M=Path(os.environ['RUNNER_TEMP'])/'completion-machine';T=ROOT/'official-main/视频/工具'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
EXPECTED_ROOT_SHA='d6ef92426f4589f0b6301566d7ebc1a03433c65256ac78bad32ad6ce5a9d3b12';EXPECTED_HELPER_SHA='5736c5e2a97fafeb1bf1e4007873d0b2fab866e9e516d2939664d9edf944090d';EXPECTED_PROFILE_SHA='f9edf45f39fa96f32bf8ded014049a456175d73e27ea7d4e3dd00be43eb24e5a';EXPECTED_ARGV_SHA='abab6f4c6bfb1017036d40efc920c3abc8c84180b6a8ffcd82634ec02eb38dd2'
assert sha(N/'root-actual-whole-observer-code-adoption.json')==EXPECTED_ROOT_SHA
assert sha(N/'observe68_strict_cached_baseline_and_selected_whole.py')==EXPECTED_HELPER_SHA and sha(N/'source68-strict-cached-whole-profile.json')==EXPECTED_PROFILE_SHA and sha(N/'native-arguments.json')==EXPECTED_ARGV_SHA
mapping={'{{TOOLS}}':str(T),'{{VIDEO_ROOT}}':str(M),'{{GITHUB_WORKSPACE}}':str(ROOT),'{{ACTUAL_ROOT_EXECUTION_ADOPTION_JSON}}':str(N/'root-actual-whole-observer-code-adoption.json'),'{{ACTUAL_ROOT_EXECUTION_ADOPTION_FULLSHA}}':EXPECTED_ROOT_SHA,'{{GITHUB_OUTPUT}}':os.environ['GITHUB_OUTPUT']}
d=json.loads((N/'native-arguments.json').read_text());args=[]
for key,value in d['arguments'].items():
 for old,new in mapping.items():value=value.replace(old,new)
 assert '{{'not in value,(key,value)
 args.extend([key,value])
raise SystemExit(subprocess.run([sys.executable,str(ROOT/d['helper']),*args]).returncode)
