"""Finish the exact partial50 archive after local Unicode URL readback error.

Primary is read-only. Backup receives only the already validated identical video
subtree, on its unchanged phase7 parent; all other roots and master stay intact.
"""
import base64,datetime,json,pathlib,subprocess
B=pathlib.Path(__file__).resolve().parent;plan=json.loads((B/'integration-plan50.json').read_text());op=pathlib.Path(plan['operation_work_dir']);P='ab9ff85f060401fbc352081f8f844d656cc46215';PRIMARY='alienalgorithm/postgraduate-vocabulary';BACKUP='AlienCodes/literate-enigma';K=plan['expected_heads']['backup'];MASTER='6355a02864ebae616b693200d9d26f74f5da80e9'
def api(repo,path,method='GET',data=None):
 cmd=['gh','api','repos/'+repo+'/'+path]
 if method!='GET':cmd+=['--method',method,'--input','-']
 p=subprocess.run(cmd,input=None if data is None else json.dumps(data),capture_output=True,text=True,check=True);return json.loads(p.stdout)
def tree(repo,sha,rec=False):
 v=api(repo,'git/trees/'+sha+('?recursive=1' if rec else ''));assert not v.get('truncated');return {x['path']:x for x in v['tree']}
def root(repo,c):return tree(repo,api(repo,'git/commits/'+c)['tree']['sha'])
def slim(v):return {k:{f:x[f] for f in ['path','mode','type','sha']} for k,x in v.items()}
def save(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
assert api(PRIMARY,'git/ref/heads/main')['object']['sha']==P;assert api(BACKUP,'git/ref/heads/codex/all-deliverables-20261113')['object']['sha']==K;assert api(BACKUP,'git/ref/heads/master')['object']['sha']==MASTER
pc=api(PRIMARY,'git/commits/'+P);assert pc['parents'][0]['sha']==plan['expected_heads']['primary']
pr=root(PRIMARY,P);oldpr=root(PRIMARY,plan['expected_heads']['primary']);br=root(BACKUP,K)
assert {n:v['sha'] for n,v in pr.items() if n!='视频修订定稿'}=={n:v['sha'] for n,v in oldpr.items() if n!='视频修订定稿'}
vt=pr['视频修订定稿']['sha'];pv=tree(PRIMARY,vt,True);bv=tree(BACKUP,vt,True);assert {n:(v['sha'],v['mode']) for n,v in pv.items()}=={n:(v['sha'],v['mode']) for n,v in bv.items()}
previous=pathlib.Path(plan['previous_inventory']).read_bytes();latest=next((op/'payload').rglob('累计清单快照.json')).read_bytes();inventory=json.loads(latest);assert inventory['archived_passed_count']==50
oldv=tree(BACKUP,br['视频修订定稿']['sha'],True);assert base64.b64decode(api(BACKUP,'git/blobs/'+oldv['已归档视频总清单.json']['sha'])['content'])==previous
assert all(n=='已归档视频总清单.json' or (n in pv and pv[n]['sha']==v['sha'] and pv[n]['mode']==v['mode']) for n,v in oldv.items() if v['type']=='blob')
newfiles=0;streams=0;newids=[]
for raw in plan['article_work_dirs']+[str(op)]:
 w=pathlib.Path(raw);m=json.loads((w/'prepared-archive.json').read_text());a=json.loads((w/'assets-primary.json').read_text());k=json.loads((w/'assets-backup.json').read_text());assert a['asset_commit']==k['asset_commit'] and a['video_tree_sha']==k['video_tree_sha']
 relprefix=m['prefix'].split('/',1)[1];assert pv[relprefix]['sha']==a['video_tree_sha']
 for row in a['files_index']:
  name=row['repo_path'].split('/',1)[1];assert pv[name]['sha']==row['git_blob_sha'] and pv[name]['size']==row['bytes'] and bv[name]['sha']==row['git_blob_sha'];newfiles+=1
 if w!=op:
  s=json.loads((w/'remote-video-byte-verification.json').read_text());assert s['passed'] and len(s['streams'])==2 and all(x['passed'] and x['http_status']==200 for x in s['streams']);streams+=2;newids +=[x['source_id'] for x in m['articles']]
assert streams==16
for repo in [PRIMARY,BACKUP]:assert base64.b64decode(api(repo,'git/blobs/'+pv['已归档视频总清单.json']['sha'])['content'])==latest
roots=slim(br);roots['视频修订定稿']={'path':'视频修订定稿','mode':'040000','type':'tree','sha':vt};rt=api(BACKUP,'git/trees','POST',{'tree':list(roots.values())})['sha'];commit=api(BACKUP,'git/commits','POST',{'message':plan['message']+'；仅续完本地URL回读异常后的备仓合并','tree':rt,'parents':[K]})['sha']
assert api(PRIMARY,'git/ref/heads/main')['object']['sha']==P;assert api(BACKUP,'git/ref/heads/codex/all-deliverables-20261113')['object']['sha']==K
api(BACKUP,'git/refs/heads/codex/all-deliverables-20261113','PATCH',{'sha':commit,'force':False});assert api(BACKUP,'git/ref/heads/codex/all-deliverables-20261113')['object']['sha']==commit
fresh=root(BACKUP,commit);assert fresh['视频修订定稿']['sha']==vt;assert {n:v['sha'] for n,v in br.items() if n!='视频修订定稿'}=={n:v['sha'] for n,v in fresh.items() if n!='视频修订定稿'};assert api(BACKUP,'git/ref/heads/master')['object']['sha']==MASTER;assert api(PRIMARY,'git/ref/heads/main')['object']['sha']==P
archives=[{'role':'primary','repository':PRIMARY,'branch':'main','parent':plan['expected_heads']['primary'],'commit':P,'root_tree':pc['tree']['sha'],'video_subtree':vt},{'role':'backup','repository':BACKUP,'branch':'codex/all-deliverables-20261113','parent':K,'commit':commit,'root_tree':rt,'video_subtree':vt}]
for r in archives:r.update(all_new_blob_sizes_and_identities_verified=True,all_prior_archive_blob_modes_and_identities_unchanged_except_cumulative_index=True,all_other_root_subtrees_unchanged=True,protected_master_unchanged=MASTER)
receipt={'status':'permanent_double_repository_archive_verified','recorded_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'archived_passed_count':50,'new_source_ids':newids,'remaining_not_claimed_passed':20,'source_run':plan['source_run'],'actual_public_HTTP200_full_MP4_SHA256_streams':16,'new_payload_files_each_repository':newfiles,'native_inline_final_bytes_preserved_without_append_or_rerender':True,'derived_final_GEN_separately_labeled':True,'release_created':False,'whole70_passed_claimed':False,'archives':archives,'local_unicode_URL_readback_error_preserved':True,'recovery':'Primary patched once and retained read-only; backup-only exact same validated subtree on actual phase7 HEAD; no media/source/quality change'}
save(op/'final-archive-receipt.json',receipt);(op/'final-remote-cumulative-inventory.json').write_bytes(latest)
state=json.loads((B/'CURRENT-ARCHIVE-STATE.json').read_text());state.update(permanently_archived_count=50,primary_main=P,backup_head=commit,video_subtree=vt,actual_inventory=str(op/'final-remote-cumulative-inventory.json'),last_completed_receipt=str(op/'final-archive-receipt.json'),next_true_passed_not_main_archived=['06'],next_expected_count=51,main_backup_write_window='archive writer window; next root window must be coordinated');save(B/'CURRENT-ARCHIVE-STATE.json',state)
save(B/'partial50-local-readback-recovery.json',{'cause':'urllib URL Chinese path was not percent encoded after successful primary PATCH; backup had not been patched','error':'UnicodeEncodeError at contents/视频修订定稿/已归档视频总清单.json local HTTP request construction','primary_patch_count':1,'primary_read_only_during_recovery':True,'backup_only_precise_recovery':True,'actual_completed_receipt':str(op/'final-archive-receipt.json'),'recovery_program':str(pathlib.Path(__file__).resolve()),'all_media_source_and_quality_unchanged':True});print(json.dumps(receipt,ensure_ascii=False))
