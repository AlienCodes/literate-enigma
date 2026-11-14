"""Compile only after all 33 current finals/review-only dual archives really exist."""
import argparse
from copy import deepcopy
import datetime
import hashlib
import json
from pathlib import Path

from review_contract import (
    BOOKS, SOURCES, TAG, ZIP_NAME, PRIMARY, BACKUP, FROZEN_MAPPING_SHA256,
    INVENTORY_PATH, REGISTRY_PATH, canonical_sha, commit40, eligible_final_ids,
    hash64, media_identity, require, safe_path, sha_bytes, validate_actual_selection,
    validate_manifest, validate_mapping, validate_review_documents,
    registry_rows,
)

HERE = Path(__file__).resolve().parent
PROGRAMS = ('publish_latest_review.py', 'compile_latest_review.py',
            'review_contract.py', 'latest_final_directory_policy.py')


def spec(path):
    p = Path(path)
    raw = p.read_bytes()
    return {'path': str(p.resolve()), 'bytes': len(raw), 'sha256': sha_bytes(raw)}


def load_exact(path, expected=None):
    raw = Path(path).read_bytes()
    if expected:
        require(len(raw) == expected['bytes'] and sha_bytes(raw) == expected['sha256'],
                'Local immutable evidence changed')
    return json.loads(raw)


def row_base(sid, e):
    return {'source_id': sid, 'book_order': e['frozen_book_order'],
            'current_video_order': e['current_video_order'], 'title_zh': e['title_zh'],
            'title_en': e['title_en'],
            'release_name': e['frozen_book_order'] + ' ' + e['title_zh'] + '.mp4',
            'latest_request_entry_sha256': canonical_sha(e),
            'full_V3_quality_qualified': True, 'publisher_changes_audio_or_video': False}


def validate_dual_proofs(ready, docs):
    expected = (ready['asset_commit'], ready['video_repo_path'],
                ready['bytes'], ready['sha256'])
    proof = docs['remote_video_bytes']
    require(proof['passed'] is True and len(proof['streams']) == 2 and
            {r['repository'] for r in proof['streams']} == {PRIMARY, BACKUP},
            'Two actual whole-MP4 public byte proofs are required')
    for r in proof['streams']:
        require(r['passed'] is True and r['http_status'] == 200 and
                r['source_id'] == ready['source_id'] and
                r['new_id'] == ready['frozen_book_order'] and
                (r['pinned_asset_commit'], r['repo_path'], r['bytes'], r['sha256']) == expected,
                'A permanent archive byte proof points to different media')
    blobs = docs['dual_asset_blobs']
    require(len(blobs['archives']) == 2 and
            {r['repository'] for r in blobs['archives']} == {PRIMARY, BACKUP},
            'Both immutable asset trees must have been verified')
    for r in blobs['archives']:
        require(r['asset_commit'] == ready['asset_commit'] and
                r['all_remote_Git_blob_modes_sizes_SHA_exact'] is True and
                r['record_subtree'] == ready['video_tree_sha'] and
                r['files'] == ready['archive_file_count'] > 0,
                'Actual complete dual asset proof is missing')
    require(blobs['actual_dual_blob_rows'] == 2*ready['archive_file_count'],
            'The complete two-repository asset verification is required')


