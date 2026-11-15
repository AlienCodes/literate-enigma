#!/usr/bin/env python3
"""Prepare exact independent checker references before strict production.

Uses the unchanged maker's original say() and native single-thread cache writer.
Private cache bytes stay under the private restored machine; output is scalar
provenance only. This does not approve audio, change a checker, or build a video.
"""
import argparse
import hashlib
import importlib.util
import json
import os
import pickle
from pathlib import Path
import re
import subprocess
import sys


OBSERVED_MISSING = {
    '10': {'1779cdbdd68560e1ecd50d812c5c8a8a0df6394c.pkl',
           '849001ae0dc6c1436d06f5c608358bcdca630f4b.pkl',
           'd50d3642f8022ba1c409e7ef50fabe55b50d9c8e.pkl'},
    '11': {'e4439b8ee6b2194812f91d988de7976fd5567207.pkl',
           '028265e74b4cc25c104edcc89ac79b6c02454ede.pkl',
           '54174f758622cfdd5771023fffb879634fac1f6a.pkl'},
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
    # Complete active callsite audit: title/whole raw at SPEED (首尾/可闻声/
    # 疑点), title/whole timed at SPEED with zero model pauses (词尾/停顿/
    # 高亮), punctuation slices (停顿 ratio), every display chunk of multi-
    # chunk sentences (高亮乙). Word phonemize() calls only tokenize; they do
    # not synthesize. Configured ending speeds/prefixes and donor consonants
    # are producer inputs, preserved in the original existing cache; no new
    # alternate ending speeds, donor words, or voice controls are invented.
    import numpy as np
    captured = []
    def cache_probe(method):
        filename = 'kokoro-v1.0.onnx' if method == 'create' else 'kokoro-v1.0-timed.onnx'
        model_id = module._portable_mid(str(tts / filename))
        def capture(text, voice, speed=1.0, lang='en-us', **kwargs):
            voice_id = (hashlib.sha1(np.ascontiguousarray(voice).tobytes()).hexdigest()
                        if not isinstance(voice, str) else voice)
            key = hashlib.sha1(repr((method, model_id, text, voice_id, float(speed),
                                     lang, sorted(kwargs.items()))).encode()).hexdigest() + '.pkl'
            captured.append((key, hashlib.sha256(text.encode()).hexdigest(), kwargs.get('is_phonemes', False)))
        return module._pron(capture)
    probes = {method: cache_probe(method) for method in ('create', 'create_timed')}
    references = []
    unique = {}
    def reference(text, label, kind, *, piece=None, method='create'):
        spoken = module.spoken(re.sub(r'\*\*', '', module.R.strip_gloss(text)))
        kwargs = {'clause_pause': 0, 'sentence_pause': 0} if method == 'create_timed' else {}
        before_count = len(captured)
        probes[method](spoken, voice=module.V, speed=module.SPEED, lang='en-us', **kwargs)
        assert len(captured) == before_count + 1
        key, input_hash, phonemes = captured[-1]
        references.append({'sentence': label, 'piece': piece, 'reference_kind': kind,
                           'method': method, 'source_slice': text,
                           'exact_native_cache_key': key, 'cache_input_text_sha256': input_hash,
                           'cache_input_is_phonemes': phonemes, 'cache_preexisted': key in private_before})
        unique.setdefault(key, (method, text, kwargs))
    reference(source_data['title_en'], '标题', 'title-default-raw')
    reference(source_data['title_en'], '标题', 'title-default-timed', method='create_timed')
    for si, sentence_data in enumerate(source_data['sentences'], 1):
        texts = [re.sub(r'\*\*', '', module.R.strip_gloss(c['en'])).strip()
                 for c in sentence_data['chunks']]
        sentence = ' '.join(texts)
        label = f'S{si}'
        reference(sentence, label, 'whole-default-raw')
        reference(sentence, label, 'whole-default-timed', method='create_timed')
        if len(texts) > 1:
            for ci, text in enumerate(texts, 1):
                reference(text, label, 'highlight-display-chunk', piece=ci)
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
            reference(sentence[begin:end], label, 'pause-punctuation-slice', piece=pi)
    assert OBSERVED_MISSING.get(no, set()) <= set(unique), 'Actual observed missing keys are not in original checker enumeration.'
    missing_keys = set(unique) - set(private_before)
    for key, (method, text_slice, kwargs) in unique.items():
        if key in private_before:
            module._条目核对(str(cache / key))
        else:
            # The unchanged native writer creates this exact pkl and marker.
            # No stand-in audio, alternate name, or PCM overlay is supplied.
            if method == 'create':
                module.say(text_slice)
            else:
                module.KT.create_timed(module.spoken(re.sub(r'\*\*', '', module.R.strip_gloss(text_slice))),
                                       voice=module.V, speed=module.SPEED, lang='en-us', **kwargs)
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
    # Original unprocessed mother material: publish hashes/schema only. This
    # proves the native restored entries without exporting cache or samples.
    raw_cache_manifest = []
    for key, (method, _, _) in unique.items():
        if method != 'create':
            continue
        path = cache / key
        marker = cache / (key + '.单线程')
        item = {'exact_native_cache_key': key, 'pkl_sha256': sha(path),
                'native_single_thread_marker_present': marker.is_file(),
                'input_proofs': [r for r in references if r['exact_native_cache_key'] == key]}
        if marker.is_file():
            item['native_single_thread_marker_value'] = marker.read_text().strip()
            item['native_single_thread_marker_matches'] = item['native_single_thread_marker_value'] == item['pkl_sha256'][:16]
        try:
            with path.open('rb') as stream:
                value = pickle.load(stream)
            item['container_type'] = type(value).__name__
            item['container_length'] = len(value)
            if isinstance(value, tuple) and len(value) == 2 and isinstance(value[0], np.ndarray):
                samples, sample_rate = value
                item.update({'sample_rate': int(sample_rate), 'dtype': str(samples.dtype),
                             'shape': list(samples.shape),
                             'unprocessed_array_sha256': hashlib.sha256(np.ascontiguousarray(samples).tobytes()).hexdigest()})
        except Exception as exc:
            item['schema_diagnostic_error'] = type(exc).__name__
        raw_cache_manifest.append(item)
    result = {
        'article': no, 'purpose': 'prepare original checker title/whole/punctuation/chunk references; not audio acceptance',
        'reference_prepared': True, 'acceptance': False,
        'basis': '视频/制作记录/改门_GitHub化.md:39; original single-thread cache preparation before strict production',
        'source_sha256': source_before, 'maker_sha256': module_before,
        'checker_program_sha256': {name: sha(repository / '视频/工具' / name) for name in (
            '停顿位置精确核对.py', '高亮同步核对.py', '句首句尾与停顿位置核对.py',
            '可闻声保全核对.py', '词尾辅音核对.py', '疑点清单.py')},
        'reference_calls': references, 'unique_reference_key_count': len(unique),
        'raw_mother_cache_scalar_manifest': raw_cache_manifest,
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
