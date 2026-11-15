"""Export only the passed official a.wav master; no production/audio changes."""
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import tempfile
import wave

AUTHORITY_SHA256 = 'b00a133cc88ed37496e225a181898863ce52e9a774e6b5c2991a310691fd4312'
ROLE = 'original-program-master/pre-video-AF'


class ExportRejected(Exception):
    pass


def _require(condition, code):
    if not condition:
        raise ExportRejected(code)


def _sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def _regular(path):
    _require(stat.S_ISREG(Path(path).lstat().st_mode), 'not-a-regular-nonsymlink-file')


def _pcm_format(stream):
    stream.seek(0)
    with wave.open(stream, 'rb') as wav:
        channels, width, rate, frames, compression, _ = wav.getparams()
        _require((channels, width, rate, compression) == (1, 2, 24000, 'NONE'),
                 'master-must-be-PCM16-mono-24000Hz')
        _require(frames > 0, 'empty-master')
        remaining = frames
        while remaining:
            count = min(remaining, 8192)
            _require(len(wav.readframes(count)) == count * 2, 'truncated-PCM-payload')
            remaining -= count
    stream.seek(0)
    return {'container': 'WAV', 'encoding': 'PCM', 'sample_width_bytes': width,
            'bits_per_sample': width * 8, 'channels': channels, 'sample_rate': rate,
            'frames': frames, 'duration_seconds': frames / rate}


def _identity(info):
    return info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns


