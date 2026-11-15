"""Outer budget/receipt only; runs one exact already adopted command, unchanged."""
from pathlib import Path
import argparse, datetime, hashlib, json, os, signal, subprocess, time

R = Path(__file__).resolve().parent
ADOPTION = Path('/workspace/work/ROOT-book68-source25-exact-seven-original-normal18-HOST-and-finalV3-execution-adoption-20261115.json')
EXPECTED = 'ee16a94af9975d83c3694e7c90257ddbf6666a0dc22afcdc2029d74b9ff06755'
RESERVE = 419430400

def free():
    s = os.statvfs('/workspace')
    return s.f_bavail * s.f_frsize

def verify(s):
    b = Path(s['path']).read_bytes()
    assert len(b) == s['bytes'] and hashlib.sha256(b).hexdigest() == s['sha256'], s['path']

parser = argparse.ArgumentParser()
parser.add_argument('--phase', choices=['upstream', 'compose', 'finalV3'], required=True)
args = parser.parse_args()
assert hashlib.sha256(ADOPTION.read_bytes()).hexdigest() == EXPECTED
adoption = json.loads(ADOPTION.read_bytes())
for s in adoption['programs'] + [adoption[k] for k in ['source_H', 'caller_H', 'profile', 'exact_commands', 'budget_review']]:
    verify(s)
commands = json.loads(Path(adoption['exact_commands']['path']).read_bytes())
key = {'upstream': 'producer_command', 'compose': 'compose_command',
       'finalV3': 'finalV3_after_real_five_new_boundary_review'}[args.phase]
command = commands[key]
before = free()
assert before >= RESERVE
if args.phase == 'upstream':
    assert before >= RESERVE + 134217728, 'Root first-phase conditional128MiB allowance does not fit'
else:
    budget = R / ('ACTUAL-' + args.phase.upper() + '-PREPHASE-ADDITIONAL-PEAK-BUDGET.json')
    planned = json.loads(budget.read_bytes())
    assert planned['phase'] == args.phase and planned['original_reserve_bytes'] == RESERVE
    assert planned['additional_peak_planning_bytes'] >= 0
    assert before - planned['additional_peak_planning_bytes'] >= RESERVE
    if args.phase == 'finalV3':
        review = Path(command[command.index('--boundary-review') + 1])
        assert review.is_file(), 'The five real frames have not yet been personally reviewed'

log = R / ('ACTUAL-ROOT-ADOPTED-BOOK68-' + args.phase.upper() + '.log')
receipt = R / ('ACTUAL-ROOT-ADOPTED-BOOK68-' + args.phase.upper() + '-EXECUTION.json')
assert not log.exists() and not receipt.exists(), 'Do not restart a prior actual phase'
started = datetime.datetime.now(datetime.timezone.utc).isoformat()
minimum, observations, low_reserve = before, 0, False
with log.open('xb') as output:
    child = subprocess.Popen(command, stdout=output, stderr=subprocess.STDOUT, start_new_session=True,
        env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'})
    while child.poll() is None:
        now = free()
        minimum = min(minimum, now)
        observations += 1
        if now < RESERVE:
            low_reserve = True
            os.killpg(child.pid, signal.SIGTERM)
            break
        time.sleep(.5)
    code = child.wait()
after = free()
minimum = min(minimum, after)
result = {'kind': 'actual-one-exact-root-adopted-book68-normal18-phase-execution',
    'phase': args.phase, 'command': command, 'root_adoption_sha256': EXPECTED,
    'started_UTC': started, 'finished_UTC': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'exit_code': code, 'original_reserve_bytes': RESERVE, 'before_available_bytes': before,
    'minimum_observed_available_bytes': minimum, 'after_available_bytes': after,
    'poll_interval_seconds': .5, 'observation_count': observations,
    'minimum_is_poll_observation_not_continuous_peak_claim': True,
    'terminated_if_observed_below_original_reserve': low_reserve,
    'original_programs_and_quality_guards_unchanged': True,
    'log': {'path': str(log), 'bytes': log.stat().st_size,
            'sha256': hashlib.sha256(log.read_bytes()).hexdigest()}}
receipt.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'path': str(receipt), 'bytes': receipt.stat().st_size,
    'sha256': hashlib.sha256(receipt.read_bytes()).hexdigest(), **result}, ensure_ascii=False))
assert code == 0 and not low_reserve
