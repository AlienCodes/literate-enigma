"""Retry unchanged52 plan after a pre-ref GitHub tree-registration422; log errors."""
import datetime,json,pathlib,runpy,sys,urllib.error,urllib.request
b=pathlib.Path(__file__).resolve().parent;original=urllib.request.urlopen
note={'observed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'prior_failure':'GitHub POST git/trees returned422 before any destination ref PATCH; exact phase8 branch heads checked unchanged before retry','quality_media_and_source_changes':False,'same_frozen_plan':str(b/'integration-plan52.json')}
(b/'integration52-pre-ref-HTTP422-retry.json').write_text(json.dumps(note,indent=2)+'\n')
def observe(*args,**kw):
 try:return original(*args,**kw)
 except urllib.error.HTTPError as e:
  body=e.read().decode(errors='replace');p=b/'integration52-server-HTTP-error-body.json';p.write_text(json.dumps({'status':e.code,'public_endpoint':str(e.url),'body':body},indent=2)+'\n');print('GitHub HTTP error body:',body[:2000],flush=True);raise
urllib.request.urlopen=observe;sys.argv=[str(b/'integrate_verified_batch.py'),'--plan',str(b/'integration-plan52.json'),'--execute'];runpy.run_path(str(b/'integrate_verified_batch.py'),run_name='__main__')
