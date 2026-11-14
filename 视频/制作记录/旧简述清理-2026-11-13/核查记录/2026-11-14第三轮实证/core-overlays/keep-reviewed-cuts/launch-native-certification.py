from pathlib import Path
import json,subprocess,hashlib,base64
O=Path(__file__).parent;D=O/'native-ready';repo='AlienCodes/literate-enigma';branch='codex/finish-05-and-summaries-20261112'
def api(path,data=None,method='GET'):
 args=['gh','api','repos/'+repo+'/'+path]
 if data is not None:args+=['--method',method,'--input','-']
 return json.loads(subprocess.check_output(args,input=None if data is None else json.dumps(data).encode()))
parent=api('git/ref/heads/'+branch)['object']['sha'];master=api('git/ref/heads/master')['object']['sha'];files=[]
for p in sorted(D.rglob('*')):
 if p.is_file():
  rel=str(p.relative_to(D));assert rel.startswith('.github/reviewed-cuts-certification/') or rel=='.github/workflows/reviewed-cuts-certification.yml';files.append({'path':rel,'SHA256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size})
plan={'repository':repo,'branch':branch,'parent':parent,'master_guard':master,'files':files,'touches_production_runner_or_source':False,'mode':'independent-native-certification-only'};(O/'native-launch-reviewed-plan.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n')
updates=[]
for f in files:
 raw=(D/f['path']).read_bytes();b=api('git/blobs',{'content':base64.b64encode(raw).decode(),'encoding':'base64'},'POST');updates.append({'path':f['path'],'mode':'100644','type':'blob','sha':b['sha']})
base=api('git/commits/'+parent)['tree']['sha'];tree=api('git/trees',{'base_tree':base,'tree':updates},'POST')['sha'];c=api('git/commits',{'message':'Independently certify reviewed cuts preservation with real02 read-write controls and original complete fastcheck','tree':tree,'parents':[parent]},'POST')['sha'];assert api('git/ref/heads/'+branch)['object']['sha']==parent,'Concurrent writer changed branch; do not overwrite';api('git/refs/heads/'+branch,{'sha':c,'force':False},'PATCH');assert api('git/ref/heads/master')['object']['sha']==master
state={**plan,'commit':c,'stage':'independent-native-workflow-triggered-by-push'};(O/'native-launch-state.json').write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'commit':c,'parent':parent,'master_unchanged':True,'files':len(files)}))
