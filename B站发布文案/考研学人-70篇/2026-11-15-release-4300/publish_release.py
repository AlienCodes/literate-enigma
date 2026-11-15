"""Download immutable, dual-archived originals and publish this small release only.

No rendering, git writes, tag updates, deletion, upload clobbering, or video work.
Only the explicitly installed, SHA-pinned config can authorize a live run.
"""
from pathlib import Path, PurePosixPath
from urllib.parse import quote, urlparse
from urllib.request import Request, urlopen
from urllib.error import HTTPError
import argparse
import hashlib
import io
import json
import os
import re
import struct
import subprocess
import time
import zipfile

PRIMARY = 'alienalgorithm/postgraduate-vocabulary'
BACKUP = 'AlienCodes/literate-enigma'
TAG = 'bilibili-4300-covers-and-description-2026.11.15'
TITLE = '考研学人｜4300封面与趣味简介（4:3／16:9）'
NAMESPACE = 'bilibili-4300-cover-description-v1'
ZIP_NAME = 'BILIBILI-4300-COVERS-AND-DESCRIPTION-2026.11.15.zip'
MANIFEST_NAME = 'MANIFEST.json'
SUMS_NAME = 'SHA256SUMS.txt'
FULL_NAME = 'DESCRIPTION-EMOJI-FULL-BILINGUAL-READY-TO-COPY.txt'
SHORT_NAME = 'DESCRIPTION-EMOJI-SHORT-ALL70-ZH-READY-TO-COPY.txt'
PART_NAMES = [f'EMOJI-BILINGUAL-CATALOG-PART-{n:02}.txt' for n in range(1, 5)]
COVER_NAMES = {f'BILIBILI-COVER-4300-{ratio}.{ext}': (width, height, fmt)
               for ratio, width, height in [('4x3', 1440, 1080), ('16x9', 1600, 900)]
               for ext, fmt in [('jpg', 'JPEG'), ('png', 'PNG')]}
NAMES = set(COVER_NAMES) | {FULL_NAME, SHORT_NAME, *PART_NAMES}
TEXT_PREFIX = 'B站发布文案/考研学人-70篇/2026-11-15/'
CATALOG_NAME = 'ACTUAL70-ORDERED-BILINGUAL-TITLES.json'


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + '\n').encode('utf-8')


def valid_sha(value, length=64):
    return isinstance(value, str) and bool(re.fullmatch('[0-9a-f]{' + str(length) + '}', value))


def validate_source_item(item, expected_path):
    require(set(item) == {'name', 'bytes', 'sha256', 'sources'}, 'unexpected input metadata fields')
    require(type(item['bytes']) is int and item['bytes'] > 0, 'invalid exact byte count')
    require(valid_sha(item['sha256']), 'invalid full SHA256')
    require(set(item['sources']) == {'primary', 'backup'}, 'both permanent archives required')
    for role, repo in [('primary', PRIMARY), ('backup', BACKUP)]:
        source = item['sources'][role]
        require(set(source) == {'repository', 'commit', 'path'}, 'unexpected source metadata fields')
        require(source['repository'] == repo, 'unexpected source repository')
        require(valid_sha(source['commit'], 40), 'full immutable source commit required')
        require(source['path'] == expected_path, 'unqualified archive path')


