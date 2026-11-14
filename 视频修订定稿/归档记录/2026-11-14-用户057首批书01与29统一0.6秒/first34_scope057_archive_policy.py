"""Narrow user057 scope for existing accepted rows, with exact source/book binding."""
from pathlib import Path
import hashlib
import json

KIND='explicit-user057-first34-existing-media-archive-authorization'
USER_SHA='3c91671ad6dcc1e30f6336efa394eac1ff776c8405157b924f2e86f64266284a'
PUBLIC_SCOPE_SHA='baeeb41aea6e990a3e4dcfbc5de570addd09094871f323779213de88481e8e72'
INITIAL_INDEX_SHA='9d4ef56dce6892b4278a009e31cc71a53397878247dd67955e63d4e10f4b7d6c'
EXPECTED={f'{n:02d}':sid for n,sid in enumerate('01 22 07 03 12 10 06 51 05 11 39 04 21 55 44 50 20 02 49 42 14 27 13 61 15 17 26 36 28 33 67 47 34 62'.split(),1)}
def digest(raw):return hashlib.sha256(raw).hexdigest()
def identity(value):return digest(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode())
def read(spec,expected=None):
    raw=Path(spec['path']).read_bytes();assert len(raw)==spec['bytes'] and digest(raw)==spec['sha256']
    if expected:assert digest(raw)==expected
    return json.loads(raw)
def protected(inventory):return [r for r in inventory['articles'] if int(r['new_id'])>=35]
def authorization(path):
    raw=Path(path).read_bytes();doc=json.loads(raw);assert doc['kind']==KIND
    user=read(doc['user057_record'],USER_SHA);scope=read(doc['frozen_public_book_scope'],PUBLIC_SCOPE_SHA)
    assert user['author']=='user' and user['required_scope']['book_order_inclusive']==[1,34]
    assert user['required_scope']['fix_only_current_versions_with_less_than_required_post_reading_pause_seconds']==0.6 and user['required_scope']['nominal_extra_body_hold_frames_at_30fps']==18
    assert user['execution_state']['all_PDF_work_remains_paused'] is True and user['execution_state']['no_bulk_changes_to_book35_and_later_authorized_now'] is True
    assert {r['book_order']:r['source_id'] for r in scope['book_source_mapping']}==EXPECTED
    initial=read(doc['initial_current_inventory'],INITIAL_INDEX_SHA)
    assert identity(protected(initial))==doc['protected_book35_plus_rows_sha256']
    assert doc['requirements']=={'only_book01_to34_exact_frozen_mapping':True,'existing_eleven06_versions_reused_without_change':True,'all_other_rows_old_versions_and_archives_preserved':True,'book35_plus_rows_equal_initial_frozen_index':True,'real_frozen_handoff_and_full_dual_MP4_byte_verification_required':True,'no_media_generation_or_audio_edit_by_archivist':True,'no_subjective_preview_acceptance_invented':True,'all_PDF_work_paused':True}
    permits=doc['authorized_revisions'];assert permits and len({p['source_id'] for p in permits})==len(permits)
    for p in permits:
        assert EXPECTED.get(p['new_id'])==p['source_id']
        assert p['previous_row']['source_id']==p['source_id'] and p['previous_row']['new_id']==p['new_id'] and identity(p['previous_row'])==p['previous_row_sha256']
        assert p['review_record']==doc['user057_record']
        read(p['actual_scope057_handoff'])
    return {'document':doc,'sha256':digest(raw)}
def assert_protected_rows(inventory,auth):
    assert identity(protected(inventory))==auth['document']['protected_book35_plus_rows_sha256'], 'User057 cannot change any book35+ index row'
def check_revision(old,current,permit,auth):
    assert EXPECTED.get(current['new_id'])==current['source_id']
    assert old==permit['previous_row'] and identity(old)==permit['previous_row_sha256']
    assert current['passed_per_article'] is True and current['production_delivery_eligible'] is True and current['preview_only'] is False
    assert current['post_reading_pause_seconds']==0.6 and current['nominal_extra_hold_frames_at_30fps']==18
    assert current['current_uniform_timing_authorized_by_user057'] is True
    spec=permit['actual_scope057_handoff'];h=read(spec);assert spec['sha256']==current['postprocessing_full_V3_handoff_sha256']
    assert len(h['articles'])==1;item=h['articles'][0]
    assert item['source_id']==current['source_id'] and item['new_id']==current['new_id'] and item['passed_per_article'] is True
    assert item['final_mp4']['sha256']==current['sha256'] and item['final_mp4']['bytes']==current['bytes']
    assert h['production_delivery_eligible'] is True and h['preview_only'] is False and h['new_native_job_or_TTS_claimed'] is False
    if current['source_id']=='28':
        assert spec['sha256']=='8aa9ff04e6ae659326d4269334aa870f14ff1e380f1dc0408ebb45d960850fbe'
        assert h['kind']=='first34-uniform-timing057-existing-qualified-preview-reuse' and h['status']=='passed_actual_existing18_media_adopted_under_explicit_first34_scope057'
        assert h['first34_uniform_timing_installation_eligible'] is True and h['active_final_replacement_authorized'] is True
        assert h['new_tail_or_audio_processing_claimed'] is False and h['new_subjective_listening_or_effect_acceptance_claimed'] is False and h['final_user_acceptance'] is False
        assert current['source_run']==h['source_run']==43576642418
        assert current['sha256']=='1e1685c5b0eff4ebb2d3e8bab3f368336ea31a313b38c10a0ef0f7a1ae365163' and current['bytes']==17473089
        assert current['media_origin']=='existing_qualified_preview06_reused_as_explicit_user057_uniform_timing_edition'
        assert current['subjective_listening_or_effect_acceptance_claimed'] is False
        assert current['reused_existing_preview_asset_commit']=='dd7a3d7badbdcae587f11522f69c0ebaef21853f'
    else:
        assert h['kind']=='authorized-normal18-local-tail-derivative' and h['status']=='passed_actual_normal18_post_only_for_permanent_archive'
        assert h['local_postprocessing_only'] is True and h['source_run']==current['source_run']==old['source_run']
        assert current['media_origin']=='actual_validated_normal18_local_tail_derivative_of_original_native_source'
        assert current['inherited_full_native_archive_commit']==old['asset_commit']
        prior=read(h['inherited_full_V3']);assert prior['status']=='passed_actual_native_inline_article_for_permanent_archive'
        candidates=[r for r in prior['articles'] if r['source_id']==old['source_id'] and r['new_id']==old['new_id']]
        assert len(candidates)==1 and candidates[0]['passed_per_article'] is True
        assert candidates[0]['final_mp4']['sha256']==old['sha256'] and candidates[0]['final_mp4']['bytes']==old['bytes']
        scope=[r for r in item['section']['evidence'] if r.get('sha256')==USER_SHA]
        assert scope and all(read(r,USER_SHA)['author']=='user' for r in scope)
        assert current['sha256']!=old['sha256']
    return True
