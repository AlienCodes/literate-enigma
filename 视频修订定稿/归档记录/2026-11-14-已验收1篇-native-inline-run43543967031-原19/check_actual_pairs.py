"""Verify observed-QC metadata classification on genuine sources and reject real render mutations."""
import copy
import hashlib
import json
import sys
from pathlib import Path

D = Path('/workspace/work/video-revision-delivery')
sys.path.insert(0, str(D))
from delivery import source_invariants

out = Path(__file__).resolve().parent
roots = [D / 'actual53-64-validation']
for name in ('next-passed-validated', 'recovered-canonical-validated'):
    roots += [p.parent for p in (D / name).glob('*/*/archive-handoff.json')]
pairs = []
for root in roots:
    for request in (root / 'request-source/视频/脚本').glob('*.json'):
        final = root / 'final-source/视频/脚本' / request.name
        if final.exists():
            pairs.append((request.stem, request, final))
native = Path('/workspace/work/video-audit70-20261113/next-passed-native/43543967031/19/artifact-files')
collection = json.loads(next(native.rglob('19-actual-source-collection.json')).read_text())
pairs.append(('19', next(native.rglob(collection['files']['request_json']['file'])),
              next(native.rglob(collection['files']['actual_working_source']['file']))))
actual = []
for n, requested, final in pairs:
    a, b = json.loads(requested.read_text()), json.loads(final.read_text())
    result = source_invariants(a, b, n)
    actual.append({'article': n, 'request_sha256': hashlib.sha256(requested.read_bytes()).hexdigest(),
                   'final_sha256': hashlib.sha256(final.read_bytes()).hexdigest(), 'result': result})

a, b = json.loads(pairs[-1][1].read_text()), json.loads(pairs[-1][2].read_text())
ending = 'S' + str(len(a['sentences']))
bad = []
def reject(label, edit):
    changed = copy.deepcopy(b)
    edit(changed)
    try:
        source_invariants(a, changed, '19')
    except ValueError as error:
        bad.append({'case': label, 'actual_rejected': True, 'reason': str(error)})
    else:
        raise AssertionError('Incorrectly accepted physical/content mutation: ' + label)

reject('spoken English changed', lambda d: d['sentences'][0]['chunks'][0].update(en='changed actual English'))
reject('visible Chinese changed', lambda d: d['sentences'][0]['chunks'][0].update(zh='错误正文'))
reject('actual gain changed', lambda d: d['结尾句'][ending].update(前段增益dB=3.5))
reject('actual front speed changed', lambda d: d['结尾句'][ending].update(前段语速=.81))
reject('actual tail speed changed', lambda d: d['结尾句'][ending].update(最后一段语速=.81))
reject('actual gap changed', lambda d: d['结尾句'][ending].update(最后一段前停顿=.99))
reject('actual splice changed', lambda d: d['结尾句'][ending].update(接点=[134701, 161100]))
reject('actual cut added', lambda d: d.update(非人声区间={'S1': [[.1, .2]]}))
reject('unknown extra renderer control', lambda d: d.update(未经批准的声控=True))
reject('malformed raw fingerprint', lambda d: d.update(区间声音指纹={'S1': 'not-a-raw-hash'}))
reject('raw fingerprint invalid sentence', lambda d: d.update(区间声音指纹={'S999': '0123456789ab'}))
reject('unrelated rationale substitution', lambda d: d['结尾句'][ending].update(依据='不是原定位器模板的替换说明'))
report = {'status': 'passed_real_source_pairs_and_real_render_control_negative_cases',
          'genuine_source_pair_count': len(actual), 'genuine_source_pairs': actual,
          'negative_case_count': len(bad), 'negative_cases': bad,
          'original_sound_gates_AAC_comparison_and_thresholds_changed': False,
          'renderer_or_source_or_MP4_changed_by_test': False}
(out / 'actual-pairs-and-negative-controls.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'genuine_source_pairs_passed': len(actual), 'physical_or_content_mutations_rejected': len(bad)}))