def validate_config(c):
    require(c['schema'] == NAMESPACE and c['repository'] == PRIMARY, 'wrong release namespace/repository')
    require(c['tag'] == TAG and c['name'] == TITLE, 'wrong release tag/name')
    require(c['ready'] is True, 'config template is not armed')
    authority = c['authority']
    require(set(authority) == {'approved', 'scope', 'event_sha256', 'reference'}, 'unexpected authority fields')
    require(authority['approved'] is True and authority['scope'] == NAMESPACE,
            'ROOT scoped release authority required')
    require(valid_sha(authority['event_sha256']), 'actual release authority digest required')
    require(isinstance(authority['reference'], str) and authority['reference'].startswith('ROOT-verified-'),
            'ROOT authority reference required; never include raw user messages')
    prefix = c['cover_source_prefix']
    match = re.fullmatch(r'B站封面/考研学人-70篇/\d{4}-\d{2}-\d{2}-4300-v(\d+)/成品/', prefix or '')
    require(match is not None and int(match[1]) >= 6, 'latest V6-or-later qualified cover prefix required; V5 is historical')
    require(len(c['assets']) == 10 and {a['name'] for a in c['assets']} == NAMES,
            'exactly four final covers and six latest TXT files required')
    require(len({a['name'] for a in c['assets']}) == 10, 'duplicate asset')
    for item in c['assets']:
        source_prefix = prefix if item['name'] in COVER_NAMES else TEXT_PREFIX
        validate_source_item(item, source_prefix + item['name'])
    validate_source_item(c['catalog'], TEXT_PREFIX + CATALOG_NAME)


def immutable_url(source):
    return ('https://raw.githubusercontent.com/' + source['repository'] + '/' +
            source['commit'] + '/' + quote(source['path'], safe='/'))


def download(url, max_bytes):
    """Unauthenticated whole HTTP read with a strict size cap; no token forwarding."""
    require(urlparse(url).scheme == 'https', 'HTTPS required')
    with urlopen(Request(url, headers={'User-Agent': NAMESPACE}), timeout=90) as response:
        require(response.status == 200, 'whole HTTP 200 required')
        result = response.read(max_bytes + 1)
        require(len(result) <= max_bytes, 'remote stream exceeds exact size')
        return result


def check_bytes(data, item):
    require(len(data) == item['bytes'] and sha(data) == item['sha256'], 'exact bytes/SHA256 mismatch')


def fetch_dual(item, fetch=download):
    first = None
    records = []
    for role in ['primary', 'backup']:
        source = item['sources'][role]
        data = fetch(immutable_url(source), item['bytes'])
        check_bytes(data, item)
        require(first is None or data == first, 'dual archives differ')
        first = data
        records.append({'role': role, **source, 'bytes': len(data), 'sha256': sha(data),
                        'http_status': 200, 'entire_stream_verified': True})
    return first, records


def image_header(data):
    if data[:8] == b'\x89PNG\r\n\x1a\n':
        require(len(data) >= 33 and data[12:16] == b'IHDR' and data[8:12] == b'\0\0\0\r', 'invalid PNG IHDR')
        width, height = struct.unpack('>II', data[16:24])
        return width, height, 'PNG'
    require(data[:2] == b'\xff\xd8', 'not a qualified PNG/JPEG')
    pos = 2
    while pos < len(data):
        require(data[pos] == 255, 'invalid JPEG marker')
        while pos < len(data) and data[pos] == 255:
            pos += 1
        require(pos < len(data), 'truncated JPEG marker')
        marker = data[pos]
        pos += 1
        if marker in {0xD8, 0x01, *range(0xD0, 0xD8)}:
            continue
        require(marker not in {0xD9, 0xDA} and pos + 2 <= len(data), 'missing JPEG SOF')
        length = int.from_bytes(data[pos:pos + 2], 'big')
        require(length >= 2 and pos + length <= len(data), 'invalid JPEG segment')
        if marker in {0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF}:
            require(length >= 8, 'truncated JPEG SOF')
            height, width = struct.unpack('>HH', data[pos + 3:pos + 7])
            return width, height, 'JPEG'
        pos += length
    raise ValueError('missing JPEG dimensions')


def directory_rows(text):
    return [line for line in text.splitlines() if re.match(r'^\d{2}\s', line)]


