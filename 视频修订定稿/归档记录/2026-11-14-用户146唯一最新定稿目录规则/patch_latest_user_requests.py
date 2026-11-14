"""Append London120/121 scope to the actual serving ledger; no media changes."""
from pathlib import Path
import base64,hashlib,json,subprocess,urllib.request,urllib.parse,urllib.error
R=Path(__file__).parent
def load(p):return json.loads(p.read_text())
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
import sys
from copy import deepcopy
patch=load(Path(sys.argv[1]));tag=patch['tag'];assert tag.replace('-','').isalnum()
state=load(R/'CURRENT-ARCHIVE-STATE.json');previous=(R/'latest_requests.json').read_bytes();a=json.loads(previous);b=deepcopy(a);rows={x['source_id']:x for x in b['articles']};changed=set()
for change in patch['updates']:
 sid=change['source_id'];entry=rows[sid];changed.add(sid)
 ids=list(entry['newest_user_revision_records']);hashes=dict(entry.get('user_request_SHA256',{}))
 for record in change['records']:
  p=Path(record['path']);raw=p.read_bytes();assert len(raw)==record['bytes']and hashlib.sha256(raw).hexdigest()==record['sha256'];user=json.loads(raw);assert user['author']=='user'and user['source_id']==sid
  if record['id']not in ids:ids.append(record['id'])
  hashes[record['id']]=record['sha256']
  if record['id']not in b['authority_records']:b['authority_records'].append(record['id'])
 if change.get('finalization_authority'):
  assert change['finalization_authority']in hashes
 entry.update(newest_user_revision_records=sorted(ids,key=int),user_request_SHA256=hashes,latest_finalization_authority=change.get('finalization_authority'),final_4K_generation_authorized=change['final_4K_generation_authorized'],status=change['status'],latest_requested_revision_complete=False,actual_complete_validation_passed=False,actual_dual_permanent_archive_passed=False)
 entry.pop('latest_revision_final',None)
 if 'source_and_GEN_MD'in entry:entry['previous_qualified_source_and_GEN_MD']=entry.pop('source_and_GEN_MD')
 if 'extra_scope'in change:entry['latest_pending_scope']=change['extra_scope']
for record in patch.get('global_records',[]):
 raw=Path(record['path']).read_bytes();assert len(raw)==record['bytes']and hashlib.sha256(raw).hexdigest()==record['sha256'];user=json.loads(raw);assert user['author']=='user'and user['scope']=='global'and 'source_id'not in user
 if record['id']not in b['authority_records']:b['authority_records'].append(record['id'])
 b.setdefault('global_user_rule_records',{})[record['id']]={'sha256':record['sha256'],'kind':user['kind'],'no_new_article_finalization_authority':True}
assert all(x==y for x,y in zip(a['articles'],b['articles'])if x['source_id']not in changed)
b['latest_requested_revision_completed_count']=sum(x['latest_requested_revision_complete']for x in b['articles']);b['all70_latest_complete']=all(x['latest_requested_revision_complete']for x in b['articles'])
new=(json.dumps(b,ensure_ascii=False,indent=2)+'\n').encode()
token=subprocess.check_output(['gh','auth','token'],text=True).strip()
def api(repo,path,method='GET',data=None):
 q=urllib.request.Request('https://api.github.com/repos/'+repo+'/'+urllib.parse.quote(path,safe='/?=&%'),data=None if data is None else json.dumps(data).encode(),method=method,headers={'Authorization':'Bearer '+token,'Accept':'application/vnd.github+json','Content-Type':'application/json'})
 try:
  with urllib.request.urlopen(q,timeout=90)as x:return json.loads(x.read())
 except urllib.error.HTTPError as e:
  body=e.read().decode();save(R/('latest-'+tag+'-'+repo.split('/')[0]+'-HTTP-error.json'),{'path':path,'method':method,'status':e.code,'body':body})
  if e.code==422 and path=='git/trees'and method=='POST'and 'timed out'in body and all('sha'in x and '/'not in x['path']for x in data['tree']):
   items=data['tree'];raw=b''.join((str(int(x['mode']))+' '+x['path']).encode()+b'\0'+bytes.fromhex(x['sha'])for x in sorted(items,key=lambda x:(x['path']+('/'if x['type']=='tree'else'')).encode()));sha=hashlib.sha1(b'tree '+str(len(raw)).encode()+b'\0'+raw).hexdigest();got=api(repo,'git/trees/'+sha);assert {(x['path'],x['mode'],x['type'],x['sha'])for x in items}=={(x['path'],x['mode'],x['type'],x['sha'])for x in got['tree']};return got
  raise
def tree(repo,sha,recursive=False):
 x=api(repo,'git/trees/'+sha+('?recursive=1'if recursive else''));assert not x.get('truncated');return {v['path']:v for v in x['tree']}
