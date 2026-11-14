#!/usr/bin/env python3
"""Build a read-only plan; never write PAY or invoke media acceptance gates."""
import ast
import copy
import hashlib
import json
import re
import shutil
import zipfile
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
PAY = Path('/workspace/work/video-audit70-20261113/payload')
BASE = Path('/workspace/work/audit-repo')
DELIVERY = Path('/workspace/work/video-revision-delivery')
IDS = ['26', '27', '29', '39', '43', '45', '47', '53', '64']
ROOTS = {
    '26': DELIVERY / 'next-passed-validated/43529134759/26',
    '27': DELIVERY / 'next-passed-validated/43532011110/27',
    '29': DELIVERY / 'next-passed-validated/43532011110/29',
    **{n: DELIVERY / f'next-passed-validated/43533004625/{n}' for n in ['39', '43', '45', '47']},
    '53': DELIVERY / 'actual53-64-validation',
    '64': DELIVERY / 'actual53-64-validation',
}
RECEIPTS = {
    '26': '/workspace/work/video-archive-batches-20261114/run43529134759-26/final-archive-receipt.json',
    **{n: '/workspace/work/video-archive-batches-20261114/run43532011110-27-29/final-archive-receipt.json' for n in ['27', '29']},
    **{n: '/workspace/work/video-archive-batches-20261114/run43533004625-39-43-45/final-archive-receipt.json' for n in ['39', '43', '45']},
    '47': '/workspace/work/video-archive-batches-20261114/run43533004625-47/final-archive-receipt.json',
    **{n: '/workspace/work/video-archive-actual2-20261114/final-archive-receipt.json' for n in ['53', '64']},
}


def sha(p):
    h = hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda: f.read(1024 * 1024), b''):
            h.update(b)
    return h.hexdigest()


def load(p):
    return json.loads(Path(p).read_text())


def write(p, obj):
    p = Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n')


def record(p):
    p = Path(p)
    return {'path': str(p), 'bytes': p.stat().st_size, 'sha256': sha(p)}


def snapshot(p, dest):
    dest = HERE / dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(p, dest)
    return record(dest)


def flat(x, path=''):
    if isinstance(x, dict) and x:
        return {p: v for k, y in x.items() for p, v in flat(y, path + '/' + k.replace('~', '~0').replace('/', '~1')).items()}
    if isinstance(x, list) and x:
        return {p: v for k, y in enumerate(x) for p, v in flat(y, path + '/' + str(k)).items()}
    return {path: x}


def diff(a, b):
    a, b = flat(a), flat(b)
    return [{'pointer': p, 'operation': 'remove' if p not in b else 'add' if p not in a else 'replace',
             'before_exists': p in a, 'after_exists': p in b,
             **({'before': a[p]} if p in a else {}), **({'after': b[p]} if p in b else {})}
            for p in sorted(a.keys() | b.keys()) if p not in a or p not in b or a[p] != b[p]]


def project_gen(p):
    """Read literal S/out only. Do not execute the GEN or a rewritten helper."""
    tree = ast.parse(Path(p).read_text())
    for node in tree.body:
        if isinstance(node, ast.Import):
            assert all(x.name in {'os', 'sys'} and x.asname is None for x in node.names)
        elif isinstance(node, ast.ImportFrom):
            assert node.module == '核对' and [x.name for x in node.names] == ['生成并核对']
        elif isinstance(node, ast.Assign):
            assert len(node.targets) == 1 and isinstance(node.targets[0], ast.Name) and node.targets[0].id in {'S', 'out'}
        elif isinstance(node, ast.Expr):
            assert ast.unparse(node.value) in {'sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))', '生成并核对(S, out)'}
        else:
            raise AssertionError('Unexpected executable GEN statement: ' + ast.dump(node))
    assigns = {x.targets[0].id: ast.literal_eval(x.value) for x in tree.body
               if isinstance(x, ast.Assign) and len(x.targets) == 1 and isinstance(x.targets[0], ast.Name)}
    assert set(assigns) == {'S', 'out'}
    out = copy.deepcopy(assigns['out'])
    assert out['sentences'] == []
    for para, chunks in assigns['S']:
        cs = []
        for c in chunks:
            al = [list(x) for x in c[0]]
            d = {'en': ' '.join(a for a, b in al if a != '\n'), 'zh': ''.join(b for a, b in al), 'align': al}
            if len(c) > 1:
                d['note'] = c[1]
            cs.append(d)
        out['sentences'].append({'para': para, 'chunks': cs})
    return out


