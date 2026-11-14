"""Classify the remaining36 failed native artifacts from verified public JSON only."""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re

BASE=Path(__file__).resolve().parent
PUBLIC=BASE/'public-evidence'
OLD=Path('/workspace/work/video-audit70-20261113/ci63-diagnostics-43523430839')
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
jobs=json.loads((BASE/'jobs-final.json').read_text())['jobs']
artifacts=json.loads((BASE/'artifacts-final.json').read_text())['artifacts']
by_job={re.fullmatch(r'produce \((\d\d)\)',j['name']).group(1):j for j in jobs if re.fullmatch(r'produce \((\d\d)\)',j['name'])}
by_art={re.fullmatch(r'article(\d\d)-revised-canonical-4K-final',a['name']).group(1):a for a in artifacts if re.fullmatch(r'article(\d\d)-revised-canonical-4K-final',a['name'])}
old_ids={p.name[:2]for p in (OLD/'relay-files').glob('*-status.json')}
expected={n for n,j in by_job.items()if j['status']=='completed'and j['conclusion']=='failure'}-old_ids
assert len(by_job)==63 and len(expected)==36


def text_lines(value):
    if isinstance(value,str):return value.splitlines()
    if isinstance(value,list):return [s for x in value for s in text_lines(x)]
    if isinstance(value,dict):return [s for x in value.values()for s in text_lines(x)]
    return []


def concise(s):
    return re.sub(r'\x1b\[[0-9;]*m','',s).strip()[:380]


def summary(data):
    values=[]
    for sentence in data['sentences']:
        for chunk in sentence['chunks']:
            note=chunk.get('note','');start=note.find('（简述：')
            if start<0:continue
            depth=0
            for end in range(start,len(note)):
                depth+=(note[end]=='（')-(note[end]=='）')
                if depth==0:
                    values.append(note[start:end+1]);break
    assert len(values)==1,('Expected exactly one balanced summary',data['no'])
    return values[0]


def normalize_summary(text):
    # EXACT exception: only renderer-added line-leading continuation marks;
    # primary point marks, every word and all punctuation are retained.
    return re.sub(r'\s+','',re.sub(r'(?m)^[ \t]*▹[ \t]*','',text))


def public_file_receipt(directory,path,receipt):
    row=next(r for r in receipt['public_files']if Path(r['path']).resolve()==path.resolve())
    assert sha(path)==row['saved_sha256']
    return {'path':str(path),'sha256':sha(path),'artifact_member':row['artifact_member'],
            'artifact_member_sha256':row['artifact_member_sha256'],'sanitized':row['sanitized']}