def normalize_review_ready(handoff_path, dual_ready_path, registry_path):
    """Read the real archivist output and derive the compiler receipt, without writes."""
    hp, dp = Path(handoff_path).resolve(), Path(dual_ready_path).resolve()
    h, original = load_exact(hp), load_exact(dp)
    for key in ('review_only','preview_only','preview_delivery_eligible',
                'actual_dual_permanent_archive_passed'):
        require(original[key] is True, 'Archival ready must already have real review-only status')
    for key in ('production_delivery_eligible','final_user_acceptance',
                'active_final_replacement_authorized'):
        require(original[key] is False, 'Do not convert an active-final operation into a preview')
    require(original['real_V3_handoff_sha256'] == spec(hp)['sha256'],
            'Real archival receipt must bind this exact V3 handoff')
    a = h['articles'][0]; sid, book = a['source_id'],a['new_id']
    require(len(h['articles']) == 1 and original['source_id'] == sid and
            original['frozen_book_order'] == book and original['current_video_order'] == book,
            'Wrong immutable archive-ready article')
    def meta(name):
        value = original['metadata_files'][name]
        return Path(value if isinstance(value,str) else value['path']).resolve()
    prepared = load_exact(meta('prepared-archive.json'))
    primary, backup = (load_exact(meta(n)) for n in ('assets-primary.json','assets-backup.json'))
    require(primary['asset_commit'] == backup['asset_commit'] == original['asset_commit'] and
            primary['video_tree_sha'] == backup['video_tree_sha'] == original['video_tree_sha'] and
            primary['files_index'] == backup['files_index'], 'Two actual asset archives differ')
    rp, qp = Path(a['validated_record']).resolve(), Path(a['section']['qc']['path']).resolve()
    metadata = {'handoff':hp,'validated_record':rp,'qc':qp,
                'remote_video_bytes':meta('remote-video-byte-verification.json'),
                'dual_asset_blobs':meta('actual-dual-asset-blob-verification.json')}
    evidence = {}
    for key,p in [('handoff',hp),('validated_record',rp),('qc',qp)]:
        expected = spec(p)
        matches = [r for r in prepared['material_source_bindings']
                   if Path(r['original_path']).resolve() == p and
                   (r['bytes'],r['sha256']) == (expected['bytes'],expected['sha256'])]
        require(matches, 'Actual V3 proof must already be in the permanent asset tree')
        evidence[key] = {'repo_path':matches[0]['repo_path'],
                         'bytes':expected['bytes'],'sha256':expected['sha256']}
    normalized = {key:deepcopy(original[key]) for key in
                  ('source_id','frozen_book_order','current_video_order','asset_commit',
                   'video_tree_sha','video_repo_path','bytes','sha256','real_V3_handoff_sha256')}
    normalized.update(kind='user102-actual-dual-archived-latest-review-only-ready',
        review_only=True,preview_only=True,preview_delivery_eligible=True,
        actual_dual_permanent_archive_passed=True,production_delivery_eligible=False,
        final_user_acceptance=False,active_final_replacement_authorized=False,
        archive_file_count=len(primary['files_index']),
        metadata_files={k:spec(v) for k,v in metadata.items()},archived_evidence=evidence)
    validate_dual_proofs(normalized,{k:load_exact(p) for k,p in metadata.items()})
    e = registry_rows(load_exact(registry_path))[sid]
    require(not e.get('newest_user_revision_records') and
            not e.get('final_4K_generation_authorized') and
            not e.get('latest_finalization_authority'),
            'An individual final cannot be normalized as a review-only shortcut')
    test_row = row_base(sid,e);test_row.update(media_identity(normalized))
    test_row.update(qualification='verified_latest_review_only',
        individual_user_final_acceptance=False,production_delivery_eligible=False,
        active_final_replacement_authorized=False,actual_dual_permanent_archive_passed=True,
        specific_review_authorization_id='102',source_run=h['source_run'],evidence=evidence,
        tail_policy='preserved_existing_source30' if sid=='30' else 'actual_normal18')
    validate_review_documents(test_row,{k:load_exact(metadata[k]) for k in
                                      ('handoff','validated_record','qc')})
    return normalized


def review_candidate(ready_path, e):
    ready = load_exact(ready_path)
    sid = ready['source_id']
    require(ready['kind'] == 'user102-actual-dual-archived-latest-review-only-ready',
            'A purpose-specific actual review-ready receipt is required')
    require(ready['frozen_book_order'] == e['frozen_book_order'] and
            ready['current_video_order'] == e['current_video_order'],
            'Review receipt has the wrong book/order')
    for key in ('review_only', 'preview_only', 'preview_delivery_eligible',
                'actual_dual_permanent_archive_passed'):
        require(ready[key] is True, 'Review receipt must preserve qualified preview status')
    for key in ('production_delivery_eligible', 'final_user_acceptance',
                'active_final_replacement_authorized'):
        require(ready[key] is False, 'The review receipt must not promote an active final')
    require(set(ready['metadata_files']) ==
            {'handoff', 'validated_record', 'qc', 'remote_video_bytes', 'dual_asset_blobs'},
            'The five actual metadata files must be explicit')
    docs = {k: load_exact(v['path'], v) for k, v in ready['metadata_files'].items()}
    require(spec(ready['metadata_files']['handoff']['path'])['sha256'] ==
            ready['real_V3_handoff_sha256'], 'Wrong actual complete V3 handoff')
    require(set(ready['archived_evidence']) == {'handoff', 'validated_record', 'qc'},
            'Archive all three actual V3 documents before compiling')
    for key, remote in ready['archived_evidence'].items():
        local = ready['metadata_files'][key]
        require((remote['bytes'], remote['sha256']) == (local['bytes'], local['sha256']),
                'Archived evidence differs from the real local V3 document')
        safe_path(remote['repo_path'], '.json')
    row = row_base(sid, e)
    row.update(media_identity(ready))
    row.update(qualification='verified_latest_review_only',
               individual_user_final_acceptance=False, production_delivery_eligible=False,
               active_final_replacement_authorized=False,
               actual_dual_permanent_archive_passed=True,
               specific_review_authorization_id='102',
               source_run=docs['handoff']['source_run'],
               evidence=deepcopy(ready['archived_evidence']),
               tail_policy='preserved_existing_source30' if sid == '30' else 'actual_normal18')
    validate_dual_proofs(ready, docs)
    validate_review_documents(row, docs)
    return row, {k: docs[k] for k in ('handoff', 'validated_record', 'qc')}


