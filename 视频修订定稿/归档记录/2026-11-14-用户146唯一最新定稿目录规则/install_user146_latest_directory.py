"""Atomic user146 latest-only folder and matching request/rule/index epoch."""
from pathlib import Path
from copy import deepcopy
from concurrent.futures import ThreadPoolExecutor
import base64,hashlib,json,subprocess,sys,urllib.request,urllib.parse,urllib.error
R=Path(__file__).parent;B=Path('/workspace/work/video-archive-batches-20261114');sys.path.insert(0,str(B))
import build_final_alias_plan as aliases
import final_alias_git
import latest_final_directory_policy as policy
MASTER='6355a02864ebae616b693200d9d26f74f5da80e9'
def load(p):return json.loads(Path(p).read_text())
def encode(x):return (json.dumps(x,ensure_ascii=False,indent=2)+'\n').encode()
def save(p,x):p.write_bytes(encode(x))
def digest(raw):return hashlib.sha256(raw).hexdigest()
def blob(raw):return hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
def spec(p):return {'path':str(p),'bytes':p.stat().st_size,'sha256':digest(p.read_bytes())}
state=load(R/'CURRENT-ARCHIVE-STATE.json');old_index=Path(state['actual_inventory']).read_bytes();old= json.loads(old_index);old_registry=(R/'latest_requests.json').read_bytes();oldreg=json.loads(old_registry);newreg=load(R/'user146-planned-latest_requests.json');new_registry=encode(newreg)
assert all(x==y for x,y in zip(oldreg['articles'],newreg['articles'])if x['source_id']!='40');assert newreg['latest_requested_revision_completed_count']==oldreg['latest_requested_revision_completed_count']==38
assert next(x for x in newreg['articles']if x['source_id']=='40')['latest_finalization_authority']=='144'
u=Path('/dev/shm/archive-writer-user-review-20261114/USER-REVIEW-2026-11-14-146.json');new=deepcopy(old);assert policy.KEY not in new;new[policy.KEY]=policy.activation(spec(u));new_index=encode(new);assert new['articles']==old['articles']and new['batches']==old['batches']and new['video_order_overlay']==old['video_order_overlay']
checks=load(R/'user146-actual-metadata-plan-checks.json');assert checks['legacy_no_flag_plan_entire_object_and_text_bytes_unchanged']and checks['actual_new39_final_restores_and_wrong_SHA_refused']
cs=state['final_alias_catalog'];catalog_bytes=Path(cs['path']).read_bytes();assert len(catalog_bytes)==cs['bytes']and digest(catalog_bytes)==cs['sha256'];catalog=json.loads(catalog_bytes)
records=[]
for p in [B/'latest_final_directory_policy.py',B/'build_final_alias_plan.py',B/'build_final_alias_plan-before-user146-latest-only.py',B/'final_alias_git.py',B/'final_alias_git-before-user146-latest-only.py',B/'archive_revision_policy.py',B/'archive_revision_policy-before-user146-latest-only.py',B/'integrate_verified_batch.py',B/'integrate_verified_batch-before-user146-latest-only.py',B/'latest_request_tracking.py',R/'patch_latest_user_requests.py',R/'patch_latest_user_requests-before146.py',R/'test_user146_latest_directory_plans.py',R/'user146-actual-metadata-plan-checks.json',Path(__file__),u,Path('/dev/shm/archive-writer-user-review-20261114/USER-REVIEW-2026-11-14-145.json')]:
 raw=p.read_bytes();assert digest(raw)not in {'b9a257a23820944ee95d568b67d1cd78947b1c1814bb70dc99a45871f488f778','55026ce1b7cdb7e9c1a72da2f715e3d9e6e6f45050a8ddd575dc052b09dca872','bcb37d8930d804988c95da94b9cfeaaab2c7b026df96e6e4567f9b698ce88fbf'};records.append((p.name,raw))
