"""Archive only this isolated native job's public certificate/logs; never cache/audio/model bytes."""
from pathlib import Path
import os,json,re,base64,urllib.request,urllib.error,hashlib
assert os.environ.get('GITHUB_ACTIONS')=='true';repo=os.environ['GITHUB_REPOSITORY'];assert repo=='AlienCodes/literate-enigma';rid=os.environ['GITHUB_RUN_ID'];variant=os.environ['CERT_VARIANT'];assert variant in ['original','keep-reviewed-gain'];branch=f'codex/core-gain-cert-{rid}-{variant}';prefix=f'core-gain-certification/{rid}/{variant}';token=os.environ['GH_TOKEN']
def api(path,data=None,method='GET'):
 req=urllib.request.Request('https://api.github.com/repos/'+repo+'/'+path,data=None if data is None else json.dumps(data).encode(),method=method,headers={'Authorization':'Bearer '+token,'Accept':'application/vnd.github+json','User-Agent':'core-gain-certification'})
 with urllib.request.urlopen(req) as r:return json.load(r)
master=api('git/ref/heads/master')['object']['sha'];parent=os.environ['GITHUB_SHA'];updates=[];rows=[]
for f in sorted(Path('certification-public').glob('*')):
 if not f.is_file() or f.suffix not in ['.json','.log']:continue
 assert re.fullmatch(r'[a-zA-Z0-9-]+\.(?:json|log)',f.name);raw=f.read_bytes();assert len(raw)<5*1024*1024
 if f.suffix=='.json':json.loads(raw)
 b=api('git/blobs',{'content':base64.b64encode(raw).decode(),'encoding':'base64'},'POST');updates.append({'path':prefix+'/'+f.name,'mode':'100644','type':'blob','sha':b['sha']});rows.append({'file':f.name,'bytes':len(raw),'SHA256':hashlib.sha256(raw).hexdigest()})
assert rows,'No certification outputs to archive; inspect native setup logs'
manifest={'run_id':int(rid),'source_commit':parent,'variant':variant,'native_certification_not_product_acceptance':True,'files':rows,'private_cache_models_audio_exported':False};raw=(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n').encode();b=api('git/blobs',{'content':base64.b64encode(raw).decode(),'encoding':'base64'},'POST');updates.append({'path':prefix+'/manifest.json','mode':'100644','type':'blob','sha':b['sha']})
base=api('git/commits/'+parent)['tree']['sha'];tree=api('git/trees',{'base_tree':base,'tree':updates},'POST')['sha'];commit=api('git/commits',{'message':f'Preserve native core gain certification {variant} [skip ci]','tree':tree,'parents':[parent]},'POST')['sha'];api('git/refs',{'ref':'refs/heads/'+branch,'sha':commit},'POST');assert api('git/ref/heads/master')['object']['sha']==master;print(json.dumps({'branch':branch,'commit':commit,'files':len(rows),'product_acceptance':False}))