patterns=[
    ('reported_nonvoice_noise',r'✘.*纯人声核对'),
    ('independent_cut_edges_unresolved',r'✘.*独立复核'),
    ('highlight_timing_unresolved',r'✘.*高亮同步核对（'),
    ('highlight_selftest_failure',r'✘.*高亮同步核对\s*自检'),
    ('checker_selftest_failure',r'✘.*核查程序自检'),
    ('checker_runtime_failure',r'IndexError:|RuntimeError:|AssertionError:'),
    ('machine_relisten_unresolved',r'✘.*机器复听'),
    ('checker_untrusted',r'核查程序失灵'),
    ('missing_reference_cache',r'严格缓存.*缺配音缓存|git.+show.+配音缓存'),
    ('reference_CPU_or_timeout',r'CPUExecutionProvider.*(fail|error)|TimeoutExpired|timed out|reference.*CPU.*(fail|error)'),
]
explanations={
    'wrapper_summary_decoration':'Original draft checks pass and official4K returns before stamp; actual five-point summary differs only by renderer line-leading continuation marks/whitespace, and actual4K candidate AAC equals accepted AAC. Rerun fixed strict wrapper, without relabelling failed output as passed.',
    'wrapper_summary_decoration_and_candidate_AAC_drift':'Summary decoration is the immediate assertion, but actual4K candidate AAC also differs from accepted AAC. The wrapper assertion occurs before its AAC identity gate, so fixing decoration alone cannot establish acceptance; no acoustic cause is inferred from SHA inequality.',
    'post_finalize_source_fingerprint_evidence_gap':'Official draft/4K reaches post-production stamp, but export refuses a mismatched script fingerprint. No actual working-source/proof exists to verify summary decoration or accepted AAC; not a CPU or actual-audio verdict.',
    'checker_runtime_failure':'Original independent checker raises IndexError: list index out of range and its selftest also fails. The reported zero change/cut counts are not a completed passing audit.',
    'checker_selftest_failure':'Original independent-checker selftest misses deliberately injected faults; downstream large cut/extra counts are explicitly untrusted. Do not reclassify these as verified actual acoustic faults or infer CPU failure.',
    'machine_relisten_unresolved':'Native ASR-based reread reports a word mismatch; actual acoustic review is still required, and this read-only classification has not listened to or accepted the audio.',
    'reported_audio_quality_gates':'Native nonvoice/cut/highlight checks report unresolved issues; no new acoustic acceptance or actual-listening claim is made.',
    'highlight_timing_unresolved':'Original L14 reports a block start discrepancy and fails; preserve the original threshold and resolve against actual speech/fingerprint rather than rounded displayed milliseconds.',
    'reference_CPU_or_timeout':'Explicit reference CPU/timeout diagnostics were observed; a long runtime alone is never sufficient for this class.',
    'missing_reference_cache':'An exact required private reference/cache object is absent; fixing that object does not automatically clear any other reported gates.'}