assert len({n for n,r in records})==len(records)
addition='''
## 2026-11-14 用户146：唯一最新定稿视频目录

唯一对外交付的最新定稿目录为 `视频修订定稿/最终定稿/视频/`，不再另建第二套latest目录。历史归档与最新版目录分别统计，不能以旧版填补待制作的最新修订。

- 以逐篇`latest_requests.json`和当前已验收行共同选择目录文件。该篇有新要求尚未完成真实完整核验及双仓保存时，立即在同次提交从最新目录排出旧accepted别名；原文件、旧行及previous_versions保留在历史归档。
- 新版真实完成后，在同一次提交更新current行、最新要求状态、目录清单与该篇唯一别名，替换或恢复该文件；最新目录不同时保留同篇旧名和新名。complete标记必须与current的asset、原路径、字节数及SHA精确相同。
- 没有该篇新pending要求的已验收current可以入选；不得把未验收或未获定稿授权的新稿当成最终版。目录README明确历史归档数与实际最新可交付数，按用户090视频顺序，不改原书序和PDF。
- 后续任何raw反馈、安装器和下载选择都使用同一个持久选择器。继续按079默认云端保存，109第38篇单独下载例外保持；0.6秒、原图2秒、简述2秒及重点词表同步继续执行，全部PDF工作继续暂停。
'''
token=subprocess.check_output(['gh','auth','token'],text=True).strip()
def api(repo,path,method='GET',data=None):
 q=urllib.request.Request('https://api.github.com/repos/'+repo+'/'+urllib.parse.quote(path,safe='/?=&%'),data=None if data is None else json.dumps(data).encode(),method=method,headers={'Authorization':'Bearer '+token,'Accept':'application/vnd.github+json','Content-Type':'application/json'})
 try:
  with urllib.request.urlopen(q,timeout=90)as r:return json.loads(r.read())
 except urllib.error.HTTPError as e:
  body=e.read().decode();save(R/('user146-'+repo.split('/')[0]+'-HTTP-error.json'),{'path':path,'method':method,'status':e.code,'body':body})
  if e.code==422 and method=='POST'and path=='git/trees'and 'timed out'in body and all('sha'in x and '/'not in x['path']for x in data['tree']):
   items=data['tree'];raw=b''.join((str(int(x['mode']))+' '+x['path']).encode()+b'\0'+bytes.fromhex(x['sha'])for x in sorted(items,key=lambda x:(x['path']+('/'if x['type']=='tree'else'')).encode()));expected=hashlib.sha1(b'tree '+str(len(raw)).encode()+b'\0'+raw).hexdigest();got=api(repo,'git/trees/'+expected);assert {(x['path'],x['mode'],x['type'],x['sha'])for x in items}=={(x['path'],x['mode'],x['type'],x['sha'])for x in got['tree']};return got
  raise
def tree(repo,sha,recursive=False):
 r=api(repo,'git/trees/'+sha+('?recursive=1'if recursive else''));assert not r.get('truncated');return {x['path']:x for x in r['tree']}
def shallow(t):return [{k:r[k]for k in ['path','mode','type','sha']}for r in t.values()]
def put(repo,raw):
 sha=api(repo,'git/blobs','POST',{'content':base64.b64encode(raw).decode(),'encoding':'base64'})['sha'];assert sha==blob(raw);return sha
