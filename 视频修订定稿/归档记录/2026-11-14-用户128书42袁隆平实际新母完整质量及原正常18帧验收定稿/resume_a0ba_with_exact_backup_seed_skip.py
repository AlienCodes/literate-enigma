"""One approved a0ba call: only backup ZIP56565 uses proven-existing-blob route.

Does not call a skipped POST successful. Original verify_blob immediately afterward
still performs the mandatory full raw readback; every other original guard remains.
"""
from pathlib import Path
import argparse,hashlib,importlib.util,json,sys
from observe_frozen_proxy_v2_once import safe_chain,safe_stage
CODE='a0ba64b6b96c7f08796c7b05feba83e311236f43361bfb7a5df64444a9cb3714';BLOB='56565c3aca8bc6093423e0a19172aaefe42c924a';ZIP='51ba30fa621945d4134116e08fde5b12cd12502a8c1d81439dc1ee104557fc2f';SIZE=41614365;REPO='AlienCodes/literate-enigma'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def install_exact_skip(module,record):
 original=module.GitDataClient.post_blob
 def post(self,repo,blob):
  if repo==REPO and blob.git_sha==BLOB:
   module.require(blob.size==SIZE and blob.sha256==ZIP,'Exact seed ZIP bytes/SHA scope mismatch')
   record({'repository':repo,'git_blob_sha':BLOB,'bytes':SIZE,'sha256':ZIP,'route':'existing-seed-blob-POST-not-executed-or-claimed','following_original_verify_blob_is_still_mandatory':True});return
  return original(self,repo,blob)
 module.GitDataClient.post_blob=post
 return original
def main():
 p=argparse.ArgumentParser();p.add_argument('--module',required=True);p.add_argument('--seed-proof',required=True);p.add_argument('--seed-proof-sha256',required=True);p.add_argument('--receipt',required=True);p.add_argument('module_args',nargs=argparse.REMAINDER);a=p.parse_args();file=Path(a.module).resolve();out=Path(a.receipt).resolve();assert sha(file)==CODE and out.parent==file.parent and not out.exists()
 args=a.module_args[1:]if a.module_args[:1]==['--']else a.module_args
 def value(k):return args[args.index(k)+1]
 w=Path(value('--work-dir')).resolve();assert w.parent==file.parent
 approval=json.loads(Path(value('--approval')).read_text());assert approval['exact_backup_seed_skip_wrapper_sha256']==sha(__file__)and approval['approved_seed_proof_sha256']==a.seed_proof_sha256
 assert sha(a.seed_proof)==a.seed_proof_sha256;proof=json.loads(Path(a.seed_proof).read_text());assert proof['repository']==REPO and proof['actual_backup_raw_HTTP_status']==200 and proof['actual_backup_raw_bytes']==SIZE and proof['actual_backup_raw_SHA256']==ZIP and proof['actual_backup_raw_Git_SHA']==BLOB
 spec=importlib.util.spec_from_file_location('exact_source48_seed_resume_runtime',file);m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m)
 token=m.subprocess.check_output(['gh','auth','token'],text=True).strip();client=m.GitDataClient(token);assert client.api(REPO,'git/ref/heads/'+proof['seed_ref'])['object']['sha']==proof['seed_commit']
 records=[];install_exact_skip(m,records.append);before={d.name for d in w.glob('streaming-attempt-*')};sys.argv=[str(file),*args]
 base={'kind':'exact-backup56565-seeded-blob-resume-not-READY','module_sha256':CODE,'wrapper_sha256':sha(__file__),'seed_proof_sha256':a.seed_proof_sha256,'only_exact_backup_one_blob_POST_route_replaced_with_proven_existing_blob':True,'original_verify_blob_raw_tree_commit_ref_and_all_control_guards_unchanged':True}
 def write(result):
  with out.open('x')as f:json.dump(result,f,indent=2);f.write('\n')
 try:m.main()
 except Exception as e:
  try:
   stage=None
   for d in sorted(w.glob('streaming-attempt-*')):
    if d.name not in before and (d/'stopped-not-READY.json').exists():stage=safe_stage(json.loads((d/'stopped-not-READY.json').read_text()).get('safe_Git_stage'))
   write({**base,'failed':True,'route_records':records,'safe_exception_chain':safe_chain(e,m.GuardError),'safe_stage':stage,'same_original_exception_reraised':True})
  except Exception:pass
  raise
 else:write({**base,'failed':False,'route_records':records,'READY_or_current_created_by_wrapper':False})
if __name__=='__main__':main()