rows=[]
for path in sorted(PUBLIC.glob('*/*-status.json')):
    data=json.loads(path.read_text());n=data['article']
    if n not in expected:continue
    directory=path.parent;receipt_path=directory/'artifact-retrieval-receipt.json';receipt=json.loads(receipt_path.read_text());artifact=by_art[n]
    assert data['passed']is False and by_job[n]['conclusion']=='failure'
    assert receipt['article']==n and receipt['run_id']==43523430839 and receipt['artifact_id']==artifact['id']
    assert receipt['github_declared_zip_sha256']==artifact['digest'].removeprefix('sha256:')
    assert receipt['github_declared_zip_bytes']==artifact['size_in_bytes']
    assert receipt['zip_digest_verified']and receipt['zip_removed_after_public_extraction']
    assert receipt['private_audio_GT_cache_or_media_extracted']is False
    status_receipt=public_file_receipt(directory,path,receipt)
    assert status_receipt['sanitized']is False and status_receipt['artifact_member_sha256']==sha(path)
    request_path=OLD/'immutable-requests'/(n+'.json')
    request_sha=sha(request_path)
    assert data['request_source_sha256'][f'视频/脚本/{n}.json']==request_sha
    request=json.loads(request_path.read_text())
    failure=data.get('failure_details',{})
    lines=list(dict.fromkeys(text_lines(failure)+text_lines(data.get('check_summaries',{}))))
    labels=[];diagnostics=[]
    for label,pattern in patterns:
        matches=[s for s in lines if re.search(pattern,s,re.I)]
        if matches:
            labels.append(label);diagnostics.append({'category':label,'native_diagnostic':concise(matches[0])})
    checks=data['check_summaries'];draft_pass=any('⑤ 出片后核查：全部通过'in s for s in checks.get('canonical-draft-00.log',[]))
    stamp=data['stage']=='original-stamp-after-production.log'
    proof_path=directory/(n+'-failed-draft-proof.json');working_path=directory/(n+'-failed-working-source.json')
    proof=None;proof_evidence=None;wrapper_evidence=None;immediate=False
    if proof_path.exists():
        proof=json.loads(proof_path.read_text());proof_file=public_file_receipt(directory,proof_path,receipt)
        assert proof_file['sha256']==data['failed_current_video']['proof_sha256']
        assert proof['video_sha256']==data['failed_current_video']['sha256']
        assert proof['official_fingerprint_matches_current_video_source_and_pcm']is True
        assert working_path.exists()and sha(working_path)==proof['source_sha256']
        assert proof['video_mtime_ns']>=proof['production_started_ns']
        public_file_receipt(directory,working_path,receipt)
        video=next(v for v in proof['ffprobe']['streams']if v['codec_type']=='video')
        aac_equal=proof['aac_adts_sha256']==data['accepted_source']['aac_adts_sha256']
        proof_evidence={'path':str(proof_path),'sha256':sha(proof_path),'working_source_path':str(working_path),
                        'working_source_sha256':sha(working_path),'fingerprint_matches_current_video_source_and_pcm':True,
                        'render_resolution':[video['width'],video['height']],
                        'video_sha256':proof['video_sha256'],'candidate_aac_adts_sha256':proof['aac_adts_sha256'],
                        'accepted_prior_aac_adts_sha256':data['accepted_source']['aac_adts_sha256'],
                        'AAC_exact_equal':aac_equal,'acceptance':False}
    if stamp:
        assert draft_pass and 'canonical-final4K-00.log'in checks and not failure and data.get('error','')==''
        if proof and working_path.exists():
            assert proof_evidence['render_resolution']==[3840,2160]
            working=json.loads(working_path.read_text());first=summary(request);second=summary(working)
            only_marks=normalize_summary(first)==normalize_summary(second)
            whitespace_equal=re.sub(r'\s+','',first)==re.sub(r'\s+','',second)
            assert only_marks and not whitespace_equal and first.count('▸')==second.count('▸')==5
            wrapper_evidence={'only_line_leading_continuation_marks_and_whitespace_differ':True,
                             'main_summary_points_preserved':5,
                             'added_line_leading_continuation_marks':len(re.findall(r'(?m)^[ \t]*▹',second)),
                             'requested_summary_sha256':hashlib.sha256(first.encode()).hexdigest(),
                             'actual_summary_sha256':hashlib.sha256(second.encode()).hexdigest(),
                             'canonical_finalization_returned_before_observed_stamp_stage':True,
                             'explicit_native_canonical_pipeline_passed_flag':data.get('canonical_pipeline_passed'),
                             'accepted_prior_AAC_exact_equal':proof_evidence['AAC_exact_equal']}
            if proof_evidence['AAC_exact_equal']:
                primary='wrapper_summary_decoration';immediate=True
            else:
                primary='wrapper_summary_decoration_and_candidate_AAC_drift'
                labels.append('candidate_AAC_differs_from_accepted_prior')
            diagnostics.insert(0,{'category':'wrapper_summary_decoration','native_diagnostic':'⑤ 出片后核查：全部通过；官方4K后已到stamp阶段；摘要逐字只差行首▹和空白。'})
        else:
            primary='post_finalize_source_fingerprint_evidence_gap'
            assert data.get('failed_current_video',{}).get('exported')is False
            diagnostics.insert(0,{'category':primary,'native_diagnostic':concise(data['failed_current_video']['reason'])+'; mismatched_fingerprint_fields='+str(data['failed_current_video'].get('mismatched_fingerprint_fields'))})
    elif 'reference_CPU_or_timeout'in labels:primary='reference_CPU_or_timeout'
    elif 'missing_reference_cache'in labels:primary='missing_reference_cache'
    elif 'checker_runtime_failure'in labels:primary='checker_runtime_failure'
    elif 'checker_selftest_failure'in labels:primary='checker_selftest_failure'
    elif 'machine_relisten_unresolved'in labels:primary='machine_relisten_unresolved'
    elif 'reported_nonvoice_noise'in labels:primary='reported_audio_quality_gates'
    elif 'highlight_timing_unresolved'in labels:primary='highlight_timing_unresolved'
    else:raise AssertionError(('Unclassified native failure',n,labels))
    if primary=='wrapper_summary_decoration_and_candidate_AAC_drift':
        diagnostics.insert(0,{'category':primary,'native_diagnostic':'Current4K candidate AAC '+proof_evidence['candidate_aac_adts_sha256']+' != accepted AAC '+proof_evidence['accepted_prior_aac_adts_sha256']})
    diagnostics.sort(key=lambda r:r['category']!=primary)
    rows.append({'article':n,'native_status_path':str(path),'native_status_sha256':sha(path),
                 'native_status_passed':False,'stage':data['stage'],'failure_step':failure.get('step'),
                 'primary_class':primary,'primary_explanation':explanations[primary],
                 'secondary_classes':[x for x in labels if x!=primary],
                 'final_error':concise(data.get('error','')),'diagnostics':diagnostics,
                 'original_draft_postchecks_explicitly_all_passed':draft_pass,
                 'original_4K_finalize_then_stamp_reached':stamp,
                 'original_checks_all_passed_proven_before_wrapper':bool(wrapper_evidence),
                 'wrapper_only_immediate_retry_after_fixed_strict_wrapper':immediate,
                 'wrapper_evidence':wrapper_evidence,'failed_candidate_proof':proof_evidence,
                 'request_source_path':str(request_path),'request_source_sha256':request_sha,
                 'request_SHA_matches_actual_consumed_status':True,
                 'artifact_receipt':{'path':str(receipt_path),'sha256':sha(receipt_path),
                                     'artifact_id':receipt['artifact_id'],'github_declared_zip_sha256':receipt['github_declared_zip_sha256'],
                                     'github_declared_zip_bytes':receipt['github_declared_zip_bytes'],
                                     'zip_digest_verified':True,'zip_removed_after_public_extraction':True,
                                     'status_is_actual_unsanitized_ZIP_member':True,
                                     'status_artifact_member':status_receipt['artifact_member'],
                                     'private_audio_GT_cache_or_media_extracted':False},
                 'actual_audio_listening_or_new_acoustic_acceptance_performed':False,'acceptance':False})

