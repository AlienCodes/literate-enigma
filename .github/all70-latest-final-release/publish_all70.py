"""Mature primary-token Release workflow, only after strict actual all70 qualification."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import urllib.parse
import urllib.request
import zipfile
import zlib

from all70_contract import *
from compile_all70 import public_json, public_raw

HERE = Path(__file__).resolve().parent

def file_sha(path):
    with Path(path).open('rb') as source:
        return hashlib.file_digest(source, 'sha256').hexdigest()

def api(path, method='GET', data=None, missing_ok=False):
    cmd = ['gh', 'api', 'repos/' + PRIMARY + '/' + path]
    if method != 'GET':
        cmd += ['-X', method]
    if data is not None:
        cmd += ['--input', '-']
    r = subprocess.run(cmd, input=None if data is None else json.dumps(data).encode(), capture_output=True)
    if missing_ok and r.returncode and b'(HTTP 404)' in r.stderr:
        return None
    if r.returncode:
        raise RuntimeError(r.stderr.decode(errors='replace'))
    return json.loads(r.stdout)

def current_still_exact(config):
    """Public metadata only, never read a local ROOTSTATE or infer current from history."""
    videos = validate_manifest(config)
    for repo, s in config['snapshots'].items():
        need(public_json(repo, 'git/ref/heads/' + s['branch'])['object']['sha'] == s['head'],
             'Canonical branch moved; bind a new actual complete snapshot')
        docs = {}
        for role, path in [('inventory', INVENTORY), ('registry', REGISTRY)]:
            value = public_raw(repo, s['head'], path)
            need(len(value) == s[role]['bytes'] and sha(value) == s[role]['sha256'] and
                 git_blob(value) == s[role]['git_blob_sha'], 'Actual canonical JSON no longer matches')
            docs[role] = json.loads(value)
        requests, current = require_all70(docs['inventory'], docs['registry'])
        for v in videos:
            c, e = current[v['source_id']], requests[v['source_id']]
            need(media_identity(c) == media_identity(v) and e['current_video_order'] == v['current_video_order'] and
                 e['title_zh'] == v['title_zh'] and e['validation_handoff_sha256'] == v['validation_handoff_sha256'],
                 'A pending/newer or different current row must stop publication')
        commit = public_json(repo, 'git/commits/' + s['head'])
        root = public_json(repo, 'git/trees/' + commit['tree']['sha'])
        vr = next(x['sha'] for x in root['tree'] if x['path'] == '视频修订定稿')
        vt = public_json(repo, 'git/trees/' + vr)
        fr = next(x['sha'] for x in vt['tree'] if x['path'] == '最终定稿')
        ft = public_json(repo, 'git/trees/' + fr)
        actual_alias_tree = next(x['sha'] for x in ft['tree'] if x['path'] == '视频')
        need(actual_alias_tree == s['alias_tree_sha'], 'The current final-directory tree changed')
        aliases = public_json(repo, 'git/trees/' + actual_alias_tree)
        need(not aliases.get('truncated', False) and len(aliases['tree']) == 70, 'Exactly70 latest aliases required')
        nodes = {x['path']: x for x in aliases['tree']}
        need(set(nodes) == {v['release_name'] for v in videos}, 'Wrong latest filenames/order')
        for v in videos:
            n = nodes[v['release_name']]
            need((n['mode'], n['type'], n['sha'], n['size']) ==
                 ('100644', 'blob', v['alias_git_blob_sha'], v['bytes']), 'Wrong canonical alias blob')

def archived_documents(v):
    docs = {}
    for role, e in v['evidence'].items():
        value = public_raw(PRIMARY, v['asset_commit'], e['repo_path'])
        need(len(value) == e['bytes'] and sha(value) == e['sha256'], 'Archived actual quality proof changed')
        docs[role] = json.loads(value)
    validate_documents(v, docs)
    return docs

def download_video(repo, head, v, path=None):
    url = 'https://raw.githubusercontent.com/' + repo + '/' + head + '/' + urllib.parse.quote(v['canonical_alias_path'], safe='/')
    h, size = hashlib.sha256(), 0
    with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent':'all70-current-MP4-whole-byte-readback'}), timeout=180) as source:
        need(source.status == 200, 'Actual complete MP4 read failed')
        if path is not None:
            with Path(path).open('xb') as out:
                while chunk := source.read(1024*1024):
                    h.update(chunk); size += len(chunk); out.write(chunk)
        else:
            while chunk := source.read(1024*1024):
                h.update(chunk); size += len(chunk)
    need((size, h.hexdigest()) == (v['bytes'], v['sha256']), 'Entire canonical MP4 differs from qualified final')
    return {'repository':repo, 'commit':head, 'video_order':v['current_video_order'],
            'source_id':v['source_id'], 'bytes':size, 'sha256':h.hexdigest(), 'http_status':200}

def probe_video(path, v):
    r = subprocess.run(['ffprobe','-v','error','-show_entries',
        'stream=codec_type,codec_name,width,height,r_frame_rate,nb_frames','-of','json',str(path)],
        capture_output=True, text=True, check=True)
    rows = json.loads(r.stdout)['streams']
    video = [x for x in rows if x['codec_type'] == 'video']
    audio = [x for x in rows if x['codec_type'] == 'audio']
    need(len(video) == len(audio) == 1 and audio[0]['codec_name'] == 'aac', 'Wrong media stream layout')
    p = video[0]
    need((p['width'], p['height'], p['r_frame_rate'], int(p['nb_frames'])) ==
         (3840,2160,'30/1',v['actual_probe']['frames']), 'Actual downloaded MP4 probe differs')

def zip_info(name):
    info = zipfile.ZipInfo(name, (2026,11,15,0,0,0))
    info.compress_type = zipfile.ZIP_STORED
    info.external_attr = 0o100644 << 16
    return info

def make_bundle(path, members, all_videos, directory, part_number, part_count):
    manifest, checksums = inner_lists(all_videos,members,part_number,part_count)
    with zipfile.ZipFile(path,'x',allowZip64=True) as archive:
        for v in members:
            with (directory/v['release_name']).open('rb') as source, archive.open(zip_info(v['release_name']),'w') as target:
                shutil.copyfileobj(source,target,1024*1024)
        archive.writestr(zip_info('MANIFEST.json'),manifest)
        archive.writestr(zip_info('SHA256SUMS.txt'),checksums)
    need(path.stat().st_size < LIMIT, 'Actual ZIP exceeds GitHub per-asset2GiB limit; do not upload')
    need(path.stat().st_size == exact_stored_zip_bytes(members,all_videos,part_number,part_count),
         'Actual ZIP layout differs from exact size calculation; do not publish')
    with zipfile.ZipFile(path) as archive:
        need(archive.namelist() == [v['release_name'] for v in members]+['MANIFEST.json','SHA256SUMS.txt'],
             'Unexpected ZIP member; never include source/model/private/environment files')
        for v in members:
            h, n, crc = hashlib.sha256(), 0, 0
            with archive.open(v['release_name']) as source:
                while chunk := source.read(1024*1024):
                    h.update(chunk); n += len(chunk); crc = zlib.crc32(chunk,crc)
            need((n,h.hexdigest()) == (v['bytes'],v['sha256']) and
                 (crc & 0xffffffff) == archive.getinfo(v['release_name']).CRC,
                 'ZIP internal MP4 SHA/CRC differs from the actual accepted media')
        need(archive.read('MANIFEST.json') == manifest and archive.read('SHA256SUMS.txt') == checksums,
             'ZIP integrity metadata changed')
    return {'name':path.name,'bytes':path.stat().st_size,'sha256':file_sha(path),
            'included_video_orders':[v['current_video_order'] for v in members],
            'all_internal_MP4_bytes_SHA_and_CRC_verified':True}

def main():
    if os.environ.get('GITHUB_REPOSITORY') != PRIMARY:
        print('Only the existing primary repository publishes; backup preserves code.')
        return
    config = json.loads((HERE/'MANIFEST.json').read_text())
    videos = validate_manifest(config)
    current_still_exact(config)
    out = Path(os.environ['GITHUB_WORKSPACE'])/'all70-release-output'
    out.mkdir(exist_ok=False)
    # One retained set of MP4s plus stored ZIP parts; reserve is checked before any large download.
    need(shutil.disk_usage(out).free > 2*config['total_MP4_bytes'] + 1024**3,
         'Runner has insufficient disk; do not use the small sharedHOST as fallback')
    whole_reads = []
    for v in videos:
        archived_documents(v)
        path = out/v['release_name']
        whole_reads.append(download_video(PRIMARY,config['snapshots'][PRIMARY]['head'],v,path))
        whole_reads.append(download_video(BACKUP,config['snapshots'][BACKUP]['head'],v))
        probe_video(path,v)
    parts = archive_parts(videos)
    bundles = []
    for n, members in enumerate(parts,1):
        name = ZIP_NAME if len(parts)==1 else f'01-70-LATEST-4K-FINAL.part{n:02}-of-{len(parts):02}.zip'
        bundles.append(make_bundle(out/name,members,videos,out,n,len(parts)))
    current_still_exact(config)
    head = config['snapshots'][PRIMARY]['head']
    existing_tag = api('git/ref/tags/'+TAG,missing_ok=True)
    if existing_tag is not None:
        need(existing_tag['object']['type']=='commit' and existing_tag['object']['sha']==head,
             'Existing tag has different canonical bytes; never retarget or force')
    marker = 'All70 latest final manifest SHA-256: '+file_sha(HERE/'MANIFEST.json')
    release = api('releases/tags/'+TAG,missing_ok=True)
    if release is None:
        release = api('releases','POST',{'tag_name':TAG,'target_commitish':head,
            'name':'考研学人｜70篇最新4K定稿全集｜末句停留0.6秒',
            'body':'全部70篇已完成最新用户修订、完整质量验收及双仓永久归档。包内仅70篇最新4K视频及文件校验清单，未重新编码，旧版历史保留。\n\n<!-- '+marker+' -->',
            'draft':True,'prerelease':False})
    need(release['tag_name']==TAG and marker in (release.get('body')or''), 'Release identity collision')
    need(release['target_commitish']==head, 'Wrong canonical tag target')
    assets = api('releases/'+str(release['id'])+'/assets?per_page=100')
    expected = {b['name']:b for b in bundles}
    need(len(assets)<=len(bundles) and all(x['name']in expected for x in assets), 'Unexpected old Release asset')
    present = {x['name']:x for x in assets}
    for b in bundles:
        if b['name']in present:
            x=present[b['name']];need(x['size']==b['bytes']and x['digest']=='sha256:'+b['sha256'],
                                    'Existing asset differs; never delete or clobber')
        else:
            subprocess.run(['gh','release','upload',TAG,str(out/b['name']),'--repo',PRIMARY],check=True)
    assets = api('releases/'+str(release['id'])+'/assets?per_page=100')
    need(len(assets)==len(bundles), 'Missing completed upload')
    for x in assets:
        b=expected[x['name']];need(x['state']=='uploaded'and x['size']==b['bytes']and
                                 x['digest']=='sha256:'+b['sha256'],'Server asset digest mismatch')
    current_still_exact(config)
    if release['draft']:
        api('releases/'+str(release['id']),'PATCH',{'draft':False,'prerelease':False,'make_latest':'false'})
    release=api('releases/'+str(release['id']));need(not release['draft'],'Release still draft')
    tag=api('git/ref/tags/'+TAG)['object'];need(tag['type']=='commit'and tag['sha']==head,'Wrong permanent tag')
    assets=api('releases/'+str(release['id'])+'/assets?per_page=100')
    actual_downloads=[]
    for x in assets:
        b=expected[x['name']];h,n=hashlib.sha256(),0
        with urllib.request.urlopen(x['browser_download_url'],timeout=300)as source:
            need(source.status==200,'Public complete ZIP download failed')
            while chunk:=source.read(1024*1024):h.update(chunk);n+=len(chunk)
        need((n,h.hexdigest())==(b['bytes'],b['sha256']),'Entire public ZIP digest mismatch')
        actual_downloads.append({**b,'public_download_url':x['browser_download_url'],
                                 'actual_public_entire_HTTP200_size_SHA_verified':True})
    receipt={'passed':True,'video_count':70,'release_id':release['id'],'release_url':release['html_url'],
             'public_ZIP_assets':actual_downloads,'single_fullZIP':len(bundles)==1,
             'split_only_if_actual_input_size_requires_2GiB_limit':True,
             'actual_dual_canonical_whole_MP4_reads':whole_reads,
             'all70_internal_MP4_size_SHA_CRC_verified':True,'only_MP4_manifest_checksums_inside_ZIP':True,
             'no_reencoding_source_private_models_PDF_or_ROOTSTATE_packaged':True,
             'manifest_sha256':file_sha(HERE/'MANIFEST.json'),'publisher_sha256':file_sha(__file__),
             'native_actions_run_id':int(os.environ['GITHUB_RUN_ID']),'native_actions_head_sha':os.environ['GITHUB_SHA'],
             'canonical_primary_head':head,'old_versions_Releases_and_media_deleted':False}
    (out/'RELEASE-VERIFICATION.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(receipt,ensure_ascii=False),flush=True)

if __name__=='__main__':
    main()
