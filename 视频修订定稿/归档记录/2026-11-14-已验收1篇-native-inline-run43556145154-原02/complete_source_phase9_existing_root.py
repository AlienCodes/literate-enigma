"""Complete backup using the exact tree actually created despite the GitHub timeout."""
import json,subprocess,base64
from pathlib import Path
B=Path('/workspace/work/video-audit70-20261113');Q=Path('/workspace/work/video-source-publish-snapshot-20261114-v9');L=Path('/workspace/work/github-publication/target');repo='AlienCodes/literate-enigma';branch='codex/all-deliverables-20261113'
def api(route,method='GET',data=None):
 a=['gh','api','repos/'+repo+'/'+route]
 if method!='GET':a+=['-X',method]
 if data is not None:a+=['--input','-']
 return json.loads(subprocess.check_output(a,input=None if data is None else json.dumps(data).encode()))
r=json.loads((B/'PUBLISHED-SOURCE-STATE.json').read_text());assert len(r['archives'])==1 and r['asset_commit']=='0a556bb86b1b8186c004767c389ddb2331050ff3';old='1d9db4b41e413a624a7b0e3ece5ae295454d20b9';assert api('git/ref/heads/'+branch)['object']['sha']==old
proof=json.loads((B/'phase9-recovered-root-tree.json').read_text());newtree=proof['sha'];actual=api('git/trees/'+newtree)['tree'];assert {x['path']:x['sha']for x in actual}=={x['path']:x['sha']for x in proof['tree_payload']['tree']}
base=api('git/commits/'+old)['tree']['sha'];before=api('git/trees/'+base)['tree'];changed={'视频','新版定稿'};assert {x['path']:x['sha']for x in actual if x['path']not in changed}=={x['path']:x['sha']for x in before if x['path']not in changed}
assert api('git/ref/heads/master')['object']['sha']=='6355a02864ebae616b693200d9d26f74f5da80e9'
new=api('git/commits','POST',{'message':'保存phase9精确源稿与实证；GitHub超时后回读已实际创建的同一完整树 [skip ci]','tree':newtree,'parents':[old]})['sha'];api('git/refs/heads/'+branch,'PATCH',{'sha':new,'force':False});assert api('git/ref/heads/'+branch)['object']['sha']==new
for path in ['视频/脚本/05.json','视频/脚本/18.json','视频/脚本/49.json']:
 a=api('contents/'+path+'?ref='+new);assert base64.b64decode(a['content'])==(Q/path).read_bytes()
r['archives'].append({'repository':repo,'branch':branch,'source_commit':new,'previous_commit':old,'master_unchanged':True,'existing_exact_tree_read_back_after_API_timeout':newtree});(B/'PUBLISHED-SOURCE-STATE.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n')
for p in Q.rglob('*'):
 if p.is_file() and '.git'not in p.relative_to(Q).parts:
  target=L/p.relative_to(Q);target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(p.read_bytes())
print(json.dumps(r,ensure_ascii=False),flush=True)
