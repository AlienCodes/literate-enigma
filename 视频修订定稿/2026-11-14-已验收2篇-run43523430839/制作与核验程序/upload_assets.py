"""Push the frozen two-video archive only to an isolated asset branch."""
from pathlib import Path
import argparse, hashlib, json, os, subprocess

HERE=Path(__file__).resolve().parent
PAY=HERE/'payload';GITDIR=HERE/'assets.git'
BRANCH='codex/two-passed4k-assets-43523430839'
p=argparse.ArgumentParser();p.add_argument('--repo',required=True);a=p.parse_args()
assert a.repo in ('alienalgorithm/postgraduate-vocabulary','AlienCodes/literate-enigma')
env={**os.environ,'GIT_INDEX_FILE':str(HERE/'assets.index')}
def git(*args,input=None):
 r=subprocess.run(['git','--git-dir='+str(GITDIR),'--work-tree='+str(PAY),*args],input=input,text=True,capture_output=True,env=env,cwd=PAY)
 if r.returncode:raise RuntimeError(r.stderr[-3000:])
 return r.stdout.strip()
index=json.loads((HERE/'payload-file-index.json').read_text())
for row in index:
 q=PAY/row['repo_path'];assert q.stat().st_size==row['bytes']
 assert hashlib.sha256(q.read_bytes()).hexdigest()==row['sha256']
 assert row['bytes']<90*1024*1024
if not GITDIR.exists():subprocess.run(['git','init','--bare',str(GITDIR)],capture_output=True,check=True)
for k,v in [('user.name','Codex'),('user.email','codex@users.noreply.github.com'),('core.compression','1'),('pack.threads','2'),('credential.helper','!gh auth git-credential')]:git('config',k,v)
git('read-tree','--empty')
paths=[x['repo_path'] for x in index]
hashes=git('hash-object','-w','--no-filters','--stdin-paths',input='\n'.join(paths)+'\n').splitlines()
assert len(paths)==len(hashes)
git('update-index','--add','--index-info',input=''.join(f'100644 {sha}\t{path}\n' for path,sha in zip(paths,hashes)))
tree=git('write-tree');state=HERE/'asset-local.json'
if state.exists():
 saved=json.loads(state.read_text());assert saved['root_tree']==tree;commit=saved['asset_commit']
else:
 commit=git('commit-tree',tree,'-m','归档本轮实际合格的书序35、63两部4K及完整核验证据 [skip ci]')
 saved={'asset_commit':commit,'root_tree':tree,'branch':BRANCH,'files':len(index)}
 state.write_text(json.dumps(saved,ensure_ascii=False,indent=2)+'\n')
git('update-ref','refs/heads/'+BRANCH,commit)
url='https://github.com/'+a.repo+'.git'
ref=git('ls-remote',url,'refs/heads/'+BRANCH);assert not ref or ref.split()[0]==commit
git('-c','http.postBuffer=209715200','push','--quiet',url,commit+':refs/heads/'+BRANCH)
assert git('ls-remote',url,'refs/heads/'+BRANCH).split()[0]==commit
sha_rows=[{'repo_path':path,'git_blob_sha':sha,'bytes':row['bytes'],'sha256':row['sha256']} for path,sha,row in zip(paths,hashes,index)]
video_prefix=json.loads((HERE/'prepared-archive.json').read_text())['video_prefix']
result={**saved,'repository':a.repo,'video_prefix':video_prefix,'video_tree_sha':git('rev-parse',commit+':'+video_prefix),
 'files_index':sha_rows,'remote_asset_ref_verified':True,'main_or_master_changed':False}
dest=HERE/('assets-primary.json' if a.repo.startswith('alienalgorithm/') else 'assets-backup.json')
dest.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k!='files_index'},ensure_ascii=False),flush=True)