def validate_titles(files, catalog_data):
    titles = json.loads(catalog_data.decode('utf-8'))['titles']
    require(len(titles) == 70 and [t['order'] for t in titles] == [f'{n:02}' for n in range(1, 71)],
            'catalog must contain ordered 01..70')
    require(len({t['source_id'] for t in titles}) == 70, 'catalog source IDs must be unique')
    full = directory_rows(files[FULL_NAME].decode('utf-8'))
    short = directory_rows(files[SHORT_NAME].decode('utf-8'))
    parts = sum([directory_rows(files[name].decode('utf-8')) for name in PART_NAMES], [])
    require(len(full) == 70 and len(short) == 70 and parts == full, 'full/short/parts directory coverage mismatch')
    for title, row, short_row in zip(titles, full, short):
        match = re.fullmatch(r'(\d{2}) (\S+) (.+)｜(.+)', row)
        require(match is not None, 'invalid bilingual row')
        order, emoji, zh, en = match.groups()
        require(any(ord(ch) > 0x2600 and not ('\u4e00' <= ch <= '\u9fff') for ch in emoji), 'missing emoji marker')
        require((order, zh, en) == (title['order'], title['title_zh'], title['title_en']), 'changed title/order')
        require(short_row == f'{order} {emoji} {zh}', 'short directory title/emoji changed')
    return {'all70_ordered_bilingual_titles_exact': True, 'all70_short_titles_exact': True,
            'four_parts_equal_full_directory': True, 'catalog_sha256': sha(catalog_data)}


def verify_zip(data, expected):
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        names = archive.namelist()
        require(len(names) == len(set(names)) and set(names) == set(expected), 'ZIP names differ/duplicate entries')
        require(archive.testzip() is None, 'ZIP CRC failed')
        for info in archive.infolist():
            require(PurePosixPath(info.filename).name == info.filename and not info.is_dir(), 'unsafe ZIP member')
            require(archive.read(info.filename) == expected[info.filename], 'ZIP member exact SHA/bytes mismatch')
    return True


def build_package(c, originals, catalog_data):
    require(set(originals) == NAMES, 'unexpected input files')
    for item in c['assets']:
        check_bytes(originals[item['name']], item)
    dimensions = {}
    for name, expected in COVER_NAMES.items():
        actual = image_header(originals[name])
        require(actual == expected, 'wrong cover dimensions/format')
        dimensions[name] = {'width': actual[0], 'height': actual[1], 'format': actual[2]}
    validation = validate_titles(originals, catalog_data)
    manifest = {'schema': NAMESPACE, 'repository': PRIMARY, 'tag': TAG, 'name': TITLE,
                'content': 'four final cover originals and six latest emoji description TXT files',
                'assets': [{**a, **dimensions.get(a['name'], {})} for a in sorted(c['assets'], key=lambda a: a['name'])],
                'catalog_verification_source': c['catalog'], 'validation': validation,
                'original_bytes_preserved': True, 'scope_includes_videos': False}
    files = dict(originals)
    files[MANIFEST_NAME] = json_bytes(manifest)
    files[SUMS_NAME] = ''.join(f'{sha(files[name])}  {name}\n' for name in sorted(files)).encode('utf-8')
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w', compression=zipfile.ZIP_STORED) as archive:
        for name, data in sorted(files.items()):
            info = zipfile.ZipInfo(name, (2026, 11, 15, 0, 0, 0))
            info.external_attr = 0o100644 << 16
            info.compress_type = zipfile.ZIP_STORED
            archive.writestr(info, data)
    zip_data = buffer.getvalue()
    verify_zip(zip_data, files)
    return {**files, ZIP_NAME: zip_data}, manifest


