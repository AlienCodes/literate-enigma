"""Normal18-frame contract fragment, awaiting actual frozen producer mappings.

Does not guess a kind, helper SHA, run, artifact or acceptance outcome. Callers
must supply those exact values observed from the real producer and new output.
"""
from copy import deepcopy
from pathlib import Path
import hashlib

from hold18_geometry import geometry, decoded_hold, eligibility, require


def actual_normal_tail(raw, *, article, new_id, expected_kind, expected_program_sha,
                       actual_hold, layout_row, book_row, request_json_sha256):
    require(len(expected_program_sha) == 64 and expected_kind, 'Real frozen normal18 ABI required')
    require(raw['article'] == article and raw['book_new_id'] == new_id
            and raw['kind'] == expected_kind and raw['postprocessor_sha256'] == expected_program_sha,
            'Actual normal18 producer/program/article identity differs')
    require(raw['passed'] is True and raw['source_kind'] == 'new-canonical-4K'
            and raw.get('preview_only') is False, 'Real quality-passed normal output required')
    require(article == '19' and new_id == '38'
            and raw.get('single_article_review_authorization_sha256') == '99720ce104ace96339178f37e1d0378966e1da43227505e18a88983ca59c0ab7'
            and raw.get('single_article_review_book_order') == '38'
            and raw.get('single_article_review_source_id') == '19'
            and raw.get('specific_authorization_id') == '109'
            and raw.get('finalization_authorized') is True
            and raw.get('last_body_hold_frames') == 18
            and raw.get('final_hold_policy_sha256') == '4bcae46b68b9584f107966f683af580b474fa9835f101834fe55ed6968dfc36b',
            'Actual authorized normal18 mode/policy required; a preview cannot be promoted')
    eligibility(preview_only=False, production_delivery_eligible=raw['production_delivery_eligible'])
    require(raw['body_reencoded_frames'] == raw['audio_reencoded_or_added_packets'] == 0
            and raw['body_coded_pictures_identical'] is True
            and raw['body_packet_timings_identical'] is True
            and raw['body_codec_and_display_parameters_identical'] is True
            and raw['audio_codec_parameters_identical'] is True
            and raw['aac_packet_payload_and_absolute_timings_identical'] is True,
            'Actual normal postprocessor changed its verified upstream body/audio')
    g = geometry(raw['source_voice_endpoint_seconds'], raw['body_frames'], raw['illustration_start_frame'],
                 raw['summary_start_frame'], raw['output_frames'], raw['delay_after_voice_seconds'])
    decoded_hold(actual_geometry=g, **actual_hold)
    require(raw['closed_idr_boundary_verified'] is True, 'Original closed-IDR requirement remains')
    require(raw['illustration_frames'] == raw['summary_frames'] == raw['illustration_frames_checked']
            == raw['summary_frames_checked'] == 60
            and raw['illustration_max_thumbnail_mean_absolute_error'] < 2
            and raw['summary_max_thumbnail_mean_absolute_error'] < 2,
            'All120 actual approved tail pixels must pass unchanged bounds')
    require(layout_row['source_id'] == book_row['source_id'] == article
            and layout_row['new_id'] == book_row['new_id'] == new_id,
            'Book order/source mapping differs')
    require(raw['approved_illustration_sha256'] == book_row['sha256']
            and raw['approved_summary_rgb_sha256'] == layout_row['summary_rgb_sha256'],
            'Actual illustration or summary differs from the current approved pixels')
    binding = raw['source_script_layout_binding']
    require(binding['actual_request_source_sha256'] == request_json_sha256
            and binding['approved_full_source_sha256'] == layout_row['source_json_sha256']
            and binding['approved_ordered_layout_sha256'] == layout_row['source_layout_structural_sha256'],
            'Actual requested body/layout binding differs')
    return g


def current_stills(decoded_rows, *, video_sha256, held_body_end, output_frames):
    """Build from actual new decoded frames; never inherit an old preview's stills."""
    labels = ['body-last','illustration-first','illustration-last','summary-first','summary-last']
    expected_frames = [held_body_end-1,held_body_end,held_body_end+59,held_body_end+60,output_frames-1]
    require([r['label'] for r in decoded_rows] == labels
            and [r['frame'] for r in decoded_rows] == expected_frames,
            'Actual current five-boundary identities differ')
    result = []
    for r in decoded_rows:
        p=Path(r['path']);require(hashlib.sha256(p.read_bytes()).hexdigest()==r['sha256'], 'Actual still bytes differ')
        kind='body_end' if r['label']=='body-last' else 'illustration' if r['label'].startswith('illustration') else 'summary'
        result.append({'path':str(p),'bytes':p.stat().st_size,'sha256':r['sha256'],
                       'kind':kind,'frame':r['frame'],'video_sha256':video_sha256,'decoded_from_actual_mp4':True})
    return result


def fresh_derived_record(prior, *, mp4_spec, actual_probe, current_qc, actual_audio_chain, actual_geometry):
    """Explicit current identity and named inherited QA, with no stale top-level fields."""
    require(current_qc['video_sha256']==mp4_spec['sha256'] and current_qc['video_bytes']==mp4_spec['bytes']
            and current_qc['actual_probe']==actual_probe, 'Current media identity/probe/QC disagree')
    require(actual_probe['frames']==actual_geometry['held_body_end_frame_exclusive']+120
            and (actual_probe['width'],actual_probe['height'])==(3840,2160), 'Current probe/tail disagree')
    return {'id':prior['id'],'new_id':prior['new_id'],'canonical_path':prior['canonical_path'],
            'reordered_path':prior['reordered_path'],'sha256':mp4_spec['sha256'],'bytes':mp4_spec['bytes'],
            'actual_probe':deepcopy(actual_probe),'qc':deepcopy(current_qc),
            'canonical_video_sha256':prior['canonical_video_sha256'],
            'canonical_video_bytes':prior['canonical_video_bytes'],
            'actual_audio_chain':deepcopy(actual_audio_chain),
            'source_invariants':deepcopy(prior['source_invariants']),
            'audio_repaired':prior['audio_repaired'],
            'canonical_audio_acceptance_basis':prior['canonical_audio_acceptance_basis'],
            'illustration':deepcopy(prior['illustration']),
            'tail':{'speech_end_frame':actual_geometry['speech_ceiling_frame'],
                    'held_body_end_frame':actual_geometry['held_body_end_frame_exclusive'],
                    'extra_body_hold_frames':18,'illustration_frames':60,'summary_frames':60,
                    'illustration_start_frame':actual_geometry['held_body_end_frame_exclusive'],
                    'summary_start_frame':actual_geometry['held_body_end_frame_exclusive']+60,
                    'output_frames':actual_probe['frames'],
                    'voice_endpoint_seconds':current_qc['speech_end']['endpoint_seconds'],
                    'voice_to_illustration_gap_seconds':actual_geometry['voice_to_picture_seconds']},
            'inherited_original_probe':deepcopy(prior['actual_probe']),
            'inherited_original_tail':deepcopy(prior['tail']),
            'preview_only':False,'production_delivery_eligible':True}