found={r['article']for r in rows}
assert found==expected and len(rows)==36,(sorted(expected-found),len(rows))
safe=[r['article']for r in rows if r['wrapper_only_immediate_retry_after_fixed_strict_wrapper']]
report={'kind':'read-only-remaining36-native-final-failure-classification',
        'producer_run_id':43523430839,'generated_utc':datetime.now(timezone.utc).isoformat(),
        'finalized':True,'native_status_count':36,'expected_failure_ids_from_actual_final_jobs':sorted(expected),
        'jobs_final_sha256':sha(BASE/'jobs-final.json'),'artifacts_final_sha256':sha(BASE/'artifacts-final.json'),
        'all_statuses_bound_to_actual_connector_artifact_digest_receipts':True,
        'all_original_request_JSON_hashes_match_actual_native_status':True,
        'source_or_official_checks_modified':False,'network_or_media_or_private_reference_data_read':False,
        'classifications_are_not_new_quality_acceptance':True,
        'primary_counts':dict(Counter(r['primary_class']for r in rows)),
        'fixed_wrapper_only_retry_ids':safe,
        'wrapper_candidates_blocked_by_candidate_AAC_drift':[r['article']for r in rows if r['primary_class']=='wrapper_summary_decoration_and_candidate_AAC_drift'],
        'post_finalize_evidence_gaps':[r['article']for r in rows if r['primary_class']=='post_finalize_source_fingerprint_evidence_gap'],
        'reference_CPU_or_timeout_failure_evidence_count':sum(r['primary_class']=='reference_CPU_or_timeout'for r in rows),
        'no_CPU_root_cause_inferred_from_long_runtime_or_checker_selftest_failures':True,
        'articles':rows}
(BASE/'new36-classification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:report[k]for k in ['native_status_count','primary_counts','fixed_wrapper_only_retry_ids','wrapper_candidates_blocked_by_candidate_AAC_drift','post_finalize_evidence_gaps']},ensure_ascii=False))
