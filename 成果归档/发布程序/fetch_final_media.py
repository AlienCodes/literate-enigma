from pathlib import Path
import json,hashlib,time,concurrent.futures
from urllib.request import Request,urlopen

ROOT=Path(__file__).resolve().parent
TARGET=ROOT/'target'
REF='9374187e740fcefef39e42259a2f057ae504ebc9'
TREE=json.loads(Path('/workspace/work/upload-session-tree.json').read_text())
OLD=json.loads(Path('/workspace/work/upload-original-tree.json').read_text())
JOURNAL=ROOT/'download-records.json'

def gitsha(p):
    h=hashlib.sha1(f'blob {p.stat().st_size}\0'.encode())
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()

def location(p):
    if p.startswith('.github/') or p.startswith(('新管/','改门待演练/')):
        return TARGET/'成果归档/视频制作程序'/p
    return TARGET/p

def fetch(p):
    dest=location(p);dest.parent.mkdir(parents=True,exist_ok=True)
    if dest.exists() and gitsha(dest)==TREE[p]:
        return {'path':p,'destination':str(dest.relative_to(TARGET)),'bytes':dest.stat().st_size,'sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'git_blob_sha':TREE[p]}
    from urllib.parse import quote
    url='https://raw.githubusercontent.com/AlienCodes/literate-enigma/'+REF+'/'+quote(p)+'?full=1'
    for attempt in range(3):
        try:
            h=hashlib.sha256();tmp=dest.with_name(dest.name+'.download')
            with urlopen(Request(url,headers={'Cache-Control':'no-cache'}),timeout=90) as resp,tmp.open('wb') as f:
                if resp.status!=200:raise ValueError('Incomplete response '+str(resp.status))
                for b in iter(lambda:resp.read(1024*1024),b''):f.write(b);h.update(b)
            if gitsha(tmp)!=TREE[p]:raise ValueError('Git blob mismatch for '+p)
            tmp.replace(dest)
            return {'path':p,'destination':str(dest.relative_to(TARGET)),'bytes':dest.stat().st_size,'sha256':h.hexdigest(),'git_blob_sha':TREE[p]}
        except Exception:
            if attempt==2:raise
            time.sleep(2+attempt)

def main():
    selected=[p for p in TREE if (p.startswith(('简述重制核验/','简述重制预览/','.github/','新管/','改门待演练/')) or (p.startswith('视频/') and OLD.get(p)!=TREE[p]) or (p.startswith('最终版4K视频/') and p.endswith('.mp4')))]
    # Fetch reports first, so expected final MP4 hashes are available promptly.
    selected.sort(key=lambda p:(p.endswith('.mp4'),p))
    records=json.loads(JOURNAL.read_text()) if JOURNAL.exists() else {}
    errors=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        tasks={pool.submit(fetch,p):p for p in selected}
        for i,f in enumerate(concurrent.futures.as_completed(tasks),1):
            p=tasks[f]
            try:records[p]=f.result()
            except Exception as e:errors.append({'path':p,'error':type(e).__name__+': '+str(e)})
            tmp=JOURNAL.with_suffix('.tmp');tmp.write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n');tmp.replace(JOURNAL)
            if i%20==0 or p.endswith('.mp4') or i==len(selected):
                print(json.dumps({'completed':i,'total':len(selected),'files_verified':len(records),'bytes_verified':sum(x['bytes'] for x in records.values()),'errors':len(errors),'latest':p},ensure_ascii=False),flush=True)
    (ROOT/'download-errors.json').write_text(json.dumps(errors,ensure_ascii=False,indent=2)+'\n')
    if errors:raise SystemExit(1)

if __name__=='__main__':main()
