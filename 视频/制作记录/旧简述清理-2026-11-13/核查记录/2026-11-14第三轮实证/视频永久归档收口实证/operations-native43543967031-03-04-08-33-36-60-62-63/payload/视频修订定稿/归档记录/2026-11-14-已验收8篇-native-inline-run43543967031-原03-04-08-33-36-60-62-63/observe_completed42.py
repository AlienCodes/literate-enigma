"""Read back already completed42 archive; never writes a remote ref."""
import base64,datetime,hashlib,json,pathlib,subprocess
B=pathlib.Path(__file__).resolve().parent
P='e3a94843245676c4aa618a92f3a14772491f830d';K='200ed340b16a0e170726069ca6f7e99d35f5f9c9'
OP=B/'operations-native43543967031-44-55-57-59'
def api(repo,path):return json.loads(subprocess.check_output(['gh','api','repos/'+repo+'/'+path]))
def dump(path,obj):path.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
def tree(repo,sha,rec=False):
 d=api(repo,'git/trees/'+sha+('?recursive=1' if rec else ''));assert not d.get('truncated');return {x['path']:x for x in d['tree']}
def root(repo,c):return tree(repo,api(repo,'git/commits/'+c)['tree']['sha'])
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
roots=[];videos=[];indexes=[]
for repo,c in [('alienalgorithm/postgraduate-vocabulary',P),('AlienCodes/literate-enigma',K)]:
 r=root(repo,c); roots.append(r);v=tree(repo,r['视频修订定稿']['sha'],True);videos.append(v)
 actual=api(repo,'contents/视频修订定稿/已归档视频总清单.json?ref='+c);raw=base64.b64decode(actual['content']);indexes.append(raw)
 before=api(repo,'git/commits/'+c)['parents'][0]['sha'];oldroot=root(repo,before)
 assert {n:x['sha'] for n,x in oldroot.items() if n!='视频修订定稿'}=={n:x['sha'] for n,x in r.items() if n!='视频修订定稿'}
 prior=tree(repo,oldroot['视频修订定稿']['sha'],True)
 assert all(n=='已归档视频总清单.json' or (n in v and v[n]['sha']==x['sha'] and v[n]['mode']==x['mode']) for n,x in prior.items() if x['type']=='blob')
 for sid in ['44','55','57','59']:
  w=B/('run43543967031-'+sid);a=json.loads((w/'assets-primary.json').read_text());b=json.loads((w/'assets-backup.json').read_text());assert a['asset_commit']==b['asset_commit'] and a['video_tree_sha']==b['video_tree_sha']
  m=json.loads((w/'prepared-archive.json').read_text());prefix=m['prefix'].split('/',1)[1]
  assert v[prefix]['sha']==a['video_tree_sha']
  for f in a['files_index']:
   rel=f['repo_path'].split('/',1)[1];assert v[rel]['sha']==f['git_blob_sha'] and v[rel]['size']==f['bytes']
  stream=json.loads((w/'remote-video-byte-verification.json').read_text());assert stream['passed'] and len(stream['streams'])==2 and all(x['passed'] for x in stream['streams'])
 a=json.loads((OP/'assets-primary.json').read_text());b=json.loads((OP/'assets-backup.json').read_text());m=json.loads((OP/'prepared-archive.json').read_text());assert a['video_tree_sha']==b['video_tree_sha'];assert v[m['prefix'].split('/',1)[1]]['sha']==a['video_tree_sha']
 for f in a['files_index']:
  rel=f['repo_path'].split('/',1)[1];assert v[rel]['sha']==f['git_blob_sha'] and v[rel]['size']==f['bytes']
assert roots[0]['视频修订定稿']['sha']==roots[1]['视频修订定稿']['sha'];assert indexes[0]==indexes[1]
idx=json.loads(indexes[0]);assert idx['archived_passed_count']==42 and len(idx['articles'])==42
assert api('AlienCodes/literate-enigma','git/ref/heads/master')['object']['sha']=='6355a02864ebae616b693200d9d26f74f5da80e9'
(OP/'final-remote-cumulative-inventory.json').write_bytes(indexes[0])
receipt={'status':'permanent_double_repository_archive_verified','archived_passed_count':42,'new_source_ids':['44','55','57','59'],'source_run':43543967031,'primary':{'repository':'alienalgorithm/postgraduate-vocabulary','branch':'main','commit':P},'backup':{'repository':'AlienCodes/literate-enigma','branch':'codex/all-deliverables-20261113','commit':K},'video_subtree':roots[0]['视频修订定稿']['sha'],'new_article_payload_files_each_repository':372,'operation_record_files_each_repository':10,'all_new_remote_blobs_size_and_identity_verified':True,'actual_public_HTTP200_full_MP4_SHA256_streams':8,'all_prior38_blob_modes_and_identities_unchanged_except_index':True,'all_other_root_trees_unchanged':True,'backup_master_unchanged':'6355a02864ebae616b693200d9d26f74f5da80e9','reconstructed_read_only_observation_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'remote_write_executed':False,'release_created':False,'whole70_passed_claimed':False}
dump(OP/'final-archive-receipt.json',receipt)
state=json.loads((B/'CURRENT-ARCHIVE-STATE.json').read_text());dump(B/'CURRENT-ARCHIVE-STATE-before-readonly42.json',state)
state.update(permanently_archived_count=42,primary_main=P,backup_head=K,video_subtree=receipt['video_subtree'],actual_inventory=str(OP/'final-remote-cumulative-inventory.json'),next_true_passed_not_main_archived=['33','36','63'],next_expected_count=45,main_backup_write_window='root owns phase7; wait explicit new heads before any child PATCH',completed42_receipt=str(OP/'final-archive-receipt.json'))
dump(B/'CURRENT-ARCHIVE-STATE.json',state);print(json.dumps(receipt))
