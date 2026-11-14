import copy
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
FROZEN = HERE.parent / 'native-inline-engine-frozen-20261114-v2-observation-metadata'
sys.path.insert(0, str(FROZEN))
import delivery as D
from markdown_summary_equivalence import markdown_prose_equivalence as check

BASE = Path('/workspace/work/video-audit70-20261113/next-passed-native/43543967031')

def read(n):
    p = BASE / n / 'artifact-files'
    return [(p / (n + '-request-manuscript.md')).read_text(),
            (p / (n + '-actual-working-manuscript.md')).read_text(),
            D.load(p / (n + '-request-source.json')),
            D.load(p / (n + '-actual-working-source.json'))]

def run(args, n):
    return check(*args, n, D.visible_tokens, D.require)

positive = []
for n in ['01','09','13','14','20','21','22','23','28','32','33','36']:
    result = run(read(n), n)
    positive.append(result)

negative = []
original = read('33')
cases = {}
a = copy.deepcopy(original)
head, cn = a[1].split('## 中文', 1)
prefix, rest = cn.split('（简述：', 1)
a[1] = head + '## 中文' + prefix.replace('2018年', '2019年', 1) + '（简述：' + rest
cases['changed_Chinese_body_before_summary'] = a
a = copy.deepcopy(original)
head, summary = a[1].split('（简述：', 1)
a[1] = head + '（简述：' + summary.replace('2018年', '2019年', 1)
cases['changed_final_MD_summary'] = a
a = copy.deepcopy(original)
for s in a[3]['sentences']:
    for c in s['chunks']:
        if '（简述：' in c.get('note', ''):
            c['note'] = c['note'].replace('2018年', '2019年', 1)
cases['changed_final_JSON_summary'] = a
a = copy.deepcopy(original)
a[1] += '\nChanged source appendix fact.\n'
cases['changed_factual_source_appendix'] = a
a = copy.deepcopy(original)
pre, en = a[1].split('## 英文', 1)
a[1] = pre + '## 英文' + en.replace('June', 'July', 1)
cases['changed_English_body'] = a
a = copy.deepcopy(original)
a[1] = a[1].replace('## 速查表', 'Extra Chinese prose.\n\n## 速查表', 1)
cases['inserted_unapproved_prose_after_summary'] = a
a = copy.deepcopy(original)
a[1] = a[1].replace('（简述：', '（新简述：', 1)
cases['missing_identifiable_final_brief'] = a
a = copy.deepcopy(original)
a[0] = a[0].replace('## 速查表', '（不得吞掉的旧尾重要小字）\n\n## 速查表', 1)
cases['old_brief_followed_by_another_parenthetical_note'] = a
a = copy.deepcopy(original)
a[1] = a[1].replace('## 速查表', '（不得吞掉的新尾重要小字）\n\n## 速查表', 1)
cases['new_brief_followed_by_another_parenthetical_note'] = a
a = copy.deepcopy(original)
for document in a[2:]:
    for sentence in document['sentences']:
        for chunk in sentence['chunks']:
            if '（简述：' in chunk.get('note', ''):
                chunk['note'] += '（必须保留的JSON尾后重要小字）'
cases['both_JSON_briefs_followed_by_another_parenthetical_note'] = a
a = copy.deepcopy(original)
a[0] = a[0].replace('（简述：', '（简述：（未闭合的内层括注', 1)
cases['unbalanced_old_brief_inner_parenthesis'] = a
a = copy.deepcopy(original)
a[1] = a[1].replace('（简述：', '（简述：（未闭合的内层括注', 1)
cases['unbalanced_new_brief_inner_parenthesis'] = a
for label, args in cases.items():
    try:
        run(args, '33')
    except ValueError as e:
        negative.append({'case': label, 'rejected': True, 'reason': str(e)})
    else:
        raise AssertionError('Unapproved change accepted: ' + label)

out = {'scope': 'Isolated Markdown equivalence helper only, not full V3 or publication',
       'unchanged_frozen_validator': str(FROZEN / 'delivery.py'),
       'candidate_helper_sha256': hashlib.sha256((HERE / 'markdown_summary_equivalence.py').read_bytes()).hexdigest(),
       'positive_actual_pairs': positive, 'positive_count': len(positive),
       'negative_controls': negative, 'negative_rejected_count': len(negative),
       'passed': True, 'source_media_or_frozen_checker_modified': False}
(HERE / 'actual-12-pairs-and-12-negative-controls-balanced-tail.json').write_text(json.dumps(out, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'passed': True, 'actual_pairs': len(positive), 'negative_rejected': len(negative)}))
