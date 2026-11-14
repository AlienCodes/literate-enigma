"""Inventory-only revision safeguards; never produce media or alter quality gates."""
from copy import deepcopy
from pathlib import Path
import datetime
import hashlib
import json


def identity(value):
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()
    return hashlib.sha256(raw).hexdigest()


def authorization(path):
    if path is None:
        return None
    p = Path(path)
    raw = p.read_bytes()
    doc = json.loads(raw)
    assert doc['kind'] == 'explicit-completed-user-review-video-revision-archive-authorization'
    requirements = doc['requirements']
    assert requirements == {
        'old_asset_blobs_and_history_preserved': True,
        'unique_article_count_increased_by_revisions': False,
        'all_other_article_rows_unchanged': True,
        'published_review40_release_unchanged': True,
        'real_new_native_handoff_and_full_dual_byte_verification_still_required': True,
    }
    rows = doc['authorized_revisions']
    assert rows and len({r['source_id'] for r in rows}) == len(rows)
    for row in rows:
        prior = row['previous_row']
        assert prior['source_id'] == row['source_id'] and prior['new_id'] == row['new_id']
        assert identity(prior) == row['previous_row_sha256']
        spec = row['review_record']
        raw_review = Path(spec['path']).read_bytes()
        assert len(raw_review) == spec['bytes'] and hashlib.sha256(raw_review).hexdigest() == spec['sha256']
        review = json.loads(raw_review)
        state = review['execution_state']
        assert review['kind'] == 'completed_article_review_and_explicit_4k_regeneration_authorization'
        assert review['source_id'] == row['source_id'] and review['book_order'] == row['new_id']
        assert state['review_collection_complete_for_this_article'] is True
        allowed = state.get('new_regeneration_authorized_now_for_source_ids', [state.get('new_regeneration_authorized_now_for_source_id')])
        assert row['source_id'] in allowed
        assert state.get('existing_published_review_package_must_be_preserved', False) is True
    return {'document': doc, 'sha256': hashlib.sha256(raw).hexdigest()}


def revised_row(old, current, auth):
    assert auth is not None, 'Existing source ID requires explicit completed-review authorization'
    matches = [r for r in auth['document']['authorized_revisions'] if r['source_id'] == old['source_id']]
    assert len(matches) == 1, 'Revision source is outside the authorized review scope'
    permit = matches[0]
    assert old == permit['previous_row'] and identity(old) == permit['previous_row_sha256']
    assert current['source_id'] == old['source_id'] and current['new_id'] == old['new_id']
    assert current['passed_per_article'] is True
    assert current['source_run'] != old['source_run'], 'New review revision must be from a new actual native run'
    assert current['video_repo_path'] != old['video_repo_path']
    assert current['archive_prefix'] != old['archive_prefix'] and current['asset_commit'] != old['asset_commit']
    result = deepcopy(current)
    assert 'previous_versions' not in result and 'revision_archive_authorization' not in result
    result['previous_versions'] = deepcopy(old.get('previous_versions', [])) + [deepcopy(old)]
    result['revision_archive_authorization'] = {
        'document_sha256': auth['sha256'],
        'authority_review_record_sha256': permit['review_record']['sha256'],
        'previous_row_sha256': permit['previous_row_sha256'],
        'previous_video_sha256': old['sha256'],
        'previous_source_run': old['source_run'],
        'unique_article_count_increased': False,
    }
    return result


def expected_rows(previous, incoming, auth=None):
    old = {r['source_id']: r for r in previous['articles']}
    assert len(old) == len(previous['articles']) == previous['archived_passed_count']
    assert len({r['new_id'] for r in old.values()}) == len(old)
    assert len({r['source_id'] for r in incoming}) == len(incoming)
    result = deepcopy(old)
    for row in incoming:
        assert row['passed_per_article'] is True
        sid = row['source_id']
        result[sid] = revised_row(old[sid], row, auth) if sid in old else deepcopy(row)
    assert len({r['new_id'] for r in result.values()}) == len(result) <= 70
    return result


def merge_inventory(previous, incoming, batch, auth=None):
    rows = expected_rows(previous, incoming, auth)
    batches = deepcopy(previous.get('batches', []))
    assert not any(r['prefix'] == batch['prefix'] for r in batches), 'New revision must append a new archive prefix'
    batches.append(deepcopy(batch))
    return {
        'schema_version': 1,
        'updated_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'requested_total': 70,
        'archived_passed_count': len(rows),
        'remaining_not_claimed_passed': 70-len(rows),
        'release_created': False,
        'articles': sorted(rows.values(), key=lambda r: int(r['new_id'])),
        'batches': batches,
    }


def validate_transition(previous, current, incoming, auth=None):
    expected = expected_rows(previous, incoming, auth)
    actual = {r['source_id']: r for r in current['articles']}
    assert len(actual) == len(current['articles'])
    assert actual == expected, 'Unrelated row, revision history or accepted article identity changed'
    assert current['archived_passed_count'] == len(expected)
    assert current['remaining_not_claimed_passed'] == 70-len(expected)
    assert current['requested_total'] == 70 and current['release_created'] is False
    new_batches = {}
    for row in incoming:
        prefix = row['archive_prefix']
        assert not any(b['prefix'] == prefix for b in previous.get('batches', []))
        batch = new_batches.setdefault(prefix, {'prefix': prefix, 'asset_commit': row['asset_commit'], 'source_ids': []})
        assert batch['asset_commit'] == row['asset_commit']
        batch['source_ids'].append(row['source_id'])
    assert current['batches'] == previous.get('batches', []) + list(new_batches.values())
    old_ids = {r['source_id'] for r in previous['articles']}
    ids = {r['source_id'] for r in incoming}
    return sorted(ids-old_ids), sorted(ids & old_ids)
