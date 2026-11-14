"""Copy only two frozen, already-approved PUBLIC asset Git commits to backup.

No synthesis, model/cache/PCM access, video edits or quality reclassification.
This runs on GitHub's own runner to avoid a stalled workstation receive-pack.
"""
import argparse,datetime,hashlib,json,os,pathlib,subprocess,tempfile
p=argparse.ArgumentParser();p.add_argument('--input',required=True);p.add_argument('--out',required=True);a=p.parse_args();cfg=json.loads(pathlib.Path(a.input).read_text());DEST='AlienCodes/literate-enigma';SOURCE='alienalgorithm/postgraduate-vocabulary';MASTER='6355a02864ebae616b693200d9d26f74f5da80e9';assert os.environ['GITHUB_REPOSITORY']==DEST;assert cfg['destination']==DEST and cfg['source']==SOURCE;assert {x['source_id']for x in cfg['assets']}=={'02','49'}
report={'scope':'PUBLIC approved Git asset transport only, no synthesis/source or quality changes','source_repository':SOURCE,'destination_repository':DEST,'native_transport_run_id':os.environ['GITHUB_RUN_ID'],'native_transport_commit':os.environ['GITHUB_SHA'],'copied':[],'passed':False,'does_not_claim_new_video_quality_acceptance':True,'main_master_or_dedicated_source_branch_modified':False}
def save():pathlib.Path(a.out).write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
def run(args,cwd=None,binary=False):
 r=subprocess.run(args,cwd=cwd,capture_output=True,text=not binary)
 if r.returncode:raise RuntimeError((r.stderr.decode(errors='replace')if binary else r.stderr)[-3000:])
 return r.stdout if binary else r.stdout.strip()
backup='https://github.com/'+DEST+'.git';source='https://github.com/'+SOURCE+'.git';auth=['-c','credential.helper=!gh auth git-credential']
def protected():
 row=run(['git',*auth,'ls-remote',backup,'refs/heads/master']);assert row.split()[0]==MASTER
protected();save()
try:
 for item in cfg['assets']:
  assert item['asset_branch'].startswith('codex/passed4k-assets-') and item['source_id']in['02','49'];assert len(item['asset_commit'])==40
  d=pathlib.Path(tempfile.mkdtemp(prefix='approved-public-'+item['source_id']+'-',dir=os.environ['RUNNER_TEMP']));g=d/'objects.git';run(['git','init','--bare',str(g)])
  def git(*args,binary=False):return run(['git','--git-dir='+str(g),*args],binary=binary)
  # This source ref is an orphan assets-only history with exactly two commits;
  # no default-branch history, private producer cache or model tree is fetched.
  git('-c','credential.helper=','fetch','--no-tags','--depth=2',source,'refs/heads/'+item['asset_branch']);assert git('rev-parse','FETCH_HEAD')==item['asset_commit'];assert git('rev-parse',item['asset_commit']+':'+item['prefix'])==item['video_tree_sha']
  checked=[]
  for f in item['files_index']:
   blob=git('rev-parse',item['asset_commit']+':'+f['repo_path']);assert blob==f['git_blob_sha'];raw=git('cat-file','blob',blob,binary=True);assert len(raw)==f['bytes']and hashlib.sha256(raw).hexdigest()==f['sha256'];checked.append({'path':f['repo_path'],'git_blob_sha':blob,'bytes':len(raw),'sha256':f['sha256']})
  old=git(*auth,'ls-remote',backup,'refs/heads/'+item['asset_branch']);oldsha=old.split()[0]if old else None;assert oldsha is None or oldsha in item['commits'],('Unexpected asset destination',oldsha)
  git(*auth,'-c','http.postBuffer=209715200','push','--quiet',backup,item['asset_commit']+':refs/heads/'+item['asset_branch']);assert git(*auth,'ls-remote',backup,'refs/heads/'+item['asset_branch']).split()[0]==item['asset_commit'];protected()
  report['copied'].append({'source_id':item['source_id'],'asset_branch':item['asset_branch'],'exact_original_asset_commit':item['asset_commit'],'exact_video_tree_sha':item['video_tree_sha'],'all_fetched_original_blobs_SHA256_verified':True,'files':checked,'backup_ref_exactly_matches_original':True,'old_original_asset_refs_only_fast_forwarded':True});save();print(json.dumps({'copied_exact_original_commit':item['asset_commit'],'source_id':item['source_id'],'files':len(checked),'no_video_rebuild_or_append':True}),flush=True)
 report['passed']=True;report['completed_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();save()
except Exception as e:
 report['failure']=str(e);save();raise
