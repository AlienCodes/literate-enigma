"""Upload only the reviewed immutable V4 payload on an independent asset branch.

No existing source checkout/index is touched. Main/master are never pushed by
this program; the final namespace is grafted later through Git Database APIs.
"""
from pathlib import Path
import argparse,hashlib,json,os,subprocess

HERE=Path(__file__).resolve().parent
PAYLOAD=HERE/'archive-payload'
PREFIX=Path('考研学人印刷版/2026-11-13-v4')
GITDIR=HERE/'archive-assets.git'
BRANCH='codex/punk-print-assets-20261113-v4'
JOURNAL=HERE/'asset-push-journal.json'
ENV={**os.environ,'GIT_INDEX_FILE':str(HERE/'archive-assets.index')}

def git(*args,input=None):
 r=subprocess.run(['git','--git-dir='+str(GITDIR),'--work-tree='+str(PAYLOAD),*map(str,args)],input=input,cwd=PAYLOAD,capture_output=True,text=True,env=ENV)
 if r.returncode:raise RuntimeError(r.stderr[-3500:])
 return r.stdout.strip()
def batches(files):
 def typ(p):
  rel=p.relative_to(PAYLOAD/PREFIX)
  if rel.parts[0]=='分篇PDF':return '20-chapters-'+str((int(rel.name[:2])-1)//10)
  if rel.parts[0]=='分册PDF':return '30-volumes-'+rel.name
  if rel.parts[:2]==('整本','parts'):return '40-book-'+rel.name
  if rel.parts[0]=='插图':return '10-illustrations-'+str((int(rel.name[:2])-1)//10) if rel.suffix=='.png' else '00-source-code-and-QA'
  return '00-source-code-and-QA'
 groups={}
 for p in files:groups.setdefault(typ(p),[]).append(p)
 return [(key,groups[key]) for key in sorted(groups)]
def main():
 p=argparse.ArgumentParser();p.add_argument('--repo',required=True);args=p.parse_args();repo=args.repo
 assert repo in ('alienalgorithm/postgraduate-vocabulary','AlienCodes/literate-enigma')
 manifest=json.loads((PAYLOAD/PREFIX/'files-SHA256.json').read_text())
 for row in manifest['files']:
  path=PAYLOAD/row['repo_path'];assert path.stat().st_size==row['bytes'] and hashlib.sha256(path.read_bytes()).hexdigest()==row['sha256'],row['repo_path'];assert row['bytes']<=90*1024*1024
 if not GITDIR.exists():subprocess.run(['git','init','--bare',str(GITDIR)],check=True,capture_output=True)
 for key,value in [('user.name','Codex'),('user.email','codex@users.noreply.github.com'),('core.compression','1'),('pack.threads','2'),('credential.helper','!gh auth git-credential')]:git('config',key,value)
 records=json.loads(JOURNAL.read_text()) if JOURNAL.exists() else []
 all_files=sorted(p for p in (PAYLOAD/PREFIX).rglob('*') if p.is_file())
 local_records=[r for r in records if r['repository']==repo]
 if repo=='alienalgorithm/postgraduate-vocabulary':
  parent=local_records[-1]['commit'] if local_records else None
  if parent:git('read-tree',parent)
  else:git('read-tree','--empty')
  completed={r['batch'] for r in local_records}
  for label,files in batches(all_files):
   if label in completed:continue
   rel=[str(x.relative_to(PAYLOAD)) for x in files];hashes=git('hash-object','-w','--no-filters','--stdin-paths',input='\n'.join(rel)+'\n').splitlines();assert len(hashes)==len(rel)
   git('update-index','--add','--index-info',input=''.join(f'100644 {h}\t{path}\n' for path,h in zip(rel,hashes)))
   tree=git('write-tree');argv=['commit-tree',tree,'-m',f'归档475页主册V4资产：{label} [skip ci]']
   if parent:argv.extend(['-p',parent])
   commit=git(*argv);git('update-ref','refs/heads/'+BRANCH,commit)
   url='https://github.com/'+repo+'.git';git('-c','http.postBuffer=209715200','push','--quiet',url,'refs/heads/'+BRANCH+':refs/heads/'+BRANCH)
   remote=git('ls-remote',url,'refs/heads/'+BRANCH).split()[0];assert remote==commit
   row={'repository':repo,'branch':BRANCH,'batch':label,'commit':commit,'files':len(files),'remote_ref_verified':True};records.append(row);JOURNAL.write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n');print(json.dumps(row,ensure_ascii=False),flush=True);parent=commit
 else:
  assert records and git('rev-parse','refs/heads/'+BRANCH)
  commit=git('rev-parse','refs/heads/'+BRANCH);url='https://github.com/'+repo+'.git';git('-c','http.postBuffer=209715200','push','--quiet',url,'refs/heads/'+BRANCH+':refs/heads/'+BRANCH);assert git('ls-remote',url,'refs/heads/'+BRANCH).split()[0]==commit;records.append({'repository':repo,'branch':BRANCH,'batch':'complete-mirror','commit':commit,'files':len(all_files),'remote_ref_verified':True});JOURNAL.write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n')
 head=git('rev-parse','refs/heads/'+BRANCH);node=git('rev-parse',head+':'+str(PREFIX));result={'repository':repo,'asset_branch':BRANCH,'asset_commit':head,'archive_tree_sha':node,'prefix':str(PREFIX),'gitdir':str(GITDIR),'files':len(all_files),'main_or_master_changed_by_this_program':False};path=HERE/('asset-primary.json' if repo.startswith('alienalgorithm/') else 'asset-backup.json');path.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result,ensure_ascii=False),flush=True)
if __name__=='__main__':main()