class GitHub:
    def request(self, path, body=None, method='GET', missing_ok=False):
        command = ['gh', 'api', '--include', '--method', method, path]
        if body is not None:
            command += ['--input', '-']
        process = subprocess.run(command, input=json.dumps(body) if body is not None else None,
                                 capture_output=True, text=True)
        # gh --include prints a status line before headers; only 404 may mean absent.
        status = re.search(r'^HTTP/\S+ (\d+)', process.stdout, re.M)
        if missing_ok and status and status[1] == '404':
            return None
        require(process.returncode == 0, 'GitHub API failed: ' + process.stderr[-500:])
        require(status is not None and 200 <= int(status[1]) < 300, 'unexpected GitHub HTTP status')
        normalized = process.stdout.replace('\r\n', '\n')
        return json.loads(normalized.split('\n\n', 1)[1])

    def assets(self, release_id):
        result = []
        page = 1
        while True:
            rows = self.request(f'repos/{PRIMARY}/releases/{release_id}/assets?per_page=100&page={page}')
            result.extend(rows)
            if len(rows) < 100:
                return result
            page += 1

    def upload(self, tag, path):
        process = subprocess.run(['gh', 'release', 'upload', tag, str(path), '--repo', PRIMARY],
                                 capture_output=True, text=True)
        require(process.returncode == 0, 'asset upload failed: ' + process.stderr[-500:])


def assert_remote_asset(asset, name, data):
    require(asset['name'] == name and asset['size'] == len(data) and asset['digest'] == 'sha256:' + sha(data)
            and asset['state'] == 'uploaded', 'remote asset name/size/server SHA256 mismatch')


def assert_release(release, marker, commit, body):
    require(release['tag_name'] == TAG and release['name'] == TITLE and release['target_commitish'] == commit,
            'existing release tag/name/target collision')
    require(release['body'] == body and marker in release['body'], 'release marker/content collision')
    require(release.get('prerelease') is False, 'unexpected prerelease')


