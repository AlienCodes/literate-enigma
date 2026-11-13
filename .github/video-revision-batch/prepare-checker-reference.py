#!/usr/bin/env python3
"""Prepare only an observed missing checker slice, outside strict production.

Uses the unchanged maker's original say() and native single-thread cache writer.
Private cache bytes stay under the private restored machine; output is scalar
provenance only. This does not approve audio, change a checker, or build a video.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys


EXPECTED = {
    '10': '1779cdbdd68560e1ecd50d812c5c8a8a0df6394c.pkl',
    '11': 'e4439b8ee6b2194812f91d988de7976fd5567207.pkl',
}


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def inventory(folder):
    if not folder.exists():
        return {}
    result = {}
    for path in sorted(folder.iterdir()):
        if path.is_file():
            assert not path.is_symlink(), 'Cache inventory must not follow symlinks.'
            result[path.name] = sha(path)
    return result


def digest_inventory(values):
    return hashlib.sha256(json.dumps(values, sort_keys=True).encode()).hexdigest()


def aac_hash(path):
    raw = subprocess.check_output(['ffmpeg', '-v', 'error', '-i', str(path), '-map', '0:a:0',
                                   '-c:a', 'copy', '-f', 'adts', '-'])
    return hashlib.sha256(raw).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--article', required=True, choices=sorted(EXPECTED))
    parser.add_argument('--video-root', required=True, type=Path)
    parser.add_argument('--repository', required=True, type=Path)
    parser.add_argument('--accepted-video', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    no = args.article
    root, repository = args.video_root.resolve(), args.repository.resolve()
    work, tts = root / 'video', root / 'tts'
    cache, public_cache = tts / 'cache_tts', repository / '视频/配音缓存'
    assert not os.environ.get('STRICT_CACHE'), 'Preparation must be a separate non-strict subprocess.'
    assert os.environ.get('XG_NOPUSH') == '1'
    assert not root.is_relative_to(repository)
    assert cache.is_dir() and not cache.is_symlink()
    assert not args.output.resolve().is_relative_to(root)
    model_ids = json.loads((repository / '视频/工具/环境/模型校验码.json').read_text())
    models = {}
    for name in ('kokoro-v1.0.onnx', 'kokoro-v1.0-timed.onnx', 'voices-v1.0.bin'):
        actual = sha(tts / name)
        assert actual[:16] == model_ids[name].split(':')[1], f'Original model mismatch: {name}'
        models[name] = actual
    voice_sha = sha(tts / 'voice_mb.npy')
    assert voice_sha[:16] == '1f97658bb5a4280c', 'Original fixed voice file mismatch.'
    wav = work / f'work_{no}/a.wav'
    wav_before = sha(wav) if wav.is_file() else None
    accepted_aac_before = aac_hash(args.accepted_video)
    private_before = inventory(cache)
    public_before = inventory(public_cache)
    module_before = sha(work / 'make_video.py')
    source = work / f'scripts/{no}.json'
    source_before = sha(source)
    source_data = json.loads(source.read_text())
    os.chdir(work)
    sys.path.insert(0, str(work))
    spec = importlib.util.spec_from_file_location('original_checker_reference_maker', work / 'make_video.py')
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    # Original cache provenance checks remain active. Only the automatic copy
    # destination is a nonexistent private path so no pkl is exported to ROOT.
    module._REPO_CACHE = str(root / 'do-not-export-reference-cache')
    assert not Path(module._REPO_CACHE).exists()
    sessions = []
    for obj in (module.k, module.KT):
        values = list(vars(obj).values())
        candidates = [v for v in values if hasattr(v, 'get_session_options')]
        assert candidates, 'Cannot verify original single-thread ONNX session.'
        for session in candidates:
            options = session.get_session_options()
            assert options.intra_op_num_threads == options.inter_op_num_threads == 1
            sessions.append({'intra_op_num_threads': options.intra_op_num_threads,
                             'inter_op_num_threads': options.inter_op_num_threads})
    # Exact same sentence construction and first punctuation slice as the
    # unchanged pause checker. The observed cache key must match before say().
    sentence = ' '.join(re.sub(r'\*\*', '', module.R.strip_gloss(c['en'])).strip()
                        for c in source_data['sentences'][0]['chunks'])
    punctuation = next(re.finditer(r'[,;:](?=\s)', sentence))
    text_slice = sentence[:punctuation.end()]
    spoken = module.spoken(re.sub(r'\*\*', '', module.R.strip_gloss(text_slice)))
    import numpy as np
    voice_id = hashlib.sha1(np.ascontiguousarray(module.V).tobytes()).hexdigest()
    model_id = module._portable_mid(str(tts / 'kokoro-v1.0.onnx'))
    key = hashlib.sha1(repr(('create', model_id, spoken, voice_id, float(module.SPEED),
                             'en-us', [])).encode()).hexdigest() + '.pkl'
    assert key == EXPECTED[no], 'Derived original checker slice is not the observed missing cache key.'
    destination = cache / key
    existed = destination.is_file()
    # No stand-in audio, alternate cache name, parameter change, or PCM overlay.
    module.say(text_slice)
    private_after = inventory(cache)
    public_after = inventory(public_cache)
    allowed_additions = {key, key + '.单线程'}
    assert set(private_after) - set(private_before) <= allowed_additions
    assert all(private_after.get(k) == v for k, v in private_before.items()), 'Existing private cache changed.'
    assert public_after == public_before, 'Public repository cache changed.'
    marker = cache / (key + '.单线程')
    assert destination.is_file() and marker.is_file()
    assert marker.read_text().strip() == sha(destination)[:16], 'Native single-thread marker mismatch.'
    assert source_before == sha(source) and module_before == sha(work / 'make_video.py')
    wav_after = sha(wav) if wav.is_file() else None
    assert wav_before == wav_after, 'Existing producer PCM changed.'
    accepted_aac_after = aac_hash(args.accepted_video)
    assert accepted_aac_before == accepted_aac_after, 'Accepted video AAC changed.'
    result = {
        'article': no, 'purpose': 'prepare an actually missing checker-only reference slice; not audio acceptance',
        'reference_prepared': True, 'acceptance': False,
        'basis': '视频/制作记录/改门_GitHub化.md:39; original single-thread cache preparation before strict production',
        'source_sha256': source_before, 'maker_sha256': module_before,
        'source_slice': text_slice, 'spoken_slice': spoken,
        'observed_missing_cache_key': key, 'cache_preexisted': existed,
        'new_private_cache_names': sorted(set(private_after) - set(private_before)),
        'native_single_thread_marker_verified': True, 'single_thread_sessions': sessions,
        'models_sha256': models, 'fixed_voice_sha256': voice_sha,
        'existing_private_cache_count': len(private_before),
        'existing_private_cache_inventory_sha256_before': digest_inventory(private_before),
        'existing_private_cache_inventory_sha256_after': digest_inventory({k: private_after[k] for k in private_before}),
        'existing_private_cache_bytes_unchanged': True,
        'public_repository_cache_inventory_sha256': digest_inventory(public_before),
        'public_repository_cache_unchanged': True,
        'producer_pcm_existed_before': wav_before is not None,
        'producer_pcm_sha256_before': wav_before, 'producer_pcm_sha256_after': wav_after,
        'accepted_aac_adts_sha256_before': accepted_aac_before,
        'accepted_aac_adts_sha256_after': accepted_aac_after,
        'strict_cache_disabled_only_for_this_reference_preparation_subprocess': True,
        'private_cache_exported': False,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'article': no, 'reference_prepared': True, 'private_cache_exported': False,
                      'observed_missing_cache_key': key}, ensure_ascii=False))


if __name__ == '__main__':
    main()
