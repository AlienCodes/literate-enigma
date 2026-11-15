"""Strict final-only contract; no network, media processing, or publication here."""
from copy import deepcopy
import hashlib
import json
import math
from pathlib import PurePosixPath
import re

PRIMARY = 'alienalgorithm/postgraduate-vocabulary'
BACKUP = 'AlienCodes/literate-enigma'
BRANCHES = {PRIMARY: 'main', BACKUP: 'codex/all-deliverables-20261113'}
TAG = 'all70-latest-final-4k-hold06-v1'
ZIP_NAME = '01-70-LATEST-4K-FINAL.zip'
INVENTORY = '视频修订定稿/已归档视频总清单.json'
REGISTRY = '视频修订定稿/latest_requests.json'
ALIASES = '视频修订定稿/最终定稿/视频/'
AUTH_SHA = '55285b58c86b066692f3d6ac7e5a0d4e5e1f5d0977d597c2fd51d6b886bd1be7'
LIMIT = 2 * 1024**3
ORDER_AUTHORITY_SHA = '3120efc6893981436cb81458ce57f6aca7601edc5e7326cce1388b68de959001'
SOURCE_ORDER = ['07', '01', '12', '10', '22', '06', '11', '39', '21', '51', '03', '05', '04', '55', '44', '50', '20', '02', '49', '42', '14', '27', '13', '61', '15', '17', '26', '36', '28', '33', '67', '47', '34', '62', '53', '60', '65', '19', '29', '43', '52', '48', '37', '31', '16', '40', '54', '46', '24', '70', '38', '09', '68', '35', '30', '69', '66', '08', '63', '32', '57', '23', '64', '18', '56', '41', '58', '25', '59', '45']

# Exact existing source-proof ABIs, independently read from their immutable dual
# archives. This recognizes old schema names, not arbitrary same-status proofs.
LEGACY_SOURCE_STATUS = {
    '25': ('27c9cfb3e050163d697febed2a3560327f02333ed6154db11af9129c6fde1d68', 'passed_actual_one_article_section_for_permanent_archive'),
    '45': ('9f762e30c9ebdf61d38cc369ae5127b3c978e7d758717d2c909bd5a27465e0af', 'passed_actual_one_article_section_for_permanent_archive'),
    '12': ('96f69fd842aba0f92745b773413b9cbde539d12353eb65b51462c47385ab18b2', 'passed_genuine_canonical_quality_and_actual_missing_art_recovery_for_permanent_archive'),
    '10': ('d16c4a7fd05f533e4b1365eefd666dcccf8271eecc8c2b70d0d969a7c2c6e0c0', 'passed_genuine_canonical_quality_and_actual_missing_art_recovery_for_permanent_archive'),
    '51': ('50d8432bb395fda33e813c508ef92cdc047d91ba83b6e180184a93ef16871ab6', 'passed_genuine_canonical_quality_and_actual_missing_art_recovery_for_permanent_archive'),
    '11': ('bf50a41b7c4c5984bae3fc734d074f2483c770ee266c2d21762e12500ff85ad6', 'passed_genuine_canonical_quality_and_actual_missing_art_recovery_for_permanent_archive'),
    '42': ('d51ca8d72a498ef650b5f91d86a639693ac44d43b2bc89929f8e8d5a9ac46c69', 'passed_genuine_canonical_quality_and_actual_missing_art_recovery_for_permanent_archive'),
    '39': ('e00dae8f306af1288466b1c5f176bcba82e258e8f8d2ca03a3d4159023d41afd', 'passed_actual_one_article_section_for_permanent_archive'),
    '50': ('d87ead008a58c435d75b5a7078295a31d7ad3a9f3f1529ff1563cf3e62f90f35', 'passed_actual_one_article_section_for_permanent_archive'),
    '29': ('5182f5abb510246822e7267dd7cc463960396220c324d9e55e29372e11a159c9', 'passed_actual_one_article_section_for_permanent_archive'),
    '31': ('9a461a42861364201f3b8b7eedb61522b2dfceebf46287299f33ad32fed730a9', 'passed_actual_one_article_section_for_permanent_archive'),
}
EXISTING28_STATUS = 'passed_actual_existing18_media_adopted_under_explicit_first34_scope057'
EXISTING28_PROOFS = {
    'handoff': '8aa9ff04e6ae659326d4269334aa870f14ff1e380f1dc0408ebb45d960850fbe',
    'record': '184128200d780fb2658ef3549e94dbdc139fd6bd99fd342230192ce656098f05',
    'qc': 'b9d993b1e4afea72851127dca9c1864a1d1dc3d93205300e46c898f38b5d2f24',
    'source_handoff': '0a6132afd529dddd8425a84253b15e823af9b55360895b1dcb61428abf1b5423',
    'source_qc': '86ed0f8348485ce79ec911708567f05375946afd21837319ff6165704a0399b8',
    'scope_authority': '3c91671ad6dcc1e30f6336efa394eac1ff776c8405157b924f2e86f64266284a',
    'reuse_authority': '307da9d1bdda2a652caa8138cb68e35d7e1970acfcd591d15aa70d842c381b17',
    'preview18_handoff': '9a8718c1ce2d62f4017d7a7adb55e5a87bb5a61209ad3d806864514e0a663860',
    'preview18_qc': 'e37e9c02fb92eba3a9b913d2a435ba4d258693838a465c14b1681ffab26a7953',
}

