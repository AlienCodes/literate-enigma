#!/usr/bin/env python3
"""V3 native uploader: exactly one frozen book PDF and70 book-order4K MP4s.
Detailed evidence and the remote receipt are repository records, never Release attachments.
"""
import argparse, base64, datetime, hashlib, json, mimetypes, os, re, shutil, urllib.error, urllib.parse, urllib.request, tempfile, subprocess
from pathlib import Path
from release_contract import pdf_reference, exact_assets, approved_compact_pdf, book_illustrations, ASSET_POLICY
REPO='alienalgorithm/postgraduate-vocabulary'
PROGRAM='成果归档/视频重制发布程序'
MAX_ASSET=2_000_000_000
_LOCAL_AUTH_TOKEN=None
def require(ok, message):
    if not ok: raise ValueError(message)

def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda: f.read(4 * 1024 * 1024), b''): h.update(b)
    return h.hexdigest()

def write(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')

def auth_token():
    # Native Actions still supplies GH_TOKEN. Local execution resolves the
    # existing gh credential without fabricating any Actions environment.
    global _LOCAL_AUTH_TOKEN
    if os.environ.get('GH_TOKEN'):return os.environ['GH_TOKEN']
    if _LOCAL_AUTH_TOKEN is None:
        result=subprocess.run(['gh','auth','token'],check=True,capture_output=True,text=True)
        _LOCAL_AUTH_TOKEN=result.stdout.strip()
        require(bool(_LOCAL_AUTH_TOKEN),'No authenticated local gh credential')
    return _LOCAL_AUTH_TOKEN

def publisher_execution(mode):
    if mode=='native-actions':
        require(os.environ.get('GITHUB_REPOSITORY')==REPO,'Native Actions publishes only in the primary repository')
        return {'kind':'native_actions','repository':REPO,'workflow_run_id':int(os.environ['GITHUB_RUN_ID']),
                'workflow_head_sha':os.environ['GITHUB_SHA'],'workflow_path':'.github/workflows/publish-video-revisions.yml'}
    require(mode=='local-gh','Unknown publisher mode')
    result=subprocess.run(['gh','--version'],check=True,capture_output=True,text=True)
    return {'kind':'local_gh','transport':'GitHub REST API with existing local gh authentication',
            'gh_version':result.stdout.splitlines()[0],
            'authentication_source':'existing GH_TOKEN'if os.environ.get('GH_TOKEN')else'gh auth token',
            'program_sha256':sha(__file__),'contract_program_sha256':sha(Path(__file__).with_name('release_contract.py'))}

def inspect_local(output):
    execution=publisher_execution('local-gh');repository=api('');releases=api('releases?per_page=100')
    require(repository['full_name'].lower()==REPO.lower(),'Actual authenticated repository differs')
    result={'schema_version':3,'scope':'actual authenticated local-gh GET-only rehearsal; not a release quality or publication claim',
            'observed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'publisher_execution':execution,
            'repository':repository['full_name'],'releases':[{'id':r['id'],'tag_name':r['tag_name'],'draft':r['draft']}for r in releases],
            'actual_repository_read_succeeded':True,'remote_mutation_executed':False,'publication_ready_claimed':False}
    write(output,result);return result

def api(route, method='GET', data=None, missing_ok=False):
    token = auth_token()
    req = urllib.request.Request('https://api.github.com/repos/' + REPO + ('/' + route if route else ''),
        data=None if data is None else json.dumps(data).encode(), method=method,
        headers={'Authorization': 'Bearer ' + token, 'Accept': 'application/vnd.github+json',
                 'Content-Type': 'application/json', 'X-GitHub-Api-Version': '2022-11-28'})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            b = r.read(); return json.loads(b) if b else None
    except urllib.error.HTTPError as e:
        if missing_ok and e.code == 404: return None
        raise

def remote_assets(release_id):
    result = []; page = 1
    while True:
        rows = api(f'releases/{release_id}/assets?per_page=100&page={page}'); result.extend(rows)
        if len(rows) < 100: return result
        page += 1

def verify_asset(remote, expected):
    require(remote['state'] == 'uploaded' and remote['size'] == expected['bytes'], 'Remote asset state/size differs: ' + expected['name'])
    actual_digest = remote.get('digest')
    if not actual_digest:
        # The server did not expose a digest: stream the actual asset back and hash it.
        data=subprocess.run(['gh','api','repos/'+REPO+'/releases/assets/'+str(remote['id']),'-H','Accept: application/octet-stream'],check=True,capture_output=True).stdout
        require(len(data)==expected['bytes'],'Downloaded actual remote asset byte count differs')
        actual_digest='sha256:'+hashlib.sha256(data).hexdigest()
    require(actual_digest == 'sha256:' + expected['sha256'], 'Remote actual digest differs: ' + expected['name'])
    return {'name': expected['name'], 'bytes': remote['size'], 'digest': actual_digest, 'asset_id': remote['id'], 'url': remote['browser_download_url'], 'passed': True}

def upload(release, path):
    url = release['upload_url'].split('{', 1)[0] + '?name=' + urllib.parse.quote(path.name, safe='')
    with path.open('rb') as body:
        request = urllib.request.Request(url, data=body, method='POST', headers={
            'Authorization': 'Bearer ' + auth_token(), 'Content-Type': mimetypes.guess_type(path.name)[0] or 'application/octet-stream',
            'Content-Length': str(path.stat().st_size), 'Accept': 'application/vnd.github+json'})
        with urllib.request.urlopen(request, timeout=900) as response: return json.load(response)

def raw_primary(path,commit):
    require(re.fullmatch('[0-9a-f]{40}',commit),'Immutable primary commit required')
    from release_contract import safe_path
    safe_path(path)
    url='https://raw.githubusercontent.com/'+REPO+'/'+commit+'/'+urllib.parse.quote(path,safe='/')
    with urllib.request.urlopen(url,timeout=300)as response:return response.read()

def download_pdf(spec,dest):
    pdf_reference(spec);commit=spec['pinned_commit']
    comparison=api('compare/'+commit+'...main')
    require(comparison['status']in('ahead','identical'),'Pinned PDF parts commit was not archived on primary main')
    a=spec['approval'];approval_bytes=raw_primary(a['repo_path'],commit)
    require(len(approval_bytes)==a['bytes']and hashlib.sha256(approval_bytes).hexdigest()==a['sha256'],'Frozen PDF approval record differs')
    approval=json.loads(approval_bytes);approved_compact_pdf(spec,approval)
    m=spec['illustrations_manifest'];image_bytes=raw_primary(m['repo_path'],commit)
    require(len(image_bytes)==m['bytes']and hashlib.sha256(image_bytes).hexdigest()==m['sha256'],'Frozen corresponding book illustration map differs')
    image_rows=book_illustrations(json.loads(image_bytes))
    if 'parts_manifest'in spec:
        m=spec['parts_manifest'];data=raw_primary(m['repo_path'],commit)
        require(len(data)==m['bytes']and hashlib.sha256(data).hexdigest()==m['sha256'],'Frozen PDF parts manifest differs')
        actual_manifest=json.loads(data);require(actual_manifest['parts']==spec['parts']and actual_manifest['bytes']==spec['bytes']and actual_manifest['sha256']==spec['sha256']and actual_manifest['release_name']==spec['release_name']and actual_manifest['edition_policy']==spec['edition_policy'],'Published PDF spec differs from actual owner parts manifest')
    dest=Path(dest);tmp=dest.with_name('.assembling-'+dest.name);whole=hashlib.sha256();total=0;header=b''
    try:
        with tmp.open('wb')as out:
            for part in spec['parts']:
                url='https://raw.githubusercontent.com/'+REPO+'/'+commit+'/'+urllib.parse.quote(part['repo_path'],safe='/')
                h=hashlib.sha256();count=0
                with urllib.request.urlopen(url,timeout=300)as response:
                    for chunk in iter(lambda:response.read(4*1024*1024),b''):
                        if len(header)<5:header=(header+chunk)[:5]
                        count+=len(chunk);total+=len(chunk);h.update(chunk);whole.update(chunk);out.write(chunk)
                require(count==part['bytes']and h.hexdigest()==part['sha256'],'Pinned actual PDF byte-part differs: '+part['repo_path'])
        require(total==spec['bytes']and whole.hexdigest()==spec['sha256']and header==b'%PDF-','Reassembled actual complete PDF bytes/SHA/header mismatch; pointer or wrong order rejected')
        tmp.replace(dest)
    finally:
        if tmp.exists():tmp.unlink()
    return image_rows

def build(root,output,hardlink_immutable_media=False):
    root=Path(root).resolve();output=Path(output).resolve()
    require(not output.exists()or not any(output.iterdir()),'Build output must be fresh/empty')
    output.mkdir(parents=True,exist_ok=True);plan=json.loads((root/PROGRAM/'release-plan.json').read_text())
    require(plan['schema_version']==3 and plan['release']['asset_policy']==ASSET_POLICY and plan['release']['expected_asset_count']==71,'V3 exact71 contract required')
    for rel,spec in plan['files'].items():
        p=root/rel;require(p.is_file()and not p.is_symlink()and p.stat().st_size==spec['bytes']and sha(p)==spec['sha256'],'Frozen assets branch differs: '+rel)
    assets=exact_assets(plan['records'],plan['published_pdf']);require(assets==plan['exact_assets'],'Frozen exact71 inventory drift')
    inventory=root/plan['repository_asset_inventory_path'];sums=root/plan['repository_sha256sums_path']
    require(sha(inventory)==plan['repository_asset_inventory_sha256']and sha(sums)==plan['repository_sha256sums_sha256'],'Repository-only inventory/SHA records differ')
    require(json.loads(inventory.read_text())['assets']==assets,'Repository inventory differs from exact71 plan')
    image_rows=download_pdf(plan['published_pdf'],output/assets[0]['name'])
    map_path=root/plan['book_illustrations_repo_path']
    require(sha(map_path)==plan['published_pdf']['illustrations_manifest']['sha256'],'Staged book map differs from pinned PDF-owner map')
    book_illustrations(json.loads(map_path.read_text()),[{'source_id':r['id'],'new_id':r['new_id']}for r in plan['records']])
    for row in plan['records']:
        if 'illustration'in row:
            require(row['illustration']['source_id']==row['id'] and row['illustration']['new_id']==row['new_id'] and row['illustration']['book_source_sha256']==image_rows[row['id']]['sha256'],'Video illustration belongs to a different book article')
    records={r['new_id']:r for r in plan['records']}
    for a in assets[1:]:
        r=records[a['new_id']];canonical=root/r['canonical_path'];reordered=root/r['reordered_path']
        require(sha(canonical)==sha(reordered)==a['sha256']and reordered.stat().st_size==a['bytes'],'Dual-path actual final MP4 differs')
        target=output/a['name']
        if hardlink_immutable_media:
            try:os.link(reordered,target)
            except OSError:shutil.copy2(reordered,target)
        else:shutil.copy2(reordered,target)
    for a in assets:require((output/a['name']).stat().st_size==a['bytes']and sha(output/a['name'])==a['sha256'],'Actual upload file changed')
    result={'schema_version':3,'revision':plan['revision'],'title':plan['release']['title'],'assets':assets,'published_pdf':plan['published_pdf'],
        'finalization_manifest_path':plan['manifest_path'],'finalization_manifest_sha256':sha(root/plan['manifest_path']),
        'repository_asset_inventory_path':plan['repository_asset_inventory_path'],'repository_asset_inventory_sha256':plan['repository_asset_inventory_sha256'],
        'repository_sha256sums_path':plan['repository_sha256sums_path'],'repository_sha256sums_sha256':plan['repository_sha256sums_sha256'],
        'remote_receipt_repo_path':plan['remote_receipt_repo_path'],'audit_path':plan['audit_path'],
        'release_plan_repo_path':PROGRAM+'/release-plan.json','release_plan_sha256':sha(root/PROGRAM/'release-plan.json')}
    write(output/'upload-plan.json',result);return output/'upload-plan.json'

def exact_remote_assets(release_id,expected,allow_partial=False):
    rows=remote_assets(release_id);names=[r['name']for r in rows];want=[a['name']for a in expected]
    require(len(names)==len(set(names))and set(names)<=set(want),'Unexpected or duplicate remote attachments; metadata/ZIP/receipt attachments are forbidden')
    if not allow_partial:require(len(rows)==71 and names==want,'Remote attachments must be exactly PDF then70 videos in frozen book order')
    return rows

def tag_commit(tag):
    ref=api('git/ref/tags/'+urllib.parse.quote(tag,safe=''));obj=ref['object'];seen=set()
    while obj['type']=='tag':
        require(obj['sha']not in seen,'Tag object cycle');seen.add(obj['sha']);obj=api('git/tags/'+obj['sha'])['object']
    require(obj['type']=='commit','Release tag must identify a commit');return obj['sha']

def publish(root,output,target_commit,publisher_mode='native-actions',asset_commit=None):
    require(re.fullmatch('[0-9a-f]{40}',target_commit or''),'Pin primary archive commit')
    execution=publisher_execution(publisher_mode)
    if publisher_mode=='native-actions':asset_commit=os.environ['ASSET_COMMIT']
    require(re.fullmatch('[0-9a-f]{40}',asset_commit or''),'Pin the actual frozen asset commit')
    output=Path(output);plan=json.loads((output/'upload-plan.json').read_text());require(plan['schema_version']==3,'V3 upload plan required')
    assets=plan['assets'];require(len(assets)==71 and sum(a['kind']=='pdf'for a in assets)==1 and sum(a['kind']=='video'for a in assets)==70,'Only one PDF+70 MP4 assets are allowed')
    manifest_bytes=raw_primary(plan['finalization_manifest_path'],target_commit)
    require(hashlib.sha256(manifest_bytes).hexdigest()==plan['finalization_manifest_sha256'],'Primary manifest does not match frozen assets')
    frozen_manifest=json.loads(manifest_bytes);require(frozen_manifest['exact_release_assets']==assets and frozen_manifest['published_pdf']==plan['published_pdf'],'Upload inventory/PDF differs from actual frozen canonical manifest')
    if publisher_mode=='local-gh':
        # This is the same immutable assets-checkout binding the native job
        # obtains from its checkout, with a real GET and no invented run ID.
        local_plan=Path(root)/plan['release_plan_repo_path'];actual_plan=raw_primary(plan['release_plan_repo_path'],asset_commit)
        require(sha(local_plan)==plan['release_plan_sha256']==hashlib.sha256(actual_plan).hexdigest(),'Actual local release plan differs from the pinned asset commit')

    # Complete the existing physical-file checks before any draft creation.
    # Upload checks still compare the actual remote bytes/digests afterward.
    for expected in assets:
        path=output/expected['name']
        require(path.is_file()and path.stat().st_size==expected['bytes']and sha(path)==expected['sha256'],'Local upload bytes missing/changed: '+expected['name'])
    revision=plan['revision'];binding='Delivery manifest SHA-256: '+plan['finalization_manifest_sha256']
    release=api('releases/tags/'+urllib.parse.quote(revision,safe=''),missing_ok=True)
    if release:
        require(release['draft']and release['target_commitish']==target_commit and binding in(release['body']or''),'Existing published release is immutable or draft belongs to other manifest')
    else:
        require(api('git/ref/tags/'+urllib.parse.quote(revision,safe=''),missing_ok=True)is None,'Existing historical tag must not move')
        release=api('releases','POST',{'tag_name':revision,'target_commitish':target_commit,'name':plan['title'],'draft':True,'prerelease':False,
            'body':'<!-- '+binding+' -->\n\n整本PDF与70部4K视频，视频依书中顺序编号。制作与核验记录永久保存在仓库。'})
    existing=exact_remote_assets(release['id'],assets,True);by_name={a['name']:a for a in existing}
    for expected in assets:
        path=output/expected['name']
        verify_asset(by_name.get(expected['name'])or upload(release,path),expected)
    # Exact set/order and all actual size/hash checks happen BEFORE making the Release public.
    rows=exact_remote_assets(release['id'],assets);verified=[verify_asset(r,e)for r,e in zip(rows,assets)]
    api('releases/'+str(release['id']),'PATCH',{'draft':False,'make_latest':'true'})
    final=api('releases/'+str(release['id']));require(final['draft']is False and tag_commit(revision)==target_commit,'Public release/tag commit verification failed')
    rows=exact_remote_assets(release['id'],assets);verified=[verify_asset(r,e)for r,e in zip(rows,assets)]
    receipt={'schema_version':3,'passed':True,'release_public':True,'delivery_complete':False,'revision':revision,'repository':REPO,
        'release_id':final['id'],'tag_name':revision,'release_url':final['html_url'],'primary_archive_commit':target_commit,
        'asset_commit':asset_commit,'publisher_execution':execution,'published_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'finalization_manifest_path':plan['finalization_manifest_path'],'finalization_manifest_sha256':plan['finalization_manifest_sha256'],
        'published_pdf':plan['published_pdf'],'planned_assets':assets,'assets':verified,'all_remote_bytes_and_digests_verified':True,
        'repository_asset_inventory_path':plan['repository_asset_inventory_path'],'repository_asset_inventory_sha256':plan['repository_asset_inventory_sha256'],
        'repository_sha256sums_path':plan['repository_sha256sums_path'],'repository_sha256sums_sha256':plan['repository_sha256sums_sha256'],
        'remote_receipt_repo_path':plan['remote_receipt_repo_path'],'audit_path':plan['audit_path'],
        'permanent_dual_repository_receipt_required':True}
    if publisher_mode=='native-actions':
        receipt.update(publisher_workflow_run_id=execution['workflow_run_id'],publisher_workflow_head_sha=execution['workflow_head_sha'],publisher_workflow_path=execution['workflow_path'])
    write(output/'REMOTE-DELIVERY-VERIFICATION.json',receipt)
    # Native Actions transports this via artifact; local mode uses this exact file.
    # Neither is a Release attachment or permanent storage before dual archival.
    result={'release_public':True,'delivery_complete':False,'url':final['html_url'],'verified_assets':71,'receipt_persistence_required':True}
    print(json.dumps(result,ensure_ascii=False));return result

def main():
    p=argparse.ArgumentParser();p.add_argument('command',choices=['build','publish','inspect-local']);p.add_argument('--root',default='.')
    p.add_argument('--output',required=True);p.add_argument('--target-commit');p.add_argument('--publisher-mode',choices=['native-actions','local-gh'],default='native-actions');p.add_argument('--asset-commit');p.add_argument('--hardlink-immutable-media',action='store_true');a=p.parse_args()
    if a.command=='build':print(build(a.root,a.output,a.hardlink_immutable_media))
    elif a.command=='inspect-local':print(json.dumps(inspect_local(a.output),ensure_ascii=False))
    else:publish(a.root,a.output,a.target_commit,a.publisher_mode,a.asset_commit)

if __name__=='__main__':main()
