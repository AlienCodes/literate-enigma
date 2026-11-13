"""Apply independently reviewed summary text without touching the narrated body."""
import argparse
import ast
import copy
import hashlib
import json
import pprint
import subprocess
from pathlib import Path

BASE = Path(__file__).resolve().parent
PAY = BASE / 'payload'
LOCAL = Path('/workspace/work/github-publication/target')


def read(path):
    if (PAY / path).exists():
        return (PAY / path).read_text()
    if (LOCAL / path).exists():
        return (LOCAL / path).read_text()
    return subprocess.check_output(['git', 'show', 'HEAD:' + path], cwd=LOCAL).decode()


def save(path, text):
    destination = PAY / path
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(text)


def tagged_span(text):
    start = text.index('（简述：')
    depth = 0
    for end in range(start, len(text)):
        depth += (text[end] == '（') - (text[end] == '）')
        if depth == 0:
            return start, end + 1
    raise AssertionError('Unclosed summary tag')


def apply(row):
    no = row['id']
    assert no.isdigit() and len(no) == 2 and 1 <= int(no) <= 70
    old, new = row['before'], row['after']
    assert hashlib.sha256(old.encode()).hexdigest() == row['before_sha256']
    assert new.count('（简述：') == 1 and new.count('▸') == 5 and new.endswith('）')
    assert not any(word in new for word in ['怎么理解', '如何理解', '是什么意思'])
    if old == new:
        return {'id': no, 'changed': False}
    sp = f'视频/脚本/{no}.json'
    original = json.loads(read(sp))
    current = copy.deepcopy(original)
    last = current['sentences'][-1]['chunks'][-1]
    already = new in last.get('note', '')
    if not already:
        if last['note'].count(old) != 1:
            previous = [item.get('before', item.get('reviewed_after'))
                        for item in row.get('independent_review_changes', [])]
            matches = [value for value in previous if value and last['note'].count(value) == 1]
            assert len(matches) == 1, (no, 'Baseline summary changed; merge required')
            old = matches[0]
        last['note'] = last['note'].replace(old, new, 1)
    current['结尾解说'] = '简述'
    control = copy.deepcopy(current)
    control['sentences'][-1]['chunks'][-1] = original['sentences'][-1]['chunks'][-1]
    if '结尾解说' in original:
        control['结尾解说'] = original['结尾解说']
    else:
        control.pop('结尾解说')
    assert control == original, (no, 'Only summary and matching label may change')

    gp = f'视频/工具/初稿生成/gen{no}.py'
    # Freeze the complete approved data so old GEN alignment or notes cannot
    # return on the next build. The shared producer/checker remains unchanged.
    source_rows = [(sentence['para'], [
        [chunk['align']] + ([chunk['note']] if 'note' in chunk else [])
        for chunk in sentence['chunks']]) for sentence in current['sentences']]
    controls = {key: copy.deepcopy(value) for key, value in current.items() if key != 'sentences'}
    controls['sentences'] = []
    generator = ('# 按批准脚本固化的数据；共享生成与核对程序保持原样。\nimport os, sys\n\nS = '
                 + pprint.pformat(source_rows, width=110, sort_dicts=False)
                 + '\n\nout = ' + pprint.pformat(controls, width=110, sort_dicts=False)
                 + '\n\nsys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))\n'
                   'from 核对 import 生成并核对\n生成并核对(S, out)\n')
    compile(generator, gp, 'exec')

    md_paths = set(subprocess.check_output(
        ['git', 'ls-tree', '-r', '--name-only', '-z', 'HEAD', '--', '新版定稿'], cwd=LOCAL
    ).decode().split('\0'))
    md_paths |= {str(path.relative_to(PAY)) for path in (PAY / '新版定稿').glob('*.md')}
    manuscript = next(path for path in md_paths if path.startswith('新版定稿/' + no + '-'))
    text = read(manuscript)
    section_start = text.index('## 中文')
    section_end = text.index('## 速查表', section_start)
    translated = text[section_start:section_end]
    assert translated.count('（简述：') <= 1, (no, 'At most one Chinese manuscript summary required')
    if '（简述：' in translated:
        begin, end = tagged_span(translated)
        translated = translated[:begin] + new + translated[end:]
    else:
        translated = translated.rstrip() + '\n\n' + new + '\n\n'
    # Validate every target before writing any of this article's three files.
    save(sp, json.dumps(current, ensure_ascii=False, indent=1) + '\n')
    save(gp, generator)
    save(manuscript, text[:section_start] + translated + text[section_end:])
    return {'id': no, 'changed': True, 'before_sha256': row['before_sha256'],
            'after_sha256': hashlib.sha256(new.encode()).hexdigest(),
            'body_notes_alignment_and_audio_preserved': True,
            'already_in_json': already,
            'summary_characters': len(new), 'files': [sp, gp, manuscript]}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('review_files', nargs='+')
    args = parser.parse_args()
    results = []
    for name in args.review_files:
        document = json.loads(Path(name).read_text())
        rows = document if isinstance(document, list) else document.get('articles', [document])
        results.extend(apply(row) for row in rows)
    (BASE / 'summary-application-log.json').write_text(json.dumps(results, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(results, ensure_ascii=False))
