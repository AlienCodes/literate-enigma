#!/usr/bin/env python3
"""Prepare two exact native S15 mothers inside the normal internal cache only.

This keeps the corrected Origin pronunciation, creates no video, changes no
existing cache entry or source, and exports only scalar provenance.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import pickle
import platform
import subprocess
import sys

p = argparse.ArgumentParser()
p.add_argument('--tools', type=Path, required=True)
p.add_argument('--video-root', type=Path, required=True)
p.add_argument('--contract', type=Path, required=True)
p.add_argument('--request', type=Path, required=True)
p.add_argument('--accepted-video', type=Path, required=True)
p.add_argument('--output', type=Path, required=True)
a = p.parse_args()
root = a.video_root.resolve()
W, tts = root / 'video', root / 'tts'
cache = tts / 'cache_tts'
contract = json.loads(a.contract.read_text())
request = json.loads(a.request.read_text())
assert not os.environ.get('STRICT_CACHE'), 'Only this dedicated preparatory subprocess is non-strict.'
assert os.environ.get('XG_NOPUSH') == '1'
assert cache.is_dir() and not cache.is_symlink()
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
def aac_sha(path):
    data = subprocess.check_output(['ffmpeg', '-v', 'error', '-nostdin', '-i', str(path),
                                    '-map', '0:a:0', '-c:a', 'copy', '-f', 'adts', '-'])
    return hashlib.sha256(data).hexdigest()
accepted_mp4_before = sha(a.accepted_video)
accepted_aac_before = aac_sha(a.accepted_video)
assert accepted_aac_before == contract['accepted_audio_AAC_SHA256']
inventory = lambda directory: {x.name: sha(x) for x in sorted(directory.iterdir()) if x.is_file()}
before = inventory(cache)
public = a.tools.parent / '配音缓存'
public_before = inventory(public)
existing_wavs = {str(x): sha(x) for x in W.glob('work_*/a.wav')}
source_before = {str(x): sha(x) for x in (W / 'scripts').glob('*.json')}
models = {name: sha(tts / name) for name in contract['models_SHA256']}
assert models == contract['models_SHA256']
assert sha(tts / 'voice_mb.npy') == contract['voice_SHA256']
os.chdir(W)
sys.path.insert(0, str(W))
spec = importlib.util.spec_from_file_location('actual_native16_reference_maker', W / 'make_video.py')
m = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = m
spec.loader.exec_module(m)
source_sentence = ' '.join(m.R.strip_gloss(c['en']).replace('**', '').strip() for c in request['sentences'][14]['chunks'])
assert source_sentence == contract['source_slice'], 'This exact cache preparation must remain bound to actual16 S15.'
assert sha(W / 'make_video.py') == '6945e9bee6db143029bace6c04b4f4df7110c41ba647eee7236b0d0e5ed75203'
m._REPO_CACHE = str(root / 'do-not-export-native16-cache')
assert not Path(m._REPO_CACHE).exists()
sessions = []
for obj in (m.k, m.KT):
    actual_sessions = [v for v in vars(obj).values() if hasattr(v, 'get_session_options')]
    assert actual_sessions
    for session in actual_sessions:
        opts = session.get_session_options()
        assert opts.intra_op_num_threads == opts.inter_op_num_threads == 1
        sessions.append({'intra_op_num_threads': opts.intra_op_num_threads,
                         'inter_op_num_threads': opts.inter_op_num_threads})
text = m.spoken(m.R.strip_gloss(contract['source_slice']).replace('**', ''))
voice_id = hashlib.sha1(m.np.ascontiguousarray(m.V).tobytes()).hexdigest()
calls = []
for method, obj, kwargs, item in [('create', m.k, {}, contract['raw']),
                                ('create_timed', m.KT, {'clause_pause': 0, 'sentence_pause': 0}, contract['timed'])]:
    captured = []
    def capture(text, voice, speed=.95, lang='en-us', **kw):
        model = m._portable_mid(str(tts / ('kokoro-v1.0.onnx' if method == 'create' else 'kokoro-v1.0-timed.onnx')))
        key = hashlib.sha1(repr((method, model, text, voice_id, float(speed), lang, sorted(kw.items()))).encode()).hexdigest() + '.pkl'
        captured.append((key, hashlib.sha256(text.encode()).hexdigest(), kw))
    m._pron(capture)(text, voice=m.V, speed=m.SPEED, lang='en-us', **kwargs)
    assert len(captured) == 1
    key, input_sha, actual_kw = captured[0]
    assert key == item['exact_native_cache_key'] and input_sha == contract['input_text_SHA256']
    assert actual_kw['is_phonemes'] is True
    getattr(obj, method)(text, voice=m.V, speed=m.SPEED, lang='en-us', **kwargs)
    path, marker = cache / key, cache / (key + '.单线程')
    assert path.is_file() and marker.is_file()
    full_sha = sha(path)
    assert marker.read_text().strip() == full_sha[:16]
    m._条目核对(str(path))
    with path.open('rb') as stream:
        value = pickle.load(stream)
    assert isinstance(value, tuple) and len(value) == (2 if method == 'create' else 3)
    array, sample_rate = value[:2]
    assert isinstance(array, m.np.ndarray) and array.dtype == m.np.float32 and array.ndim == 1
    assert sample_rate == 24000 and m.np.isfinite(array).all()
    row = {'method': method, 'exact_native_cache_key': key, 'input_text_SHA256': input_sha,
           'actual_pkl_SHA256': full_sha, 'actual_marker_value': marker.read_text().strip(),
           'array_SHA256': hashlib.sha256(m.np.ascontiguousarray(array).tobytes()).hexdigest(),
           'array_shape': list(array.shape), 'sample_rate': sample_rate,
           'cache_preexisted': key in before, 'native_writer_and_marker_check_passed': True}
    if method == 'create':
        row['known_prior_raw_SHA256'] = item['pkl_sha256']
        row['exact_prior_raw_hash_match'] = full_sha == item['pkl_sha256']
        row['known_prior_raw_array_SHA256'] = item['unprocessed_array_sha256']
        row['exact_prior_raw_array_match'] = row['array_SHA256'] == item['unprocessed_array_sha256']
        row['prior_CPU_identity_was_not_recorded'] = True
        row['prior_byte_comparison_is_observation_not_audio_acceptance'] = True
    else:
        assert isinstance(value[2], list)
        row['timed_token_count'] = len(value[2])
        row['prior_timed_full_SHA256_available'] = False
    calls.append(row)
after = inventory(cache)
allowed = {contract[k]['exact_native_cache_key'] + suffix for k in ('raw', 'timed') for suffix in ('', '.单线程')}
assert set(after) - set(before) <= allowed
assert all(after.get(k) == v for k, v in before.items()), 'Existing private cache changed.'
assert public_before == inventory(public)
assert all(sha(Path(k)) == v for k, v in existing_wavs.items()), 'Existing producer PCM changed.'
assert all(sha(Path(k)) == v for k, v in source_before.items()), 'Existing source changed.'
assert all(sha(tts / name) == value for name, value in models.items())
assert sha(a.accepted_video) == accepted_mp4_before
assert aac_sha(a.accepted_video) == accepted_aac_before
report = {'status': 'prepared_exact_native16_origin_mothers_for_internal_cache',
          'reference_preparation_only_not_audio_acceptance': True, 'article': '16',
          'frozen_request_SHA256': sha(a.request), 'source_sentence': source_sentence,
          'maker_SHA256': sha(W / 'make_video.py'), 'actual_calls': calls,
          'normal_internal_cache_directory': str(cache), 'single_thread_sessions': sessions,
          'models_SHA256': models, 'voice_SHA256': contract['voice_SHA256'],
          'native_machine_architecture': platform.machine(),
          'all_preexisting_private_cache_bytes_unchanged': True,
          'public_repository_cache_unchanged': True, 'preexisting_PCM_and_source_unchanged': True,
          'accepted_public_MP4_SHA256_unchanged': accepted_mp4_before,
          'accepted_public_AAC_SHA256_unchanged': accepted_aac_before,
          'only_two_native_cache_keys_and_their_markers_added': True,
          'private_raw_GT_pickle_or_model_exported': False,
          'cache_persistence_requires_separate_successful_Actions_cache_save': True}
a.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
print(json.dumps(report, ensure_ascii=False))