def existing28_role(video):
    return (video['source_id'] == '28' and
            video['evidence']['handoff']['sha256'] == EXISTING28_PROOFS['handoff'])

def validate_existing28_adoption(video, docs):
    """Existing media adopted under057; the old native preview stays a preview."""
    need(existing28_role(video) and video['frozen_book_order'] == '29', 'Wrong existing28 adoption scope')
    need(set(docs) == set(EXISTING28_PROOFS) and set(video['evidence']) == set(EXISTING28_PROOFS) and
         all(video['evidence'][k]['sha256'] == v for k,v in EXISTING28_PROOFS.items()),
         'All nine exact archived adoption, authority and physical quality proofs are required')
    h, q, old, oldq, source = [docs[k] for k in ['handoff','qc','preview18_handoff','preview18_qc','source_handoff']]
    need(h['status'] == EXISTING28_STATUS and h['active_final_replacement_authorized'] is True and
         h['first34_uniform_timing_installation_eligible'] is True and
         h['new_tail_or_audio_processing_claimed'] is False and h['new_native_job_or_TTS_claimed'] is False,
         'Current adopted media is not actually authorized under057')
    need(h['current_scope_authority']['sha256'] == EXISTING28_PROOFS['scope_authority'] and
         h['reuse_authority']['sha256'] == EXISTING28_PROOFS['reuse_authority'] and
         h['inherited_exact_preview_handoff']['sha256'] == EXISTING28_PROOFS['preview18_handoff'] and
         q['inherited_full_V3_handoff']['sha256'] == EXISTING28_PROOFS['source_handoff'],
         'Adoption authority or inherited physical source binding changed')
    reuse = docs['reuse_authority']
    need(reuse['source_id'] == '28' and reuse['new_id'] == '29' and
         reuse['authority']['sha256'] == EXISTING28_PROOFS['scope_authority'] and
         reuse['current_uniform_timing_installation_authorized'] is True and
         reuse['all_old_preview_flags_and_original_QA_bytes_preserved'] is True and
         reuse['new_native_TTS_render_tail_or_audio_processing_performed'] is False,
         'Existing28 reuse receipt does not authorize these unchanged bytes')
    need(old['status'] == 'passed_actual_post_only_hold18_preview28_for_user_review_only' and
         source['status'] == 'passed_actual_native_preview28_for_user_review_only',
         'Do not relabel historical previews as newly passed native finals')
    for prior in [old, source]:
        need(prior['preview_only'] is True and prior['production_delivery_eligible'] is False and
             len(prior['articles']) == 1 and prior['articles'][0]['passed_per_article'] is False,
             'Historical preview classification was changed')
    for priorq in [oldq, docs['source_qc']]:
        need(priorq['status'] == 'passed' and priorq['preview_only'] is True and
             priorq['production_delivery_eligible'] is False, 'Historical physical QC is not genuine')
    need(all(q[k] == oldq[k] for k in ['audio','actual_probe','speech_end','illustration','summary']) and
         old['articles'][0]['section']['qc']['sha256'] == EXISTING28_PROOFS['preview18_qc'] and
         (old['articles'][0]['preview_mp4']['bytes'],old['articles'][0]['preview_mp4']['sha256']) ==
         (video['bytes'],video['sha256']), 'The adopted original media or physical quality changed')
    return True

