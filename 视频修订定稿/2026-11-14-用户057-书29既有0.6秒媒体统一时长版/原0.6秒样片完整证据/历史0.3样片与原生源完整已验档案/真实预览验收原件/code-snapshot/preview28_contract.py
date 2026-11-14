"""Exact frozen source28/book29 review variant. Never renders or publishes media.

The normal engine remains the default. These adapters only describe the real
F28 preview ABI; technical preview acceptance never authorizes replacing a final.
"""
import hashlib
import json
import math
import shutil
from pathlib import Path

import delivery as D

HERE = Path(__file__).resolve().parent
HEAD = 'b91467310c4043008d0c55220b0d1844ec67ba30'
RUN = 43576642418
LAYOUT_SHA = '35acd87bcbd994c98951bddd5c83c54f24c35283808bcb76e3da4b20612f0894'
SOURCE_SHA = 'e0c8e6c644ab0c5d52d99c23461b99e9ae1574aa574369e56feb35e2ac20698b'
HELPER_SHA = 'f90e399b59ec5d1c7bc83a9d8c4c0134b7ba4dbe1627a2bde6ab91daa6c06562'
COMPOSITION_SHA = 'dc204b91415e28297b844e9666087b0e23e67194944b359cb5fb5ddbca0f1208'
BRIDGE_SHA = '3d9d13332c3a10855a4cd2ce5155f6ef677c7c2e42f15307d56d991dd45806e1'
ACCEPTED_AAC = '82898283b5f5c55b84912f8838ebdfed1a337300db09de759fc55a3eb389ddd2'
AAC_COUNT = 7469
UPSTREAM_KIND = 'preview-last-body-hold9-then-summary60'
FINAL_KIND = 'preview-last-body-hold9-then-approved-book-illustration60-then-approved-summary60'
def require(*args):
    return D.require(*args)


def load(*args):
    return D.load(*args)


def checked_file(*args):
    return D.checked_file(*args)


def is_preview(value):
    return value.get('preview_only') is True


def flags(value, article='28'):
    require(article == '28' and str(value.get('article', article)).zfill(2) == '28',
            'Preview adapter is only source28/book29')
    require(value.get('preview_only') is True and value.get('preview_delivery_eligible') is True
            and value.get('production_delivery_eligible') is False,
            'Real preview eligibility required; production final is not this variant')


def main_status(value, article='28'):
    flags(value, article)
    require(value.get('passed') is True and value.get('stage') == 'preview4K-passed'
            and value.get('canonical_pipeline_passed') is True,
            'Actual frozen F28 preview status required')
    require(value.get('active_final_replacement_authorized') is False,
            'Preview may not replace the active final')
    require(type(value.get('preview_last_body_hold_frames')) is int
            and value['preview_last_body_hold_frames'] == 9,
            'Exact integer nine-frame preview required')
    require(value.get('first_tail_page') == 'illustration'
            and value.get('illustration_frames') == value.get('summary_frames') == 60,
            'Actual preview illustration60 and summary60 required')


def geometry(value):
    endpoint = value['source_voice_endpoint_seconds']
    require(isinstance(endpoint, (int, float)) and not isinstance(endpoint, bool)
            and math.isfinite(endpoint) and endpoint > 0, 'Actual source voice endpoint required')
    ceiling = math.ceil(endpoint * 30 - .000001)
    end = value['body_frames']
    require(type(end) is int and end == ceiling + 9, 'Body must end exactly nine frames after speech ceiling')
    require(value['illustration_start_frame'] == end
            and value['summary_start_frame'] == end + 60
            and value['output_frames'] == end + 120,
            'Preview must be held body then illustration60 then summary60')
    require(abs(value['illustration_start_seconds'] - end / 30) < 1e-9
            and abs(value['summary_start_seconds'] - (end + 60) / 30) < 1e-9
            and abs(value['output_seconds'] - (end + 120) / 30) < 1e-9,
            'Actual preview times must match original 30fps frame indices')
    gap = end / 30 - endpoint
    require(9 / 30 <= gap < 10 / 30 + .000001
            and abs(value['delay_after_voice_seconds'] - gap) < 1e-9,
            'Preview gap must be the exact nine-frame ceiling hold')
    return ceiling, end


