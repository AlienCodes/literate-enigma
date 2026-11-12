#!/usr/bin/env python3
"""Collect only verified GitHub outputs and save them on this isolated task branch."""
import copy
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

ROOT = Path.cwd()
INCOMING = ROOT / 'incoming'
DELIVERY = ROOT / 'delivery'
BASE = 'c9d52b26fe981ef8e4c412189ca289716ab8bf00'
IDS = [f'{i:02}' for i in range(1, 21) if i != 5] + ['22']


def git(*args):
    return subprocess.run(['git', *args], check=True, capture_output=True, text=True).stdout


def sha(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for block in iter(lambda: f.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def install(source, destination):
    p = ROOT / destination
    p.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, p)
    return str(destination)


reports, changes = [], []
preview_cards = []
for no in IDS:
    folder = INCOMING / f'video-{no}'
    report = json.loads((folder / f'{no}-verification.json').read_text())
    videos = list(folder.glob('*.mp4'))
    assert len(videos) == 1, (no, videos)
    video = videos[0]
    assert sha(video) == report['video_sha256'], f'{no}: downloaded video checksum mismatch'
    script = json.loads((folder / f'{no}-script.json').read_text())
    note = script['sentences'][-1]['chunks'][-1].get('note', '')
    assert '（简述：' in note and note.count('▸') == 5
    if no == '05':
        assert report['delivery_check_passed']
        check = (folder / '05-delivery-check.txt').read_text()
        assert '全部通过' in check and '【不通过' not in check
        changes.append(install(video, '视频/视频/草稿1080p/05_1080p.mp4'))
        changes.append(install(folder / '05-delivery-check.txt', '视频/音频核对/交付核查_05_1080p.txt'))
    else:
        assert report['all_original_frames_identical'] and report['original_audio_identical']
        assert report['body_script_identical'] and report['layout']['items'] == 5
        original = json.loads(git('show', f'{BASE}:视频/脚本/{no}.json'))
        restored = copy.deepcopy(script)
        old_chunk = original['sentences'][-1]['chunks'][-1]
        last = restored['sentences'][-1]['chunks'][-1]
        if 'note' in old_chunk:
            last['note'] = old_chunk['note']
        else:
            last.pop('note', None)
        assert restored == original, f'{no}: script changed outside the final note'
        assert report['source'].startswith(f'最终版4K视频/{no} - ')
        changes.append(install(video, report['source']))
        destination = DELIVERY / '20篇简述补页_4K'
        destination.mkdir(parents=True, exist_ok=True)
        shutil.copy2(video, destination / video.name)
        shutil.copy2(folder / f'{no}-简述.png', destination / f'{no}-简述.png')
        preview_cards.append((no, folder / f'{no}-简述.png'))
        shutil.copy2(folder / f'{no}-verification.json', destination / f'{no}-核验.json')
    changes.append(install(folder / f'{no}-script.json', f'视频/脚本/{no}.json'))
    changes.append(install(folder / f'{no}-verification.json', f'视频/音频核对/简述补页_{no}.json'))
    reports.append(report)

record = ROOT / '视频/制作记录/简述补页_2026-11-12.json'
record.parent.mkdir(parents=True, exist_ok=True)
record.write_text(json.dumps({
    'user_request': '第05篇做出来；没有简述的只在最后一页加简述，其他地方不要乱改；直接在GitHub最多20个并行',
    'source_base': BASE, 'summaries_added': 20, 'existing_4k_videos_updated': 20,
    'new_article_05': 'separate production workflow', 'verification': reports
}, ensure_ascii=False, indent=2) + '\n')
changes.append(str(record.relative_to(ROOT)))
git('add', '--sparse', '--', *changes)
git('-c', 'user.name=github-actions[bot]', '-c', 'user.email=41898282+github-actions[bot]@users.noreply.github.com',
    'commit', '-m', '完成20篇4K简述补页；原有画面、音轨与正文逐项保持一致')
git('push', 'origin', 'HEAD:codex/finish-05-and-summaries-20261112')
print('Saved all 20 verified end-page outputs on the task branch; original main and master branches are untouched.')

# Small review sheets contain only the new end pages, never altered programme frames.
from PIL import Image, ImageDraw
previews = ROOT / 'previews'
previews.mkdir(exist_ok=True)
for start in range(0, len(preview_cards), 4):
    page = Image.new('RGB', (1920, 1120), (14, 36, 30))
    draw = ImageDraw.Draw(page)
    for i, (no, path) in enumerate(preview_cards[start:start + 4]):
        im = Image.open(path).convert('RGB')
        im.thumbnail((960, 540), Image.Resampling.LANCZOS)
        x, y = (i % 2) * 960, (i // 2) * 560
        page.paste(im, (x, y + 20))
        draw.text((x + 10, y + 2), 'Article ' + no, fill=(251, 191, 36))
    page.save(previews / f'end-pages-{start // 4 + 1}.png')
