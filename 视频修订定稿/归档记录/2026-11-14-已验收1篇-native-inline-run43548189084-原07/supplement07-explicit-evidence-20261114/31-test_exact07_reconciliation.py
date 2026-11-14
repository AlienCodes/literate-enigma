"""Actual exact07 pair and mutation checks, without media/source writes."""
import copy
import hashlib
import importlib.util
import json
import traceback
from pathlib import Path

import delivery as D

HERE = Path(__file__).resolve().parent
AUDIT = Path('/workspace/work/video-audit70-20261113')
NATIVE = AUDIT / 'next-passed-native/43548189084/07'
FILES = NATIVE / 'artifact-files'
check = D.markdown_prose_equivalence
pair = [(FILES / '07-request-manuscript.md').read_text(),
        (FILES / '07-actual-working-manuscript.md').read_text(),
        D.load(FILES / '07-request-source.json'),
        D.load(FILES / '07-actual-working-source.json')]

def run(args, article='07'):
    return check(*args, article, D.visible_tokens, D.require)

positive = run(pair)
assert positive['kind'] == 'exact_original_sync_of_already_approved_JSON_into_stale_imported_MD'
proofs = [AUDIT / 'article07-original-sync-reproduction-20261114' / name
          for name in ('reproduction.json', 'paragraph-and-table-mapping.json')]
assert [D.digest(p) for p in proofs] == positive['required_reproduction_evidence_sha256']

cases = {}
for index, side in ((0, 'request'), (1, 'actual')):
    for label, marker in (('Chinese_body', '## 中文'), ('English_body', '## 英文'),
                          ('vocabulary', '## 速查表'), ('facts', '## 史实与来源')):
        candidate = copy.deepcopy(pair)
        assert marker in candidate[index]
        candidate[index] = candidate[index].replace(marker, marker + '\nX', 1)
        cases[side + '_' + label + '_one_character'] = candidate
    candidate = copy.deepcopy(pair)
    assert '（whose pipe' in candidate[index] or '（简述：' in candidate[index]
    marker = '（whose pipe' if '（whose pipe' in candidate[index] else '（简述：'
    candidate[index] = candidate[index].replace(marker, marker + 'X', 1)
    cases[side + '_note_one_character'] = candidate
for index, side in ((2, 'request'), (3, 'actual')):
    candidate = copy.deepcopy(pair)
    candidate[index]['sentences'][0]['chunks'][0]['en'] += 'X'
    cases[side + '_source_English_one_character'] = candidate
    candidate = copy.deepcopy(pair)
    candidate[index]['unauthorized_metadata'] = 'X'
    cases[side + '_source_metadata_one_character'] = candidate

rejected = []
for name, candidate in cases.items():
    try:
        run(candidate)
    except ValueError as e:
        rejected.append({'case': name, 'rejected': True, 'actual_reason': str(e)})
    else:
        raise AssertionError('Unapproved mutation accepted: ' + name)
try:
    run(pair, '08')
except ValueError as e:
    rejected.append({'case': 'exact_pair_under_another_article', 'rejected': True, 'actual_reason': str(e)})
else:
    raise AssertionError('Exact07 profile applied to another article')

old = HERE.parent / 'native-inline-engine-frozen-20261114-v3-voice-and-approved-summary-sync/delivery.py'
module_spec = importlib.util.spec_from_file_location('original_v3_delivery_for07', old)
original = importlib.util.module_from_spec(module_spec)
module_spec.loader.exec_module(original)
try:
    original.markdown_prose_equivalence(*pair, '07', original.visible_tokens, original.require)
except ValueError:
    error = traceback.format_exc()
else:
    raise AssertionError('Expected the actual old v3 mismatch to reproduce')
(HERE / 'actual07-original-v3-MD-error-replay.log').write_text(
    'Actual replay of the prior v3 MD comparison; not a contemporaneous copy of the first failed process stderr.\n' + error)

prepared = D.load(NATIVE / 'prepared-inline-section.json')
review = D.load(NATIVE / 'actual-boundary-frame-review.json')
assert D.digest(Path(prepared['final']['path'])) == prepared['final']['sha256'] == review['video_sha256']
assert review['actually_visually_reviewed'] is True
assert len(review['frames']) == 5
assert {v['sha256'] for v in review['frames']} == {v['sha256'] for v in prepared['decoded_frames_to_actually_view']}
for frame in prepared['decoded_frames_to_actually_view']:
    D.checked_file(frame)
report = {'scope': 'One actual07 full-pinned stale MD reconciliation only; not full V3 acceptance',
          'passed': True, 'actual_exact07_pair': positive,
          'negative_controls': rejected, 'negative_rejected_count': len(rejected),
          'old_v3_failure_actually_reproduced_and_logged': True,
          'prior_actual_five_frame_review_and_native_MP4_SHA_rechecked': True,
          'video_sha256': review['video_sha256'],
          'delivery_program_sha256': D.digest(HERE / 'delivery.py'),
          'sources_and_media_modified': False}
D.write(HERE / 'actual07-pair-and-mutation-validation.json', report)
print(json.dumps({'passed': True, 'negative_rejected': len(rejected), 'same_actual_five_frames': True}))
