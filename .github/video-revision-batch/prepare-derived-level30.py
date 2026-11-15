#!/usr/bin/env python3
"""Prepare one genuinely missing original G36 JSON for approved 30 S9.

Original mother synthesis and clip construction stay STRICT_CACHE=1.  Only the
unchanged original _auto_level function may temporarily write its one derived
JSON, in the private cache.  No voice, checker, threshold or source is changed.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile


EXPECTED_MAKER = '4c85e1fbdd2e82c5646d5f58df63c85eca60af4ef521f1d36f765575a568d6f3'
EXPECTED_REQUEST = 'cdf727cb4c6832063421df9da6ab8ae7729cf9df01d6be089a8981c92c360f06'
EXPECTED_KEY = '5684a76d239dd589c24e3483bd1e378b5dcf7a12'
EXPECTED_NAME = f'调平_{EXPECTED_KEY}.json'
EXPECTED_CLIP_HASHES = [
    'f1feec87a7a1174555696abd7c0672df1e0974b3a2273664ec11e557bae587d9',
    '1150614eeef2a65b28a3da2abfca749b4906da643a8f6e4737da2fd50916c1e6',
    '3a3a2f169cf51d183757d5b5ee7b30689f9abae1aae577a542434a6bf0aa5316',
]


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def inventory(folder, recursive=False):
    folder = Path(folder)
    if not folder.exists():
        return {}
    result = {}
    for path in sorted(folder.rglob('*') if recursive else folder.iterdir()):
        if path.is_file():
            assert not path.is_symlink(), 'Protected cache/data files must not be symlinks.'
            result[str(path.relative_to(folder))] = sha(path)
    return result


def inventory_hash(values):
    return hashlib.sha256(json.dumps(values, sort_keys=True).encode()).hexdigest()


def aac_hash(path):
    raw = subprocess.check_output(['ffmpeg', '-v', 'error', '-nostdin', '-i', str(path),
                                   '-map', '0:a:0', '-c:a', 'copy', '-f', 'adts', '-'])
    return hashlib.sha256(raw).hexdigest()


def file_state(path):
    path = Path(path)
    return {'present': path.is_file(), 'sha256': sha(path) if path.is_file() else None}


def clip_binding(clips, tmap, gaps, np):
    # This is the original G51/G36 key expression, with fixed NO30 (the K134
    # equivalent-level suffix does not apply to NO30).
    raw = b''.join(np.ascontiguousarray(c, np.float32).tobytes() for c in clips)
    timing = [(round(t[2], 4), round(t[3], 4)) for t in tmap]
    key = hashlib.sha1(raw + repr(('30', list(gaps), timing)).encode()).hexdigest()
    hashes = [hashlib.sha256(np.ascontiguousarray(c, np.float32).tobytes()).hexdigest()
              for c in clips]
    assert key == EXPECTED_KEY, 'Pre-level inputs do not produce the approved exact G36 key.'
    assert hashes == EXPECTED_CLIP_HASHES, 'Approved original pre-level clip bytes differ.'
    assert [len(c) for c in clips] == [151200, 9120, 34680]
    assert list(gaps) == [0.4] and timing == [(0.0, 6.3), (6.68, 8.125)]
    return {'exact_original_G36_key': key, 'expected_filename': EXPECTED_NAME,
            'clip_float32_sha256': hashes, 'clip_sample_counts': [len(c) for c in clips],
            'sample_rate': 24000, 'gaps_seconds': list(gaps), 'piece_times_seconds': timing}


def ensure_level(module, clips, tmap, gaps, cache, no_export):
    """Call only the unchanged original mathematical function for this exact key."""
    np = module.np
    binding = clip_binding(clips, tmap, gaps, np)
    original = module._auto_level
    old_repository_cache = module._REPO_CACHE
    assert not Path(no_export).exists()
    private_target = Path(cache) / EXPECTED_NAME
    locations = [private_target, Path(old_repository_cache) / EXPECTED_NAME]
    existing = [p for p in locations if p.is_file()]
    for path in existing:
        assert not path.is_symlink()
    if len(existing) == 2:
        assert sha(existing[0]) == sha(existing[1]), 'Two original exact-key caches disagree.'
    before = inventory(cache)
    strict_before = os.environ.get('STRICT_CACHE')
    assert strict_before == '1', 'All preparation except the one derived write must be strict.'
    try:
        if existing:
            # Original strict reader chooses an already present exact cache.
            # Its _to_repo is inert while STRICT_CACHE=1.
            gains = original(clips, tmap, gaps, no='30')
            assert inventory(cache) == before, 'A strict cache hit wrote files.'
            target = existing[0]
            created = False
        else:
            # The original function has no TTS callsite; clips have already
            # been constructed strictly.  Disable only this function's JSON
            # writer guard in this isolated subprocess.  Never export to ROOT.
            module._REPO_CACHE = str(no_export)
            os.environ.pop('STRICT_CACHE')
            gains = original(clips, tmap, gaps, no='30')
            target = private_target
            created = True
    finally:
        module._REPO_CACHE = old_repository_cache
        os.environ['STRICT_CACHE'] = strict_before
    after = inventory(cache)
    additions = set(after) - set(before)
    assert additions == ({EXPECTED_NAME} if created else set()), 'Unexpected derived cache additions.'
    assert all(after.get(k) == v for k, v in before.items()), 'Pre-existing cache bytes changed.'
    assert target.is_file() and not target.is_symlink()
    actual = json.loads(target.read_text())
    assert {int(k): float(v) for k, v in actual.items()} == gains
    assert all(str(k).isdigit() and 1 <= int(k) <= len(tmap)
               and abs(float(v)) <= 6 for k, v in actual.items())
    assert os.environ.get('STRICT_CACHE') == '1'
    return {**binding, 'created_exact_derived_JSON': created,
            'cache_hit_before_measurement': bool(existing), 'derived_JSON_sha256': sha(target),
            'actual_original_returned_gain_dB': gains,
            'actual_original_stored_gain_dB': actual,
            'private_cache_additions': sorted(additions),
            'preexisting_private_cache_bytes_unchanged': True,
            'only_original_auto_level_temporarily_non_strict': created,
            'strict_cache_restored_before_return': True}


def copy_isolated_work(work, isolated):
    isolated.mkdir()
    # Import the actual unchanged producer files, but never copy existing work
    # audio/output.  The isolated sibling tts link points only into private M.
    for path in work.iterdir():
        if path.is_file() and path.suffix in {'.py', '.json'}:
            shutil.copyfile(path, isolated / path.name)
    (isolated / 'scripts').mkdir()
    for path in (work / 'scripts').glob('*.json'):
        shutil.copyfile(path, isolated / 'scripts' / path.name)
    if (work / 'fonts').exists():
        shutil.copytree(work / 'fonts', isolated / 'fonts')


def prepare(args, report):
    assert os.environ.get('STRICT_CACHE') == '1'
    assert os.environ.get('XG_NOPUSH') == '1'
    root, repository = args.video_root.resolve(), args.repository.resolve()
    work, tts = root / 'video', root / 'tts'
    cache, public_cache = tts / 'cache_tts', repository / '视频/配音缓存'
    assert not root.is_relative_to(repository)
    assert cache.is_dir() and not cache.is_symlink()
    assert not args.output.resolve().is_relative_to(root)
    request = work / 'scripts/30.json'
    assert sha(request) == EXPECTED_REQUEST, 'Only the exact root-approved30 source is authorized.'
    assert sha(work / 'make_video.py') == EXPECTED_MAKER
    data = json.loads(request.read_text())
    assert str(data['no']) == '30'
    assert not data.get('停顿处除阻', {}).get('S9')
    assert data['除阻加强']['S9'] == {'1': [6.245, 6.305, 3.5]}
    model_ids = json.loads((repository / '视频/工具/环境/模型校验码.json').read_text())
    model_hashes = {}
    for name in ('kokoro-v1.0.onnx', 'kokoro-v1.0-timed.onnx', 'voices-v1.0.bin'):
        model_hashes[name] = sha(tts / name)
        assert model_hashes[name][:16] == model_ids[name].split(':')[1]
    assert sha(tts / 'voice_mb.npy')[:16] == '1f97658bb5a4280c'
    private_before, public_before = inventory(cache), inventory(public_cache)
    scripts_before = inventory(work / 'scripts')
    producer_before = {p.name: sha(p) for p in work.iterdir() if p.is_file() and p.suffix == '.py'}
    actual_work_before = inventory(work / 'work_30', recursive=True)
    actual_outputs_before = {p.name: sha(p) for p in work.iterdir()
                             if p.is_file() and p.suffix in {'.mp4', '.m4a', '.wav'}}
    wav_before = file_state(work / 'work_30/a.wav')
    accepted_sha_before, accepted_aac_before = sha(args.accepted_video), aac_hash(args.accepted_video)
    report.update({'request_source_sha256': EXPECTED_REQUEST, 'original_maker_sha256': EXPECTED_MAKER,
                   'fixed_voice_sha256': sha(tts / 'voice_mb.npy'), 'models_sha256': model_hashes,
                   'actual_W_producer_PCM_before': wav_before})
    original_cwd = Path.cwd()
    with tempfile.TemporaryDirectory(prefix='private-derived-level30-', dir=root) as temporary:
        temporary = Path(temporary)
        isolated = temporary / 'video'
        copy_isolated_work(work, isolated)
        (temporary / 'tts').symlink_to(tts, target_is_directory=True)
        os.chdir(isolated)
        sys.path.insert(0, str(isolated))
        cache_log = temporary / 'native-cache-input-names.log'
        previous_cache_log = os.environ.get('CACHE_LOG')
        os.environ['CACHE_LOG'] = str(cache_log)
        try:
            spec = importlib.util.spec_from_file_location('unchanged_original_level30_maker', isolated / 'make_video.py')
            module = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = module
            spec.loader.exec_module(module)
            assert sha(isolated / 'make_video.py') == EXPECTED_MAKER
            sentence = data['sentences'][8]
            texts = [re.sub(r'\*\*', '', module.R.strip_gloss(c['en'])).strip()
                     for c in sentence['chunks']]
            text = ' '.join(texts)
            listed, pieces, gaps, previous = module.list_commas(text), [], [], 0
            for match in re.finditer(r'[,;:](?=\s)', text):
                pieces.append((previous, match.end()))
                previous = match.end() + 1
                gaps.append(module.P_LIST if match.start() in listed else module.P_COMMA)
            pieces.append((previous, len(text)))
            clips, tmap = module.sentence_audio(text, pieces, gaps)
            assert inventory(cache) == private_before, 'Strict clip construction changed native cache.'
            assert not (isolated / 'work_30/a.wav').exists(), 'This preparation must not build producer PCM.'
            binding = ensure_level(module, clips, tmap, gaps, cache, temporary / 'no-public-cache-export')
            report.update(binding)
            report['original_sentence_text'] = text
            report['original_pieces'] = pieces
            report['original_auto_level_source_SHA256'] = hashlib.sha256(
                __import__('inspect').getsource(module._auto_level).encode()).hexdigest()
            report['original_loudness_program_SHA256'] = sha(isolated / '响度一致性核对.py')
            loudness = __import__('响度一致性核对')
            report['original_loudness_ffmpeg_version'] = subprocess.check_output(
                [loudness.FF, '-version'], text=True).splitlines()[0]
            used = sorted(set(cache_log.read_text().splitlines())) if cache_log.exists() else []
            mother = []
            for name in used:
                if not re.fullmatch(r'[0-9a-f]{40}\.pkl', name):
                    assert name == EXPECTED_NAME
                    continue
                path = cache / name
                module._条目核对(str(path))
                assert name in private_before and sha(path) == private_before[name]
                mother.append({'exact_native_cache_key': name, 'pkl_sha256': sha(path),
                               'original_G72_provenance_checked': True})
            assert mother, 'No original mother-material cache inputs were recorded.'
            report['original_mother_material_fullSHA_manifest'] = mother
            assert sha(isolated / 'scripts/30.json') == EXPECTED_REQUEST
        finally:
            if previous_cache_log is None:
                os.environ.pop('CACHE_LOG', None)
            else:
                os.environ['CACHE_LOG'] = previous_cache_log
            os.chdir(original_cwd)
    private_after = inventory(cache)
    allowed = {EXPECTED_NAME} if report['created_exact_derived_JSON'] else set()
    assert set(private_after) - set(private_before) == allowed
    assert all(private_after.get(k) == v for k, v in private_before.items())
    assert inventory(public_cache) == public_before, 'Public ROOT cache changed.'
    assert inventory(work / 'scripts') == scripts_before, 'Actual source context changed.'
    assert {p.name: sha(p) for p in work.iterdir() if p.is_file() and p.suffix == '.py'} == producer_before
    assert inventory(work / 'work_30', recursive=True) == actual_work_before
    assert {p.name: sha(p) for p in work.iterdir()
            if p.is_file() and p.suffix in {'.mp4', '.m4a', '.wav'}} == actual_outputs_before
    assert file_state(work / 'work_30/a.wav') == wav_before
    assert sha(args.accepted_video) == accepted_sha_before and aac_hash(args.accepted_video) == accepted_aac_before
    assert os.environ.get('STRICT_CACHE') == '1'
    report.update({'derived_reference_prepared': True,
                   'existing_private_cache_inventory_SHA256_before': inventory_hash(private_before),
                   'existing_private_cache_inventory_SHA256_after': inventory_hash({k: private_after[k] for k in private_before}),
                   'public_ROOT_cache_inventory_SHA256_unchanged': inventory_hash(public_before),
                   'actual_W_producer_PCM_after': file_state(work / 'work_30/a.wav'),
                   'actual_W_source_producer_outputs_and_PCM_unchanged': True,
                   'accepted_video_SHA256_unchanged': accepted_sha_before,
                   'accepted_AAC_ADTS_SHA256_unchanged': accepted_aac_before,
                   'all_preexisting_mother_and_derived_cache_bytes_unchanged': True})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--video-root', required=True, type=Path)
    parser.add_argument('--repository', required=True, type=Path)
    parser.add_argument('--accepted-video', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    report = {'article': '30', 'kind': 'one-exact-original-G36-derived-cache-preparation',
              'derived_reference_prepared': False, 'acceptance': False,
              'official_quality_gate_or_threshold_modified': False,
              'private_PCM_GT_cache_arrays_or_models_exported': False,
              'program_sha256': sha(__file__)}
    try:
        prepare(args, report)
    except BaseException as error:
        report['error'] = {'type': type(error).__name__, 'message': str(error)}
        report['strict_cache_at_exit'] = os.environ.get('STRICT_CACHE')
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
        raise
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'article': '30', 'derived_reference_prepared': True,
                      'created_exact_derived_JSON': report['created_exact_derived_JSON'],
                      'acceptance': False}, ensure_ascii=False))


if __name__ == '__main__':
    main()
