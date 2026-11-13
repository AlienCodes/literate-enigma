from pathlib import Path
import os,json,subprocess

BASE=Path(__file__).resolve().parent;REPO=BASE/'target'
BRANCH='codex/all-deliverables-20261113'
SOURCE='9374187e740fcefef39e42259a2f057ae504ebc9'
JOURNAL=BASE/'backup-push-journal.json'
ENV={**os.environ,'GIT_INDEX_FILE':str(BASE/'backup.index')}

def git(*args,input=None):
    r=subprocess.run(['git',*args],cwd=REPO,capture_output=True,text=True,input=input,env=ENV)
    if r.returncode:raise RuntimeError(r.stderr[-3000:])
    return r.stdout

def tree_entries(ref):
    data=git('ls-tree','-r','--format=%(objectname)\t%(path)',ref)
    out={}
    for line in data.splitlines():
        sha,p=line.split('\t',1)
        if p.startswith('"'):p=p[1:-1].encode().decode('unicode_escape').encode('latin1').decode('utf8')
        out[p]=sha
    return out

def main():
    remotes=git('remote').splitlines()
    if 'archive-backup' not in remotes:git('remote','add','archive-backup','https://github.com/AlienCodes/literate-enigma.git')
    records=json.loads(JOURNAL.read_text()) if JOURNAL.exists() else []
    parent=records[-1]['commit'] if records else SOURCE
    git('read-tree',parent)
    current=tree_entries(parent)
    source=json.loads(Path('/workspace/work/upload-session-tree.json').read_text())
    b=REPO/'插图阅读小册'
    initial=[REPO/x for x in ['README.md','CLAUDE.md','AGENTS.md']]
    initial.extend(p for p in b.rglob('*') if p.is_file() and p.suffix in ['.py','.json','.txt','.md','.ttf'] and '__pycache__' not in p.parts)
    initial.append(b/'.gitignore')
    for name in ['成果归档','简述重制核验','简述重制预览']:
        initial.extend(p for p in (REPO/name).rglob('*') if p.is_file())
    downloads=json.loads((BASE/'download-records.json').read_text())
    initial.extend(REPO/v['destination'] for p,v in downloads.items() if p.startswith('视频/'))
    initial.append(REPO/'最终版4K视频/README.md')
    groups=[('完整归档70篇源文稿、制作程序、核验记录及长期保存规则',initial)]
    for group in range(7):
        paths=[]
        for n in range(group*10+1,group*10+11):
            paths.extend(p for p in (b/f'production/{n:02}').iterdir() if p.suffix in ['.pdf','.png','.jpg'])
            paths.append(b/'illustrations'/('01-preview.png' if n==1 else f'{n:02}.png'))
        paths.extend(p for p in (b/f'volumes/{group+1:02}').iterdir() if p.suffix in ['.pdf','.png'])
        if group==0:paths.extend((b/'output').glob('*.pdf'))
        groups.append((f'完整保存第{group*10+1:02}–{group*10+10:02}篇插图小册子和PDF实页',paths))
    for label,paths in groups:
        paths=sorted({str(p.relative_to(REPO)) for p in paths if p.is_file() and '__pycache__' not in p.parts})
        # The final videos/cards are already byte-identical in SOURCE. Avoid
        # fetching or uploading an unchanged baseline binary a second time.
        paths=[p for p in paths if not(p in source and source[p]==current.get(p) and p.startswith(('视频/','简述重制预览/','简述重制核验/')))]
        if not paths:continue
        hashes=git('hash-object','-w','--stdin-paths',input='\n'.join(paths)+'\n').splitlines()
        changes=[(p,h) for p,h in zip(paths,hashes) if current.get(p)!=h]
        if not changes:continue
        data=''.join(f'100644 {h}\t{p}\n' for p,h in changes)
        git('update-index','--add','--index-info',input=data)
        # Unchanged baseline blobs are deliberately absent in this partial
        # clone and already exist on the destination. Do not download them
        # merely to repeat existence checks while writing the new tree.
        tree=git('write-tree','--missing-ok').strip()
        commit=git('commit-tree',tree,'-p',parent,'-m',label+' [skip ci]').strip()
        git('update-ref','refs/heads/'+BRANCH,commit)
        git('-c','http.postBuffer=209715200','-c','pack.threads=2','push','--quiet','archive-backup','refs/heads/'+BRANCH+':refs/heads/'+BRANCH)
        remote=git('ls-remote','archive-backup','refs/heads/'+BRANCH).split()[0]
        if remote!=commit:raise ValueError('Backup remote mismatch')
        records.append({'label':label,'commit':commit,'files':len(changes),'remote_verified':True,'repository':'AlienCodes/literate-enigma','branch':BRANCH})
        JOURNAL.write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n')
        print(json.dumps(records[-1],ensure_ascii=False),flush=True)
        current.update(changes);parent=commit
    print(json.dumps({'all_backup_batches_pushed':True,'head':parent,'master_unchanged':True},ensure_ascii=False),flush=True)

if __name__=='__main__':main()