def prepare(role,repo,branch,parent):
 assert api(repo,'git/ref/heads/'+branch)['object']['sha']==parent;root=tree(repo,api(repo,'git/commits/'+parent)['tree']['sha']);assert root['视频修订定稿']['sha']==state['video_subtree'];video=tree(repo,root['视频修订定稿']['sha']);full=tree(repo,root['视频修订定稿']['sha'],True)
 assert base64.b64decode(api(repo,'git/blobs/'+video['已归档视频总清单.json']['sha'])['content'])==old_index;assert base64.b64decode(api(repo,'git/blobs/'+video['latest_requests.json']['sha'])['content'])==old_registry
 final_alias_git.assert_existing_final_matches(old,full,catalog,latest_requests=oldreg);plan=aliases.build(new,full,catalog,latest_requests=newreg);directory=final_alias_git.create_final_tree(api,repo,plan);assert directory['video_count']==checks['actual_planned_latest_directory_count']
 updated={k:{n:r[n]for n in ['path','mode','type','sha']}for k,r in video.items()};docs={'已归档视频总清单.json':new_index,'latest_requests.json':new_registry,'最新定稿目录规则146.json':encode(policy.POLICY)}
 existing_rules=json.loads(base64.b64decode(api(repo,'git/blobs/'+video['最新视频选择规则.json']['sha'])['content']));existing_rules['latest_final_directory_policy']=deepcopy(policy.POLICY);existing_rules['global_all_known_issues_reaffirmation_user145_sha256']=digest(Path('/dev/shm/archive-writer-user-review-20261114/USER-REVIEW-2026-11-14-145.json').read_bytes());docs['最新视频选择规则.json']=encode(existing_rules)
 for name,raw in docs.items():updated[name]={'path':name,'mode':'100644','type':'blob','sha':put(repo,raw)}
 updated['最终定稿']={'path':'最终定稿','mode':'040000','type':'tree','sha':directory['final_tree_sha']}
 record_nodes={name:{'path':name,'mode':'100644','type':'blob','sha':put(repo,raw)}for name,raw in records};record_sha=api(repo,'git/trees','POST',{'tree':list(record_nodes.values())})['sha'];existing_records=tree(repo,video['归档记录']['sha']);record_name='2026-11-14-用户146唯一最新定稿目录规则';assert record_name not in existing_records;new_records={k:{n:r[n]for n in ['path','mode','type','sha']}for k,r in existing_records.items()};new_records[record_name]={'path':record_name,'mode':'040000','type':'tree','sha':record_sha};updated['归档记录']={'path':'归档记录','mode':'040000','type':'tree','sha':api(repo,'git/trees','POST',{'tree':list(new_records.values())})['sha']}
 vsha=api(repo,'git/trees','POST',{'tree':list(updated.values())})['sha'];old_agents=base64.b64decode(api(repo,'git/blobs/'+root['AGENTS.md']['sha'])['content']);assert addition.strip()not in old_agents.decode();agents=old_agents+addition.encode();nr={k:{n:r[n]for n in ['path','mode','type','sha']}for k,r in root.items()};nr['AGENTS.md']={'path':'AGENTS.md','mode':'100644','type':'blob','sha':put(repo,agents)};nr['视频修订定稿']={'path':'视频修订定稿','mode':'040000','type':'tree','sha':vsha};rsha=api(repo,'git/trees','POST',{'tree':list(nr.values())})['sha'];commit=api(repo,'git/commits','POST',{'message':'按用户146落实唯一最新定稿目录，待修订旧版退出，保全部原归档与090视频顺序 [skip ci]','tree':rsha,'parents':[parent]})['sha']
 return {'role':role,'repository':repo,'branch':branch,'parent':parent,'commit':commit,'video_subtree':vsha,'root_tree':rsha,'old_root':root,'old_full':full,'old_record_tree':existing_records,'directory':directory,'plan':plan,'documents':docs,'agents':agents,'record_tree':record_sha,'record_name':record_name}
assert api('AlienCodes/literate-enigma','git/ref/heads/master')['object']['sha']==MASTER
with ThreadPoolExecutor(max_workers=2)as pool:
 a=pool.submit(prepare,'primary','alienalgorithm/postgraduate-vocabulary','main',state['primary_main']);b=pool.submit(prepare,'backup','AlienCodes/literate-enigma','codex/all-deliverables-20261113',state['backup_head']);prepared=[a.result(),b.result()]
