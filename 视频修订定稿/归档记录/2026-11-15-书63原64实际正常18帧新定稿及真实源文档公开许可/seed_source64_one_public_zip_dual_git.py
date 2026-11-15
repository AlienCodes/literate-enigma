"""CODE-ONLY exact source64/book63 one-public-ZIP dual Git seed. Default is local plan.
No encoding/media changes; actual execution requires exact code/three-input approval.
The original standard-Git helper functions are unchanged from the accepted48 seed.
"""
from pathlib import Path
import argparse,datetime,hashlib,json,os,shutil,subprocess,tempfile,urllib.request,zlib,re
HS='a573114f9deef6d042f25f53f21fd3b5c2b340bbc2758e912264fb2fce9faacb';PS='8b7ffa18fc9c8e0f321ac3ce06f47e6444ec3ca431c2998b6bb4650b267da2fc';IS='910b9e0ed9420c920b6d30b8fad69cfafd842378d8c0b743f77fd2b96591f18b'
WORK_DIR='/workspace/work/video-archive-batches-20261114/book63-source64-full-host-isolated-assets-fun_nv1b/run43728310644-64-book63-review-normal18-v1';HANDOFF='/workspace/work/review64-finalV3/43728310644-normal18/archive-handoff.json'
ZIP_SHA='deb1bf8f75314223802ef4d25039c31d011a1def39ded1e01e944082c43e7768';BLOB='db71dd09e5ef5673b3eb5e81f7c3fbdc40b14d2d';SIZE=46858906
REF='codex/source64-book63-exact-public-nativeZIP-seed-20261115';NAME='source64-original-public-native-artifact.zip';MESSAGE='Transport only exact source64 book63 public native ZIP; no final or quality change [skip ci]\n'
REPOS=(('primary','alienalgorithm/postgraduate-vocabulary'),('backup','AlienCodes/literate-enigma'))
MASTER='6355a02864ebae616b693200d9d26f74f5da80e9'
FLOOR=419430400;GIT_METADATA=2*1024*1024;BUDDY_MISC=40*1024*1024
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb')as f:
  for b in iter(lambda:f.read(196608),b''):h.update(b)
 return h.hexdigest()

def gitsha(kind,raw):return hashlib.sha1(kind.encode()+b' '+str(len(raw)).encode()+b'\0'+raw).hexdigest()

def pinned(p,expected):
 raw=Path(p).read_bytes();assert hashlib.sha256(raw).hexdigest()==expected;return json.loads(raw)

def run(args,env=None,input=None):
 p=subprocess.run(list(map(str,args)),input=input,text=True,capture_output=True,env=env,timeout=180)
 if p.returncode:raise RuntimeError(p.stderr[-2000:])
 return p.stdout.strip()

def identities(blob,date,message=MESSAGE):
 raw=b'100644 '+NAME.encode()+b'\0'+bytes.fromhex(blob);tree=gitsha('tree',raw);stamp=int(datetime.datetime.fromisoformat(date.replace('Z','+00:00')).timestamp());body=(f'tree {tree}\nauthor Codex <codex@users.noreply.github.com> {stamp} +0000\ncommitter Codex <codex@users.noreply.github.com> {stamp} +0000\n\n'+message).encode();return tree,gitsha('commit',body),stamp

def local_objects(g,source,blob,tree,commit,stamp):
 run(['git','init','--bare','--template=',g]);args=['git','--git-dir='+str(g)]
 for k,v in [('gc.auto','0'),('core.compression','1'),('pack.threads','1'),('pack.window','0')]:run(args+['config',k,v])
 assert run(args+['hash-object','-w','--no-filters',source])==blob
 assert run(args+['mktree'],input=f'100644 blob {blob}\t{NAME}\n')==tree
 env={**os.environ,'GIT_AUTHOR_NAME':'Codex','GIT_AUTHOR_EMAIL':'codex@users.noreply.github.com','GIT_COMMITTER_NAME':'Codex','GIT_COMMITTER_EMAIL':'codex@users.noreply.github.com','GIT_AUTHOR_DATE':f'@{stamp} +0000','GIT_COMMITTER_DATE':f'@{stamp} +0000'}
 assert run(args+['commit-tree',tree,'-m',MESSAGE.rstrip('\n')],env=env)==commit


def expected_refs(value):
    keys={'alienalgorithm/postgraduate-vocabulary:main','AlienCodes/literate-enigma:codex/all-deliverables-20261113','AlienCodes/literate-enigma:master'}
    assert isinstance(value,dict)and set(value)==keys
    assert all(isinstance(v,str)and re.fullmatch('[0-9a-f]{40}',v)for v in value.values())
    assert value['AlienCodes/literate-enigma:master']==MASTER
    return value