def hold_validation(value, ceiling, end):
    expected = {'preview_last_body_hold_frames': 9,
                'preview_hold_start_frame': ceiling,
                'preview_hold_end_frame_inclusive': end - 1,
                'preview_frozen_reference_frame': ceiling - 1,
                'preview_actual_held_frames_checked': 9}
    require(all(type(value.get(k)) is int and value[k] == v for k, v in expected.items()),
            'Actual all-nine decoded hold frame identities differ')
    require(value.get('preview_last_body_hold_seconds') == .3, 'Exact nine-frame duration required')
    errors = value.get('preview_hold_thumbnail_MAE_each')
    require(isinstance(errors, list) and len(errors) == 9
            and all(isinstance(x, (int, float)) and math.isfinite(x) and 0 <= x < 2 for x in errors)
            and value.get('preview_hold_thumbnail_MAE_max') == max(errors),
            'Actual nine-frame continuity must retain the existing MAE bound')


def proof(value, article='28'):
    flags(value, article)
    require(value.get('passed') is True and value.get('kind') == FINAL_KIND
            and value.get('source_kind') == 'new-canonical-4K'
            and value.get('postprocessor_sha256') == HELPER_SHA,
            'Genuine frozen new-canonical preview proof required')
    ceiling, end = geometry(value)
    hold_validation(value, ceiling, end)
    hold_validation(value['output_preview_hold_validation'], ceiling, end)
    return ceiling, end


def copy_proof(value, final_proof):
    ceiling, end = proof(final_proof)
    require(value.get('article') == '28' and value.get('kind') == UPSTREAM_KIND
            and value.get('preview_only') is True
            and type(value.get('preview_last_body_hold_frames')) is int
            and value['preview_last_body_hold_frames'] == 9,
            'Actual upstream hold9 end-card proof required')
    require(value.get('unheld_voice_ceiling_frame') == ceiling
            and value.get('held_body_reference_frame') == ceiling - 1
            and value.get('summary_start_frame') == end
            and value.get('source_voice_endpoint_seconds') == final_proof['source_voice_endpoint_seconds'],
            'Upstream actual speech ceiling and held body differ')
    require(value.get('source_kind') == 'new-canonical-4K'
            and value.get('canonical_pipeline_passed') is True
            and value.get('original_audio_identical') is True
            and value.get('original_audio_packet_timings_identical') is True
            and value.get('final_canonical_aac_identical') is True
            and value.get('accepted_prior_aac_identical') is True
            and value.get('canonical_aac_adts_sha256') == ACCEPTED_AAC
            and value.get('end_page_frames') == 60 and value.get('end_page_seconds') == 2,
            'Original complete voice and exact accepted AAC copy must remain passed')


def layout_reference(article, explicit, output):
    require(article == '28' and explicit['sha256'] == LAYOUT_SHA, 'Exact immutable native-head28 layout required')
    source = checked_file(explicit)
    remote = load(HERE / 'actual-preview28-layout-immutable-read.json')
    require(remote['ref'] == HEAD and remote['sha256'] == LAYOUT_SHA
            and remote['working_CI_used_as_reference'] is False,
            'Layout must come from the actual immutable native head GET')
    rows = load(source)
    row = next(r for r in rows['articles'] if r['source_id'] == '28')
    require(row['new_id'] == '29' and row['source_json_sha256'] == SOURCE_SHA,
            'Actual frozen28 render source/order differs')
    target = Path(output) / '28' / 'approved-video-layouts70-frozen.json'
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        require(D.digest(target) == LAYOUT_SHA, 'Existing frozen28 preview layout differs')
    else:
        shutil.copyfile(source, target)
    return {'path': str(target), 'bytes': target.stat().st_size, 'sha256': LAYOUT_SHA}


