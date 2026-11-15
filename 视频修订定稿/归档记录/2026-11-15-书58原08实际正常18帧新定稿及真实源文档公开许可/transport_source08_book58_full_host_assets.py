"""Original standard Git after one stopped large-blob JSON POST; same frozen payload."""
from pathlib import Path
import hashlib,json,os,signal,subprocess,sys,time
R=Path(__file__).resolve().parent;B=R.parent
pins=json.loads((R/'FROZEN-BOOK58-STREAM-INPUT-CONTROL-PINS.json').read_bytes());W=Path(pins['work_dir'])
budget=R/'ACTUAL-BOOK58-MATURE-GIT-UNIQUE-BUDGET-AFTER-422.json'
assert hashlib.sha256(budget.read_bytes()).hexdigest()=='566199147d5db5b0622b8324c7477db4e424c28abb955f0280083c83ad7b6479'
bp=json.loads(budget.read_bytes());assert bp['engineering_budget_2x_loose_plus64MiB']==268017664
assert json.loads((R/'ACTUAL-READONLY-NATIVE-ZIP-BLOB-AFTER-FIRST422.json').read_bytes())['actual_http_status']==404
assert not (W/'assets.git').exists() and not (W/'asset-local.json').exists()
for name,key in [('prepared-archive.json','prepared_sha256'),('payload-file-index.json','index_sha256')]:assert hashlib.sha256((W/name).read_bytes()).hexdigest()==pins[key]
assert hashlib.sha256(Path(pins['handoff']).read_bytes()).hexdigest()==pins['handoff_sha256']
refs=[('alienalgorithm/postgraduate-vocabulary','main','9e94f52a5b46b0d3a629ebf1b8dccbca46e14d41'),('AlienCodes/literate-enigma','codex/all-deliverables-20261113','6a48d420a6d36c164f1a746fec3c9232d33d5182'),('AlienCodes/literate-enigma','master','6355a02864ebae616b693200d9d26f74f5da80e9')]
def readrefs():
 out={}
 for repo,branch,expected in refs:
  found=subprocess.check_output(['gh','api','repos/'+repo+'/git/ref/heads/'+branch,'--jq','.object.sha'],text=True).strip();assert found==expected;out[repo+':'+branch]=found
 return out
def free():
 s=os.statvfs('/workspace');return s.f_bavail*s.f_frsize
protected=readrefs();start=free();required=419430400+268017664+40*1024*1024
assert start>=required,'Keep original400MiB plus measured Git budget and buddy8MiB+misc32MiB'
observations=[];phases=[];tripped=False
for role,repo in [('primary','alienalgorithm/postgraduate-vocabulary'),('backup','AlienCodes/literate-enigma')]:
 with (W/('assets-'+role+'-original-Git-after422.log')).open('x')as log:
  p=subprocess.Popen([sys.executable,str(R/'archive_batch.py'),'push','--work-dir',str(W),'--repo',repo],stdout=log,stderr=subprocess.STDOUT,start_new_session=True,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1','TMPDIR':str(R)})
  while p.poll()is None:
   n=free();observations.append(n)
   if n<419430400:tripped=True;os.killpg(p.pid,signal.SIGTERM);break
   time.sleep(.5)
  rc=p.wait();phases.append({'role':role,'exit_code':rc})
  assert rc==0 and not tripped,'Inspect actual original Git partial state; do not retry blindly'
 local=json.loads((W/'asset-local.json').read_bytes())
 assert local['root_tree']=='0a24864dda8b64eba415e4104d0a58a8edfcd1d5','Same immutable frozen payload root required'
 assert hashlib.sha256((W/'prepared-archive.json').read_bytes()).hexdigest()==pins['prepared_sha256']
 assert hashlib.sha256((W/'payload-file-index.json').read_bytes()).hexdigest()==pins['index_sha256']
assert readrefs()==protected
proof={'kind':'actual-original-standard-Git-dual-transport-after-one-stopped422-large-JSON-post','frozen_H_prepared_index_unchanged':True,'same_frozen_payload_root':'0a24864dda8b64eba415e4104d0a58a8edfcd1d5','actual_asset_commit':local['asset_commit'],'phases':phases,'available_before':start,'measured_engineering_Git_allowance':268017664,'buddy_metadata_and_misc_allowance':40*1024*1024,'original_reserve_unchanged':419430400,'minimum_0p5s_observed':min(observations),'samples':len(observations),'sampled_not_continuous_peak_claim':True,'original400_guard_tripped':tripped,'available_after':free(),'no_large_ZIP_JSON_POST_retry':True,'first_API_failure_and_all_old_inputs_preserved':True,'canonical_refs_unchanged':protected,'READY_and_current_not_yet_claimed':True}
p=R/'ACTUAL-BOOK58-ORIGINAL-GIT-DUAL-TRANSPORT-AND-BUDGET-AFTER422.json';p.write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps({'proof':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'asset_commit':local['asset_commit'],'minimum_observed':proof['minimum_0p5s_observed'],'no_current_change':True}),flush=True)
