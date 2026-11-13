from pathlib import Path
import argparse,json,subprocess,hashlib,concurrent.futures,tempfile

def run(*args):
    r=subprocess.run(['gh',*args],capture_output=True,text=True)
    if r.returncode:raise RuntimeError(r.stderr[-2500:])
    return r.stdout

def api(path):return json.loads(run('api',path))
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
    return h.hexdigest()

def main():
    p=argparse.ArgumentParser();p.add_argument('--repository',required=True);p.add_argument('--tag',required=True);p.add_argument('--commit',required=True);p.add_argument('--assets',required=True);p.add_argument('--notes',required=True);a=p.parse_args()
    assets=Path(a.assets);repo=a.repository;tag=a.tag
    q=subprocess.run(['gh','api',f'repos/{repo}/releases/tags/{tag}'],capture_output=True,text=True)
    if q.returncode:
        if '404' not in q.stderr:raise RuntimeError(q.stderr)
        run('release','create',tag,'--repo',repo,'--target',a.commit,'--draft','--latest=false','--title','70篇完整成果：4K视频、插图阅读小册及全部配套材料','--notes-file',a.notes)
    release=api(f'repos/{repo}/releases/tags/{tag}')
    if not release['draft']:raise RuntimeError('This version is already public; do not overwrite it')
    rid=release['id']
    prior={x['name']:x for x in api(f'repos/{repo}/releases/{rid}/assets?per_page=100')}
    files=sorted([x for x in assets.iterdir() if x.is_file() and not x.name.endswith('.tmp') and x.name!='PUBLISH-RESULT.json'],key=lambda x:(x.stat().st_size,x.name))
    verified=[]
    def upload(path):
        digest=sha(path);old=prior.get(path.name)
        if old:
            if old['size']!=path.stat().st_size or old.get('digest') not in [None,'sha256:'+digest]:raise ValueError('Conflicting existing draft asset '+path.name)
            item=old
        else:
            run('release','upload',tag,str(path),'--repo',repo)
            matches=[x for x in api(f'repos/{repo}/releases/{rid}/assets?per_page=100') if x['name']==path.name]
            if len(matches)!=1:raise ValueError('Upload not uniquely saved '+path.name)
            item=matches[0]
        if item['size']!=path.stat().st_size:raise ValueError('Remote byte count mismatch '+path.name)
        if item.get('digest'):
            if item['digest']!='sha256:'+digest:raise ValueError('Remote SHA mismatch '+path.name)
        else:
            with tempfile.TemporaryDirectory() as folder:
                run('release','download',tag,'--repo',repo,'--pattern',path.name,'--dir',folder)
                if sha(Path(folder)/path.name)!=digest:raise ValueError('Downloaded SHA mismatch '+path.name)
        result={'name':path.name,'bytes':item['size'],'sha256':digest,'asset_id':item['id'],'download_url':item['browser_download_url'],'remote_verified':True}
        print(json.dumps(result,ensure_ascii=False),flush=True);return result
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        futures=[pool.submit(upload,path) for path in files]
        for f in concurrent.futures.as_completed(futures):verified.append(f.result())
    report={'repository':repo,'tag':tag,'source_commit':a.commit,'release_id':rid,'status':'all_assets_uploaded_and_remote_sha256_verified','assets':sorted(verified,key=lambda x:x['name']),'video_count':70,'individual_booklets':70,'combined_volumes':7,'original_illustrations':70,'PDF_page_previews':467,'primary_sync':'blocked_by_integration_403','primary_repository':'alienalgorithm/postgraduate-vocabulary'}
    result=assets/'PUBLISH-RESULT.json';result.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');receipt=upload(result)
    run('release','edit',tag,'--repo',repo,'--draft=false','--latest=false','--target',a.commit)
    saved=api(f'repos/{repo}/releases/tags/{tag}')
    if saved['draft'] or saved['target_commitish']!=a.commit:raise ValueError('Final release not published at expected commit')
    final={**report,'status':'published','release_url':saved['html_url'],'receipt_asset':receipt}
    (assets.parent/'RELEASE-DELIVERY-RECEIPT.json').write_text(json.dumps(final,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'published':True,'url':saved['html_url'],'remote_assets':len(saved['assets']),'source_commit':a.commit},ensure_ascii=False),flush=True)

if __name__=='__main__':main()
