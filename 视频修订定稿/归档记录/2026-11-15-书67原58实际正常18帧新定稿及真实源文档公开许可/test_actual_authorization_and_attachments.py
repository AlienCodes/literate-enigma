"""Finite local-only source58/book67 installer data checks; no production execution."""
from pathlib import Path
import ast
import hashlib
import json
import sys

B = Path('/workspace/work/video-archive-batches-20261114')
C = Path('/dev/shm/archive-writer-main061')
R = Path(__file__).resolve().parent
sys.path.insert(0, str(B))
import archive_revision_policy as revisions
import exact_known_final_authorities17 as exact


def spec(path):
    p = Path(path)
    return {'path': str(p), 'bytes': p.stat().st_size,
            'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}


state = json.loads((C / 'CURRENT-ARCHIVE-STATE.json').read_bytes())
assert state['primary_main'] == '405ff24683833df29af89f018f37ae48e0ae58ce'
assert state['backup_head'] == '3deb81763c31088aeb5197ab238cb0559c7274c9'
inventory_path = Path(state['actual_inventory'])
inventory_raw = inventory_path.read_bytes()
inventory = json.loads(inventory_raw)
old = next(x for x in inventory['articles'] if x['source_id'] == '58')
assert len(inventory['articles']) == 69
assert old['source_run'] == 43533004625
assert old['asset_commit'] == '4e9b424736bf1bd703f64cda4ef77a6b8fc081df'
assert old['sha256'] == 'd47b9807105b5433cf93e120aad64cf17ba2805720ada9bdade33c63745db75f'
user = Path('/workspace/work/book67-source58-scratch-collecting-20261115/USER-BOOK67-SOURCE58-FINALIZATION-AFTER-SCRATCH-20261115.json')
user_spec = spec(user)
assert user_spec['bytes'] == 614
assert user_spec['sha256'] == '584a40908d831f219eebd0af1c2ac0f140de452a39cbec29fb8dd9daa09b74ed'
raw = user.read_bytes()
receipt = exact.check_exact_authority(raw, '58', '67')
assert receipt['actual_quote_verbatim'] == '67定稿 4K'
assert 'author' not in json.loads(raw)
authorization = {
    'kind': 'explicit-completed-user-review-video-revision-archive-authorization',
    'requirements': {
        'old_asset_blobs_and_history_preserved': True,
        'unique_article_count_increased_by_revisions': False,
        'all_other_article_rows_unchanged': True,
        'published_review40_release_unchanged': True,
        'real_new_native_handoff_and_full_dual_byte_verification_still_required': True,
    },
    'authorized_revisions': [{
        'source_id': '58', 'new_id': '67', 'previous_row': old,
        'previous_row_sha256': revisions.identity(old), 'review_record': user_spec,
    }],
}
authorization_path = R / 'ACTUAL-BOOK67-LOCAL-EXISTING-ROW-AUTHORIZATION-DRYCALL-INPUT.json'
assert json.loads(authorization_path.read_bytes()) == authorization
actual = revisions.authorization(authorization_path)
assert actual['document'] == authorization
assert revisions.original_source_run(old, authorization['authorized_revisions'][0]) == 43533004625

handoff_path = Path('/workspace/work/review58-finalV3/43736478355-normal18/archive-handoff.json')
assert spec(handoff_path) == {
    'path': str(handoff_path), 'bytes': 76510,
    'sha256': '4c833c5b9581e4974fd28a92658711578219989ca9092c60b531ce215572fe82',
}
handoff = json.loads(handoff_path.read_bytes())
assert handoff['source_run'] == 43736478355
assert handoff['production_delivery_eligible'] is True and handoff['preview_only'] is False
assert handoff['original_producer_claimed_prior_delivery_V3'] is False
assert len(handoff['articles']) == 1
article = handoff['articles'][0]
assert (article['source_id'], article['new_id']) == ('58', '67')
assert article['passed_per_article'] is True
assert article['final_mp4']['bytes'] == 16765169
assert article['final_mp4']['sha256'] == '55b0450125e66dc5d79249405aaf6bea6bc1f114b7ee689d6c9b3698b048f1ee'
source_path = Path(handoff['current_source_validation_handoff']['path'])
assert spec(source_path) == handoff['current_source_validation_handoff']
assert spec(source_path)['sha256'] == '1bd4de3cccb5939fcad09e4022f3f252d84a1c39188842f1aefea43d4e674dca'
qc = json.loads(Path(article['section']['qc']['path']).read_bytes())
assert qc['audio']['repair_applied'] is False
assert qc['audio_repair_applied_in_this_tail_postprocess'] is False

bad = []
mutated_kind = json.loads(raw)
mutated_kind['kind'] = 'wrong-kind'
mutated_raw = json.dumps(mutated_kind, ensure_ascii=False).encode()
assert mutated_raw != raw
for name, callback in [
    ('wrong-source', lambda: exact.check_exact_authority(raw, '59', '67')),
    ('wrong-book', lambda: exact.check_exact_authority(raw, '58', '66')),
    ('wrong-raw-SHA', lambda: exact.check_exact_authority(raw + b' ', '58', '67')),
    ('modified-actual-kind', lambda: exact.check_exact_authority(mutated_raw, '58', '67')),
]:
    try:
        callback()
    except AssertionError:
        bad.append({'name': name, 'rejected': True})
    else:
        raise AssertionError('Negative accepted: ' + name)

candidate = R / 'install_book67_source58_full_current_final.py'
tree = ast.parse(candidate.read_text())
main = next(x for x in tree.body if isinstance(x, ast.FunctionDef) and x.name == 'main')
attach_loop = next(x for x in main.body if isinstance(x, ast.For) and isinstance(x.target, ast.Name)
                   and x.target.id == 'p' and isinstance(x.iter, ast.List))
integrator = C / 'integrate_verified_batch-book61-isolated-single-delta-transport.py'
assert spec(integrator)['sha256'] == 'e44686bf2d238e96c1aad08f522b927de8c29955e196d61277a6e28a5fed9400'
paths = []
for node in attach_loop.iter.elts:
    if isinstance(node, ast.Starred):
        continue  # Future actual transport records, owned and supplied by sole writer.
    expression = ast.Expression(body=node)
    path = eval(compile(expression, str(candidate) + '#local-attachment-path', 'eval'),
                {'Path': Path, 'B': B, 'integrator': integrator, 'user': user,
                 'consent': Path('/workspace/work/all-project-deliverables-and-final70-release-authorities-20261115/USER-ALL-PROJECT-GENERATED-DELIVERABLES-GITHUB-ARCHIVE-AUTHORITY.json'),
                 '__file__': str(candidate)})
    assert path.is_file(), str(path)
    paths.append(spec(path))
assert len({Path(x['path']).name for x in paths}) == len(paths)
assert spec(user) == user_spec and inventory_path.read_bytes() == inventory_raw

record = {
    'kind': 'actual-source58-book67-local-only-existing-row-authorization-and-qualified-H-binding',
    'baseline_heads': {'primary': state['primary_main'], 'backup': state['backup_head']},
    'actual_inventory': spec(inventory_path), 'actual_existing_oldrow_source_run': 43533004625,
    'actual_oldrow_identity_SHA256': revisions.identity(old),
    'actual_oldrow_preserved_entire_typed_value': True, 'actual_final_raw': user_spec,
    'actual_raw_reader_receipt': receipt, 'actual_mature_authorization_drycall_passed': True,
    'no_legacy_manifest_or_fabricated_old_run_added': True,
    'actual_final_H': spec(handoff_path), 'actual_sourceQA_H': spec(source_path),
    'source_native_audio_repair_applied': False, 'local_tail_audio_repair_applied': False,
    'old_accepted_AAC_equality_true_is_separate_from_original_producer_prior_fullV3_false': True,
    'negative_cases': bad, 'all_current_concrete_attachment_paths_checked': paths,
    'future_loc_READY_and_actual_transport_records_not_assumed_or_fabricated': True,
    'future_transport_reserved_existing_basenames': [Path(x['path']).name for x in paths],
    'source_H_raw_oldrow_registry_and_remote_unchanged': True,
    'no_collector_or_installer_or_remote_execution': True,
}
output = R / 'ACTUAL-EXISTING58-RAW-AUTHORIZATION-H-BINDING-AND4-REJECTION-DRYCALL.json'
output.write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n')
print(json.dumps(spec(output)))
