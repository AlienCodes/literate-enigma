"""Original standard Git first choice for exact book60/source32; same frozen qualified payload."""
from pathlib import Path
import hashlib,json,os,signal,subprocess,sys,time
R=Path(__file__).resolve().parent;B=R.parent
pins=json.loads((R/'FROZEN-BOOK60-ORIGINAL-GIT-INPUT-CONTROL-PINS.json').read_bytes());W=Path(pins['work_dir'])
budget=R/'ACTUAL-BOOK60-MATURE-GIT-UNIQUE-BUDGET.json'
assert hashlib.sha256(budget.read_bytes()).hexdigest()=='3184804c33fbe744f71ce6302977d102b67cd71b4928960980ac266f661cdbf7'
bp=json.loads(budget.read_bytes());assert bp['engineering_budget_2x_loose_plus64MiB']==261668864
assert not any(W.glob('streaming-attempt-*')), 'Original standardGit is first choice, no stopped API attempt here'
assert not (W/'assets.git').exists() and not (W/'asset-local.json').exists()
for name,key in [('prepared-archive.json','prepared_sha256'),('payload-file-index.json','index_sha256')]:assert hashlib.sha256((W/name).read_bytes()).hexdigest()==pins[key]
assert hashlib.sha256(Path(pins['handoff']).read_bytes()).hexdigest()==pins['handoff_sha256']
refs=[('alienalgorithm/postgraduate-vocabulary','main','f37464292db767da09844ad6b602c7c94619a401'),('AlienCodes/literate-enigma','codex/all-deliverables-20261113','f385c0d650221af066800d6dc1a07afa846fa518'),('AlienCodes/literate-enigma','master','6355a02864ebae616b693200d9d26f74f5da80e9')]
def readrefs():
 out={}
 for repo,branch,expected in refs:
  found=subprocess.check_output(['gh','api','repos/'+repo+'/git/ref/heads/'+branch,'--jq','.object.sha'],text=True).strip();assert found==expected;out[repo+':'+branch]=found
 return out
def free():
 s=os.statvfs('/workspace');return s.f_bavail*s.f_frsize
protected=readrefs();start=free();required=419430400+261668864+40*1024*1024
assert start>=required,'Keep original400MiB plus measured Git budget and buddy8MiB+misc32MiB'
observations=[];phases=[];tripped=False
for role,repo in [('primary','alienalgorithm/postgraduate-vocabulary'),('backup','AlienCodes/literate-enigma')]:
 with (W/('assets-'+role+'-original-Git-first-choice.log')).open('x')as log:
  p=subprocess.Popen([sys.executable,str(R/'archive_batch.py'),'push','--work-dir',str(W),'--repo',repo],stdout=log,stderr=subprocess.STDOUT,start_new_session=True,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1','TMPDIR':str(R)})
  while p.poll()is None:
   n=free();observations.append(n)
   if n<419430400:tripped=True;os.killpg(p.pid,signal.SIGTERM);break
   time.sleep(.5)
  rc=p.wait();phases.append({'role':role,'exit_code':rc})
  assert rc==0 and not tripped,'Inspect actual original Git partial state; do not retry blindly'
 local=json.loads((W/'asset-local.json').read_bytes())
 assert local['root_tree']=='876e67e39a1831dff5ac2f03620bec7a4b6280da','Same immutable frozen payload root required'
 assert hashlib.sha256((W/'prepared-archive.json').read_bytes()).hexdigest()==pins['prepared_sha256']
 assert hashlib.sha256((W/'payload-file-index.json').read_bytes()).hexdigest()==pins['index_sha256']
assert readrefs()==protected
proof={'kind':'actual-original-standard-Git-dual-transport-first-choice-no-large-JSON-POST','frozen_H_prepared_index_unchanged':True,'same_frozen_payload_root':'876e67e39a1831dff5ac2f03620bec7a4b6280da','actual_asset_commit':local['asset_commit'],'phases':phases,'available_before':start,'measured_engineering_Git_allowance':261668864,'buddy_metadata_and_misc_allowance':40*1024*1024,'original_reserve_unchanged':419430400,'minimum_0p5s_observed':min(observations),'samples':len(observations),'sampled_not_continuous_peak_claim':True,'original400_guard_tripped':tripped,'available_after':free(),'no_large_ZIP_JSON_POST_attempted':True,'all_original_frozen_inputs_preserved':True,'canonical_refs_unchanged':protected,'READY_and_current_not_yet_claimed':True}
p=R/'ACTUAL-BOOK60-ORIGINAL-GIT-DUAL-TRANSPORT-AND-BUDGET.json';p.write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps({'proof':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'asset_commit':local['asset_commit'],'minimum_observed':proof['minimum_0p5s_observed'],'no_current_change':True}),flush=True)