def compile_input(input_path):
    inputs = load_exact(input_path)
    require(inputs['kind'] == 'latest38-70-user102-publication-inputs-not-a-manifest',
            'Do not feed the obsolete mixed review manifest')
    inventory_raw = Path(inputs['inventory_local_path']).read_bytes()
    registry_raw = Path(inputs['latest_requests_local_path']).read_bytes()
    mapping_raw = Path(inputs['frozen_mapping_local_path']).read_bytes()
    require(sha_bytes(mapping_raw) == FROZEN_MAPPING_SHA256, 'Frozen source/book map changed')
    inventory, registry, mapping = map(json.loads, (inventory_raw, registry_raw, mapping_raw))
    byid = validate_mapping(registry, mapping)
    eligible = eligible_final_ids(inventory, registry)
    current = {r['source_id']: r for r in inventory['articles']}
    review_paths = {}
    for path in inputs['review_ready_files']:
        r = load_exact(path)
        sid = r['source_id']
        require(sid not in review_paths, 'Duplicate review-ready receipt')
        review_paths[sid] = path
    require(set(review_paths) <= set(SOURCES), 'Extra or source65 review receipt is forbidden')
    videos, review_docs, missing = [], {}, []
    for book, sid in zip(BOOKS, SOURCES):
        e = byid[sid]
        if sid in eligible:
            require(sid not in review_paths, 'A current final and review must not compete')
            c = current[sid]
            require(c.get('preview_only', False) is False and
                    c.get('production_delivery_eligible', True) is True,
                    'Preview media must not be relabeled in the current index')
            row = row_base(sid, e)
            row.update(media_identity(c))
            row.update(qualification='current_verified_final',
                       individual_user_final_acceptance=bool(
                           e.get('latest_requested_revision_complete') and
                           e.get('final_4K_generation_authorized')),
                       production_delivery_eligible=True,
                       current_archive_source_run_if_recorded=c.get('source_run'),
                       tail_policy=('actual_normal18' if c.get('post_reading_pause_seconds') == .6
                                    else 'preserved_current_final'),
                       actual_dual_permanent_archive_passed=True)
            videos.append(row)
        elif sid in review_paths:
            require(sid not in current and not e.get('newest_user_revision_records') and
                    not e.get('final_4K_generation_authorized') and
                    not e.get('latest_finalization_authority'),
                    'A pending final cannot be replaced by a review-only shortcut')
            row, docs = review_candidate(review_paths[sid], e)
            videos.append(row); review_docs[sid] = docs
        else:
            missing.append({'source_id': sid, 'book_order': book, 'title_zh': e['title_zh'],
                            'status': e['status'],
                            'latest_user_records': e.get('newest_user_revision_records', []),
                            'reason': ('pending_new_final_must_complete_current_archive' if
                                       e.get('final_4K_generation_authorized') or
                                       e.get('newest_user_revision_records') else
                                       'actual_review_V3_plus_dual_ready_binding_not_supplied')})
    status = {'kind': 'actual-local-latest33-preparation-status-not-a-release',
              'requested_count': 33,
              'qualified_current_final_count': sum(
                  r['qualification']=='current_verified_final' for r in videos),
              'qualified_review_only_count': sum(
                  r['qualification']=='verified_latest_review_only' for r in videos),
              'qualified_total_count':len(videos),
              'missing_count': len(missing), 'missing': missing,
              'missing_means_binding_not_supplied_not_no_newer_file_generated':True,
              'complete_manifest_built': False, 'remote_mutation_or_publication': False}
    if missing:
        return None, status
    snapshot = {'primary_commit': commit40(inputs['primary_snapshot_commit']),
                'backup_commit': commit40(inputs['backup_snapshot_commit']),
                'inventory': {'repo_path': INVENTORY_PATH, 'bytes': len(inventory_raw),
                              'sha256': sha_bytes(inventory_raw)},
                'latest_requests': {'repo_path': REGISTRY_PATH, 'bytes': len(registry_raw),
                                    'sha256': sha_bytes(registry_raw)}}
    manifest = {'kind': 'latest-complete-books38-70-user102-review-release-v2',
                'specific_user_review_authorization': '102',
                'requested_book_range': ['38','70'], 'requested_video_count': 33,
                'actual_available_video_count': 33, 'requested_video_range_complete': True,
                'all33_actual_full_V3_quality_qualified': True,
                'all33_individually_finalized_by_user_claimed': False,
                'uniform_0_6_second_tail_claimed_for_this_release': False,
                'old_mixed_or_legacy_fallback_allowed': False,
                'current_final_aliases_changed_by_publisher': False,
                'media_reencoded_or_audio_changed_by_publisher': False,
                'release_tag': TAG, 'zip_name': ZIP_NAME, 'release_prerelease': True,
                'release_title': '考研学人｜第38—70篇｜33篇最新4K审核视频',
                'release_body': (
                    '第38—70篇，共33篇本次最新、已完成实际完整质量核验的视频，供逐篇审核。'
                    '有新修改的篇目采用修订后的文件；不使用旧混合包或未通过完整核验的历史视频补齐。\n\n'
                    '本包包含已定稿文件及已核查、仍待用户逐篇定稿的审核文件。审核文件不进入“最新定稿视频”目录。'
                    '新生成审核视频末句读完后保留约0.6秒，再展示插图2秒及简述2秒；'
                    '复用的已核查旧成片保留其原尾段，逐篇版本和尾段方式见包内清单。\n\n'
                    '最新定稿目录：https://github.com/' + PRIMARY +
                    '/tree/main/视频修订定稿/最终定稿/视频'),
                'snapshot': snapshot, 'source_frozen_mapping_sha256': FROZEN_MAPPING_SHA256,
                'videos': videos, 'total_video_bytes': sum(r['bytes'] for r in videos),
                'individual_user_finalized_count': sum(
                    r['individual_user_final_acceptance'] for r in videos),
                'review_only_count': sum(
                    r['qualification'] == 'verified_latest_review_only' for r in videos),
                'publisher_program_sha256s': {name: spec(HERE/name)['sha256'] for name in PROGRAMS},
                'compiled_utc': datetime.datetime.now(datetime.timezone.utc).isoformat()}
    validate_manifest(manifest)
    validate_actual_selection(manifest, inventory, registry, review_docs)
    status.update(complete_manifest_built=True, missing_count=0)
    return manifest, status


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--inputs', type=Path)
    p.add_argument('--normalize-review-ready', action='store_true')
    p.add_argument('--handoff', type=Path)
    p.add_argument('--dual-ready', type=Path)
    p.add_argument('--latest-requests', type=Path)
    p.add_argument('--status-only', action='store_true')
    p.add_argument('--output', type=Path, default=HERE/'MANIFEST.json')
    args = p.parse_args()
    if args.normalize_review_ready:
        require(args.inputs is None and args.handoff is not None and args.dual_ready is not None and
                args.latest_requests is not None,
                'Use only the real handoff and actual dual-ready for normalization')
        ready = normalize_review_ready(args.handoff,args.dual_ready,args.latest_requests)
        raw = (json.dumps(ready,ensure_ascii=False,indent=2)+'\n').encode()
        require(args.output.name != 'MANIFEST.json', 'A ready receipt is not a publication manifest')
        require(not args.output.exists() or args.output.read_bytes()==raw,
                'Do not overwrite a different archived-ready receipt')
        args.output.write_bytes(raw)
        print(json.dumps({'review_ready':str(args.output),'bytes':len(raw),'sha256':sha_bytes(raw),
                          'no_remote_mutation':True}))
        return
    require(args.inputs is not None and args.handoff is None and args.dual_ready is None and
            args.latest_requests is None,
            'Compiling requires explicit actual latest inputs')
    manifest, status = compile_input(args.inputs)
    report = HERE/'ACTUAL-PREPARATION-STATUS.json'
    report.write_text(json.dumps(status, ensure_ascii=False, indent=2)+'\n')
    if args.status_only or manifest is None:
        print(json.dumps(status, ensure_ascii=False))
        if manifest is None and not args.status_only:
            raise SystemExit('Incomplete latest33 set: no MANIFEST.json was created')
        return
    raw = (json.dumps(manifest, ensure_ascii=False, indent=2)+'\n').encode()
    if args.output.exists():
        require(args.output.read_bytes() == raw, 'Never overwrite a frozen actual manifest')
    else:
        args.output.write_bytes(raw)
    print(json.dumps({'manifest': str(args.output), 'bytes': len(raw),
                      'sha256': sha_bytes(raw), 'remote_mutation': False}))


if __name__ == '__main__':
    main()
