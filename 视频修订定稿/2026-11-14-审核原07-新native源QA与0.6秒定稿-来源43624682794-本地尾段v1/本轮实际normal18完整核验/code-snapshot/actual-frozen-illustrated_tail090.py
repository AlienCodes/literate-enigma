#!/usr/bin/env python3
"""Losslessly retain a verified NEW body/AAC, then show approved art60 + summary60.

Only accepts this batch's passed new-canonical summary delivery (or an explicitly
labelled, non-deliverable validation fixture). A closed IDR at the existing summary
start is mandatory: this helper never re-encodes, freezes, crops or erases body video.
The original official maker and acceptance programs are not imported or modified.
"""
import argparse
from fractions import Fraction
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from PIL import Image, ImageChops, ImageFilter, ImageOps, ImageStat, __version__ as PILLOW_VERSION

FPS = 30
PAGE_FRAMES = 60
SIZE = (3840, 2160)
THUMB = (384, 216)
FINAL_HOLD18_POLICY_SHA256 = '4bcae46b68b9584f107966f683af580b474fa9835f101834fe55ed6968dfc36b'
FINAL_HOLD18_SOURCE_IDS = frozenset(('14','27','13','26','15','17','36','33','47','34','62'))
# Explicit review-only top-level keys. The pinned official render.py never reads
# either key (including apply_script/layout/size); no gain, timing or content key
# is omitted. JSON key order and all remaining data stay part of the digest.
REVIEW_ONLY_TOP_LEVEL_KEYS = ('核对确认', '区间声音指纹')


def run(args, *, capture=False):
    return subprocess.run([str(x) for x in args], check=True,
                          stdout=subprocess.PIPE if capture else None,
                          stderr=subprocess.PIPE if capture else None).stdout


def digest_bytes(value):
    return hashlib.sha256(value).hexdigest()


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1048576), b''):
            h.update(block)
    return h.hexdigest()


def probe(path):
    return json.loads(run(['ffprobe', '-v', 'error', '-show_streams', '-show_format',
                           '-of', 'json', path], capture=True))


def packets(path, stream, payload=False):
    args = ['ffprobe', '-v', 'error', '-select_streams', stream, '-show_packets']
    if payload:
        args += ['-show_data_hash', 'sha256']
    args += ['-show_entries', 'packet=pts,dts,duration,pts_time,dts_time,duration_time,flags,size'
             + (',data_hash:packet_side_data' if payload else ''), '-of', 'json', path]
    return json.loads(run(args, capture=True))['packets']


def packet_timing(rows):
    keys = ('pts', 'dts', 'duration', 'pts_time', 'dts_time', 'duration_time', 'flags')
    return [{key: row[key] for key in keys if key in row} for row in rows]


def coded_pictures_sha(path, count):
    return digest_bytes(run(['ffmpeg', '-v', 'error', '-i', path, '-map', '0:v:0', '-an',
                             '-c:v', 'copy', '-frames:v', count, '-bsf:v',
                             'h264_mp4toannexb,filter_units=pass_types=1-5',
                             '-f', 'h264', '-'], capture=True))


def boundary_is_idr(path, seconds):
    annexb = run(['ffmpeg','-v','error','-ss',f'{seconds:.9f}','-i',path,
                  '-map','0:v:0','-an','-c:v','copy','-frames:v','1',
                  '-bsf:v','h264_mp4toannexb','-f','h264','-'],capture=True)
    types = [unit[0] & 31 for unit in re.split(b'\x00\x00(?:\x00)?\x01',annexb) if unit]
    pictures = [kind for kind in types if 1 <= kind <= 5]
    return bool(pictures) and pictures[0] == 5


def aac_sha(path):
    return digest_bytes(run(['ffmpeg', '-v', 'error', '-i', path, '-map', '0:a:0',
                             '-vn', '-c:a', 'copy', '-f', 'adts', '-'], capture=True))


def rgb_sha(path):
    with Image.open(path) as picture:
        assert picture.size == SIZE, (path, picture.size, SIZE)
        return digest_bytes(picture.convert('RGB').tobytes())


