"""Temporary exact original95/b244 regression data, with inode restoration.

This module does not invoke a checker or a model. It neither changes expected
values nor supplies article acceptance. The caller runs the original quickcheck.
"""
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import stat
import uuid

MANIFEST_SHA256 = 'e81d2f49eea100c89a75cbe286b1f8422e4e80e993f59e05c0db3d3e361805bd'
COMMIT = 'b24406d11f2ddd936f65bcc344aa9a7d32d074da'
ORIGINAL_FONT_FILES = {'Inter.ttf': '29160a80ff49ddcab2c97711247e08b1fab27a484a329ce8b813d820dc559031', 'MaShanZheng-Regular.ttf': '6d2546bb189c732a8ca29af9e22457b152387d158aa459e4ac2ce1e51788b7fb', 'NotoSansSC.ttf': 'a3041811a78c361b1de50f953c805e0244951c21c5bd412f7232ef0d899af0da', 'ZCOOLQingKeHuangYou-Regular.ttf': '54f0c0df4308cd74cd0f2fd3494ae054dbc4a1fd6fa7d71f4807eb4cdd8b4136'}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def snapshot(path):
    path = Path(path)
    if not os.path.lexists(path):
        return {'exists': False}
    info = path.lstat()
    require(stat.S_ISREG(info.st_mode) or stat.S_ISLNK(info.st_mode),
            'Refuse non-file fixture target ' + str(path))
    require(path.is_file(), 'Refuse dangling fixture target ' + str(path))
    return {'exists': True, 'inode': info.st_ino, 'device': info.st_dev,
            'mode': info.st_mode, 'mtime_ns': info.st_mtime_ns,
            'SHA256': sha(path), 'symlink': os.readlink(path) if path.is_symlink() else None}


def inode_identity(value):
    """A symlink's referent may temporarily be another owned fixture target."""
    return {k: v for k, v in value.items() if k != 'SHA256'}


def validate_runtime_context(root, tools, work, alias=Path('/home/user/postgraduate-vocabulary')):
    root, tools, work, alias = map(Path, (root, tools, work, alias))
    require(alias.resolve(strict=True) == root.resolve(strict=True),
            'Original canonical repository alias must exist before format quickcheck')
    fonts = tools / 'fonts'
    require(fonts.is_dir(), 'Original tools fonts missing')
    observations = []
    # The real original checkout has two distinct directories containing the
    # same immutable font blobs. Bind content, not directory inode identity.
    for path in (fonts, root / '视频/资源/字体', work / 'fonts'):
        require(path.is_dir(), 'Original font setup must precede format quickcheck: ' + str(path))
        values = {}
        for name, expected in ORIGINAL_FONT_FILES.items():
            font = path / name
            require(font.is_file() and sha(font) == expected,
                    'Original font bytes mismatch: ' + str(font))
            values[name] = {'sha256': sha(font), 'bytes': font.stat().st_size}
        observations.append({'path': str(path), 'realpath': str(path.resolve(strict=True)), 'files': values})
    return {'canonical_repository_alias_exact': True, 'original_four_font_fullSHA_exact_in_all_three_roles': True,
            'font_roles': observations, 'font_files_changed': False}


def prepare_fixture_plan(root, work, package):
    """All 18 sources and every destination are checked before any rename/write."""
    root, work, package = map(lambda p: Path(p).resolve(strict=True), (root, work, package))
    manifest_path = package / 'historical-fixtures-manifest.json'
    require(manifest_path.resolve(strict=True) == manifest_path and
            sha(manifest_path) == MANIFEST_SHA256, 'Wrong actual original95 fixture manifest')
    manifest = json.loads(manifest_path.read_text())
    require(manifest['immutable_commit'] == COMMIT and len(manifest['files']) == 18,
            'Wrong historical fixture provenance')
    plan, physical = [], {}
    for row in manifest['files']:
        rel = Path(row['path'])
        require(not rel.is_absolute() and '..' not in rel.parts, 'Unsafe original fixture path')
        source = package / 'historical-fixtures' / rel
        require(source.resolve(strict=True) == source and source.is_file() and sha(source) == row['SHA256'],
                'Historical source fixture SHA mismatch: ' + str(rel))
        destinations = [('ROOT', root / rel)]
        if rel.parts[:2] == ('视频', '脚本'):
            destinations.append(('W', work / 'scripts' / rel.name))
        for role, logical in destinations:
            # Resolve the directory only. A target file symlink itself must be
            # renamed/restored as its original inode, never written through.
            destination = logical.parent.resolve() / logical.name
            require(destination.is_relative_to(root) or destination.is_relative_to(work),
                    'Fixture destination outside the two isolated original roots')
            before = snapshot(destination)
            key = str(destination)
            if key in physical:
                existing = physical[key]
                require(existing['fixture_SHA256'] == row['SHA256'], 'Conflicting aliased fixture destinations')
                existing['logical_roles'].append({'role': role, 'path': str(logical), 'before': before})
                continue
            item = {'target': destination, 'source': source, 'fixture_SHA256': row['SHA256'],
                    'before': before, 'logical_roles': [{'role': role, 'path': str(logical), 'before': before}]}
            physical[key] = item
            plan.append(item)
    require(sum(len(x['logical_roles']) for x in plan) == 21, 'Expected ROOT18 + W3 logical roles')
    return plan


