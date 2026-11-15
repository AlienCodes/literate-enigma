"""Bind actual canonical snapshots and already dual-archived fullV3 proof files."""
import argparse
import datetime
import json
from pathlib import Path
import urllib.parse
import urllib.request

from all70_contract import *

# These three existing accepted normal18 rows predate the inventory's redundant
# postprocessing-H field. Their real H is already pinned by latest_requests and
# the immutable dual archive; do not edit historical canonical rows to add it.
LEGACY_CURRENT_FINAL_H = {
    '17': '1a2553945daf42b14ef36b8d3345050b7b5a366e0b47ce2b9f061fcc854f1e5a',
    '36': '01ec2636a3e3ae3df2c05661c44b31e34ab669cc77878d2de11eb282fda0f3da',
    '33': '147dfe1469ea1f5c6057398b96fe92ab549c2e3d39a1cd105a711ffab23752f8',
}

def load(path):
    return json.loads(Path(path).read_bytes())

def spec(path):
    raw = Path(path).read_bytes()
    return {'bytes': len(raw), 'sha256': sha(raw), 'git_blob_sha': git_blob(raw)}

def write(path, value):
    path = Path(path)
    need(not path.exists(), 'Do not overwrite a frozen publication input')
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')

def public_json(repo, path):
    q = urllib.request.Request('https://api.github.com/repos/' + repo + '/' +
        urllib.parse.quote(path, safe='/?=&'), headers={'User-Agent': 'all70-exact-canonical-snapshot'})
    with urllib.request.urlopen(q, timeout=90) as response:
        need(response.status == 200, 'Canonical public API read failed')
        return json.loads(response.read())

def public_raw(repo, commit, path):
    safe_path(path)
    q = urllib.request.Request('https://raw.githubusercontent.com/' + repo + '/' + commit + '/' +
        urllib.parse.quote(path, safe='/'), headers={'User-Agent': 'all70-exact-canonical-JSON-readback'})
    with urllib.request.urlopen(q, timeout=90) as response:
        need(response.status == 200, 'Canonical raw read failed')
        return response.read()

def capture_snapshot(inventory_path, registry_path, heads):
    """Read-only; require actual all70 complete before any remote metadata reads."""
    inventory, registry = load(inventory_path), load(registry_path)
    requests, current = require_all70(inventory, registry)
    aliases = {e['current_video_order'] + ' ' + e['title_zh'] + '.mp4': current[sid]
               for sid, e in requests.items()}
    snapshots = {}
    for repo in [PRIMARY, BACKUP]:
        head = commit40(heads[repo])
        need(public_json(repo, 'git/ref/heads/' + BRANCHES[repo])['object']['sha'] == head,
             'Canonical HEAD moved before capture')
        commit = public_json(repo, 'git/commits/' + head)
        root = public_json(repo, 'git/trees/' + commit['tree']['sha'])
        vroot = next(r['sha'] for r in root['tree'] if r['path'] == '视频修订定稿')
        tree = public_json(repo, 'git/trees/' + vroot)
        byname = {r['path']: r for r in tree['tree']}
        for name, local in [('已归档视频总清单.json', inventory_path), ('latest_requests.json', registry_path)]:
            raw = public_raw(repo, head, '视频修订定稿/' + name)
            need(raw == Path(local).read_bytes() and git_blob(raw) == byname[name]['sha'],
                 'Canonical remote full JSON differs from local exact snapshot')
        final = public_json(repo, 'git/trees/' + byname['最终定稿']['sha'])
        alias_tree = next(r['sha'] for r in final['tree'] if r['path'] == '视频')
        actual = public_json(repo, 'git/trees/' + alias_tree)
        need(not actual.get('truncated', False), 'Truncated alias tree')
        nodes = [{k: x[k] for k in ['path', 'mode', 'type', 'sha', 'size']} for x in actual['tree']]
        need(len(nodes) == 70 and {x['path'] for x in nodes} == set(aliases),
             'Unique latest directory must contain exactly the70 current filenames')
        need(all(x['mode'] == '100644' and x['type'] == 'blob' and
                 x['size'] == aliases[x['path']]['bytes'] for x in nodes), 'Alias node identity/size mismatch')
        snapshots[repo] = {'head': head, 'branch': BRANCHES[repo], 'inventory': spec(inventory_path),
                           'registry': spec(registry_path), 'alias_tree_sha': alias_tree,
                           'alias_entries': nodes}
        need(public_json(repo, 'git/ref/heads/' + BRANCHES[repo])['object']['sha'] == head,
             'Canonical HEAD moved during capture')
    need(snapshots[PRIMARY]['alias_entries'] == snapshots[BACKUP]['alias_entries'],
         'Both latest directory trees must be fully identical')
    return {'kind': 'actual-all70-dual-current-metadata-readback-not-a-release-manifest',
            'snapshots': snapshots, 'no_media_download_or_remote_mutation': True}

