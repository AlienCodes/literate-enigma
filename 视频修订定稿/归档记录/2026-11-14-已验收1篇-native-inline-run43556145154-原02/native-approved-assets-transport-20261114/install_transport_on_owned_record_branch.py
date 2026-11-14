"""Append only public transport controls to an owned closed asset-record branch."""
import base64,hashlib,json,pathlib,subprocess,urllib.parse
D=pathlib.Path(__file__).resolve().parent;R='AlienCodes/literate-enigma';BR='codex/passed4k-records-43554669373-53';EXPECTED='a4f8c2f497227940e0273e0a75b5caa723a049bd'
def api(path,method='GET',body=None):
 args=['gh','api','repos/'+R+'/'+path]
 if method!='GET':
  req=D/'current-contents-upload-request.json';req.write_text(json.dumps(body));args+=['--method',method,'--input',str(req)]
 p=subprocess.run(args,capture_output=True,text=True)
 if p.returncode:raise RuntimeError(p.stdout[:1000]+p.stderr[:1000])
 return json.loads(p.stdout)
start=api('git/ref/heads/'+BR)['object']['sha'];assert start==EXPECTED
steps=[]
for source,target,trigger in [('transport-input.json','.github/approved-asset-transport/input.json',False),('transport_approved_assets.py','.github/approved-asset-transport/transport.py',False),('transport-approved-public-assets.yml','.github/workflows/transport-approved-public-assets.yml',True)]:
 raw=(D/source).read_bytes();data={'message':('启动已验02/49公开Git资产精确备仓运输，不重制视频'if trigger else'保存已验公开资产运输输入/程序 [skip ci]'),'content':base64.b64encode(raw).decode(),'branch':BR};result=api('contents/'+urllib.parse.quote(target,safe='/'),'PUT',data);assert result['content']['sha']==hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest();steps.append({'source':source,'repository_path':target,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'commit':result['commit']['sha'],'stored_git_blob':result['content']['sha'],'push_trigger_requested':trigger});(D/'installation-observations.json').write_text(json.dumps({'repository':R,'owned_transport_branch':BR,'prior53_record_commit_retained_as_ancestor':EXPECTED,'protected_refs_modified':False,'steps':steps},ensure_ascii=False,indent=2)+'\n');print(json.dumps(steps[-1],ensure_ascii=False),flush=True)
end=api('git/ref/heads/'+BR)['object']['sha'];assert end==steps[-1]['commit'];assert api('git/ref/heads/master')['object']['sha']=='6355a02864ebae616b693200d9d26f74f5da80e9';print(json.dumps({'installed_push_trigger_commit':end,'repository':R,'branch':BR,'main_master_source_refs_untouched':True}),flush=True)
# Request bodies contain only already-public code/metadata, but avoid retaining
# redundant base64 copies. Original code and exact hashes stay in this folder.
(D/'current-contents-upload-request.json').unlink()
