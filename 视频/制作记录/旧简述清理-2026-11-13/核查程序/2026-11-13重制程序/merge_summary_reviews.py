"""Prepare one fact-checked summary set, with independent review corrections."""
import hashlib
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent
rows = []
for group in ['01-24', '25-48', '49-70']:
    rows.extend(json.loads((BASE / f'summary-revisions-{group}.json').read_text()))
by_id = {row['id']: row for row in rows}
assert len(rows) == len(by_id) == 70
corrections = []
for group, key in [('01-24', 'changes'), ('25-48', 'corrections'), ('49-70', 'corrections')]:
    path = BASE / f'summary-crossreview-{group}.json'
    if not path.exists():
        continue
    document = json.loads(path.read_text())
    changes = document.get(key, document.get('changes', []))
    if group == '49-70' and not changes:
        changes = [
            {'id': item['id'], 'before': item['original_after'], 'after': item['full_after'],
             'candidate_before_sha256': hashlib.sha256(item['original_after'].encode()).hexdigest(),
             'issues': item.get('issues', []), 'fact_sources': item.get('body_sections', [])}
            for item in document.get('articles', [])
            if item['id'] in document.get('correction_ids', [])]
    for change in changes:
        row = by_id[change['id']]
        old = row['after']
        expected = change.get('reviewed_after_sha256') or change.get('candidate_before_sha256')
        if expected:
            assert hashlib.sha256(old.encode()).hexdigest() == expected, change['id']
        else:
            assert change.get('before', change.get('reviewed_after')) == old, change['id']
        row['after'] = change['after']
        row['changed'] = row['before'] != row['after']
        row.setdefault('independent_review_changes', []).append(change)
        corrections.append(change['id'])

# The user specifically requested a more detailed Y2K explanation after review.
priority = BASE / 'summary-revision-39-priority.json'
if priority.exists():
    row = json.loads(priority.read_text())
    assert row['before'] == by_id['39']['before']
    staged = BASE / 'payload/视频/脚本/39.json'
    if staged.exists():
        note = json.loads(staged.read_text())['sentences'][-1]['chunks'][-1]['note']
        previous = '（简述：' + note.split('（简述：', 1)[1]
        if previous != row['before'] and previous != row['after']:
            assert previous.replace('美国估算总花费约1000亿美元',
                                    '美国估算本国政府和企业总共要花约1000亿美元') == row['after']
            row.setdefault('independent_review_changes', []).append({
                'before': previous, 'after': row['after'],
                'reason': 'Clarify that the US estimate covers its own government and businesses, not global spending.'})
    row.setdefault('reasons', []).append('User explicitly requested a clearer, more detailed Y2K closing summary after approving the prevention-cost note.')
    by_id['39'] = row

factual_report = BASE / 'article65-factual-clarification.json'
if factual_report.exists():
    actual = json.loads((BASE / 'payload/视频/脚本/65.json').read_text())
    note = actual['sentences'][-1]['chunks'][-1]['note']
    value = '（简述：' + note.split('（简述：', 1)[1]
    expected = by_id['65']['after'].replace('2015年取回自存的部分备份',
                                           '2015年请求取出自存的部分备份')
    assert value == expected
    by_id['65']['after'] = value
    by_id['65']['changed'] = by_id['65']['before'] != value
    by_id['65'].setdefault('reasons', []).append('Retain the exact requested-withdrawal wording; the published body says asked for, not a verified first shipment quantity.')

adjustments = BASE / 'summary-root-adjustments.json'
if adjustments.exists():
    for change in json.loads(adjustments.read_text()):
        row = by_id[change['id']]
        assert hashlib.sha256(row['after'].encode()).hexdigest() == change['reviewed_after_sha256']
        row['after'] = change['after']
        row['changed'] = row['before'] != row['after']
        row.setdefault('independent_review_changes', []).append(change)

for row in by_id.values():
    assert row['before_sha256'] == hashlib.sha256(row['before'].encode()).hexdigest(), row['id']
    assert row['after'].startswith('（简述：') and row['after'].endswith('）')
    assert row['after'].count('▸') == 5 and row['after'].count('（简述：') == 1
    assert row['changed'] == (row['before'] != row['after'])
approved = [by_id[f'{n:02d}'] for n in range(1, 71)]
(BASE / 'summary-approved-70.json').write_text(json.dumps(approved, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'reviewed': 70, 'changed': sum(row['changed'] for row in approved),
                  'independent_corrections': corrections,
                  'pending_independent_review_49_70': not (BASE / 'summary-crossreview-49-70.json').exists(),
                  'pending_user_requested_39_priority': not priority.exists()}, ensure_ascii=False))
