"""Bind an already exported public master to one immutable native sourceQA lane.

This is IO provenance only. It never exports private work, changes audio,
reinterprets native quality, invokes a producer, or writes a repository.
"""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import os
import stat

MODULE = Path('/workspace/work/original-program-master-WAV-export-code-only-proposal-20261115/original_program_master_export.py')
MODULE_SHA = 'd4735d1b66ee59879be266a9b48f5d7e658b5c8a62d66a969e95fcaf4d4597a7'
ALLOWED = {'41': 43723634020, '59': 43723690942, '64': 43728310644,
           '69': 43724729006, '70': 43728728741, '58': 43736478355}
AUTHORITY_SHA = 'b00a133cc88ed37496e225a181898863ce52e9a774e6b5c2991a310691fd4312'


def require(ok, message):
    if not ok:
        raise AssertionError(message)


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1048576), b''):
            h.update(block)
    return h.hexdigest()


def spec(path):
    p = Path(path).resolve(strict=True)
    require(stat.S_ISREG(p.stat().st_mode), 'regular file required')
    return {'path': str(p), 'bytes': p.stat().st_size, 'sha256': sha(p)}


def checked(row):
    p = Path(row['path'])
    require(not p.is_symlink() and spec(p) == row, 'frozen input spec differs')
    return p


def validate_records(sid, run, native, evidence):
    require(ALLOWED.get(sid) == run, 'not the exact passed native lane')
    require(native.get('article') == sid and native.get('passed') is True and
            native.get('canonical_pipeline_passed') is True and
            native.get('stage') == 'final4K-passed', 'native quality not passed')
    master = native.get('original_program_master_export', {})
    require(master.get('exported') is True and master.get('evidence_written') is True,
            'native did not export this master')
    require(master.get('kind') == 'passed-original-program-master-WAV-export' and
            master.get('article') == sid and
            master.get('role') == 'original-program-master/pre-video-AF', 'wrong master role')
    require(master.get('file') == sid + '-original-program-master-pre-video-AF.wav' and
            master.get('evidence_file') == sid + '-original-program-master-export.json',
            'wrong fixed public member names')
    require(master.get('authority', {}).get('sha256') == AUTHORITY_SHA and
            master['authority'].get('authorized_role') ==
            'project_master_WAV_MP3_and_actual_target_mother_audio', 'wrong archive authority')
    require(master.get('quality_verdict_changed') is False and
            master.get('inference_cache_or_voice_embedding_exported') is False and
            master.get('byte_exact_copy_no_reencode') is True and
            master.get('original_master_hash_equals_status_final_wav_sha256') is True and
            master.get('exported_WAV_is_not_post_video_AF_or_decoded_AAC') is True,
            'master export provenance flags differ')
    # Exporter writes evidence before adding this return-only status flag.
    require(evidence == {k: v for k, v in master.items() if k != 'evidence_written'},
            'original evidence differs from actual native status')
    require(master['sha256'] == native['final_wav_sha256'] and
            master['final_video_sha256'] == native['video_sha256'] and
            master['illustrated_tail_proof_sha256'] ==
            native['illustrated_tail_verification']['sha256'], 'master identity chain differs')
    return master


def bind(profile_path, expected_profile_sha):
    require(sha(profile_path) == expected_profile_sha, 'binding profile SHA differs')
    profile = json.loads(Path(profile_path).read_text())
    sid, run = profile['source_id'], profile['native_run']
    native_path = checked(profile['actual_native_status'])
    native = json.loads(native_path.read_text())
    root = Path(profile['native_root']).resolve(strict=True)
    out = Path(profile['sourceQA_output_root']).resolve(strict=True)
    require(root == Path('/workspace/work/review' + sid + '-native') / str(run) / sid,
            'wrong fixed native root')
    require(out == Path('/workspace/work/review' + sid + '-sourceQA') / str(run),
            'wrong fixed sourceQA root')
    require(native_path.parent == root / 'artifact-files', 'status outside exact artifact')
    native_master = native.get('original_program_master_export', {})
    wav = root / 'artifact-files' / (sid + '-original-program-master-pre-video-AF.wav')
    evidence_path = root / 'artifact-files' / (sid + '-original-program-master-export.json')
    require(not wav.is_symlink() and not evidence_path.is_symlink(), 'symlink member rejected')
    evidence = json.loads(evidence_path.read_text())
    master = validate_records(sid, run, native, evidence)
    require(native_master == profile['actual_export_record'], 'frozen export record differs')
    require(sha(wav) == master['sha256'] and wav.stat().st_size == master['bytes'],
            'actual whole master bytes differ')
    require(sha(MODULE) == MODULE_SHA, 'original exporter verification module differs')
    module_spec = importlib.util.spec_from_file_location('original_master_io_only', MODULE)
    original = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(original)
    original._regular(wav)
    with wav.open('rb') as stream:
        require(original._pcm_format(stream) == master['format'], 'actual PCM format differs')
    # No export_passed_original_master call: this only reads the native public WAV.
    context_path = root / 'inline-adapter-context.json'
    context = json.loads(context_path.read_text())
    require(context['main_status_sha256'] == sha(native_path), 'prepared native status differs')
    dest = out / 'actual-original-program-master-export'
    require(not dest.exists(), 'never overwrite a prior master binding')
    dest.mkdir()
    rows = []
    for source in (wav, evidence_path, native_path, Path(profile_path).resolve(), MODULE):
        target = dest / source.name
        os.link(source, target)
        require(spec(target)['sha256'] == sha(source), 'same-byte link differs')
        rows.append(spec(target))
    receipt = dest / 'actual-HOST-master-role-binding.json'
    receipt.write_text(json.dumps({
        'kind': 'actual-native-exported-master-sourceQA-public-role-binding',
        'source_id': sid, 'native_run': run, 'actual_files': rows,
        'actual_export_record': master,
        'original_PCM_format_reader_module_sha256': MODULE_SHA,
        'existing_native_quality_verdict_unchanged': True,
        'pre_video_AF_role_not_final_AAC_decoded_PCM': True,
        'no_private_cache_or_model_or_TTS_or_remote_write': True,
    }, ensure_ascii=False, indent=2) + '\n')
    context['extra_evidence_local_files'] += [r['path'] for r in rows] + [str(receipt)]
    context['actual_original_program_master_public_binding'] = spec(receipt)
    context_path.write_text(json.dumps(context, ensure_ascii=False, indent=2) + '\n')
    return spec(receipt)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--profile', required=True)
    parser.add_argument('--profile-sha256', required=True)
    args = parser.parse_args()
    print(json.dumps(bind(args.profile, args.profile_sha256), ensure_ascii=False))
