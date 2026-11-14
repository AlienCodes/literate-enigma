"""Read-only classification of the first25 actual failed native status JSONs."""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re

B=Path('/workspace/work/video-audit70-20261113/ci63-diagnostics-43523430839')
OUT=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
old_path=B/'ci63-diagnostic-report.json'
old=json.loads(old_path.read_text())
previous={r['article']:r for r in old['articles']}
wrapper={r['article']:r for r in old['summary_wrapper_false_rejections']}
primary={
    '01':'missing_reference_cache','02':'missing_reference_cache','03':'text_table_parser_data',
    '04':'missing_reference_cache','05':'cross_article_context','06':'audio_interval_data_invalid',
    '08':'missing_reference_cache','09':'missing_reference_cache','13':'reported_audio_quality_gates',
    '14':'independent_cut_review','15':'audio_double_release','16':'missing_reference_cache',
    '17':'audio_double_release','18':'audio_double_release','19':'independent_cut_review',
    '20':'reported_audio_quality_gates','21':'reported_audio_quality_gates','22':'independent_cut_review',
    '23':'reported_audio_quality_gates','24':'reported_audio_quality_gates',
    '26':'wrapper_summary_decoration','27':'wrapper_summary_decoration','28':'checker_selftest_failure',
    '29':'wrapper_summary_decoration','30':'audio_double_release'}
meaning={
    'missing_reference_cache':'Terminal missing exact reference/cache key; other reported audio failures remain unresolved and cannot be erased by fixing the missing reference.',
    'text_table_parser_data':'Original sync_article K98 cannot read a usable part-of-speech/meaning entry for germ.',
    'cross_article_context':'Original T12 sees convicted of highlighted in baseline article23 inside a per-article job; install the consistent approved all70 context before rechecking.',
    'audio_interval_data_invalid':'Actual configured nonvoice interval is rejected before rendering; generated fingerprint/report files subsequently absent are downstream context failures.',
    'reported_audio_quality_gates':'Native checker reports unresolved noise/cut/highlight issues; audio was not listened to for this read-only classification.',
    'independent_cut_review':'Native independent cut/edge review is not passed; no conclusion that audio is acceptable follows from other checks passing.',
    'audio_double_release':'Original A21 reports duplicated transplanted release over an existing original release, requiring specific acoustic/data review.',
    'wrapper_summary_decoration':'Original draft post-checks pass, official4K/stamp stage completes, and only renderer line-leading continuation marks plus whitespace differ in the summary; rerun the strict wrapper, never relabel the failed artifact as passed.',
    'checker_selftest_failure':'Original checker selftest fails, so its downstream cut counts are explicitly untrusted and cannot be treated as a valid acoustic verdict.'}
patterns=[
    ('reported_nonvoice_noise',r'✘.*纯人声核对'),
    ('independent_cut_edges_unresolved',r'✘.*独立复核'),
    ('highlight_timing_unresolved',r'✘.*高亮同步核对（'),
    ('highlight_selftest_failure',r'✘.*高亮同步核对\s*自检'),
    ('checker_selftest_failure',r'✘.*核查程序自检'),
    ('audio_nonvoice_interval_invalid',r'【停止】非人声区间不对'),
    ('audio_double_release',r'BAD 双爆破'),
    ('reported_loudness_mismatch',r'相邻两句相差.*LU'),
    ('pronunciation_replacement_incomplete',r'【停止】读音改正没有全部换到'),
    ('checker_untrusted',r'核查程序失灵'),
    ('missing_generated_fingerprint_context',r'FileNotFoundError:.*句子声音指纹'),
]

def lines_of(value):
    if isinstance(value,str): return value.splitlines()
    if isinstance(value,list): return [s for x in value for s in lines_of(x)]
    if isinstance(value,dict): return [s for x in value.values() for s in lines_of(x)]
    return []

def concise(value):
    value=re.sub(r'\x1b\[[0-9;]*m','',value).strip()
    return value[:320]

