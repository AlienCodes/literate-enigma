"""User102's latest 33 review files. This contract never promotes a final."""
from pathlib import PurePosixPath
from copy import deepcopy
import hashlib
import json
import math
import re

PRIMARY = 'alienalgorithm/postgraduate-vocabulary'
BACKUP = 'AlienCodes/literate-enigma'
REPOSITORIES = (PRIMARY, BACKUP)
TAG = 'books38-70-latest-review-4k-20261114-v2'
ZIP_NAME = '38-70-4K-LATEST-REVIEW.zip'
BOOKS = tuple(f'{n:02d}' for n in range(38, 71))
SOURCES = ('19','29','43','52','48','37','31','16','40','54','46','24',
           '70','38','09','68','35','30','69','66','08','63','32','57',
           '23','64','18','56','41','58','25','59','45')
REVIEW_ONLY_SOURCES = frozenset(('54','70','68','30','69','66','18'))
FROZEN_MAPPING_SHA256 = '083da8975cd2204e3f8325f48373d04987aac24c7f9b5c40c5a81282e1cdaf9c'
SOURCE30_H_SHA = 'ac03f85dc1a3c55a5cbebdfb7236bb21e20cc9968ef5483f44098e77f3d61fc1'
SOURCE30_VIDEO_SHA = '9bb0be9d36cc219b8c1bdf286a1dc4b990a91160d8254cc55e323050ebed79b2'
INVENTORY_PATH = '视频修订定稿/已归档视频总清单.json'
REGISTRY_PATH = '视频修订定稿/latest_requests.json'
ASSET_NAMES = (ZIP_NAME, 'MANIFEST.json', 'SHA256SUMS.txt', 'README.txt')


def require(condition, why):
    if not condition:
        raise AssertionError(why)


