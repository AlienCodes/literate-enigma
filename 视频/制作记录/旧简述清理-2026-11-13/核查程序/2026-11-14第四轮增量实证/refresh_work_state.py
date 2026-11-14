"""Refresh the progress journal from actual passed handoffs, without changing media or remote refs."""
import base64
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

B = Path(__file__).resolve().parent
D = Path('/workspace/work/video-revision-delivery')
state = json.loads((B / 'LATEST-WORK-STATE.json').read_text())
passed = {}
handoffs = [D / 'actual53-64-validation/archive-handoff.json']
for folder in ('next-passed-validated', 'recovered-canonical-validated', 'inline-passed-validated'):
    handoffs += sorted((D / folder).glob('*/*/archive-handoff.json'))
for handoff in handoffs:
    if not handoff.exists():
        continue
    raw = handoff.read_bytes()
    for article in json.loads(raw).get('articles', []):
        assert article['passed_per_article'] is True
        media = article['final_mp4']
        path = Path(media['path'])
        if path.exists():
            assert path.stat().st_size == media['bytes']
            assert hashlib.sha256(path.read_bytes()).hexdigest() == media['sha256']
        item = {'original_id': article['source_id'], 'book_order': article['new_id'],
                'bytes': media['bytes'], 'sha256': media['sha256'],
                'passed_handoff': str(handoff),
                'passed_handoff_sha256': hashlib.sha256(raw).hexdigest()}
        if item['original_id'] in passed:
            assert passed[item['original_id']]['sha256'] == item['sha256'], 'Conflicting final handoffs'
        passed[item['original_id']] = item
assert len({x['book_order'] for x in passed.values()}) == len(passed)

def api(path):
    return json.loads(subprocess.check_output(['gh', 'api', 'repos/alienalgorithm/postgraduate-vocabulary/' + path]))

head = api('git/ref/heads/main')['object']['sha']
response = api('contents/视频修订定稿/已归档视频总清单.json?ref=' + head)
index_raw = base64.b64decode(response['content'])
index = json.loads(index_raw)
assert len(index['articles']) == index['archived_passed_count']
backup_base = ['gh', 'api', 'repos/AlienCodes/literate-enigma/']
backup_head = json.loads(subprocess.check_output(backup_base[:-1] + [backup_base[-1] + 'git/ref/heads/codex/all-deliverables-20261113']))['object']['sha']
backup_response = json.loads(subprocess.check_output(backup_base[:-1] + [backup_base[-1] + 'contents/视频修订定稿/已归档视频总清单.json?ref=' + backup_head]))
assert base64.b64decode(backup_response['content']) == index_raw, 'Archive writer is still synchronizing the two repositories; retry after its completion.'
for article in index['articles']:
    assert article['source_id'] in passed
    assert article['sha256'] == passed[article['source_id']]['sha256']
archive_state = B / 'progress-observations'
archive_state.mkdir(exist_ok=True)
snapshot = archive_state / ('archived-index-' + head + '.json')
snapshot.write_bytes(index_raw)
state['recorded_at_utc'] = datetime.now(timezone.utc).isoformat()
state['state'] = (f'COMPACT_BOOK_DUAL_ARCHIVED; ALL70_TEXT_LAYOUT_BASE_PASSED; '
                  f'{len(passed)}_ILLUSTRATED_4K_VIDEOS_PASSED; '
                  f'{len(index["articles"])}_PERMANENTLY_DUAL_ARCHIVED; '
                  'REMAINING_OFFICIAL_PRODUCTION_IN_PROGRESS; RELEASE_NOT_YET_PUBLISHED')
p = state['production']
p['new_final_videos_passed'] = len(passed)
p['passed_videos'] = sorted(passed.values(), key=lambda x: int(x['book_order']))
p['permanent_video_archive_snapshot'] = {
    'primary_commit_observed': head, 'count': len(index['articles']),
    'backup_commit_observed': backup_head, 'index_bytes_identical_in_both_repositories': True,
    'path': '视频修订定稿/已归档视频总清单.json',
    'sha256': hashlib.sha256(index_raw).hexdigest(), 'local_original_snapshot': str(snapshot)}
