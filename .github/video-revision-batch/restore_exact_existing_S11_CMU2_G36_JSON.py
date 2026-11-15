"""Restore one already-measured original G36 JSON. Never calculate gain."""
import hashlib
import json
import os
from pathlib import Path
import stat
import tempfile

NAME = '调平_f8530296a68d023c59d49bcc027d1e23c0bd9a2c.json'
SHA256 = '98c2e92f9fe36307e60e0a857a97d5595015278b2add1fed2bcea10248eb43d6'
KEY = 'Linux-native56-only-S11-CMU2-whole-original-math-43765008177'
VERSION = '9379d7272d5811602cc5c1c7e1393a7c44306e0d70d6fbe78050864cb190b053'


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def restore_existing_original_math(source, destination, cache_hit):
    source, destination = Path(source), Path(destination)
    require(cache_hit == 'true', 'Exact saved private G36 cache must hit; no calculation fallback')
    require(source.name == destination.name == NAME, 'Only exact original S11 G36 filename is allowed')
    require(source.parent.name == 'source56-only-S11-CMU2-whole-original-math-cache' and
            destination.parent.name == 'cache_tts' and source.parent.parent == destination.parent.parent,
            'Keep exact saved private path and normal cache path')
    require(stat.S_ISREG(source.lstat().st_mode), 'Saved G36 source must be a regular nonsymlink file')
    raw = source.read_bytes()
    require(hashlib.sha256(raw).hexdigest() == SHA256, 'Existing G36 source full SHA differs')
    require(json.loads(raw) == {'1': -1.5, '2': 1.5}, 'Original measured G36 values differ')
    destination.parent.mkdir(parents=True, exist_ok=True)
    existed = destination.exists() or destination.is_symlink()
    if existed:
        require(stat.S_ISREG(destination.lstat().st_mode), 'Normal G36 destination must be regular nonsymlink')
        require(destination.read_bytes() == raw, 'Existing normal G36 differs; never overwrite or recalculate')
    else:
        fd, temporary = tempfile.mkstemp(prefix='.restore-exact-S11-G36-', suffix='.partial', dir=destination.parent)
        try:
            with os.fdopen(fd, 'wb') as stream:
                stream.write(raw)
                stream.flush()
                os.fsync(stream.fileno())
            require(digest(temporary) == SHA256, 'Temporary copy differs')
            require(not destination.exists() and not destination.is_symlink(), 'Normal G36 appeared concurrently; refuse overwrite')
            os.rename(temporary, destination)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)
    require(digest(source) == digest(destination) == SHA256, 'Exact G36 readback failed')
    return {'kind': 'actual-existing-source56-S11-original-G36-single-JSON-restore-and-readback',
            'restored_existing_original_math': True, 'normal_cache_was_already_exact': existed,
            'filename': NAME, 'bytes': len(raw), 'sha256': SHA256,
            'actual_saved_cache_key': KEY, 'actual_saved_cache_version': VERSION,
            'saved_path_role': 'completion-machine/tts/source56-only-S11-CMU2-whole-original-math-cache/' + NAME,
            'normal_path_role': 'completion-machine/tts/cache_tts/' + NAME,
            'no_original_G36_calculation_or_model_called': True,
            'source_JSON_not_exported_as_artifact': True,
            'only_one_original_JSON_copied_or_exactly_reused': True,
            'quality_or_formal_acceptance': False}


def main():
    machine = Path(os.environ['RUNNER_TEMP']) / 'completion-machine'
    output = Path(os.environ['GITHUB_WORKSPACE']) / 'source56-CMU2-existing-math-public'
    output.mkdir(exist_ok=True)
    proof = restore_existing_original_math(
        machine / 'tts/source56-only-S11-CMU2-whole-original-math-cache' / NAME,
        machine / 'tts/cache_tts' / NAME, os.environ['CACHE_HIT'])
    (output / 'actual-existing-S11-CMU2-original-G36-JSON-restore-readback.json').write_text(
        json.dumps(proof, ensure_ascii=False, indent=2) + '\n')


if __name__ == '__main__':
    main()