class GuardError(ValueError):
    pass

def need(value, message):
    if not value:
        raise GuardError(message)

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def git_blob(raw):
    return hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()

def hash64(value):
    need(isinstance(value, str) and re.fullmatch('[0-9a-f]{64}', value), 'Invalid SHA256')
    return value

def commit40(value):
    need(isinstance(value, str) and re.fullmatch('[0-9a-f]{40}', value), 'Invalid Git identity')
    return value

def safe_path(value, suffix=None):
    need(isinstance(value, str) and not value.startswith('/') and
         '\\' not in value and '..' not in PurePosixPath(value).parts,
         'Unsafe repository/file path')
    if suffix:
        need(value.endswith(suffix), 'Unexpected path suffix')
    return value

def rows_by_source(registry):
    rows = registry['articles']
    need(len(rows) == 70 and len({x['source_id'] for x in rows}) == 70,
         'Exactly70 unique request entries are required')
    need({x['current_video_order'] for x in rows} == {f'{n:02}' for n in range(1, 71)},
         'Current video order must be exactly01 through70')
    return {x['source_id']: x for x in rows}

def eligibility(inventory, registry):
    requests = rows_by_source(registry)
    current = {x['source_id']: x for x in inventory['articles']}
    need(len(current) == len(inventory['articles']), 'Duplicate current source')
    pending = []
    for e in sorted(requests.values(), key=lambda x: int(x['current_video_order'])):
        c = current.get(e['source_id'])
        reasons = []
        for key in ['latest_requested_revision_complete', 'actual_complete_validation_passed',
                    'actual_dual_permanent_archive_passed']:
            if e.get(key) is not True:
                reasons.append(key)
        if c is None:
            reasons.append('no_actual_current_accepted_row')
        elif c.get('passed_per_article') is not True or c.get('preview_only', False) is not False:
            reasons.append('not_actual_final')
        elif c.get('production_delivery_eligible', True) is not True:
            reasons.append('not_production_eligible')
        if c is not None and e.get('latest_revision_final'):
            if any(c.get(k) != e['latest_revision_final'].get(k)
                   for k in ['asset_commit', 'video_repo_path', 'bytes', 'sha256']):
                reasons.append('latest_request_media_identity_mismatch')
        elif c is not None:
            reasons.append('no_qualified_latest_revision_identity')
        if reasons:
            pending.append({'video_order': e['current_video_order'], 'source_id': e['source_id'],
                            'title_zh': e['title_zh'], 'reasons': reasons})
    actual = sum(e.get('latest_requested_revision_complete') is True for e in requests.values())
    need(registry['latest_requested_revision_completed_count'] == actual,
         'Registry completion count does not equal its actual rows')
    return {'eligible': not pending and len(current) == 70 and
            inventory['archived_passed_count'] == 70 and registry['all70_latest_complete'] is True,
            'actual_current_accepted_count': len(current),
            'actual_latest_request_complete_count': actual, 'pending': pending}

