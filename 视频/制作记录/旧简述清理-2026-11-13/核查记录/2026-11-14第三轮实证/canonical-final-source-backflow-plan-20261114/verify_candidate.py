#!/usr/bin/env python3
"""Exercise the candidate on isolated copies only, plus a read-only PAY dry-run."""
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
M = json.loads((HERE / 'apply-manifest.json').read_text())
PAY = Path(M['default_payload_root'])


def hashed(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def run(*args):
    return subprocess.run([sys.executable, str(HERE / 'apply_candidate.py'), *map(str, args)], text=True, capture_output=True)


before = {str(p): hashed(p) for p in [PAY / op['relative_path'] for op in M['operations']]}
dry = run()
assert dry.returncode == 0 and json.loads(dry.stdout)['mode'] == 'dry-run'
with tempfile.TemporaryDirectory(prefix='candidate-test-', dir=HERE) as tmp:
    root = Path(tmp)
    for op in M['operations']:
        target = root / op['relative_path']
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(PAY / op['relative_path'], target)
    untouched = root / '新版定稿/keep-approved.md'
    untouched.parent.mkdir(parents=True)
    untouched.write_text('已批准稿，任何回灌均不得改此文件。\n')
    original_md = untouched.read_bytes()
    applied = run('--apply', '--payload-root', root)
    assert applied.returncode == 0, applied.stderr
    assert json.loads(applied.stdout)['pending_files'] == 18
    assert all(hashed(root / op['relative_path']) == op['after_sha256'] for op in M['operations'])
    assert untouched.read_bytes() == original_md
    idem = run('--apply', '--payload-root', root)
    assert idem.returncode == 0 and json.loads(idem.stdout)['already_final_files'] == 18
    # Create a concurrent edit in one old-state source. No target may change after this failed apply.
    for op in M['operations']:
        shutil.copyfile(PAY / op['relative_path'], root / op['relative_path'])
    target = root / M['operations'][-1]['relative_path']
    target.write_bytes(target.read_bytes() + b'\n# concurrent edit\n')
    concurrent = {str(root / op['relative_path']): hashed(root / op['relative_path']) for op in M['operations']}
    rejected = run('--apply', '--payload-root', root)
    assert rejected.returncode != 0 and 'Concurrent canonical change' in rejected.stderr
    assert all(hashed(Path(p)) == h for p, h in concurrent.items())
    assert untouched.read_bytes() == original_md
assert all(hashed(Path(p)) == h for p, h in before.items())
result = {'status': 'passed_isolated_candidate_test', 'PAY_dry_run_only': True,
          'production_files_pre_post_exact': before,
          'isolated_apply_18_exact': True, 'isolated_idempotent_18': True,
          'concurrent_change_rejected_before_any_write': True,
          'MD_untouched': True, 'production_apply_executed': False,
          'media_or_QC_invoked': False}
(HERE / 'candidate-test-report.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({k: v for k, v in result.items() if k != 'production_files_pre_post_exact'}, ensure_ascii=False))
