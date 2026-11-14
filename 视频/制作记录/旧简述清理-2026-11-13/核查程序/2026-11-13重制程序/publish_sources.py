"""Archive the reviewed sources/evidence in both authorized repositories without fetching video history."""
import ast,base64,hashlib,json,os,re,shutil,subprocess
from pathlib import Path

OUT=Path('/workspace/work/video-audit70-20261113')
PAY=Path(os.environ.get('VIDEO_SOURCE_PAYLOAD',str(OUT/'payload'))).resolve()
LOCAL=Path('/workspace/work/github-publication/target')
REPORT='视频/制作记录/旧简述清理-2026-11-13'
BRANCH='codex/review-source-fixes-20261113-v1'
namespace={'base64':base64,'hashlib':hashlib,'json':json,'subprocess':subprocess}
for node in ast.parse(Path('/workspace/work/video05-keywords/save_pending.py').read_text()).body:
    if isinstance(node,ast.FunctionDef) and node.name=='api':exec(compile(ast.Module(body=[node],type_ignores=[]),'<existing-api>','exec'),namespace)
api=namespace['api']
def command(args,cwd=PAY):
    r=subprocess.run(args,cwd=cwd,check=True,capture_output=True,text=True)
    return r.stdout.strip()
def gitsha(data):return hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()

# The parallel source editor owns only03; include its completed report as evidence.
focus_report=OUT/'article03-focus-report.json'
assert focus_report.exists(),'Wait for original03 source edits before publishing the combined revision.'
(PAY/REPORT/'核查记录'/focus_report.name).write_bytes(focus_report.read_bytes())
assert (PAY/'视频/脚本/03.json').exists()
if not (PAY/'.git').exists():
    command(['git','init','-q','-b',BRANCH])
    command(['git','config','user.name','Codex'])
    command(['git','config','user.email','codex@users.noreply.github.com'])
    command(['git','config','credential.helper','!gh auth git-credential'])
command(['git','add','--all'])
if command(['git','status','--porcelain']):
    command(['git','commit','-q','-m','保存70篇重制源稿、最新重点词和清晰简述；视频与PDF实物验收另记 [skip ci]'])
asset_commit=command(['git','rev-parse','HEAD'])
files=[str(p.relative_to(PAY)) for p in PAY.rglob('*') if p.is_file() and '.git' not in p.relative_to(PAY).parts]
canonical=[p for p in files if not p.startswith(REPORT+'/')]
assert all(p.startswith(('视频/脚本/','视频/工具/初稿生成/','新版定稿/','视频/制作记录/待修改/',
                         '视频/制作记录/本轮70篇GEN与文本预检-2026-11-13/',
                         '视频/制作记录/42_2026-11-13词汇修订/'))
           or p=='视频/工具/用户同意记录.json'
           or p in {'视频/工具/草稿声音.sh','视频/工具/句内响度.py',
                    '视频/工具/独立复核/synth.py','视频/工具/新管/回归基准_27.json',
                    '视频/工具/新管/快测通过.json'}
           or re.fullmatch(r'视频/制作记录/(?:\d{2}_待改清单\.md|逐句确认/\d{2}\.json)',p) for p in canonical)
assert not any(p.endswith(('.mp4','.pdf')) for p in files)

def rows(repo,sha):
    if not sha:return []
    r=api(repo,'git/trees/'+sha);assert not r.get('truncated')
    return [{k:x[k] for k in ['path','mode','type','sha']} for x in r['tree']]
def attach(repo,branch):
    master=api(repo,'git/ref/heads/master')['object']['sha'] if branch!='main' else None
    parent=api(repo,'git/ref/heads/'+branch)['object']['sha']
    base=api(repo,'git/commits/'+parent)['tree']['sha']
    cache={}
    def listing(sha):
        if sha not in cache:cache[sha]=rows(repo,sha)
        return cache[sha]
    def lookup(path):
        node=base;parts=path.split('/')
        for i,part in enumerate(parts):
            found=next((x for x in listing(node) if x['path']==part),None)
            if not found:return None
            if i==len(parts)-1:return found['sha']
            node=found['sha']
    # Protect against a parallel editor's changes. New GEN03 is allowed only if absent.
    for path in canonical:
        found=lookup(path)
        local=LOCAL/path
        if local.exists():old=local.read_bytes()
        else:
            p=subprocess.run(['git','show','HEAD:'+path],cwd=LOCAL,capture_output=True)
            old=p.stdout if p.returncode==0 else None
        assert found in {(gitsha(old) if old is not None else None),gitsha((PAY/path).read_bytes())},(repo,path,'baseline changed; merge required')
    updates={}
    def insert(path,leaf):
        node=updates;parts=path.split('/')
        for name in parts[:-1]:node=node.setdefault(name,{})
        node[parts[-1]]={'@leaf':leaf}
    for path in canonical:
        sha=command(['git','rev-parse',asset_commit+':'+path])
        insert(path,{'mode':'100644','type':'blob','sha':sha})
    insert(REPORT,{'mode':'040000','type':'tree','sha':command(['git','rev-parse',asset_commit+':'+REPORT])})
    def graft(old,patch):
        existing={r['path']:r for r in listing(old)} if old else {}
        for name,value in patch.items():
            leaf=value.get('@leaf')
            if leaf is None:
                sha=graft(existing.get(name,{}).get('sha'),value)
                leaf={'mode':'040000','type':'tree','sha':sha}
            existing[name]={'path':name,**leaf}
        return api(repo,'git/trees','POST',{'tree':list(existing.values())})['sha']
    tree=graft(base,updates)
    commit=api(repo,'git/commits','POST',{'message':'保存70篇清晰简述及末页重排源稿、最新重点词和真实核验；新4K仍待正式验收 [skip ci]','tree':tree,'parents':[parent]})['sha']
    api(repo,'git/refs/heads/'+branch,'PATCH',{'sha':commit,'force':False})
    assert api(repo,'git/ref/heads/'+branch)['object']['sha']==commit
    for path in ['视频/脚本/12.json','视频/脚本/03.json']:
        actual=api(repo,'contents/'+path+'?ref='+commit)
        assert base64.b64decode(actual['content'])==(PAY/path).read_bytes()
    if master:assert api(repo,'git/ref/heads/master')['object']['sha']==master
    return {'repository':repo,'branch':branch,'source_commit':commit,'previous_commit':parent,'master_unchanged':True if master else None}

result={'asset_branch':BRANCH,'asset_commit':asset_commit,'payload_files':len(files),'payload_bytes':sum((PAY/p).stat().st_size for p in files),'archives':[]}
for name,repo,branch in [('primary','alienalgorithm/postgraduate-vocabulary','main'),('backup','AlienCodes/literate-enigma','codex/all-deliverables-20261113')]:
    command(['git','push','https://github.com/'+repo+'.git',asset_commit+':refs/heads/'+BRANCH])
    result['archives'].append(attach(repo,branch))
    (OUT/'PUBLISHED-SOURCE-STATE.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(result['archives'][-1],ensure_ascii=False),flush=True)
for path in files:
    target=LOCAL/path;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes((PAY/path).read_bytes())
print(json.dumps({'status':'sources and audit evidence archived','files':len(files),'new_videos_not_yet_delivered':True},ensure_ascii=False),flush=True)