p['active_runs_at_recording'] = {}
ready41 = Path('/workspace/work/video-official-ready41-core3-frozen-20261114/TASK-STATE.json')
if ready41.exists():
    request_state = json.loads(ready41.read_text())
    observation = json.loads(subprocess.check_output(['gh', 'api', 'repos/AlienCodes/literate-enigma/actions/runs/43543967031']))
    assert observation['head_sha'] == request_state['commit']
    p['ready41_official_run'] = {'run': 43543967031, 'commit': request_state['commit'],
        'status_observed': observation['status'], 'conclusion_observed': observation['conclusion'],
        'selected': request_state['selected'], 'original_programs_and_actual_resource_fetch_fix': True,
        'not_counted_as_passed_before_actual_media_validation': True}
    if observation['status'] != 'completed':
        p['active_runs_at_recording']['ready41_official_run'] = 43543967031
p['priority7_native_run'] = 43538347790
p['priority_new_seven']['article_acceptance_not_yet_claimed'] = False
p['priority_new_seven']['accepted_recovered_source_ids'] = [n for n in ('10', '11', '12', '42', '51') if n in passed]
p['priority_new_seven']['all_seven_passed'] = False
p['final_three_core_certification_status'] = 'REAL_ORIGINAL_FULL_QUICKCHECK_PASSED; actual canonical5 permanently saved in both repositories by source phase5'
p['A21_four_specific_data_repairs'] = 'Applied only precise original-release boost instead of duplicate donor metadata15/17/18/30; exact GEN roundtrip and original text gate passed; formal actual audio QA pending'
p['priority7_actual_result'] = {
    'original_quality_passed_png_resource_missing': ['10', '11', '12', '42', '51'],
    'original_outer_failed_status_preserved': True,
    'recovered_counted_only_after_actual_boundary_frames_and_V3': True,
    '44': 'actual raw-PCM G45 confirmation corrected, awaiting official rerun',
    '07': 'requested old ending splice was rewritten automatically; exact existing nonvoice proofs retained; program repair and original checks pending'}
p['observed_blockers'] = [
    '07原已验结尾接点被自动重算，须保留合法已验点并重新通过真实声音检查；不放宽AAC一致性',
    '15/17/18/30四处真实重复词尾已按精确位置修源；须正式合成及全轨声音检查通过',
    '其余篇继续原正式入口逐篇核查；失败计数与机器识别差异不冒称成片合格'
]
p['validated_program_repairs'] = {
    'original_full_regression_run': 43535822030,
    'original_full_regression_passed': True,
    'original_audit_and_thresholds_unchanged': True,
    'repairs': ['显式保持已审增益', '独立核验读取未经加工的原create母素材'],
    'note': '程序回归通过不代替逐篇实际音频和画面验收'}
core5 = B / 'core-overlays/reviewed-five-core/validated-install/manifest.json'
core5_application = core5.parent.parent / 'root-validated-install-application.json'
if core5.exists() and core5_application.exists():
    certified = json.loads(core5.read_text())
    p['validated_program_repairs'] = {
        'original_full_regression_run': certified['run_id'],
        'original_full_regression_passed': certified['actual_full_quickcheck_exit'] == 0,
        'program_count': certified['program_count'],
        'runtime_file_count': certified['runtime_file_count'],
        'all_production_T_program_count': certified['all_production_program_count_verified'],
        'actual_original_full_stamp_sha256': certified['actual_original_full_stamp_SHA256'],
        'repairs': ['显式保持已审增益', '独立核验读取未经加工的原create母素材',
                    '显式保持已有合法末句接点', 'K102仅自检注错保持复合词注册结构'],
        'original_producer_audit_and_thresholds_unchanged': True,
        'stage': 'validated actual full; locally installed PAY; source publication receipt separately recorded',
        'note': '程序回归通过不代替任何篇的实际音频、画面或成片验收'}
    p['core_program_full_original_quickcheck'] = {
        'passed': True, 'run': certified['run_id'], 'commit': certified['source_commit'],
        'seconds': certified['actual_full_quickcheck_seconds'],
        'real_stamp_sha256': certified['actual_original_full_stamp_SHA256'],
        'original_producer_and_quality_thresholds_unchanged': True,
        'not_article_audio_acceptance': True}