def preparation_bridge(qc, preparation, composition_program):
    flags(qc)
    require(composition_program == COMPOSITION_SHA and preparation['preparer_program_sha256'] == HELPER_SHA,
            'Only frozen dc204 composition to f90 preview bridge is authorized')
    require(D.digest(HERE / 'preview28-composition-compatibility.json') == BRIDGE_SHA, 'Frozen composition bridge report changed')
    bridge = load(HERE / 'preview28-composition-compatibility.json')
    require(bridge['source_id'] == '28' and bridge['book_order'] == '29'
            and bridge['original_composition_program_sha256'] == COMPOSITION_SHA
            and bridge['new_preview_preparer_sha256'] == HELPER_SHA
            and len(bridge['actual_function_comparisons']) == 15
            and all(r['AST_identical'] is True for r in bridge['actual_function_comparisons']),
            'Frozen original pixel-algorithm compatibility evidence differs')
    require(D.digest(HERE / 'preview28-original-composition-dc204.py') == COMPOSITION_SHA
            and D.digest(HERE / 'preview28-frozen-illustrated-tail.py') == HELPER_SHA,
            'Frozen original/new helper bytes differ')


def adapt_qc(qc, raw, upstream_copy):
    ceiling, end = proof(raw, qc['article'])
    copy_proof(upstream_copy, raw)
    qc.update(status='passed', preview_only=True, preview_delivery_eligible=True,
              production_delivery_eligible=False, active_final_replacement_authorized=False,
              final_user_acceptance=False)
    qc['speech_end'].update(end_frame=ceiling, endpoint_seconds=raw['source_voice_endpoint_seconds'])
    qc['preview_hold'] = {'start_frame': ceiling, 'end_frame_exclusive': end, 'frames': 9,
                          'frozen_reference_frame': ceiling - 1,
                          'raw_hold_validation': raw['output_preview_hold_validation']}
    qc['body_end'] = {'end_frame_exclusive': end, 'includes_nine_frame_preview_hold': True}
    qc['adapter_scope'] += ' Exact28 preview only: measured speech ceiling and held body end remain distinct; no production/final eligibility.'


def validate_qc_scope(qc, run):
    flags(qc)
    require(qc.get('final_user_acceptance') is False and qc.get('active_final_replacement_authorized') is False
            and run['run_id'] == RUN and run['head_sha'] == HEAD,
            'Preview belongs to the exact frozen F28 native run and cannot replace a final')
    require(qc['source_sha256']['request']['json'] == SOURCE_SHA,
            'Preview request is not frozen source28')


def ensure_no_production_release(config):
    require(not is_preview(config), 'Preview28 cannot enter normal70 final validation/staging')
    for row in config.get('articles', []):
        require(not is_preview(row), 'Preview component cannot enter normal70 final validation/staging')
        qc = load(checked_file(row['qc']))
        require(not is_preview(qc), 'Preview28 cannot enter normal70 final validation/staging')


def preview_record(record):
    record.update(preview_only=True, preview_delivery_eligible=True,
                  production_delivery_eligible=False, final_user_acceptance=False,
                  active_final_replacement_authorized=False,
                  normal70_final_assembly_eligible=False)
    return record


