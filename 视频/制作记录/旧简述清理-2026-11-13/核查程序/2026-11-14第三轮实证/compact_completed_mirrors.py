"""Losslessly compact only completed temporary source mirrors; retain every original byte."""
import argparse
import hashlib
import json
import os
import shutil
import stat
import subprocess
import zipfile
from pathlib import Path

B = Path(__file__).resolve().parent
NAMES = ['preflight-final12-readonly', 'preflight-final70-part4',
         'actual-audio-confirmation-preflight', 'actual-audio-confirmation-preflight-v2',
         'audio51-confirmation-renewal-preflight', 'existing-ASR-renewal-preflight',
         'existing-ASR-renewal51-clarity-preflight', '44-raw-clock-text-preflight',
         'A21-specific-repair-text-preflight', 'lavish42-exact',
         'preflight-frozen66-v2-part2', 'preflight-frozen66-v2-part3']
parser = argparse.ArgumentParser()
parser.add_argument('--apply-cleanup', action='store_true')
args = parser.parse_args()
out = B / 'temporary-mirror-snapshots'
out.mkdir(exist_ok=True)
archive = out / 'completed-source-mirrors-original-bytes.zip'
assert not archive.exists(), 'Immutable compaction archive already exists; do not overwrite.'
roots = [B / name / 'mirror' for name in NAMES if (B / name / 'mirror').exists()]
records, seen, source_bytes = [], set(), 0
public_resources = {}
with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as z:
    for root in roots:
        assert not root.is_symlink() and root.resolve().is_relative_to(B)
        for path in sorted(root.rglob('*')):
            rel = str(path.relative_to(B))
            info = path.lstat()
            if path.is_symlink():
                records.append({'path': rel, 'type': 'symlink', 'target': os.readlink(path)})
            elif path.is_dir():
                records.append({'path': rel, 'type': 'directory', 'mode': stat.S_IMODE(info.st_mode)})
            else:
                assert '.git' not in path.relative_to(root).parts
                raw = path.read_bytes()
                if path.suffix.lower() in {'.pkl', '.wav', '.npy', '.npz', '.safetensors', '.pt', '.mp4'}:
                    public_path = str(path.relative_to(root))
                    if public_path not in public_resources:
                        public_resources[public_path] = subprocess.check_output(['git','show','64621068034f8b6e09836a6d97210a0e9b2f1ed6:'+public_path], cwd='/workspace/work/github-publication/target')
                    assert raw == public_resources[public_path], path
                sha = hashlib.sha256(raw).hexdigest()
                source_bytes += len(raw)
                records.append({'path': rel, 'type': 'file', 'mode': stat.S_IMODE(info.st_mode),
                                'bytes': len(raw), 'sha256': sha})
                if sha not in seen:
                    z.writestr('blobs/' + sha, raw)
                    seen.add(sha)
    inventory = {'scope': 'Only completed temporary source mirrors; active original-tool part1 mirror, all media and QC records remain in place',
                 'roots': [str(x.relative_to(B)) for x in roots], 'records': records,
                 'source_bytes': source_bytes, 'unique_content_blobs': len(seen),
                 'private_audio_or_model_arrays': False}
    inventory['existing_public_test_audio_and_voice_resources'] = {'git_ref':'64621068034f8b6e09836a6d97210a0e9b2f1ed6', 'sha256':{name:hashlib.sha256(raw).hexdigest()for name,raw in public_resources.items()}, 'new_private_synthesis_array':False}
    z.writestr('inventory.json', json.dumps(inventory, ensure_ascii=False, indent=2).encode())

with zipfile.ZipFile(archive) as z:
    assert json.loads(z.read('inventory.json')) == inventory
    for sha in seen:
        assert hashlib.sha256(z.read('blobs/' + sha)).hexdigest() == sha
for row in records:
    path = B / row['path']
    if row['type'] == 'file':
        assert path.stat().st_size == row['bytes'] and hashlib.sha256(path.read_bytes()).hexdigest() == row['sha256']
    elif row['type'] == 'symlink':
        assert os.readlink(path) == row['target']
if args.apply_cleanup:
    for root in roots:
        assert root == B / root.parent.name / 'mirror'
        shutil.rmtree(root)
receipt = {'status': 'lossless_completed_temporary_mirrors_compacted', 'original_bytes_preserved': True,
           'archive': str(archive), 'archive_bytes': archive.stat().st_size,
           'archive_sha256': hashlib.sha256(archive.read_bytes()).hexdigest(),
           'input_file_bytes': source_bytes, 'content_blobs': len(seen), 'record_count': len(records),
           'removed_only_completed_temporary_mirrors': args.apply_cleanup,
           'mirror_roots': inventory['roots'], 'active_original_tools_and_media_and_QC_unchanged': True,
           'restoration': 'Read inventory.json; restore file bytes from blobs/<sha256>, directory modes and symbolic link targets under the chosen workspace root.'}
(out / 'compaction-receipt.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n')
print(json.dumps(receipt, ensure_ascii=False))
