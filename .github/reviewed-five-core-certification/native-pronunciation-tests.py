#!/usr/bin/env python3
"""Actual original producer/checker namespaces and dictionaries; no mocked pronunciation."""
import argparse
import ast
import contextlib
import copy
import hashlib
import io
import json
import os
import re
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument('--tools', type=Path, required=True)
p.add_argument('--requests', type=Path, required=True)
p.add_argument('--original-tool', type=Path, required=True)
p.add_argument('--output', type=Path, required=True)
a = p.parse_args()
candidate = (a.tools / '读音核对.py').read_text()
original = a.original_tool.read_text()
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert hashlib.sha256(original.encode()).hexdigest() == '0a3b97e1179e47c0593f69286f4206eecc123cc7ec5d5adf4f5e62457c228a41'
assert hashlib.sha256(candidate.encode()).hexdigest() == '50f4363bb2fc2930be59904cdccfa44fd46f14393a0385c7846028ee25b4e84c'
strip_selftest = lambda text: [ast.dump(n, include_attributes=False) for n in ast.parse(text).body if not isinstance(n, ast.FunctionDef) or n.name != 'selftest']
assert strip_selftest(original) == strip_selftest(candidate)
source = Path('scripts/16.json')
raw = (a.requests / '16.json').read_bytes()
source.write_bytes(raw)
dict_files = {str(p.relative_to(a.tools)): sha(p) for p in (a.tools / '发音词典').glob('*') if p.is_file()}


def load(text):
    # Set __file__ to the real canonical checker location so both exact programs
    # read the same original dictionary files. No initializer or check() is stubbed.
    ns = {'__name__': 'independent_real_pronunciation_namespace', '__file__': str(a.tools / '读音核对.py')}
    exec(compile(text[:text.rindex("if __name__")], str(a.tools / '读音核对.py'), 'exec'), ns)
    return ns


old = load(original)
baseline = old['check']('16')
assert sum(bool(bad) for _, _, bad in baseline) == 0
prior = dict(old['PRON_WORDS'])
log = io.StringIO()
with contextlib.redirect_stdout(log):
    try:
        old['selftest']('16')
        raise AssertionError('Expected real old compound fault-injection bug was not reproduced')
    except SystemExit as e:
        error = str(e)
        assert 'Haber 出现 2 次，换了 1 次' in error
old['PRON_WORDS'].clear()
old['PRON_WORDS'].update(prior)
new = load(candidate)
assert new['check']('16') == baseline
before = dict(new['PRON_WORDS'])
captured = io.StringIO()
with contextlib.redirect_stdout(captured):
    result = new['selftest']('16')
assert result is True and new['PRON_WORDS'] == before
assert new['check']('16') == baseline
expected = ['ammonia', 'sanctuary', 'Karlsruhe', 'Immerwahr', 'Zyklon', 'Clara', 'BASF', 'Haber', 'Haber-Bosch']
lines = captured.getvalue().splitlines()
for w in expected:
    assert any(f'K102 ② {w}：' in line and '报 BAD（当样本）' in line for line in lines)
# Independently apply each exact real uncorrected espeak pronunciation without
# deleting its key. The unchanged real checker must identify the bad word.
faults = []
base_bad = {line for _, line, bad in baseline if bad}
for w in expected:
    raw_ipa = re.sub(r'[,;:.!?]', '', new['KT'].tokenizer.phonemize(w, 'en-us')).strip()
    previous = new['PRON_WORDS'][w]
    new['PRON_WORDS'][w] = raw_ipa
    try:
        got = {line for _, line, bad in new['check']('16') if bad}
        hit = any(re.search(r'\] ' + re.escape(w) + r"(['’]s)? ", line) for line in got - base_bad)
        assert hit, w
        faults.append({'word': w, 'real_uncorrected_espeak_IPA': raw_ipa, 'unchanged_real_checker_reported_BAD': True})
    finally:
        new['PRON_WORDS'][w] = previous
assert new['PRON_WORDS'] == before and new['check']('16') == baseline
# An unrelated failure must still propagate; finally must restore the entry.
original_check = new['check']
def fail_during_fault(no):
    if new['PRON_WORDS'] != before:
        raise RuntimeError('unrelated-checker-exception-test-sentinel')
    return original_check(no)
new['check'] = fail_during_fault
seen = False
with contextlib.redirect_stdout(io.StringIO()):
    try:
        new['selftest']('16')
    except RuntimeError as e:
        assert str(e) == 'unrelated-checker-exception-test-sentinel'
        seen = True
assert seen and new['PRON_WORDS'] == before
new['check'] = original_check
assert new['check']('16') == baseline
assert source.read_bytes() == raw
assert all(sha(a.tools / name) == h for name, h in dict_files.items())
report = {'status': 'passed_real_original_namespace_pronunciation_selftest_repair',
          'original_selftest_real_exception': error, 'candidate_original_full_selftest_true': True,
          'all_non_selftest_AST_nodes_exact': True, 'original_normal_checker_full_output_exact_before_after': True,
          'normal_original_BAD_count': 0, 'actual_nine_real_uncorrected_bad_words': faults,
          'all_dictionary_keys_values_restored': True, 'unrelated_exception_propagates_and_entry_restored': True,
          'original_source_SHA256': hashlib.sha256(raw).hexdigest(), 'candidate_SHA256': sha(a.tools / '读音核对.py'),
          'original_dictionary_files_SHA256_unchanged': dict_files,
          'original_full_producer_namespace_not_mocked': True, 'private_PCM_exported': False,
          'article_audio_or_video_accepted': False, 'old_actual_selftest_stdout': log.getvalue(),
          'new_actual_full_selftest_stdout': captured.getvalue()}
a.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({k: v for k, v in report.items() if k not in {'original_dictionary_files_SHA256_unchanged', 'old_actual_selftest_stdout', 'new_actual_full_selftest_stdout'}}, ensure_ascii=False, indent=2))
