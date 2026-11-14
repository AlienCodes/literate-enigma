"""Actual source28 hold18 preview: inherit real full V3; validate only changed tail.

No new Actions job, TTS, body generation or user final acceptance is claimed.
Original immutable artifacts, original quality reports and the0.3 preview remain.
"""
import copy
import hashlib
import importlib.util
import json
import shutil
import sys
from pathlib import Path

from hold18_geometry import geometry, decoded_hold, eligibility, require
from build_actual_composition_bridge import build as build_bridge

HERE = Path(__file__).resolve().parent
BASE = Path('/workspace/work/video-revision-delivery/native-inline-engine-frozen-20261114-v13-reviewed33-layout-reference')
sys.path.insert(0, str(BASE))
import delivery as D

H = Path('/workspace/work/video-audit70-20261113/article28-user-review-20261114')
UP = H / 'hold18-preview/upstream'
TAIL = H / 'hold18-integrator'
PRIOR = Path('/workspace/work/video-revision-delivery/preview28-validated/43576642418/28/preview-handoff.json')
OUT = Path('/workspace/work/video-revision-delivery/post-only-hold18-validated/28')
PROGRAM_SHA = 'a05b4455de5225bfca0f5f2ee8fa31ce59d15cd3556dd831228a754fc290831a'
POLICY = Path('/workspace/work/first50-review-release/USER-REVIEW-2026-11-14-051.json')


def spec(path):
    p = Path(path).resolve()
    return {'path': str(p), 'bytes': p.stat().st_size, 'sha256': D.digest(p)}


def checked(row):
    p = Path(row['path'])
    require(p.stat().st_size == row['bytes'] and D.digest(p) == row['sha256'], 'Actual frozen file differs: ' + str(p))
    return p


def module(path):
    s = importlib.util.spec_from_file_location('actual_frozen_hold18_tail', path)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


