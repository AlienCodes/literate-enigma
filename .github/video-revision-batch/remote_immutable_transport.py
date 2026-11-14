"""Sole CI immutable Git blob/tree transport; no local Git clone/object writes."""
from pathlib import Path
import argparse,base64,concurrent.futures,hashlib,json,subprocess

REPO='AlienCodes/literate-enigma'
ASSET_BRANCH='codex/rebuild-requests-assets-20261113'
PRODUCTION_BRANCH='codex/finish-05-and-summaries-20261112'

def api(path,data=None,method='GET'):
    cmd=['gh','api','repos/'+REPO+'/'+path]
    if data is not None:cmd+=['--method',method,'--input','-']
    return json.loads(subprocess.check_output(cmd,input=None if data is None else json.dumps(data).encode()))

def blob_id(raw):
    return hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()

def upload_assets(root,prefixes=None,receipt_path=None):
    root=Path(root).resolve();parent=api('git/ref/heads/'+ASSET_BRANCH)['object']['sha']
    current=api('git/commits/'+parent);base=current['tree']['sha']
    listing=api('git/trees/'+base+'?recursive=1');assert not listing.get('truncated')
    existing={x['path']:x['sha']for x in listing['tree']if x['type']=='blob'}
    files=[]
    for p in sorted((root/'.github').rglob('*')):
        if not p.is_file()or'__pycache__'in p.parts:continue
        rel=str(p.relative_to(root));assert rel.startswith('.github/')
        if prefixes and not any(rel==prefix or rel.startswith(prefix.rstrip('/')+'/')for prefix in prefixes):continue
        raw=p.read_bytes();files.append({'path':rel,'sha':blob_id(raw),'SHA256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw),'local':p})
    assert files
    def upload(row):
        if existing.get(row['path'])==row['sha']:return False
        result=api('git/blobs',{'content':base64.b64encode(row['local'].read_bytes()).decode(),'encoding':'base64'},'POST')
        assert result['sha']==row['sha'];return True
    with concurrent.futures.ThreadPoolExecutor(max_workers=4)as pool:uploaded=list(pool.map(upload,files))
    updates=[{'path':x['path'],'mode':'100644','type':'blob','sha':x['sha']}for x in files]
    tree=api('git/trees',{'base_tree':base,'tree':updates},'POST')['sha']
    commit=api('git/commits',{'message':'Freeze exact requested CI inputs by immutable remote blobs; same reviewed branch only [skip ci]','tree':tree,'parents':[parent]},'POST')['sha']
    assert api('git/ref/heads/'+ASSET_BRANCH)['object']['sha']==parent,'Concurrent asset writer; retain created objects but do not overwrite branch'
    api('git/refs/heads/'+ASSET_BRANCH,{'sha':commit,'force':False},'PATCH')
    assert api('git/ref/heads/'+ASSET_BRANCH)['object']['sha']==commit
    receipt={'kind':'sole-CI-remote-immutable-blob-tree-transport-no-local-Git','repository':REPO,'branch':ASSET_BRANCH,'parent':parent,'commit':commit,'base_tree':base,'tree':tree,'files':[{k:v for k,v in x.items()if k!='local'}for x in files],'new_remote_blobs_uploaded':sum(uploaded),'existing_remote_blobs_reused':len(files)-sum(uploaded),'local_asset47_closed_snapshot_not_written':True}
    if receipt_path:Path(receipt_path).write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
    return updates,commit,receipt

def launch(root,prefixes,state_path,message):
    updates,asset,receipt=upload_assets(root,prefixes,Path(state_path).with_name('immutable-asset-transport-receipt.json'))
    parent=api('git/ref/heads/'+PRODUCTION_BRANCH)['object']['sha'];master=api('git/ref/heads/master')['object']['sha'];base=api('git/commits/'+parent)['tree']['sha']
    tree=api('git/trees',{'base_tree':base,'tree':updates},'POST')['sha']
    commit=api('git/commits',{'message':message,'tree':tree,'parents':[parent]},'POST')['sha']
    assert api('git/ref/heads/'+PRODUCTION_BRANCH)['object']['sha']==parent,'Concurrent official producer writer; do not overwrite'
    api('git/refs/heads/'+PRODUCTION_BRANCH,{'sha':commit,'force':False},'PATCH')
    assert api('git/ref/heads/master')['object']['sha']==master
    state={'repository':REPO,'branch':PRODUCTION_BRANCH,'parent':parent,'commit':commit,'request_assets_commit':asset,'files':receipt['files'],'only_authorized_production_branch_reference_updated':True,'master_observed_unchanged':True,'transport':'remote immutable Git blobs/trees, closed asset47 clone untouched','stage':'actual-native-workflow-triggered-by-push'}
    Path(state_path).write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n')
    return state

def install_on_unlaunched_F(root):
    """Route only local input transport in a new F; native runtime is unchanged."""
    import ast,shutil
    root=Path(root).resolve();assert not(root/'TASK-STATE.json').exists()
    target=root/'.github/video-revision-batch/remote_immutable_transport.py'
    shutil.copyfile(Path(__file__),target)
    p=root/'start.py';source=p.read_text();lo=source.index('if args.bulk_upload:\n');hi=source.index('\nelse:',lo)
    replacement="""if args.bulk_upload:
    # Closed historical asset47 worktree is never written again.
    import importlib.util
    _sp = importlib.util.spec_from_file_location('actual_remote_input_transport', TASK / 'remote_immutable_transport.py')
    _transport = importlib.util.module_from_spec(_sp)
    _sp.loader.exec_module(_transport)
    updates, asset_commit, _asset_receipt = _transport.upload_assets(ROOT, receipt_path=ROOT/'immutable-asset-transport-receipt.json')
"""
    source=source[:lo]+replacement+source[hi:];ast.parse(source);p.write_text(source)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--prefix',action='append',required=True);p.add_argument('--state',type=Path,required=True);p.add_argument('--message',required=True);a=p.parse_args()
    r=launch(a.root,a.prefix,a.state,a.message);print(json.dumps({k:r[k]for k in ['repository','commit','request_assets_commit','stage']}),flush=True)
