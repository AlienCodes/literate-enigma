"""Append three public transport controls on the existing owned record-only branch.

Only these control file commits are appended; preserve original record subtree,
all ancestors, protected source branches and master. No media is generated.
"""
import base64,hashlib,json,pathlib,subprocess,urllib.parse
D=pathlib.Path(__file__).resolve().parent;R='AlienCodes/literate-enigma';BR='codex/passed4k-records-43554669373-53';EXPECTED='689f2b9a1311232a6de391e574de9d42c81287d1';OLD='a4f8c2f497227940e0273e0a75b5caa723a049bd';MASTER='6355a02864ebae616b693200d9d26f74f5da80e9';PREFIX='视频修订定稿/归档记录/2026-11-14-已验收1篇-native-inline-run43554669373-原46';TREE='25cf175c31b6a1c5a35af4c0cfe3d203f4784359'
def api(path,method='GET',body=None):
 args=['gh','api','repos/'+R+'/'+path]
 if method!='GET':
  req=D/'current-contents-upload-request.json';req.write_text(json.dumps(body));args+=['--method',method,'--input',str(req)]
 p=subprocess.run(args,capture_output=True,text=True)
 if p.returncode:raise RuntimeError(p.stdout[:1000]+p.stderr[:1000])
 return json.loads(p.stdout)
def original_history(head):
 c=api('compare/'+OLD+'...'+head);assert c['behind_by']==0 and c['status'] in ('ahead','identical')
 t=api('git/trees/'+head+'?recursive=1');assert not t.get('truncated')
 e=next(x for x in t['tree'] if x['path']==PREFIX);assert e['type']=='tree' and e['sha']==TREE
 return {'head':head,'original_record_commit':OLD,'compare_status':c['status'],'behind_by':c['behind_by'],'original_record_tree':e['sha'],'original_subtree_unchanged':True}
start=api('git/ref/heads/'+BR)['object']['sha'];assert start==EXPECTED
assert api('git/ref/heads/master')['object']['sha']==MASTER
before=original_history(start);steps=[];current=start
for source,target,trigger in [('transport-input.json','.github/approved-asset-transport/input.json',False),('transport_approved_assets.py','.github/approved-asset-transport/transport.py',False),('transport-approved-public-assets.yml','.github/workflows/transport-approved-public-assets.yml',True)]:
 assert api('git/ref/heads/'+BR)['object']['sha']==current
 raw=(D/source).read_bytes();old=api('contents/'+urllib.parse.quote(target,safe='/')+'?ref='+urllib.parse.quote(current,safe=''))
 data={'message':('启动已验61/15/17公开Git资产精确备仓运输，不重制视频' if trigger else '保存已验61/15/17公开资产运输输入或程序 [skip ci]'),'content':base64.b64encode(raw).decode(),'branch':BR,'sha':old['sha']}
 result=api('contents/'+urllib.parse.quote(target,safe='/'),'PUT',data)
 expected=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest();assert result['content']['sha']==expected
 new=result['commit']['sha'];commit=api('git/commits/'+new);assert [x['sha'] for x in commit['parents']]==[current]
 steps.append({'source':source,'repository_path':target,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'commit':new,'parent':current,'replaced_git_blob':old['sha'],'stored_git_blob':result['content']['sha'],'push_trigger_requested':trigger});current=new
 (D/'installation-observations.json').write_text(json.dumps({'repository':R,'owned_transport_branch':BR,'prior53_record_commit_retained_as_ancestor':OLD,'protected_refs_modified':False,'before':before,'steps':steps},ensure_ascii=False,indent=2)+'\n');print(json.dumps(steps[-1],ensure_ascii=False),flush=True)
end=api('git/ref/heads/'+BR)['object']['sha'];assert end==current
assert api('git/ref/heads/master')['object']['sha']==MASTER
after=original_history(end);record={'repository':R,'owned_transport_branch':BR,'prior53_record_commit_retained_as_ancestor':OLD,'protected_refs_modified':False,'before':before,'steps':steps,'after':after,'installed_push_trigger_commit':end}
(D/'installation-observations.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'installed_push_trigger_commit':end,'main_master_source_refs_untouched':True},ensure_ascii=False),flush=True)
(D/'current-contents-upload-request.json').unlink()
