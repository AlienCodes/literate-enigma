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
import numpy as np
from PIL import Image, ImageDraw
import subprocess

ROOT = Path(__file__).resolve().parents[2]
TASK = ROOT / '.github/video-batch'
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
    all_summaries = {}
    for path in sorted((TASK / 'summaries').glob('*.json')):
        part = json.loads(path.read_text())
        assert not (all_summaries.keys() & part.keys()), 'Duplicate summary article.'
        all_summaries.update(part)
    data = all_summaries[no]
    assert len(data) == 5 and all(len(x) == 2 and all(x) for x in data)
    return '（简述：' + ''.join('▸' + label + '：' + body for label, body in data) + '）'


def add_summary(data, no):
    d = copy.deepcopy(data)
    c = d['sentences'][-1]['chunks'][-1]
    old = c.get('note') or ''
    head = old.split('（简述：', 1)[0].rstrip()
    c['note'] = (head + '\n' if head else '') + summary(no)
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


def get_renderer(data, reference_commit=None):
    reference_commit = reference_commit or BASE
    os.environ['VIDEO_S'] = '2'
    cache = Path(os.environ.get('RUNNER_TEMP', str(ROOT / 'work')))
    cache.mkdir(parents=True, exist_ok=True)
    baseline_render = cache / f'source-render-{reference_commit}.py'
    if not baseline_render.exists():
        baseline_render.write_text(get(['git', 'show', reference_commit + ':视频/工具/render.py']))
    spec = importlib.util.spec_from_file_location('body_render', baseline_render)
    r = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(r)
    r.F = str(ROOT / '视频/工具/fonts') + '/'
    tree = ast.parse(get(['git', 'show', reference_commit + ':视频/工具/make_video.py']))
    node = next(n.value for n in tree.body if isinstance(n, ast.Assign)
                and any(isinstance(t, ast.Name) and t.id == 'T' for t in n.targets)
                and isinstance(n.value, ast.Call) and isinstance(n.value.func, ast.Name)
                and n.value.func.id == 'dict' and any(k.arg == 'BG_TOP' for k in n.value.keywords))
    for k in node.keywords:
        setattr(r, k.arg, ast.literal_eval(k.value))
    r.apply_script(data)
    return r


TW, TH = 384, 216

# These two source videos predate the later note-only bullet-format commits.
# Their exact video-producing scripts/renderers are retained solely as pixel references.
PICTURE_REFERENCES = {
    '67': '35f90ba0552524301ce93831279155aa1984a61e',
    '69': 'a140726316c4f918d57534e27dbdce0282583e16',
}


def picture_reference(no, source, data, total_frames):
    commit = PICTURE_REFERENCES.get(no)
    if not commit:
        return data, BASE
    available = subprocess.run(['git', 'cat-file', '-e', commit + '^{commit}'],
                               capture_output=True).returncode == 0
    if not available:
        command(['git', 'fetch', '--no-tags', '--depth=1', '--filter=blob:none', 'origin', commit])
    historical = json.loads(get(['git', 'show', commit + f':视频/脚本/{no}.json']))
    current_chunks = data['sentences'][-1]['chunks']
    old_chunks = historical['sentences'][-1]['chunks']
    assert len(current_chunks) == len(old_chunks)
    for current, old in zip(current_chunks, old_chunks):
        for field in ('en', 'zh', 'align'):
            assert current[field] == old[field], (no, 'Historical body differs.', field)
        assert (current.get('note') or '').split('（简述：', 1)[0].rstrip() == (old.get('note') or '').split('（简述：', 1)[0].rstrip()
    paths = get(['git', '-c', 'core.quotepath=off', 'ls-tree', '-rz', '--name-only', commit]).split('\0')
    videos = [p for p in paths if p.startswith('最终版4K视频/' + no + ' - ') and p.endswith('.mp4')]
    assert len(videos) == 1
    reference_blob = get(['git', 'rev-parse', commit + ':' + videos[0]]).strip()
    source_blob = get(['git', 'hash-object', source]).strip()
    if source_blob != reference_blob:
        # A separately corrected audio track may change the container; its
        # encoded video must still be exactly the historical source pictures.
        reference = OUT / f'{no}-historical-video-check.mp4'
        with reference.open('wb') as f:
            command(['git', 'show', commit + ':' + videos[0]], stdout=f)
        assert coded_frames_hash(source, total_frames) == coded_frames_hash(reference, total_frames)
        reference.unlink()
    return historical, commit


def thumb(path):
    with Image.open(path) as im:
        return np.asarray(im.convert('RGB').resize((TW, TH), Image.Resampling.BOX))[:TH-2].copy()