def visible_zh(s):
    return re.sub(r'\*\*([^*]+)\*\*\(([^)]+)\)', r'\1', s)


def normalized_note(s):
    # Only remove G35 whitespace and line-leading continuation marker. Retain ▸ and all wording.
    return re.sub(r'\s+', '', re.sub(r'(?m)^[ \t]*▹[ \t]*', '', s))


def classify(n, entry, before, after):
    p = entry['pointer']
    if p.endswith('/note'):
        a, b = entry['before'], entry['after']
        assert '（简述：' in a and '（简述：' in b
        prefix_a, summary_a = a.split('（简述：', 1)
        prefix_b, summary_b = b.split('（简述：', 1)
        assert prefix_a == prefix_b
        assert normalized_note(a) == normalized_note(b)
        assert summary_a.count('▸') == summary_b.count('▸') == 5
        entry.update(category='G35_summary_linebreaks', semantic_change=False,
                     explanation='仅把五点简述拆行，并按需加入行首▹续行标记；前置原小字、五点内容及标点完整不变。',
                     original_note_prefix_exact=True, five_primary_points_retained=True,
                     before_lines=len(summary_a.splitlines()), after_lines=len(summary_b.splitlines()),
                     normalized_note_sha256=hashlib.sha256(normalized_note(a).encode()).hexdigest())
    elif n == '29' and (p.endswith('/zh') or '/align/' in p):
        a, b = entry['before'], entry['after']
        assert visible_zh(a) == visible_zh(b)
        assert re.findall(r'\*\*[^*]+\*\*\(([^)]+)\)', a) == re.findall(r'\*\*[^*]+\*\*\(([^)]+)\)', b)
        assert re.sub(r'\*\*([^*]+)的\*\*\(([^)]+)\)', r'**\1**(\2)的', b) == a
        entry.update(category='T38_highlight_includes_de', semantic_change=False,
                     explanation='既有重点词中文的末尾“的”并入同色粗体；可见汉字、英文重点键及语序不变。此为标色范围变化，非新增词义。',
                     visible_Chinese_exact=True, English_focus_keys_exact=True)
    elif n == '53' and (p.startswith('/换行变更已获同意/') or p.startswith('/换行变更记录/1/')):
        pending = before['换行变更已获同意']
        assert after['换行变更记录'][:-1] == before['换行变更记录']
        assert after['换行变更记录'][-1] == {'日期': '2026-11-13', **pending}
        assert '换行变更已获同意' not in after
        entry.update(category='pending_layout_permission_archived_verbatim', semantic_change=False,
                     explanation='程序消费临时换行授权字段后，将S6/S17原话逐字转存历史记录。旧2026-11-07记录完整保留，新增2026-11-13是运行记录日期，并非新的用户授权日期。',
                     original_authorization_verbatim_retained=True,
                     root_attention='删除临时字段是实际已验收运行状态，需连同历史记录一起回灌；不可只删字段或把运行日期误称用户授权日期。')
    else:
        entry.update(category='unclassified_requires_root_review', semantic_change=None,
                     root_attention='未识别的正文/词义/控制语义差异，禁止自动覆盖。')
    return entry