p['source_and_audio_revisions_pending_original_final_validation'] = {
    '05': 'Actual old accepted voice source recovered by original source/video/PCM fingerprint and exact accepted AAC; restored only7 controls/reviews+2 existing highlight settings; explicit whole sentence .95 proved bit-identical to old implicit default; genuine core4 rerun43548189084',
    '06_07': 'Original legal requested joins verified by old raw mothers; core4 preserves them and all original sound checks remain; run43548189084',
    '15_17_18_30': 'Actual original A21 duplicate-burst check now0; remaining existing cut/edge confirmations require strict original old/current PCM migration; not final passed',
    '16': 'K102 fault-injection-only repair passed actual full and true original namespace; actual article rerun still required',
    '46_49': 'Root separately approved current-fingerprint S6/S8 ASR measurement record after exact whole accepted audio and original two-engine padded-context agreement; no claimed listening or source/audio/ASR-threshold modification; genuine article rerun required',
    '02': 'Original auto writer demonstrably cut90ms of previously confirmed /v/; source-preservation mode candidate remains isolated until separate real full certification',
}
cuts = B / 'core-overlays/keep-reviewed-cuts/production-contract/manifest.json'
if cuts.exists() and (cuts.parent.parent / 'root-validated-install-application.json').exists():
    certified = json.loads(cuts.read_text())
    actual = certified['actual_native_certification']
    p['validated_program_repairs'].update(
        original_full_regression_run=actual['run_id'],
        original_full_regression_passed=actual['actual_full_quickcheck_exit'] == 0,
        program_count=certified['program_count'], runtime_file_count=certified['runtime_file_count'],
        actual_original_full_stamp_sha256=certified['actual_native_fastcheck_stamp']['sha256'],
        stage='validated actual full and complete02 default/preserve comparison; locally installed PAY; publication receipts tracked separately')
    p['validated_program_repairs']['repairs'].append('显式保持已审切点，仍实测并报告原auto建议、保留原坏区间拒绝')
    p['core_program_full_original_quickcheck'].update(
        run=actual['run_id'], commit=actual['commit'], seconds=actual['actual_full_quickcheck_seconds'],
        real_stamp_sha256=certified['actual_native_fastcheck_stamp']['sha256'])
    p['source_and_audio_revisions_pending_original_final_validation']['02'] = (
        'Preserve-reviewed-cuts mode passed actual original full plus complete02 default/preserve PCM/AAC comparisons and all original negative controls; installed PAY; actual article full gates still required')
p['historical_three_core_regression'] = {'run': 43535822030, 'passed': True, 'superseded_runtime_certificate_is_recorded_above': True}
p.pop('final_three_core_certification_status', None)
for title, run_id in (('05_06_07_core4', 43548189084), ('16_46_49_core5', 43554669373)):
    observed = json.loads(subprocess.check_output(['gh', 'api', 'repos/AlienCodes/literate-enigma/actions/runs/' + str(run_id)]))
    p.setdefault('actual_new_native_run_observations', {})[title] = {
        'run_id': run_id, 'head_sha': observed['head_sha'], 'status': observed['status'],
        'conclusion': observed['conclusion'], 'not_article_acceptance_without_actual_handoff': True}
    if observed['status'] != 'completed':
        p['active_runs_at_recording'][title] = run_id
if '44' in passed:
    p['priority7_actual_result']['44'] = 'Actual genuine new native4K, original special full-audio QC, actual five-frame review and complete V3 passed; permanent archive tracked separately'
p['observed_blockers'] = [
    '02原auto writer新增剪已确认/v/；严格A/B已复现90ms差异；仅候选保护已审切点模式，须单独原full后正式重验',
    'A21四篇原词尾门已0，已有typed确认需原严格平移；新boost区内不能冒称逐样本原声相同',
    '剩余真实响度/高亮/识别及原AAC不一致逐篇实测，不以程序证书或队列状态当成片通过',
]
p['release_published'] = False
p['old_release_deleted'] = False
(B / 'LATEST-WORK-STATE.json').write_text(json.dumps(state, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'actual_passed': len(passed), 'permanent_archived': len(index['articles']),
                  'source_ids': sorted(passed), 'remote_write_executed': False}, ensure_ascii=False))