def _write_report(path, record):
    _require(not path.exists() and not path.is_symlink(), 'evidence-file-already-exists')
    fd, name = tempfile.mkstemp(prefix='.master-export-evidence-', suffix='.partial', dir=path.parent)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as stream:
            json.dump(record, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
            stream.flush()
            os.fsync(stream.fileno())
        _require(not path.exists() and not path.is_symlink(), 'evidence-file-already-exists')
        os.rename(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def export_passed_original_master(article, work_root, output_dir, status, final_video, authority):
    """Return independent IO evidence. Never mutate status or reinterpret quality.

    The only audio input is work_root/work_NN/a.wav. The native master is copied
    byte for byte, before any downstream video's AF, and is not decoded/re-encoded.
    The caller must call this only after add_approved_illustrated_tail returns.
    """
    record = {'kind': 'passed-original-program-master-WAV-export', 'article': article,
              'exported': False, 'role': ROLE, 'quality_verdict_changed': False,
              'archive_remote_verified': False, 'all_generated_assets_complete_claimed': False,
              'native_quality_status_is_a_separate_verdict': True,
              'inference_cache_or_voice_embedding_exported': False}
    evidence = None
    temporary = None
    try:
        _require(isinstance(article, str) and re.fullmatch(r'(0[1-9]|[1-6][0-9]|70)', article),
                 'invalid-article')
        work_root, output_dir = Path(work_root), Path(output_dir)
        _require(work_root.is_dir() and not work_root.is_symlink(), 'invalid-private-work-root')
        _require(output_dir.is_dir() and not output_dir.is_symlink(), 'invalid-public-output-directory')
        evidence = output_dir / f'{article}-original-program-master-export.json'
        destination = output_dir / f'{article}-original-program-master-pre-video-AF.wav'
        record.update({'evidence_file': evidence.name, 'file': destination.name,
                       'source_private_path_role': f'W/work_{article}/a.wav',
                       'source_private_path_is_not_an_artifact': True})
        _require(not evidence.exists() and not evidence.is_symlink(), 'evidence-file-already-exists')
        _require(not destination.exists() and not destination.is_symlink(), 'export-file-already-exists')
        _regular(authority)
        _require(_sha(authority) == AUTHORITY_SHA256, 'archive-authority-SHA256-mismatch')
        auth = json.loads(Path(authority).read_text(encoding='utf-8'))
        _require(auth.get('author') == 'user' and
                 auth.get('kind') == 'actual-user-all-project-generated-deliverables-existing-and-future-GitHub-archive-authorization' and
                 'project_master_WAV_MP3_and_actual_target_mother_audio' in auth.get('authorized_project_output_roles', []),
                 'archive-authority-role-mismatch')
        record['authority'] = {'sha256': AUTHORITY_SHA256, 'descriptive_id': auth['descriptive_id'],
                               'authorized_role': 'project_master_WAV_MP3_and_actual_target_mother_audio'}
        _require(status.get('article') == article and status.get('canonical_pipeline_passed') is True and
                 status.get('passed') is True and status.get('stage') == 'final4K-passed',
                 'original-native-and-final-quality-not-passed')
        _require(status.get('width') == 3840 and status.get('height') == 2160,
                 'final-status-is-not-4K')
        final_video = Path(final_video)
        _require(final_video.parent == output_dir and
                 final_video.name == f'{article}-4K-正文-书中插图2秒-简述2秒.mp4' and
                 status.get('final_video_file') == final_video.name,
                 'final-video-role-mismatch')
        _regular(final_video)
        final_sha = _sha(final_video)
        _require(final_sha == status.get('video_sha256'), 'final-video-SHA256-mismatch')
        proof_ref = status.get('illustrated_tail_verification', {})
        _require(proof_ref.get('file') == f'{article}-illustrated-tail-verification.json',
                 'illustrated-tail-proof-role-mismatch')
        proof_path = output_dir / proof_ref['file']
        _regular(proof_path)
        proof_sha = _sha(proof_path)
        _require(proof_sha == proof_ref.get('sha256'), 'illustrated-tail-proof-SHA256-mismatch')
        proof = json.loads(proof_path.read_text(encoding='utf-8'))
        _require(proof.get('passed') is True and proof.get('production_delivery_eligible') is True and
                 proof.get('source_kind') == 'new-canonical-4K' and proof.get('video_sha256') == final_sha,
                 'illustrated-tail-proof-not-eligible-or-not-this-final')
        expected_sha = status.get('final_wav_sha256')
        _require(isinstance(expected_sha, str) and re.fullmatch(r'[0-9a-f]{64}', expected_sha),
                 'missing-original-final-WAV-SHA256')
        source_directory = work_root / f'work_{article}'
        _require(source_directory.is_dir() and not source_directory.is_symlink(), 'invalid-fixed-master-directory')
        source = source_directory / 'a.wav'
        _regular(source)
        source_fd = os.open(source, os.O_RDONLY | os.O_NOFOLLOW)
        with os.fdopen(source_fd, 'rb') as original:
            before = os.fstat(original.fileno())
            _require(stat.S_ISREG(before.st_mode), 'not-a-regular-master')
            audio_format = _pcm_format(original)
            fd, temporary = tempfile.mkstemp(prefix='.master-export-', suffix='.partial', dir=output_dir)
            digest = hashlib.sha256()
            copied = 0
            with os.fdopen(fd, 'wb') as target:
                for block in iter(lambda: original.read(1024 * 1024), b''):
                    target.write(block)
                    digest.update(block)
                    copied += len(block)
                target.flush()
                os.fsync(target.fileno())
            _require(_identity(before) == _identity(os.fstat(original.fileno())) and
                     _identity(before) == _identity(source.stat()), 'master-changed-during-export')
        _require(copied == before.st_size and digest.hexdigest() == expected_sha and
                 _sha(temporary) == expected_sha, 'original-master-SHA256-or-size-mismatch')
        _require(not destination.exists() and not destination.is_symlink(), 'export-file-already-exists')
        os.rename(temporary, destination)
        temporary = None
        record.update({'exported': True, 'bytes': copied, 'sha256': expected_sha,
                       'format': audio_format, 'original_master_hash_equals_status_final_wav_sha256': True,
                       'byte_exact_copy_no_reencode': True, 'final_video_sha256': final_sha,
                       'illustrated_tail_proof_sha256': proof_sha,
                       'upstream_quality_passed_observed': True,
                       'exported_WAV_is_not_post_video_AF_or_decoded_AAC': True})
    except Exception as exc:
        record['error'] = {'type': type(exc).__name__,
                           'code': str(exc) if isinstance(exc, ExportRejected) else 'export-IO-or-format-error'}
        if isinstance(exc, OSError):
            record['error']['errno'] = exc.errno
    finally:
        if temporary is not None:
            try:
                os.unlink(temporary)
            except OSError:
                pass
    if evidence is not None:
        try:
            _write_report(evidence, record)
            record['evidence_written'] = True
        except Exception as exc:
            record['evidence_written'] = False
            record['evidence_write_error'] = {'type': type(exc).__name__,
                                               'code': str(exc) if isinstance(exc, ExportRejected) else 'evidence-IO-error'}
    return record
