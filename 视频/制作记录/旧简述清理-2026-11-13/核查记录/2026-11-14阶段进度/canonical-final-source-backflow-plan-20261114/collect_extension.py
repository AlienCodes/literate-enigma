#!/usr/bin/env python3
"""Read-only statistics for genuine additional passed handoffs; no apply bundle."""
import copy
import datetime
import hashlib
import importlib.util
import json
import re
import shutil
import zipfile
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('original_plan_reader', HERE / 'build_readonly_plan.py')
M = importlib.util.module_from_spec(spec)
spec.loader.exec_module(M)
OUT = HERE / 'additional-passed-readonly'
OUT.mkdir(exist_ok=True)
rows = []
for handoff in sorted(M.DELIVERY.rglob('archive-handoff.json')):
    h = M.load(handoff)
    for a in h['articles']:
        n = a['source_id']
        if n in M.IDS or a.get('passed_per_article') is not True:
            continue
        sec = a['section']
        req, final, current = {}, {}, {}
        sources = {}
        for kind in ['json', 'gen', 'md']:
            rm, fm = sec['request_source'][kind], sec['final_source'][kind]
            rp, fp = handoff.parent / 'request-source' / rm['path'], handoff.parent / 'final-source' / fm['path']
            cp = M.PAY / rm['path']
            if not cp.exists():
                cp = M.BASE / rm['path']
            assert M.sha(rp) == rm['sha256'] and M.sha(fp) == fm['sha256']
            sources[kind] = {'request': M.record(rp), 'final': M.record(fp), 'current': M.record(cp),
                             'current_equals_request_bytes': M.sha(cp) == M.sha(rp),
                             'final_origin': fm.get('origin')}
            if kind == 'json':
                req, final, current = M.load(rp), M.load(fp), M.load(cp)
        proof_path = Path(sec['final_source']['gen']['derivation_proof']['path'])
        proof = M.load(proof_path)
        assert M.sha(proof_path) == sec['final_source']['gen']['derivation_proof']['sha256']
        assert proof['status'] == 'passed' and proof['original_helper_exit'] == 0 and proof['whole_JSON_roundtrip_exact'] is True
        assert M.load(proof_path.parent / f'{n}-roundtrip.json') == final
        assert M.project_gen(sources['gen']['final']['path']) == final
        rec = M.load(a['validated_record'])
        assert rec['qc']['status'] == 'passed' and rec['sha256'] == a['final_mp4']['sha256']
        assert rec['qc']['source_sha256']['final']['json'] == sources['json']['final']['sha256']
        # Only already-passed source provenance, not re-acceptance of the MP4.
        assert M.sha(a['immutable_native_zip']['path']) == a['immutable_native_zip']['sha256']
        with zipfile.ZipFile(a['immutable_native_zip']['path']) as z:
            member = sec['final_source']['json'].get('artifact_member', f'{n}-source.json')
            assert hashlib.sha256(z.read(member)).hexdigest() == sources['json']['final']['sha256']
        changes = M.diff(current, final)
        for e in changes:
            p = e['pointer']
            if p.endswith('/note') and M.normalized_note(e.get('before', '')) == M.normalized_note(e.get('after', '')):
                e.update(category='G35_summary_linebreaks', root_review_required=False)
            elif (p.endswith('/zh') or '/align/' in p) and isinstance(e.get('before'), str) and isinstance(e.get('after'), str) and M.visible_zh(e['before']) == M.visible_zh(e['after']):
                e.update(category='visible_Chinese_identical_highlight_scope', root_review_required=False)
            elif p.startswith('/核对确认/'):
                e.update(category='confirmation_metadata_review_separately', root_review_required=True,
                         note='实际已通过运行的确认/指纹/位置元数据，不能笼统称无声音语义差异；先由root核既有授权与来源后决定成对回灌，不改变本篇已通过成片判定。')
            elif p.startswith('/区间声音指纹/'):
                e.update(category='interval_fingerprint_metadata_review_separately', root_review_required=True)
            elif p.startswith('/换行变更已获同意/') or p.startswith('/换行变更记录/'):
                old = current.get('换行变更已获同意')
                expected = current.get('换行变更记录', [])
                hist = final.get('换行变更记录', [])
                exact = isinstance(old, dict) and len(hist) == len(expected) + 1 and hist[:-1] == expected and {k: v for k, v in hist[-1].items() if k != '日期'} == old
                e.update(category='layout_permission_archive_verbatim' if exact else 'layout_permission_review_separately',
                         root_review_required=not exact, original_quotes_verbatim_retained=exact)
            elif p.startswith('/结尾句/') and p.endswith('/依据'):
                e.update(category='ending_basis_description_only_review', root_review_required=True,
                         note='仅依据说明文本变化，其他结尾数值需保持深等；不可把自动新文案冒充新用户原话。')
            else:
                e.update(category='unclassified_root_review', root_review_required=True)
        en = [c['en'] for s in current['sentences'] for c in s['chunks']]
        enf = [c['en'] for s in final['sentences'] for c in s['chunks']]
        zh = [M.visible_zh(c['zh']) for s in current['sentences'] for c in s['chunks']]
        zhf = [M.visible_zh(c['zh']) for s in final['sentences'] for c in s['chunks']]
        row = {'source_id': n, 'new_id': a['new_id'], 'handoff': M.record(handoff), 'source_run': h['source_run'],
               'already_passed_video_sha256': a['final_mp4']['sha256'], 'source_files': sources,
               'current_to_request_leaf_diff': M.diff(current, req), 'current_to_final_leaf_diff': changes,
               'proof': M.record(proof_path), 'whole_original_helper_JSON_deep_equal': True,
               'derived_GEN_not_claimed_runtime_executed': True, 'English_exact': en == enf, 'visible_Chinese_exact': zh == zhf,
               'MD_current_request_final_byte_exact': sources['md']['current']['sha256'] == sources['md']['request']['sha256'] == sources['md']['final']['sha256'],
               'categories': dict(Counter(e['category'] for e in changes)),
               'root_review_leaf_count': sum(e['root_review_required'] for e in changes),
               'PAY_write': False, 'video_acceptance_changed': False}
        M.write(OUT / f'article{n}-leaf-diff.json', row)
        rows.append(row)
allc = Counter(e['category'] for r in rows for e in r['current_to_final_leaf_diff'])
summary = {'status': 'additional_passed_readonly_statistics_not_applied', 'created_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
           'articles': [r['source_id'] for r in rows], 'article_count': len(rows), 'leaf_count': sum(allc.values()), 'categories': dict(allc),
           'requires_paired_JSON_GEN_to_capture_final_runtime_state': [r['source_id'] for r in rows if r['current_to_final_leaf_diff']],
           'root_review_articles': [r['source_id'] for r in rows if r['root_review_leaf_count']],
           'not_assumed_from_expected_total': ['10', '11'],
           'root_attention': '12/51有真实确认、指纹和位置元数据变化；25结尾依据文本变化需逐字审。只读记录，不擅盖canonical。',
           'PAY_write': False, 'media_or_acceptance_changed': False,
           'articles_summary': [{k: v for k, v in r.items() if k in ['source_id', 'new_id', 'categories', 'root_review_leaf_count', 'English_exact', 'visible_Chinese_exact', 'MD_current_request_final_byte_exact']} for r in rows]}
M.write(OUT / 'summary.json', summary)
print(json.dumps(summary, ensure_ascii=False, indent=2))
