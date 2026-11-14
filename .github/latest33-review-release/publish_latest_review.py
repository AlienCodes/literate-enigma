"""Verify the exact qualified latest33 bytes and publish one immutable review ZIP."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import urllib.parse
import urllib.request
import zipfile

from review_contract import (
    PRIMARY, BACKUP, REPOSITORIES, ASSET_NAMES, TAG, ZIP_NAME, INVENTORY_PATH,
    REGISTRY_PATH, require, sha_bytes, validate_manifest, validate_actual_selection,
)

HERE = Path(__file__).resolve().parent
STAMP = (2026, 11, 14, 0, 0, 0)


def sha(path):
    with Path(path).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def api(path, method='GET', data=None, missing=False):
    command = ['gh', 'api', 'repos/'+PRIMARY+'/'+path]
    if method != 'GET':
        command += ['-X', method]
    if data is not None:
        command += ['--input', '-']
    result = subprocess.run(command, input=None if data is None else json.dumps(data).encode(),
                            capture_output=True)
    if missing and result.returncode and b'HTTP 404' in result.stderr:
        return None
    if result.returncode:
        raise RuntimeError('GitHub publication operation failed, exit '+str(result.returncode))
    return json.loads(result.stdout)


def raw_url(repository, ref, path):
    require(repository in REPOSITORIES, 'Unexpected repository')
    return ('https://raw.githubusercontent.com/'+repository+'/'+ref+'/' +
            urllib.parse.quote(path, safe='/'))


def fetch_small(repository, ref, expected):
    with urllib.request.urlopen(raw_url(repository, ref, expected['repo_path']), timeout=180) as r:
        require(r.status == 200, 'Public archived evidence was not readable')
        raw = r.read(expected['bytes']+1)
    require(len(raw) == expected['bytes'] and sha_bytes(raw) == expected['sha256'],
            'Archived metadata identity differs')
    return json.loads(raw)


def fetch_dual_snapshots(manifest):
    snap = manifest['snapshot']
    result = {}
    for key in ('inventory', 'latest_requests'):
        p = fetch_small(PRIMARY, snap['primary_commit'], snap[key])
        b = fetch_small(BACKUP, snap['backup_commit'], snap[key])
        require(p == b, 'Primary and backup frozen snapshots differ')
        result[key] = p
    return result


def fetch_review_documents(manifest):
    result = {}
    for row in manifest['videos']:
        if row['qualification'] != 'verified_latest_review_only':
            continue
        docs = {}
        for key, ev in row['evidence'].items():
            p = fetch_small(PRIMARY, row['asset_commit'], ev)
            b = fetch_small(BACKUP, row['asset_commit'], ev)
            require(p == b, 'The actual review proof must be preserved in both repositories')
            docs[key] = p
        result[row['source_id']] = docs
    return result


def live_metadata(repository, ref, path):
    with urllib.request.urlopen(raw_url(repository, ref, path), timeout=180) as r:
        require(r.status == 200, 'Latest canonical metadata was not readable')
        raw = r.read(5_000_001)
    require(len(raw) < 5_000_001, 'Unexpectedly large live canonical metadata')
    return json.loads(raw)


def require_still_latest(manifest, docs):
    # Check per-article identities, allowing unrelated article updates elsewhere.
    for repo, ref in ((PRIMARY, 'main'), (BACKUP, 'codex/all-deliverables-20261113')):
        inventory = live_metadata(repo, ref, INVENTORY_PATH)
        registry = live_metadata(repo, ref, REGISTRY_PATH)
        validate_actual_selection(manifest, inventory, registry, docs)


def stream_media(row, repository, destination=None):
    h = hashlib.sha256(); size = 0
    target = None if destination is None else Path(destination).open('wb')
    try:
        with urllib.request.urlopen(raw_url(repository, row['asset_commit'],
                                            row['video_repo_path']), timeout=180) as response:
            require(response.status == 200, 'Archived video was not readable')
            while chunk := response.read(1024*1024):
                h.update(chunk); size += len(chunk)
                if target is not None:
                    target.write(chunk)
    finally:
        if target is not None:
            target.close()
    require(size == row['bytes'] and h.hexdigest() == row['sha256'],
            'The entire archived MP4 must match the qualified file')
    return {'repository': repository, 'source_id': row['source_id'],
            'book_order': row['book_order'], 'bytes': size, 'sha256': h.hexdigest(),
            'http_status': 200, 'passed': True}


def actual_4K_probe(path):
    result = subprocess.run(['ffprobe','-v','error','-select_streams','v:0',
                             '-show_entries','stream=width,height,avg_frame_rate,nb_frames',
                             '-of','json',str(path)], check=True, capture_output=True)
    s = json.loads(result.stdout)['streams']
    require(len(s) == 1, 'Exactly one video stream required')
    s = s[0]
    require((s['width'], s['height'], s['avg_frame_rate']) == (3840,2160,'30/1') and
            int(s['nb_frames']) > 120, 'Archived media is not the required 4K/30 video')
    return s


def write_bundle(manifest_path, manifest, media, out):
    raw_manifest = Path(manifest_path).read_bytes()
    checksums = ''.join(r['sha256']+'  '+r['release_name']+'\n'
                        for r in manifest['videos']).encode()
    readme = (
        '第38—70篇：33篇最新4K审核视频\n\n'
        '每个MP4均由已核查的实际文件逐字节复制，未重新编码或更改音频。\n'
        '本包包含已定稿文件及已核查、仍待用户逐篇定稿的审核文件；'
        '审核文件不替换GitHub的最新定稿目录。\n'
        '新生成审核文件采用末句后约0.6秒、插图2秒及简述2秒；'
        '复用的已核查成片保留原尾段，逐篇方式见MANIFEST.json。\n'
        'SHA256SUMS.txt列出33个MP4的完整SHA-256。\n\n'
        '最新定稿目录：https://github.com/'+PRIMARY+
        '/tree/main/视频修订定稿/最终定稿/视频\n').encode()
    (out/'MANIFEST.json').write_bytes(raw_manifest)
    (out/'SHA256SUMS.txt').write_bytes(checksums)
    (out/'README.txt').write_bytes(readme)
    zipped = out/ZIP_NAME
    def entry(name):
        info = zipfile.ZipInfo(name, date_time=STAMP)
        info.compress_type = zipfile.ZIP_STORED
        info.external_attr = 0o100644 << 16
        return info
    with zipfile.ZipFile(zipped,'w',compression=zipfile.ZIP_STORED,allowZip64=True) as z:
        for row in manifest['videos']:
            with Path(media[row['source_id']]).open('rb') as src, z.open(entry(row['release_name']),'w') as dst:
                shutil.copyfileobj(src,dst,length=1024*1024)
        for name in ('MANIFEST.json','SHA256SUMS.txt','README.txt'):
            z.writestr(entry(name),(out/name).read_bytes())
    with zipfile.ZipFile(zipped) as z:
        expected = {r['release_name'] for r in manifest['videos']} | {
            'MANIFEST.json','SHA256SUMS.txt','README.txt'}
        require(len(z.infolist()) == 36 and set(z.namelist()) == expected,
                'ZIP must contain exactly 33 MP4s and three public metadata files')
        require(z.testzip() is None, 'ZIP CRC validation failed')
        require(z.read('MANIFEST.json') == raw_manifest, 'The frozen manifest changed')
        for row in manifest['videos']:
            require(z.getinfo(row['release_name']).file_size == row['bytes'], 'ZIP member size differs')
            with z.open(row['release_name']) as src:
                require(hashlib.file_digest(src,'sha256').hexdigest() == row['sha256'],
                        'ZIP member SHA-256 differs')
    return zipped


def publish_assets(manifest, files, head):
    zip_sha = sha(files[ZIP_NAME])
    existing = api('git/ref/tags/'+TAG, missing=True)
    if existing is not None:
        require(existing['object']['type'] == 'commit' and existing['object']['sha'] == head,
                'Never retarget a published or partially published immutable tag')
    marker = 'Latest qualified books38-70 user102 ZIP SHA-256: '+zip_sha
    release = api('releases/tags/'+TAG, missing=True)
    if release is None:
        candidates = [r for r in api('releases?per_page=100')
                      if r['tag_name'] == TAG and marker in (r.get('body') or '')]
        require(len(candidates) <= 1, 'Ambiguous prior draft')
        release = candidates[0] if candidates else None
    if release is None:
        release = api('releases','POST',{'tag_name':TAG,'target_commitish':head,
                      'name':manifest['release_title'],
                      'body':manifest['release_body']+'\n\n<!-- '+marker+' -->',
                      'draft':True,'prerelease':True})
    require(release['tag_name'] == TAG and marker in (release.get('body') or '') and
            release['target_commitish'] == head, 'Existing release identity differs')
    assets = api('releases/'+str(release['id'])+'/assets?per_page=100')
    require(len({a['name'] for a in assets}) == len(assets) and
            {a['name'] for a in assets} <= set(ASSET_NAMES), 'Unexpected existing asset')
    byname = {a['name']:a for a in assets}
    for name in ASSET_NAMES:
        path = files[name]
        if name in byname:
            a = byname[name]
            require(a['state'] == 'uploaded' and a['size'] == path.stat().st_size and
                    a['digest'] == 'sha256:'+sha(path), 'Never overwrite different old assets')
        else:
            subprocess.run(['gh','release','upload',TAG,str(path),'--repo',PRIMARY],check=True)
    return release, marker


def main():
    if os.environ.get('GITHUB_REPOSITORY') != PRIMARY:
        print('The backup retains source files; only the primary publishes this review Release.')
        return
    out = Path(os.environ['GITHUB_WORKSPACE'])/'latest-review-release-output'
    out.mkdir(exist_ok=True)
    mp = HERE/'MANIFEST.json'
    manifest = validate_manifest(json.loads(mp.read_text()))
    for name, expected in manifest['publisher_program_sha256s'].items():
        require(Path(name).name == name and sha(HERE/name) == expected, 'Publisher code changed')
    require(set(manifest['publisher_program_sha256s']) ==
            {'publish_latest_review.py','compile_latest_review.py','review_contract.py',
             'latest_final_directory_policy.py'}, 'All four reviewed programs must be pinned')
    snap = fetch_dual_snapshots(manifest)
    docs = fetch_review_documents(manifest)
    validate_actual_selection(manifest,snap['inventory'],snap['latest_requests'],docs)
    require_still_latest(manifest,docs)
    folder = out/'unchanged-validated-MP4s'; folder.mkdir(exist_ok=True)
    media, streams, probes = {}, [], {}
    for row in manifest['videos']:
        path = folder/row['release_name']
        streams.append(stream_media(row,PRIMARY,path))
        streams.append(stream_media(row,BACKUP))
        probes[row['source_id']] = actual_4K_probe(path)
        media[row['source_id']] = path
    zipped = write_bundle(mp,manifest,media,out)
    require_still_latest(manifest,docs)
    files = {name:out/name for name in ASSET_NAMES}
    head = os.environ['GITHUB_SHA']
    require(len(head) == 40, 'Actual native head is required')
    release, marker = publish_assets(manifest,files,head)
    require_still_latest(manifest,docs)
    if release['draft']:
        api('releases/'+str(release['id']),'PATCH',
            {'draft':False,'prerelease':True,'make_latest':'false'})
    release = api('releases/'+str(release['id']))
    require(release['draft'] is False and release['prerelease'] is True and
            marker in release['body'], 'Release must remain an explicitly marked review')
    tag = api('git/ref/tags/'+TAG)['object']
    require(tag['type'] == 'commit' and tag['sha'] == head, 'Immutable release tag mismatch')
    assets = api('releases/'+str(release['id'])+'/assets?per_page=100')
    require(len(assets) == 4 and {a['name'] for a in assets} == set(ASSET_NAMES),
            'Release assets are incomplete')
    public = []
    for a in assets:
        path = files[a['name']]
        require(a['state'] == 'uploaded' and a['size'] == path.stat().st_size and
                a['digest'] == 'sha256:'+sha(path), 'Uploaded asset identity differs')
        h = hashlib.sha256(); n = 0
        with urllib.request.urlopen(a['browser_download_url'],timeout=180) as r:
            require(r.status == 200, 'Published asset is not publicly readable')
            while chunk := r.read(1024*1024):
                n += len(chunk); h.update(chunk)
        require(n == path.stat().st_size and h.hexdigest() == sha(path),
                'Entire public download differs')
        public.append({'name':a['name'],'bytes':n,'sha256':h.hexdigest(),
                       'url':a['browser_download_url'],'actual_entire_public_download_verified':True})
    receipt = {'passed':True,'kind':'actual-latest-qualified-books38-70-user102-review-release',
               'requested_book_range':['38','70'],'video_count':33,'ZIP_entry_count':36,
               'ZIP_CRC_errors':0,'all33_qualified_MP4s_exact_before_and_inside_ZIP':True,
               'actual_dual_full_video_HTTP_streams':len(streams),
               'all33_individual_user_final_acceptance_claimed':False,
               'uniform_0_6_second_tail_claimed':False,'current_final_aliases_changed':False,
               'media_reencoded_or_audio_changed':False,'other_releases_or_tags_modified':False,
               'release_id':release['id'],'release_url':release['html_url'],
               'assets':public,'manifest_sha256':sha(mp),
               'publisher_program_sha256s':manifest['publisher_program_sha256s'],
               'actual_current33_live_registry_checked_before_download_and_twice_before_publish':True,
               'native_actions_run_id':int(os.environ['GITHUB_RUN_ID']),
               'native_actions_head_sha':head,'actual_4K_probes':probes,
               'actual_dual_downloads':streams,
               'recorded_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
    (out/'RELEASE-VERIFICATION.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:v for k,v in receipt.items()
                      if k not in ('actual_4K_probes','actual_dual_downloads')},ensure_ascii=False),flush=True)


if __name__ == '__main__':
    main()
