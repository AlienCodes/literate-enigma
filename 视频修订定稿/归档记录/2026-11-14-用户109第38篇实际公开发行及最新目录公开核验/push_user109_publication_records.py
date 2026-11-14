"""Isolated safe small records only; no main, video downloads, QA or Releases."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import base64,hashlib,json,os,shutil,subprocess,sys,urllib.request,urllib.parse
R=Path(__file__).parent;location=json.loads((R/'user109-publication-records-staging-location.json').read_text());T=Path(location['root']);W=Path(location['work_dir']);P=W/'payload'
def load(p):return json.loads(p.read_text())
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
meta=load(W/'prepared-archive.json');index=load(W/'payload-file-index.json');scope={'kind':'completed-user109-publication-small-records-and-purpose-built-public-folder-proofs','original_records':index,'no_media_redownload_current_QA_PDF_ROOT_or_Release_operation':True}
sp=P/meta['prefix']/'PUBLIC-ARCHIVE-SCOPE.json';save(sp,scope);index=[{'repo_path':str(p.relative_to(P)),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}for p in sorted(P.rglob('*'))if p.is_file()];save(W/'payload-file-index.json',index)
for role,repo in [('primary','alienalgorithm/postgraduate-vocabulary'),('backup','AlienCodes/literate-enigma')]:
 with (W/(role+'-push.log')).open('w')as f:subprocess.run([sys.executable,str(T/'archive_batch.py'),'push','--work-dir',str(W),'--repo',repo],check=True,timeout=85,env={**os.environ,'TMPDIR':str(T)},stdout=f,stderr=subprocess.STDOUT)
token=subprocess.check_output(['gh','auth','token'],text=True).strip()
def api(repo,path):
 q=urllib.request.Request('https://api.github.com/repos/'+repo+'/'+urllib.parse.quote(path,safe='/?=&%'),headers={'Authorization':'Bearer '+token,'Accept':'application/vnd.github+json'})
 with urllib.request.urlopen(q,timeout=60)as r:return json.loads(r.read())
def verify(role,repo):
 asset=load(W/('assets-'+role+'.json'));assert api(repo,'git/ref/heads/'+asset['asset_branch'])['object']['sha']==asset['asset_commit'];actual=api(repo,'git/trees/'+asset['video_tree_sha']+'?recursive=1');assert not actual.get('truncated');leaves={x['path']:x for x in actual['tree']if x['type']=='blob'};assert len(leaves)==len(index)
 def check(row):
  p=P/row['repo_path'];data=p.read_bytes();relative=row['repo_path'][len(meta['prefix'])+1:];v=leaves[relative];expected=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest();assert v['sha']==expected and v['size']==len(data)and v['mode']=='100644';got=base64.b64decode(api(repo,'git/blobs/'+expected)['content']);assert got==data;return {'path':row['repo_path'],'bytes':len(data),'sha256':hashlib.sha256(got).hexdigest(),'git_blob_sha':expected,'actual_full_blob_bytes_read_back':True}
 with ThreadPoolExecutor(max_workers=4)as pool:checks=list(pool.map(check,index))
 return {'repository':repo,'branch':asset['asset_branch'],'asset_commit':asset['asset_commit'],'subtree':asset['video_tree_sha'],'files':checks}
with ThreadPoolExecutor(max_workers=2)as pool:
 p=pool.submit(verify,'primary','alienalgorithm/postgraduate-vocabulary');b=pool.submit(verify,'backup','AlienCodes/literate-enigma');out=[p.result(),b.result()]
assert out[0]['asset_commit']==out[1]['asset_commit']and out[0]['subtree']==out[1]['subtree']and out[0]['files']==out[1]['files']
proof={'kind':'actual-safe-small-records-dual-complete-immutable-byte-verification','archives':out,'actual_full_blob_readbacks':sum(len(x['files'])for x in out),'no_main_current_alias_media_QA_or_Release_operation':True};save(W/'actual-dual-small-record-verification.json',proof)
for x in out:assert api(x['repository'],'git/ref/heads/'+x['branch'])['object']['sha']==x['asset_commit']
bare=W/'assets.git';test=subprocess.run(['git','--git-dir='+str(bare),'fsck','--full','--no-reflogs'],capture_output=True,text=True);assert test.returncode==0;size=sum(p.stat().st_size for p in bare.rglob('*')if p.is_file());shutil.rmtree(bare)
idx=W/'assets.index'
if idx.exists():idx.unlink()
save(W/'closed-own-safe-record-RAMGit-cleanup-receipt.json',{'only_own_RAM_Git_removed':str(bare),'logical_bytes_removed':size,'git_fsck_exit_code':0,'all_payload_records_retained':True,'asset_commit':out[0]['asset_commit']})
print(json.dumps({'work_dir':str(W),'asset_commit':out[0]['asset_commit'],'branch':out[0]['branch'],'files':len(index),'actual_full_blob_readbacks':proof['actual_full_blob_readbacks'],'only_closed_own_RAMGit_cleaned':True},ensure_ascii=False),flush=True)