def frame_thumb(path, frame):
    raw = command(['ffmpeg', '-v', 'error', '-ss', f'{frame / 30:.9f}', '-i', path,
                   '-frames:v', '1', '-vf', f'scale={TW}:{TH}:flags=area', '-pix_fmt', 'rgb24',
                   '-f', 'rawvideo', '-'], capture_output=True).stdout
    assert len(raw) == TW * TH * 3, (frame, len(raw))
    return np.frombuffer(raw, np.uint8).reshape(TH, TW, 3)[:TH-2].copy()


def score(frame, reference, mask):
    return float(np.abs(frame.astype(np.int16) - reference.astype(np.int16))[mask].mean())


def thumbnail_frames(source, start):
    args = ['ffmpeg', '-v', 'error', '-ss', f'{start / 30:.9f}', '-i', source,
            '-map', '0:v:0', '-an', '-vf', f'scale={TW}:{TH}:flags=area', '-pix_fmt', 'rgb24',
            '-fps_mode', 'passthrough', '-f', 'rawvideo', '-']
    p = subprocess.Popen([str(x) for x in args], stdout=subprocess.PIPE)
    size = TW * TH * 3
    index = start
    try:
        while True:
            raw = p.stdout.read(size)
            if not raw:
                break
            assert len(raw) == size
            yield index, np.frombuffer(raw, np.uint8).reshape(TH, TW, 3)[:TH-2].copy()
            index += 1
    finally:
        p.stdout.close()
        assert p.wait() == 0


def find_old_summary(no, source, data, total_frames, transition_frame):
    """Classify the actual pixels, including older videos with an inline summary."""
    data, reference_commit = picture_reference(no, source, data, total_frames)
    old_note = data['sentences'][-1]['chunks'][-1].get('note') or ''
    if '（简述：' not in old_note:
        return {'kind': 'absent', 'change_start': transition_frame, 'crop_height': 2144}
    old_summary = old_note[old_note.index('（简述：'):]
    r = get_renderer(data, reference_commit)
    background = r.bg()
    bg_thumb = np.asarray(background.resize((TW, TH), Image.Resampling.BOX))[:TH-2]
    last_score = float('inf')
    if hasattr(r, 'frame_简述'):
        old_card = OUT / f'{no}-old-summary-reference.png'
        r.frame_简述(old_summary, 1, old_card)
        card_ref = thumb(old_card)
        card_mask = np.max(np.abs(card_ref.astype(np.int16) - bg_thumb.astype(np.int16)), axis=2) > 8
        last_score = score(frame_thumb(source, total_frames-1), card_ref, card_mask)
    if last_score < 8:
        start = max(0, total_frames - 210)
        scores = [(f, score(a, card_ref, card_mask)) for f, a in thumbnail_frames(source, start)]
        assert len(scores) == total_frames-start
        good = [f for f, s in scores if s < 8]
        first = good[0]
        assert first > start and good == list(range(first, total_frames)), 'Old card is not one contiguous final page.'
        return {'kind': 'standalone', 'old_card_start': first,
                'change_start': min(first, transition_frame), 'crop_height': 2144,
                'reference_commit': reference_commit,
                'reference_score': last_score, 'old_card_match_max': max(s for f,s in scores if f>=first)}

    # Preserve the original layout calculation. Record where the old summary
    # was drawn, then cover only that region with the identical background.
    colors = r.分色(data)
    r.unify_colors(colors, data['sentences'])
    sent = data['sentences'][-1]
    chunks = [[tuple(p) for p in c['align']] for c in sent['chunks']]
    notes = [c.get('note') for c in sent['chunks']]
    es = min(r.max_es(chunks, r.sent_colors(colors, sent), notes), 200)
    cap = data.get('字号上限', {}).get(f'S{len(data["sentences"])}')
    if cap is not None:
        es = min(es, float(cap) * r.S)
    r.ES_FIXED = es
    first_line = old_summary.split('\n')[0]
    shown = getattr(r, '简条显示', lambda line: line)(first_line)
    heading = shown[:shown.index('：')+1] if '▸' in first_line and '：' in shown else shown
    refs = []
    erase_y = None
    original_text = ImageDraw.ImageDraw.text
    for active in range(len(chunks)):
        calls = []
        def record(draw, xy, text, *args, **kw):
            if str(text).strip():
                calls.append((str(text), draw.textbbox(xy, text, font=kw.get('font'))))
            return original_text(draw, xy, text, *args, **kw)
        ImageDraw.ImageDraw.text = record
        destination = OUT / f'{no}-old-body-active{active}.png'
        try:
            r.frame_interlinear(chunks, r.sent_colors(colors, sent), '', 1, str(destination),
                                active=active, notes=notes)
        finally:
            ImageDraw.ImageDraw.text = original_text
        marker = next((i for i,(txt,bbox) in enumerate(calls)
                       if txt.startswith('（简述：') or (heading and txt == heading)), None)
        assert marker is not None, 'Cannot identify the old summary text calls.'
        y = math.floor(min(b[1] for _,b in calls[marker:])) - 6
        previous_bottom = max(b[3] for _,b in calls[:marker])
        assert previous_bottom < y, ('Summary removal would touch the body.', previous_bottom, y)
        assert 0 < y < 2144
        if erase_y is None:
            erase_y = y
        assert y == erase_y
        ref = thumb(destination)
        mask = np.max(np.abs(ref.astype(np.int16) - bg_thumb.astype(np.int16)), axis=2) > 8
        refs.append((ref, mask))
    word_count = len(' '.join(c['en'] for c in sent['chunks']).split())
    scan_seconds = max(16, word_count * .85 + 10)
    scan_start = max(0, transition_frame - math.ceil(scan_seconds * 30))
    matches = []
    for f, a in thumbnail_frames(source, scan_start):
        values = [score(a, ref, mask) for ref, mask in refs]
        matches.append((f, min(values), int(np.argmin(values))))
    assert len(matches) == total_frames - scan_start
    assert matches[-1][1] < 8, ('Final body does not match original script/layout.', matches[-1])
    pos = len(matches) - 1
    while pos >= 0 and matches[pos][1] < 8:
        pos -= 1
    assert pos >= 0, 'Scan window does not extend before the final sentence.'
    first = matches[pos+1][0]
    assert first < transition_frame
    patch = background.convert('RGBA')
    alpha = Image.new('L', patch.size, 0)
    ImageDraw.Draw(alpha).rectangle((0, erase_y, r.W-1, r.H-8*r.S-1), fill=255)
    patch.putalpha(alpha)
    patch_path = OUT / f'{no}-old-summary-removal.png'
    patch.save(patch_path)
    (OUT / f'{no}-body-matching.json').write_text(json.dumps({
        'first_frame': first, 'erase_y': erase_y, 'font_px': es,
        'matches': matches[pos:],
    }, ensure_ascii=False, indent=2))
    return {'kind': 'inline', 'change_start': first, 'patch': str(patch_path),
            'reference_commit': reference_commit,
            'crop_height': erase_y, 'font_px_preserved': es,
            'match_max': max(v for f,v,i in matches[pos+1:]),
            'previous_frame_score': matches[pos][1]}

