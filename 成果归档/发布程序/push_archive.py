from pathlib import Path
import json,subprocess,hashlib,re

BASE=Path(__file__).resolve().parent;REPO=BASE/'target'
JOURNAL=BASE/'push-journal.json'

def git(*args):
    r=subprocess.run(['git',*args],cwd=REPO,capture_output=True,text=True)
    if r.returncode:raise RuntimeError(r.stderr[-4000:])
    return r.stdout

def commit_push(label,paths,records):
    paths=sorted({str(p.relative_to(REPO)) for p in paths if p.is_file() and '__pycache__' not in p.parts})
    for start in range(0,len(paths),250):git('add','--sparse','-f','--',*paths[start:start+250])
    changes=git('diff','--cached','--name-status').splitlines()
    if not changes:return
    if any(x.startswith('D\t') for x in changes):raise ValueError('Archival must not delete existing files')
    git('commit','-m',label+' [skip ci]')
    commit=git('rev-parse','HEAD').strip()
    git('-c','http.postBuffer=209715200','-c','pack.threads=2','push','--quiet','origin','HEAD:main')
    remote=git('ls-remote','origin','refs/heads/main').split()[0]
    if remote!=commit:raise ValueError('Remote commit differs after push')
    records.append({'label':label,'commit':commit,'files':len(changes),'remote_verified':True})
    tmp=JOURNAL.with_suffix('.tmp');tmp.write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n');tmp.replace(JOURNAL)
    print(json.dumps(records[-1],ensure_ascii=False),flush=True)

def main():
    for k,v in [('user.name','Codex'),('user.email','codex@users.noreply.github.com')]:
        if not git('config','--get',k).strip():git('config',k,v)
    git('config','credential.helper','!gh auth git-credential')
    b=REPO/'插图阅读小册';records=json.loads(JOURNAL.read_text()) if JOURNAL.exists() else []
    initial=[REPO/x for x in ['README.md','CLAUDE.md','AGENTS.md']]
    initial += [p for p in b.rglob('*') if p.is_file() and p.suffix.lower() not in ['.pdf','.png','.jpg','.pyc'] and '__pycache__' not in p.parts]
    initial += [b/'.gitignore']
    for dirname in ['成果归档','简述重制核验','简述重制预览']:
        initial.extend(p for p in (REPO/dirname).rglob('*') if p.is_file())
    data=json.loads((BASE/'download-records.json').read_text())
    initial.extend(REPO/v['destination'] for p,v in data.items() if p.startswith('视频/'))
    initial.append(REPO/'最终版4K视频/README.md')
    commit_push('保存70篇文稿、简述、源码、审校记录与GitHub长期归档规则',initial,records)
    for group in range(7):
        paths=[]
        for n in range(group*10+1,group*10+11):
            paths.extend(p for p in (b/f'production/{n:02}').iterdir() if p.suffix in ['.pdf','.png','.jpg'])
            paths.append(b/'illustrations'/('01-preview.png' if n==1 else f'{n:02}.png'))
        paths.extend(p for p in (b/f'volumes/{group+1:02}').iterdir() if p.suffix in ['.pdf','.png'])
        if group==0:paths.extend((b/'output').glob('*.pdf'))
        commit_push(f'完整保存第{group*10+1:02}–{group*10+10:02}篇小册子PDF、原图和实页预览',paths,records)
    videos=json.loads((REPO/'成果归档/视频定稿文件清单.json').read_text())['videos']
    for group in range(7):
        subset=videos[group*10:(group+1)*10]
        for v in subset:
            p=REPO/v['path'];assert hashlib.sha256(p.read_bytes()).hexdigest()==v['sha256']
        commit_push(f'完整保存第{group*10+1:02}–{group*10+10:02}部已验收4K视频及原音频',[REPO/v['path'] for v in subset],records)
    print(json.dumps({'all_batches_pushed':True,'head':git('rev-parse','HEAD').strip(),'pushes':len(records)},ensure_ascii=False),flush=True)

if __name__=='__main__':main()
