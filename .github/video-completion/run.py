#!/usr/bin/env python3
"""Add only an end card, checking every original decoded frame and audio sample."""
import argparse
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
TASK = ROOT / '.github/video-completion'
OUT = ROOT / 'completion-output'


def command(args, **kw):
    return subprocess.run([str(x) for x in args], check=True, **kw)


def get(args):
    return command(args, capture_output=True, text=True).stdout


def materialize(paths):
    command(['git', 'sparse-checkout', 'add', '--stdin'], cwd=ROOT,
            input=''.join('/' + p + '\n' for p in paths), text=True)


def tree_paths():
    return get(['git', '-c', 'core.quotepath=off', 'ls-tree', '-rz', '--name-only', 'HEAD']).split('\0')


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


def frame_hashes(p, count=None):
    args = ['ffmpeg', '-v', 'error', '-threads', '2', '-i', p, '-map', '0:v:0', '-an']
    if count is not None:
        args += ['-frames:v', str(count)]
    raw = get(args + ['-fps_mode', 'passthrough', '-f', 'framehash', '-hash', 'sha256', '-'])
    return [line.rsplit(',', 1)[-1].strip() for line in raw.splitlines() if line and not line.startswith('#')]


def audio_hash(p):
    return get(['ffmpeg', '-v', 'error', '-i', p, '-map', '0:a:0', '-vn',
                '-c:a', 'pcm_s16le', '-f', 'hash', '-hash', 'sha256', '-']).strip()


def render_card(no, data, width, height, destination):
    os.environ['VIDEO_S'] = '2' if width == 3840 else '1'
    spec = importlib.util.spec_from_file_location('completion_render', ROOT / '视频/工具/render.py')
    renderer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(renderer)
    renderer.F = str(ROOT / '视频/工具/fonts') + '/'
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
    selected = [originals[0], f'视频/脚本/{no}.json', '视频/工具/render.py', '视频/工具/fonts']
    materialize(selected)
    source = ROOT / originals[0]
    data = json.loads((ROOT / f'视频/脚本/{no}.json').read_text())
    changed = add_summary(data, no)
    info = probe(source)
    vs = next(s for s in info['streams'] if s['codec_type'] == 'video')
    assert vs['codec_name'] == 'h264' and (vs['width'], vs['height']) == (3840, 2160)
    card = OUT / f'{no}-简述.png'
    layout = render_card(no, changed, vs['width'], vs['height'], card)
    tail = OUT / f'{no}-endcard.mp4'
    # Match the current specification: a separate, silent two-second end page.
    command(['ffmpeg', '-v', 'error', '-y', '-loop', '1', '-framerate', vs['r_frame_rate'], '-i', card,
             '-t', '2', '-an', '-c:v', 'libx264', '-preset', 'fast', '-crf', '16', '-threads', '2',
             '-pix_fmt', vs['pix_fmt'], '-profile:v', 'high', '-level:v', '5.1', tail])
    concat = OUT / f'{no}.ffconcat'
    concat.write_text("ffconcat version 1.0\nfile '" + str(source) + "'\nfile '" + str(tail) + "'\n")
    final = OUT / f'{no} - {data["title_en"]} - {data["title_zh"]}.mp4'
    # The complete original video is copied. Its original audio track is copied once.
    # Adding a silent end page does not decode/re-encode or cut the existing programme.
    command(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', concat,
             '-i', source, '-map', '0:v:0', '-map', '1:a:0', '-c', 'copy', '-movflags', '+faststart', final])
    before = frame_hashes(source)
    after = frame_hashes(final)
    assert after[:len(before)] == before, 'An original decoded frame changed.'
    assert len(after) > len(before), 'End page is missing.'
    ah = audio_hash(source)
    assert audio_hash(final) == ah, 'Original decoded audio changed.'
    updated = OUT / f'{no}-script.json'
    updated.write_text(json.dumps(changed, ensure_ascii=False, indent=1) + '\n')
    (OUT / f'{no}-verification.json').write_text(json.dumps({
        'article': no, 'kind': 'end-page-only', 'source': originals[0], 'source_frames': len(before),
        'output_frames': len(after), 'all_original_frames_identical': True,
        'original_audio_identical': True, 'audio_sha256': ah, 'body_script_identical': True,
        'layout': layout, 'end_page_seconds': 2,
        'video_sha256': hashlib.sha256(final.read_bytes()).hexdigest()
    }, ensure_ascii=False, indent=2))
    tail.unlink()
    concat.unlink()
    print(f'{no}: completed; all {len(before)} original frames and original audio are identical.', flush=True)


def create_five():
    materialize(['视频/工具', '视频/脚本', '视频/配音缓存', '视频/制作记录', '视频/音频核对',
                 '视频/*.md', '新版定稿', '视频/视频/27.mp4', '最终版4K视频/27*'])
    machine = Path(os.environ['RUNNER_TEMP']) / 'completion-machine'
    tools = ROOT / '视频/工具'
    command(['bash', tools / '环境/准备机器.sh', ROOT, machine])
    work = machine / 'video'
    command([sys.executable, tools / '初稿生成/gen05.py'], cwd=work)
    script = work / 'scripts/05.json'
    d = json.loads(script.read_text())
    c = d['sentences'][-1]['chunks'][-1]
    original_note = (c.get('note') or '').split('（简述：', 1)[0].rstrip()
    c['note'] = (original_note + '\n' if original_note else '') + summary('05')
    script.write_text(json.dumps(d, ensure_ascii=False, indent=1) + '\n')
    env = {**os.environ, 'XG_P': str(ROOT), 'XG_TOOLS': str(tools), 'XG_WORK': str(work)}
    # --不推 keeps the existing backup/release branches untouched.
    command(['bash', tools / '新管/做.sh', '05', '--不推'], cwd=work, env=env)
    check = get([sys.executable, tools / '交付核查.py', '05', '出片后'], cwd=work, env=env)
    (OUT / '05-delivery-check.txt').write_text(check)
    assert '全部通过' in check and '【不通过' not in check
    final = OUT / '05 - The Fingerprint in the Blood - 血里的指纹_1080p.mp4'
    shutil.copy2(work / '05.mp4', final)
    shutil.copy2(script, OUT / '05-script.json')
    dossier = ROOT / '视频/制作记录/05_疑点.md'
    if dossier.exists():
        shutil.copy2(dossier, OUT / '05-疑点说明.md')
    (OUT / '05-verification.json').write_text(json.dumps({
        'article': '05', 'kind': 'new-1080p-video', 'delivery_check_passed': True,
        'video_sha256': hashlib.sha256(final.read_bytes()).hexdigest()
    }, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    no = argparse.ArgumentParser()
    no.add_argument('article')
    n = no.parse_args().article.zfill(2)
    os.chdir(ROOT)
    OUT.mkdir(exist_ok=True)
    create_five() if n == '05' else end_card(n)