def finalize(a):
    """Called after the unchanged actual five-boundary identity review."""
    from import_actual_article import import_one, spec
    root, out = Path(a.native_root).resolve(), Path(a.output_root).resolve()
    prepared = load(root / 'prepared-inline-section.json')
    require(a.article.zfill(2) == '28' and is_preview(prepared), 'Only real prepared28 preview is accepted')
    import_one(root, '28', out)
    review = load(a.boundary_review)
    D.write(out / '28' / 'actual-boundary-frame-review.json', review)
    config = load(out / 'actual-sample-input.json')
    item = config['articles'][0]
    record = load(out / '28' / 'validated-article-record.json')
    context = load(root / 'inline-adapter-context.json')
    require(record['sha256'] == context['original_native_final_sha256'] == prepared['final']['sha256'],
            'Actual preview original bytes differ')
    require(record['preview_only'] is True and record['production_delivery_eligible'] is False,
            'Preview validation may not become a production final')
    snapshot = out / 'code-snapshot'
    snapshot.mkdir(exist_ok=True)
    names = ['delivery.py', 'release_contract.py', 'derive_final_generator.py',
             'validate_actual_samples.py', 'ingest_passed_article.py', 'import_actual_article.py',
             'validate_section.py', 'request_source_inputs.py', 'ingest_inline_article.py',
             'ingest_recover_missing_illustration.py', 'preview28_contract.py',
             'preview28-composition-compatibility.json', 'actual-preview28-layout-immutable-read.json',
             'approved-video-layouts70-frozen-preview28.json',
             'preview28-original-composition-dc204.py', 'preview28-frozen-illustrated-tail.py']
    hashes = {}
    for name in names:
        shutil.copyfile(HERE / name, snapshot / name)
        hashes[name] = D.digest(snapshot / name)
    D.write(snapshot / 'snapshot-manifest.json', {'scope': 'Exact28 preview-only intake; no media rendering or new acoustic audit', 'sha256': hashes})
    handoff = {'status': 'passed_actual_native_preview28_for_user_review_only',
               'kind': 'source28-book29-hold9-user-review-preview',
               'preview_only': True, 'preview_delivery_eligible': True,
               'production_delivery_eligible': False, 'active_final_replacement_authorized': False,
               'final_user_acceptance': False,
               'complete70_release_validated': False, 'normal70_final_assembly_eligible': False,
               'publishing_or_remote_mutation_executed': False,
               'native_inline_preview_original_bytes_preserved': True,
               'source_run': record['qc']['official_run']['run_id'], 'native_root': str(root),
               'articles': [{'source_id': '28', 'new_id': '29', 'preview_passed': True,
                             'passed_per_article': False, 'production_delivery_eligible': False,
                             'preview_only': True, 'final_user_acceptance': False,
                             'preview_mp4': item['mp4'], 'canonical_source_mp4': item['canonical_mp4'],
                             'immutable_native_zip': record['qc']['official_run']['artifact_zip'],
                             'validated_record': str(out / '28' / 'validated-article-record.json'), 'section': item}],
               'report_path': str(out / 'report.json'), 'input_path': str(out / 'actual-sample-input.json'),
               'tool_source_sha256': hashes, 'code_snapshot_path': str(snapshot),
               'global_approved_evidence': {k: config[k] for k in ('book_illustrations', 'illustration_composition_review', 'illustration_crop_review', 'video_layout_approval')},
               'validation_files': [{**spec(p), 'relative_validation_path': str(p.relative_to(out))}
                                    for p in sorted(out.rglob('*')) if p.is_file() and p.name != 'preview-handoff.json']}
    D.write(out / 'preview-handoff.json', handoff)
    print(json.dumps({'article': '28', 'status': handoff['status'], 'preview_handoff': str(out / 'preview-handoff.json')}, ensure_ascii=False))


def actual_illustrated_tail_report(qc,run,evidence,status_sha,layout_row,book_row):
    fingerprint=qc['illustration']['frame_comparison']['report_sha256']
    raw=load(checked_file(next(e for e in evidence if e['sha256']==fingerprint)))
    native_input=run['artifact_native_final_sha256']if run['canonical_selection']=='native_pre_card'else run['artifact_mp4_sha256']
    proof(raw, qc['article'])
    require(raw['article']==qc['article']==book_row['source_id']and raw['book_new_id']==book_row['new_id']and raw['input_video_sha256']==native_input and raw['upstream_status_sha256']==status_sha and raw['video_sha256']==qc['video_sha256'],'Actual tail report belongs to different media/native source')
    require(raw['body_reencoded_frames']==raw['audio_reencoded_or_added_packets']==0 and raw['body_coded_pictures_identical']is True and raw['body_packet_timings_identical']is True and raw['aac_packet_payload_and_absolute_timings_identical']is True,'Actual tail processing changed body pictures or audio')
    require(raw['body_frames']==raw['illustration_start_frame']==qc['preview_hold']['end_frame_exclusive']==qc['speech_end']['end_frame']+9 and raw['summary_start_frame']==qc['summary']['start_frame']and raw['output_frames']==qc['actual_probe']['frames'],'Actual tail frame counts/timeline differ')
    require(raw['illustration_frames_checked']==raw['summary_frames_checked']==raw['illustration_frames']==raw['summary_frames']==60 and raw['illustration_max_thumbnail_mean_absolute_error']<2 and raw['summary_max_thumbnail_mean_absolute_error']<2,'Actual full120 tail-frame pixel comparisons failed')
    require(9/30<=raw['delay_after_voice_seconds']<10/30+.000001 and abs(raw['illustration_start_seconds']-raw['source_voice_endpoint_seconds']-raw['delay_after_voice_seconds'])<1e-9,'Preview tail does not start after the exact nine-frame speech-ceiling hold')
    require(raw['illustration_preparation']==qc['illustration']['preparation']and raw['approved_illustration_sha256']==book_row['sha256'],'Actual preparation/native image identity differs')
    require(layout_row['source_id']==qc['article']and layout_row['new_id']==book_row['new_id']and raw['approved_summary_rgb_sha256']==layout_row['summary_rgb_sha256']and qc['summary']['font_px']==layout_row['summary_font_4k_px']and qc['summary']['approved_request_text_sha256']==layout_row['approved_summary_text_sha256'],'Actual card differs from current approved article/layout/text')
    binding=raw['source_script_layout_binding']
    require(binding['actual_request_source_sha256']==qc['source_sha256']['request']['json'] and binding['approved_full_source_sha256']==layout_row['source_json_sha256']and binding['approved_ordered_layout_sha256']==layout_row['source_layout_structural_sha256'],'Actual approved layout and exact render request differ')
    return raw


