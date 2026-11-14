#!/usr/bin/env python3
"""Collect actual passed outputs; a partial collection can never be published."""
import argparse
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent


def read(path):
    return json.loads(path.read_text())


def digest(path):
    with path.open('rb') as source:
        return hashlib.file_digest(source, 'sha256').hexdigest()


def assemble(output, primary, backup):
    handoffs = [HERE / 'actual53-64-validation/archive-handoff.json']
    for folder in ('next-passed-validated', 'recovered-canonical-validated', 'inline-passed-validated'):
        handoffs.extend(sorted((HERE / folder).glob('*/*/archive-handoff.json')))
    output.mkdir(parents=True, exist_ok=True)
    actual = {}
    common = None
    common_keys = ('mapping_commit', 'book_illustrations', 'illustration_composition_review',
                   'illustration_crop_review', 'video_layout_approval', 'source_derivation')
    provenance = []
    for handoff in handoffs:
        if not handoff.exists():
            continue
        source_config = read(handoff.parent / 'actual-sample-input.json')
        current = {key: source_config[key] for key in common_keys}
        current['catalog_sha256'] = digest(Path(source_config['catalog_path']))
        current['order_map_sha256'] = digest(Path(source_config['order_map_path']))
        if common is None:
            common = current
            template = source_config
        assert current == common, 'Common approval/mapping changed; reconcile explicitly first'
        for article in read(handoff)['articles']:
            assert article['passed_per_article'] is True
            item = article['section']
            n = item['id']
            assert n == article['source_id']
            assert item['mp4'] == article['final_mp4']
            media = Path(item['mp4']['path'])
            assert media.stat().st_size == item['mp4']['bytes'] and digest(media) == item['mp4']['sha256']
            if n in actual:
                assert actual[n]['mp4']['sha256'] == item['mp4']['sha256'], 'Conflicting final outputs'
                continue
            for layer, root_key in (('request_source', 'request_source_root'), ('final_source', 'final_source_root')):
                for kind, spec in item[layer].items():
                    source = Path(source_config[root_key]) / spec['path']
                    assert source.stat().st_size == spec['bytes'] and digest(source) == spec['sha256']
                    destination = output / layer / spec['path']
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    if destination.exists():
                        assert digest(destination) == spec['sha256']
                    else:
                        shutil.copy2(source, destination)
            actual[n] = item
            provenance.append({'source_id': n, 'book_order': article['new_id'],
                               'handoff': str(handoff), 'handoff_sha256': digest(handoff),
                               'final_mp4': item['mp4']})
    required = {f'{n:02d}' for n in range(1, 71)}
    missing = sorted(required - actual.keys())
    report = {'recorded_utc': datetime.now(timezone.utc).isoformat(),
              'status': 'collected_actual_passed_handoffs_only', 'actual_passed_count': len(actual),
              'missing_source_ids': missing, 'complete70_collection': not missing,
              'whole_release_validation_executed': False, 'remote_mutation_executed': False,
              'sources': sorted(provenance, key=lambda row: int(row['book_order']))}
    (output / 'collection-progress.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    if missing:
        assert not (output / 'complete70-input.json').exists(), 'Stale complete input must not survive a partial collection'
        return report
    assert primary and backup, 'Actual final dual-archive HEADs are required for the complete input'
    config = read(HERE / 'input.example.json')
    revision = 'kaoyanxueren-2026.11.14-final'
    config.update({key: template[key] for key in common_keys})
    config.update(schema_version=3, revision=revision, requested_ids=sorted(required),
                  asset_branch='codex/video-assets-20261114-final',
                  expected_heads={'primary': primary, 'backup': backup},
                  backup_master_expected='6355a02864ebae616b693200d9d26f74f5da80e9',
                  request_source_root=str(output / 'request_source'),
                  final_source_root=str(output / 'final_source'),
                  catalog_path=template['catalog_path'], order_map_path=template['order_map_path'],
                  articles=[actual[n] for n in sorted(required)], unchanged_videos=[],
                  published_pdf=read(HERE / 'published-pdf-v4-frozen-primary.json'))
    config['release'].update(tag=revision, title='考研学人：全册PDF与70部4K视频')
    config['audio_changed_articles'] = [n for n in sorted(required)
        if read(Path(actual[n]['qc']['path']))['audio']['repair_applied']]
    from delivery import AUTHORIZED_OLD_RELEASE_TARGET
    config['cleanup_targets'] = [AUTHORIZED_OLD_RELEASE_TARGET]
    target = output / 'complete70-input.json'
    target.write_text(json.dumps(config, ensure_ascii=False, indent=2) + '\n')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--primary')
    parser.add_argument('--backup')
    args = parser.parse_args()
    result = assemble(args.output.resolve(), args.primary, args.backup)
    print(json.dumps({key: value for key, value in result.items() if key != 'sources'}, ensure_ascii=False))
