"""Replicate exact frozen asset Git objects using GitHub's normal REST Git-data API.

Fallback only for an isolated assets branch after git-receive-pack transport
stalls. Original blobs, trees and commits must reproduce the primary SHA exactly;
otherwise no ref is written. Never touches main, master, production inputs or QA.
"""
import argparse,base64,datetime,hashlib,json,pathlib,re,subprocess,time,urllib.error,urllib.request
p=argparse.ArgumentParser();p.add_argument('--work-dir',required=True);a=p.parse_args();W=pathlib.Path(a.work_dir).resolve();R='AlienCodes/literate-enigma';G=W/'assets.git';PRIMARY=json.loads((W/'assets-primary.json').read_text());LOCAL=json.loads((W/'asset-local.json').read_text());META=json.loads((W/'prepared-archive.json').read_text());BRANCH=LOCAL['asset_branch'];MASTER='6355a02864ebae616b693200d9d26f74f5da80e9'
assert W.parent==pathlib.Path(__file__).resolve().parent and BRANCH.startswith('codex/passed4k-')
token=subprocess.check_output(['gh','auth','token'],text=True).strip();events=[];receipt=W/'REST-GIT-DATA-REPLICATION.json'
if receipt.exists():
 previous=receipt.read_bytes();hist=W/'rest-transfer-history';hist.mkdir(exist_ok=True);(hist/(hashlib.sha256(previous).hexdigest()+'.json')).write_bytes(previous);events=json.loads(previous).get('events',[]);events.append({'stage':'resume_same_immutable_objects_after_transient_HTTP_error','prior_receipt_sha256':hashlib.sha256(previous).hexdigest(),'program_sha256':hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest()})
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def save(status):receipt.write_text(json.dumps({'status':status,'recorded_utc':now(),'repository':R,'asset_branch':BRANCH,'expected_primary_asset_commit':LOCAL['asset_commit'],'exact_blob_tree_commit_identity_required':True,'main_master_or_source_or_quality_changes':False,'events':events},ensure_ascii=False,indent=2)+'\n')
def api(path,method='GET',data=None,missing=False):
 q=urllib.request.Request('https://api.github.com/repos/'+R+'/'+path,data=None if data is None else json.dumps(data).encode(),method=method,headers={'Authorization':'Bearer '+token,'Accept':'application/vnd.github+json','Content-Type':'application/json','X-GitHub-Api-Version':'2022-11-28'})
 for attempt in range(4):
  try:
   with urllib.request.urlopen(q,timeout=120)as r:
    raw=r.read();return json.loads(raw)if raw else {'http_status':r.status}
  except urllib.error.HTTPError as e:
   body=e.read().decode(errors='replace')
   if e.code==404 and missing:return None
   events.append({'api_path':path,'method':method,'http_status':e.code,'error_body_first_2048':body[:2048],'bounded_attempt':attempt+1});save('API_error_no_acceptance_claimed')
   if e.code in [429,500,502,503,504] and attempt<3:
    time.sleep(min(2**attempt,4));continue
   raise

def git(*args,raw=False):
 r=subprocess.check_output(['git','--git-dir='+str(G),*args]);return r if raw else r.decode().strip()

def gettree(sha,recursive=False,missing=False):
 v=api('git/trees/'+sha+('?recursive=1'if recursive else ''),missing=missing)
 if v is None:return None
 assert not v.get('truncated');return {x['path']:x for x in v['tree']}

def blobid(raw):return hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()

assert api('git/ref/heads/master')['object']['sha']==MASTER
ref=api('git/ref/heads/'+BRANCH,missing=True)
if ref is not None:assert ref['object']['sha'] in LOCAL['commits']
index=json.loads((W/'payload-file-index.json').read_text());files={}
for row in index:
 f=W/'payload'/row['repo_path'];raw=f.read_bytes();assert len(raw)==row['bytes'] and hashlib.sha256(raw).hexdigest()==row['sha256'];sha=blobid(raw);assert sha==git('rev-parse',LOCAL['asset_commit']+':'+row['repo_path']);files.setdefault(sha,(f,row))
print(json.dumps({'stage':'local112_or116_files_exactly_bound','work_dir':str(W),'files':len(index),'unique_blobs':len(files),'largest_blob':max(r['bytes']for _,r in files.values())}),flush=True)
# HEAD is standard REST discovery, with no large response body. Even reused
# objects are checked by exact tree SHA and each stored blob size after transfer.
for i,(sha,(f,row))in enumerate(files.items(),1):
 exists=api('git/blobs/'+sha,'HEAD',missing=True)
 if exists is None:
  raw=f.read_bytes();assert blobid(raw)==sha
  result=api('git/blobs','POST',{'content':base64.b64encode(raw).decode(),'encoding':'base64'});assert result['sha']==sha
  action='uploaded_exact_blob'
 else:action='existing_exact_blob'
 events.append({'stage':action,'git_blob_sha':sha,'bytes':row['bytes'],'original_sha256':row['sha256']});save('exact_objects_in_progress_no_ref_change')
 if action.startswith('uploaded') or i%20==0:print(json.dumps({'stage':action,'number':i,'unique_blobs':len(files),'bytes':row['bytes'],'git_blob_sha':sha}),flush=True)