def require_all70(inventory, registry):
    status = eligibility(inventory, registry)
    need(status['eligible'], 'All70 actual latest requests and cloud archives are not complete')
    order = inventory['video_order_overlay']['video_order']
    need(len(order) == 70 and inventory['video_order_overlay']['authority_review_sha256'] == ORDER_AUTHORITY_SHA and
         [x['source_id'] for x in order] == SOURCE_ORDER, 'Missing or changed current090 video order')
    request = rows_by_source(registry)
    need({(x['source_id'], x['video_order'], x['frozen_book_order']) for x in order} ==
         {(x['source_id'], x['current_video_order'], x['frozen_book_order'])
          for x in request.values()}, '090 overlay and actual request mapping differ')
    return request, {x['source_id']: x for x in inventory['articles']}

def media_identity(row):
    return tuple(row[k] for k in ['asset_commit', 'video_repo_path', 'bytes', 'sha256'])

def validate_tail(record):
    p, t = record['actual_probe'], record['tail']
    need((p['width'], p['height'], p['fps']) == (3840, 2160, '30/1'), 'Not actual4K30')
    need(t['extra_body_hold_frames'] == 18 and t['illustration_frames'] == t['summary_frames'] == 60,
         'Need actual18 hold plus60 illustration and60 summary frames')
    need(t['speech_end_frame'] == math.ceil(t['voice_endpoint_seconds'] * 30), 'Voice ceiling mismatch')
    need(t['held_body_end_frame'] == t['illustration_start_frame'] == t['speech_end_frame'] + 18,
         'Hold or illustration boundary mismatch')
    need(t['summary_start_frame'] == t['illustration_start_frame'] + 60 and
         t['output_frames'] == t['summary_start_frame'] + 60 == p['frames'],
         'Tail frame count mismatch')
    gap = t['illustration_start_frame'] / 30 - t['voice_endpoint_seconds']
    actual_gap = t['voice_to_illustration_gap_seconds']
    need(.6 <= actual_gap < .633334 and abs(gap - actual_gap) < 1e-8,
         'Actual post-voice gap is outside the original normal18 contract')
    a = record['actual_audio_chain']
    hash64(a['aac_adts_sha256']); hash64(a['packet_projection_sha256'])
    need(type(a['packet_count']) is int and a['packet_count'] > 0, 'Missing accepted audio chain')
    return p, t

