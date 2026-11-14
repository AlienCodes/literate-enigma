"""Publish one actually validated, permanently archived article without altering media."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import urllib.parse
import urllib.request

HERE = Path(__file__).resolve().parent
REPO = 'alienalgorithm/postgraduate-vocabulary'


def api(path, method='GET', data=None, missing_ok=False):
    command = ['gh', 'api', 'repos/' + REPO + '/' + path]
    if method != 'GET':
        command += ['-X', method]
    if data is not None:
        command += ['--input', '-']
    result = subprocess.run(command, input=None if data is None else json.dumps(data).encode(), capture_output=True)
    if missing_ok and result.returncode and b'(HTTP 404)' in result.stderr:
        return None
    if result.returncode:
        raise RuntimeError(result.stderr.decode(errors='replace'))
    return json.loads(result.stdout)


def sha(path):
    with Path(path).open('rb') as source:
        return hashlib.file_digest(source, 'sha256').hexdigest()


def main():
    if os.environ.get('GITHUB_REPOSITORY') != REPO:
        print('Backup preserves publication sources; primary repository publishes the Release.')
        return
    config = json.loads((HERE / 'MANIFEST.json').read_text())
    assert config['source_id'] == '15' and config['book_order'] == '25'
    assert config['actual_complete_validation_passed'] is True
    assert config['actual_dual_permanent_archive_passed'] is True
    assert set(config['reviewed_terms']) == {'inquiries', 'patrol'}
    spec = config['video']
    assert spec['release_name'] == '25-The-Myth-of-the-Unsinkable-4K.mp4'
    assert spec['width'] == 3840 and spec['height'] == 2160
    out = Path(os.environ['GITHUB_WORKSPACE']) / 'single-release-output'
    out.mkdir(exist_ok=True)
    path = out / spec['release_name']
    raw_url = 'https://raw.githubusercontent.com/' + REPO + '/' + spec['archived_commit'] + '/' + urllib.parse.quote(spec['repo_path'], safe='/')
    with urllib.request.urlopen(raw_url, timeout=180) as source, path.open('wb') as target:
        while chunk := source.read(1024 * 1024):
            target.write(chunk)
    assert path.stat().st_size == spec['bytes'] and sha(path) == spec['sha256']
    # Exact archived/video/public SHA checks preserve the already fully validated 4K file.
    video = config['validated_video_probe']
    assert (video['width'], video['height']) == (3840, 2160)
    assert video['width'] == spec['width'] and video['height'] == spec['height']
    assert len(config['validation_record_sha256']) == 64
    tag = config['tag']
    marker = 'Article15 reviewed final video SHA-256: ' + spec['sha256']
    release = api('releases/tags/' + tag, missing_ok=True)
    if release is None:
        matches = [item for item in api('releases?per_page=100') if item['tag_name'] == tag and marker in (item.get('body') or '')]
        assert len(matches) <= 1
        release = matches[0] if matches else None
    if release is None:
        release = api('releases', 'POST', {
            'tag_name': tag,
            'target_commitish': spec['archived_commit'],
            'name': config['title'],
            'body': config['body'] + '\n\n<!-- ' + marker + ' -->',
            'draft': True,
            'prerelease': False,
        })
    assert release['tag_name'] == tag and marker in (release.get('body') or '')
    assets = api('releases/' + str(release['id']) + '/assets?per_page=100')
    assert len(assets) <= 1 and all(asset['name'] == spec['release_name'] for asset in assets)
    if not assets:
        subprocess.run(['gh', 'release', 'upload', tag, str(path), '--repo', REPO], check=True)
    assets = api('releases/' + str(release['id']) + '/assets?per_page=100')
    assert len(assets) == 1
    asset = assets[0]
    assert asset['name'] == spec['release_name'] and asset['state'] == 'uploaded'
    assert asset['size'] == spec['bytes'] and asset['digest'] == 'sha256:' + spec['sha256']
    if release['draft']:
        api('releases/' + str(release['id']), 'PATCH', {'draft': False, 'prerelease': False, 'make_latest': 'false'})
    release = api('releases/' + str(release['id']))
    assert not release['draft']
    tag_object = api('git/ref/tags/' + tag)['object']
    assert tag_object['type'] == 'commit' and tag_object['sha'] == spec['archived_commit']
    asset = api('releases/' + str(release['id']) + '/assets?per_page=100')[0]
    downloaded = hashlib.sha256()
    downloaded_bytes = 0
    with urllib.request.urlopen(asset['browser_download_url'], timeout=180) as source:
        while chunk := source.read(1024 * 1024):
            downloaded.update(chunk)
            downloaded_bytes += len(chunk)
    assert downloaded_bytes == spec['bytes'] and downloaded.hexdigest() == spec['sha256']
    receipt = {
        'passed': True,
        'source_id': '15',
        'book_order': '25',
        'release_id': release['id'],
        'release_url': release['html_url'],
        'video_url': asset['browser_download_url'],
        'video_bytes': downloaded_bytes,
        'video_sha256': downloaded.hexdigest(),
        'actual_public_entire_video_download_verified': True,
        'validated_video_probe_reference': video,
        'validation_record_sha256': config['validation_record_sha256'],
        'manifest_sha256': sha(HERE / 'MANIFEST.json'),
        'publisher_sha256': sha(__file__),
        'native_actions_run_id': int(os.environ['GITHUB_RUN_ID']),
        'native_actions_head_sha': os.environ['GITHUB_SHA'],
        'other_release_or_tag_deleted': False,
        'recorded_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }
    (out / 'RELEASE-VERIFICATION.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(receipt, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
