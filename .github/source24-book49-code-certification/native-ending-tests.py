#!/usr/bin/env python3
"""Real CLI tests using the complete original producer namespace and restored raw cache."""
import argparse
import copy
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument('--tools', type=Path, required=True)
p.add_argument('--requests', type=Path, required=True)
p.add_argument('--original-tool', type=Path, required=True)
p.add_argument('--output', type=Path, required=True)
a = p.parse_args()
W = Path.cwd()
target = W / 'scripts/07.json'
original = (a.requests / '07.json').read_bytes()
request = json.loads(original)
assert request['结尾句']['S16']['接点'] == [45598, 57353]
log = []


def run(tool, *flags, expect=0):
    r = subprocess.run([sys.executable, str(tool), '07', *flags], cwd=W, env=os.environ.copy(), text=True, capture_output=True)
    log.append({'tool': str(tool), 'flags': flags, 'exit': r.returncode, 'stdout': r.stdout, 'stderr': r.stderr})
    assert (r.returncode == 0) if expect == 0 else (r.returncode != 0), r.stdout + r.stderr
    return r


tool = a.tools / '结尾句接点.py'
target.write_bytes(original)
run(tool, '--写入', '--保持已审接点')
assert target.read_bytes() == original
good = {'original_approved_points': [45598, 57353], 'JSON_all_bytes_and_all_metadata_preserved': True, 'original_producer_guard_passed': True}
bad = []
for channel, point in [(0, 38700), (1, 48300)]:
    d = copy.deepcopy(request)
    d['结尾句']['S16']['接点'][channel] = point
    raw = (json.dumps(d, ensure_ascii=False, indent=1) + '\n').encode()
    target.write_bytes(raw)
    r = run(tool, '--写入', '--保持已审接点', expect=1)
    assert '接点不在静音里' in r.stdout + r.stderr
    assert target.read_bytes() == raw
    bad.append({'channel': channel, 'sample': point, 'original_bad_point_gate_rejected': True, 'no_automatic_fallback_or_write': True})
target.write_bytes(original)
run(a.original_tool, '--写入')
old_auto = json.loads(target.read_text())
target.write_bytes(original)
run(tool, '--写入')
assert json.loads(target.read_text()) == old_auto
default = {'original_vs_candidate_auto_full_JSON_deep_exact': True, 'actual_auto_points': old_auto['结尾句']['S16']['接点']}
missing = copy.deepcopy(request)
missing.pop('结尾句')
raw = json.dumps(missing, ensure_ascii=False, indent=1).encode()
target.write_bytes(raw)
run(a.original_tool, '--写入')
original_missing = json.loads(target.read_text())
target.write_bytes(raw)
run(tool, '--写入', '--保持已审接点')
assert json.loads(target.read_text()) == original_missing
whole = copy.deepcopy(request)
whole['结尾句']['S16'] = {'整句语速': .8, '依据': '独立测试数据：既有整句模式'}
raw = json.dumps(whole, ensure_ascii=False, indent=1).encode()
target.write_bytes(raw)
run(tool, '--写入', '--保持已审接点')
assert target.read_bytes() == raw
# Exercise the actual shell's pipeline failure propagation before later rebuilding work.
head = (a.tools / '草稿声音.sh').read_text().split('for i in 1 2 3; do', 1)[0]
headfile = a.output.parent / 'ending-shell-head.sh'
headfile.write_text(head)
d = copy.deepcopy(request)
d['结尾句']['S16']['接点'][0] = 38700
raw = json.dumps(d, ensure_ascii=False, indent=1).encode()
target.write_bytes(raw)
r = subprocess.run(['bash', str(headfile), '07'], cwd=W, env={**os.environ, 'XG_TOOLS': str(a.tools), 'XG_KEEP_REVIEWED_ENDING': '1'}, text=True, capture_output=True)
log.append({'tool': 'actual shell ending prefix', 'exit': r.returncode, 'stdout': r.stdout, 'stderr': r.stderr})
assert r.returncode != 0 and '接点不在静音里' in r.stdout + r.stderr and target.read_bytes() == raw
target.write_bytes(original)
report = {'status': 'passed_real_complete_original_namespace_ending_mode_tests', 'production_audio_or_video_acceptance': False,
          'good_original_source': good, 'bad_front_and_tail': bad, 'default_mode': default,
          'no_existing_points_uses_exact_original_auto_algorithm': True, 'whole_speed_mode_preserves_JSON_bytes': True,
          'actual_shell_pipeline_bad_point_exit_propagated': True,
          'request_SHA256': hashlib.sha256(original).hexdigest(),
          'candidate_tool_SHA256': hashlib.sha256(tool.read_bytes()).hexdigest(),
          'original_producer_namespace_not_replaced_by_mocks': True,
          'private_raw_audio_exported': False, 'calls': log}
a.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({k: v for k, v in report.items() if k != 'calls'}, ensure_ascii=False, indent=2))