@contextmanager
def temporary_historical_fixtures(root, work, package, evidence):
    plan = prepare_fixture_plan(root, work, package)
    token = uuid.uuid4().hex
    created_directories, active = [], []
    evidence.update({'fixture_manifest_SHA256': MANIFEST_SHA256, 'fixture_commit': COMMIT,
                     'fixture_sources': 18, 'logical_destination_count': 21,
                     'physical_destination_count': len(plan), 'all_sources_preflight_SHA_passed': True,
                     'original_files_or_absence_restored': False})
    try:
        for index, item in enumerate(plan):
            target = item['target']
            current = snapshot(target)
            if current != item['before']:
                # ROOT/script10 can be temporarily replaced before a W file
                # symlink pointing to it is renamed. Its original link inode
                # must remain exact; only our earlier, known fixture may own
                # the changed referent bytes. Final verification is full SHA.
                owned_referent = next((x for x in active if x['owned_temporary_target'] and
                                      target.resolve() == x['target']), None)
                require(item['before'].get('symlink') is not None and
                        inode_identity(current) == inode_identity(item['before']) and
                        owned_referent is not None and current['SHA256'] == owned_referent['fixture_SHA256'],
                        'Destination changed since preflight')
            missing, parent = [], target.parent
            while not parent.exists():
                missing.append(parent)
                parent = parent.parent
            for directory in reversed(missing):
                directory.mkdir()
                created_directories.append(directory)
            backup = target.parent / ('.' + target.name + '.source46-cert-backup-' + token)
            require(not os.path.lexists(backup), 'Backup namespace collision')
            item.update({'backup': backup, 'moved': False, 'owned_temporary_target': False})
            active.append(item)
            if item['before']['exists']:
                os.replace(target, backup)
                item['moved'] = True
            # exclusive create refuses a concurrent/link target instead of
            # following it or replacing another writer's inode.
            with target.open('xb') as out:
                item['owned_temporary_target'] = True
                out.write(item['source'].read_bytes())
            require(sha(target) == item['fixture_SHA256'], 'Fixture write/readback mismatch')
        evidence['historical_fixtures_active_only_inside_original_fullquick_context'] = True
        yield
    finally:
        errors = []
        for item in reversed(active):
            target, backup = item['target'], item['backup']
            try:
                if item['owned_temporary_target'] and os.path.lexists(target):
                    require(not target.is_dir() or target.is_symlink(), 'Unexpected directory at temporary fixture file')
                    target.unlink()
                if item['moved']:
                    require(not os.path.lexists(target), 'Refuse overwriting unexpected target during restore')
                    os.replace(backup, target)
                restored = snapshot(target)
                if item['before'].get('symlink') is not None:
                    # Its ROOT referent can still be awaiting reverse-order
                    # restoration. All roles get full SHA verification below.
                    require(inode_identity(restored) == inode_identity(item['before']),
                            'Original symlink inode/metadata not restored')
                else:
                    require(restored == item['before'], 'Original fixture target inode/bytes/absence not restored')
            except BaseException as exc:
                errors.append(str(exc))
        for directory in reversed(created_directories):
            try:
                directory.rmdir()
            except BaseException as exc:
                errors.append('Created directory not restored to absence: ' + str(directory) + ': ' + str(exc))
        for item in plan:
            try:
                require(snapshot(item['target']) == item['before'], 'Final original target mismatch')
                require(sha(item['source']) == item['fixture_SHA256'], 'Immutable historical source changed')
                for role in item['logical_roles']:
                    require(snapshot(Path(role['path'])) == role['before'], 'Original logical role not restored')
            except BaseException as exc:
                errors.append(str(exc))
        evidence['restore_errors'] = errors
        evidence['original_files_or_absence_restored'] = not errors
        evidence['restored_logical_roles'] = [
            {'role': role['role'], 'path': role['path'], 'existed': role['before']['exists'],
             'inode': role['before'].get('inode'), 'original_SHA256': role['before'].get('SHA256')}
            for item in plan for role in item['logical_roles']]
        require(not errors, 'Historical fixture finally restoration failed: ' + '; '.join(errors))
