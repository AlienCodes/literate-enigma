import csv
import datetime
import hashlib
import json
import pathlib

B = pathlib.Path(__file__).parent
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
d = json.loads((B / 'claimed-state.json').read_text())
rows = []
for a in d['ingested_and_handed_off']:
    p = pathlib.Path(d['handoffs'][a])
    h = json.loads(p.read_text())['articles'][0]
    r = json.loads((p.parent / 'report.json').read_text())['actual_articles'][0]
    review = json.loads((p.parent / a / 'actual-boundary-frame-review.json').read_text())
    assert h['passed_per_article'] and review['actually_visually_reviewed']
    rows.append(dict(source_id=a, new_id=h['new_id'], actual_native_quality_acceptance=True,
        V3_passed=True, actual_5_boundaries_visually_reviewed=True,
        mp4_bytes=h['final_mp4']['bytes'], mp4_sha256=h['final_mp4']['sha256'],
        AAC_packets=r['actual_aac_packet_count'], handoff=str(p), handoff_sha256=sha(p),
        archive_owner_received=True))
for a in d['native_job_failed_ids']:
    if a in ['46', '48', '49']:
        p = B / f'failed{a}/readonly-failure-classification.json'
        f = json.loads(p.read_text())
        stage, error = f['actual_stage'], f['actual_error']
        primary = f.get('primary_class', f.get('actual_primary_failure_class'))
    elif a in ['65', '67', '68', '70']:
        p = B / 'readonly65-67-68-70-priorAAC.json'
        f = next(x for x in json.loads(p.read_text())['rows'] if x['source_id'] == a)
        stage, error = f['original_stage'], f['actual_error']
        primary = 'canonical_pipeline_passed_but_exact_prior_AAC_identity_failed'
    else:
        p = pathlib.Path(d['delegated_failure_report'])
        f = next(x for x in json.loads(p.read_text())['articles'] if x['article'] == a)
        stage, error = f.get('stage', f.get('actual_stage')), f.get('error', f.get('actual_error'))
        primary = {'54':'formal4K_original_loudness_2_low_segments',
            '61':'draft_original_highlight_boundary_S1C2',
            '66':'draft_original_ASR_duly_dually_S9',
            '69':'canonical_pipeline_passed_but_exact_prior_AAC_identity_failed'}[a]
    rows.append(dict(source_id=a, actual_native_quality_acceptance=False, V3_passed=False,
        native_stage=stage, actual_error=error, classification=primary,
        original_failure_report=str(p), failure_report_sha256=sha(p), not_ingested_as_final=True))
rows.sort(key=lambda x: int(x['source_id']))
assert len(rows) == 20 and sum(x['V3_passed'] for x in rows) == 9
report = dict(created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    run_id=43543967031, scope='root-assigned actual second20 terminal outcomes; no unsuccessful media substituted',
    genuine_native_success_V3_passed_count=9, failed_native_not_accepted_count=11,
    source_or_core_or_threshold_changed=False, successful_native_final_bytes_preserved=True,
    tail_appended_again=False, rows=rows, current_readonly_further_diagnosis_ids=['48','67','68','70'],
    archive_state='root confirms all nine included in actual global50 dual main/backup archive; exact complete commit receipt remains with archive owner',
    root_reported_main_commit_prefix='ab9ff85f', root_reported_backup_commit_prefix='b6696157')
p = B / 'final20-native-outcomes.json'
p.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
c = B / 'final20-native-outcomes.csv'
fields = ['source_id','new_id','actual_native_quality_acceptance','V3_passed','mp4_bytes','mp4_sha256','native_stage','classification','handoff','original_failure_report']
with c.open('w', newline='') as fh:
    w = csv.DictWriter(fh, fieldnames=fields, extrasaction='ignore')
    w.writeheader()
    w.writerows(rows)
print(json.dumps(dict(report=str(p), sha256=sha(p), csv=str(c), passed=9, failed=11)))
