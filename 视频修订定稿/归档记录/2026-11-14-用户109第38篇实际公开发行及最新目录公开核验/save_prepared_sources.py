"""Save only three publisher source files to a new isolated skip-ci branch."""
from pathlib import Path
import subprocess,json,hashlib,urllib.request,urllib.parse,datetime,os,importlib.util
R=Path(__file__).resolve().parent;BR='codex/book38-tulip-mania-final-4k-hold06-v1';REPOS=['AlienCodes/literate-enigma','alienalgorithm/postgraduate-vocabulary']
PATHS={'.github/tulip-mania-release/publish_single.py':'publish_single.py','.github/tulip-mania-release/PUBLICATION-PROFILE.json':'PUBLICATION-PROFILE.json','.github/workflows/publish-book38-tulip-mania-4k-hold06-v1.yml':'publish-single.yml'}
assert not (R/'MANIFEST.json').exists();spec=importlib.util.spec_from_file_location('prepared_book38_publisher',R/'publish_single.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
try:m.validate_config({})
except (AssertionError,KeyError):pass
else:raise AssertionError('Absent actual validation must fail closed')
assert m.SOURCE_ID=='19' and m.BOOK_ORDER=='38' and m.TAG=='book38-tulip-mania-final-4k-hold06-v1'
def sha(b):return hashlib.sha256(b).hexdigest()
def blob(b):return hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
def api(repo,path,missing=False):
 assert path.startswith(('git/','actions/'))
 p=subprocess.run(['gh','api','repos/'+repo+'/'+path],capture_output=True,text=True)
 if missing and p.returncode and 'HTTP 404' in p.stderr:return None
 if p.returncode:raise RuntimeError(p.stderr)
 return json.loads(p.stdout)
for repo in REPOS:assert api(repo,'git/ref/heads/'+BR,True) is None,'Do not overwrite any existing branch'
G=R/'code-only-git';G.mkdir();
def git(*args,input=None):
 p=subprocess.run(['git','-C',str(G),*args],input=input,capture_output=True,text=True,check=True,env={**os.environ,'TMPDIR':str(R)});return p.stdout.strip()
git('init','--initial-branch='+BR);git('config','user.name','Codex');git('config','user.email','codex@users.noreply.github.com')
data={p:(R/n).read_bytes() for p,n in PATHS.items()}
for path,b in data.items():
 target=G/path;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(b)
git('add','--',*PATHS);git('-c','commit.gpgsign=false','commit','--no-verify','-m','Prepare book38 user109 single-MP4 publisher sources only [skip ci]');commit=git('rev-parse','HEAD');assert git('rev-list','--parents','-n','1',commit)==commit
result={'kind':'book38-source19-user109-code-only-publisher-dual-storage','source_id':'19','book_order':'38','branch':BR,'actual_code_commit':commit,'source_files_count':3,'MANIFEST_created':False,'workflow_trigger_requested':False,'Release_created_or_queried':False,'media_or_QA_or_rootstate_or_PDF_collected':False,'local_absent_actual_manifest_rejected':True,'archives':[]}
for repo in REPOS:
 assert api(repo,'git/ref/heads/'+BR,True) is None
 git('-c','credential.helper=','-c','credential.helper=!gh auth git-credential','push','--quiet','https://github.com/'+repo+'.git',commit+':refs/heads/'+BR)
 assert api(repo,'git/ref/heads/'+BR)['object']['sha']==commit
 c=api(repo,'git/commits/'+commit);assert c['parents']==[];t=api(repo,'git/trees/'+c['tree']['sha']+'?recursive=1');assert not t.get('truncated');files={x['path']:x for x in t['tree'] if x['type']=='blob'};assert set(files)==set(PATHS)
 actual=[]
 for path,b in data.items():
  f=files[path];assert f['mode']=='100644' and f['size']==len(b) and f['sha']==blob(b)
  url='https://raw.githubusercontent.com/'+repo+'/'+commit+'/'+urllib.parse.quote(path,safe='/')
  with urllib.request.urlopen(url,timeout=60) as response:raw=response.read();assert response.status==200
  assert raw==b;actual.append({'repo_path':path,'bytes':len(raw),'sha256':sha(raw),'git_blob_sha':f['sha'],'immutable_HTTP200_exact_bytes':True})
 runs=api(repo,'actions/runs?branch='+urllib.parse.quote(BR,safe='')+'&per_page=10');assert runs['total_count']==0,'Code-only skip-ci preparation must not create a publication run'
 result['archives'].append({'repository':repo,'actual_commit':commit,'orphan_commit':True,'tree_sha':c['tree']['sha'],'exact_three_file_blob_set':True,'immutable_files':actual,'actual_workflow_run_count':runs['total_count']});(R/'ACTUAL-CODE-ONLY-DUAL-SAVE.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'repository':repo,'actual_commit':commit,'exact_code_files':3,'immutable_readback_passed':True,'actual_workflow_runs':0},ensure_ascii=False),flush=True)
result.update(completed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),actual_dual_commit_identical=True,no_other_publisher_branch_or_canonical_ref_modified=True);(R/'ACTUAL-CODE-ONLY-DUAL-SAVE.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'receipt':str(R/'ACTUAL-CODE-ONLY-DUAL-SAVE.json'),'receipt_sha256':sha((R/'ACTUAL-CODE-ONLY-DUAL-SAVE.json').read_bytes()),'actual_dual_commit':commit,'no_manifest_trigger_or_Release':True},ensure_ascii=False),flush=True)