def validate_documents(video, docs):
    h, r, q, source, sourceq = [docs[k] for k in ['handoff', 'record', 'qc', 'source_handoff', 'source_qc']]
    adopted28 = validate_existing28_adoption(video, docs) if existing28_role(video) else False
    legacy_source = LEGACY_SOURCE_STATUS.get(video['source_id']) == (
        video['evidence']['source_handoff']['sha256'], source['status'])
    need((h['status'] == 'passed_actual_normal18_post_only_for_permanent_archive' or adopted28) and
         h['production_delivery_eligible'] is True and h['preview_only'] is False,
         'An actual accepted normal18 fullV3 handoff is required')
    need((h.get('local_postprocessing_only') is True or adopted28) and h['new_native_job_or_TTS_claimed'] is False,
         'Do not invent a new native/TTS run for the tail')
    need(len(h['articles']) == 1, 'Wrong final handoff scope')
    a = h['articles'][0]
    need(a['source_id'] == video['source_id'] and a['new_id'] == video['frozen_book_order'] and
         a['passed_per_article'] is True, 'Frozen quality identity differs from current video order')
    need((a['final_mp4']['bytes'], a['final_mp4']['sha256']) == (video['bytes'], video['sha256']),
         'The real final handoff points to different MP4 bytes')
    need(r['id'] == video['source_id'] and r['new_id'] == video['frozen_book_order'] and
         r['production_delivery_eligible'] is True and r['preview_only'] is False and
         (r['bytes'], r['sha256']) == (video['bytes'], video['sha256']), 'Wrong actual final record')
    p, t = validate_tail(r)
    need(p == video['actual_probe'] and t == video['validated_tail'], 'Manifest changes actual probe/tail')
    need(q['status'] == 'passed' and q['article'] == video['source_id'] and
         (q['video_bytes'], q['video_sha256']) == (video['bytes'],video['sha256']) and
         q['production_delivery_eligible'] is True and q['preview_only'] is False and
         (source['status'] == 'passed_actual_native_inline_article_for_permanent_archive' or legacy_source or adopted28),
         'Actual final/source full quality proof is missing')
    need(len(source['articles']) == 1 and source['articles'][0]['source_id'] == video['source_id'] and
         source['articles'][0]['new_id'] == video['frozen_book_order'] and
         (source['articles'][0]['passed_per_article'] is True or adopted28), 'A preview source cannot replace final sourceQA')
    need((source.get('preview_only', False) is False or adopted28) and sourceq['status'] == 'passed', 'Source is not accepted')
    source_spec = q['inherited_full_V3_handoff'] if adopted28 else h.get('current_source_validation_handoff', h.get('inherited_full_V3'))
    need(source_spec and source_spec['sha256'] == video['evidence']['source_handoff']['sha256'],
         'Final handoff does not inherit this exact qualified source')
    need(a['section']['qc']['sha256'] == video['evidence']['qc']['sha256'] and
         source['articles'][0]['section']['qc']['sha256'] == video['evidence']['source_qc']['sha256'],
         'QC role/identity mismatch')
    need(type(sourceq['audio']['repair_applied']) is bool, 'Unknown original audio repair role')
    if sourceq['audio']['repair_applied']:
        repair = sourceq['audio']['controlled_repair']
        need(repair['status'] == 'passed' and repair['actual_new_output'] is True, 'Unqualified audio repair')
    chain, accepted = r['actual_audio_chain'], sourceq['audio']['lossless_copy']
    need(chain['aac_adts_sha256'] == accepted['canonical_aac_adts_sha256'] and
         chain['packet_projection_sha256'] == accepted['canonical_packet_projection_sha256'] and
         chain['packet_count'] == accepted['canonical_packet_count'], 'Accepted full AAC/clock identity changed')
    return True

def validate_video(v):
    need(v['qualification'] == 'current_verified_latest_final' and v['actual_complete_validation_passed'] is True and
         v['actual_dual_permanent_archive_passed'] is True and v['production_delivery_eligible'] is True and
         v['preview_only'] is False, 'A review or old final cannot enter this release')
    need(v['release_name'] == v['current_video_order'] + ' ' + v['title_zh'] + '.mp4' and
         PurePosixPath(v['release_name']).name == v['release_name'], 'Wrong current090 filename')
    need(v['canonical_alias_path'] == ALIASES + v['release_name'], 'Not the unique latest alias')
    need(v['video_repo_path'].startswith('视频修订定稿/'), 'Wrong immutable video scope')
    safe_path(v['video_repo_path'], '.mp4'); commit40(v['asset_commit']); commit40(v['alias_git_blob_sha']); hash64(v['sha256'])
    need(type(v['bytes']) is int and v['bytes'] > 0, 'Invalid final size')
    need(v['end_reading_pause_seconds'] == .6 and v['nominal_extra_hold_frames_at_30fps'] == 18,
         'Wrong final timing policy')
    for x in v['evidence'].values():
        need(x['repo_path'].startswith('视频修订定稿/'), 'Wrong archived evidence scope')
        safe_path(x['repo_path'], '.json'); hash64(x['sha256'])
        need(type(x['bytes']) is int and 0 < x['bytes'] <= 2_000_000, 'Invalid small proof size')
    roles = set(EXISTING28_PROOFS) if existing28_role(v) else {'handoff', 'record', 'qc', 'source_handoff', 'source_qc'}
    need(set(v['evidence']) == roles, 'Exact archived quality roles required')
    need(v['evidence']['handoff']['sha256'] == v['validation_handoff_sha256'], 'Wrong current final handoff')

