"""Read one immutable purpose-specific user authority; no general schema fallback."""
import hashlib
import json

KIND = 'actual-user-finalization-authority-book48-source46-after-all-feedback'
DESCRIPTIVE_ID = 'book48-finalization-after-brightening-20261115'
SHA256 = '82cd0b5dbe9b796faef7c8c108aad00efef68fb9797d7eaef6d8ea5a97da9038'
SIZE = 2049
VERBATIM = '48篇定稿，第48篇定稿。这一篇定稿，这一篇定稿。记住，记住最后这个0.6，记住最后这个0.6。然后然然后这个前47天都已经弄好了吗？全都搞定了吗？'


def check(raw, source_id, book_order):
    """Bind the original user words instead of inventing missing legacy fields."""
    assert isinstance(raw, bytes) and len(raw) == SIZE
    assert hashlib.sha256(raw).hexdigest() == SHA256
    assert source_id == '46' and str(book_order) == '48'
    d = json.loads(raw)
    assert d['kind'] == KIND and d['local_descriptive_id'] == DESCRIPTIVE_ID
    assert d['numeric_review_message_id_invented'] is False
    assert d['source_id'] == source_id and d['book_order'] == 48
    assert d['raw_user_text_verbatim'] == VERBATIM
    assert d['final_4K_generation_authorized'] is True
    assert d['post_reading_pause_seconds'] == 0.6
    assert d['post_reading_hold_frames_at_30fps'] == 18
    assert d['prior_hold152_preserved_as_history_and_superseded_only_for_book48'] is True
    assert d['include_all_actual_latest_book48_feedback_before_this_authority'] is True
    assert d['original_illustration_seconds_under_existing_global_policy'] == 2
    assert d['original_summary_card_seconds_under_existing_global_policy'] == 2
    assert d['cloud_final_and_unique_latest_final_directory_under_existing_policy'] is True
    assert d['book49_through70_pause153_unchanged'] is True
    assert d['all_PDF_book_and_catalog_work_stays_paused'] is True
    assert d['no_quality_gate_or_numeric_threshold_changes_authorized'] is True
    assert d['completion_requires_actual_full_official_audio_text_layout_and_final_V3_validation_then_permanent_dual_cloud_and_latest_selector_update'] is True
    assert d['not_a_claim_of_completed_book48_media'] is True
    return d