def rows(t):return [{k:r[k]for k in ['path','mode','type','sha']}for r in t.values()]
B=Path('/workspace/work/video-archive-batches-20261114');sys.path.insert(0,str(B));inv=load(Path(state['actual_inventory']));policy_active='latest_final_directory_policy'in inv;finals={}
if policy_active:
 import build_final_alias_plan as aliases
 import final_alias_git
 cs=state['final_alias_catalog'];cb=Path(cs['path']).read_bytes();assert len(cb)==cs['bytes']and hashlib.sha256(cb).hexdigest()==cs['sha256'];catalog=json.loads(cb)
prepared=[]
for role,repo,branch,parent in [('primary','alienalgorithm/postgraduate-vocabulary','main',state['primary_main']),('backup','AlienCodes/literate-enigma','codex/all-deliverables-20261113',state['backup_head'])]:
 assert api(repo,'git/ref/heads/'+branch)['object']['sha']==parent;rt=tree(repo,api(repo,'git/commits/'+parent)['tree']['sha']);vt=tree(repo,rt['视频修订定稿']['sha']);assert rt['视频修订定稿']['sha']==state['video_subtree'];assert base64.b64decode(api(repo,'git/blobs/'+vt['latest_requests.json']['sha'])['content'])==previous
 nv=dict(vt)
 if policy_active:
  full=tree(repo,rt['视频修订定稿']['sha'],True);final_alias_git.assert_existing_final_matches(inv,full,catalog,latest_requests=a);active_plan=aliases.build(inv,full,catalog,latest_requests=b);finals[role]=final_alias_git.create_final_tree(api,repo,active_plan);nv['最终定稿']={'path':'最终定稿','mode':'040000','type':'tree','sha':finals[role]['final_tree_sha']}
 bs=api(repo,'git/blobs','POST',{'encoding':'base64','content':base64.b64encode(new).decode()})['sha'];nv['latest_requests.json']={'path':'latest_requests.json','mode':'100644','type':'blob','sha':bs};vsha=api(repo,'git/trees','POST',{'tree':rows(nv)})['sha'];nr=dict(rt);nr['视频修订定稿']={'path':'视频修订定稿','mode':'040000','type':'tree','sha':vsha};rsha=api(repo,'git/trees','POST',{'tree':rows(nr)})['sha'];commit=api(repo,'git/commits','POST',{'message':patch['message']+' [skip ci]','tree':rsha,'parents':[parent]})['sha'];prepared.append((role,repo,branch,parent,commit,vsha,rsha,rt,vt,bs))
assert len({r[5]for r in prepared})==1
out=[]
for role,repo,branch,parent,commit,vsha,rsha,rt,vt,bs in prepared:
 assert api(repo,'git/ref/heads/'+branch)['object']['sha']==parent;api(repo,'git/refs/heads/'+branch,'PATCH',{'sha':commit,'force':False});assert api(repo,'git/ref/heads/'+branch)['object']['sha']==commit
 rr=tree(repo,rsha);vv=tree(repo,vsha);assert {k:r['sha']for k,r in rt.items()if k!='视频修订定稿'}=={k:r['sha']for k,r in rr.items()if k!='视频修订定稿'};assert {k:r['sha']for k,r in vt.items()if k not in ({'latest_requests.json','最终定稿'}if policy_active else{'latest_requests.json'})}=={k:r['sha']for k,r in vv.items()if k not in ({'latest_requests.json','最终定稿'}if policy_active else{'latest_requests.json'})};assert base64.b64decode(api(repo,'git/blobs/'+bs)['content'])==new
 if policy_active:assert vv['最终定稿']['sha']==finals[role]['final_tree_sha']
 assert api('AlienCodes/literate-enigma','git/ref/heads/master')['object']['sha']=='6355a02864ebae616b693200d9d26f74f5da80e9';out.append({'role':role,'repository':repo,'branch':branch,'parent':parent,'commit':commit,'video_subtree':vsha,'registry_git_blob':bs,'latest_final_directory':finals.get(role)})
save(R/('actual-latest-requests-'+tag+'-dual-closure.json'),{'kind':'actual-public-latest-user-request-pending-scope-only-update','archives':out,'only_specified_source_request_scopes_changed':sorted(changed),'original_media_accepted_index_history_QA_PDF_master_unchanged':True,'latest_directory_refiltered_same_commit':policy_active,'actual_full_blob_readbacks':2})
state.update(primary_main=out[0]['commit'],backup_head=out[1]['commit'],video_subtree=out[0]['video_subtree']);
if policy_active:state.update(final_directory=finals['primary'],last_final_directory_receipt=str(R/('actual-latest-requests-'+tag+'-dual-closure.json')))
save(R/'CURRENT-ARCHIVE-STATE.json',state);(R/'latest_requests.json').write_bytes(new);print(json.dumps(out),flush=True)