def sha_bytes(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical_sha(value):
    return sha_bytes(json.dumps(value, ensure_ascii=False, sort_keys=True,
                               separators=(',', ':'), allow_nan=False).encode())


def hash64(value):
    require(isinstance(value, str) and re.fullmatch('[0-9a-f]{64}', value),
            'Expected a complete SHA-256')
    return value


def commit40(value):
    require(isinstance(value, str) and re.fullmatch('[0-9a-f]{40}', value),
            'An immutable full Git commit is required')
    return value


def safe_path(value, suffix=None):
    require(isinstance(value, str) and value and '\\' not in value and
            not any(c in value for c in '\r\n\0'), 'Unsafe repository path')
    p = PurePosixPath(value)
    require(not p.is_absolute() and '..' not in p.parts and '.' not in p.parts,
            'Repository path must be relative')
    require(value.startswith(('视频修订定稿/', '审核样片/')),
            'Only immutable public video or review archives are allowed')
    require(not any(x in value.lower() for x in
                    ('rootstate', '/.cache/', '/gt/', '/tts/', 'voices-v1', '.onnx')),
            'Private state, models and caches are excluded')
    if suffix:
        require(p.suffix == suffix, 'Wrong evidence file extension')
    return value


def media_identity(row):
    return {k: row[k] for k in ('asset_commit', 'video_repo_path', 'bytes', 'sha256')}


def registry_rows(registry):
    require(registry['kind'] == 'public-purpose-built-latest-user-video-request-registry',
            'Use the real public latest-request registry')
    rows = registry['articles']
    byid = {r['source_id']: r for r in rows}
    require(len(rows) == len(byid) == 70 and set(byid) ==
            {f'{n:02d}' for n in range(1, 71)}, 'All 70 registry entries required')
    requested = registry['requested_latest_review_release_range']
    require(requested['from_video_order'] == '38' and
            requested['through_video_order'] == '70' and
            requested['only_actual_newest_qualified_files'] is True and
            requested['missing_or_pending_items_are_production_pending_not_legacy_fillers'] is True,
            'The release must remain in the actual user102 latest-only scope')
    return byid


def eligible_final_ids(inventory, registry):
    # Identical user146 selector used by the actual latest final directory.
    from latest_final_directory_policy import select
    return select(inventory, registry)[0]


def validate_mapping(registry, frozen):
    byid = registry_rows(registry)
    rows = frozen['illustrations']
    require(frozen['count'] == len(rows) == 70, 'Frozen book mapping is incomplete')
    mapping = {r['new_id']: r for r in rows}
    require(tuple(mapping[b]['source_id'] for b in BOOKS) == SOURCES,
            'Do not slice or reuse the old mixed 37–70 manifest')
    for book, sid in zip(BOOKS, SOURCES):
        require(byid[sid]['frozen_book_order'] == book and
                byid[sid]['current_video_order'] == book,
                'Video090 changes only the first 13 positions; these books stay fixed')
    return byid


def validate_row(row):
    require(row['source_id'] in SOURCES and row['book_order'] in BOOKS,
            'Only the exact requested 33 sources are eligible')
    require(SOURCES[BOOKS.index(row['book_order'])] == row['source_id'],
            'Source/book mismatch')
    require(row['current_video_order'] == row['book_order'], 'Wrong current order')
    require(row['release_name'] == row['book_order'] + ' ' + row['title_zh'] + '.mp4',
            'Use the current canonical title once, without old aliases')
    require(PurePosixPath(row['release_name']).name == row['release_name'] and
            not any(c in row['release_name'] for c in '\\\r\n\0'), 'Unsafe ZIP name')
    commit40(row['asset_commit']); safe_path(row['video_repo_path'], '.mp4')
    hash64(row['sha256']); hash64(row['latest_request_entry_sha256'])
    require(type(row['bytes']) is int and row['bytes'] > 0, 'Unknown video bytes')
    require(row['qualification'] in ('current_verified_final', 'verified_latest_review_only'),
            'Historical, pending or unqualified media cannot be published')
    require(row['full_V3_quality_qualified'] is True, 'Full actual V3 is mandatory')
    require(row['publisher_changes_audio_or_video'] is False, 'No media transformation')
    if row['qualification'] == 'verified_latest_review_only':
        require(row['source_id'] in REVIEW_ONLY_SOURCES, 'Unapproved review-only article')
        require(row['individual_user_final_acceptance'] is False and
                row['production_delivery_eligible'] is False and
                row['active_final_replacement_authorized'] is False,
                'A review must not be promoted to the final directory')
        require(row['specific_review_authorization_id'] == '102', 'Wrong review authority')
        require(set(row['evidence']) == {'handoff', 'validated_record', 'qc'},
                'Actual handoff, record and QC evidence must be archived')
        for evidence in row['evidence'].values():
            safe_path(evidence['repo_path'], '.json')
            hash64(evidence['sha256'])
            require(type(evidence['bytes']) is int and 0 < evidence['bytes'] <= 3_000_000,
                    'Missing or oversized public proof')
        require(row['actual_dual_permanent_archive_passed'] is True,
                'Review files must already be permanently stored in both repositories')
        require(row['tail_policy'] in ('actual_normal18', 'preserved_existing_source30'),
                'Tail provenance must be explicit')
    return row


def validate_review_documents(row, docs):
    validate_row(row)
    require(row['qualification'] == 'verified_latest_review_only', 'Wrong evidence mode')
    h, record, qc = (docs[k] for k in ('handoff', 'validated_record', 'qc'))
    sid, book = row['source_id'], row['book_order']
    require(h['source_run'] == row['source_run'] and type(h['source_run']) is int,
            'Actual native run must be bound')
    require(len(h['articles']) == 1, 'A per-article handoff is required')
    a = h['articles'][0]
    require(a['source_id'] == sid and a['new_id'] == book, 'Wrong handoff article')
    if sid == '30':
        require(row['evidence']['handoff']['sha256'] == SOURCE30_H_SHA and
                row['sha256'] == SOURCE30_VIDEO_SHA and row['source_run'] == 43562525001,
                'Only the actually found newer source30 file is allowed')
        require(h['kind'] == 'existing-native-V3-reviewed-source30-for-user102-review-only' and
                h['status'] == 'passed_existing_native_inline_source_and_media_V3_for_user102_review' and
                h['review_delivery_eligible'] is True and
                h['user_final_acceptance_claimed'] is False and
                h['active_final_replacement_authorized'] is False,
                'Source30 remains an existing-byte review, not a newly finalized file')
        require(a['passed_per_article'] is True and row['tail_policy'] ==
                'preserved_existing_source30', 'Do not invent a new 0.6s tail')
        video = a['final_mp4']
    else:
        require(row['source_run'] >= 43600000000,
                'Old unqualified or legacy outputs cannot fill newly produced review slots')
        require(h.get('preview_only') is True and h.get('review_only') is True and
                h.get('production_delivery_eligible') is False and
                h.get('preview_delivery_eligible') is True and
                h.get('specific_review_authorization_id') == '102',
                'Use the actual user102 review-only final V3 handoff')
        require(a.get('preview_passed') is True and a.get('passed_per_article') is False and
                a.get('production_delivery_eligible') is False,
                'Review metadata must not be relabeled as individual final acceptance')
        require(record.get('preview_only') is True and
                record.get('production_delivery_eligible') is False and
                record.get('preview_delivery_eligible') is True,
                'The actual record must preserve review-only status')
        video = a['preview_mp4']
        tail = record['tail']
        require(tail['extra_body_hold_frames'] == 18 and
                tail['illustration_frames'] == tail['summary_frames'] == 60,
                'New review output requires 18 + 60 + 60 actual frames')
        require(tail['speech_end_frame'] == math.ceil(tail['voice_endpoint_seconds'] * 30) and
                tail['held_body_end_frame'] == tail['speech_end_frame'] + 18 ==
                tail['illustration_start_frame'] and
                tail['summary_start_frame'] == tail['illustration_start_frame'] + 60 and
                tail['output_frames'] == tail['summary_start_frame'] + 60,
                'Incorrect actual tail boundaries')
        require(.6 <= tail['voice_to_illustration_gap_seconds'] < .633334 and
                abs(tail['voice_to_illustration_gap_seconds'] -
                    (tail['illustration_start_frame']/30 - tail['voice_endpoint_seconds'])) < 1e-8,
                'The actual voiced endpoint must precede the image by about 0.6s')
        require(row['tail_policy'] == 'actual_normal18', 'Wrong new-review tail claim')
    require((video['bytes'], video['sha256']) == (row['bytes'], row['sha256']) and
            (record['id'], record['new_id'], record['bytes'], record['sha256']) ==
            (sid, book, row['bytes'], row['sha256']), 'Media/proof identity differs')
    require(qc['article'] == sid and qc['status'] == 'passed' and
            qc['video_sha256'] == row['sha256'] and qc['video_bytes'] == row['bytes'],
            'The actual final QC must pass for these exact bytes')
    require(qc['official_run']['run_id'] == row['source_run'] and
            qc['official_run']['status'] == 'completed' and
            qc['official_run']['conclusion'] == 'success' and
            qc['official_run']['stage'] == '4K', 'Real successful original 4K job required')
    probe = record['actual_probe']
    require((probe['width'], probe['height'], probe['fps']) == (3840, 2160, '30/1') and
            probe['frames'] > 120, 'Actual 4K/30 probe is required')
    require(qc['audio']['canonical_qc']['status'] == 'passed', 'Original audio gates must pass')
    chain, lossless = record['actual_audio_chain'], qc['audio']['lossless_copy']
    for key, ck, fk in (('aac_adts_sha256', 'canonical_aac_adts_sha256', 'final_aac_adts_sha256'),
                       ('packet_projection_sha256', 'canonical_packet_projection_sha256',
                        'final_packet_projection_sha256'),
                       ('packet_count', 'canonical_packet_count', 'final_packet_count')):
        require(chain[key] == lossless[ck] == lossless[fk], 'AAC bytes/clock must stay exact')
    require(lossless['audio_packet_times_identical'] is True, 'AAC clock changed')
    require(a['section']['qc']['sha256'] == row['evidence']['qc']['sha256'],
            'Handoff must bind this QC file')
    return probe


def validate_actual_selection(manifest, inventory, registry, review_docs):
    byid = registry_rows(registry)
    finals = eligible_final_ids(inventory, registry)
    current = {r['source_id']: r for r in inventory['articles']}
    for row in manifest['videos']:
        sid = row['source_id']; e = byid[sid]
        require(canonical_sha(e) == row['latest_request_entry_sha256'],
                'A newer source-specific request invalidates this release manifest')
        require((e['frozen_book_order'], e['current_video_order'], e['title_zh'], e['title_en']) ==
                (row['book_order'], row['current_video_order'], row['title_zh'], row['title_en']),
                'Current title or ordering changed')
        if row['qualification'] == 'current_verified_final':
            require(sid in finals, 'Pending old accepted video is excluded')
            require(media_identity(current[sid]) == media_identity(row),
                    'A newer current final replaces this manifest media')
        else:
            require(sid not in current, 'Review-only media must remain separate from current finals')
            require(not e.get('newest_user_revision_records') and
                    not e.get('final_4K_generation_authorized') and
                    not e.get('latest_finalization_authority'),
                    'A pending individual final must first complete its actual final archive')
            require(sid in review_docs, 'Missing actual archived review documents')
            validate_review_documents(row, review_docs[sid])
    return True


def validate_manifest(manifest):
    require(manifest['kind'] == 'latest-complete-books38-70-user102-review-release-v2' and
            manifest['specific_user_review_authorization'] == '102', 'Wrong publication purpose')
    require(manifest['requested_book_range'] == ['38','70'] and
            manifest['requested_video_count'] == manifest['actual_available_video_count'] == 33 and
            manifest['requested_video_range_complete'] is True, 'Exactly all 33 are mandatory')
    require(manifest['all33_actual_full_V3_quality_qualified'] is True and
            manifest['all33_individually_finalized_by_user_claimed'] is False and
            manifest['uniform_0_6_second_tail_claimed_for_this_release'] is False and
            manifest['old_mixed_or_legacy_fallback_allowed'] is False,
            'Do not overclaim final acceptance, timing or permit legacy fillers')
    require(manifest['current_final_aliases_changed_by_publisher'] is False and
            manifest['media_reencoded_or_audio_changed_by_publisher'] is False,
            'The publisher only packages unchanged qualified bytes')
    require(manifest['release_tag'] == TAG and manifest['zip_name'] == ZIP_NAME and
            manifest['release_prerelease'] is True, 'Wrong release identity')
    videos = manifest['videos']
    require(len(videos) == 33 and tuple(r['source_id'] for r in videos) == SOURCES and
            tuple(r['book_order'] for r in videos) == BOOKS, 'Wrong or incomplete source order')
    require(len({r['release_name'] for r in videos}) == 33, 'Duplicate or old filename')
    for row in videos:
        validate_row(row)
    require(manifest['total_video_bytes'] == sum(r['bytes'] for r in videos),
            'Total bytes do not match')
    require(manifest['source_frozen_mapping_sha256'] == FROZEN_MAPPING_SHA256,
            'The frozen book mapping must not change')
    snap = manifest['snapshot']
    commit40(snap['primary_commit']); commit40(snap['backup_commit'])
    for key, path in (('inventory', INVENTORY_PATH), ('latest_requests', REGISTRY_PATH)):
        spec = snap[key]
        require(spec['repo_path'] == path, 'Only the canonical frozen metadata is permitted')
        hash64(spec['sha256'])
        require(type(spec['bytes']) is int and 0 < spec['bytes'] < 5_000_000,
                'Missing frozen snapshot')
    return manifest