def validate_manifest(config):
    need(config['kind'] == 'all70-actually-complete-latest-final-release-manifest' and
         config['tag'] == TAG and config['actual_all70_latest_qualified_and_dual_archived'] is True,
         'Not a completed all70 final manifest')
    need(config['actual_release_authority_sha256'] == AUTH_SHA, 'Wrong actual conditional user authority')
    need(set(config['snapshots']) == {PRIMARY, BACKUP}, 'Both canonical repositories required')
    for repo, s in config['snapshots'].items():
        need(s['branch'] == BRANCHES[repo], 'Wrong protected canonical branch')
        commit40(s['head']); commit40(s['alias_tree_sha'])
        for n in ['inventory', 'registry']:
            hash64(s[n]['sha256']); commit40(s[n]['git_blob_sha'])
            need(type(s[n]['bytes']) is int and s[n]['bytes'] > 0, 'Invalid canonical snapshot bytes')
    need(config['snapshots'][PRIMARY]['inventory'] == config['snapshots'][BACKUP]['inventory'] and
         config['snapshots'][PRIMARY]['registry'] == config['snapshots'][BACKUP]['registry'] and
         config['snapshots'][PRIMARY]['alias_tree_sha'] == config['snapshots'][BACKUP]['alias_tree_sha'],
         'Two actual current snapshots differ')
    videos = config['videos']
    need(len(videos) == 70 and len({v['source_id'] for v in videos}) == 70 and
         [v['current_video_order'] for v in videos] == [f'{n:02}' for n in range(1, 71)],
         'Exactly70 current video orders required')
    need([v['source_id'] for v in videos] == SOURCE_ORDER, 'Source IDs do not follow the actual090 video order')
    for v in videos:
        validate_video(v)
    need(sum(v['bytes'] for v in videos) == config['total_MP4_bytes'], 'Wrong total size')
    return videos

def inner_lists(all_videos, members, part_number, part_count):
    public_rows = [{k:v[k] for k in ['source_id','current_video_order','release_name','bytes','sha256']}
                   for v in all_videos]
    metadata = {'kind':'all70-latest-final-MP4-integrity-list','all70_video_count':70,
                'videos':public_rows, 'MP4_bytes_preserved_without_reencoding':True,
                'nominal_post_reading_pause_seconds':.6,'part_number':part_number,'part_count':part_count,
                'this_part_files':[v['release_name'] for v in members]}
    manifest = (json.dumps(metadata,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
    checksums = ''.join(v['sha256']+'  '+v['release_name']+'\n' for v in all_videos).encode()
    return manifest, checksums

def exact_stored_zip_bytes(members, all_videos, part_number=1, part_count=1):
    """No ZIP comment/extra/descriptor: seekable ZIP_STORED local30+central46+names."""
    manifest, checksums = inner_lists(all_videos,members,part_number,part_count)
    entries = [(v['release_name'],v['bytes']) for v in members] + [
        ('MANIFEST.json',len(manifest)),('SHA256SUMS.txt',len(checksums))]
    need(all(len(name.encode('utf-8')) <= 65535 for name,_ in entries), 'ZIP filename is too long')
    return 22 + sum(size + 76 + 2*len(name.encode('utf-8')) for name,size in entries)

def archive_parts(videos):
    """Prefer the actual exact single ZIP; split only when that exact result cannot fit."""
    if exact_stored_zip_bytes(videos,videos) < LIMIT:
        return [videos]
    parts, current = [], []
    for v in videos:
        #70 is a two-digit upper bound for actual part IDs/count, not a guessed MB reserve.
        need(exact_stored_zip_bytes([v],videos,70,70) < LIMIT, 'One MP4 exceeds a Release asset budget')
        if current and exact_stored_zip_bytes(current+[v],videos,70,70) >= LIMIT:
            parts.append(current); current = []
        current.append(v)
    if current:
        parts.append(current)
    return parts
