"""Read back immutable source trees in both repositories after phase9 publication."""
import json,subprocess,hashlib,concurrent.futures
from pathlib import Path
B=Path('/workspace/work/video-audit70-20261113'); P=Path('/workspace/work/video-source-publish-snapshot-20261114-v9'); R=json.loads((B/'PUBLISHED-SOURCE-STATE.json').read_text()); C=R['asset_commit']
def api(repo,path):return json.loads(subprocess.check_output(['gh','api','repos/'+repo+'/'+path]))
def git(path):return subprocess.check_output(['git','-C',str(P),'rev-parse',C+':'+path],text=True).strip()
def verify(row):
 repo=row['repository'];head=row['source_commit'];prefix='视频/制作记录/旧简述清理-2026-11-13'
 canonical=[]
 for p in P.rglob('*'):
  if p.is_file() and '.git' not in p.relative_to(P).parts:
   rel=str(p.relative_to(P))
   if not rel.startswith(prefix+'/'):canonical.append(rel)
 paths=canonical+[prefix];cache={}
 def tree(s):
  if s not in cache:cache[s]=api(repo,'git/trees/'+s)['tree']
  return cache[s]
 root=api(repo,'git/commits/'+head)['tree']['sha']; old=api(repo,'git/commits/'+row['previous_commit'])['tree']['sha']
 def lookup(path):
  node=root
  for n in path.split('/'):
   match=next(x for x in tree(node) if x['path']==n);node=match['sha']
  return node
 observed=[]
 for path in paths:
  value=lookup(path);expected=git(path);assert value==expected,(repo,path);observed.append({'path':path,'git_blob_or_tree':value})
 oldroot={x['path']:x['sha'] for x in tree(old)}; newroot={x['path']:x['sha'] for x in tree(root)}; touched={p.split('/')[0] for p in paths};assert {k:v for k,v in oldroot.items() if k not in touched}=={k:v for k,v in newroot.items() if k not in touched}
 return {'repository':repo,'immutable_commit':head,'canonical_files_verified':len(canonical),'record_subtree_exact':True,'unrelated_root_trees_unchanged':True,'observed':observed}
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(verify,R['archives']))
backup_master=api('AlienCodes/literate-enigma','git/ref/heads/master')['object']['sha'];assert backup_master=='6355a02864ebae616b693200d9d26f74f5da80e9'
report={'status':'passed_actual_immutable_dual_archive_tree_readback','asset_commit':C,'payload_files':R['payload_files'],'payload_bytes':R['payload_bytes'],'backup_master_unchanged':True,'archives':results}
(B/'phase9-actual-dual-subtree-verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='archives'}))
