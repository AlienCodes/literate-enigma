"""Read exact immutable user quotes; do not rewrite old records or grant other scopes."""
from pathlib import Path
from copy import deepcopy
import hashlib, json

RAW = {
    '25': {'book': '68', 'bytes': 752,
        'sha256': 'c9640c633ed9daac77730f01e9bb4228208b09977b9f0a6d0a3c4d6f7da18f7a',
        'kind': 'actual-user-finalization-no-source-revision',
        'id_key': 'local_descriptive_id', 'id': 'book68-source25-apollo13-finalization-20261115',
        'quote_key': 'raw_user_text_verbatim',
        'quote': '68 阿波罗13号：成功的失败 定稿，这个定稿出4k视频。出4k 视频'},
    '45': {'book': '70', 'bytes': 1957,
        'sha256': '591135ed41aa8fa6fea7b97c838214571d7be7342ef59255fca6a3fe1dbe7f8a',
        'kind': 'actual-user-book70-source45-finalization-quote-no-new-content-edits',
        'id_key': 'descriptive_id', 'id': 'book70-source45-finalization-20261115',
        'quote_key': 'actual_raw_user_quote', 'quote': '70篇 定稿 4k'},
}
# The source45 final is deliberately unavailable until it has actually passed
# and its concrete SHA is frozen. Its original user quote can already be read.
FINAL = {
    '25': {'sha256': 'd149ef0fee2c13f575ef47de57f5f5e4e67427c8864a6cf68a32542c2f6d72a7',
        'bytes': 41014, 'video_sha256': '06af27da5d079a24aa8434f426a8417882e42b4686ecdfd874251ecc9ea0ce46',
        'video_bytes': 15969007, 'source_handoff_sha256': '27c9cfb3e050163d697febed2a3560327f02333ed6154db11af9129c6fde1d68',
        'run': 43533004625},
}

def check_authority(raw, sid, book):
    assert sid in RAW and str(book) == RAW[sid]['book']
    expected = RAW[sid]
    assert len(raw) == expected['bytes'] and hashlib.sha256(raw).hexdigest() == expected['sha256']
    user = json.loads(raw)
    assert user['kind'] == expected['kind'] and user['author'] == 'user'
    assert user['source_id'] == sid and user['book_order'] == expected['book']
    assert user[expected['id_key']] == expected['id'] and user[expected['quote_key']] == expected['quote']
    if sid == '25':
        assert user['new_media_or_QA_pass_not_claimed'] is True
    else:
        assert user['actual_scope']['final_4K_generation_authorized'] is True
        assert user['actual_scope']['new_text_translation_focus_note_or_audio_change_requested_in_this_quote'] is False
    return user

def check_handoff(h, sha):
    assert len(h['articles']) == 1
    a = h['articles'][0]
    sid = a['source_id']
    assert sid in FINAL, 'No actual frozen final has been bound for this source yet'
    c = FINAL[sid]
    assert sha == c['sha256'] and a['new_id'] == RAW[sid]['book']
    assert h['kind'] == 'actual-new-native-source-QA-then-authorized-normal18-local-tail'
    assert h['status'] == 'passed_actual_normal18_post_only_for_permanent_archive'
    assert h['local_postprocessing_only'] is True and h['new_native_job_or_TTS_claimed'] is False
    assert h['production_delivery_eligible'] is True and h['preview_only'] is False
    assert a['passed_per_article'] is True and h['source_run'] == c['run']
    assert (a['final_mp4']['bytes'], a['final_mp4']['sha256']) == (c['video_bytes'], c['video_sha256'])
    assert h['current_source_validation_handoff']['sha256'] == c['source_handoff_sha256']
    return True

def check_review(raw, sid, book, hold_spec):
    check_authority(raw, sid, book)
    data = Path(hold_spec['path']).read_bytes()
    assert sid in FINAL and len(data) == hold_spec['bytes'] == FINAL[sid]['bytes']
    assert hashlib.sha256(data).hexdigest() == hold_spec['sha256'] == FINAL[sid]['sha256']
    check_handoff(json.loads(data), hold_spec['sha256'])
    return True

def register_before_complete(entry, authority_spec, h, row):
    """Only the incoming row, in the same guarded installation that makes it complete."""
    sid = row['source_id']
    raw = Path(authority_spec['path']).read_bytes()
    assert len(raw) == authority_spec['bytes'] and hashlib.sha256(raw).hexdigest() == authority_spec['sha256']
    check_authority(raw, sid, row['new_id'])
    assert authority_spec['sha256'] == RAW[sid]['sha256']
    check_handoff(h, row['postprocessing_full_V3_handoff_sha256'])
    assert entry['source_id'] == sid and entry['frozen_book_order'] == entry['current_video_order'] == row['new_id']
    assert entry['latest_requested_revision_complete'] is False
    assert entry.get('actual_complete_validation_passed') is False
    assert entry.get('actual_dual_permanent_archive_passed') is False
    desc = RAW[sid]['id']
    assert not entry.get('latest_finalization_authority') or entry['latest_finalization_authority'] == desc
    requests = deepcopy(entry['newest_user_revision_records'])
    if desc not in requests:
        requests.append(desc)
    hashes = deepcopy(entry['user_request_SHA256'])
    assert desc not in hashes or hashes[desc] == authority_spec['sha256']
    hashes[desc] = authority_spec['sha256']
    entry.update(status='latest_authorized_revision_in_production',
        newest_user_revision_records=requests, user_request_SHA256=hashes,
        latest_finalization_authority=desc, final_4K_generation_authorized=True,
        pending_newer_request_blocks_old_fallback=True,
        older_accepted_archive_is_history_until_newest_request_qualified=True)
