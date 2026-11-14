from pathlib import Path
import hashlib,json,os,shutil,subprocess
R=Path(__file__).resolve().parent;G=R/'code-only-git';BR='codex/book38-tulip-mania-final-4k-hold06-v1';P='.github/tulip-mania-release/MANIFEST.json';expected='f2e27cf6d3da7277a48a32978cbac6a4e9f8ec0e';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert sha(R/'MANIFEST.json')=='3828c49e1c8c490e3b06306b3725cfb639fe960b23eacb6b9d6bbe8a9b99927c'
def git(*args):return subprocess.check_output(['git','-C',str(G),*args],text=True,env={**os.environ,'TMPDIR':str(R)}).strip()
def api(repo,path):return json.loads(subprocess.check_output(['gh','api','repos/'+repo+'/'+path]))
assert git('rev-parse','HEAD')==expected and not git('status','--porcelain')
for repo in ['AlienCodes/literate-enigma','alienalgorithm/postgraduate-vocabulary']:assert api(repo,'git/ref/heads/'+BR)['object']['sha']==expected
shutil.copyfile(R/'MANIFEST.json',G/P);git('add','--',P);git('-c','commit.gpgsign=false','commit','--no-verify','-m','Publish actual user109 book38 source19 final after genuine sourceQA, normal18 V3 and dual-byte-verified archive')
commit=git('rev-parse','HEAD');assert git('diff-tree','--no-commit-id','--name-only','-r',commit)==P
receipt={'kind':'actual-user109-book38-single-MP4-native-publication-trigger','handoff_sha256':'34fef28e5b543d60a8fa6830e71b3f1bfeb43f8565faf83be6a145d6ed7e98e5','actual_dual_ready_sha256':'22c35859db9a673f2d77e530938a4da70754905bd1b76998785dd333343745f2','manifest_sha256':sha(R/'MANIFEST.json'),'commit':commit,'parent':expected,'changed_paths':[P],'branch':BR,'no_canonical_alias_source_media_or_QA_mutation':True,'archives':[]}
for repo in ['AlienCodes/literate-enigma','alienalgorithm/postgraduate-vocabulary']:
 assert api(repo,'git/ref/heads/'+BR)['object']['sha']==expected
 git('-c','credential.helper=','-c','credential.helper=!gh auth git-credential','push','--quiet','https://github.com/'+repo+'.git',commit+':refs/heads/'+BR)
 assert api(repo,'git/ref/heads/'+BR)['object']['sha']==commit
 receipt['archives'].append({'repository':repo,'actual_publisher_branch_commit':commit,'primary_native_publication_expected':repo.startswith('alienalgorithm/')})
 (R/'ACTUAL-MANIFEST-PUBLICATION-TRIGGER.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n');print(json.dumps(receipt['archives'][-1]),flush=True)
print(json.dumps({'commit':commit,'manifest_sha256':receipt['manifest_sha256'],'native_primary_publication_triggered':True}),flush=True)
