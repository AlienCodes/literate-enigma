"""Reuse the verified archive process for actual V3-passed article handoffs.

prepare preserves bytes and their existing provenance; push only writes an
isolated asset branch; index merges the published inventory; stream reads back
actual remote MP4 bytes. Main/backup integration remains a small Git-tree graft
onto the freshly read branch HEAD. This program never renders or changes QC.
"""
from pathlib import Path
import argparse,datetime,hashlib,json,os,re,shutil,subprocess,urllib.parse,urllib.request

def load(p):return json.loads(Path(p).read_text())
def write(p,d):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def digest(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()

def prepare(a):
 h=load(a.handoff);root=Path(a.handoff).resolve().parent;out=Path(a.work_dir).resolve();pay=out/'payload'
 report=load(h['report_path']);passed={x['id']:x for x in report['actual_articles'] if x['passed_per_article']}
 assert h['articles'] and len(passed)==len(h['articles'])
 book=load(h['global_approved_evidence']['book_illustrations']['path'])
 catalog={x['source_id']:x for x in book['illustrations']}
 label=a.batch or f"2026-11-14-run{h['source_run']}-"+'-'.join(x['source_id'] for x in h['articles'])
 assert '/' not in label and label not in ('.','..')
 prefix=Path('视频修订定稿')/label;rows=[]
 def add(src,rel,size=None,sha=None):
  src=Path(src);dst=pay/rel;actual=digest(src)
  assert size is None or src.stat().st_size==size,str(src)
  assert sha is None or actual==sha,str(src)
  dst.parent.mkdir(parents=True,exist_ok=True)
  if dst.exists():
   assert digest(dst)==actual,str(dst)
   if dst.stat().st_ino==src.stat().st_ino and src.suffix not in ('.mp4','.png','.jpg','.zip'):
    tmp=dst.with_name(dst.name+'.snapshot.tmp');shutil.copyfile(src,tmp);os.replace(tmp,dst)
  elif src.suffix in ('.mp4','.png','.jpg','.zip'):os.link(src,dst)
  else:shutil.copyfile(src,dst)
  rows.append({'repo_path':str(rel),'bytes':src.stat().st_size,'sha256':actual})
 def spec(row,rel):add(row['path'],rel,row['bytes'],row['sha256'])
 for row in h['validation_files']:
  rel=row.get('relative_validation_path',row.get('validation_relative_path'))
  assert rel;spec(row,prefix/'V3逐项核验'/rel)
 add(a.handoff,prefix/'V3逐项核验/archive-handoff.json')
 codes=Path(h.get('code_snapshot_path',a.code_snapshot or ''))
 for name,sha in h['tool_source_sha256'].items():add(codes/name,prefix/'制作与核验程序/V3本次实际验证代码'/name,sha=sha)
 add(codes/'snapshot-manifest.json',prefix/'制作与核验程序/V3本次实际验证代码/snapshot-manifest.json')
 for row in h['global_approved_evidence'].values():spec(row,prefix/'批准依据'/Path(row['path']).name)
 articles=[]
 for item in h['articles']:
  sid=item['source_id'];nid=item['new_id'];b=catalog[sid];section=item['section'];native=Path(item['final_mp4']['path']).parent
  assert sid in passed and b['new_id']==nid and passed[sid]['sha256']==item['final_mp4']['sha256']
  stem=f"{nid} {b['title_zh']}";spec(item['final_mp4'],prefix/'视频'/(stem+'.mp4'))
  spec(item['canonical_source_mp4'],prefix/'实际官方新底片'/(stem+'（未插图底片）.mp4'))
  spec(item['immutable_native_zip'],prefix/'原始Actions产物'/f"original{sid}-run{h['source_run']}-passed-output.zip")
  for r in section['stills']:spec(r,prefix/'实际解码帧'/nid/Path(r['path']).name)
  spec(section['illustration'],prefix/'插图'/(stem+'-4K.png'))
  spec(section['illustration']['native_source'],prefix/'插图'/(stem+'-书内批准原图.png'))
  for src in sorted((native/'files').iterdir()):
   if src.suffix in ('.json','.png'):add(src,prefix/'官方原产物解包'/sid/src.name)
  tail=load(native/f'{sid}-illustrated-tail-verification.json')
  helper=Path('/workspace/work/video-audit70-20261113/illustrated-tail/illustrated_tail.py')
  if not any(x['repo_path']==str(prefix/'制作与核验程序/illustrated_tail.py') for x in rows):
   add(helper,prefix/'制作与核验程序/illustrated_tail.py',sha=tail['postprocessor_sha256'])
  for name in [f'{sid}-illustrated-tail-verification.json','illustrated-tail.log','retrieval-receipt.json','actual-boundary-frame-review.json','illustrated-tail-command.json']:
   q=native/name
   if q.exists():add(q,prefix/'尾部实际核验'/sid/name)
  articles.append({'source_id':sid,'new_id':nid,'title_zh':b['title_zh'],'title_en':b['title_en'],
   'video_repo_path':str(prefix/'视频'/(stem+'.mp4')),'bytes':item['final_mp4']['bytes'],'sha256':item['final_mp4']['sha256'],
   'passed_per_article':True,'source_run':h['source_run'],'GEN_origin':section['final_source']['gen'].get('origin'),
   'MD_origin':section['final_source']['md'].get('origin'),'runtime_GEN_observed':False})
 add(Path(__file__),prefix/'制作与核验程序/archive_batch.py')
 meta={'schema_version':1,'created_utc':now(),'source_run':h['source_run'],'prefix':str(prefix),
       'asset_branch':'codex/passed4k-assets-'+str(h['source_run'])+'-'+'-'.join(x['source_id'] for x in articles),
       'scope':'Only the actual passed articles listed here; no full70 or Release assertion.',
       'articles':articles,'material_source_bindings':rows,'release_created':False,
       'provenance':'Working JSON is an observed original native artifact. Derived GEN and request-equivalent MD retain their existing honest origin labels. No original runtime GEN is claimed observed.',
       'all_payload_file_hashes':'files-SHA256.json'}
 write(pay/prefix/'archive-manifest.json',meta)
 hashfile=pay/prefix/'files-SHA256.json';index=[]
 for q in sorted(pay.rglob('*')):
  if q.is_file() and q!=hashfile:index.append({'repo_path':str(q.relative_to(pay)),'bytes':q.stat().st_size,'sha256':digest(q)})
 write(hashfile,{'excludes_only_itself':True,'files':index})
 index.append({'repo_path':str(hashfile.relative_to(pay)),'bytes':hashfile.stat().st_size,'sha256':digest(hashfile)})
 write(out/'payload-file-index.json',index);write(out/'prepared-archive.json',meta)
 print(json.dumps({'prefix':str(prefix),'files':len(index),'bytes':sum(x['bytes'] for x in index),'articles':articles},ensure_ascii=False))

def push(a):
 out=Path(a.work_dir).resolve();pay=out/'payload';gitdir=out/'assets.git';meta=load(out/'prepared-archive.json');branch=meta['asset_branch']
 assert a.repo in ('alienalgorithm/postgraduate-vocabulary','AlienCodes/literate-enigma')
 env={**os.environ,'GIT_INDEX_FILE':str(out/'assets.index')}
 def git(*args,input=None):
  r=subprocess.run(['git','--git-dir='+str(gitdir),'--work-tree='+str(pay),*args],input=input,text=True,capture_output=True,env=env,cwd=pay)
  if r.returncode:raise RuntimeError(r.stderr[-3000:])
  return r.stdout.strip()
 index=load(out/'payload-file-index.json')
 for x in index:assert (pay/x['repo_path']).stat().st_size==x['bytes'] and digest(pay/x['repo_path'])==x['sha256']
 if not gitdir.exists():subprocess.run(['git','init','--bare',str(gitdir)],capture_output=True,check=True)
 for k,v in [('user.name','Codex'),('user.email','codex@users.noreply.github.com'),('credential.helper','!gh auth git-credential'),('core.compression','1'),('pack.threads','2')]:git('config',k,v)
 local=out/'asset-local.json'
 if not local.exists():
  git('read-tree','--empty');parent=None;commits=[];batch=[];size=0
  groups=[]
  for x in sorted(index,key=lambda r:r['repo_path']):
   if batch and size+x['bytes']>64*1024*1024:groups.append(batch);batch=[];size=0
   batch.append(x);size+=x['bytes']
  if batch:groups.append(batch)
  for number,group in enumerate(groups,1):
   paths=[x['repo_path'] for x in group];hashes=git('hash-object','-w','--no-filters','--stdin-paths',input='\n'.join(paths)+'\n').splitlines()
   git('update-index','--add','--index-info',input=''.join(f'100644 {sha}\t{path}\n' for path,sha in zip(paths,hashes)))
   args=['commit-tree',git('write-tree'),'-m',f'保存本批实际合格视频及证据资产{number}/{len(groups)} [skip ci]']
   if parent:args+=['-p',parent]
   parent=git(*args);commits.append(parent)
  write(local,{'asset_commit':parent,'commits':commits,'asset_branch':branch,'root_tree':git('rev-parse',parent+'^{tree}')})
 data=load(local);url='https://github.com/'+a.repo+'.git';ref='refs/heads/'+branch
 remote=git('ls-remote',url,ref);head=remote.split()[0] if remote else None
 assert head is None or head in data['commits'],'Unexpected concurrent asset head; inspect before writing'
 start=data['commits'].index(head)+1 if head else 0
 for commit in data['commits'][start:]:
  git('-c','http.postBuffer=209715200','push','--quiet',url,commit+':'+ref)
  assert git('ls-remote',url,ref).split()[0]==commit
 data.update(repository=a.repo,video_tree_sha=git('rev-parse',data['asset_commit']+':'+meta['prefix']),files=len(index),remote_asset_ref_verified=True,main_or_master_changed=False)
 data['files_index']=[{**x,'git_blob_sha':git('rev-parse',data['asset_commit']+':'+x['repo_path'])} for x in index]
 write(out/('assets-primary.json' if a.repo.startswith('alienalgorithm/') else 'assets-backup.json'),data)
 print(json.dumps({k:v for k,v in data.items() if k!='files_index'},ensure_ascii=False))

def inventory(a):
 out=Path(a.work_dir);meta=load(out/'prepared-archive.json');asset=load(out/'asset-local.json')
 existing=load(a.existing) if a.existing else {'schema_version':1,'articles':[],'batches':[]}
 entries={x['source_id']:x for x in existing['articles']}
 for x in meta['articles']:
  row={**x,'asset_commit':asset['asset_commit'],'archive_prefix':meta['prefix']}
  old=entries.get(x['source_id'])
  if old and old['sha256']!=row['sha256']:row['previous_versions']=old.get('previous_versions',[])+[old]
  entries[x['source_id']]=row
 batches=existing.get('batches',[])
 if not any(x['prefix']==meta['prefix'] for x in batches):batches.append({'prefix':meta['prefix'],'asset_commit':asset['asset_commit'],'source_ids':[x['source_id'] for x in meta['articles']]})
 result={'schema_version':1,'updated_utc':now(),'requested_total':70,'archived_passed_count':len(entries),'remaining_not_claimed_passed':70-len(entries),'release_created':False,'articles':sorted(entries.values(),key=lambda x:int(x['new_id'])),'batches':batches}
 write(out/'cumulative-inventory.json',result);print(json.dumps({'archived_passed_count':len(entries),'path':str(out/'cumulative-inventory.json')},ensure_ascii=False))

def stream(a):
 out=Path(a.work_dir);meta=load(out/'prepared-archive.json');asset=load(out/'asset-local.json');rows=[]
 for repo in ['alienalgorithm/postgraduate-vocabulary','AlienCodes/literate-enigma']:
  for x in meta['articles']:
   url='https://raw.githubusercontent.com/'+repo+'/'+asset['asset_commit']+'/'+urllib.parse.quote(x['video_repo_path'],safe='/')
   h=hashlib.sha256();n=0
   with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Codex-archive-byte-verification'}),timeout=30) as r:
    status=r.status
    for b in iter(lambda:r.read(1024*1024),b''):h.update(b);n+=len(b)
   assert n==x['bytes'] and h.hexdigest()==x['sha256']
   row={'repository':repo,'source_id':x['source_id'],'new_id':x['new_id'],'pinned_asset_commit':asset['asset_commit'],'repo_path':x['video_repo_path'],'bytes':n,'sha256':h.hexdigest(),'http_status':status,'passed':True};rows.append(row);print(json.dumps(row,ensure_ascii=False),flush=True)
 write(out/'remote-video-byte-verification.json',{'passed':True,'checked_utc':now(),'scope':'Only actual videos listed in this batch, no full70 assertion','streams':rows,'temporary_videos_written':False})

def main():
 p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','push','index','stream']);p.add_argument('--work-dir',required=True);p.add_argument('--handoff');p.add_argument('--batch');p.add_argument('--code-snapshot');p.add_argument('--repo');p.add_argument('--existing');a=p.parse_args()
 {'prepare':prepare,'push':push,'index':inventory,'stream':stream}[a.action](a)
if __name__=='__main__':main()
