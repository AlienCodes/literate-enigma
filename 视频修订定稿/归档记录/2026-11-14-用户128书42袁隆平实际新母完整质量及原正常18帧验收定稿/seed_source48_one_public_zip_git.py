"""One root-approved PUBLIC ZIP Git seed; default plan only, no media re-encoding."""
from pathlib import Path
import argparse,datetime,hashlib,json,os,shutil,subprocess,tempfile,urllib.request,zlib
HS='2082052baf9f71be9a0dcc5090234129a08e297714dc1738be8e2c1ffb099ece';PS='b61b29c558e63da7b1f7d76d0499a25ecf976d47a1f23f41ce1420e0898e8db4';IS='93874a48c31b70f732c50981f1ec8d429a57d74fcef53ab62821d5a9341db8a1'
ZIP_SHA='51ba30fa621945d4134116e08fde5b12cd12502a8c1d81439dc1ee104557fc2f';BLOB='56565c3aca8bc6093423e0a19172aaefe42c924a';SIZE=41614365
REF='codex/source48-zip56565-public-only-seed-20261115';REPO='AlienCodes/literate-enigma';NAME='source48-original-public-native-artifact.zip';MESSAGE='Transport only exact source48 public native ZIP; no final or quality change [skip ci]\n'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb')as f:
  for b in iter(lambda:f.read(196608),b''):h.update(b)
 return h.hexdigest()