def publish(c, files, output, config_sha256, commit, github=None, fetch=download):
    gh = github or GitHub()
    require(valid_sha(commit, 40), 'full workflow commit required')
    require(os.environ.get('GITHUB_REPOSITORY') == PRIMARY, 'publishing allowed only in primary Actions repository')
    marker = f'<!-- {NAMESPACE};config-sha256={config_sha256};manifest-sha256={sha(files[MANIFEST_NAME])} -->'
    body = ('四张4300新版封面（1440×1080、1600×900，PNG/JPG）与六份带emoji的最新简介、70篇中英目录文案。'
            '\n附件含原文件、清单、校验和及完整ZIP。图片保持原始已验收字节。'
            '\n本次仅发布封面与文案；不表示70篇视频已全部完成。'
            '\n\n完整包 SHA-256：' + sha(files[ZIP_NAME]) + '\n\n' + marker)
    tag_path = f'repos/{PRIMARY}/git/ref/tags/{quote(TAG, safe="")}'
    tag = gh.request(tag_path, missing_ok=True)
    release = gh.request(f'repos/{PRIMARY}/releases/tags/{quote(TAG, safe="")}', missing_ok=True)
    if tag is not None:
        require(tag['object']['type'] == 'commit' and tag['object']['sha'] == commit, 'tag commit collision')
    if release is not None:
        require(tag is not None or release['draft'] is True, 'public release without matching immutable tag')
        assert_release(release, marker, commit, body)
    else:
        require(tag is None, 'orphan existing tag is not owned by this release')
        release = gh.request(f'repos/{PRIMARY}/releases', {'tag_name': TAG, 'target_commitish': commit,
            'name': TITLE, 'body': body, 'draft': True, 'prerelease': False, 'make_latest': 'false'}, 'POST')
        assert_release(release, marker, commit, body)
        require(release['draft'] is True, 'new release must start as draft')
    rid = release['id']
    existing = gh.assets(rid)
    require(len({a['name'] for a in existing}) == len(existing), 'duplicate remote asset names')
    require({a['name'] for a in existing} <= set(files), 'unexpected existing release assets')
    for asset in existing:
        assert_remote_asset(asset, asset['name'], files[asset['name']])
    uploaded = {a['name'] for a in existing}
    require(release['draft'] or uploaded == set(files), 'public release incomplete: verify-only')
    for name, data in sorted(files.items()):
        if name not in uploaded:
            require(release['draft'], 'never upload to an existing public release')
            path = output / name
            require(path.read_bytes() == data, 'local output changed before upload')
            gh.upload(TAG, path)
    actual_assets = gh.assets(rid)
    require(len(actual_assets) == len(files) and {a['name'] for a in actual_assets} == set(files), 'exact asset set required')
    for asset in actual_assets:
        assert_remote_asset(asset, asset['name'], files[asset['name']])
    if release['draft']:
        gh.request(f'repos/{PRIMARY}/releases/{rid}', {'draft': False, 'make_latest': 'false'}, 'PATCH')
    actual = gh.request(f'repos/{PRIMARY}/releases/tags/{quote(TAG, safe="")}')
    assert_release(actual, marker, commit, body)
    require(actual['draft'] is False, 'release not public')
    tag = gh.request(tag_path)
    require(tag['object']['type'] == 'commit' and tag['object']['sha'] == commit, 'published tag changed')
    verified = []
    for asset in gh.assets(rid):
        name = asset['name']
        require(name in files, 'unexpected public asset')
        assert_remote_asset(asset, name, files[name])
        url = asset['browser_download_url']
        require(url.startswith(f'https://github.com/{PRIMARY}/releases/download/{TAG}/'), 'unexpected public download URL')
        for attempt in range(6):
            try:
                data = fetch(url, len(files[name]))
                require(data == files[name], 'public whole-download differs')
                break
            except (HTTPError, OSError, ValueError):
                if attempt == 5:
                    raise
                time.sleep(min(2 ** attempt, 16))
        if name == ZIP_NAME:
            verify_zip(data, {n: b for n, b in files.items() if n != ZIP_NAME})
        verified.append({'name': name, 'bytes': len(data), 'sha256': sha(data), 'asset_id': asset['id'],
                         'download_url': url, 'server_digest_verified': True, 'public_entire_stream_verified': True})
    require(len(verified) == len(files) and {a['name'] for a in verified} == set(files), 'public assets changed')
    return {'passed': True, 'schema': NAMESPACE, 'repository': PRIMARY, 'tag': TAG,
            'workflow_commit': commit, 'config_sha256': config_sha256, 'release_url': actual['html_url'],
            'assets': sorted(verified, key=lambda a: a['name']), 'asset_count': len(verified),
            'zip_crc_and_internal_bytes_verified': True, 'no_video_or_old_release_modification': True}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--config-sha256', required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--publish', action='store_true')
    args = parser.parse_args()
    config_data = args.config.read_bytes()
    require(valid_sha(args.config_sha256) and sha(config_data) == args.config_sha256, 'config SHA pin mismatch')
    c = json.loads(config_data)
    validate_config(c)
    originals, readbacks = {}, []
    for item in c['assets']:
        data, records = fetch_dual(item)
        originals[item['name']] = data
        readbacks.extend(records)
    catalog, records = fetch_dual(c['catalog'])
    readbacks.extend(records)
    files, manifest = build_package(c, originals, catalog)
    args.output.mkdir(parents=True, exist_ok=False)
    for name, data in files.items():
        (args.output / name).write_bytes(data)
    (args.output / 'INPUT-DUAL-HTTP-READBACK.json').write_bytes(json_bytes({'passed': True, 'streams': readbacks}))
    if args.publish:
        require(os.environ.get('GITHUB_ACTIONS') == 'true' and os.environ.get('GH_TOKEN'), 'native Actions token required')
        report = publish(c, files, args.output, args.config_sha256, os.environ['GITHUB_SHA'])
        report['input_dual_http_streams'] = readbacks
        (args.output / 'PUBLIC-RELEASE-VERIFICATION.json').write_bytes(json_bytes(report))
        print(json.dumps({'passed': True, 'release_url': report['release_url'], 'assets': report['asset_count']}, ensure_ascii=False))
    else:
        print(json.dumps({'prepared': True, 'published': False, 'assets': len(files), 'dual_HTTP_streams': len(readbacks)}))


if __name__ == '__main__':
    main()
