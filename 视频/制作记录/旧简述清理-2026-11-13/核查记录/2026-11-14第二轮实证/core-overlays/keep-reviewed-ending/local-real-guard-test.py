#!/usr/bin/env python3
"""Actual pinned mother PCM + exact original guard functions; no private arrays exported."""
import ast
import copy
import hashlib
import json
import pickle
import re
import subprocess
import sys
import types
from pathlib import Path
import numpy as np

O = Path(__file__).resolve().parent
maker = O / 'original-pinned/视频/工具/make_video.py'
candidate = O / 'patch/视频/工具/结尾句接点.py'
private = Path('/workspace/work/video-private-reference-analysis/07-raw-cache-readonly')
source_path = Path('/workspace/work/video-audit70-20261113/payload/视频/脚本/07.json')
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
source_sha = sha(source_path)
d = json.loads(source_path.read_text())
sent = ' '.join(re.sub(r'\*\*', '', c['en']).strip() for c in d['sentences'][-1]['chunks'])
assert sent == 'Inky, somewhere beyond the pipe, remained wholly oblivious to the debate.'
e = d['结尾句'][f"S{len(d['sentences'])}"]
assert e['接点'] == [45598, 57353]
arrays = {}
evidence = []
for speed, key, want in [(0.9, '5f93aa786be55c461e644507810b77990fa6e4da.pkl', 'd92e6ab085713243e61f92fc237677e1429e4bd5dd7d7cb1e187ab29ce18547e'),
                          (0.78, '37112da59e215ce16f6352f7f133828c39d090a8.pkl', '857ed318a2254d1b8971499cdc5c8d1c118957ef9978cd0653bfe7165b59fc74')]:
    p = private / key
    assert sha(p) == want
    value = pickle.loads(p.read_bytes())
    assert isinstance(value, tuple) and value[1] == 24000
    arrays[speed] = np.asarray(value[0], np.float32)
    evidence.append({'speed': speed, 'cache_key': key, 'pinned_private_mother_pkl_sha256': want,
                     'PCM_array_sha256': hashlib.sha256(arrays[speed].tobytes()).hexdigest(), 'samples': len(arrays[speed])})


class PinnedRawAdapter:
    """Only replace model initialization with exact trusted raw PCM; guard code is original."""
    def create(self, text, voice, speed, lang):
        assert text == sent and lang == 'en-us'
        return arrays[float(speed)].copy(), 24000


ns = {'np': np, 're': re, 'SR': 24000, 'V': 'PINNED_VOICE_INPUT_BINDING_IN_EXISTING_REPORT', 'k': PinnedRawAdapter(), '_EJ': {}}
tree = ast.parse(maker.read_text())
parts = [x for x in tree.body if isinstance(x, ast.FunctionDef) and x.name in {'_env5', '_ending_parts', '_ending_front', 'spoken'}]
parts += [x for x in tree.body if isinstance(x, ast.Assign) and any(isinstance(t, ast.Name) and t.id == '_MONTHS' for t in x.targets)]
exec(compile(ast.Module(body=parts, type_ignores=[]), str(maker), 'exec'), ns)
guard = ns['_ending_parts']
ctree = ast.parse(candidate.read_text())
func = next(x for x in ctree.body if isinstance(x, ast.FunctionDef) and x.name == '保持已有接点')
scope = {}
exec(compile(ast.Module(body=[func], type_ignores=[]), str(candidate), 'exec'), scope)
keep = scope['保持已有接点']
old = copy.deepcopy(d)
assert keep(d, sent, guard) is True and d == old
guard(sent, e)
measurements = []
for speed, point in zip([0.9, .78], e['接点']):
    env = ns['_env5'](arrays[speed])
    measurements.append({'speed': speed, 'join_sample': point,
                         'original_3x5ms_RMS_max_dB': float(env[max(0, point // 120 - 1):point // 120 + 2].max())})
bad_cases = []
for channel, speed in [(0, .9), (1, .78)]:
    b = copy.deepcopy(d)
    point = int(np.argmax(ns['_env5'](arrays[speed]))) * 120 + 60
    b['结尾句']['S16']['接点'][channel] = point
    prior = copy.deepcopy(b)
    try:
        keep(b, sent, guard)
        raise AssertionError('Actual original bad-point gate was bypassed')
    except SystemExit as error:
        assert '接点不在静音里' in str(error)
        bad_cases.append({'channel': channel, 'speed': speed, 'sample': point, 'original_error': str(error), 'rejected': True})
    assert b == prior
assert sha(source_path) == source_sha
r = subprocess.run([sys.executable, str(candidate), '--自检'], text=True, capture_output=True)
assert r.returncode == 0, r.stdout + r.stderr
(O / 'candidate-original-selftests.log').write_text(r.stdout + r.stderr)
r = subprocess.run(['bash', '-n', str(O / 'patch/视频/工具/草稿声音.sh')], capture_output=True, text=True)
assert r.returncode == 0, r.stderr
report = {'status': 'passed_local_real_original_guard_positive_negative', 'source_sha256': source_sha,
          'test_program_sha256': sha(Path(__file__)),
          'producer_sha256': sha(maker), 'candidate_tool_sha256': sha(candidate),
          'method': 'Execute unchanged original _env5/_ending_parts/spoken AST definitions; initialize exact original raw arrays through a pinned read-only model adapter. Full original model namespace is reserved for native certification.',
          'original_approved_join': e['接点'], 'original_guard_measurements': measurements,
          'actual_bad_front_and_tail_rejected_by_original_guard': bad_cases,
          'all_original_selftests_exit': 0, 'bash_syntax_exit': 0,
          'PAY_source_and_all_ending_settings_unchanged': d == old and sha(source_path) == source_sha,
          'private_mother_scalar_bindings': evidence, 'private_PCM_exported': False,
          'full_original_quickcheck_ran_here': False, 'production_audio_or_video_accepted': False}
(O / 'local-real-guard-report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({k: v for k, v in report.items() if k not in {'private_mother_scalar_bindings', 'method'}}, ensure_ascii=False, indent=2))
