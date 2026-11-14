"""Recover only final metadata readback after a real primary recursive GET500."""
from pathlib import Path
from copy import deepcopy
import ast,base64,hashlib,json,subprocess,sys,time,urllib.request,urllib.parse,urllib.error
R=Path(__file__).parent;B=Path('/workspace/work/video-archive-batches-20261114');sys.path.insert(0,str(B))
import final_alias_git as final
import build_final_alias_plan as aliases
import latest_final_directory_policy as policy
def load(p):return json.loads(Path(p).read_text())
def encode(x):return (json.dumps(x,ensure_ascii=False,indent=2)+'\n').encode()
def save(p,x):p.write_bytes(encode(x))
def blob(raw):return hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
def sha(raw):return hashlib.sha256(raw).hexdigest()
state=load(R/'CURRENT-ARCHIVE-STATE.json');old_index=Path(state['actual_inventory']).read_bytes();old=json.loads(old_index);new=load(R/'user146-planned-cumulative-inventory.json');newreg=load(R/'user146-planned-latest_requests.json');oldreg=load(R/'latest_requests.json');prepared=load(R/'user146-prepared-canonical-commits.json');assert new['articles']==old['articles']and new['batches']==old['batches']and new['video_order_overlay']==old['video_order_overlay'];assert new[policy.KEY]==policy.POLICY
cache=load(R/'actual-canonical-video-tree-before146.local.json');assert cache['sha']==state['video_subtree'];oldfull={x['path']:x for x in cache['tree']};oldvideo={k:r for k,r in oldfull.items()if '/'not in k};catalog=load(state['final_alias_catalog']['path']);plan=aliases.build(new,oldfull,catalog,latest_requests=newreg);assert len(plan['video_entries'])==55
source=ast.parse((R/'install_user146_latest_directory.py').read_text());addition=next(ast.literal_eval(x.value)for x in source.body if isinstance(x,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='addition'for t in x.targets))
record_files=[B/'latest_final_directory_policy.py',B/'build_final_alias_plan.py',B/'build_final_alias_plan-before-user146-latest-only.py',B/'final_alias_git.py',B/'final_alias_git-before-user146-latest-only.py',B/'archive_revision_policy.py',B/'archive_revision_policy-before-user146-latest-only.py',B/'integrate_verified_batch.py',B/'integrate_verified_batch-before-user146-latest-only.py',B/'latest_request_tracking.py',R/'patch_latest_user_requests.py',R/'patch_latest_user_requests-before146.py',R/'test_user146_latest_directory_plans.py',R/'user146-actual-metadata-plan-checks.json',R/'install_user146_latest_directory.py',Path('/dev/shm/archive-writer-user-review-20261114/USER-REVIEW-2026-11-14-146.json'),Path('/dev/shm/archive-writer-user-review-20261114/USER-REVIEW-2026-11-14-145.json')]
token=subprocess.check_output(['gh','auth','token'],text=True).strip()
def api(repo,path,method='GET',data=None):
 q=urllib.request.Request('https://api.github.com/repos/'+repo+'/'+urllib.parse.quote(path,safe='/?=&%'),data=None if data is None else json.dumps(data).encode(),method=method,headers={'Authorization':'Bearer '+token,'Accept':'application/vnd.github+json','Content-Type':'application/json'})
 for attempt in range(3):
  try:
   with urllib.request.urlopen(q,timeout=60)as r:return json.loads(r.read())
  except urllib.error.HTTPError as e:
   body=e.read().decode();save(R/('user146-completion-'+repo.split('/')[0]+'-HTTP-error.json'),{'path':path,'method':method,'status':e.code,'body':body,'attempt':attempt+1})
   if method=='GET'and e.code in [500,502,503,504]and attempt<2:continue
   raise
def tree(repo,sha,recursive=False):
 d=api(repo,'git/trees/'+sha+('?recursive=1'if recursive else''));assert d['sha']==sha and not d.get('truncated');return {x['path']:x for x in d['tree']}
