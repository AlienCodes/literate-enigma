"""Geometry for the user's18-frame hold; no producer/report ABI is assumed.

Callers must map fields from the actual frozen producer report explicitly.
This never renders media, changes audio, or declares a delivery accepted.
"""
import math
from fractions import Fraction


def require(value, message):
    if not value:
        raise ValueError(message)


def geometry(endpoint_seconds, body_end_frame, illustration_start_frame,
             summary_start_frame, output_frames, delay_after_voice_seconds):
    require(type(endpoint_seconds) in (int, float) and math.isfinite(endpoint_seconds)
            and endpoint_seconds > 0, 'Real finite measured voice endpoint required')
    values = (body_end_frame, illustration_start_frame, summary_start_frame, output_frames)
    require(all(type(v) is int for v in values), 'Actual integer frame indices required')
    endpoint = Fraction(str(endpoint_seconds))
    ceiling = math.ceil(endpoint * 30)
    require(body_end_frame == ceiling + 18, 'Exactly18 held last-body frames required')
    require(illustration_start_frame == body_end_frame
            and summary_start_frame == body_end_frame + 60
            and output_frames == body_end_frame + 120,
            'Tail must be held body18 then approved illustration60 then summary60')
    gap = Fraction(body_end_frame, 30) - endpoint
    require(Fraction(18, 30) <= gap < Fraction(19, 30), 'Voice-to-picture gap outside0.6s ceiling hold')
    require(type(delay_after_voice_seconds) in (int, float)
            and math.isfinite(delay_after_voice_seconds)
            and abs(delay_after_voice_seconds - float(gap)) < 1e-9,
            'Reported voice delay differs from actual measured endpoint/frame indices')
    return {'speech_ceiling_frame': ceiling, 'hold_start_frame': ceiling,
            'hold_end_frame_inclusive': body_end_frame - 1,
            'held_body_end_frame_exclusive': body_end_frame,
            'frozen_reference_frame': ceiling - 1, 'extra_body_frames': 18,
            'voice_to_picture_seconds': float(gap)}


def decoded_hold(*, frame_count, hold_seconds, start_frame, end_frame_inclusive,
                 reference_frame, checked_frames, thumbnail_mae_each,
                 thumbnail_mae_max, actual_geometry):
    expected = (frame_count, start_frame, end_frame_inclusive, reference_frame, checked_frames)
    require(all(type(v) is int for v in expected), 'Actual integer hold decoder indices required')
    require(frame_count == checked_frames == 18 and hold_seconds == .6,
            'All18 actual held frames must be decoded and compared')
    require(start_frame == actual_geometry['hold_start_frame']
            and end_frame_inclusive == actual_geometry['hold_end_frame_inclusive']
            and reference_frame == actual_geometry['frozen_reference_frame'],
            'Hold is not compared with the final spoken-page frame')
    require(isinstance(thumbnail_mae_each, list) and len(thumbnail_mae_each) == 18
            and all(type(v) in (int, float) and math.isfinite(v) and 0 <= v < 2
                    for v in thumbnail_mae_each)
            and thumbnail_mae_max == max(thumbnail_mae_each),
            'Actual18 held-page comparisons failed the unchanged MAE<2 rule')


def eligibility(*, preview_only, production_delivery_eligible,
                preview_delivery_eligible=None, active_final_replacement_authorized=None,
                final_user_acceptance=None):
    require(type(preview_only) is bool, 'Explicit actual preview/final mode required')
    if preview_only:
        require(preview_delivery_eligible is True and production_delivery_eligible is False
                and active_final_replacement_authorized is False
                and final_user_acceptance is False,
                'Preview acceptance cannot authorize final replacement or user acceptance')
    else:
        require(production_delivery_eligible is True,
                'Normal delivery needs actual production eligibility')
