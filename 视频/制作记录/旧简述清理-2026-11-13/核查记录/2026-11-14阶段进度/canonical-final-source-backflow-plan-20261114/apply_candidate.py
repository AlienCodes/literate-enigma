#!/usr/bin/env python3
"""Root-reviewed candidate: default read-only; --apply replaces JSON+GEN only.

No network, generation, audio processing, media changes, or acceptance gates.
"""
import argparse
import hashlib
import json
import os
import tempfile
from pathlib import Path


def digest(data):
    return hashlib.sha256(data).hexdigest()


def replace_bytes(path, data):
    # Replace each existing source atomically; retain its access mode.
    mode = path.stat().st_mode & 0o777
    fd, name = tempfile.mkstemp(prefix='.' + path.name + '.backflow-', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        os.chmod(name, mode)
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--apply', action='store_true')
    p.add_argument('--payload-root', type=Path)
    a = p.parse_args()
    here = Path(__file__).resolve().parent
    manifest = json.loads((here / 'apply-manifest.json').read_text())
    root = (a.payload_root or Path(manifest['default_payload_root'])).resolve()
    expected_paths = {f'视频/脚本/{n}.json' for n in manifest['articles']} | {f'视频/工具/初稿生成/gen{n}.py' for n in manifest['articles']}
    assert len(expected_paths) == 18 and {x['relative_path'] for x in manifest['operations']} == expected_paths
    pending, skipped = [], []
    # Compare all originals before any write. Any concurrent source edit aborts the whole apply.
    for op in manifest['operations']:
        target = root / op['relative_path']
        assert not target.is_symlink() and target.resolve().is_relative_to(root)
        original = target.read_bytes()
        candidate = (here / op['candidate_relative_path']).read_bytes()
        assert digest(candidate) == op['after_sha256'], 'Candidate changed: ' + str(target)
        if digest(original) == op['after_sha256']:
            skipped.append(op['relative_path'])
            continue
        assert digest(original) == op['expected_before_sha256'], 'Concurrent canonical change: ' + str(target)
        pending.append((target, original, candidate, op))
    written = []
    if a.apply:
        try:
            for target, original, candidate, op in pending:
                # Recheck immediately before each atomic replace, then restore any completed writes on error.
                assert target.read_bytes() == original, 'Concurrent canonical change: ' + str(target)
                replace_bytes(target, candidate)
                written.append((target, original))
            assert all(target.read_bytes() == candidate for target, original, candidate, op in pending)
        except BaseException:
            for target, original in reversed(written):
                replace_bytes(target, original)
            raise
    print(json.dumps({'mode': 'applied' if a.apply else 'dry-run', 'root': str(root),
                      'pending_files': len(pending), 'already_final_files': len(skipped),
                      'write_files': [op['relative_path'] for target, original, candidate, op in pending] if a.apply else [],
                      'MD_written': False, 'network_used': False}, ensure_ascii=False))


if __name__ == '__main__':
    main()