def gitsha(kind,raw):return hashlib.sha1(kind.encode()+b' '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
def pinned(p,expected):
 raw=Path(p).read_bytes();assert hashlib.sha256(raw).hexdigest()==expected;return json.loads(raw)
def run(args,env=None,input=None):
 p=subprocess.run(list(map(str,args)),input=input,text=True,capture_output=True,env=env,timeout=180)
 if p.returncode:raise RuntimeError(p.stderr[-2000:])
 return p.stdout.strip()
def identities(blob,date,message=MESSAGE):
 raw=b'100644 '+NAME.encode()+b'\0'+bytes.fromhex(blob);tree=gitsha('tree',raw);stamp=int(datetime.datetime.fromisoformat(date.replace('Z','+00:00')).timestamp());body=(f'tree {tree}\nauthor Codex <codex@users.noreply.github.com> {stamp} +0000\ncommitter Codex <codex@users.noreply.github.com> {stamp} +0000\n\n'+message).encode();return tree,gitsha('commit',body),stamp
def local_objects(g,source,blob,tree,commit,stamp):
 run(['git','init','--bare','--template=',g]);args=['git','--git-dir='+str(g)]
 for k,v in [('gc.auto','0'),('core.compression','1'),('pack.threads','1'),('pack.window','0')]:run(args+['config',k,v])
 assert run(args+['hash-object','-w','--no-filters',source])==blob
 assert run(args+['mktree'],input=f'100644 blob {blob}\t{NAME}\n')==tree
 env={**os.environ,'GIT_AUTHOR_NAME':'Codex','GIT_AUTHOR_EMAIL':'codex@users.noreply.github.com','GIT_COMMITTER_NAME':'Codex','GIT_COMMITTER_EMAIL':'codex@users.noreply.github.com','GIT_AUTHOR_DATE':f'@{stamp} +0000','GIT_COMMITTER_DATE':f'@{stamp} +0000'}
 assert run(args+['commit-tree',tree,'-m',MESSAGE.rstrip('\n')],env=env)==commit
def refs():
 result={}
 for repo,branch,expected in [('alienalgorithm/postgraduate-vocabulary','main','80a867b87ea4c61f778f86d7b76de3b2747541b0'),(REPO,'codex/all-deliverables-20261113','8c077873565086032dcc2bd003e69ee618382051'),(REPO,'master','6355a02864ebae616b693200d9d26f74f5da80e9')]:
  actual=run(['gh','api',f'repos/{repo}/git/ref/heads/{branch}','--jq','.object.sha']);assert actual==expected;result[repo+':'+branch]=actual
 return result
def main():
 p=argparse.ArgumentParser();p.add_argument('--work-dir',required=True);p.add_argument('--handoff',required=True);p.add_argument('--approval');p.add_argument('--execute',action='store_true');a=p.parse_args();w=Path(a.work_dir).resolve();root=w.parent
 h=pinned(a.handoff,HS);meta=pinned(w/'prepared-archive.json',PS);index=pinned(w/'payload-file-index.json',IS);assert h['articles'][0]['source_id']=='48'and h['articles'][0]['new_id']=='42'and h['production_delivery_eligible']is True
 row=next(x for x in index if x['bytes']==SIZE and x['sha256']==ZIP_SHA);source=(w/'payload'/row['repo_path']).resolve();assert source.stat().st_size==SIZE and sha(source)==ZIP_SHA
 ghash=hashlib.sha1(f'blob {SIZE}\0'.encode());z=zlib.compressobj(1);compressed=len(z.compress(f'blob {SIZE}\0'.encode()))
 with source.open('rb')as f:
  for b in iter(lambda:f.read(196608),b''):ghash.update(b);compressed+=len(z.compress(b))
 compressed+=len(z.flush());assert ghash.hexdigest()==BLOB
 tree,commit,stamp=identities(BLOB,meta['created_utc']);allocated=((compressed+4095)//4096)*4096
 plan={'kind':'exact-one-public-source48-ZIP-standard-Git-seed-plan','source_id':'48','source_bytes':SIZE,'source_SHA256':ZIP_SHA,'git_blob_sha':BLOB,'seed_ref':REF,'seed_tree':tree,'seed_commit':commit,'actual_zlib1_loose_object_bytes':compressed,'estimated_loose_allocated4KiB':allocated,'Git_metadata_reserved_bytes':2*1024*1024,'minimum_RAM_remaining_reserved':8*1024*1024,'no_ZIP_or_pack_copy_or_base64_body_file':True,'outbound_pack_is_standard_Git_stdout_and_HTTP_buffer_heap':True,'network_executed':False}
 if not a.execute:print(json.dumps(plan));return
 approval=json.loads(Path(a.approval).read_text());assert approval['kind']=='root-approved-source48-exact-one-public-ZIP-standard-Git-seed'and approval['approved']is True and approval['approved_seed_code_sha256']==sha(__file__)and approval['handoff_sha256']==HS and approval['prepared_sha256']==PS and approval['index_sha256']==IS and approval['seed_commit']==commit and approval['seed_ref']==REF
 assert os.statvfs('/dev/shm').f_bavail*os.statvfs('/dev/shm').f_frsize>allocated+10*1024*1024
 before=refs();url='https://github.com/'+REPO+'.git';auth=['-c','credential.helper=!gh auth git-credential'];assert not run(['git',*auth,'ls-remote',url,'refs/heads/'+REF]),'Seed branch must be absent'
 own=Path(tempfile.mkdtemp(prefix='source48-exact-zip56565-seed-',dir='/dev/shm'));g=own/'objects.git';local_objects(g,source,BLOB,tree,commit,stamp)
 assert pinned(a.handoff,HS)and pinned(w/'prepared-archive.json',PS)and pinned(w/'payload-file-index.json',IS);refs()
 # Single orphan target has no distinct ancestor: default nonforced push cannot
 # fast-forward or replace any different concurrently-created seed head.
 run(['git','--git-dir='+str(g),*auth,'-c','http.postBuffer=67108864','push','--porcelain',url,commit+':refs/heads/'+REF]);assert run(['git',*auth,'ls-remote',url,'refs/heads/'+REF]).split()[0]==commit
 token=run(['gh','auth','token']);req=urllib.request.Request('https://api.github.com/repos/'+REPO+'/git/blobs/'+BLOB,headers={'Authorization':'Bearer '+token,'Accept':'application/vnd.github.raw+json','Accept-Encoding':'identity','User-Agent':'exact-source48-public-ZIP-seed-proof'})
 full=hashlib.sha256();gg=hashlib.sha1(f'blob {SIZE}\0'.encode());n=0
 with urllib.request.urlopen(req,timeout=90)as r:
  assert r.status==200
  for b in iter(lambda:r.read(196608),b''):n+=len(b);assert n<=SIZE;full.update(b);gg.update(b)
 assert n==SIZE and full.hexdigest()==ZIP_SHA and gg.hexdigest()==BLOB;assert refs()==before
 fsck=run(['git','--git-dir='+str(g),'fsck','--full']);size=sum(p.stat().st_size for p in g.rglob('*')if p.is_file())
 proof={**plan,'kind':'actual-source48-one-public-ZIP-standard-Git-seed-and-full-raw-proof','network_executed':True,'repository':REPO,'actual_backup_raw_HTTP_status':200,'actual_backup_raw_bytes':n,'actual_backup_raw_SHA256':full.hexdigest(),'actual_backup_raw_Git_SHA':gg.hexdigest(),'protected_refs_unchanged':before,'source_and_all_frozen_inputs_unchanged':True,'no_full_asset_READY_or_current_claimed':True,'git_fsck_exit_code':0,'own_RAM_Git_logical_bytes_removed':size}
 out=root/'actual-backup-zip56565-standard-Git-seed-full-raw-proof.json';out.write_text(json.dumps(proof,indent=2)+'\n');shutil.rmtree(g);print(json.dumps({'seed_proof':str(out),'seed_proof_sha256':sha(out),'only_own_RAM_Git_removed':size,'actual_seed_commit':commit,'latest_directory_unchanged':True}))
if __name__=='__main__':main()