def validate_ready(ready_path, current, entry):
    ready = load(ready_path)
    need(media_identity(ready) == media_identity(current) and ready['source_id'] == current['source_id'] and
         ready['new_id'] == entry['frozen_book_order'], 'Wrong current immutable dual-ready file')
    need(ready['passed_per_article'] is True and ready['production_delivery_eligible'] is True and
         ready['preview_only'] is False, 'Review-only ready cannot enter a final release')
    metadata = {k: Path(v if isinstance(v, str) else v['path']) for k, v in ready['metadata_files'].items()}
    prepared = load(metadata['prepared-archive.json'])
    primary, backup = [load(metadata[k]) for k in ['assets-primary.json', 'assets-backup.json']]
    need(primary['asset_commit'] == backup['asset_commit'] == current['asset_commit'] and
         primary['video_tree_sha'] == backup['video_tree_sha'] == ready['video_tree_sha'] and
         primary['files_index'] == backup['files_index'], 'Actual dual asset archives differ')
    streams = load(metadata['remote-video-byte-verification.json'])
    need(streams['passed'] is True and len(streams['streams']) == 2 and
         {s['repository'] for s in streams['streams']} == {PRIMARY, BACKUP}, 'Need two whole public MP4 proofs')
    for s in streams['streams']:
        need(s['passed'] is True and s['http_status'] == 200 and s['source_id'] == current['source_id'] and
             s['new_id'] == entry['frozen_book_order'] and
             (s['pinned_asset_commit'], s['repo_path'], s['bytes'], s['sha256']) == media_identity(current),
             'Whole MP4 proof has different archived bytes')
    blobs = load(metadata['actual-dual-asset-blob-verification.json'])
    need(len(blobs['archives']) == 2 and blobs['actual_dual_blob_rows'] == 2 * len(primary['files_index']) and
         {s['repository'] for s in blobs['archives']} == {PRIMARY, BACKUP}, 'Need complete two-repository Git blob proof')
    for b in blobs['archives']:
        need(b['all_remote_Git_blob_modes_sizes_SHA_exact'] is True and
             b['asset_commit'] == current['asset_commit'] and b['files'] == len(primary['files_index']) and
             b['record_subtree'] == ready['video_tree_sha'], 'Incomplete immutable archive proof')
    hp = Path(ready['real_V3_handoff'])
    actual_h_sha = sha(hp.read_bytes())
    need(actual_h_sha == entry['validation_handoff_sha256'],
         'Current request does not bind this actual final H')
    if 'postprocessing_full_V3_handoff_sha256' in current:
        need(actual_h_sha == current['postprocessing_full_V3_handoff_sha256'],
             'Current inventory points to a different final H')
    else:
        need(LEGACY_CURRENT_FINAL_H.get(current['source_id']) == actual_h_sha,
             'Only the three exact archived old-schema final H bindings may omit the redundant inventory field')
    h = load(hp); a = h['articles'][0]
    adopted28 = current['source_id'] == '28' and actual_h_sha == EXISTING28_PROOFS['handoff']
    current_qc = load(a['section']['qc']['path'])
    source_spec = (current_qc['inherited_full_V3_handoff'] if adopted28 else
                   h.get('current_source_validation_handoff', h.get('inherited_full_V3')))
    need(source_spec, 'Missing inherited actual full source validation')
    sp = Path(source_spec['path'])
    need(spec(sp)['sha256'] == source_spec['sha256'] and sp.stat().st_size == source_spec['bytes'], 'Source H changed')
    source = load(sp)
    paths = {'handoff': hp, 'record': Path(a['validated_record']), 'qc': Path(a['section']['qc']['path']),
             'source_handoff': sp, 'source_qc': Path(source['articles'][0]['section']['qc']['path'])}
    if adopted28:
        prior = load(h['inherited_exact_preview_handoff']['path'])
        paths.update({'scope_authority': Path(h['current_scope_authority']['path']),
                      'reuse_authority': Path(h['reuse_authority']['path']),
                      'preview18_handoff': Path(h['inherited_exact_preview_handoff']['path']),
                      'preview18_qc': Path(prior['articles'][0]['section']['qc']['path'])})
    docs = {k: load(p) for k, p in paths.items()}
    evidence = {}
    bindings = prepared.get('material_source_bindings')
    if bindings is None:
        # The existing057 source28 asset commit reuses already archived Git
        # objects. Its genuine old preparation schema has no source-locator
        # table. Bind its nine proofs by full bytes/SHA to the same complete
        # dual-verified file index; never manufacture fields in the old archive.
        need(adopted28 and sha(metadata['prepared-archive.json'].read_bytes()) ==
             'e8b0751895ecea86c62829588e711eddd15ac3b651e13b00088e25ef79d416fa' and
             prepared['kind'] == 'user057-existing-qualified-Tu29-Git-object-reuse-archive' and
             prepared['actual_handoff_sha256'] == actual_h_sha,
             'Unknown prepared-archive schema without material bindings')
        bindings = primary['files_index']
    for key, p in paths.items():
        identity = spec(p)
        # Older accepted bundles preserve the same exact proof under an owned
        # archive path while the frozen H keeps its original absolute locator.
        # Bind full bytes/SHA to the actual remote file index, never rewrite H.
        matches = [x for x in bindings if x['bytes'] == identity['bytes'] and
                   x['sha256'] == identity['sha256']]
        need(matches, 'Every actual source/final proof must already be permanently dual archived')
        indexed = {x['repo_path']: x for x in primary['files_index']}
        matches = [x for x in matches if x['repo_path'] in indexed and
                   all(indexed[x['repo_path']][k] == x[k] for k in ['bytes','sha256'])]
        need(matches, 'The full-hash proof binding must be in the already verified dual Git index')
        evidence[key] = {k: matches[0][k] for k in ['repo_path', 'bytes', 'sha256']}
    file_nodes = [x for x in primary['files_index'] if x['repo_path'] == current['video_repo_path']]
    need(len(file_nodes) == 1 and all(file_nodes[0][k] == current[k] for k in ['bytes', 'sha256']),
         'MP4 absent from exact immutable dual asset tree')
    name = entry['current_video_order'] + ' ' + entry['title_zh'] + '.mp4'
    video = {'source_id': current['source_id'], 'frozen_book_order': entry['frozen_book_order'],
             'current_video_order': entry['current_video_order'], 'title_zh': entry['title_zh'],
             'title_en': entry['title_en'], 'release_name': name, 'canonical_alias_path': ALIASES + name,
             'asset_commit': current['asset_commit'], 'video_repo_path': current['video_repo_path'],
             'bytes': current['bytes'], 'sha256': current['sha256'], 'alias_git_blob_sha': file_nodes[0]['git_blob_sha'],
             'qualification': 'current_verified_latest_final', 'actual_complete_validation_passed': True,
             'actual_dual_permanent_archive_passed': True, 'production_delivery_eligible': True, 'preview_only': False,
             'end_reading_pause_seconds': .6, 'nominal_extra_hold_frames_at_30fps': 18,
             'validation_handoff_sha256': entry['validation_handoff_sha256'],
             'actual_probe': docs['record']['actual_probe'], 'validated_tail': docs['record']['tail'], 'evidence': evidence}
    validate_video(video); validate_documents(video, docs)
    return video

