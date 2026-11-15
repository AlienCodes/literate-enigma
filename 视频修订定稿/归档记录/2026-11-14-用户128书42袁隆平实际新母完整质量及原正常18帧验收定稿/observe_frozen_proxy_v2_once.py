"""Observe an approved a0ba main call; add no requests and re-raise its same exception."""
import argparse,hashlib,importlib.util,json,re,sys
from pathlib import Path
MODULE_SHA='a0ba64b6b96c7f08796c7b05feba83e311236f43361bfb7a5df64444a9cb3714'
STATUS=re.compile(r'^(?:Git API (?:GET|POST) failed status |Blob POST failed status )([1-5][0-9]{2}); no ref progression$')
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def safe_chain(error,guard_type):
 rows=[];seen=set()
 while error is not None and id(error)not in seen and len(rows)<8:
  seen.add(id(error));status=None
  if isinstance(error,guard_type):
   match=STATUS.fullmatch(str(error))
   if match:status=int(match.group(1))
  rows.append({'class':type(error).__name__,'HTTP_status_from_exact_owned_template':status})
  error=error.__context__
 return rows
def safe_stage(stage):
 if not isinstance(stage,dict):return None
 method=stage.get('method');endpoint=stage.get('git_endpoint');result={}
 if method in {'GET','POST'}:result['method']=method
 if isinstance(endpoint,str):
  for prefix in ['git/blobs','git/trees','git/commits','git/refs','git/ref/heads']:
   if endpoint==prefix or endpoint.startswith(prefix+'/'):
    result['Git_endpoint_category']=prefix;break
 sha=stage.get('expected_git_blob_sha')
 if isinstance(sha,str)and re.fullmatch('[0-9a-f]{40}',sha):result['expected_git_blob_sha']=sha
 return result or None
def main():
 p=argparse.ArgumentParser();p.add_argument('--module',required=True);p.add_argument('--receipt',required=True);p.add_argument('module_args',nargs=argparse.REMAINDER);a=p.parse_args()
 module=Path(a.module).resolve();receipt=Path(a.receipt).resolve();assert digest(module)==MODULE_SHA
 assert receipt.parent==module.parent and receipt.name.startswith('streaming-observer-')and not receipt.exists()
 args=a.module_args[1:]if a.module_args[:1]==['--']else a.module_args
 def value(name):return args[args.index(name)+1]
 w=Path(value('--work-dir')).resolve();assert w.parent==module.parent
 approval=json.loads(Path(value('--approval')).read_text());assert approval['safe_exception_observer_sha256']==digest(__file__)
 spec=importlib.util.spec_from_file_location('approved_source48_proxy_v2_runtime',module);m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m)
 before={d.name for d in w.glob('streaming-attempt-*')};sys.argv=[str(module),*args]
 def write(result):
  with receipt.open('x')as f:json.dump(result,f,indent=2);f.write('\n')
 base={'kind':'safe-frozen-proxy-v2-one-call-observer','module_sha256':MODULE_SHA,'observer_sha256':digest(__file__),'observer_adds_no_network_request_or_retry':True,'arbitrary_exception_text_URL_token_response_not_recorded':True}
 try:m.main()
 except Exception as error:
  try:
   stage=None
   for d in sorted(w.glob('streaming-attempt-*')):
    if d.name not in before and (d/'stopped-not-READY.json').exists():stage=safe_stage(json.loads((d/'stopped-not-READY.json').read_text()).get('safe_Git_stage'))
   write({**base,'original_call_failed':True,'safe_exception_chain':safe_chain(error,m.GuardError),'safe_stage':stage,'same_original_exception_reraised':True})
  except Exception:pass  # Observer read/write failure must not replace the actual exception.
  raise
 else:
  try:write({**base,'original_call_failed':False,'READY_created_by_observer':False})
  except OSError:pass
if __name__=='__main__':main()
