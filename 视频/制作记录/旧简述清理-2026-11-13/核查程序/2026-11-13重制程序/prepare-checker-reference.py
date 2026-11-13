#!/usr/bin/env python3
"""Prepare exactly the original checker's punctuation slices, before production.

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


OBSERVED_MISSING = {
    '10': {'1779cdbdd68560e1ecd50d812c5c8a8a0df6394c.pkl',
           '849001ae0dc6c1436d06f5c608358bcdca630f4b.pkl'},
    '11': {'e4439b8ee6b2194812f91d988de7976fd5567207.pkl',
           '028265e74b4cc25c104edcc89ac79b6c02454ede.pkl'},
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
    parser.add_argument('--article', required=True, choices=[f'{n:02d}' for n in range(1, 71)])
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
    # Exact sentence/slice enumeration from 停顿位置精确核对.py's ratio
    # expression. A dry call through the original pronunciation wrapper
    # captures the exact cache parameters without synthesizing any audio.
    import numpy as np
    model_id = module._portable_mid(str(tts / 'kokoro-v1.0.onnx'))
    captured = []
    def capture(text, voice, speed=1.0, lang='en-us', **kwargs):
        voice_id = (hashlib.sha1(np.ascontiguousarray(voice).tobytes()).hexdigest()
                    if not isinstance(voice, str) else voice)
        key = hashlib.sha1(repr(('create', model_id, text, voice_id, float(speed),
                                 lang, sorted(kwargs.items()))).encode()).hexdigest() + '.pkl'
        captured.append((key, hashlib.sha256(text.encode()).hexdigest(), kwargs.get('is_phonemes', False)))
    probe = module._pron(capture)
    references = []
    unique = {}
    for si, sentence_data in enumerate(source_data['sentences'], 1):
        sentence = ' '.join(re.sub(r'\*\*', '', module.R.strip_gloss(c['en'])).strip()
                            for c in sentence_data['chunks'])
        punctuation = list(re.finditer(r'[,;:](?=\s)', sentence))
        if not punctuation:
            continue
        pieces = []
        previous = 0
        for item in punctuation:
            pieces.append((previous, item.end()))
            previous = item.end() + 1
        pieces.append((previous, len(sentence)))
        for pi, (begin, end) in enumerate(pieces, 1):
            text_slice = sentence[begin:end]
            spoken = module.spoken(re.sub(r'\*\*', '', module.R.strip_gloss(text_slice)))
            before_count = len(captured)
            probe(spoken, voice=module.V, speed=module.SPEED, lang='en-us')
            assert len(captured) == before_count + 1
            key, input_hash, phonemes = captured[-1]
            references.append({'sentence': f'S{si}', 'piece': pi, 'source_slice': text_slice,
                               'exact_native_cache_key': key, 'cache_input_text_sha256': input_hash,
                               'cache_input_is_phonemes': phonemes, 'cache_preexisted': key in private_before})
            unique.setdefault(key, text_slice)
    assert OBSERVED_MISSING.get(no, set()) <= set(unique), 'Actual observed missing keys are not in original checker enumeration.'
    missing_keys = set(unique) - set(private_before)
    for key, text_slice in unique.items():
        if key in private_before:
            module._条目核对(str(cache / key))
        else:
            # The unchanged native writer creates this exact pkl and marker.
            # No stand-in audio, alternate name, or PCM overlay is supplied.
            module.say(text_slice)
    private_after = inventory(cache)
    public_after = inventory(public_cache)
    allowed_additions = missing_keys | {key + '.单线程' for key in missing_keys}
    assert set(private_after) - set(private_before) == allowed_additions
    assert all(private_after.get(k) == v for k, v in private_before.items()), 'Existing private cache changed.'
    assert public_after == public_before, 'Public repository cache changed.'
    for key in missing_keys:
        destination, marker = cache / key, cache / (key + '.单线程')
        assert destination.is_file() and marker.is_file()
        assert marker.read_text().strip() == sha(destination)[:16], 'Native single-thread marker mismatch.'
    assert source_before == sha(source) and module_before == sha(work / 'make_video.py')
    wav_after = sha(wav) if wav.is_file() else None
    assert wav_before == wav_after, 'Existing producer PCM changed.'
    accepted_aac_after = aac_hash(args.accepted_video)
    assert accepted_aac_before == accepted_aac_after, 'Accepted video AAC changed.'
    result = {
        'article': no, 'purpose': 'prepare missing references from the original full punctuation-slice enumeration; not audio acceptance',
        'reference_prepared': True, 'acceptance': False,
        'basis': '视频/制作记录/改门_GitHub化.md:39; original single-thread cache preparation before strict production',
        'source_sha256': source_before, 'maker_sha256': module_before,
        'checker_program_sha256': sha(repository / '视频/工具/停顿位置精确核对.py'),
        'reference_calls': references, 'unique_reference_key_count': len(unique),
        'missing_reference_key_count': len(missing_keys),
        'observed_missing_keys_covered': sorted(OBSERVED_MISSING.get(no, set())),
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
                      'unique_reference_key_count': len(unique),
                      'missing_reference_key_count': len(missing_keys)}, ensure_ascii=False))


if __name__ == '__main__':
    main()
