"""Read approved repository cache bytes in memory; emit hashes/schema only.

No waveform, token list, raw pickle, model bytes, or private URLs are exported.
This is a diagnostic, not an audio acceptance gate.
"""
import hashlib
import io
import json
from pathlib import Path
import pickle
import re
import subprocess

import numpy as np

BASE = Path('/workspace/work/video-audit70-20261113')
REPO = Path('/workspace/work/github-publication/target')
OUT = BASE / 'core-overlays/reference-reproducibility'
MAKER = BASE / 'final-layout/official/make_video.py'
PREP = BASE / 'ci-direct-43526354790-51/51-checker-reference-preparation.json'
PIN = '64621068034f8b6e09836a6d97210a0e9b2f1ed6'

def sha(b):
    return hashlib.sha256(b).hexdigest()

def git_bytes(path):
    return subprocess.check_output(['git', 'cat-file', 'blob', PIN + ':' + path], cwd=REPO)

prep = json.loads(PREP.read_text())
voice_bytes = git_bytes('视频/工具/配音/voice_mb.npy')
assert sha(voice_bytes) == prep['fixed_voice_sha256']
voice = np.load(io.BytesIO(voice_bytes), allow_pickle=False)
vh = hashlib.sha1(np.ascontiguousarray(voice).tobytes()).hexdigest()
mid = 'kokoro-v1.0.onnx:' + prep['models_sha256']['kokoro-v1.0.onnx'][:16]

source = MAKER.read_text()
ns = {'re': re}
exec(source[source.index('# 朗读用的数字读法'):source.index('def say(t):')], ns)
chosen = [c for c in prep['reference_calls']
          if c['method'] == 'create' and c['reference_kind'] in
          ('title-default-raw', 'whole-default-raw') and c['sentence'] in ('标题', 'S1', 'S2')]
records = []
for c in chosen:
    assert not c['cache_input_is_phonemes']
    text = ns['spoken'](c['source_slice'])
    text_sha = sha(text.encode())
    assert text_sha == c['cache_input_text_sha256']
    key_tuple = ('create', mid, text, vh, float(.95), 'en-us', [])
    key = hashlib.sha1(repr(key_tuple).encode()).hexdigest() + '.pkl'
    assert key == c['exact_native_cache_key']
    path = '视频/配音缓存/' + key
    raw = git_bytes(path)
    marker = git_bytes(path + '.单线程').decode().strip()
    assert marker == sha(raw)[:16]
    # Only unpickle after exact pinned-path/marker checks. No files written.
    item = pickle.loads(raw)
    assert type(item) is tuple and len(item) == 2
    a, sr = item
    assert isinstance(a, np.ndarray) and a.dtype == np.float32 and a.ndim == 1
    assert int(sr) == 24000 and np.isfinite(a).all()
    records.append({
        'sentence': c['sentence'], 'reference_kind': c['reference_kind'],
        'exact_native_cache_key': key, 'method': 'create',
        'input_text_sha256': text_sha, 'input_is_phonemes': False,
        'model_identifier': mid, 'model_sha256': prep['models_sha256']['kokoro-v1.0.onnx'],
        'voice_file_sha256': sha(voice_bytes), 'voice_array_sha1': vh,
        'speed': .95, 'lang': 'en-us', 'keyword_arguments': [],
        'key_independently_reconstructed': True,
        'repository_commit': PIN, 'repository_path': path,
        'cache_pickle_bytes': len(raw), 'cache_pickle_sha256': sha(raw),
        'native_single_thread_marker': marker,
        'marker_matches_exact_original_cache_bytes': True,
        'cache_preexisted_in_actual_native_run': c['cache_preexisted'],
        'schema': {'container': 'tuple', 'tuple_length': 2,
                   'waveform_type': 'ndarray', 'dtype': str(a.dtype),
                   'shape': list(a.shape), 'sample_rate': int(sr),
                   'all_finite': True, 'sample_peak': float(np.max(np.abs(a))),
                   'raw_array_sha256': sha(np.ascontiguousarray(a).tobytes())},
        'raw_bytes_or_samples_exported': False,
    })
report = {
    'purpose': '51 original unprocessed create-cache mother provenance; not acceptance',
    'acceptance': False, 'repository_commit': PIN,
    'actual_run_id': 43526354790, 'actual_preparation_report_sha256': sha(PREP.read_bytes()),
    'maker_sha256': sha(MAKER.read_bytes()), 'checked_count': len(records),
    'raw_create_cache_schema_verified': True,
    'scope_limit': 'Three exact title/S1/S2 raw-create keys checked against original source reading rules and actual native call metadata. Other keys require the same native preflight before use.',
    'provenance_basis': 'The original maker _cached wrapper stores the direct create return tuple before say/clean_tail, consonant grafts, gain, fades, pause edits, concatenation, or PCM quantization. These are original create-cache bytes, not a.wav or generated GT.',
    'records': records,
    'no_waveform_or_cache_bytes_exported': True,
}
dest = OUT / '51-raw-mother-provenance.json'
dest.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'report': str(dest), 'sha256': sha(dest.read_bytes()),
                  'checked': [{'sentence': r['sentence'], 'key': r['exact_native_cache_key'],
                               'sha256': r['cache_pickle_sha256'], 'samples': r['schema']['shape'][0],
                               'marker_match': True} for r in records]}, ensure_ascii=False))