def compile_input(path):
    inputs = load(path)
    need(inputs['kind'] == 'all70-latest-final-publication-inputs-not-a-manifest', 'Wrong publication inputs')
    authority = Path(inputs['actual_user_release_authority'])
    need(sha(authority.read_bytes()) == AUTH_SHA, 'Wrong real conditional user release request')
    inventory, registry = load(inputs['inventory_local_path']), load(inputs['latest_requests_local_path'])
    requests, current = require_all70(inventory, registry)
    snapshot = load(inputs['dual_current_snapshot_local_path'])
    need(snapshot['kind'] == 'actual-all70-dual-current-metadata-readback-not-a-release-manifest', 'Actual readback snapshot required')
    snapshots = snapshot['snapshots']
    for repo in [PRIMARY, BACKUP]:
        s = snapshots[repo]
        need(s['inventory'] == spec(inputs['inventory_local_path']) and
             s['registry'] == spec(inputs['latest_requests_local_path']), 'Inconsistent snapshot files')
    ready_paths = inputs['actual_dual_ready_files_by_source']
    need(set(ready_paths) == set(requests), 'Exactly70 real source-specific ready files required')
    videos = []
    aliases = {x['path']: x for x in snapshots[PRIMARY]['alias_entries']}
    need(snapshots[PRIMARY]['alias_entries'] == snapshots[BACKUP]['alias_entries'], 'Different canonical alias trees')
    for entry in sorted(requests.values(), key=lambda e: int(e['current_video_order'])):
        sid = entry['source_id']; video = validate_ready(ready_paths[sid], current[sid], entry)
        need(video['release_name'] in aliases, 'Missing current latest alias')
        node = aliases[video['release_name']]
        need((node['mode'], node['type'], node['sha'], node['size']) ==
             ('100644', 'blob', video['alias_git_blob_sha'], video['bytes']), 'Wrong current alias Git blob')
        videos.append(video)
    public_snapshots = {repo: {k: v for k, v in value.items() if k != 'alias_entries'}
                        for repo, value in snapshots.items()}
    result = {'kind': 'all70-actually-complete-latest-final-release-manifest', 'tag': TAG,
              'actual_release_authority_sha256': AUTH_SHA,
              'actual_all70_latest_qualified_and_dual_archived': True,
              'compiled_UTC': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'snapshots': public_snapshots, 'videos': videos, 'total_MP4_bytes': sum(v['bytes'] for v in videos),
              'no_local_abs_paths_or_private_sources_in_manifest': True,
              'publisher_rechecks_fresh_dual_heads_all_proofs_media_and_latest_directory_before_Release': True}
    validate_manifest(result)
    return result

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--status', action='store_true'); p.add_argument('--capture-snapshot', action='store_true')
    p.add_argument('--inventory'); p.add_argument('--registry'); p.add_argument('--primary-head'); p.add_argument('--backup-head')
    p.add_argument('--input'); p.add_argument('--output', required=True)
    a = p.parse_args()
    if a.status:
        write(a.output, {'kind': 'actual-current-readiness-only-not-a-release-manifest',
                        **eligibility(load(a.inventory), load(a.registry)),
                        'no_publication_manifest_created': True, 'no_network_or_media_read': True})
    elif a.capture_snapshot:
        write(a.output, capture_snapshot(a.inventory, a.registry, {PRIMARY:a.primary_head, BACKUP:a.backup_head}))
    else:
        need(a.input, 'Actual complete source inputs are required')
        write(a.output, compile_input(a.input))

if __name__ == '__main__':
    main()
