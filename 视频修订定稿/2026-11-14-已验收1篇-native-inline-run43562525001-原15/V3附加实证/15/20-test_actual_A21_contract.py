"""Actual17 contract and mutation checks; no acoustic/threshold/media change."""
import ast
import copy
import hashlib
import json
from pathlib import Path
import tempfile

import delivery as D
import release_contract as R
from import_actual_article import explicit_approved_layout_reference

HERE = Path(__file__).resolve().parent
NATIVE = Path('/workspace/work/video-audit70-20261113/next-passed-native/43562525001/17')
FILES = NATIVE / 'files'
raw_path = NATIVE / 'artifact-files/17-approved-audio-qc.json'
native = D.load(FILES / '17-status.json')
raw = D.load(raw_path)
copy_proof = D.load(FILES / '17-summary-verification.json')
selected = native['video_sha256']
aac = native['canonical_aac_adts_sha256']
evidence = {D.digest(raw_path), D.digest(FILES / '17-summary-verification.json'), D.digest(FILES / '17-status.json')}
review = {'tool': 'audio-a21-qc.py', 'actual_new_output': True, 'status': 'passed',
          'canonical_video_sha256': selected, 'reviewed_canonical_video_sha256': raw['canonical_sha256'],
          'binding': 'reviewed_native_pre_card_then_exact_audio_copy',
          'copy_verification_sha256': D.digest(FILES / '17-summary-verification.json'),
          'report_sha256': D.digest(raw_path), 'program_sha256': raw['program_sha256'],
          'reference_file_sha256': raw['reference_file_sha256'],
          'request_source_sha256': native['approved_audio_repair_scope']['request_source_sha256']}

def check(args):
    r, n, q, p, a = args
    result = R.canonical_audio_contract(r, n, '17', selected, a, evidence, D.digest(FILES / '17-status.json'), True)
    assert result == 'actual_dedicated_audio_qc_then_verified_exact_AAC_copy'
    assert R.reviewed_canonical_audio_copy(r, n, q, p, '17', selected, a)
    return result

original = [review, native, raw, copy_proof, aac]
basis = check(original)
assert native['accepted_prior_aac_identical'] is False
cases = {}
def bad(label, mutate):
    a = copy.deepcopy(original)
    mutate(a)
    # Actual file/native object identity is checked independently in fullV3;
    # here keep objects consistent to exercise the deeper semantic guards.
    a[1]['approved_audio_qc'] = a[2]
    cases[label] = a

bad('wrong_actual_program', lambda a: a[0].update(program_sha256='0'*64))
bad('wrong_reference', lambda a: a[0].update(reference_file_sha256='0'*64))
bad('wrong_request', lambda a: a[0].update(request_source_sha256='0'*64))
bad('wrong_repair_scope', lambda a: a[1]['approved_audio_repair_scope'].update(kind='arbitrary-change'))
bad('original_full_pipeline_not_passed', lambda a: a[1].update(canonical_pipeline_passed=False))
bad('wrong_original_A21_program', lambda a: a[2].update(original_A21_program_sha256='0'*64))
bad('one_original_phase_failed', lambda a: a[2]['actual_original_A21']['phase_results'][0].update(single_release_original_A21_passed=False))
bad('double_release_in_one_phase', lambda a: a[2]['actual_original_A21']['phase_results'][0].update(double_release=[1,2]))
bad('wrong_phase_offsets', lambda a: a[2]['actual_original_A21']['phase_results'][0].update(endpoint_offset_s=-.004))
bad('untouched_voice_not_preserved', lambda a: next(c for c in a[2]['checks'] if c['name']=='every-untouched-whole-sentence-preserved').update(passed=False))
bad('missing_required_original_check', lambda a: a[2].update(checks=[c for c in a[2]['checks'] if c['name']!='whole-track-level-preserved']))
bad('canonical_identity_changed', lambda a: a[2].update(canonical_sha256='0'*64))
bad('copy_absolute_packet_clock_changed', lambda a: a[3].update(original_audio_packet_timings_identical=False))
bad('selected_AAC_changed', lambda a: a.__setitem__(4, '0'*64))
rejected = []
for label, args in cases.items():
    try:
        check(args)
    except (ValueError, AssertionError) as e:
        rejected.append({'case': label, 'rejected': True, 'reason': str(e)})
    else:
        raise AssertionError('Unapproved case accepted: ' + label)

# Remove only the added explicit-A21 branch to prove legacy checks are intact.
def definitions(path):
    return {n.name:n for n in ast.parse(path.read_text()).body if isinstance(n,ast.FunctionDef)}
before = definitions(HERE.parent / 'native-inline-engine-frozen-20261114-v5-explicit-approved-layout-reference/release_contract.py')
after = definitions(HERE / 'release_contract.py')
for name in before:
    node = copy.deepcopy(after[name])
    if name == 'canonical_audio_contract':
        strict = next(n for n in node.body if isinstance(n,ast.If) and isinstance(n.test,ast.Name) and n.test.id=='strict_review')
        strict.body.pop(0)
    elif name == 'reviewed_canonical_audio_copy':
        node.body.pop(1)  # Original docstring, then the new explicit A21 check.
    assert ast.dump(node,include_attributes=False) == ast.dump(before[name],include_attributes=False), name

manifest = HERE / 'approved-video-layouts70-frozen-A21.json'
spec = {'path': str(manifest), 'bytes': manifest.stat().st_size, 'sha256': D.digest(manifest)}
with tempfile.TemporaryDirectory(prefix='actualA21-layout-reference-') as temp:
    actual = explicit_approved_layout_reference('17', {'explicit_approved_video_layout': spec}, temp)
    assert D.digest(actual['path']) == '40414bed8e2bf8ffc32c6fe24d0a9ac5c40fd6fe12571f8f66d6a39a736507b0'

D.write(HERE / 'actual17-A21-contract-and-mutation-tests.json', {
    'scope': 'Actual immutable17 approved-A21 report/copy contract plus14 mutated bad cases; not full V3 or new acoustic acceptance',
    'passed': True, 'actual_audio_report_sha256': D.digest(raw_path),
    'actual_native_old_AAC_identical': False, 'truthful_actual_program': review['tool'],
    'actual_contract_basis': basis, 'mutations_rejected': rejected,
    'legacy_release_contract_function_AST_exact_after_removing_only_new_A21_branches': True,
    'strict_delivery_program_byte_unchanged': D.digest(HERE/'delivery.py') == D.digest(HERE.parent/'native-inline-engine-frozen-20261114-v5-explicit-approved-layout-reference/delivery.py'),
    'actual_immutable17_approved_layout_copied_exactly': True,
    'source_audio_GEN_original_report_or_quality_threshold_modified': False,
    'contract_program_sha256': D.digest(HERE/'release_contract.py'),
    'importer_program_sha256': D.digest(HERE/'import_actual_article.py')})
print(json.dumps({'actual17_contract_passed': True, 'negative_rejected': len(rejected), 'legacy_checks_intact': True}))
