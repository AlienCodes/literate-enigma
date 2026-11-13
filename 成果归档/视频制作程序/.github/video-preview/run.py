#!/usr/bin/env python3
"""Replace the original silent end hold with an immediate two-second summary."""
import argparse
import array
import ast
import copy
from fractions import Fraction
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[2]
TASK = ROOT / '.github/video-preview'
BASE = 'c9d52b26fe981ef8e4c412189ca289716ab8bf00'
OUT = ROOT / 'completion-output'


def command(args, **kw):
    return subprocess.run([str(x) for x in args], check=True, **kw)


def get(args):
    return command(args, capture_output=True, text=True).stdout


def materialize(paths):
    command(['git', 'sparse-checkout', 'add', '--stdin'], cwd=ROOT,
            input=''.join('/' + p + '\n' for p in paths), text=True)


def tree_paths():
    return get(['git', '-c', 'core.quotepath=off', 'ls-tree', '-rz', '--name-only', BASE]).split('\0')


def summary(no):
    data = json.loads((TASK / 'summaries.json').read_text())[no]
    assert len(data) == 5 and all(len(x) == 2 and all(x) for x in data)
    return '（简述：' + ''.join('▸' + label + '：' + body for label, body in data) + '）'


def add_summary(data, no):
    d = copy.deepcopy(data)
    c = d['sentences'][-1]['chunks'][-1]
    old = c.get('note') or ''
    assert '（简述：' not in old, 'Already has a summary; do not overwrite it.'
    c['note'] = (old + '\n' if old else '') + summary(no)
    check = copy.deepcopy(d)
    if 'note' in data['sentences'][-1]['chunks'][-1]:
        check['sentences'][-1]['chunks'][-1]['note'] = data['sentences'][-1]['chunks'][-1]['note']
    else:
        check['sentences'][-1]['chunks'][-1].pop('note')
    assert check == data, 'A field outside the final note changed.'
    return d


def probe(p):
    return json.loads(get(['ffprobe', '-v', 'error', '-show_streams', '-show_format', '-of', 'json', p]))


def packet_times(path, stream):
    return json.loads(get(['ffprobe', '-v', 'error', '-select_streams', stream, '-show_packets',
                          '-show_entries', 'packet=pts_time,dts_time,duration_time,flags',
                          '-of', 'json', path]))['packets']


def coded_frames_hash(path, count):
    args = ['ffmpeg', '-v', 'error', '-i', path, '-map', '0:v:0', '-an', '-c:v', 'copy',
            '-frames:v', str(count), '-bsf:v', 'h264_mp4toannexb,filter_units=pass_types=1-5',
            '-f', 'h264', '-']
    return hashlib.sha256(command(args, capture_output=True).stdout).hexdigest()