assert len({p['video_subtree']for p in prepared})==1 and len({p['directory']['final_tree_sha']for p in prepared})==1
save(R/'user146-prepared-canonical-commits.json',[{k:p[k]for k in ['role','repository','branch','parent','commit','video_subtree','root_tree','directory','record_tree']}for p in prepared])
for p in prepared:assert api(p['repository'],'git/ref/heads/'+p['branch'])['object']['sha']==p['parent']
out=[]
for p in prepared:
 repo=p['repository'];api(repo,'git/refs/heads/'+p['branch'],'PATCH',{'sha':p['commit'],'force':False});assert api(repo,'git/ref/heads/'+p['branch'])['object']['sha']==p['commit'];root=tree(repo,p['root_tree']);actual=tree(repo,p['video_subtree'],True)
 assert {k:r['sha']for k,r in p['old_root'].items()if k not in ['AGENTS.md','视频修订定稿']}=={k:r['sha']for k,r in root.items()if k not in ['AGENTS.md','视频修订定稿']}
 mutable={'已归档视频总清单.json','latest_requests.json','最新视频选择规则.json'};assert all(path in mutable or path.startswith('最终定稿/')or(actual[path]['sha']==node['sha']and actual[path]['mode']==node['mode'])for path,node in p['old_full'].items()if node['type']=='blob')
 assert final_alias_git.assert_existing_final_matches(new,actual,catalog,latest_requests=newreg)==p['directory']
 for name,raw in p['documents'].items():assert base64.b64decode(api(repo,'git/blobs/'+actual[name]['sha'])['content'])==raw
 assert base64.b64decode(api(repo,'git/blobs/'+root['AGENTS.md']['sha'])['content'])==p['agents']
 rtree=tree(repo,p['record_tree']);assert len(rtree)==len(records)
 for name,raw in records:assert rtree[name]['sha']==blob(raw)and rtree[name]['size']==len(raw)and rtree[name]['mode']=='100644'
 assert api('AlienCodes/literate-enigma','git/ref/heads/master')['object']['sha']==MASTER
 out.append({k:p[k]for k in ['role','repository','branch','parent','commit','video_subtree','root_tree','directory','record_tree']})
summary={'kind':'actual-user146-unique-latest-final-directory-dual-closure','archives':out,'archived_passed_count':60,'latest_deliverable_video_count':prepared[0]['directory']['video_count'],'latest_user_request_completed_count':newreg['latest_requested_revision_completed_count'],'excluded_old_accepted_sources':[x['source_id']for x in prepared[0]['plan']['manifest']['excluded_older_accepted']],'unique_latest_video_directory':'视频修订定稿/最终定稿/视频/','all60_article_rows_previous_versions_and_batches_exact':True,'only_current40_request_scope_updated_to144_and_global145146_rules_added':True,'all_other69_request_entries_exact':True,'all_original_media_blobs_and_original_archive_records_preserved':True,'only_latest_aliases_and_metadata_changed_no_media_upload_or_audio_QA_repeated':True,'actual_both_remote_alias_mode_size_Git_SHA_and_folder_tree_verified':True,'video_order090_and_title077_preserved':True,'book_PDF_all_other_root_trees_and_protected_master_unchanged':True,'no_Release_created_or_modified':True,'recorded_exact_control_programs_and_tests':len(records)};save(R/'actual-user146-latest-directory-dual-closure.json',summary)
(R/'user146-current-cumulative-inventory.json').write_bytes(new_index);(R/'latest_requests.json').write_bytes(new_registry);state.update(primary_main=out[0]['commit'],backup_head=out[1]['commit'],video_subtree=out[0]['video_subtree'],actual_inventory=str(R/'user146-current-cumulative-inventory.json'),final_alias_inventory_snapshot=str(R/'user146-current-cumulative-inventory.json'),final_directory=prepared[0]['directory'],last_final_directory_receipt=str(R/'actual-user146-latest-directory-dual-closure.json'));state['active_latest_directory_policy146']=deepcopy(policy.POLICY);save(R/'CURRENT-ARCHIVE-STATE.json',state);print(json.dumps(summary,ensure_ascii=False),flush=True)
