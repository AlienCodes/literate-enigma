"""Collect the actually passed existing-source normal18 tail, without inventing a new native run."""
from pathlib import Path
import hashlib, json, os, shutil, subprocess, sys, tempfile

B = Path(__file__).resolve().parent
C = Path('/dev/shm/archive-writer-main061')
K = B
H = Path('/workspace/work/review45-finalV3/43533004625-normal18-book70-20261115/archive-handoff.json')
HS = '9755327747b30b8e83878836f26f4cf682ebadb851b0fd0c66e72d7e01b0564c'
USER = Path('/workspace/work/book70-source45-final-baseline-preparation-20261115/USER-BOOK70-SOURCE45-ACTUAL-FINALIZATION-20261115.json')
CONSENT = Path('/workspace/work/all-project-deliverables-and-final70-release-authorities-20261115/USER-ALL-PROJECT-GENERATED-DELIVERABLES-GITHUB-ARCHIVE-AUTHORITY.json')

def spec(p):
    p = Path(p); raw = p.read_bytes()
    return {'path': str(p), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}

assert spec(H)['sha256'] == HS and H.stat().st_size == 41409
assert spec(USER)['sha256'] == '591135ed41aa8fa6fea7b97c838214571d7be7342ef59255fca6a3fe1dbe7f8a'
assert spec(CONSENT)['sha256'] == 'b00a133cc88ed37496e225a181898863ce52e9a774e6b5c2991a310691fd4312'
state = json.loads((C / 'CURRENT-ARCHIVE-STATE.json').read_bytes())
prior = json.loads(Path(state['actual_inventory']).read_bytes())
old = next(x for x in prior['articles'] if x['source_id'] == '45')
assert old['asset_commit'] == '24d017c559d8091af47a0decbe9fdde761a260c4'
ORIGINAL = B / 'run43533004625-45'
assert json.loads((ORIGINAL / 'assets-primary.json').read_bytes())['asset_commit'] == old['asset_commit']
R = Path(tempfile.mkdtemp(prefix='book70-source45-existing-normal18-host-assets-', dir=str(B)))
W = R / 'run43533004625-45-book70-existing-normal18-v1'
W.mkdir()
BASE = R / 'actual-existing-source45-archive-base'
BASE.mkdir()
for name in ['prepared-archive.json', 'assets-primary.json', 'assets-backup.json', 'payload-file-index.json']:
    shutil.copyfile(ORIGINAL / name, BASE / name)
(BASE / 'payload').symlink_to(ORIGINAL / 'payload', target_is_directory=True)
for name in ['prepare_normal_hold18_postonly_assets.py', 'archive_batch.py',
             'verify_dual_media_asset_blobs.py', 'emit_ready_revision_download_manifest.py',
             'cleanup_closed_media_asset_bare.py']:
    shutil.copyfile(B / name, R / name)
for name in ['exact_existing_tail_authorities.py', 'existing_final_tail_handoff_compat.py']:
    shutil.copyfile(K / name, R / name)

rows = []
def add(p, relative):
    rows.append({**spec(p), 'archive_relative_path': relative})

add(USER, 'actual-book70-unchanged-source-finalization-authority.json')
add(CONSENT, 'actual-new-all-project-generated-deliverables-publication-authority.json')
P = Path('/workspace/work/book70-source45-original-normal18-data-only-caller-preparation-20261115')
for name in ['ACTUAL-ROOT-ADOPTED-BOOK70-UPSTREAM-EXECUTION.json',
             'ACTUAL-ROOT-ADOPTED-BOOK70-COMPOSE-EXECUTION.json',
             'ACTUAL-ROOT-ADOPTED-BOOK70-FINALV3-EXECUTION.json',
             'ACTUAL-COMPOSE-PREPHASE-ADDITIONAL-PEAK-BUDGET.json',
             'ACTUAL-FINALV3-PREPHASE-ADDITIONAL-PEAK-BUDGET.json',
             'execute_exact_serial_book70_phase.py',
             'BOOK70-SOURCE45-ORIGINAL-SEVEN-PROGRAM-NORMAL18-DATA-ONLY-CALLER-HANDOFF.json',
             'COORDINATOR-ACTUAL-INDEPENDENT-70-PURE-DATA-REVIEW.json']:
    add(P / name, 'actual-source-and-original-normal18-execution/' + name)
