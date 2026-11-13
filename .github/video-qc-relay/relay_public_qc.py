"""Native-GitHub-runner draft; public QC only, never a quality-gate bypass."""
import base64
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import urllib.error
import urllib.request
import zipfile


PUBLIC_JSON = re.compile(r'^(\d{2})-(?:status|failed-working-source|user-authorization|source|summary-verification|canonical-fingerprint|approved-audio-qc|failed-draft-proof|failed-draft-fingerprint|reference-gain-diagnostic|checker-reference-preparation)\.json$')
PUBLIC_MEDIA = re.compile(r'^\d{2}-failed-draft\.mp4$|^\d{2}-failed-draft-(?:opening-ok|oll-wright|ending|title|s5-highlight|norway-finland|last-sentence)\.wav$')


def allowed_member(name, status_only=False):
    """Keep default draft retrieval; status-only never exports audio/video bytes."""
    return bool(PUBLIC_JSON.fullmatch(name) or
                (not status_only and PUBLIC_MEDIA.fullmatch(name)))


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def main(request_path):
    request = json.loads(Path(request_path).read_text())
    status_only = request.get('status_only', False)
    assert isinstance(status_only, bool)
    repo = request['repository']
    assert repo == os.environ['GITHUB_REPOSITORY'] == 'AlienCodes/literate-enigma'
    branch = request['debug_branch']
    assert re.fullmatch(r'codex/public-ci-qc-\d+', branch)
    assert branch not in {'main', 'master', 'codex/all-deliverables-20261113'}
    prefix = request['prefix']
    assert re.fullmatch(r'public-ci-qc/\d+', prefix)
    token = os.environ['GH_TOKEN']
    def api(path, data=None, method='GET'):
        payload = None if data is None else json.dumps(data).encode()
        req = urllib.request.Request('https://api.github.com/repos/' + repo + '/' + path,
            data=payload, method=method,
            headers={'Authorization': 'Bearer ' + token,
                     'Accept': 'application/vnd.github+json', 'User-Agent': 'public-qc-relay'})
        with urllib.request.urlopen(req) as response:
            return json.load(response)

    run = api('actions/runs/' + str(request['run_id']))
    assert run['head_sha'] == request['source_commit']
    assert run['head_branch'] == 'codex/finish-05-and-summaries-20261112'
    master_before = api('git/ref/heads/master')['object']['sha']
    listed = api('actions/runs/' + str(request['run_id']) + '/artifacts?per_page=100')['artifacts']
    jobs = api('actions/runs/' + str(request['run_id']) + '/jobs?per_page=100')['jobs'] if status_only else []
    updates = []
    observations = []
    for name in request['artifacts']:
        assert re.fullmatch(r'article\d{2}-revised-canonical-4K-final', name)
        found = next((item for item in listed if item['name'] == name and not item['expired']), None)
        if not found:
            observations.append({'name': name, 'available': False})
            continue
        # Resolve authenticated GitHub's redirect separately so no GitHub token
        # can be forwarded to the signed storage URL.
        req = urllib.request.Request('https://api.github.com/repos/' + repo + '/actions/artifacts/' + str(found['id']) + '/zip',
            headers={'Authorization': 'Bearer ' + token, 'User-Agent': 'public-qc-relay'})
        try:
            urllib.request.build_opener(NoRedirect).open(req)
            raise AssertionError('Expected an authenticated signed download redirect')
        except urllib.error.HTTPError as error:
            assert error.code == 302
            location = error.headers['Location']
        with urllib.request.urlopen(urllib.request.Request(location, headers={'User-Agent': 'public-qc-relay'})) as response:
            raw = response.read(64 * 1024 * 1024 + 1)
        assert len(raw) <= 64 * 1024 * 1024
        digest = 'sha256:' + hashlib.sha256(raw).hexdigest()
        if status_only:
            assert found.get('digest'), 'Status-only observation requires an artifact ZIP digest'
        if found.get('digest'):
            assert digest == found['digest'], 'Artifact ZIP digest mismatch'
        files = []
        omitted_media = []
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:
            for member in archive.infolist():
                path = PurePosixPath(member.filename)
                assert not path.is_absolute() and '..' not in path.parts
                if status_only and not member.is_dir() and path.name[:2] == name[7:9] and re.fullmatch(r'\d{2}-(?:4K-[^/\r\n]+|failed-draft(?:-[^/\r\n]+)?)\.(?:mp4|wav)', path.name):
                    omitted_media.append({'name': path.name, 'bytes': member.file_size})
                if member.is_dir() or not allowed_member(path.name, status_only):
                    continue
                assert path.name[:2] == name[7:9]
                assert member.file_size <= 40 * 1024 * 1024
                data = archive.read(member)
                if path.suffix == '.json':
                    json.loads(data)
                blob = api('git/blobs', {'content': base64.b64encode(data).decode(), 'encoding': 'base64'}, 'POST')
                destination = prefix + '/' + path.name
                assert not any(item['path'] == destination for item in updates), 'Duplicate destination'
                updates.append({'path': destination, 'mode': '100644', 'type': 'blob', 'sha': blob['sha']})
                files.append({'path': destination, 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()})
        observations.append({'name': name, 'available': True, 'artifact_id': found['id'],
                             'zip_sha256': digest, 'zip_digest_verified': bool(found.get('digest')),
                             'omitted_public_media_metadata': omitted_media,
                             'files': files})
    manifest = {'kind': 'public-observation-only-not-quality-acceptance',
                'run_id': request['run_id'], 'source_commit': run['head_sha'],
                'run_status_at_observation': run['status'], 'artifacts': observations,
                'status_only': status_only,
                'media_content_exported': not status_only,
                'workflow_jobs_at_observation': [
                    {k: job.get(k) for k in ('id', 'name', 'status', 'conclusion', 'started_at', 'completed_at', 'html_url')}
                    for job in jobs if re.fullmatch(r'produce \(\d{2}\)', job['name'])],
                'private_cache_GT_model_exports': False}
    data = (json.dumps(manifest, ensure_ascii=False, indent=2) + '\n').encode()
    blob = api('git/blobs', {'content': base64.b64encode(data).decode(), 'encoding': 'base64'}, 'POST')
    updates.append({'path': prefix + '/manifest.json', 'mode': '100644', 'type': 'blob', 'sha': blob['sha']})
    try:
        parent = api('git/ref/heads/' + branch)['object']['sha']
        exists = True
    except urllib.error.HTTPError as error:
        assert error.code == 404
        parent = request['source_commit']
        exists = False
    base = api('git/commits/' + parent)['tree']['sha']
    tree = api('git/trees', {'base_tree': base, 'tree': updates}, 'POST')['sha']
    commit = api('git/commits', {'tree': tree, 'parents': [parent],
                               'message': 'Preserve public failed-candidate QC observations [skip ci]'}, 'POST')['sha']
    if exists:
        api('git/refs/heads/' + branch, {'sha': commit, 'force': False}, 'PATCH')
    else:
        api('git/refs', {'ref': 'refs/heads/' + branch, 'sha': commit}, 'POST')
    assert api('git/ref/heads/master')['object']['sha'] == master_before
    print(json.dumps({'branch': branch, 'commit': commit, 'files': len(updates), 'acceptance': False}))


if __name__ == '__main__':
    import argparse
    import sys
    parser = argparse.ArgumentParser()
    parser.add_argument('request_path')
    parser.add_argument('--status-only', action='store_true')
    args = parser.parse_args()
    if args.status_only:
        request = json.loads(Path(args.request_path).read_text())
        assert request.get('status_only') is True, 'CLI flag must match the reviewable request'
    main(args.request_path)
