"""Isolated source69 asset transport proposal. No network without --execute and review pin.

Reads the mature collector's frozen payload. Creates no .git, pack, encoded-body,
MP4 or ZIP copies. Does not integrate main, create READY, or change quality gates.
The existing dual-blob/full-MP4/READY/current installer remains mandatory afterward.
"""
from __future__ import annotations
import argparse
import base64
from dataclasses import dataclass
import datetime as dt
import hashlib
import http.client
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import uuid
from typing import BinaryIO, Callable
import urllib.parse
import urllib.request

CHUNK=196608  # 192 KiB; encoded chunks at most 256 KiB.
PREFIX=b'{"encoding":"base64","content":"'
SUFFIX=b'"}'
MAX_BLOB=100_000_000
MAX_NEW_METADATA=8*1024*1024
REPOS=(('primary','alienalgorithm/postgraduate-vocabulary'),('backup','AlienCodes/literate-enigma'))
DENY={'b9a257a23820944ee95d568b67d1cd78947b1c1814bb70dc99a45871f488f778','55026ce1b7cdb7e9c1a72da2f715e3d9e6e6f45050a8ddd575dc052b09dca872','bcb37d8930d804988c95da94b9cfeaaab2c7b026df96e6e4567f9b698ce88fbf'}
HEX40=re.compile(r'^[0-9a-f]{40}$'); HEX64=re.compile(r'^[0-9a-f]{64}$')

class GuardError(RuntimeError): pass
def require(test, message):
    if not test: raise GuardError(message)
def load(p): return json.loads(Path(p).read_text())
def read_pinned_json(path, expected=None):
    # Parse exactly the bytes whose digest was checked, not a second file read.
    with Path(path).open('rb') as f:raw=f.read(2*1024*1024+1)
    require(len(raw)<=2*1024*1024,'Oversized pinned metadata')
    actual=hashlib.sha256(raw).hexdigest()
    if expected is not None:require(actual==expected,'Frozen metadata pin mismatch')
    return json.loads(raw),actual
def sha256(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(CHUNK),b''): h.update(b)
    return h.hexdigest()
