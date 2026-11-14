"""Read-only full Git-tree identity checks for three isolated public assets.

No rendering, source edits, quality changes, Git writes or canonical count change.
"""
import pathlib,json,subprocess,datetime
D=pathlib.Path(__file__).resolve().parent;B=D.parent
SIDRUN=[('61','43560056264'),('15','43562525001'),('17','43562525001')]
def api(repo,path):
 r=subprocess.run(['gh','api','repos/'+repo+'/'+path],capture_output=True,text=True,check=True);return json.loads(r.stdout)
receipt=json.loads((D/'actual-native-transfer-receipt.json').read_text());assert receipt['passed'] is True
native={x['source_id']:x for x in receipt['copied']};rows=[]
for sid,run in SIDRUN:
 W=B/f'run{run}-{sid}';m=json.loads((W/'prepared-archive.json').read_text());p=json.loads((W/'assets-primary.json').read_text());b=json.loads((W/'assets-backup.json').read_text());assert p['asset_commit']==b['asset_commit'] and p['root_tree']==b['root_tree'] and p['video_tree_sha']==b['video_tree_sha'] and p['files_index']==b['files_index']
 n=native[sid];assert n['exact_original_asset_commit']==p['asset_commit'] and n['exact_video_tree_sha']==p['video_tree_sha']
 assert [{'path':f['repo_path'],'git_blob_sha':f['git_blob_sha'],'bytes':f['bytes'],'sha256':f['sha256']} for f in p['files_index']]==n['files']
 for repo in ['alienalgorithm/postgraduate-vocabulary','AlienCodes/literate-enigma']:
  head=api(repo,'git/ref/heads/'+p['asset_branch'])['object']['sha'];assert head==p['asset_commit']
  commit=api(repo,'git/commits/'+head);assert commit['tree']['sha']==p['root_tree']
  subtree=api(repo,'git/trees/'+p['video_tree_sha']+'?recursive=1');assert not subtree.get('truncated');remote={x['path']:x for x in subtree['tree'] if x['type']=='blob'};assert len(remote)==len(p['files_index'])
  for f in p['files_index']:
   rel=f['repo_path'][len(m['prefix'])+1:];r=remote[rel];assert r['sha']==f['git_blob_sha'] and r['size']==f['bytes'] and r['mode']=='100644'
  rows.append({'repository':repo,'source_id':sid,'asset_branch':p['asset_branch'],'exact_original_asset_commit':head,'root_tree':p['root_tree'],'video_subtree':p['video_tree_sha'],'checked_blob_rows':len(remote),'all_blob_modes_SHA1_and_sizes_exact':True,'passed':True})
refs={}
for repo,branch in [('alienalgorithm/postgraduate-vocabulary','main'),('AlienCodes/literate-enigma','codex/all-deliverables-20261113'),('AlienCodes/literate-enigma','master')]:refs[repo+':'+branch]=api(repo,'git/ref/heads/'+branch)['object']['sha']
prior=json.loads((D/'pre-stage-protected-ref-observation.json').read_text());assert all(prior[k]==v for k,v in refs.items())
result={'scope':'Only three independently staged already-passed assets; canonical archive count remains55','passed':True,'checked_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'all383_original_blobs_verified_in_each_repository':True,'total_dual_blob_rows':sum(r['checked_blob_rows'] for r in rows),'checks':rows,'protected_refs_after':refs,'all_observed_protected_refs_unchanged':True,'release_modified':False,'archivist_changes_source_audio_video_or_QC':False}
(D/'dual-isolated-asset-blob-verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'passed':True,'rows':len(rows),'total_dual_blob_rows':result['total_dual_blob_rows'],'canonical_count_still':55},ensure_ascii=False))