tree_done=set()
def ensure_tree(sha):
 if sha in tree_done:return
 raw=git('ls-tree','-z',sha,raw=True);entries=[]
 for line in raw.split(b'\0'):
  if not line:continue
  spec,name=line.split(b'\t',1);mode,kind,child=spec.decode().split();name=name.decode();entries.append({'path':name,'mode':mode,'type':kind,'sha':child})
  if kind=='tree':ensure_tree(child)
  else:assert kind=='blob' and child in files
 actual=gettree(sha,missing=True)
 if actual is None:
  try:result=api('git/trees','POST',{'tree':entries});assert result['sha']==sha
  except urllib.error.HTTPError as e:
   if e.code!=422:raise
   # A timeout can leave the exact Git object present. It counts only after a
   # real GET of that known immutable SHA and exact child comparison below.
   actual=gettree(sha,missing=True)
   if actual is None:raise
  actual=gettree(sha)
 expected={v['path']:(v['mode'],v['type'],v['sha'])for v in entries};assert {n:(v['mode'],v['type'],v['sha'])for n,v in actual.items()}==expected
 tree_done.add(sha);events.append({'stage':'exact_tree_read_back','sha':sha,'entries':len(entries)});save('exact_objects_in_progress_no_ref_change')

def person(s):
 m=re.fullmatch(r'(.*) <([^<>]+)> (\d+) ([+-]\d{4})',s);assert m and m[4]=='+0000',s
 return {'name':m[1],'email':m[2],'date':datetime.datetime.fromtimestamp(int(m[3]),datetime.timezone.utc).isoformat()}
commit_done=set()
def ensure_commit(sha):
 if sha in commit_done:return
 raw=git('cat-file','commit',sha,raw=True);head,msg=raw.split(b'\n\n',1);headers=[v.decode()for v in head.splitlines()];tree=next(v[5:]for v in headers if v.startswith('tree '));parents=[v[7:]for v in headers if v.startswith('parent ')];assert all(v.split(' ',1)[0] in ['tree','parent','author','committer']for v in headers);assert all(v in LOCAL['commits']for v in parents)
 for parent in parents:ensure_commit(parent)
 ensure_tree(tree)
 actual=api('git/commits/'+sha,missing=True)
 if actual is None:
  body={'message':msg.decode(),'tree':tree,'parents':parents,'author':person(next(v[7:]for v in headers if v.startswith('author '))),'committer':person(next(v[10:]for v in headers if v.startswith('committer ')))};actual=api('git/commits','POST',body);assert actual['sha']==sha,('Commit bytes differ; no ref written',sha,actual['sha'])
 assert actual['tree']['sha']==tree and [v['sha']for v in actual['parents']]==parents
 commit_done.add(sha);events.append({'stage':'exact_commit_read_back','sha':sha,'tree':tree,'parents':parents});save('exact_objects_in_progress_no_ref_change')
for sha in LOCAL['commits']:ensure_commit(sha)
assert git('rev-parse',LOCAL['asset_commit']+'^{tree}')==LOCAL['root_tree'];assert gettree(LOCAL['root_tree'])is not None
ref=api('git/ref/heads/'+BRANCH,missing=True)
if ref is None:
 try:api('git/refs','POST',{'ref':'refs/heads/'+BRANCH,'sha':LOCAL['asset_commit']})
 except urllib.error.HTTPError as e:
  if e.code!=422:raise
  ref=api('git/ref/heads/'+BRANCH);assert ref['object']['sha'] in LOCAL['commits']
  if ref['object']['sha']!=LOCAL['asset_commit']:api('git/refs/heads/'+BRANCH,'PATCH',{'sha':LOCAL['asset_commit'],'force':False})
else:
 assert ref['object']['sha'] in LOCAL['commits']
 if ref['object']['sha']!=LOCAL['asset_commit']:api('git/refs/heads/'+BRANCH,'PATCH',{'sha':LOCAL['asset_commit'],'force':False})
assert api('git/ref/heads/'+BRANCH)['object']['sha']==LOCAL['asset_commit']
remote=gettree(PRIMARY['video_tree_sha'],True)
for row in PRIMARY['files_index']:
 rel=row['repo_path'][len(META['prefix'])+1:];r=remote[rel];assert r['sha']==row['git_blob_sha'] and r['size']==row['bytes'] and r['type']=='blob'
assert api('git/ref/heads/master')['object']['sha']==MASTER
result={**PRIMARY,'repository':R,'REST_exact_object_replication':True,'git_receive_pack_transport_recovered_without_media_changes':True,'main_or_master_changed':False,'files':len(index),'remote_asset_ref_verified':True};(W/'assets-backup.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');events.append({'stage':'exact_asset_ref_and_all_blob_sizes_read_back','asset_commit':LOCAL['asset_commit'],'video_tree_sha':PRIMARY['video_tree_sha'],'files':len(index),'master_unchanged':MASTER});save('exact_dual_repository_asset_objects_and_ref_verified');print(json.dumps({'passed':True,'repository':R,'exact_asset_commit':LOCAL['asset_commit'],'exact_video_tree_sha':PRIMARY['video_tree_sha'],'files':len(index),'next_required':'Actual complete MP4 streams in both repositories; main/backup canonical refs untouched'}),flush=True)
