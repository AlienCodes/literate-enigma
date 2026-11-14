"""Inventory-only revision safeguards; never produce media or alter quality gates."""
from copy import deepcopy
from pathlib import Path
import datetime
import hashlib
import json
import first34_scope057_archive_policy as scope057


def identity(value):
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()
    return hashlib.sha256(raw).hexdigest()


def authorization(path):
    if path is None:
        return None
    p = Path(path)
    raw = p.read_bytes()
    doc = json.loads(raw)
    if doc['kind']==scope057.KIND:
        return scope057.authorization(path)
    assert doc['kind'] == 'explicit-completed-user-review-video-revision-archive-authorization'
    requirements = doc['requirements']
    expected_requirements = {
        'old_asset_blobs_and_history_preserved': True,
        'unique_article_count_increased_by_revisions': False,
        'all_other_article_rows_unchanged': True,
        'published_review40_release_unchanged': True,
        'real_new_native_handoff_and_full_dual_byte_verification_still_required': True,
    }
    if doc.get('actual_original_native_source_run_preserved_for_local_tail_derivative') is True:
        del expected_requirements['real_new_native_handoff_and_full_dual_byte_verification_still_required']
        expected_requirements['real_actual_full_V3_handoff_and_full_dual_byte_verification_still_required'] = True
        spec = doc['additional_global_transition_authority']
        raw_global = Path(spec['path']).read_bytes()
        assert len(raw_global)==spec['bytes'] and hashlib.sha256(raw_global).hexdigest()==spec['sha256']=='4bcae46b68b9584f107966f683af580b474fa9835f101834fe55ed6968dfc36b'
        global_review = json.loads(raw_global)
        assert global_review['required_behavior']['pause_seconds']==0.6 and global_review['required_behavior']['nominal_extra_hold_frames']==18
        assert global_review['execution_state']['all_prior_final_authorizations_remain_valid'] is True
        assert doc['new_native_or_TTS_run_not_invented'] is True
    assert requirements == expected_requirements
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
        legacy_kinds={'completed_article_review_and_explicit_4k_regeneration_authorization','completed_article_review_and_explicit_4k_regeneration_authorization_with_vocabulary_table_sync'}
        pause_kind='completed_article_review_and_explicit_4k_regeneration_authorization_with_end_reading_pause'
        dolly_kind='completed_dolly_review_global_future_4k_pause_rule_and_tu_youyou_preview_priority'
        assert review['kind'] in legacy_kinds|{pause_kind,dolly_kind}
        if review['kind']==pause_kind:
            assert doc.get('actual_original_native_source_run_preserved_for_local_tail_derivative') is True
            assert state['end_reading_pause_explicitly_required_for_this_article'] is True and state['old_audio_and_published_versions_preserved'] is True
        if review['kind']==dolly_kind:
            assert doc.get('actual_original_native_source_run_preserved_for_local_tail_derivative') is True
            assert state['global_future_post_reading_pause_seconds']==0.3 and state['nominal_extra_hold_frames_at_30fps']==9
            assert state['old_published_versions_preserved'] is True and state['audio_quality_issues_must_be_resolved_before_dolly_new_final'] is True
            assert state['do_not_publish_or_promote_tu_youyou_as_accepted_final_before_user_effect_acceptance'] is True
        if review['kind'].endswith('_with_vocabulary_table_sync'):
            assert state['sync_newly_marked_words_to_corresponding_article_vocabulary_tables_authorized'] is True
        assert review['source_id'] == row['source_id'] and review['book_order'] == row['new_id']
        assert state['review_collection_complete_for_this_article'] is True
        allowed = state.get('new_regeneration_authorized_now_for_source_ids', [state.get('new_regeneration_authorized_now_for_source_id')])
        if review['kind']==dolly_kind:allowed=state['new_final_4k_authorizations']
        assert row['source_id'] in allowed
        preserved = state.get('existing_published_review_package_must_be_preserved', state.get('existing_published_review_packages_must_be_preserved', False))
        if review['kind']==pause_kind:preserved=state['old_audio_and_published_versions_preserved']
        if review['kind']==dolly_kind:preserved=state['old_published_versions_preserved']
        assert preserved is True
    return {'document': doc, 'sha256': hashlib.sha256(raw).hexdigest()}


def revised_row(old, current, auth):
    assert auth is not None, 'Existing source ID requires explicit completed-review authorization'
    matches = [r for r in auth['document']['authorized_revisions'] if r['source_id'] == old['source_id']]
    assert len(matches) == 1, 'Revision source is outside the authorized review scope'
    permit = matches[0]
    assert old == permit['previous_row'] and identity(old) == permit['previous_row_sha256']
    assert current['source_id'] == old['source_id'] and current['new_id'] == old['new_id']
    assert current['passed_per_article'] is True
    if auth['document']['kind']==scope057.KIND:
        scope057.check_revision(old,current,permit,auth)
    elif current['source_run'] == old['source_run']:
        assert auth['document'].get('actual_original_native_source_run_preserved_for_local_tail_derivative') is True
        assert current.get('local_postprocessing_only') is True and current.get('new_native_Actions_run_claimed') is False
        assert current.get('production_delivery_eligible') is True and current.get('preview_only') is False
        assert current.get('media_origin')=='actual_validated_normal18_local_tail_derivative_of_original_native_source'
        assert current.get('inherited_full_native_archive_commit')==old['asset_commit']
        assert current.get('post_reading_pause_seconds')==0.6 and current.get('nominal_extra_hold_frames_at_30fps')==18
        spec=permit['actual_hold18_handoff']
        raw=Path(spec['path']).read_bytes()
        assert len(raw)==spec['bytes'] and hashlib.sha256(raw).hexdigest()==spec['sha256']==current['postprocessing_full_V3_handoff_sha256']
        h=json.loads(raw)
        assert h['kind']=='authorized-normal18-local-tail-derivative' and h['status']=='passed_actual_normal18_post_only_for_permanent_archive'
        assert h['local_postprocessing_only'] is True and h['new_native_job_or_TTS_claimed'] is False and h['production_delivery_eligible'] is True and h['preview_only'] is False
        assert h['source_run']==old['source_run'] and len(h['articles'])==1
        actual=h['articles'][0]
        assert actual['passed_per_article'] is True and actual['source_id']==old['source_id'] and actual['new_id']==old['new_id']
        assert actual['final_mp4']['sha256']==current['sha256'] and actual['final_mp4']['bytes']==current['bytes']
        assert current['sha256']!=old['sha256']
    else:
        assert current['source_run'] != old['source_run']
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
    if auth and auth['document']['kind']==scope057.KIND:
        scope057.assert_protected_rows(previous,auth)
        assert all(r['source_id'] in old for r in incoming), 'Unarchived09/31 need an actual new-source validation adapter before addition'
    for row in incoming:
        assert row['passed_per_article'] is True
        sid = row['source_id']
        result[sid] = revised_row(old[sid], row, auth) if sid in old else deepcopy(row)
    assert len({r['new_id'] for r in result.values()}) == len(result) <= 70
    if auth and auth['document']['kind']==scope057.KIND:scope057.assert_protected_rows({'articles':sorted(result.values(),key=lambda r:int(r['new_id']))},auth)
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