def source_layout_digest(data):
    stripped = {key:value for key,value in data.items() if key not in REVIEW_ONLY_TOP_LEVEL_KEYS}
    return digest_bytes(json.dumps(stripped, ensure_ascii=False, separators=(',',':')).encode())


def source_layout_binding(path, source_id, status, approved):
    assert path is not None, 'Attach the exact newly requested source script.'
    raw_sha = sha(path)
    assert status['request_source_sha256'][f'视频/脚本/{source_id}.json'] == raw_sha, 'Source does not match the new canonical production request.'
    data = json.loads(path.read_text())
    assert str(data['no']).zfill(2) == source_id
    method = 'identical_full_source_sha256'
    if raw_sha != approved['source_json_sha256']:
        assert source_layout_digest(data) == approved['source_layout_structural_sha256'], (
            'Current request differs from approved layout outside the two explicit review-only keys.')
        method = 'all_ordered_json_identical_except_explicit_review_only_top_level_keys'
    return {'method':method, 'actual_request_source_sha256':raw_sha,
            'approved_full_source_sha256':approved['source_json_sha256'],
            'approved_ordered_layout_sha256':approved['source_layout_structural_sha256'],
            'permitted_review_only_top_level_keys':list(REVIEW_ONLY_TOP_LEVEL_KEYS)}


def approved_inputs(args):
    manifest = json.loads(args.illustration_manifest.read_text())
    order_bytes = args.order_manifest.read_bytes()
    assert digest_bytes(order_bytes) == manifest['order_source_manifest_sha256'], 'Book order manifest SHA differs.'
    rows = manifest['illustrations']
    assert manifest['count'] == len(rows) == 70
    assert {r['source_id'] for r in rows} == {f'{n:02d}' for n in range(1, 71)}
    assert [r['new_id'] for r in rows] == [f'{n:02d}' for n in range(1, 71)]
    row = next(r for r in rows if r['source_id'] == args.source_id)
    assert sha(args.illustration) == row['sha256'], 'Wrong or changed approved book illustration.'
    with Image.open(args.illustration) as im:
        assert list(im.size) == row['native_pixel_dimensions']
    review = json.loads(args.crop_review.read_text())
    assert review['illustration_manifest_sha256'] == sha(args.illustration_manifest)
    choice = next(r for r in review['articles'] if r['source_id'] == args.source_id)
    assert choice['source_image_sha256'] == row['sha256'] and choice['actually_visually_reviewed'] is True
    assert choice['review_state'] == 'approved_composition'
    assert choice['new_id'] == row['new_id']
    layouts = json.loads(args.layout_approval.read_text())
    assert layouts['passed'] is True and layouts['count'] == 70
    approved = next(r for r in layouts['articles'] if r['source_id'] == args.source_id)
    assert approved['new_id'] == row['new_id'], 'Approved layout and book order do not match.'
    assert rgb_sha(args.summary_image) == approved['summary_rgb_sha256'], 'Summary is not the approved current4K card.'
    return row, choice, approved


