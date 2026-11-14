#!/usr/bin/env python3
"""Additional real06 guard evidence; no native rerun and no PCM export."""
import ast
import copy
import hashlib
import json
import pickle
import re
from pathlib import Path
import numpy as np

O = Path(__file__).resolve().parent
maker = O / 'original-pinned/视频/工具/make_video.py'
source_path = Path('/workspace/work/video-audit70-20261113/payload/视频/脚本/06.json')
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
old_sha = sha(source_path)
d = json.loads(source_path.read_text())
sent = ' '.join(re.sub(r'\*\*', '', c['en']).strip() for c in d['sentences'][-1]['chunks'])
assert d['结尾句']['S19']['接点'] == [98100, 128220]
ns = {'np': np, 're': re, 'SR': 24000, 'V': None, '_EJ': {}}
tree = ast.parse(maker.read_text())
functions = {'_env5', '_ending_parts', '_ending_front', 'spoken', '_year', '_n2w', '_ordinal', '_int2w'}
constants = {'_ONES', '_TENS', '_ORD', '_PL', '_MONTHS', '_ROMAN'}
nodes = [x for x in tree.body if isinstance(x, ast.FunctionDef) and x.name in functions or isinstance(x, ast.Assign) and any(isinstance(t, ast.Name) and t.id in constants for t in x.targets)]
exec(compile(ast.Module(body=nodes, type_ignores=[]), str(maker), 'exec'), ns)
spoken = ns['spoken'](sent)
assert 'June nineteen oh nine,' in spoken
arrays, bindings = {}, []
for speed, key, expected in [(0.9, '8a3136f2036c46650c6ca146fce0f1969aad19bc.pkl', 'f3a0f677b91cf6b7b89121e1570b05d5c31c93d94152c10f685bb9ce4be93121'),
                              (0.78, '4d11379c4698031c8ddeec970e7d141444f6a21f.pkl', '85e1e4be26b3fe243db8f1ba38c86744158bceae064cfd443204489b25e427c8')]:
    p = Path('/workspace/work/video-private-reference-analysis/06-raw-cache-readonly') / key
    assert sha(p) == expected
    arrays[speed] = np.asarray(pickle.loads(p.read_bytes())[0], np.float32)
    bindings.append({'speed': speed, 'key': key, 'full_private_mother_SHA256': expected})


class Adapter:
    def create(self, text, voice, speed, lang):
        assert text == spoken and lang == 'en-us'
        return arrays[float(speed)].copy(), 24000


ns['k'] = Adapter()
candidate = O / 'patch/视频/工具/结尾句接点.py'
f = next(x for x in ast.parse(candidate.read_text()).body if isinstance(x, ast.FunctionDef) and x.name == '保持已有接点')
cns = {}
exec(compile(ast.Module(body=[f], type_ignores=[]), str(candidate), 'exec'), cns)
before = copy.deepcopy(d)
assert cns['保持已有接点'](d, sent, ns['_ending_parts']) is True
assert d == before and sha(source_path) == old_sha
levels = []
for speed, point in zip([.9, .78], [98100, 128220]):
    env = ns['_env5'](arrays[speed])
    levels.append({'speed': speed, 'sample': point, 'original_guard_3x5ms_RMS_max_dB': float(env[point // 120 - 1:point // 120 + 2].max())})
report = {'status': 'additional_real06_old_points_pass_exact_original_guard', 'source_SHA256': old_sha,
          'producer_SHA256': sha(maker), 'candidate_tool_SHA256': sha(candidate), 'test_program_SHA256': sha(Path(__file__)),
          'spoken_English_from_original_function': spoken, 'old_join_samples': [98100, 128220], 'guard_levels': levels,
          'original_ending_settings_and_source_JSON_unchanged': True, 'raw_private_bindings': bindings,
          'method': 'Original AST functions and trusted pinned raw PCM adapter, not a full model namespace run.',
          'production_audio_or_video_accepted': False, 'native_workflow_restarted_or_changed': False,
          'private_PCM_exported': False, 'nonvoice_intervals_changed': False}
(O / 'additional-real06-guard-report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({k: v for k, v in report.items() if k != 'raw_private_bindings'}, ensure_ascii=False, indent=2))