rows=[]
for path in sorted((B/'relay-files').glob('*-status.json')):
    data=json.loads(path.read_text());n=data['article'];before=previous[n]
    assert data['passed']is False
    assert sha(path)==before['status_file_SHA256']
    failure=data.get('failure_details',{})
    lines=list(dict.fromkeys(lines_of(failure)+lines_of(data.get('check_summaries',{}))))
    labels=[];evidence=[]
    for label,pattern in patterns:
        matches=[s for s in lines if re.search(pattern,s)]
        if matches:
            labels.append(label);evidence.append({'category':label,'native_diagnostic':concise(matches[0])})
    terminal=data.get('error','')
    cache_key=re.search(r'([0-9a-f]{40}\.pkl)',terminal)
    if cache_key:
        evidence.insert(0,{'category':'missing_reference_cache','native_diagnostic':f"git show HEAD:视频/配音缓存/{cache_key.group(1)} returned exit128; exact Git reference/cache object absent"})
    if primary[n]in('text_table_parser_data','cross_article_context'):
        textline=next(s for s in lines if ('速查表这些新重点词' in s if n=='03' else 'T12 新加重点词撞词' in s))
        evidence.insert(0,{'category':primary[n],'native_diagnostic':concise(textline)})
    immediate=False;wrapper_proof=None
    checks=data.get('check_summaries',{})
    draft_pass=any('⑤ 出片后核查：全部通过'in s for s in checks.get('canonical-draft-00.log',[]))
    if n in wrapper:
        w=wrapper[n];p=w['canonical_4K_failed_proof']
        assert data['stage']=='original-stamp-after-production.log'
        assert 'canonical-final4K-00.log'in checks and draft_pass and not failure and terminal==''
        assert w['candidate_line_leading_continuation_only_equal']is True
        assert w['current_rule_whitespace_only_equal']is False
        assert w['requested_primary_points']==w['actual_primary_points']==5
        assert p['render_resolution']==[3840,2160] and p['AAC_exact_equal']is True
        assert p['sourcehash_matches_proof']and p['english_word_lists_equal_request']
        immediate=True
        wrapper_proof={'source':'previous report exact source/summary comparison plus actual native status and4K failed-current proof',
                       'source_evidence_report_sha256':sha(old_path),
                       'only_line_leading_continuation_marks_and_whitespace_differ':True,
                       'main_summary_points_preserved':5,
                       'added_line_leading_continuation_marks':w['added_line_leading_continuation_bullets'],
                       'actual_working_source_sha256':w['working_source_SHA256'],
                       'failed_current_4K_proof_path':p['file'],'failed_current_4K_proof_sha256':p['SHA256'],
                       'accepted_prior_AAC_exact_equal':True,
                       'canonical_finalization_returned_before_observed_stamp_stage':True,
                       'explicit_native_canonical_pipeline_passed_flag':data.get('canonical_pipeline_passed'),
                       'does_not_convert_native_failed_status_to_passed':True}
        evidence=[{'category':'wrapper_summary_decoration','native_diagnostic':'⑤ 出片后核查：全部通过；随后已到 original-stamp-after-production.log；现存3840×2160 proof，摘要仅行首▹和空白差异。'}]
    rows.append({'article':n,'native_status_path':str(path),'native_status_sha256':sha(path),
                 'native_status_passed':False,'stage':data['stage'],'failure_step':failure.get('step'),
                 'primary_class':primary[n],'primary_explanation':meaning[primary[n]],
                 'secondary_classes':[x for x in labels if x!=primary[n]],
                 'final_error':concise(terminal),'terminal_missing_reference_key':cache_key.group(1)if cache_key else None,
                 'diagnostics':evidence,'original_draft_postchecks_explicitly_all_passed':draft_pass,
                 'original_4K_finalize_then_stamp_reached':data['stage']=='original-stamp-after-production.log',
                 'original_checks_all_passed_proven_before_wrapper':immediate,
                 'wrapper_only_immediate_retry_after_fixed_strict_wrapper':immediate,
                 'wrapper_evidence':wrapper_proof,
                 'actual_audio_listening_or_new_acoustic_acceptance_performed':False,
                 'candidate_audio_fault_not_independently_proven_by_this_classification':primary[n]!='wrapper_summary_decoration',
                 'acceptance':False})
assert len(rows)==25 and {r['article']for r in rows}==set(primary)
report={'kind':'read-only-first25-native-final-failure-classification',
        'producer_run_id':43523430839,'generated_utc':datetime.now(timezone.utc).isoformat(),
        'input_original_diagnostic_report':str(old_path),'input_original_diagnostic_report_sha256':sha(old_path),
        'native_status_count':25,'all_status_files_SHA256_match_original_public_diagnostic_report':True,
        'network_or_media_or_private_reference_data_read':False,'source_or_official_checks_modified':False,
        'classifications_are_not_new_quality_acceptance':True,
        'primary_counts':dict(Counter(r['primary_class']for r in rows)),
        'fixed_wrapper_only_retry_ids':[r['article']for r in rows if r['wrapper_only_immediate_retry_after_fixed_strict_wrapper']],
        'articles':rows}
OUT.mkdir(parents=True,exist_ok=True)
(OUT/'initial25-classification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'count':25,'primary_counts':report['primary_counts'],'fixed_wrapper_only_retry_ids':report['fixed_wrapper_only_retry_ids']},ensure_ascii=False))