def git_sha(kind, raw): return hashlib.sha1(kind.encode()+b' '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
def content_length(size):
    require(type(size) is int and 0<=size<=MAX_BLOB,'Invalid or unsupported blob size')
    return len(PREFIX)+4*((size+2)//3)+len(SUFFIX)
def file_pin(st): return (st.st_dev,st.st_ino,st.st_size,st.st_mtime_ns,st.st_ctime_ns)

@dataclass(frozen=True)
class Blob:
    path: Path
    size: int
    sha256: str
    git_sha: str
    pin: tuple

def inspect_blob(path, size, expected):
    p=Path(path); require(not p.is_symlink() and p.is_file(),'Payload leaf must be a regular nonsymlink')
    require(HEX64.fullmatch(expected) is not None and expected not in DENY,'Invalid or denied digest')
    content_length(size)
    with p.open('rb') as f:
        st=os.fstat(f.fileno()); require(st.st_size==size,'Local source size mismatch')
        h=hashlib.sha256(); g=hashlib.sha1(f'blob {size}\0'.encode()); n=0
        for b in iter(lambda:f.read(CHUNK),b''): h.update(b);g.update(b);n+=len(b)
        require(file_pin(os.fstat(f.fileno()))==file_pin(st),'Source changed during inspection')
    require(n==size and h.hexdigest()==expected,'Local source digest mismatch')
    return Blob(p,size,expected,g.hexdigest(),file_pin(st))

def encoded_body(stream: BinaryIO, blob: Blob):
    """No full-body buffer; preserve 0..2 bytes when an input read is short.

    Deliberately withhold the closing JSON suffix until source size/hashes pass.
    A midstream mismatch cannot produce a complete JSON upload body.
    """
    yield PREFIX
    h=hashlib.sha256(); g=hashlib.sha1(f'blob {blob.size}\0'.encode()); n=0; pending=b''
    while True:
        b=stream.read(CHUNK)
        require(isinstance(b,bytes) and len(b)<=CHUNK,'Binary bounded source read required')
        if not b: break
        n+=len(b); require(n<=blob.size,'Source grew during upload')
        h.update(b); g.update(b); joined=pending+b
        count=(len(joined)//3)*3
        if count: yield base64.b64encode(joined[:count])
        pending=joined[count:]
    require(n==blob.size and h.hexdigest()==blob.sha256 and g.hexdigest()==blob.git_sha,'Source changed during upload')
    if pending: yield base64.b64encode(pending)
    yield SUFFIX

def validated_source_body(blob):
    with blob.path.open('rb') as stream:
        require(file_pin(os.fstat(stream.fileno()))==blob.pin,'Source identity changed before upload')
        for piece in encoded_body(stream,blob):
            if piece==SUFFIX:
                require(file_pin(os.fstat(stream.fileno()))==blob.pin,'Source identity changed during upload')
            yield piece

def repo_path(path):
    require(isinstance(path,str) and path and not path.startswith('/'),'Invalid repository path')
    parts=path.split('/')
    require(all(p and p not in ('.','..','.git') and not any(c in p for c in '\0\n\r\t') for p in parts),'Unsafe repository path')
    require(str(PurePosixPath(path))==path,'Noncanonical repository path')
    return parts

def make_trees(files):
    """Return bottom-up trees with independent, exact Git tree identities."""
    nodes={'':{}}
    for f in files:
        parts=repo_path(f['repo_path']); require(HEX40.fullmatch(f['git_blob_sha']) is not None,'Bad Git blob SHA')
        require(f.get('mode','100644')=='100644','Only frozen regular payload files are supported')
        parent=''
        for name in parts[:-1]:
            child='/'.join(filter(None,[parent,name])); existing=nodes[parent].get(name)
            require(existing is None or existing==('tree',child),'File/directory collision')
            nodes[parent][name]=('tree',child);nodes.setdefault(child,{});parent=child
        require(parts[-1] not in nodes[parent],'Duplicate or conflicting repository path')
        nodes[parent][parts[-1]]=('blob',f['git_blob_sha'])
    result=[]; hashes={}
    for path in sorted(nodes,key=lambda p:(-p.count('/'),-len(p))):
        entries=[]; raw=[]
        for name,(kind,target) in sorted(nodes[path].items(),key=lambda x:(x[0]+('/' if x[1][0]=='tree' else '')).encode('utf-8')):
            sha=hashes[target] if kind=='tree' else target; mode='040000' if kind=='tree' else '100644'
            entries.append({'path':name,'mode':mode,'type':kind,'sha':sha})
            raw.append(('40000' if kind=='tree' else '100644').encode()+b' '+name.encode('utf-8')+b'\0'+bytes.fromhex(sha))
        hashes[path]=git_sha('tree',b''.join(raw)); result.append({'path':path,'sha':hashes[path],'tree':entries})
    return result,hashes

def commit_spec(root_tree, created):
    date=dt.datetime.fromisoformat(created.replace('Z','+00:00'))
    require(date.tzinfo is not None,'Frozen prepared timestamp needs timezone')
    stamp=int(date.timestamp()); iso=dt.datetime.fromtimestamp(stamp,dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    message='保存书56源69真实合格定稿及原证据资产（低磁盘流式运输） [skip ci]\n'
    identity={'name':'Codex','email':'codex@users.noreply.github.com','date':iso}
    raw=(f'tree {root_tree}\nauthor Codex <codex@users.noreply.github.com> {stamp} +0000\ncommitter Codex <codex@users.noreply.github.com> {stamp} +0000\n\n'+message).encode()
    return {'sha':git_sha('commit',raw),'raw':raw,'data':{'message':message,'tree':root_tree,'parents':[],'author':identity,'committer':identity}}

def prepare_bundle(work_dir, handoff_path, handoff_sha, prepared_sha, index_sha):
    w=Path(work_dir).resolve(); pay=(w/'payload').resolve(); hp=Path(handoff_path).resolve()
    h,_=read_pinned_json(hp,handoff_sha);meta,_=read_pinned_json(w/'prepared-archive.json',prepared_sha);index,_=read_pinned_json(w/'payload-file-index.json',index_sha)
    require(h['status']=='passed_actual_normal18_post_only_for_permanent_archive' and h['production_delivery_eligible'] is True and h['preview_only'] is False,'Only qualified production handoff')
    require(h['kind']=='actual-new-native-source-QA-then-authorized-normal18-local-tail' and h['actual_new_source_QA_then_final_normal18_verified'] is True,'Actual new source QA required')
    require(len(h['articles'])==len(meta['articles'])==1,'Exact single article required')
    a=h['articles'][0]; row=meta['articles'][0]
    require(a['source_id']==row['source_id']=='69' and a['new_id']==row['new_id']=='56' and a['passed_per_article'] is row['passed_per_article'] is True,'Only exact source69/book56')
    require(row['production_delivery_eligible'] is True and row['preview_only'] is False and row['postprocessing_full_V3_handoff_sha256']==handoff_sha==meta['actual_handoff_sha256'],'Prepared final/H not exact')
    require(all(a['final_mp4'][k]==row[k] for k in ('bytes','sha256')),'Final MP4 binding mismatch')
    require(meta['asset_branch']==f"codex/passed4k-assets-{h['source_run']}-69-hold18-postonly-v1",'Only exact isolated asset branch')
    prefix=meta['prefix']; require(prefix.startswith('视频修订定稿/') and len(repo_path(prefix))==2,'Only frozen single archive prefix')
    unique={}; files=[]
    for x in index:
        parts=repo_path(x['repo_path']); require(x['repo_path'].startswith(prefix+'/'),'Out-of-prefix payload')
        p=pay.joinpath(*parts); require(p.resolve().is_relative_to(pay),'Out-of-payload leaf')
        b=inspect_blob(p,x['bytes'],x['sha256']); old=unique.get(b.git_sha)
        require(old is None or (old.size,old.sha256)==(b.size,b.sha256),'Blob collision')
        unique.setdefault(b.git_sha,b);files.append({**x,'git_blob_sha':b.git_sha})
    require(len(files)==len({f['repo_path'] for f in files}),'Duplicate payload index path')
    bound=[f for f in files if f['sha256']==handoff_sha]
    require(bound and any(f['repo_path']==row['video_repo_path'] and (f['bytes'],f['sha256'])==(row['bytes'],row['sha256']) for f in files),'H/final missing from payload')
    trees,hashes=make_trees(files);commit=commit_spec(hashes[''],meta['created_utc'])
    controls=[(hp,handoff_sha),(w/'prepared-archive.json',prepared_sha),(w/'payload-file-index.json',index_sha)]
    return {'w':w,'hp':hp,'handoff_sha':handoff_sha,'prepared_sha':prepared_sha,'index_sha':index_sha,'control_pins':controls,'meta':meta,'files':files,'blobs':unique,'trees':trees,'hashes':hashes,'commit':commit,'prefix':prefix}

def recheck_controls(bundle):
    for path,expected in bundle.get('control_pins',[]):read_pinned_json(path,expected)

def environment_https_connection():
    """Use the same environment HTTP CONNECT route as urllib/gh, never log its URL."""
    proxy=urllib.request.getproxies().get('https')
    if not proxy or urllib.request.proxy_bypass('api.github.com'):
        return http.client.HTTPSConnection('api.github.com',timeout=90)
    route=urllib.parse.urlsplit(proxy)
    require(route.scheme=='http' and route.hostname and not route.query and not route.fragment and route.path in ('','/'),'Unsupported environment HTTPS proxy route')
    c=http.client.HTTPSConnection(route.hostname,port=route.port or 80,timeout=90)
    headers={}
    if route.username is not None:
        credentials=urllib.parse.unquote(route.username)+':'+urllib.parse.unquote(route.password or '')
        headers['Proxy-Authorization']='Basic '+base64.b64encode(credentials.encode()).decode('ascii')
    c.set_tunnel('api.github.com',443,headers=headers)
    return c

class GitDataClient:
    def __init__(self, token, connection_factory=None):
        self._token=token;self._factory=connection_factory or environment_https_connection;self.safe_stage=None
    def _headers(self,accept='application/vnd.github+json'):
        return {'Authorization':'Bearer '+self._token,'Accept':accept,'Accept-Encoding':'identity','Content-Type':'application/json','User-Agent':'Codex-reviewed-source69-streaming-asset-transport','X-GitHub-Api-Version':'2022-11-28'}
    def api(self,repo,path,method='GET',data=None,allow404=False):
        self.safe_stage={'method':method,'git_endpoint':path}
        c=self._factory(); raw=None if data is None else json.dumps(data,separators=(',',':'),ensure_ascii=False).encode()
        try:
            c.request(method,'/repos/'+repo+'/'+urllib.parse.quote(path,safe='/?=&%'),body=raw,headers=self._headers());r=c.getresponse()
            if allow404 and r.status==404: r.read();return None
            require(r.status==(201 if method=='POST' else 200),f'Git API {method} failed status {r.status}; no ref progression')
            payload=r.read(2*1024*1024+1);require(len(payload)<=2*1024*1024,'Oversized metadata response')
            try:return json.loads(payload)
            except (ValueError,UnicodeError) as e: raise GuardError('Malformed Git API JSON; no ref progression') from e
        finally:c.close()
    def post_blob(self,repo,blob):
        self.safe_stage={'method':'POST','git_endpoint':'git/blobs','expected_git_blob_sha':blob.git_sha}
        c=self._factory()
        try:
            c.putrequest('POST','/repos/'+repo+'/git/blobs',skip_accept_encoding=True)
            for k,v in self._headers().items():c.putheader(k,v)
            c.putheader('Content-Length',str(content_length(blob.size)));c.endheaders()
            n=0
            for piece in validated_source_body(blob): c.send(piece);n+=len(piece)
            require(n==content_length(blob.size),'Encoded request length mismatch')
            r=c.getresponse();require(r.status==201,f'Blob POST failed status {r.status}; no ref progression')
            raw=r.read(65537);require(len(raw)<=65536,'Oversized blob JSON response')
            try:result=json.loads(raw)
            except (ValueError,UnicodeError) as e:raise GuardError('Malformed blob response; no ref progression')from e
            require(result.get('sha')==blob.git_sha,'Blob POST returned wrong Git SHA; no ref progression')
        finally:c.close()
    def verify_blob(self,repo,blob):
        self.safe_stage={'method':'GET','git_endpoint':'git/blobs/'+blob.git_sha}
        c=self._factory()
        try:
            c.request('GET','/repos/'+repo+'/git/blobs/'+blob.git_sha,headers=self._headers('application/vnd.github.raw+json'));r=c.getresponse()
            require(r.status==200,'Raw blob readback failed; no ref progression')
            require(r.getheader('Content-Encoding') in (None,'identity'),'Unexpected raw content encoding')
            declared=r.getheader('Content-Length')
            if declared is not None:require(int(declared)==blob.size,'Wrong raw Content-Length')
            h=hashlib.sha256();g=hashlib.sha1(f'blob {blob.size}\0'.encode());n=0
            while True:
                b=r.read(CHUNK)
                if not b:break
                n+=len(b);require(n<=blob.size,'Oversized raw blob readback');h.update(b);g.update(b)
            require(n==blob.size and h.hexdigest()==blob.sha256 and g.hexdigest()==blob.git_sha,'Wrong raw blob bytes/digest; no ref progression')
        finally:c.close()

def verify_remote_tree(client,repo,bundle):
    root=client.api(repo,'git/trees/'+bundle['hashes']['']+'?recursive=1')
    require(root.get('sha')==bundle['hashes'][''] and root.get('truncated') is False,'Root tree mismatch/truncation')
    actual={x['path']:x for x in root['tree']}
    require(len(actual)==len(root['tree']),'Duplicate remote tree path')
    expected={f['repo_path']:{'path':f['repo_path'],'mode':'100644','type':'blob','sha':f['git_blob_sha'],'size':f['bytes']} for f in bundle['files']}
    for path,sha in bundle['hashes'].items():
        if path:expected[path]={'path':path,'mode':'040000','type':'tree','sha':sha}
    require(set(actual)==set(expected),'Remote recursive tree leaf/directory set mismatch')
    require(all(all(actual[p].get(k)==v for k,v in e.items()) for p,e in expected.items()),'Remote tree mode/size/SHA mismatch')

def publish_repository(client,repo,bundle,journal: Callable):
    require(repo in {r for _,r in REPOS},'Unsupported repository')
    recheck_controls(bundle)
    branch=bundle['meta']['asset_branch']; target=bundle['commit']['sha']
    initial=client.api(repo,'git/ref/heads/'+branch,allow404=True)
    require(initial is None or initial['object']['sha']==target,'Existing isolated branch differs; refuse update')
    # No ref mutation until every local/remote blob, tree, and commit has passed.
    for sha,b in bundle['blobs'].items():
        if initial is None:client.post_blob(repo,b)
        client.verify_blob(repo,b);journal({'repository':repo,'action':'raw-blob-exact','git_sha':sha,'bytes':b.size,'sha256':b.sha256})
    if initial is None:
        for tree in bundle['trees']:
            made=client.api(repo,'git/trees','POST',{'tree':tree['tree']});require(made.get('sha')==tree['sha'],'Created tree Git SHA mismatch')
        made=client.api(repo,'git/commits','POST',bundle['commit']['data']);require(made.get('sha')==target,'Created commit Git SHA mismatch')
    verify_remote_tree(client,repo,bundle)
    raw_commit=client.api(repo,'git/commits/'+target)
    c=bundle['commit']['data']
    require(raw_commit.get('sha')==target and raw_commit['tree']['sha']==c['tree'] and raw_commit['parents']==[],'Commit tree/parents mismatch')
    require(raw_commit['message'].rstrip('\n')==c['message'].rstrip('\n'),'Commit message mismatch')
    for role in ('author','committer'):
        require(all(raw_commit[role].get(k)==c[role][k] for k in ('name','email','date')),'Commit identity/date mismatch')
    recheck_controls(bundle)
    latest=client.api(repo,'git/ref/heads/'+branch,allow404=True)
    require(latest is None or latest['object']['sha']==target,'Isolated branch changed during verification')
    if latest is None:
        # Create-only has an atomic nonexistence guard. No PATCH, force, or fake CAS.
        created=client.api(repo,'git/refs','POST',{'ref':'refs/heads/'+branch,'sha':target})
        require(created.get('object',{}).get('sha')==target,'Created ref mismatch')
    require(client.api(repo,'git/ref/heads/'+branch)['object']['sha']==target,'Final isolated ref readback mismatch')
    journal({'repository':repo,'action':'isolated-ref-exact','asset_commit':target,'new_ref_created':latest is None})
    return {'asset_commit':target,'commits':[target],'asset_branch':branch,'root_tree':bundle['hashes'][''],'repository':repo,'video_tree_sha':bundle['hashes'][bundle['prefix']],'files':len(bundle['files']),'remote_asset_ref_verified':True,'main_or_master_changed':False,'files_index':bundle['files'],'transport':'root-reviewed-exact-source69-streaming-Git-data-no-local-Git','all_blobs_raw_HTTP_readback_exact':True}

def allocated_budget(path,block):
    st=Path(path).stat()
    return max(block if Path(path).is_dir() else ((st.st_size+block-1)//block)*block,st.st_blocks*512)

def write_small(path,value,owned):
    raw=(json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode();new=Path(path);tmp=new.with_name(new.name+'.stream-atomic.tmp')
    block=os.statvfs(new.parent).f_frsize
    total=sum(allocated_budget(p,block) for p in owned if p.exists())
    temporary=((len(raw)+block-1)//block)*block
    # Include old+temporary files, owned attempt directories, and 64KiB reserve
    # for parent/attempt directory growth. This is a controlled-file allocation
    # budget, not a claim about kernel journals or unrelated concurrent writers.
    require(total+temporary+16*block<=MAX_NEW_METADATA,'Transport allocated-file/temporary/directory budget exceeds 8MiB')
    require(os.statvfs(new.parent).f_bavail*os.statvfs(new.parent).f_frsize>=2*len(raw)+4*1024*1024,'Insufficient metadata reserve')
    with tmp.open('xb')as f:f.write(raw);f.flush();os.fsync(f.fileno())
    os.replace(tmp,new);owned.add(new)

def write_exact_asset(path,value,owned):
    """An existing successful partial-repository result is retained, never rewritten."""
    p=Path(path)
    if p.exists():
        require(load(p)==value,'Existing asset metadata differs; inspect instead of overwriting')
        owned.add(p)
    else:write_small(p,value,owned)

def main():
    p=argparse.ArgumentParser();p.add_argument('--work-dir',required=True);p.add_argument('--handoff',required=True);p.add_argument('--handoff-sha256',required=True);p.add_argument('--prepared-sha256',required=True);p.add_argument('--index-sha256',required=True);p.add_argument('--approval');p.add_argument('--execute',action='store_true');a=p.parse_args()
    b=prepare_bundle(a.work_dir,a.handoff,a.handoff_sha256,a.prepared_sha256,a.index_sha256)
    plan={'kind':'source69-streaming-Git-data-local-plan-not-upload','handoff_sha256':a.handoff_sha256,'prepared_sha256':a.prepared_sha256,'index_sha256':a.index_sha256,'files':len(b['files']),'unique_blobs':len(b['blobs']),'unique_raw_bytes':sum(x.size for x in b['blobs'].values()),'largest_blob_bytes':max(x.size for x in b['blobs'].values()),'asset_commit':b['commit']['sha'],'root_tree':b['hashes'][''],'isolated_branch':b['meta']['asset_branch'],'controlled_metadata_allocated_file_budget_bytes':MAX_NEW_METADATA,'budget_includes_temporary_files_owned_attempt_directories_and64KiB_directory_reserve':True,'kernel_filesystem_journal_or_other_writers_not_claimed':True,'chunk_read_bytes':CHUNK,'maximum_encoded_chunk_bytes':4*((CHUNK+2)//3),'no_git_pack_or_media_or_request_body_copies':True,'network_executed':False}
    if not a.execute:print(json.dumps(plan,ensure_ascii=False));return
    require(a.approval is not None,'Root code and actual-H adoption pin required before any network')
    decision,approval_sha=read_pinned_json(a.approval)
    require(decision.get('kind')=='root-reviewed-exact-source69-streaming-asset-transport' and decision.get('approved') is True,'Missing exact root adoption')
    require(decision.get('approved_module_sha256')==sha256(__file__) and decision.get('source_id')=='69' and decision.get('new_id')=='56','Wrong approved code/scope')
    require(all(decision.get(k)==getattr(a,k) for k in ('handoff_sha256','prepared_sha256','index_sha256')) and decision.get('only_new_isolated_ref_or_exact_readonly_resume') is True,'Wrong adopted frozen input pins/ref scope')
    require(not (b['w']/'assets.git').exists() and not (b['w']/'assets.index').exists(),'Separate transport from any existing local Git work')
    # Keep every attempt's stop/journal record. Re-running never relabels an old failure.
    owned={p for d in b['w'].glob('streaming-attempt-*') if d.is_dir() and not d.is_symlink() for p in [d,*d.iterdir()] if not p.is_symlink() and (p.is_dir() or p.is_file())}
    owned.update(p for p in [b['w']/'assets-primary.json',b['w']/'assets-backup.json',b['w']/'asset-local.json'] if p.exists())
    block=os.statvfs(b['w']).f_frsize
    require(sum(allocated_budget(p,block) for p in owned)+17*block<MAX_NEW_METADATA,'No attempt-directory allocation budget')
    attempt=b['w']/('streaming-attempt-'+dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%S')+'-'+uuid.uuid4().hex[:8]);attempt.mkdir();owned.add(attempt)
    records=[]; before=os.statvfs(b['w']).f_bavail*os.statvfs(b['w']).f_frsize
    def journal(row):
        records.append(row);write_small(attempt/'actual-object-journal.json',{'kind':'actual-object-log-not-READY','records':records},owned)
    write_small(attempt/'approved-local-plan.json',{**plan,'approval_sha256':approval_sha},owned)
    try:
        recheck_controls(b)
        token=subprocess.check_output(['gh','auth','token'],text=True).strip();client=GitDataClient(token)
        results=[]
        for role,repo in REPOS:
            result=publish_repository(client,repo,b,journal)
            write_exact_asset(b['w']/f'assets-{role}.json',result,owned);results.append(result)
        require(results[0]['asset_commit']==results[1]['asset_commit'] and results[0]['video_tree_sha']==results[1]['video_tree_sha'],'Dual identity mismatch')
        recheck_controls(b)
        write_exact_asset(b['w']/'asset-local.json',{k:results[0][k]for k in ('asset_commit','commits','asset_branch','root_tree')},owned)
        write_small(attempt/'dual-transport-completion-not-READY.json',{'kind':'actual-dual-isolated-assets-raw-object-transport-not-READY','source_id':'69','new_id':'56','asset_commit':results[0]['asset_commit'],'handoff_sha256':a.handoff_sha256,'all_blobs_both_repos_full_raw_SHA256_verified':True,'owned_controlled_file_and_directory_allocated_budget_bytes':sum(allocated_budget(x,block) for x in owned),'owned_metadata_logical_file_bytes':sum(x.stat().st_size for x in owned if x.is_file()),'host_available_before':before,'host_available_after':os.statvfs(b['w']).f_bavail*os.statvfs(b['w']).f_frsize,'requires_original_dual_blob_verifier_complete_MP4_HTTP_and_emit_READY':True,'main_or_master_modified':False},owned)
    except Exception as e:
        # Store only class and safe stage summary; no token, source content, or response bodies.
        write_small(attempt/'stopped-not-READY.json',{'kind':'streaming-transport-stopped-not-READY','error_class':type(e).__name__,'safe_Git_stage':getattr(locals().get('client'),'safe_stage',None),'completed_journal_records':len(records),'no_automatic_write_retry':True,'inspect_remote_exact_state_before_any_retry':True,'may_have_orphan_blobs_trees_commit_or_one_completed_isolated_ref':True,'main_or_master_modified':False},owned)
        raise GuardError('Transport stopped without READY; inspect safe stop receipt and exact remote state')from None
    print(json.dumps({'source_id':'69','asset_commit':results[0]['asset_commit'],'dual_raw_objects_exact':True,'READY_created':False,'main_or_master_modified':False}))
if __name__=='__main__':main()
