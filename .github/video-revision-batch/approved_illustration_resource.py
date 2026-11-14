#!/usr/bin/env python3
"""Resolve approved book artwork from its pinned public publication commit."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def resolve(source_id, checkout, task):
    checkout, task = Path(checkout), Path(task)
    contract_path = task / 'approved-illustration-source70.json'
    contract = json.loads(contract_path.read_text())
    assert contract['kind'] == 'exact-approved-illustrations-from-pinned-publication'
    assert contract['repository'] == 'alienalgorithm/postgraduate-vocabulary'
    assert contract['count'] == 70 and contract['all_match'] is True
    actual_ref = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=checkout, text=True).strip()
    assert actual_ref == contract['ref'], 'Illustration checkout is not the reviewed immutable publication.'
    manifest_path = task / 'illustration-manifest70.json'
    assert sha(manifest_path) == contract['approved_manifest_sha256']
    manifest = json.loads(manifest_path.read_text())
    approved, = [row for row in manifest['illustrations'] if row['source_id'] == source_id]
    source, = [row for row in contract['files'] if row['source_id'] == source_id]
    # The approved manifest supplies the native filename, including 01-preview.
    relative = Path('插图阅读小册/illustrations') / Path(approved['approved_book_illustration_path']).name
    assert str(relative) == source['path'] and source['sha256'] == approved['sha256']
    image = checkout / relative
    raw = image.read_bytes()
    actual_sha = hashlib.sha256(raw).hexdigest()
    actual_blob = hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()
    assert actual_sha == source['sha256'] and actual_blob == source['git_blob_sha1']
    assert len(raw) == source['bytes'] == approved['bytes']
    receipt = {'kind': contract['kind'], 'source_id': source_id, 'resource_verified': True,
               'repository': contract['repository'], 'ref': actual_ref, 'path': str(relative),
               'sha256': actual_sha, 'git_blob_sha1': actual_blob, 'bytes': len(raw),
               'approved_manifest_sha256': contract['approved_manifest_sha256'],
               'resource_contract_sha256': sha(contract_path)}
    return image, receipt


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source-id', required=True)
    parser.add_argument('--checkout', type=Path, required=True)
    parser.add_argument('--task', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    _, receipt = resolve(args.source_id, args.checkout, args.task)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(receipt, ensure_ascii=False))


if __name__ == '__main__':
    main()