def tail_contract(qc,illustration,stills,evidence_hashes,book_row):
    flags(qc)
    speech=qc['speech_end'];art=qc['illustration'];summary=qc['summary'];total=qc['actual_probe']['frames']
    require(speech['actual_new_output']is True and speech['measured_from_actual_audio']is True and speech['report_sha256']in evidence_hashes,'Actual narration-end evidence required')
    require(type(speech['end_frame'])is int and speech['end_frame']>0,'Actual speech-end frame required')
    require(math.ceil(speech['endpoint_seconds']*30-.000001)==speech['end_frame'],'Measured voice endpoint differs from its ceiling')
    held=qc['preview_hold'];start=held['end_frame_exclusive']
    require(type(start)is int and held['start_frame']==speech['end_frame']and type(held['frames'])is int and held['frames']==9 and start==speech['end_frame']+9,'Exact preview hold geometry required')
    hold_validation(held['raw_hold_validation'],speech['end_frame'],start)
    require(qc['article']==illustration['source_id']==book_row['source_id'] and illustration['new_id']==book_row['new_id'],'Illustration belongs to a different article/book-order entry')
    require(illustration['approved']is True and illustration['book_source_sha256']==book_row['sha256'],'Illustration does not match this exact article in the frozen approved book map')
    require(art['decoded_from_actual_mp4']is True and art['frames']==60 and art['start_frame']==start,'Preview illustration must follow the exact nine held body frames for60 frames')
    require((art['width'],art['height'])==(3840,2160)and art['approved_illustration_sha256']==book_row['sha256']and art['book_source_sha256']==illustration['book_source_sha256'],'Actual4K illustration/native source SHA mismatch')
    compare=art['frame_comparison'];require(compare['status']=='passed'and compare['actual_new_output']is True and compare['decoded_from_actual_mp4']is True and compare['frames_checked']==60 and compare['start_frame']==start and compare['video_sha256']==qc['video_sha256']and compare['reference_sha256']==illustration['sha256']and compare['report_sha256']in evidence_hashes,'Actual60-frame illustration comparison report required')
    require(summary['decoded_from_actual_mp4']is True and summary['frames']==60 and summary['start_frame']==start+60 and summary['start_frame']+60==total,'Tail must be speech→60 illustration→60 summary→end')
    require({s['kind']for s in stills}>={'body_end','illustration','summary'},'Actual body/illustration/card stills required')
    for s in stills:
        if s['kind']=='body_end':require(0<=s['frame']<start,'Body still after speech end')
        if s['kind']=='illustration':require(start<=s['frame']<start+60,'Illustration still outside actual illustration interval')
        if s['kind']=='summary':require(start+60<=s['frame']<total,'Summary still outside final card')
    return {'speech_end_frame':speech['end_frame'],'held_body_end_frame':start,'preview_only':True,'illustration_frames':60,'summary_frames':60,'approved_illustration_sha256':illustration['sha256']}