def voice_end(path, video_seconds):
    # Inspect the existing audio; never synthesize, trim or re-encode the voice.
    pcm = array.array('f', command(['ffmpeg', '-v', 'error', '-i', path, '-map', '0:a:0',
                                  '-ac', '1', '-ar', '48000', '-f', 'f32le', '-'],
                                 capture_output=True).stdout)
    hop = 240  # 5 ms RMS windows, including the quiet final consonant/decay.
    start = max(0, len(pcm) // hop - 1000)
    ends = {}
    for threshold in (-60, -70, -80):
        audible = [i for i in range(start, len(pcm) // hop)
                   if sum(v * v for v in pcm[i * hop:(i + 1) * hop]) / hop > 10 ** (threshold / 10)]
        assert audible, 'No speech detected near the end.'
        ends[str(threshold)] = (audible[-1] + 1) * hop / 48000
    assert abs(ends['-80'] - ends['-70']) < .06, 'Uncertain voice endpoint; inspect rather than guess.'
    end = max(ends.values())
    assert 1.5 < video_seconds - end < 2.5, 'Unexpected original end hold.'
    return end, ends


def audio_hash(p):
    return get(['ffmpeg', '-v', 'error', '-i', p, '-map', '0:a:0', '-vn',
                '-c:a', 'pcm_s16le', '-f', 'hash', '-hash', 'sha256', '-']).strip()


def render_card(no, data, width, height, destination):
    os.environ['VIDEO_S'] = '2' if width == 3840 else '1'
    spec = importlib.util.spec_from_file_location('completion_render', ROOT / '视频/工具/render.py')
    renderer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(renderer)
    renderer.F = str(ROOT / '视频/工具/fonts') + '/'
    theme_tree = ast.parse((ROOT / '视频/工具/make_video.py').read_text())
    theme_node = next(node.value for node in theme_tree.body if isinstance(node, ast.Assign)
                      and any(isinstance(t, ast.Name) and t.id == 'T' for t in node.targets)
                      and isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Name)
                      and node.value.func.id == 'dict' and any(k.arg == 'BG_TOP' for k in node.value.keywords))
    theme = {k.arg: ast.literal_eval(k.value) for k in theme_node.keywords}
    for key, value in theme.items():
        setattr(renderer, key, value)
    assert (renderer.W, renderer.H) == (width, height)
    renderer.apply_script(data)
    text = summary(no)
    size, lines, first = renderer.简述排(text)
    font, bold = renderer.ZH(size, 400), renderer.ZH(size, 700)
    indent = font.getlength('• ')
    max_width = max(sum((bold if b else font).getlength(ch) for ch, b in line)
                    + (0 if i in first else indent) for i, line in enumerate(lines))
    assert len(first) == 5 and max_width <= width * .92 + 1
    assert len(lines) * size * 1.5 <= (height - 8 * renderer.S) * .9 + 1
    renderer.frame_简述(text, 1, str(destination))
    return {'font_px': size, 'lines': len(lines), 'items': len(first), 'max_text_width': max_width}


def end_card(no):
    paths = tree_paths()
    originals = [p for p in paths if p.startswith('最终版4K视频/' + no + ' - ') and p.endswith('.mp4')]
    assert len(originals) == 1, (no, originals)
    selected = ['视频/工具/render.py', '视频/工具/make_video.py', '视频/工具/fonts']
    materialize(selected)
    source = OUT / f'{no}-original.mp4'
    with source.open('wb') as f:
        command(['git', 'show', BASE + ':' + originals[0]], stdout=f)
    data = json.loads(get(['git', 'show', BASE + f':视频/脚本/{no}.json']))
    changed = add_summary(data, no)
    info = probe(source)
    vs = next(s for s in info['streams'] if s['codec_type'] == 'video')
    assert vs['codec_name'] == 'h264' and (vs['width'], vs['height']) == (3840, 2160)
    card = OUT / f'{no}-简述.png'
    layout = render_card(no, changed, vs['width'], vs['height'], card)
    fps = Fraction(vs['r_frame_rate'])
    assert fps == 30
    old_v = packet_times(source, 'v:0')
    speech_end, endpoint_checks = voice_end(source, float(vs['duration']))
    transition_frame = math.ceil(speech_end * fps)
    transition = transition_frame / float(fps)
    assert 0 <= transition - speech_end < 1 / fps
    # Copy the complete original programme up to its final closed GOP. Re-encode
    # only that GOP, replacing its silent end hold with the summary page.
    keys = [(i, float(p['pts_time'])) for i, p in enumerate(old_v)
            if 'K' in p['flags'] and float(p['pts_time']) < transition]
    prefix_count, key_time = keys[-1]
    assert prefix_count == round(key_time * fps)
    body_tail_frames = transition_frame - prefix_count
    card_frames = 60
    print(f'Voice ends {speech_end:.3f}s; summary starts {transition:.6f}s; '
          f'original end hold removed; summary {card_frames} frames.', flush=True)
    prefix = OUT / f'{no}-prefix.mp4'
    tail = OUT / f'{no}-replacement-tail.mp4'
    command(['ffmpeg', '-v', 'error', '-y', '-copyts', '-i', source, '-map', '0:v:0',
             '-an', '-c:v', 'copy', '-frames:v', prefix_count,
             '-avoid_negative_ts', 'disabled', prefix])
    graph = (f'[0:v]trim=end_frame={body_tail_frames},setpts=PTS-STARTPTS[b];'
             f'[1:v]trim=end_frame={card_frames},setpts=PTS-STARTPTS[c];'
             '[b][c]concat=n=2:v=1:a=0[out]')
    command(['ffmpeg', '-v', 'error', '-y', '-ss', f'{key_time:.9f}', '-i', source,
             '-loop', '1', '-framerate', str(fps), '-i', card,
             '-filter_complex', graph, '-map', '[out]', '-an',
             '-frames:v', body_tail_frames + card_frames, '-r', str(fps), '-fps_mode', 'cfr',
             '-c:v', 'libx264', '-preset', 'fast', '-crf', '10', '-threads', '2',
             '-pix_fmt', vs['pix_fmt'], '-profile:v', 'high', '-level:v', '5.1',
             '-video_track_timescale', Fraction(vs['time_base']).denominator, tail])
    concat = OUT / f'{no}.ffconcat'
    concat.write_text("ffconcat version 1.0\nfile '" + str(prefix) + "'\nduration "
                      + f'{key_time:.9f}' + "\nfile '" + str(tail) + "'\n")
    safe_title = data['title_en'].replace(':', '：')
    final = OUT / f'{no} - {safe_title} - {data["title_zh"]}.mp4'
    command(['ffmpeg', '-v', 'error', '-y', '-copyts', '-f', 'concat', '-safe', '0', '-i', concat,
             '-i', source, '-map', '0:v:0', '-map', '1:a:0', '-c', 'copy',
             '-avoid_negative_ts', 'disabled', '-movflags', '+faststart', final])
    for attempt in range(3):
        new_v = packet_times(final, 'v:0')
        delta = float(new_v[0]['pts_time']) - float(old_v[0]['pts_time'])
        if abs(delta) < .00001:
            break
        fixed = OUT / f'{no}-timing-fixed.mp4'
        command(['ffmpeg', '-v', 'error', '-y', '-copyts', '-itsoffset', str(-delta), '-i', final,
                 '-i', source, '-map', '0:v:0', '-map', '1:a:0', '-c', 'copy',
                 '-avoid_negative_ts', 'disabled', '-movflags', '+faststart', fixed])
        os.replace(fixed, final)
    new_v = packet_times(final, 'v:0')
    assert new_v[:prefix_count] == old_v[:prefix_count], 'Original programme prefix timing changed.'
    assert packet_times(final, 'a:0') == packet_times(source, 'a:0'), 'Original audio timing changed.'
    assert coded_frames_hash(source, prefix_count) == coded_frames_hash(final, prefix_count)
    assert len(new_v) == transition_frame + card_frames
    presentation_times = sorted(float(p['pts_time']) for p in new_v)
    assert all(abs(t - i / float(fps)) < .000002 for i, t in enumerate(presentation_times))
    ah = audio_hash(source)
    assert audio_hash(final) == ah, 'Original decoded audio changed.'
    after_vs = next(x for x in probe(final)['streams'] if x['codec_type'] == 'video')
    assert (after_vs['width'], after_vs['height']) == (3840, 2160)
    assert abs(float(after_vs['duration']) - (transition + 2)) < .00001
    # Verify the few body frames in the re-encoded GOP remain visually faithful.
    ssim = OUT / f'{no}-body-tail-ssim.txt'
    graph = (f'[0:v]trim=end_frame={body_tail_frames},setpts=PTS-STARTPTS[a];'
             f'[1:v]trim=end_frame={body_tail_frames},setpts=PTS-STARTPTS[b];'
             f'[a][b]ssim=stats_file={ssim}[out]')
    command(['ffmpeg', '-v', 'error', '-ss', f'{key_time:.9f}', '-i', source,
             '-ss', f'{key_time:.9f}', '-i', final, '-filter_complex', graph,
             '-map', '[out]', '-an', '-f', 'null', '-'])
    similarity = [float(x) for x in re.findall(r'All:([0-9.]+)', ssim.read_text())]
    assert len(similarity) == body_tail_frames and min(similarity) > .995, similarity
    # Save the two sides of the exact cut for a visual review.
    for name, frame in [('转场前', transition_frame - 1), ('简述首帧', transition_frame),
                        ('简述末帧', transition_frame + card_frames - 1)]:
        command(['ffmpeg', '-v', 'error', '-y', '-ss', f'{frame / float(fps):.9f}',
                 '-i', final, '-frames:v', '1', '-update', '1', OUT / f'{no}-{name}.png'])
    (OUT / f'{no}-script.json').write_text(json.dumps(changed, ensure_ascii=False, indent=1) + '\n')
    (OUT / f'{no}-verification.json').write_text(json.dumps({
        'article': no, 'kind': 'replace-original-end-hold', 'source': originals[0],
        'source_frames': int(vs['nb_frames']), 'output_frames': len(new_v),
        'source_voice_endpoint_seconds': speech_end, 'endpoint_threshold_checks': endpoint_checks,
        'summary_start_frame': transition_frame, 'summary_start_seconds': transition,
        'delay_after_voice_seconds': transition - speech_end,
        'end_page_frames': card_frames, 'end_page_seconds': 2,
        'copied_original_frames': prefix_count, 'reencoded_body_frames': body_tail_frames,
        'copied_prefix_coded_pictures_identical': True, 'copied_prefix_packet_timings_identical': True,
        'body_tail_min_ssim': min(similarity), 'original_audio_identical': True,
        'original_audio_packet_timings_identical': True, 'audio_sha256': ah,
        'body_script_identical': True, 'layout': layout,
        'video_sha256': hashlib.sha256(final.read_bytes()).hexdigest()
    }, ensure_ascii=False, indent=2))
    for p in (source, prefix, tail, concat):
        p.unlink()
    print(f'{no}: verified; immediate transition, exactly 60 summary frames; '
          'original audio samples and timing identical.', flush=True)


if __name__ == '__main__':
    no = argparse.ArgumentParser()
    no.add_argument('article')
    n = no.parse_args().article.zfill(2)
    os.chdir(ROOT)
    OUT.mkdir(exist_ok=True)
    assert n == '03', 'This workflow is limited to the single requested preview.'
    end_card(n)