def main():
    assert HERE.name == 'canonical-final-source-backflow-plan-20261114'
    input_hashes = {}
    articles, operations = [], []
    for n in IDS:
        root = ROOTS[n]
        handoff_path = root / 'archive-handoff.json'
        h = load(handoff_path)
        article = next(a for a in h['articles'] if a['source_id'] == n)
        assert article['passed_per_article'] is True
        sec = article['section']
        proof_path = Path(sec['final_source']['gen']['derivation_proof']['path'])
        proof = load(proof_path)
        assert sha(proof_path) == sec['final_source']['gen']['derivation_proof']['sha256']
        assert proof['status'] == 'passed' and proof['whole_JSON_roundtrip_exact'] is True
        assert proof['original_helper_exit'] == 0
        srcs = {}
        for kind in ['json', 'gen', 'md']:
            reqmeta, finmeta = sec['request_source'][kind], sec['final_source'][kind]
            req, fin = root / 'request-source' / reqmeta['path'], root / 'final-source' / finmeta['path']
            effective = PAY / reqmeta['path']
            effective_origin = 'PAY'
            if not effective.exists():
                effective, effective_origin = BASE / reqmeta['path'], 'audit-repo baseline, PAY has no override'
            assert sha(req) == reqmeta['sha256']
            assert sha(fin) == finmeta['sha256']
            assert sha(effective) == reqmeta['sha256'], f'{n} current {kind} drifted from request'
            input_hashes[str(effective)] = sha(effective)
            srcs[kind] = {'current': record(effective), 'effective_origin': effective_origin,
                          'immutable_request': record(req), 'final': record(fin),
                          'current_equals_request_bytes': True,
                          'final_origin': finmeta.get('origin', 'see handoff')}
            snapshot(effective, f'snapshots/{n}/current/{reqmeta["path"]}')
            snapshot(req, f'snapshots/{n}/request/{reqmeta["path"]}')
            snapshot(fin, f'snapshots/{n}/final/{finmeta["path"]}')
            if kind != 'md':
                candidate = snapshot(fin, f'apply-payload/{finmeta["path"]}')
                operations.append({'article': n, 'kind': kind, 'relative_path': finmeta['path'],
                                   'expected_before_sha256': sha(effective), 'after_sha256': candidate['sha256'],
                                   'candidate_relative_path': str(Path(candidate['path']).relative_to(HERE))})
            else:
                assert sha(req) == sha(fin), 'Approved MD must stay byte-exact'
        asked, final, current = load(srcs['json']['immutable_request']['path']), load(srcs['json']['final']['path']), load(srcs['json']['current']['path'])
        assert proof['source_json_sha256'] == srcs['json']['final']['sha256']
        assert proof['derived_generator_sha256'] == srcs['gen']['final']['sha256']
        assert proof['request_json_sha256'] == srcs['json']['immutable_request']['sha256']
        assert proof['request_generator_sha256'] == srcs['gen']['immutable_request']['sha256']
        assert proof['request_manuscript_sha256'] == srcs['md']['immutable_request']['sha256']
        roundtrip = proof_path.parent / f'{n}-roundtrip.json'
        assert load(roundtrip) == final
        assert project_gen(srcs['gen']['final']['path']) == final
        assert project_gen(srcs['gen']['current']['path']) == current
        changes = [classify(n, e, current, final) for e in diff(current, final)]
        assert not diff(current, asked)
        assert diff(asked, final) == diff(current, final)
        assert all(e['category'] != 'unclassified_requires_root_review' for e in changes)
        with zipfile.ZipFile(article['immutable_native_zip']['path']) as z:
            # Verify the complete immutable archive before reading JSON members; do not export media.
            assert sha(article['immutable_native_zip']['path']) == article['immutable_native_zip']['sha256']
            member = sec['final_source']['json'].get('artifact_member', f'{n}-source.json')
            data = z.read(member)
            assert hashlib.sha256(data).hexdigest() == srcs['json']['final']['sha256']
            native_status = json.loads(z.read(f'{n}-status.json'))
            assert native_status['passed'] is True and native_status['stage'] == 'final4K-passed'
            assert native_status['article'] == n
            for kind in ['json', 'gen', 'md']:
                ref = sec['request_source'][kind]
                assert native_status['request_source_sha256'][ref['path']] == ref['sha256']
        # Explicitly check body text and the English/CN lookup-key strings; no audio regeneration.
        en_equal, zh_equal, keys_equal, note_equal = True, True, True, True
        for sa, sb in zip(current['sentences'], final['sentences'], strict=True):
            for a, b in zip(sa['chunks'], sb['chunks'], strict=True):
                en_equal &= a['en'] == b['en']
                zh_equal &= visible_zh(a['zh']) == visible_zh(b['zh'])
                keys_equal &= re.findall(r'\*\*[^*]+\*\*\(([^)]+)\)', a['zh']) == re.findall(r'\*\*[^*]+\*\*\(([^)]+)\)', b['zh'])
                note_equal &= normalized_note(a.get('note', '')) == normalized_note(b.get('note', ''))
        assert en_equal and zh_equal and keys_equal and note_equal
        protected = [e for e in changes if e['category'] == 'unclassified_requires_root_review']
        ev = {}
        for name, p in [('handoff', handoff_path), ('derived-source-proof', proof_path), ('original-helper-roundtrip', proof_path.parent / 'original-helper-roundtrip.log'),
                        ('roundtrip', roundtrip), ('V3-record', Path(article['validated_record'])), ('permanent-archive-receipt', Path(RECEIPTS[n]))]:
            ev[name] = snapshot(p, f'evidence/{n}/{p.name}')
        rec = load(article['validated_record'])
        assert rec['qc']['status'] == 'passed'
        assert rec['qc']['source_sha256']['final']['json'] == srcs['json']['final']['sha256']
        assert rec['qc']['source_sha256']['final']['gen'] == srcs['gen']['final']['sha256']
        assert rec['sha256'] == article['final_mp4']['sha256']
        row = {'source_id': n, 'new_id': article['new_id'], 'name': article['canonical_archive_path'],
               'source_run': h['source_run'], 'passed_handoff': record(handoff_path),
               'already_accepted_video_sha256': article['final_mp4']['sha256'],
               'source_files': srcs, 'native_final_JSON_member': member,
               'immutable_native_archive': article['immutable_native_zip'],
               'source_provenance_verified_without_exporting_media': True,
               'PAY_to_request_leaf_diff': [], 'PAY_to_final_leaf_diff': changes,
               'request_to_final_leaf_diff': changes,
               'derived_GEN_full_JSON_leaf_diff_equals_JSON_diff': diff(project_gen(srcs['gen']['current']['path']), project_gen(srcs['gen']['final']['path'])) == diff(current, final),
               'derived_GEN_is_data_after_final_QC_not_claimed_executed_originally': True,
               'original_helper_roundtrip': {'existing_true_proof': True, 'exit': proof['original_helper_exit'], 'whole_JSON_deep_equal': True,
                                             'original_helpers_sha256': proof['original_helper_sha256'],
                                             'reexecuted_media_or_QC_in_this_plan': False},
               'invariants': {'English_exact_including_focus_markup': en_equal, 'visible_Chinese_exact': zh_equal,
                              'Chinese_English_focus_lookup_keys_exact': keys_equal, 'notes_and_5point_summary_wording_exact_after_G35_normalization': note_equal,
                              'all_other_runtime_and_audio_control_fields_identical': not protected,
                              'font_gain_cut_speech_timing_values_changed': False,
                              'MD_current_request_final_byte_exact_and_will_not_write': True},
               'root_attention': [e for e in changes if e.get('root_attention')], 'evidence_snapshots': ev}
        articles.append(row)
        write(HERE / f'article{n}-leaf-diff.json', row)
    assert all(sha(p) == h for p, h in input_hashes.items()), 'PAY/baseline changed during read-only collection'
    categories = Counter(e['category'] for a in articles for e in a['PAY_to_final_leaf_diff'])
    report = {'status': 'read_only_backflow_plan_ready_for_root_review', 'article_ids': IDS,
              'scope': 'Preserve the already accepted runtime data in canonical JSON+pure-data GEN for the next generation. This is not a new video acceptance gate.',
              'PAY_changed': False, 'pushed_remote': False, 'media_rerendered': False,
              'changed_leaf_count': sum(categories.values()), 'leaf_category_counts': dict(categories),
              'current_matches_immutable_request_all9': True, 'original_helper_full_JSON_proof_verified_all9': True,
              'unexpected_body_gloss_audio_control_diffs': [],
              'review_notes': ['准确共22叶：9处简述note、29篇8处中文粗体范围、53篇5处授权字段转存。此前口头合计23已更正。',
                               '53篇原声按位置确认迁移并未出现；迁移的是换行变更授权字段，原话在历史记录中完整保留。不得将其误称音频确认。',
                               '9篇无字体、gain、cut、speech时间或音控值差异。',
                               '29篇四处“的”纳入已存在重点词标色；MD保持已验原稿，不将这些格式容许差异反向写入MD。',
                               '最终GEN是从实际最终JSON派生并通过原helper完整JSON深等的纯数据GEN；不冒充原成片任务实际执行的GEN。',
                               '候选脚本仅18个JSON/GEN路径，默认dry-run，root审后一次应用；所有MD、其他篇、媒体与检查程序不触碰。'],
              'normalization_rules': {'G35': 'Only whitespace plus line-leading ▹ removed; retain ▸ and all wording/punctuation. Original note prefix before （简述： is byte-exact.',
                                      'T38': '**译文**(key) -> visible 译文; compare key strings independently. Assert sole markup change is terminal 的 entering bold.'},
              'articles': articles}
    assert report['changed_leaf_count'] == 22
    write(HERE / 'backflow-plan.json', report)
    write(HERE / 'apply-manifest.json', {'status': 'candidate_only_not_applied', 'default_payload_root': str(PAY), 'articles': IDS,
                                       'allowed_types': ['json', 'gen'], 'operations': operations,
                                       'unchanged_MD': [a['source_files']['md']['current'] for a in articles],
                                       'base_inputs_pre_post_exact': input_hashes})
    print(json.dumps({'status': report['status'], 'articles': len(articles), 'leaves': report['changed_leaf_count'],
                      'categories': dict(categories), 'candidate_write_files': len(operations), 'PAY_changed': False}, ensure_ascii=False))


if __name__ == '__main__':
    main()