def validate(write=True):
    require(D.digest(POLICY) == '4bcae46b68b9584f107966f683af580b474fa9835f101834fe55ed6968dfc36b', 'Actual accepted0.6 policy differs')
    require(D.digest(PRIOR) == '0a6132afd529dddd8425a84253b15e823af9b55360895b1dcb61428abf1b5423', 'Original full V3 preview handoff differs')
    prior = D.load(PRIOR)
    require(prior['status'] == 'passed_actual_native_preview28_for_user_review_only' and prior['preview_only'] is True, 'Real original full V3 preview required')
    for row in prior['validation_files']:
        checked(row)
    original = prior['articles'][0]
    checked(original['preview_mp4'])
    source = checked(original['canonical_source_mp4'])
    old_record = D.load(original['validated_record'])
    old_qc = old_record['qc']
    require(old_qc['source_sha256']['request']['json'] == 'e0c8e6c644ab0c5d52d99c23461b99e9ae1574aa574369e56feb35e2ac20698b', 'Inherited request differs')
    require(old_record['preview_delivery_eligible'] is True and original['preview_passed'] is True and old_qc['audio']['repair_applied'] is False, 'Original full source/audio V3 must remain passed')
    report_path = TAIL / '28-actual-new-hold18-art60-summary60-report.json'
    raw = D.load(report_path)
    require(raw['article'] == '28' and raw['book_new_id'] == '29' and raw['passed'] is True
            and raw['kind'] == 'preview-last-body-hold18-then-approved-book-illustration60-then-approved-summary60'
            and raw['postprocessor_sha256'] == PROGRAM_SHA, 'Actual source28 frozen hold18 report required')
    eligibility(preview_only=raw['preview_only'], preview_delivery_eligible=raw['preview_delivery_eligible'],
                production_delivery_eligible=raw['production_delivery_eligible'],
                active_final_replacement_authorized=False, final_user_acceptance=False)
    helper = TAIL / 'illustrated_tail.py'
    require(D.digest(helper) == PROGRAM_SHA, 'Actual postprocessor bytes changed')
    final = TAIL / '28-4K-正文读完停留0.6秒-插图2秒-简述2秒-审核样片.mp4'
    require(D.digest(final) == raw['video_sha256'], 'Actual new preview MP4 differs')
    raw_up = D.load(UP / '28-verification.json')
    adapted = D.load(UP / '28-summary-verification.json')
    status = D.load(UP / '28-upstream-summary-status.json')
    produced = D.load(UP / '28-current-new-body-hold18-upstream-verification.json')
    upstream = UP / '28-new-requested-preview-hold18-then-summary60.mp4'
    require(D.digest(upstream) == raw_up['video_sha256'] == raw['input_video_sha256'] == produced['actual_output_sha256'], 'Actual local upstream identity differs')
    require(produced['original_source_video_sha256'] == D.digest(source)
            and produced['real_prior_quality_passed_run'] == 43576642418
            and produced['native_new_requested_video_generated'] is False,
            'Local postprocessor must inherit the actual original QA source, never a fabricated new native run')
    require(produced['original_builtin_end_card_checks_really_passed'] is True
            and produced['all_audio_packet_payload_side_data_absolute_clock_exact'] is True,
            'Real original end-card checks and audio copy required')
    for key in ('original_audio_identical', 'original_audio_packet_timings_identical',
                'copied_prefix_coded_pictures_identical', 'copied_prefix_packet_timings_identical', 'body_script_identical'):
        require(raw_up[key] is True, 'Actual original end-card failed: ' + key)
    require(raw_up['body_outside_summary_min_ssim'] >= .999 and raw_up['old_summary_pixel_verification']['held_body_frame_match_error'] < 2,
            'Actual changed tail/body must retain the original end-card visual bounds')
    require(raw_up['kind'] == 'preview-last-body-hold18-then-summary60' and raw_up['unheld_voice_ceiling_frame'] == 4720
            and raw_up['held_body_reference_frame'] == 4719 and raw_up['held_final_body_frames'] == 18,
            'Local18 source must not relabel speech end')
    require(adapted['postprocessing_only'] is True and adapted['inherited_true_native_full_QA_run'] == 43576642418
            and status['true_original_native_full_QA_run'] == 43576642418
            and D.digest(UP / '28-summary-verification.json') == raw['upstream_verification_sha256']
            and D.digest(UP / '28-upstream-summary-status.json') == raw['upstream_status_sha256'],
            'Honest local adapter lineage differs')
    require(raw['body_reencoded_frames'] == raw['audio_reencoded_or_added_packets'] == 0
            and raw['body_coded_pictures_identical'] is True and raw['body_packet_timings_identical'] is True
            and raw['body_codec_and_display_parameters_identical'] is True
            and raw['audio_codec_parameters_identical'] is True
            and raw['aac_packet_payload_and_absolute_timings_identical'] is True,
            'Art/card composition must preserve the actual upstream body and audio')
    g = geometry(raw['source_voice_endpoint_seconds'], raw['body_frames'], raw['illustration_start_frame'],
                 raw['summary_start_frame'], raw['output_frames'], raw['delay_after_voice_seconds'])
    require(g['speech_ceiling_frame'] == 4720 and raw_up['source_voice_endpoint_seconds'] == raw['source_voice_endpoint_seconds'] == 157.33,
            'Actual narration endpoint changed')
    for held in (raw, raw['output_preview_hold_validation']):
        decoded_hold(frame_count=held['preview_last_body_hold_frames'], hold_seconds=held['preview_last_body_hold_seconds'],
                     start_frame=held['preview_hold_start_frame'], end_frame_inclusive=held['preview_hold_end_frame_inclusive'],
                     reference_frame=held['preview_frozen_reference_frame'], checked_frames=held['preview_actual_held_frames_checked'],
                     thumbnail_mae_each=held['preview_hold_thumbnail_MAE_each'], thumbnail_mae_max=held['preview_hold_thumbnail_MAE_max'], actual_geometry=g)
    require(raw['illustration_frames'] == raw['summary_frames'] == raw['illustration_frames_checked'] == raw['summary_frames_checked'] == 60
            and raw['illustration_max_thumbnail_mean_absolute_error'] < 2 and raw['summary_max_thumbnail_mean_absolute_error'] < 2,
            'Actual complete120 approved tail pixels must pass')
    layout_path = checked(prior['global_approved_evidence']['video_layout_approval'])
    layout = next(r for r in D.load(layout_path)['articles'] if r['source_id'] == '28')
    require(raw['approved_summary_rgb_sha256'] == layout['summary_rgb_sha256']
            and raw['source_script_layout_binding']['approved_full_source_sha256'] == layout['source_json_sha256']
            and raw['source_script_layout_binding']['approved_ordered_layout_sha256'] == layout['source_layout_structural_sha256'],
            'Source, approved card or layout changed during postprocessing')
    require(raw['approved_illustration_sha256'] == old_qc['illustration']['approved_illustration_sha256']
            and raw['illustration_composed_4k_rgb_sha256'] == old_qc['illustration']['preparation']['prepared_rgb_sha256'],
            'Approved illustration pixels changed')
    preparation = raw['illustration_preparation']
    checked({'path': preparation['prepared_image_path'], 'bytes': Path(preparation['prepared_image_path']).stat().st_size,
             'sha256': preparation['prepared_png_sha256']})
    frozen = module(helper)
    require(frozen.rgb_sha(preparation['prepared_image_path']) == preparation['prepared_rgb_sha256'], 'Actual prepared RGB differs')
    actual_hold = frozen.verify_preview_hold(final, raw['body_frames'])
    require(actual_hold == raw['output_preview_hold_validation'], 'Actual independent18-frame decode differs')
    audios = [D.actual_aac(p) for p in (source, upstream, final)]
    require(audios[0] == audios[1] == audios[2] and audios[0]['packet_count'] == 7469
            and audios[0]['aac_adts_sha256'] == '82898283b5f5c55b84912f8838ebdfed1a337300db09de759fc55a3eb389ddd2',
            'Actual original→held18→final AAC payload/codec/side-data/absolute clock differs')
    probe = D.probe(final)
    require((probe['width'], probe['height'], probe['frames']) == (3840,2160,4858) and probe['fps'] in ('30/1','60/2'), 'Actual4K30fps output differs')
    review_path = TAIL / 'actual-seven-frame-boundary-review.json'
    review = D.load(review_path)
    require(review.get('actually_visually_reviewed') is True and review['video_sha256'] == raw['video_sha256'], 'Actual visual review required')
    for row in raw['decoded_frame_previews']:
        require(D.digest(row['path']) == row['sha256'], 'Actual decoded boundary bytes differ')
    if not write:
        return {'passed': True, 'geometry': g}
    OUT.mkdir(parents=True, exist_ok=True)
    bridge_path = OUT / 'actual18-existing-composition-bridge.json'
    if not bridge_path.exists():
        build_bridge(Path('/workspace/work/video-revision-delivery/native-preview28-engine-candidate-20261114-v1/preview28-original-composition-dc204.py'), helper, PROGRAM_SHA, bridge_path)
    audio_summary = [{k:v for k,v in a.items() if k != 'projection'} for a in audios]
    report = {'status':'passed_actual_post_only_hold18_preview28','source_run':43576642418,
              'actual_new_native_job_or_TTS_or_body_production_claimed':False,
              'prior_full_V3_handoff':spec(PRIOR),'actual_mp4':spec(final),'actual_geometry':g,
              'actual_probe':probe,'actual_AAC_original_held18_final':audio_summary,
              'actual_raw_hold18_proof':spec(report_path),'actual_seven_frame_review':spec(review_path),
              'preview_only':True,'preview_delivery_eligible':True,'production_delivery_eligible':False,
              'final_user_acceptance':False,'active_final_replacement_authorized':False,
              'full_source_GEN_MD_layout_and_native_voice_QA_inherited_unchanged':True,
              'audio_repair_applied_in_this_postprocess':False,'raw_original_upstream_and_status_preserved':True,
              'scope':'Only18 cloned last-body frames and relocation of approved art/card. Original raw report retains legacy source label; the adapter explicitly binds the real435766 input SHA and inherited quality. No fresh native quality run is claimed.'}
    D.write(OUT/'report.json',report)
    snapshot=OUT/'code-snapshot';snapshot.mkdir(exist_ok=True)
    tools=[Path(__file__),HERE/'hold18_geometry.py',HERE/'build_actual_composition_bridge.py',BASE/'delivery.py',BASE/'release_contract.py',helper,H/'hold18-preview/preview28_hold18.py',H/'hold18-preview/produce28_hold18_upstream.py']
    hashes={}
    for p in tools:
        name=p.name if p!=helper else 'actual_hold18_illustrated_tail.py';target=snapshot/name;shutil.copyfile(p,target);hashes[name]=D.digest(target)
    new_qc=copy.deepcopy(old_qc)
    new_qc.update(video_sha256=D.digest(final),video_bytes=final.stat().st_size,actual_probe=probe,
                  local_postprocessing_only=True,new_native_quality_run_claimed=False,
                  inherited_full_V3_handoff=spec(PRIOR),local_hold18_validation=report)
    new_qc['speech_end'].update(end_frame=g['speech_ceiling_frame'],endpoint_seconds=157.33)
    new_qc['preview_hold']={'start_frame':4720,'end_frame_exclusive':4738,'frames':18,
                            'frozen_reference_frame':4719,'raw_hold_validation':actual_hold}
    new_qc['body_end']={'end_frame_exclusive':4738,'includes_eighteen_frame_preview_hold':True}
    new_qc['illustration'].update(start_frame=4738,preparation=preparation)
    new_qc['illustration']['frame_comparison'].update(start_frame=4738,video_sha256=D.digest(final),report_sha256=D.digest(report_path))
    new_qc['summary'].update(start_frame=4798)
    new_qc['audio']['lossless_copy'].update(final_video_sha256=D.digest(final),
          final_aac_adts_sha256=audios[2]['aac_adts_sha256'],
          final_packet_projection_sha256=audios[2]['packet_projection_sha256'],final_packet_count=7469)
    D.write(OUT/'28-current-local-postprocess-QC.json',new_qc)
    item=copy.deepcopy(original['section']);item['mp4']=spec(final);item['qc']=spec(OUT/'28-current-local-postprocess-QC.json')
    item['local_hold18_postprocessing']={'actual_source_run':43576642418,'original_native_final_unchanged':original['preview_mp4'],'report':spec(OUT/'report.json'),'new_native_job_claimed':False}
    D.write(OUT/'actual-sample-input.json',{'kind':'post-only18-preview-inheriting-real-full-V3','articles':[item],'prior_full_V3':spec(PRIOR)})
    record=copy.deepcopy(old_record);record.update(bytes=final.stat().st_size,sha256=D.digest(final),qc=new_qc,preview_only=True,preview_passed=True,passed_per_article=False,production_delivery_eligible=False,normal70_final_assembly_eligible=False,local_hold18_postprocessing=report)
    D.write(OUT/'validated-article-record.json',record)
    extra=[POLICY,report_path,review_path,bridge_path,*UP.glob('*.json'),*UP.glob('*.py'),H/'hold18-preview/preview28_hold18.py',H/'hold18-preview/produce28_hold18_upstream.py',*TAIL.glob('*.json'),*TAIL.glob('*.py'),*TAIL.glob('*.png'),*TAIL.glob('actual-boundary-previews/*.jpg'),*(HERE/name for name in ('actual28-post-only-hold18-validation.log','actual28-post-only-hold18-validation-2.log','actual28-post-only-hold18-validation-3.log'))]
    extras={str(p.resolve()):p for p in extra if p.is_file()}
    validation=[{**r,'relative_validation_path':'prior-preview0.3/'+r['relative_validation_path']} for r in prior['validation_files']]
    validation += [{**spec(p),'relative_validation_path':'actual-hold18-evidence/'+str(i)+'-'+p.name}for i,p in enumerate(extras.values())]
    validation += [{**spec(p),'relative_validation_path':str(p.relative_to(OUT))}for p in OUT.rglob('*')if p.is_file() and p.name!='preview-handoff.json']
    hand={'status':'passed_actual_post_only_hold18_preview28_for_user_review_only','kind':'source28-book29-hold18-user-review-preview','source_run':43576642418,
          'local_postprocessing_only':True,'new_native_job_or_TTS_claimed':False,'preview_only':True,'preview_delivery_eligible':True,'production_delivery_eligible':False,
          'final_user_acceptance':False,'active_final_replacement_authorized':False,'complete70_release_validated':False,'normal70_final_assembly_eligible':False,
          'publishing_or_remote_mutation_executed':False,'prior_full_V3':spec(PRIOR),'native_root':prior['native_root'],
          'articles':[{'source_id':'28','new_id':'29','preview_passed':True,'passed_per_article':False,'preview_only':True,'production_delivery_eligible':False,'final_user_acceptance':False,
                       'preview_mp4':spec(final),'canonical_source_mp4':original['canonical_source_mp4'],'immutable_native_zip':original['immutable_native_zip'],
                       'validated_record':str(OUT/'validated-article-record.json'),'section':item}],
          'report_path':str(OUT/'report.json'),'input_path':str(OUT/'actual-sample-input.json'),'validation_files':validation,
          'global_approved_evidence':prior['global_approved_evidence'],'tool_source_sha256':hashes,'code_snapshot_path':str(snapshot)}
    D.write(OUT/'preview-handoff.json',hand)
    print(json.dumps({'status':hand['status'],'handoff':spec(OUT/'preview-handoff.json')},ensure_ascii=False))
    return report


if __name__ == '__main__':
    validate()