for p in [P/'COORDINATOR-EXACT-70-PHASE-INPUTS-UNDER-EXISTING-ROOT-WINDOW.json', P/'ACTUAL-OUTER-FINALV3-COMMAND-KEY-IO-CORRECTION-NO-MEDIA-OR-GATE-CHANGE.json']:
    add(p, 'actual-root-source-and-frame-review/' + p.name)
for name in ['exact_existing_tail_authorities.py', 'existing_final_tail_handoff_compat.py']:
    add(K / name, 'exact-original-role-readers/' + name)
manifest = R / 'EXACT-BOOK70-EXISTING-SOURCE-PUBLIC-EVIDENCE.json'
manifest.write_text(json.dumps({'kind': 'exact-existing-source45-book70-normal18-final-and-actual-global-project-publication-authority',
    'source_id': '45', 'book_order': '70', 'files': rows,
    'new_native_run_or_TTS_or_source_change_claimed': False,
    'original_H_and_raw_authorities_unchanged': True,
    'all_materials_are_explicit_prior_dual_public_archive_or_declared_real_H_inputs': True,
    'private_RAW_GT_models_cache_embeddings_ROOTSTATE_PDF_not_included': True}, ensure_ascii=False, indent=2) + '\n')
command = [sys.executable, R / 'prepare_normal_hold18_postonly_assets.py',
    '--handoff', H, '--expected-handoff-sha256', HS, '--base-work-dir', BASE,
    '--work-dir', W, '--explicit-public-manifest', manifest,
    '--explicit-public-manifest-sha256', spec(manifest)['sha256']]
env = {**os.environ, 'PYTHONPATH': str(R) + ':' + str(B), 'PYTHONDONTWRITEBYTECODE': '1', 'TMPDIR': str(R)}
result = subprocess.run(list(map(str, command)), capture_output=True, text=True, env=env)
(R / 'ACTUAL-BOOK70-LOCAL-PREPARE.log').write_text(result.stdout + result.stderr)
assert result.returncode == 0, (result.stdout + result.stderr)[-3000:]
meta = json.loads((W / 'prepared-archive.json').read_bytes())
row = meta['articles'][0]
assert row['source_id'] == '45' and row['new_id'] == '70'
assert row['inherited_full_native_archive_commit'] == old['asset_commit']
assert row['sha256'] == 'c72753547d18ca0f9e9041ef41de9502d25d31e39295a2488c2886cec6bccef8'
assert row['new_native_Actions_run_claimed'] is False
shutil.copyfile(__file__, W / 'payload' / meta['prefix'] / '归档程序' / Path(__file__).name)
index = [{'repo_path': str(p.relative_to(W / 'payload')), 'bytes': p.stat().st_size,
          'sha256': spec(p)['sha256']} for p in sorted((W / 'payload').rglob('*')) if p.is_file()]
(W / 'payload-file-index.json').write_text(json.dumps(index, ensure_ascii=False, indent=2) + '\n')
location = {'root': str(R), 'work_dir': str(W), 'source_id': '45', 'new_id': '70',
    'handoff': str(H), 'handoff_sha256': HS, 'source_publication_consent': str(CONSENT),
    'source_publication_consent_sha256': spec(CONSENT)['sha256'],
    'files': len(index), 'logical_bytes': sum(x['bytes'] for x in index),
    'only_existing_media_hardlinks_and_small_text_metadata_copied': True,
    'no_remote_write_by_local_preparation': True}
(C / 'active-source45-book70-existing-normal18-staging-location.json').write_text(json.dumps(location, ensure_ascii=False, indent=2) + '\n')
print(json.dumps(location, ensure_ascii=False), flush=True)