def compose_illustration(source, choice, destination):
    """Only resize/crop the approved art; risk cases retain the complete sharp image."""
    with Image.open(source) as raw:
        image = raw.convert('RGB')
    if choice['mode'] == 'cover':
        box = tuple(choice['source_crop_box'])
        assert len(box) == 4 and 0 <= box[0] < box[2] <= image.width and 0 <= box[1] < box[3] <= image.height
        assert Fraction(box[2] - box[0], box[3] - box[1]) == Fraction(*SIZE)
        result = image.crop(box).resize(SIZE, Image.Resampling.LANCZOS)
    elif choice['mode'] == 'contain_blur':
        assert choice.get('source_crop_box') in (None, [0, 0, image.width, image.height])
        result = ImageOps.fit(image, SIZE, method=Image.Resampling.LANCZOS).filter(ImageFilter.GaussianBlur(64))
        foreground = ImageOps.contain(image, SIZE, method=Image.Resampling.LANCZOS)
        result.paste(foreground, ((SIZE[0] - foreground.width) // 2, (SIZE[1] - foreground.height) // 2))
    else:
        raise ValueError('Unreviewed composition mode: ' + str(choice['mode']))
    result.save(destination)


def preview_hold_contract(args, timing, body_frames=None):
    """The only new branch: explicit article28, exactly18frames, review-only."""
    hold = getattr(args, 'preview_last_body_hold_frames', 0)
    assert type(hold) is int and hold in (0, 18), 'Only default0 or explicitly authorized18 hold frames are supported.'
    if hold == 0:
        if not args.validation_fixture:
            assert not timing.get('preview_only', False) and not timing.get('preview_last_body_hold_frames', 0), 'Preview metadata requires the explicit article28 hold18 CLI.'
        if body_frames is not None:
            seconds = body_frames / FPS
            assert 0 <= seconds - float(timing['source_voice_endpoint_seconds']) < 1/FPS + .000001
        return False
    assert args.source_id == '28', 'Eighteen-frame trial is authorized only for source28/book29.'
    assert not args.validation_fixture, 'Preview acceptance requires actual new-canonical production provenance; synthetic fixtures are never preview deliveries.'
    assert timing.get('kind') == 'preview-last-body-hold18-then-summary60', 'Wrong upstream preview stage kind.'
    assert timing.get('preview_only') is True and type(timing.get('preview_last_body_hold_frames')) is int and timing['preview_last_body_hold_frames'] == 18, 'Missing exact preview-only hold18 declaration.'
    if body_frames is not None:
        endpoint = float(timing['source_voice_endpoint_seconds'])
        gap = body_frames / FPS - endpoint
        assert 18/FPS <= gap < 19/FPS + .000001, 'Voice-to-illustration gap is not the authorized18-frame ceiling hold.'
        ceiling = __import__('math').ceil(endpoint * FPS - .000001)
        assert body_frames == ceiling + 18, 'Hold must start after the actual measured speech ceiling and last exactly18frames.'
    return True


def verify_preview_hold(video, body_frames):
    """Inspect the18 actual decoded hold frames against the final spoken-page frame.

    The same existing <2 thumbnail MAE bound as static pages accommodates H264
    chroma/rounding. All original body coded pictures/timing stay independently exact.
    """
    freeze_frame = body_frames - 19
    assert freeze_frame >= 0
    raw = run(['ffmpeg','-v','error','-ss',f'{max(0,(freeze_frame-.25)/FPS):.9f}',
               '-i',video,'-map','0:v:0','-an','-frames:v','19',
               '-vf','scale=384:216:flags=area','-pix_fmt','rgb24','-f','rawvideo','-'],capture=True)
    stride = THUMB[0] * THUMB[1] * 3
    assert len(raw) == 19 * stride, 'Could not inspect final spoken-page frame plus all18 held frames.'
    reference = Image.frombytes('RGB', THUMB, raw[:stride])
    errors = [sum(ImageStat.Stat(ImageChops.difference(reference, Image.frombytes('RGB', THUMB, raw[i*stride:(i+1)*stride]))).mean)/3 for i in range(1,19)]
    assert max(errors) < 2, ('Preview held body page changed.', errors)
    return {'preview_last_body_hold_frames':18, 'preview_last_body_hold_seconds':18/FPS,
            'preview_hold_start_frame':body_frames-18, 'preview_hold_end_frame_inclusive':body_frames-1,
            'preview_frozen_reference_frame':freeze_frame, 'preview_actual_held_frames_checked':18,
            'preview_hold_thumbnail_MAE_each':errors, 'preview_hold_thumbnail_MAE_max':max(errors),
            'preview_hold_visual_reference':'actual decoded last spoken-page frame before18-frame hold; existing static-page MAE<2 rule'}


def final_hold_contract(args, timing, body_frames=None):
    """Explicit final18 mode; the policy never grants final approval to other articles."""
    hold = getattr(args, 'final_last_body_hold_frames', 0)
    preview = getattr(args, 'preview_last_body_hold_frames', 0)
    policy = getattr(args, 'final_hold_policy', None)
    assert type(hold) is int and hold in (0,18), 'Only default0 or exactly18 final hold frames are supported.'
    assert not (hold and preview), 'Final and preview hold modes are mutually exclusive.'
    if getattr(args, 'single_article_review_authorization', None) is not None:
        assert hold == 18, 'A specific article final authorization requires exactly18 final frames.'
    if hold == 0:
        assert policy is None, 'A final hold policy requires explicit final18 mode.'
        assert timing.get('kind') != 'last-body-hold18-then-summary60' and not timing.get('last_body_hold_frames',0), 'Final hold metadata requires explicit final18 mode.'
        return False
    if getattr(args, 'single_article_review_authorization', None) is not None:
        assert sha(args.single_article_review_authorization) == '3120efc6893981436cb81458ce57f6aca7601edc5e7326cce1388b68de959001', 'Wrong specific article finalization authorization.'
        assert args.source_id == '07' and str(args.single_article_book_order).zfill(2) == '03', 'Only user090 quality-book03/source07.'
    else:
        raise AssertionError('User090 quality-book03/source07 requires its exact specific finalization authorization.')
    assert not args.validation_fixture, 'Final delivery requires actual passed native quality provenance.'
    assert policy is not None and sha(policy) == FINAL_HOLD18_POLICY_SHA256, 'Wrong or missing approved final hold policy.'
    assert timing.get('kind') == 'last-body-hold18-then-summary60', 'Wrong normal-final upstream kind; a preview cannot be promoted.'
    assert timing.get('finalization_authorized') is True, 'Missing explicit finalization authorization.'
    assert timing.get('preview_only') is False, 'A preview cannot be promoted to final delivery.'
    assert type(timing.get('last_body_hold_frames')) is int and timing['last_body_hold_frames'] == 18, 'Missing exact final18 declaration.'
    assert type(timing.get('preview_last_body_hold_frames',0)) is int and timing.get('preview_last_body_hold_frames',0) == 0, 'Preview declarations cannot enter final mode.'
    if body_frames is not None:
        endpoint = Fraction(str(timing['source_voice_endpoint_seconds']))
        gap = Fraction(body_frames,FPS) - endpoint
        assert Fraction(18,FPS) <= gap < Fraction(19,FPS), 'Voice-to-illustration gap is outside the exact18-frame ceiling hold.'
        ceiling = __import__('math').ceil(endpoint * FPS)
        assert body_frames == ceiling + 18, 'Final hold must start after measured speech ceiling and last exactly18frames.'
    return True


def verify_final_hold(video, body_frames):
    """Run the identical actual19-frame decode and pixel check without preview labels."""
    checked = verify_preview_hold(video, body_frames)
    return {key.removeprefix('preview_'): value for key,value in checked.items()}


def provenance(args, source_sha, approved):
    timing = json.loads(args.verification.read_text())
    assert str(timing['article']).zfill(2) == args.source_id
    assert timing['video_sha256'] == source_sha, 'Input MP4 does not match its passed verification.'
    is_final = final_hold_contract(args, timing)
    is_preview = False if is_final else preview_hold_contract(args, timing)
    if args.validation_fixture:
        assert timing.get('synthetic_validation_fixture') is True
        assert timing.get('source_kind') == 'synthetic-validation-only'
        return timing, None, {'method':'synthetic_only_not_production_source_acceptance'}
    assert timing.get('source_kind') == 'new-canonical-4K', 'Historical accepted/failed sources are forbidden.'
    expected_kind = 'last-body-hold18-then-summary60' if is_final else ('preview-last-body-hold18-then-summary60' if is_preview else 'immediate-standalone-summary')
    assert timing.get('kind') == expected_kind, 'Input is not the verified new two-second summary stage.'
    assert timing.get('canonical_pipeline_passed') is True
    assert timing.get('original_audio_identical') is True
    assert timing.get('original_audio_packet_timings_identical') is True
    assert args.status is not None
    status = json.loads(args.status.read_text())
    assert status.get('passed') is True and status.get('canonical_pipeline_passed') is True
    assert status.get('stage') == 'final4K-passed'
    assert str(status['article']).zfill(2) == args.source_id and status['video_sha256'] == source_sha
    assert status['canonical_video_sha256'] == timing['canonical_source_video_sha256']
    assert status['temporary_output_reset']['production_started_ns'] > 0, 'Missing fresh-production provenance.'
    assert timing['end_page_frames'] == 60 and timing['end_page_seconds'] == 2
    binding = source_layout_binding(args.source_script, args.source_id, status, approved)
    return timing, status, binding


def verify_static_pages(video, start_frame, illustration, summary):
    # Quarter-frame early seek avoids decimal rounding onto the following frame.
    raw = run(['ffmpeg', '-v', 'error', '-ss', f'{(start_frame-.25)/FPS:.9f}', '-i', video,
               '-map', '0:v:0', '-an', '-frames:v', 120, '-vf', 'scale=384:216:flags=area',
               '-pix_fmt', 'rgb24', '-f', 'rawvideo', '-'], capture=True)
    stride = THUMB[0] * THUMB[1] * 3
    assert len(raw) == stride * 120, 'Unable to inspect all120 tail frames.'
    # Reference the intended UNCOMPRESSED yuv420p raster. Comparing a PIL RGB
    # box-resize with ffmpeg's YUV area-resize otherwise counts normal chroma
    # conversion/resampling as H264 errors, especially in detailed paintings.
    refs=[]
    for path in (illustration,summary):
        reference=run(['ffmpeg','-v','error','-i',path,'-frames:v','1',
                       '-vf','format=yuv420p,scale=384:216:flags=area','-pix_fmt','rgb24',
                       '-f','rawvideo','-'],capture=True)
        assert len(reference)==stride
        refs.append(Image.frombytes('RGB',THUMB,reference))
    errors = [[], []]
    for frame in range(120):
        picture = Image.frombytes('RGB', THUMB, raw[frame*stride:(frame+1)*stride])
        errors[frame // 60].append(sum(ImageStat.Stat(ImageChops.difference(picture, refs[frame // 60])).mean) / 3)
    assert max(errors[0]) < 2 and max(errors[1]) < 2, ('Tail frame/reference mismatch.', max(errors[0]), max(errors[1]))
    return {'illustration_frames_checked': 60, 'summary_frames_checked': 60,
            'visual_reference':'uncompressed intended yuv420p raster; matching ffmpeg area resampling',
            'illustration_max_thumbnail_mean_absolute_error': max(errors[0]),
            'summary_max_thumbnail_mean_absolute_error': max(errors[1])}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--source-id', required=True)
    for name in ['input', 'verification', 'illustration-manifest', 'order-manifest', 'crop-review',
                 'illustration', 'summary-image', 'layout-approval', 'output', 'report']:
        ap.add_argument('--' + name, type=Path, required=True)
    ap.add_argument('--status', type=Path)
    ap.add_argument('--source-script', type=Path)
    ap.add_argument('--work', type=Path)
    ap.add_argument('--preview-dir', type=Path)
    ap.add_argument('--prepared-illustration-output', type=Path)
    ap.add_argument('--plan-only', action='store_true')
    ap.add_argument('--overwrite', action='store_true')
    ap.add_argument('--validation-fixture', action='store_true')
    ap.add_argument('--preview-last-body-hold-frames', type=int, default=0, help='Only source28 authorized review variant: exactly18frames after actual final speech; default0 retains original contract.')
    ap.add_argument('--final-last-body-hold-frames', type=int, default=0, help='Only explicitly finalized articles: exactly18frames after measured final speech, bound to policy051.')
    ap.add_argument('--final-hold-policy', type=Path)
    ap.add_argument('--single-article-review-authorization', type=Path)
    ap.add_argument('--single-article-book-order')
    args = ap.parse_args(); args.source_id = args.source_id.zfill(2)
    assert PILLOW_VERSION == '12.3.0', 'Use the approved Pillow12.3.0 production environment.'
    assert args.input.resolve() != args.output.resolve(), 'Write a separate new output; retain the verified input.'
    args.report.parent.mkdir(parents=True, exist_ok=True)
    result = {'article': args.source_id, 'passed': False, 'production_delivery_eligible': False,
              'postprocessor_sha256':sha(Path(__file__)),
              'kind': 'approved-book-illustration60-then-approved-summary60', 'body_reencoded_frames': 0,
              'audio_reencoded_or_added_packets': 0, 'official_maker_or_acceptance_modified': False}
    try:
        image_row, choice, approved = approved_inputs(args)
        source_sha = sha(args.input); timing, status, binding = provenance(args, source_sha, approved)
        info = probe(args.input); vs = next(s for s in info['streams'] if s['codec_type'] == 'video')
        au = next(s for s in info['streams'] if s['codec_type'] == 'audio')
        assert vs['codec_name'] == 'h264' and (vs['width'], vs['height']) == SIZE and Fraction(vs['r_frame_rate']) == FPS
        assert au['codec_name'] == 'aac'
        before_v = packets(args.input, 'v:0'); before_a = packets(args.input, 'a:0', payload=True)
        body_frames = int(timing['summary_start_frame']); body_seconds = body_frames / FPS
        assert body_frames > 0 and len(before_v) == body_frames + PAGE_FRAMES
        is_final = final_hold_contract(args, timing, body_frames)
        is_preview = False if is_final else preview_hold_contract(args, timing, body_frames)
        assert 'K' in before_v[body_frames]['flags'], 'Body boundary is not a closed IDR: rerun only the NEW end-card stage with a forced keyframe; no silent body re-encode.'
        assert round(float(before_v[body_frames]['pts_time']) * FPS) == body_frames
        assert boundary_is_idr(args.input,body_seconds), 'The summary keyframe is not an H.264 IDR; no silent body re-encode.'
        assert max(float(p['pts_time']) for p in before_v[:body_frames]) < body_seconds
        result.update({'input_video_sha256': source_sha, 'upstream_verification_sha256': sha(args.verification),
                       'upstream_status_sha256': sha(args.status) if args.status else None,
                       'source_script_layout_binding':binding,
                       'source_kind': timing['source_kind'], 'canonical_source_video_sha256': timing.get('canonical_source_video_sha256'),
                       'book_new_id': image_row['new_id'], 'illustration_manifest_sha256': sha(args.illustration_manifest),
                       'book_order_manifest_sha256': sha(args.order_manifest), 'approved_illustration_sha256': image_row['sha256'],
                       'approved_summary_rgb_sha256': approved['summary_rgb_sha256'], 'composition': choice,
                       'body_frames': body_frames, 'illustration_start_frame': body_frames,
                       'summary_start_frame': body_frames+60, 'illustration_frames': 60, 'summary_frames': 60,
                       'illustration_start_seconds':body_seconds,'summary_start_seconds':body_seconds+2,
                       'source_voice_endpoint_seconds':timing['source_voice_endpoint_seconds'],
                       'delay_after_voice_seconds':body_seconds-float(timing['source_voice_endpoint_seconds']),
                       'illustration_seconds': 2, 'summary_seconds': 2, 'closed_idr_boundary_verified': True})
        if is_preview:
            result.update({'preview_only':True,'preview_delivery_eligible':False,'production_delivery_eligible':False,'kind':'preview-last-body-hold18-then-approved-book-illustration60-then-approved-summary60'})
            result.update(verify_preview_hold(args.input,body_frames))
        if is_final:
            result.update({'preview_only':False,'finalization_authorized':True,'kind':'last-body-hold18-then-approved-book-illustration60-then-approved-summary60','final_hold_policy_sha256':sha(args.final_hold_policy)})
            result.update(verify_final_hold(args.input,body_frames))
            if args.single_article_review_authorization is not None:
                result.update(single_article_review_authorization_sha256=sha(args.single_article_review_authorization), single_article_review_book_order='03', single_article_review_source_id='07', specific_authorization_id='090', requested_video_order='01', frozen_quality_book_order='03')
        if args.plan_only:
            result['plan_passed'] = True
            args.report.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
            print(json.dumps(result, ensure_ascii=False)); return
        assert args.overwrite or not args.output.exists(), 'Output exists; use an explicit new path or --overwrite.'
        args.output.parent.mkdir(parents=True, exist_ok=True)
        if args.work: args.work.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix='illustrated-tail-', dir=args.work) as temporary:
            tmp = Path(temporary); art = tmp/'approved-illustration-4K.png'; prefix = tmp/'body-prefix.mp4'; tail = tmp/'static-tail.mp4'; joined = tmp/'joined.mp4'
            compose_illustration(args.illustration, choice, art)
            timescale = Fraction(vs['time_base']).denominator
            run(['ffmpeg','-v','error','-y','-copyts','-i',args.input,'-map','0:v:0','-an','-c:v','copy',
                 '-frames:v',body_frames,'-avoid_negative_ts','disabled','-video_track_timescale',timescale,prefix])
            graph = '[0:v]trim=end_frame=60,setpts=PTS-STARTPTS,setsar=1[a];[1:v]trim=end_frame=60,setpts=PTS-STARTPTS,setsar=1[b];[a][b]concat=n=2:v=1:a=0,format=yuv420p[out]'
            run(['ffmpeg','-v','error','-y','-loop','1','-framerate','30','-i',art,'-loop','1','-framerate','30','-i',args.summary_image,
                 '-filter_complex',graph,'-map','[out]','-an','-frames:v','120','-r','30','-fps_mode','cfr',
                 '-c:v','libx264','-preset','fast','-crf','10','-threads','2','-g','60','-keyint_min','60','-sc_threshold','0',
                 '-force_key_frames','0,2','-pix_fmt','yuv420p','-profile:v','high','-level:v','5.1','-video_track_timescale',timescale,tail])
            concat = tmp/'tail.ffconcat'; concat.write_text("ffconcat version 1.0\nfile 'body-prefix.mp4'\nduration " + f'{body_seconds:.9f}' + "\nfile 'static-tail.mp4'\n")
            run(['ffmpeg','-v','error','-y','-copyts','-f','concat','-safe','0','-i',concat,'-i',args.input,
                 '-map','0:v:0','-map','1:a:0','-c','copy','-avoid_negative_ts','disabled','-video_track_timescale',timescale,'-movflags','+faststart',joined])
            for attempt in range(3):
                after_v = packets(joined, 'v:0'); delta = float(after_v[0]['pts_time']) - float(before_v[0]['pts_time'])
                if abs(delta) < .00001: break
                fixed = tmp/f'timing-fixed-{attempt}.mp4'
                run(['ffmpeg','-v','error','-y','-copyts','-itsoffset',f'{-delta:.9f}','-i',joined,'-i',args.input,
                     '-map','0:v:0','-map','1:a:0','-c','copy','-avoid_negative_ts','disabled','-video_track_timescale',timescale,'-movflags','+faststart',fixed])
                os.replace(fixed, joined)
            after_v = packets(joined,'v:0'); after_a = packets(joined,'a:0',payload=True)
            assert len(after_v) == body_frames + 120
            assert packet_timing(after_v[:body_frames]) == packet_timing(before_v[:body_frames]), 'Body packet timing changed.'
            old_coded = coded_pictures_sha(args.input, body_frames); new_coded = coded_pictures_sha(joined, body_frames)
            assert old_coded == new_coded, 'Body coded pictures changed.'
            assert before_a == after_a, 'AAC packet payload, side data, or absolute timing changed.'
            old_aac = aac_sha(args.input); assert aac_sha(joined) == old_aac
            pts = sorted(float(p['pts_time']) for p in after_v)
            assert all(abs(t-i/FPS)<.000002 for i,t in enumerate(pts)), 'Video frame gap or duplicate timestamp.'
            out_info = probe(joined); out_v = next(s for s in out_info['streams'] if s['codec_type']=='video'); out_a = next(s for s in out_info['streams'] if s['codec_type']=='audio')
            assert (out_v['width'], out_v['height']) == SIZE and Fraction(out_v['r_frame_rate']) == FPS
            assert abs(float(out_v['duration']) - (body_seconds+4)) < .00001
            video_parameters=['codec_name','profile','level','width','height','pix_fmt','sample_aspect_ratio',
                              'color_range','color_space','color_transfer','color_primaries','chroma_location','time_base']
            audio_parameters=['codec_name','profile','sample_rate','channels','channel_layout','sample_fmt','time_base']
            assert {k:vs.get(k) for k in video_parameters} == {k:out_v.get(k) for k in video_parameters}, 'Body codec/display parameters changed.'
            assert {k:au.get(k) for k in audio_parameters} == {k:out_a.get(k) for k in audio_parameters}, 'Audio codec parameters changed.'
            page_checks = verify_static_pages(joined, body_frames, art, args.summary_image)
            result.update(page_checks)
            # A normal final remains ineligible until its output18 frames pass too.
            final_output_hold_validation = verify_final_hold(joined,body_frames) if is_final else None
            result.update({'passed':True,'production_delivery_eligible':not args.validation_fixture and not is_preview,
                           'source_kind':'new-canonical-4K' if not args.validation_fixture else 'synthetic-validation-only',
                           'output_frames':len(after_v),'output_seconds':body_seconds+4,
                           'body_coded_pictures_identical':True,'body_packet_timings_identical':True,
                           'body_codec_and_display_parameters_identical':True,'audio_codec_parameters_identical':True,
                           'body_coded_pictures_sha256':old_coded,'aac_packet_payload_and_absolute_timings_identical':True,
                           'aac_packet_count':len(before_a),'aac_adts_sha256':old_aac,
                           'audio_packet_records_sha256':digest_bytes(json.dumps(before_a,sort_keys=True,separators=(',',':')).encode()),
                           'illustration_composed_4k_rgb_sha256':rgb_sha(art),'video_sha256':sha(joined)})
            if is_preview:
                result.update({'preview_only':True,'preview_delivery_eligible':True,'production_delivery_eligible':False})
                result['output_preview_hold_validation'] = verify_preview_hold(joined,body_frames)
            if is_final:
                result.update({'preview_only':False,'finalization_authorized':True,'production_delivery_eligible':True})
                result['output_final_hold_validation'] = final_output_hold_validation
            result['illustration_preparation'] = {
                'source_id':args.source_id, 'new_id':image_row['new_id'],
                'native_image_sha256':image_row['sha256'],
                'native_pixel_dimensions':image_row['native_pixel_dimensions'],
                'prepared_png_sha256':sha(art), 'prepared_rgb_sha256':rgb_sha(art),
                'prepared_pixel_dimensions':list(SIZE), 'mode':choice['mode'],
                'Pillow':PILLOW_VERSION,
                'native_source_crop_box':choice['source_crop_box'],
                'resampling':'Pillow Image.Resampling.LANCZOS',
                'same_image_background_gaussian_blur_radius':64 if choice['mode']=='contain_blur' else None,
                'derived_in_this_process_from_exact_approved_native_image':True,
                'generated_or_substituted_artwork':False, 'added_text_or_graphics':False,
                'preparer_program_sha256':sha(Path(__file__))}
            if args.prepared_illustration_output:
                destination=args.prepared_illustration_output
                assert destination.resolve() not in (args.illustration.resolve(), args.summary_image.resolve(), args.input.resolve(), args.output.resolve())
                assert args.overwrite or not destination.exists()
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(art,destination)
                result['illustration_preparation']['prepared_image_path']=str(destination)
            if args.preview_dir:
                args.preview_dir.mkdir(parents=True,exist_ok=True)
                names=[('body-last',body_frames-1),('illustration-first',body_frames),
                       ('illustration-last',body_frames+59),('summary-first',body_frames+60),
                       ('summary-last',body_frames+119)]
                result['decoded_frame_previews']=[]
                for label,frame in names:
                    destination=args.preview_dir/f'{args.source_id}-{label}.jpg'
                    run(['ffmpeg','-v','error','-y','-ss',f'{max(0,(frame-.25)/FPS):.9f}',
                         '-i',joined,'-frames:v','1','-vf','scale=1920:1080','-q:v','2',destination])
                    result['decoded_frame_previews'].append({'frame':frame,'label':label,
                                                            'path':str(destination),'sha256':sha(destination)})
            os.replace(joined, args.output)
        args.report.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
        print(json.dumps(result,ensure_ascii=False))
    except Exception as error:
        if getattr(args,'final_last_body_hold_frames',0) == 18:
            result.update({'passed':False,'production_delivery_eligible':False})
        result['error'] = str(error)
        args.report.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
        raise


if __name__ == '__main__':
    main()