def refs(expected):
    expected_refs(expected);result={}
    for key,value in expected.items():
        repo,branch=key.split(':',1)
        actual=run(['gh','api',f'repos/{repo}/git/ref/heads/{branch}','--jq','.object.sha'])
        assert actual==value,'Protected ref changed; no further seed writes'
        result[key]=actual
    return result

def local_plan(work_dir,handoff):
    w=Path(work_dir).resolve();assert str(w)==WORK_DIR and str(Path(handoff).resolve())==HANDOFF
    h=pinned(handoff,HS);meta=pinned(w/'prepared-archive.json',PS);index=pinned(w/'payload-file-index.json',IS)
    assert h['kind']=='actual-new-native-source-QA-then-authorized-normal18-local-tail'and h['status']=='passed_actual_normal18_post_only_for_permanent_archive'
    assert h['production_delivery_eligible']is True and h['preview_only']is False and h['source_run']==43728310644
    assert len(h['articles'])==len(meta['articles'])==1
    a=h['articles'][0];row=meta['articles'][0]
    assert a['source_id']==row['source_id']=='64'and a['new_id']==row['new_id']=='63'and a['passed_per_article']is row['passed_per_article']is True
    assert meta['actual_handoff_sha256']==row['postprocessing_full_V3_handoff_sha256']==HS
    assert a['final_mp4']['bytes']==row['bytes']==16404902 and a['final_mp4']['sha256']==row['sha256']=='f0b058d5689c08f6f95d94610c26c725397e957b5f1ef170612a32b5d59d3b1f'
    x=next(x for x in index if x['bytes']==SIZE and x['sha256']==ZIP_SHA)
    source=(w/'payload'/x['repo_path']).resolve();assert source.is_file()and source.stat().st_size==SIZE and sha(source)==ZIP_SHA
    gg=hashlib.sha1(f'blob {SIZE}\0'.encode());z=zlib.compressobj(1);compressed=len(z.compress(f'blob {SIZE}\0'.encode()))
    with source.open('rb')as stream:
        for part in iter(lambda:stream.read(196608),b''):gg.update(part);compressed+=len(z.compress(part))
    compressed+=len(z.flush());assert gg.hexdigest()==BLOB
    tree,commit,stamp=identities(BLOB,meta['created_utc']);allocated=((compressed+4095)//4096)*4096
    plan={'kind':'exact-source64-book63-single-public-ZIP-two-repository-standard-Git-seed-plan','source_id':'64','book_order':'63','handoff_sha256':HS,'prepared_sha256':PS,'index_sha256':IS,'native_source_run':43728310644,'ZIP_bytes':SIZE,'ZIP_SHA256':ZIP_SHA,'git_blob_sha':BLOB,'seed_ref':REF,'seed_tree':tree,'seed_commit':commit,'actual_zlib1_loose_object_bytes':compressed,'estimated_loose_allocated4KiB':allocated,'Git_metadata_reserved_bytes':GIT_METADATA,'worker8MiB_and_misc32MiB':BUDDY_MISC,'original400MiB_reserve':FLOOR,'required_available_before_seed':FLOOR+allocated+GIT_METADATA+BUDDY_MISC,'no_ZIP_pack_copy_or_base64_body_file':True,'outbound_pack_is_original_standard_Git_stdout_and_HTTP_buffer_heap':True,'network_executed':False,'protected_refs_are_only_supplied_and_freshchecked_at_actual_execution':True}
    return plan,source,stamp

def actual_raw(repo):
    token=run(['gh','auth','token'])
    request=urllib.request.Request('https://api.github.com/repos/'+repo+'/git/blobs/'+BLOB,headers={'Authorization':'Bearer '+token,'Accept':'application/vnd.github.raw+json','Accept-Encoding':'identity','User-Agent':'exact-source64-book63-public-ZIP-seed-proof'})
    full=hashlib.sha256();gg=hashlib.sha1(f'blob {SIZE}\0'.encode());n=0
    with urllib.request.urlopen(request,timeout=120)as response:
        assert response.status==200 and response.getheader('Content-Encoding')in(None,'identity')
        for part in iter(lambda:response.read(196608),b''):n+=len(part);assert n<=SIZE;full.update(part);gg.update(part)
    assert n==SIZE and full.hexdigest()==ZIP_SHA and gg.hexdigest()==BLOB
    return {'repository':repo,'http_status':200,'bytes':n,'sha256':full.hexdigest(),'git_blob_sha':gg.hexdigest(),'entire_raw_HTTP_verified':True,'seed_ref':REF}

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--work-dir',required=True);parser.add_argument('--handoff',required=True);parser.add_argument('--approval');parser.add_argument('--execute',action='store_true');a=parser.parse_args()
    plan,source,stamp=local_plan(a.work_dir,a.handoff)
    if not a.execute:print(json.dumps(plan));return
    assert a.approval,'Explicit exact execution adoption required; code-only is not execution'
    approval=json.loads(Path(a.approval).read_text())
    assert approval['kind']=='root-approved-source64-book63-exact-public-ZIP-two-repository-Git-seed'and approval['approved']is True and approval['approved_seed_code_sha256']==sha(__file__)
    assert approval['source_id']=='64'and approval['new_id']=='63'
    assert approval['handoff_sha256']==HS and approval['prepared_sha256']==PS and approval['index_sha256']==IS and approval['seed_ref']==REF and approval['seed_commit']==plan['seed_commit']
    assert os.environ.get('EXACT64_BOOK63_SEED_ORIGINAL400_MONITORED')=='1','Run via reviewed0.5s400MiB monitor'
    expected=expected_refs(approval['expected_protected_refs']);root=Path(a.work_dir).resolve().parent
    assert os.statvfs(root).f_bavail*os.statvfs(root).f_frsize>=plan['required_available_before_seed']
    before=refs(expected);auth=['-c','credential.helper=!gh auth git-credential']
    for _,repo in REPOS:
        assert not run(['git',*auth,'ls-remote','https://github.com/'+repo+'.git','refs/heads/'+REF]),'New seed ref must be absent in both repositories'
    own=Path(tempfile.mkdtemp(prefix='source64-book63-exact-one-ZIP-seed-',dir=str(root)));g=own/'objects.git'
    local_objects(g,source,BLOB,plan['seed_tree'],plan['seed_commit'],stamp)
    rows=[]
    for role,repo in REPOS:
        assert os.statvfs(root).f_bavail*os.statvfs(root).f_frsize>=FLOOR
        assert pinned(a.handoff,HS)and pinned(Path(a.work_dir)/'prepared-archive.json',PS)and pinned(Path(a.work_dir)/'payload-file-index.json',IS)
        assert refs(expected)==before
        url='https://github.com/'+repo+'.git'
        # An orphan seed commit cannot fast-forward or replace a different concurrently-created seed ref.
        run(['git','--git-dir='+str(g),*auth,'-c','http.postBuffer=67108864','push','--porcelain',url,plan['seed_commit']+':refs/heads/'+REF])
        assert run(['git',*auth,'ls-remote',url,'refs/heads/'+REF]).split()[0]==plan['seed_commit']
        rows.append({'role':role,**actual_raw(repo),'seed_commit':plan['seed_commit']})
    assert refs(expected)==before
    assert pinned(a.handoff,HS)and pinned(Path(a.work_dir)/'prepared-archive.json',PS)and pinned(Path(a.work_dir)/'payload-file-index.json',IS)
    run(['git','--git-dir='+str(g),'fsck','--full']);logical=sum(p.stat().st_size for p in g.rglob('*')if p.is_file())
    assert g.parent==own and own.parent==root and own.name.startswith('source64-book63-exact-one-ZIP-seed-')and not g.is_symlink()
    shutil.rmtree(g)
    result={**plan,'kind':'actual-source64-book63-single-public-ZIP-two-repository-seed-fullraw-proof','network_executed':True,'approved_seed_code_sha256':sha(__file__),'actual_rows':rows,'protected_refs_before':before,'protected_refs_after':refs(expected),'source_and_all_frozen_controls_unchanged':True,'git_fsck_exit_code':0,'only_own_seed_Git_removed_after_dual_raw_and_fsck':True,'own_seed_Git_logical_bytes_removed':logical,'no_asset_READY_or_current_claimed':True,'whole_transport_role':'one-standard-Git-publicZIP-seed-then-separate-streaming-Git-data-builder'}
    out=root/'ACTUAL-BOOK63-EXACT-PUBLIC-ZIP-DUAL-GIT-SEED-FULLRAW-PROOF.json'
    with out.open('x')as stream:json.dump(result,stream,indent=2);stream.write('\n')
    print(json.dumps({'seed_proof':str(out),'seed_proof_sha256':sha(out),'only_own_Git_removed':logical,'no_asset_READY_or_current_claimed':True}))
if __name__=='__main__':main()
