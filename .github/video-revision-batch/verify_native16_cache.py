#!/usr/bin/env python3
"""Read back the four exact certified internal16 mother-cache files, with no inference."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import pickle
import sys

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def verify(args):
    root = args.video_root.resolve()
    work, tts = root / 'video', root / 'tts'
    contract = json.loads(args.contract.read_text())
    assert contract['kind'] == 'actual-six-core-native16-correct-Origin-cache-restore-contract'
    assert os.environ.get('STRICT_CACHE') == '1'
    assert sha(work / 'make_video.py') == contract['maker_sha256']
    cache_contract = contract['origin_mother_cache']
    expected = cache_contract['exact_four_file_restore_verification']
    allowed = {row['exact_native_cache_key'] + suffix
               for row in cache_contract['actual_calls'] for suffix in ('', '.单线程')}
    assert len(expected) == 4 and {Path(row['path_below_runner_temp']).name for row in expected} == allowed
    measured = []
    for row in expected:
        rel = Path(row['path_below_runner_temp'])
        assert rel.parts[:3] == ('completion-machine', 'tts', 'cache_tts')
        path = root.parent / rel
        assert path.is_file() and not path.is_symlink()
        assert path.resolve().parent == (tts / 'cache_tts').resolve()
        digest = sha(path)
        assert digest == row['expected_file_SHA256'], 'Restored certified native mother bytes differ: ' + path.name
        if 'expected_literal_text_no_newline' in row:
            assert path.read_bytes() == row['expected_literal_text_no_newline'].encode('ascii')
        measured.append({'native_cache_filename': path.name, 'actual_file_SHA256': digest,
                         'bytes': path.stat().st_size, 'full_file_readback_observed': True})
    assert {name: sha(tts / name) for name in contract['models_SHA256']} == contract['models_SHA256']
    assert sha(tts / 'voice_mb.npy') == contract['voice_SHA256']
    before = {row['native_cache_filename']: row['actual_file_SHA256'] for row in measured}
    os.chdir(work)
    sys.path.insert(0, str(work))
    spec = importlib.util.spec_from_file_location('actual_certified_case_consistent_maker', work / 'make_video.py')
    m = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = m
    spec.loader.exec_module(m)
    source = json.loads(args.request.read_text())
    assert source['no'] == '16'
    sentence = ' '.join(m.R.strip_gloss(c['en']).replace('**', '').strip()
                        for c in source['sentences'][14]['chunks'])
    assert sentence == contract['source_sentence']
    spoken = m.spoken(sentence)
    voice_id = hashlib.sha1(m.np.ascontiguousarray(m.V).tobytes()).hexdigest()
    ordinary = contract['ordinary_next_accepted_text_mother']
    next_text = ' '.join(m.R.strip_gloss(c['en']).replace('**', '').strip()
                         for c in source['sentences'][12]['chunks'])
    assert next_text == ordinary['source_sentence']
    ordinary_calls = []
    def capture_next(text, voice, speed=.95, lang='en-us', **kw):
        assert text == next_text and kw == {}
        model = m._portable_mid(str(tts / 'kokoro-v1.0.onnx'))
        key = hashlib.sha1(repr(('create', model, text, voice_id, float(speed), lang, sorted(kw.items()))).encode()).hexdigest() + '.pkl'
        assert key == ordinary['exact_cache_key']
        assert hashlib.sha256(text.encode()).hexdigest() == ordinary['input_sha256']
        ordinary_calls.append({'sentence': 'S13', 'source_text_input_used': True,
                               'is_phonemes': False, 'exact_native_cache_key': key})
    m._pron(capture_next)(m.spoken(next_text), voice=m.V, speed=m.SPEED, lang='en-us')
    assert len(ordinary_calls) == 1
    ordinary_verified = False
    if args.verify_ordinary_next_mother:
        path = tts / 'cache_tts' / ordinary['exact_cache_key']
        assert path.is_file() and sha(path) == ordinary['pkl_sha256']
        m._条目核对(str(path))
        with path.open('rb') as stream:
            value = pickle.load(stream)
        assert isinstance(value, tuple) and len(value) == 2 and value[1] == 24000
        array = value[0]
        assert array.dtype == m.np.float32 and array.shape == (ordinary['sample_count'],)
        assert hashlib.sha256(m.np.ascontiguousarray(array).tobytes()).hexdigest() == ordinary['array_sha256']
        ordinary_calls[0].update(actual_pkl_SHA256=sha(path), actual_array_SHA256=ordinary['array_sha256'],
                                 original_G72_check_passed=True)
        ordinary_verified = True
    bindings = []
    for item in cache_contract['actual_calls']:
        method = item['method']
        kwargs = {} if method == 'create' else {'clause_pause': 0, 'sentence_pause': 0}
        captured = []
        def callback(text, voice, speed=.95, lang='en-us', **kw):
            model = m._portable_mid(str(tts / ('kokoro-v1.0.onnx' if method == 'create' else 'kokoro-v1.0-timed.onnx')))
            key = hashlib.sha1(repr((method, model, text, voice_id, float(speed), lang, sorted(kw.items()))).encode()).hexdigest() + '.pkl'
            captured.append({'exact_native_cache_key': key, 'input_text_SHA256': hashlib.sha256(text.encode()).hexdigest(),
                             'actual_input_parameters': {'speed': speed, 'lang': lang, **kw}})
        # This callback captures the real producer's dictionary dispatch only;
        # it never calls Kokoro.create or creates another cache entry.
        m._pron(callback)(spoken, voice=m.V, speed=m.SPEED, lang='en-us', **kwargs)
        assert len(captured) == 1
        row = captured[0]
        assert row['exact_native_cache_key'] == item['exact_native_cache_key']
        assert row['input_text_SHA256'] == item['input_text_SHA256'] == contract['input_text_SHA256']
        assert row['actual_input_parameters']['is_phonemes'] is True
        path = tts / 'cache_tts' / item['exact_native_cache_key']
        m._条目核对(str(path))
        with path.open('rb') as stream:
            value = pickle.load(stream)
        assert isinstance(value, tuple) and len(value) == (2 if method == 'create' else 3)
        array, sr = value[:2]
        assert sr == 24000 and array.dtype == m.np.float32 and array.ndim == 1 and m.np.isfinite(array).all()
        assert list(array.shape) == item['array_shape']
        assert hashlib.sha256(m.np.ascontiguousarray(array).tobytes()).hexdigest() == item['array_SHA256']
        if method == 'create_timed':
            assert len(value[2]) == item['timed_token_count']
        bindings.append({**row, 'actual_original_G72_check_passed': True,
                         'native_array_SHA256': item['array_SHA256'], 'sample_rate': sr,
                         'array_shape': list(array.shape), 'raw_array_bytes_exported': False})
    assert {name: sha(tts / 'cache_tts' / name) for name in allowed} == before
    report = {'article': '16', 'exact_certified_internal_reference_cache_verified': True,
              'quality_acceptance': False, 'audio_inference_performed': False,
              'private_cache_or_source_modified': False, 'private_arrays_exported': False,
              'actual_native_cache_key': cache_contract['normal_internal_Actions_cache_key'],
              'actual_native_certification': contract['actual_native_certification'],
              'contract_SHA256': sha(args.contract), 'program_SHA256': sha(__file__),
              'request_SHA256': sha(args.request), 'maker_SHA256': sha(work / 'make_video.py'),
              'all_four_actual_file_readbacks': measured, 'producer_input_bindings': bindings,
              'ordinary_next_dispatch_observed': ordinary_calls,
              'ordinary_next_exact_accepted_text_mother_verified': ordinary_verified,
              'prior_different_CPU_mother_not_claimed_identical': True}
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'article': '16', 'exact_certified_internal_reference_cache_verified': True}))

if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    for name in ['video-root', 'request', 'contract', 'output']:
        p.add_argument('--' + name, type=Path, required=True)
    p.add_argument('--verify-ordinary-next-mother', action='store_true')
    verify(p.parse_args())