def raw(repo,sha):return base64.b64decode(api(repo,'git/blobs/'+sha)['content'])
MASTER='6355a02864ebae616b693200d9d26f74f5da80e9';assert api('AlienCodes/literate-enigma','git/ref/heads/master')['object']['sha']==MASTER
out=[]
for p in prepared:
 repo=p['repository'];branch=p['branch'];head=api(repo,'git/ref/heads/'+branch)['object']['sha'];assert head in [p['parent'],p['commit']]
 patched=False
 if head==p['parent']:api(repo,'git/refs/heads/'+branch,'PATCH',{'sha':p['commit'],'force':False});patched=True
 assert api(repo,'git/ref/heads/'+branch)['object']['sha']==p['commit'];commit=api(repo,'git/commits/'+p['commit']);assert commit['tree']['sha']==p['root_tree']
 oldroot=tree(repo,api(repo,'git/commits/'+p['parent'])['tree']['sha']);root=tree(repo,p['root_tree']);video=tree(repo,p['video_subtree']);assert root['视频修订定稿']['sha']==p['video_subtree']
 assert {k:(r['sha'],r['mode'])for k,r in oldroot.items()if k not in ['AGENTS.md','视频修订定稿']}=={k:(r['sha'],r['mode'])for k,r in root.items()if k not in ['AGENTS.md','视频修订定稿']}
 permitted={'已归档视频总清单.json','latest_requests.json','最新视频选择规则.json','最终定稿','归档记录'}
 assert all(k in permitted or (video[k]['sha']==r['sha']and video[k]['mode']==r['mode'])for k,r in oldvideo.items())
 old_records=tree(repo,oldvideo['归档记录']['sha']);new_records=tree(repo,video['归档记录']['sha']);assert all(new_records[k]['sha']==r['sha']and new_records[k]['mode']==r['mode']for k,r in old_records.items());added=set(new_records)-set(old_records);assert added=={'2026-11-14-用户146唯一最新定稿目录规则'};assert new_records[next(iter(added))]['sha']==p['record_tree']
 # Read the complete small final subtree, rather than refetching all old archives.
 final_sha=video['最终定稿']['sha'];assert final_sha==p['directory']['final_tree_sha'];observed=tree(repo,final_sha,True);files=final.expected_file_identities(plan);final._verify_tree(files,observed,final_sha)
 logical={k:v for k,v in oldfull.items()if k!='最终定稿'and not k.startswith('最终定稿/')};logical['最终定稿']={'path':'最终定稿','type':'tree','mode':'040000','sha':final_sha};logical.update({'最终定稿/'+k:v for k,v in observed.items()});assert final.assert_existing_final_matches(new,logical,catalog,latest_requests=newreg)==p['directory']
 for name,wanted in [('已归档视频总清单.json',encode(new)),('latest_requests.json',encode(newreg)),('最新定稿目录规则146.json',encode(policy.POLICY))]:assert raw(repo,video[name]['sha'])==wanted
 rules=load(R/'user146-planned-latest_requests.json');actual_rules=json.loads(raw(repo,video['最新视频选择规则.json']['sha']));assert actual_rules['latest_final_directory_policy']==policy.POLICY
 assert raw(repo,root['AGENTS.md']['sha'])==raw(repo,oldroot['AGENTS.md']['sha'])+addition.encode()
 for name in ['README.md','当前清单.json','视频顺序.json']:assert raw(repo,observed[name]['sha'])==plan['text_files'][name].encode()
 record_tree=tree(repo,p['record_tree']);assert len(record_tree)==len(record_files)
 for f in record_files:
  data=f.read_bytes();n=record_tree[f.name];assert n['mode']=='100644'and n['size']==len(data)and n['sha']==blob(data)
 assert api('AlienCodes/literate-enigma','git/ref/heads/master')['object']['sha']==MASTER
 out.append({**p,'PATCH_performed_by_this_completion':patched,'actual_complete_final_subtree_entries_read':len(observed),'actual_alias_files_and_text_modes_sizes_Git_SHA_exact':True,'original_archive_subtrees_and_all_existing_record_children_exact':True,'actual_manifest_README_order_and_registry_entire_blob_readback':True})
 assert p['directory']['video_count']==55 and p['directory']['expected_file_count']==113
summary={'kind':'actual-user146-unique-latest-final-directory-dual-closure','archives':out,'archived_passed_count':60,'latest_deliverable_video_count':55,'latest_user_request_completed_count':38,'excluded_old_accepted_sources':[x['source_id']for x in plan['manifest']['excluded_older_accepted']],'unique_latest_video_directory':'视频修订定稿/最终定稿/视频/','all60_article_rows_previous_versions_and_batches_exact':True,'only_source40_request_scope_updated_to144_and_global145146_rules_added':True,'all_other69_request_entries_exact':True,'all_original_media_blobs_and_original_archive_records_preserved':True,'no_media_upload_audio_change_or_quality_rerun':True,'actual_both_remote_alias_mode_size_Git_SHA_and_complete_final_folder_tree_verified':True,'video_order090_title077_book_PDF_all_other_root_trees_and_master_preserved':True,'no_Release_created_or_modified':True,'recorded_exact_control_programs_and_tests':len(record_files),'transport_recovery':'Original primary PATCH succeeded; one large recursive archive-tree GET returned500. This completion reads all113 latest-folder entries and immutable original subtree identities; primary is not repatched.'};save(R/'actual-user146-latest-directory-dual-closure.json',summary)
(R/'user146-current-cumulative-inventory.json').write_bytes(encode(new));(R/'latest_requests.json').write_bytes(encode(newreg));state.update(primary_main=out[0]['commit'],backup_head=out[1]['commit'],video_subtree=out[0]['video_subtree'],actual_inventory=str(R/'user146-current-cumulative-inventory.json'),final_alias_inventory_snapshot=str(R/'user146-current-cumulative-inventory.json'),final_directory=prepared[0]['directory'],last_final_directory_receipt=str(R/'actual-user146-latest-directory-dual-closure.json'));state['active_latest_directory_policy146']=deepcopy(policy.POLICY);save(R/'CURRENT-ARCHIVE-STATE.json',state);print(json.dumps({'main':out[0]['commit'],'backup':out[1]['commit'],'latest_video_count':55,'archived_count':60,'receipt':str(R/'actual-user146-latest-directory-dual-closure.json'),'receipt_sha256':sha((R/'actual-user146-latest-directory-dual-closure.json').read_bytes())},ensure_ascii=False),flush=True)
