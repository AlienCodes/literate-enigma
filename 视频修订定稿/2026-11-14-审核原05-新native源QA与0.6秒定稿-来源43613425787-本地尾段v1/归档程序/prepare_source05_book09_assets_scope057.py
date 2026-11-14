"""Own source05/book09 archive inventory adaptation; no source, media, or QA mutation."""
from pathlib import Path
import hashlib
import json
import os
import shutil
import subprocess
import sys

B = Path('/workspace/work/video-archive-batches-20261114')
W = B / 'user057-book09-source05-newsourceQA-normal18-assets'
RAM = Path('/dev/shm/user057-book09-source05-newsourceQA-normal18-assets-payload')
H = Path('/dev/shm/first34-hold06-intake/validated/book09-source05/archive-handoff.json')
H_SHA = '3051d13df5c46129f6f5a700f9af503a8f837e4d067c01d93c4d98f1d27f27aa'
AUTH = Path('/workspace/work/first50-review-release/USER-REVIEW-2026-11-14-057.json')
AUTH_SHA = '3c91671ad6dcc1e30f6336efa394eac1ff776c8405157b924f2e86f64266284a'
REFUSED = {
    'b9a257a23820944ee95d568b67d1cd78947b1c1814bb70dc99a45871f488f778',
    '55026ce1b7cdb7e9c1a72da2f715e3d9e6e6f45050a8ddd575dc052b09dca872',
    'bcb37d8930d804988c95da94b9cfeaaab2c7b026df96e6e4567f9b698ce88fbf',
}
SAFE = {'.json', '.py', '.sh', '.md', '.txt', '.log', '.csv', '.diff', '.patch', '.yml', '.yaml', '.png', '.jpg', '.mp4', '.zip'}

def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()

def load(path):
    return json.loads(Path(path).read_text())

def write(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')

def checked(spec):
    path = Path(spec['path'])
    assert path.suffix.lower() in SAFE
    assert '__pycache__' not in path.parts
    assert not path.name.startswith('CURRENT-ROOT-DELIVERY-STATE')
    assert path.stat().st_size == spec['bytes'] and sha(path) == spec['sha256']
    assert spec['sha256'] not in REFUSED
    return path

def physical(path):
    path = Path(path)
    return {'path': str(path), 'bytes': path.stat().st_size, 'sha256': sha(path)}

assert W.parent == B and W.name == 'user057-book09-source05-newsourceQA-normal18-assets'
assert (W / 'payload').is_symlink() and (W / 'payload').resolve() == RAM
assert not (W / 'prepared-archive.json').exists()
assert sha(H) == H_SHA and sha(AUTH) == AUTH_SHA
h = load(H)
source_spec = h['current_source_validation_handoff']
source = load(checked(source_spec))
assert h['source_run'] == source['source_run'] == 43613425787
assert h['articles'][0]['source_id'] == source['articles'][0]['source_id'] == '05'
assert h['articles'][0]['new_id'] == '09'

# These are archivist declarations derived exclusively from frozen handoff lists.
# They are never represented as a producer-created manifest or a new QA result.
unique = {}
for label, section in [('current-source-handoff', source['articles'][0]['section']), ('new-normal18-handoff', h['articles'][0]['section'])]:
    for number, spec in enumerate(section.get('evidence', [])):
        path = checked(spec)
        assert path.suffix.lower() in {'.json', '.md', '.py'}
        key = (spec['bytes'], spec['sha256'])
        entry = unique.setdefault(key, {**spec, 'declarations': []})
        entry['declarations'].append({'handoff': label, 'section_evidence_index': number, 'declared_path': str(path)})
illustration = h['articles'][0]['section']['illustration']
for label, spec in [('current-illustration', illustration), ('current-illustration-native-source', illustration['native_source'])]:
    path = checked(spec)
    key = (spec['bytes'], spec['sha256'])
    entry = unique.setdefault(key, {'path': str(path), 'bytes': spec['bytes'], 'sha256': spec['sha256'], 'declarations': []})
    entry['declarations'].append({'handoff': 'new-normal18-handoff', 'field': label, 'declared_path': str(path)})
files = []
for number, entry in enumerate(unique.values(), 1):
    files.append({**entry, 'archive_relative_path': f'{number:03d}-{Path(entry["path"]).name}'})
manifest = W / 'safe-public-evidence-manifest.json'
write(manifest, {
    'kind': 'archivist-derived-physical-public-evidence-declarations-from-frozen-handoffs',
    'producer_manifest_claimed': False,
    'derived_from_frozen_normal18_handoff': physical(H),
    'derived_from_frozen_current_source_handoff': source_spec,
    'deduplication': 'actual bytes and SHA256; all frozen declaration locations retained',
    'private_wav_GT_cache_PDF_or_live_ROOT_payloads_collected': False,
    'files': files,
})

# Audit exactly the generic collector's physical inputs before invoking it.
inputs = list(source['validation_files']) + list(h['validation_files']) + list(h['global_approved_evidence'].values()) + list(h.get('additional_public_media_inputs', [])) + files
inputs += [source_spec, physical(H), physical(h['report_path']), physical(h['input_path']), physical(AUTH)]
inputs += [physical(Path(h['code_snapshot_path']) / name) for name in h['tool_source_sha256']]
article = h['articles'][0]
inputs += article['section'].get('stills', []) + [article['final_mp4'], article['canonical_source_mp4'], article['immutable_native_zip']]
for spec in inputs:
    checked(spec)
env = {**os.environ, 'PYTHONDONTWRITEBYTECODE': '1', 'TMPDIR': str(RAM / 'own-transport-tmp')}
subprocess.run([
    sys.executable, str(B / 'prepare_new_sourceQA_normal18_assets.py'),
    '--handoff', str(H), '--expected-handoff-sha256', H_SHA,
    '--work-dir', str(W), '--explicit-public-manifest', str(manifest),
    '--explicit-public-manifest-sha256', sha(manifest),
], check=True, env=env)

meta = load(W / 'prepared-archive.json')
record = load(article['validated_record'])
assert record['sha256'] == article['final_mp4']['sha256']
row = meta['articles'][0]
row['current_uniform_timing_authorized_by_user057'] = True
row['actual_end_reading_pause_seconds'] = record['tail']['voice_to_illustration_gap_seconds']
prefix = Path(meta['prefix'])
for original, relative in [(AUTH, prefix / '用户057统一0.6秒实际授权.json'), (Path(__file__), prefix / '归档程序' / Path(__file__).name)]:
    spec = physical(original)
    checked(spec)
    target = W / 'payload' / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(original, target)
    meta['material_source_bindings'].append({'original_path': str(original), 'repo_path': str(relative), 'bytes': spec['bytes'], 'sha256': spec['sha256']})
write(W / 'prepared-archive.json', meta)
write(W / 'payload' / prefix / 'archive-manifest.json', meta)
index = []
for path in sorted((W / 'payload').rglob('*')):
    if path.is_file():
        assert path.suffix.lower() in SAFE and sha(path) not in REFUSED
        index.append({'repo_path': str(path.relative_to(W / 'payload')), 'bytes': path.stat().st_size, 'sha256': sha(path)})
write(W / 'payload-file-index.json', index)
assert sha(H) == H_SHA
print(json.dumps({'work_dir': str(W), 'files': len(index), 'logical_bytes': sum(item['bytes'] for item in index), 'frozen_handoff_sha256': sha(H), 'explicit_public_manifest_sha256': sha(manifest), 'adaptation_code_sha256': sha(__file__), 'actual_end_reading_pause_seconds': row['actual_end_reading_pause_seconds']}, ensure_ascii=False))
