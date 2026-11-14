"""Retry only the independent dispatch harness import path; six runtime files unchanged."""
from pathlib import Path
import json,subprocess,base64,hashlib
O=Path(__file__).resolve().parent;repo='AlienCodes/literate-enigma';branch='codex/finish-05-and-summaries-20261112';rel='.github/producer-dispatch-certification/native-dispatch-tests.py'
def api(path,data=None,method='GET'):
 args=['gh','api','repos/'+repo+'/'+path]
 if data is not None:args+=['--method',method,'--input','-']
 return json.loads(subprocess.check_output(args,input=None if data is None else json.dumps(data).encode()))
parent=api('git/ref/heads/'+branch)['object']['sha'];master=api('git/ref/heads/master')['object']['sha'];assert master=='6355a02864ebae616b693200d9d26f74f5da80e9'
raw=(O/'native-ready'/rel).read_bytes();old=base64.b64decode(api('contents/'+rel+'?ref='+parent)['content']);assert raw!=old
assert raw.decode().replace('import sys\n','').replace('sys.path.insert(0, str(Path.cwd()))\n','')==old.decode()
blob=api('git/blobs',{'content':base64.b64encode(raw).decode(),'encoding':'base64'},'POST')['sha'];base=api('git/commits/'+parent)['tree']['sha'];tree=api('git/trees',{'base_tree':base,'tree':[{'path':rel,'mode':'100644','type':'blob','sha':blob}]},'POST')['sha'];c=api('git/commits',{'message':'Fix only native dispatch certification loader sys.path; preserve all six runtime programs and original gates','tree':tree,'parents':[parent]},'POST')['sha'];assert api('git/ref/heads/'+branch)['object']['sha']==parent;api('git/refs/heads/'+branch,{'sha':c,'force':False},'PATCH');assert api('git/ref/heads/master')['object']['sha']==master
j=json.loads((O/'native-launch-state.json').read_text());j.update({'parent':parent,'commit':c,'previous_failed_run_id':43562440630,'single_test_harness_loader_only_retry':True,'run_id':None,'stage':'retry-triggered-by-push','quality_pass_not_yet_claimed':True});j['files']=[{'path':str(p.relative_to(O/'native-ready')),'SHA256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size}for p in (O/'native-ready').rglob('*')if p.is_file()];(O/'native-launch-state.json').write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'commit':c,'parent':parent,'only_modified_path':rel,'master_unchanged':True}))