def end_card(no):
    paths = tree_paths()
    originals = [p for p in paths if p.startswith('最终版4K视频/' + no + ' - ') and p.endswith('.mp4')]
    assert len(originals) == 1, (no, originals)
    materialize(['视频/工具/render.py', '视频/工具/make_video.py', '视频/工具/fonts'])
    source = OUT / f'{no}-original.mp4'
    with source.open('wb') as f:
        command(['git', 'show', BASE + ':' + originals[0]], stdout=f)
    data = json.loads(get(['git', 'show', BASE + f':视频/脚本/{no}.json']))
    changed = add_summary(data, no)
    info = probe(source)
    vs = next(s for s in info['streams'] if s['codec_type'] == 'video')
    assert vs['codec_name'] == 'h264' and (vs['width'], vs['height']) == (3840, 2160)
    fps = Fraction(vs['r_frame_rate'])
    assert fps == 30
    old_v = packet_times(source, 'v:0')
    total_frames = int(vs['nb_frames'])
    speech_end, endpoint_checks = voice_end(source, float(vs['duration']))
    transition_frame = math.ceil(speech_end * fps)
    transition = transition_frame / float(fps)
    assert 0 <= transition - speech_end < 1/fps
    card = OUT / f'{no}-简述.png'
    layout = render_card(no, changed, 3840, 2160, card)
    removal = find_old_summary(no, source, data, total_frames, transition_frame)
    print('Original summary:', json.dumps(removal, ensure_ascii=False), flush=True)
    # A former independent page must never flash before the new summary.
    freeze_at = min(removal.get('old_card_start', transition_frame), transition_frame)
    change_start = removal['change_start']
    keys = [(i, float(p['pts_time'])) for i,p in enumerate(old_v)
            if 'K' in p['flags'] and round(float(p['pts_time']) * 30) < change_start]
    prefix_count, key_time = keys[-1]
    assert prefix_count == round(key_time * fps)
    body_tail_frames = transition_frame - prefix_count
    valid_body_frames = freeze_at - prefix_count
    assert 0 < valid_body_frames <= body_tail_frames
    prefix = OUT / f'{no}-prefix.mp4'
    tail = OUT / f'{no}-replacement-tail.mp4'
    command(['ffmpeg','-v','error','-y','-copyts','-i',source,'-map','0:v:0','-an',
             '-c:v','copy','-frames:v',prefix_count,'-avoid_negative_ts','disabled',prefix])
    graph = f'[0:v]trim=end_frame={valid_body_frames},setpts=PTS-STARTPTS'
    if valid_body_frames < body_tail_frames:
        graph += f',tpad=stop_mode=clone:stop={body_tail_frames-valid_body_frames}'
    graph += f',trim=end_frame={body_tail_frames}[base];'
    args = ['ffmpeg','-v','error','-y','-ss',f'{key_time:.9f}','-i',source]
    if removal['kind'] == 'inline':
        args += ['-loop','1','-framerate','30','-i',removal['patch']]
        graph += ('[1:v]format=rgba[patch];'
                  f"[base][patch]overlay=enable='gte(n,{change_start-prefix_count})':shortest=1[b];")
        card_index = 2
    else:
        graph += '[base]null[b];'
        card_index = 1
    args += ['-loop','1','-framerate','30','-i',card]
    graph += f'[{card_index}:v]trim=end_frame=60,setpts=PTS-STARTPTS[c];[b][c]concat=n=2:v=1:a=0[out]'
    command(args + ['-filter_complex',graph,'-map','[out]','-an',
                    '-frames:v',body_tail_frames+60,'-r','30','-fps_mode','cfr',
                    '-c:v','libx264','-preset','fast','-crf','10','-threads','2',
                    '-pix_fmt','yuv420p','-profile:v','high','-level:v','5.1',
                    '-video_track_timescale',Fraction(vs['time_base']).denominator,tail])
    concat = OUT / f'{no}.ffconcat'
    concat.write_text("ffconcat version 1.0\nfile '"+str(prefix)+"'\nduration "+
                      f'{key_time:.9f}'+"\nfile '"+str(tail)+"'\n")
    filename = f'{no} - {data["title_en"]} - {data["title_zh"]}.mp4'
    filename = filename.translate(str.maketrans({
        '?':'？', ':':'：', '*':'＊', '<':'＜', '>':'＞',
        '"':'＂', '|':'｜', '/':'／', '\\':'＼',
    })).replace('\r','').replace('\n','')
    final = OUT / filename
    command(['ffmpeg','-v','error','-y','-copyts','-f','concat','-safe','0','-i',concat,
             '-i',source,'-map','0:v:0','-map','1:a:0','-c','copy',
             '-avoid_negative_ts','disabled','-movflags','+faststart',final])
    for attempt in range(3):
        new_v = packet_times(final,'v:0')
        delta = float(new_v[0]['pts_time'])-float(old_v[0]['pts_time'])
        if abs(delta)<.00001:
            break
        fixed = OUT / f'{no}-timing-fixed.mp4'
        command(['ffmpeg','-v','error','-y','-copyts','-itsoffset',str(-delta),'-i',final,
                 '-i',source,'-map','0:v:0','-map','1:a:0','-c','copy',
                 '-avoid_negative_ts','disabled','-movflags','+faststart',fixed])
        os.replace(fixed,final)
    new_v = packet_times(final,'v:0')
    assert new_v[:prefix_count] == old_v[:prefix_count], 'Original prefix timing changed.'
    assert coded_frames_hash(source,prefix_count) == coded_frames_hash(final,prefix_count)
    assert packet_times(final,'a:0') == packet_times(source,'a:0'), 'Original audio timing changed.'
    assert len(new_v) == transition_frame+60
    pts = sorted(float(p['pts_time']) for p in new_v)
    assert all(abs(t-i/30)<.000002 for i,t in enumerate(pts)), 'Video frame gap or duplicate timestamp.'
    ah = audio_hash(source)
    assert audio_hash(final)==ah, 'Original audio samples changed.'
    out_vs = next(s for s in probe(final)['streams'] if s['codec_type']=='video')
    assert (out_vs['width'],out_vs['height']) == (3840,2160)
    assert abs(float(out_vs['duration'])-(transition+2))<.00001
    # Verify source body pixels outside the intentionally erased note.
    crop_h = 2*(removal['crop_height']//2)
    ssim = OUT / f'{no}-body-tail-ssim.txt'
    graph = (f'[0:v]trim=end_frame={valid_body_frames},setpts=PTS-STARTPTS,crop=iw:{crop_h}:0:0[a];'
             f'[1:v]trim=end_frame={valid_body_frames},setpts=PTS-STARTPTS,crop=iw:{crop_h}:0:0[b];'
             f'[a][b]ssim=stats_file={ssim}[out]')
    command(['ffmpeg','-v','error','-ss',f'{key_time:.9f}','-i',source,
             '-ss',f'{key_time:.9f}','-i',final,'-filter_complex',graph,
             '-map','[out]','-an','-f','null','-'])
    similarities = [float(x) for x in re.findall(r'All:([0-9.]+)',ssim.read_text())]
    assert len(similarities)==valid_body_frames and min(similarities)>.995, (len(similarities),valid_body_frames,min(similarities))
    removal_check = {}
    if removal['kind'] == 'inline':
        background_ref = thumb(removal['patch'])
        old_ref = thumb(sorted(OUT.glob(f'{no}-old-body-active*.png'))[-1])
        erased_pixels = np.max(np.abs(old_ref.astype(np.int16)-background_ref.astype(np.int16)),axis=2)>8
        erased_pixels[:math.ceil(removal['crop_height']/10)+1] = False
        assert erased_pixels.sum()>20
        values = [score(a, background_ref, erased_pixels)
                  for f,a in thumbnail_frames(final, removal['change_start']) if f<transition_frame]
        assert len(values)==transition_frame-removal['change_start']
        assert max(values)<3, ('Old summary pixels remain visible.', max(values))
        removal_check = {'erased_region_checked_frames':len(values),'background_match_max_error':max(values)}
    elif body_tail_frames>valid_body_frames:
        frozen_reference = frame_thumb(source, freeze_at-1)
        held_frame = frame_thumb(final, transition_frame-1)
        error=float(np.abs(frozen_reference.astype(float)-held_frame).mean())
        assert error<2, ('Old summary may be flashing before the cut.',error)
        removal_check = {'held_body_frame_match_error':error}
    for name,frame in [('转场前',transition_frame-1),('简述首帧',transition_frame),
                       ('简述末帧',transition_frame+59)]:
        command(['ffmpeg','-v','error','-y','-ss',f'{frame/30:.9f}','-i',final,
                 '-frames:v','1','-update','1',OUT/f'{no}-{name}.png'])
    card_ref = thumb(card)
    last_card = thumb(OUT/f'{no}-简述末帧.png')
    first_card = thumb(OUT/f'{no}-简述首帧.png')
    assert np.abs(card_ref.astype(float)-first_card).mean()<2
    assert np.abs(card_ref.astype(float)-last_card).mean()<2
    assert np.abs(card_ref.astype(float)-thumb(OUT/f'{no}-转场前.png')).mean()>3
    (OUT/f'{no}-script.json').write_text(json.dumps(changed,ensure_ascii=False,indent=1)+'\n')
    (OUT/f'{no}-verification.json').write_text(json.dumps({
        'article':no,'kind':'immediate-standalone-summary','source_commit':BASE,'source':originals[0],
        'width':3840,'height':2160,'source_frames':total_frames,'output_frames':len(new_v),
        'source_voice_endpoint_seconds':speech_end,
        'endpoint_threshold_checks':endpoint_checks,'summary_start_frame':transition_frame,
        'summary_start_seconds':transition,'delay_after_voice_seconds':transition-speech_end,
        'end_page_frames':60,'end_page_seconds':2,'old_summary_handling':removal,
        'old_summary_pixel_verification':removal_check,
        'copied_original_frames':prefix_count,'reencoded_body_frames':body_tail_frames,
        'held_final_body_frames':body_tail_frames-valid_body_frames,
        'copied_prefix_coded_pictures_identical':True,'copied_prefix_packet_timings_identical':True,
        'body_outside_summary_min_ssim':min(similarities),
        'original_audio_identical':True,'original_audio_packet_timings_identical':True,
        'audio_sha256':ah,'body_script_identical':True,'layout':layout,
        'video_sha256':hashlib.sha256(final.read_bytes()).hexdigest(),
    },ensure_ascii=False,indent=2))
    for p in (source,prefix,tail,concat):
        p.unlink()
    print(f'{no}: 4K; original audio identical; next-frame summary; exactly 60 end-page frames.',flush=True)


if __name__ == '__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('article')
    no=ap.parse_args().article.zfill(2)
    assert no!='05', 'Article05 is produced and audited by its own canonical pipeline.'
    os.chdir(ROOT)
    OUT.mkdir(exist_ok=True)
    end_card(no)

